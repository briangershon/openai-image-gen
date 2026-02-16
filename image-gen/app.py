"""
Flask REST API for OpenAI image generation service.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

from flask import Flask, request, jsonify, send_file
from werkzeug.exceptions import HTTPException

from image_generator import (
    ImageGenerator,
    ImageGenerationError,
    RateLimitError,
    InvalidAPIKeyError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
IMAGES_DIR = Path("/app/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def get_api_key() -> str:
    """
    Read OpenAI API key from Docker secret.

    Returns:
        API key string

    Raises:
        RuntimeError: If API key cannot be found or read
    """
    secret_path = "/run/secrets/openai_api_key"

    # Check if Docker secret exists
    if not os.path.exists(secret_path):
        raise RuntimeError(
            "OpenAI API key not found. Docker secret 'openai_api_key' must be configured.\n"
            "See README.md for setup instructions."
        )

    # Read the secret
    try:
        with open(secret_path, "r") as f:
            api_key = f.read().strip()
            if not api_key:
                raise RuntimeError("OpenAI API key secret exists but is empty")
            logger.info("Loaded API key from Docker secret")
            return api_key
    except Exception as e:
        raise RuntimeError(f"Failed to read Docker secret: {e}")


# Initialize API key and generator
try:
    API_KEY = get_api_key()
    generator = ImageGenerator(API_KEY)
    API_KEY_CONFIGURED = True
except Exception as e:
    logger.error(f"Failed to initialize API key: {e}")
    API_KEY = None
    generator = None
    API_KEY_CONFIGURED = False


def error_response(message: str, code: str, status_code: int) -> Tuple[Dict[str, Any], int]:
    """
    Create standardized error response.

    Args:
        message: Error message
        code: Error code
        status_code: HTTP status code

    Returns:
        Tuple of (response dict, status code)
    """
    return {
        "error": message,
        "status": "failed",
        "code": code
    }, status_code


def validate_generate_request(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate image generation request data.

    Args:
        data: Request JSON data

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data:
        return False, "Request body is required"

    if "prompt" not in data:
        return False, "Missing required field: prompt"

    prompt = data.get("prompt", "")
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"

    # Validate model
    model = data.get("model", "dall-e-3")
    valid_models = ["dall-e-2", "dall-e-3"]
    if model not in valid_models:
        return False, f"Invalid model. Supported models: {', '.join(valid_models)}"

    # Validate size
    size = data.get("size", "1024x1024")
    if model == "dall-e-3":
        valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
    else:
        valid_sizes = ["256x256", "512x512", "1024x1024"]

    if size not in valid_sizes:
        return False, f"Invalid size for {model}. Supported sizes: {', '.join(valid_sizes)}"

    # Validate quality (dall-e-3 only)
    quality = data.get("quality", "standard")
    if quality not in ["standard", "hd"]:
        return False, "Invalid quality. Supported: standard, hd"

    # Validate style (dall-e-3 only)
    style = data.get("style")
    if style and style not in ["vivid", "natural"]:
        return False, "Invalid style. Supported: vivid, natural"

    # Validate count
    count = data.get("count", 1)
    if not isinstance(count, int) or count < 1 or count > 10:
        return False, "Count must be an integer between 1 and 10"

    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dash, underscore, and dot
    sanitized = "".join(c for c in filename if c.isalnum() or c in ".-_")
    return sanitized


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "api_key_configured": API_KEY_CONFIGURED,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate one or more images.

    Request body:
        {
            "prompt": "A serene mountain landscape",
            "count": 1,
            "model": "dall-e-3",
            "size": "1024x1024",
            "quality": "standard",
            "style": null
        }

    Response:
        {
            "job_id": "uuid",
            "status": "completed",
            "images": [
                {
                    "id": "image-uuid",
                    "url": "/images/image-uuid.png",
                    "prompt": "...",
                    "model": "dall-e-3"
                }
            ]
        }
    """
    if not API_KEY_CONFIGURED:
        return error_response(
            "Image generation service not properly configured",
            "SERVICE_UNAVAILABLE",
            503
        )

    # Parse and validate request
    try:
        data = request.get_json()
    except Exception:
        return error_response(
            "Invalid JSON in request body",
            "INVALID_JSON",
            400
        )

    is_valid, error_msg = validate_generate_request(data)
    if not is_valid:
        return error_response(error_msg, "VALIDATION_ERROR", 400)

    # Extract parameters
    prompt = data["prompt"]
    count = data.get("count", 1)
    model = data.get("model", "dall-e-3")
    size = data.get("size", "1024x1024")
    quality = data.get("quality", "standard")
    style = data.get("style")

    # Generate job ID
    job_id = str(uuid.uuid4())
    job_dir = IMAGES_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting job {job_id}: {count} images, model={model}, prompt='{prompt[:50]}...'")

    try:
        # Generate images
        images_data = generator.generate_batch(
            prompt=prompt,
            count=count,
            model=model,
            size=size,
            quality=quality,
            style=style
        )

        # Download and save images
        result_images = []
        for idx, img_data in enumerate(images_data, 1):
            image_id = str(uuid.uuid4())
            image_url = img_data.get("url")
            revised_prompt = img_data.get("revised_prompt", prompt)

            # Download image
            image_bytes = generator.download_image(image_url)

            # Save image
            filename = f"{idx:03d}-{image_id}.png"
            filepath = job_dir / filename
            generator.save_image(image_bytes, str(filepath))

            logger.info(f"Saved image {idx}/{count} to {filepath}")

            result_images.append({
                "id": image_id,
                "url": f"/images/{image_id}",
                "prompt": revised_prompt,
                "model": model,
                "size": size
            })

        # Save metadata
        metadata = {
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt,
            "count": count,
            "model": model,
            "size": size,
            "quality": quality,
            "style": style,
            "images": result_images
        }

        metadata_path = job_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Job {job_id} completed successfully: {len(result_images)} images")

        return jsonify({
            "job_id": job_id,
            "status": "completed",
            "images": result_images
        })

    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded for job {job_id}: {e}")
        response = error_response(
            str(e),
            "RATE_LIMIT_EXCEEDED",
            429
        )
        if e.retry_after:
            return response[0], response[1], {"Retry-After": str(e.retry_after)}
        return response

    except InvalidAPIKeyError as e:
        logger.error(f"Invalid API key for job {job_id}: {e}")
        return error_response(
            "Image generation service configuration error",
            "SERVICE_ERROR",
            500
        )

    except ImageGenerationError as e:
        logger.error(f"Image generation failed for job {job_id}: {e}")
        return error_response(
            str(e),
            "GENERATION_ERROR",
            400
        )

    except Exception as e:
        logger.exception(f"Unexpected error for job {job_id}: {e}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            500
        )


@app.route("/images/<image_id>", methods=["GET"])
def get_image(image_id: str):
    """
    Retrieve image file by ID.

    Args:
        image_id: Image UUID

    Returns:
        Image file (binary data)
    """
    # Sanitize image_id to prevent path traversal
    image_id = sanitize_filename(image_id)

    # Search for the image file across all job directories
    for job_dir in IMAGES_DIR.iterdir():
        if not job_dir.is_dir():
            continue

        for image_file in job_dir.glob(f"*{image_id}*"):
            if image_file.is_file() and image_file.suffix in [".png", ".jpg", ".jpeg"]:
                logger.info(f"Serving image: {image_file}")
                return send_file(
                    str(image_file),
                    mimetype="image/png",
                    as_attachment=False
                )

    logger.warning(f"Image not found: {image_id}")
    return error_response(
        f"Image not found: {image_id}",
        "IMAGE_NOT_FOUND",
        404
    )


@app.route("/images/<image_id>", methods=["DELETE"])
def delete_image(image_id: str):
    """
    Delete image file by ID.

    Args:
        image_id: Image UUID

    Returns:
        Success message
    """
    # Sanitize image_id to prevent path traversal
    image_id = sanitize_filename(image_id)

    # Search for the image file across all job directories
    for job_dir in IMAGES_DIR.iterdir():
        if not job_dir.is_dir():
            continue

        for image_file in job_dir.glob(f"*{image_id}*"):
            if image_file.is_file() and image_file.suffix in [".png", ".jpg", ".jpeg"]:
                try:
                    image_file.unlink()
                    logger.info(f"Deleted image: {image_file}")
                    return jsonify({
                        "status": "success",
                        "message": f"Image {image_id} deleted"
                    })
                except Exception as e:
                    logger.error(f"Failed to delete image {image_id}: {e}")
                    return error_response(
                        f"Failed to delete image: {str(e)}",
                        "DELETE_ERROR",
                        500
                    )

    logger.warning(f"Image not found for deletion: {image_id}")
    return error_response(
        f"Image not found: {image_id}",
        "IMAGE_NOT_FOUND",
        404
    )


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions."""
    return error_response(
        e.description,
        "HTTP_ERROR",
        e.code
    )


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {e}")
    return error_response(
        "Internal server error",
        "INTERNAL_ERROR",
        500
    )


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=5000, debug=False)
