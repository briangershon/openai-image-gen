"""
OpenAI image generation module.
Uses stdlib urllib instead of OpenAI SDK for minimal dependencies.
"""

import json
import urllib.request
import urllib.error
import uuid
from typing import Dict, List, Optional, Any


class ImageGenerationError(Exception):
    """Base exception for image generation errors."""
    pass


class RateLimitError(ImageGenerationError):
    """Raised when OpenAI API rate limit is exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class InvalidAPIKeyError(ImageGenerationError):
    """Raised when API key is invalid or missing."""
    pass


class ImageGenerator:
    """OpenAI image generation client using stdlib urllib."""

    OPENAI_API_URL = "https://api.openai.com/v1/images/generations"

    def __init__(self, api_key: str):
        """
        Initialize the image generator.

        Args:
            api_key: OpenAI API key
        """
        if not api_key:
            raise InvalidAPIKeyError("OpenAI API key is required")
        self.api_key = api_key

    def generate_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        style: Optional[str] = None,
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Generate a single image using OpenAI API.

        Args:
            prompt: Text description of desired image
            model: Model to use (dall-e-2, dall-e-3)
            size: Image size (1024x1024, 1024x1792, 1792x1024 for dall-e-3)
            quality: Image quality (standard, hd) - dall-e-3 only
            style: Image style (vivid, natural) - dall-e-3 only
            n: Number of images (dall-e-2 supports multiple, dall-e-3 only 1)

        Returns:
            Dict with 'created', 'data' (list of image objects)

        Raises:
            RateLimitError: When rate limit is exceeded
            InvalidAPIKeyError: When API key is invalid
            ImageGenerationError: For other API errors
        """
        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "response_format": "url"  # Get URLs, we'll download the images
        }

        # Add optional parameters for dall-e-3
        if model == "dall-e-3":
            if quality:
                payload["quality"] = quality
            if style:
                payload["style"] = style

        # Create request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.OPENAI_API_URL,
            data=data,
            headers=headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                error_message = error_data.get('error', {}).get('message', str(e))
            except json.JSONDecodeError:
                error_message = error_body or str(e)

            if e.code == 401:
                raise InvalidAPIKeyError(f"Invalid API key: {error_message}")
            elif e.code == 429:
                retry_after = e.headers.get('Retry-After')
                raise RateLimitError(
                    f"Rate limit exceeded: {error_message}",
                    retry_after=int(retry_after) if retry_after else None
                )
            elif e.code == 400:
                raise ImageGenerationError(f"Invalid request: {error_message}")
            else:
                raise ImageGenerationError(f"API error ({e.code}): {error_message}")

        except urllib.error.URLError as e:
            raise ImageGenerationError(f"Network error: {e.reason}")

        except Exception as e:
            raise ImageGenerationError(f"Unexpected error: {str(e)}")

    def generate_batch(
        self,
        prompt: str,
        count: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple images.

        For dall-e-3: Makes sequential API calls (limitation: 1 per request)
        For dall-e-2: Can generate multiple in single request

        Args:
            prompt: Text description of desired image
            count: Number of images to generate
            **kwargs: Additional arguments passed to generate_image

        Returns:
            List of image data dictionaries
        """
        model = kwargs.get('model', 'dall-e-3')
        all_images = []

        if model == "dall-e-3":
            # dall-e-3 only supports n=1, so make multiple requests
            for i in range(count):
                result = self.generate_image(prompt, n=1, **kwargs)
                all_images.extend(result.get('data', []))
        else:
            # dall-e-2 can generate multiple images in one request
            result = self.generate_image(prompt, n=count, **kwargs)
            all_images.extend(result.get('data', []))

        return all_images

    @staticmethod
    def download_image(url: str) -> bytes:
        """
        Download image from URL.

        Args:
            url: Image URL

        Returns:
            Image data as bytes

        Raises:
            ImageGenerationError: If download fails
        """
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except Exception as e:
            raise ImageGenerationError(f"Failed to download image: {str(e)}")

    @staticmethod
    def save_image(data: bytes, filepath: str) -> None:
        """
        Save image data to file.

        Args:
            data: Image data as bytes
            filepath: Path to save image

        Raises:
            ImageGenerationError: If save fails
        """
        try:
            with open(filepath, 'wb') as f:
                f.write(data)
        except Exception as e:
            raise ImageGenerationError(f"Failed to save image: {str(e)}")
