# OpenAI Image Generation REST API

Generate high-quality images using DALL-E 2 and DALL-E 3 models through a secure Docker-hosted REST API service.

## Overview

This skill provides access to OpenAI's DALL-E image generation models via a containerized REST API. The service keeps your OpenAI API credentials secure while allowing you to generate images through simple HTTP requests.

**Key Benefits:**
- **Secure**: API key stored in Docker secrets, never exposed to clients
- **Simple**: Standard REST API with curl-compatible endpoints
- **Flexible**: Supports both DALL-E 2 and DALL-E 3 with all their parameters
- **Persistent**: Images saved locally with metadata for later retrieval

## Prerequisites

Before using this skill, ensure the Docker service is running:

1. **Docker and Docker Compose installed** (v1.27+ for secrets support)
2. **Service must be running:**
   ```bash
   cd /path/to/docker-openai-image-gen
   docker compose up -d
   ```

3. **Verify service health:**
   ```bash
   curl http://openai-image-gen:5000/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "api_key_configured": true,
     "timestamp": "2026-02-16T10:30:00.000000"
   }
   ```

If the service is not running or the health check fails, you cannot generate images.

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

Check if the service is running and the API key is configured.

**Example:**
```bash
curl http://openai-image-gen:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "api_key_configured": true,
  "timestamp": "2026-02-16T10:30:00.000000"
}
```

### 2. Generate Images

**Endpoint:** `POST /generate`

Generate one or more images from a text prompt.

**Request Format:**
```bash
curl -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your image description here",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
    "style": "vivid",
    "count": 1
  }'
```

**Request Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `prompt` | Yes | string | Text description of the desired image |
| `model` | No | string | "dall-e-2" or "dall-e-3" (default: "dall-e-3") |
| `size` | No | string | Image dimensions (see model-specific options below) |
| `quality` | No | string | "standard" or "hd" (DALL-E 3 only, default: "standard") |
| `style` | No | string | "vivid" or "natural" (DALL-E 3 only, default: "vivid") |
| `count` | No | integer | Number of images (1-10 for DALL-E 2, 1 for DALL-E 3) |

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "images": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "url": "/images/7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "prompt": "A serene mountain landscape at sunset...",
      "model": "dall-e-3",
      "size": "1024x1024"
    }
  ]
}
```

### 3. Download Image

**Endpoint:** `GET /images/{image_id}`

Download a previously generated image using its ID.

**Example:**
```bash
curl http://openai-image-gen:5000/images/7c9e6679-7425-40de-944b-e07fc1f90ae7 \
  --output myimage.png
```

**Response:** Binary PNG image data

### 4. Delete Image

**Endpoint:** `DELETE /images/{image_id}`

Remove a generated image from storage.

**Example:**
```bash
curl -X DELETE http://openai-image-gen:5000/images/7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Response:**
```json
{
  "status": "success",
  "message": "Image 7c9e6679-7425-40de-944b-e07fc1f90ae7 deleted"
}
```

## Usage Examples

### Example 1: Simple DALL-E 3 Generation

Generate a single image with default settings:

```bash
curl -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A serene mountain landscape at sunset"}'
```

### Example 2: HD Quality Landscape (DALL-E 3)

Generate a high-quality portrait-oriented image:

```bash
curl -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A photorealistic portrait of a wise old tree",
    "model": "dall-e-3",
    "size": "1024x1792",
    "quality": "hd",
    "style": "natural"
  }'
```

### Example 3: Multiple Variations (DALL-E 2)

Generate multiple variations in a single request:

```bash
curl -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Abstract geometric patterns in vibrant colors",
    "count": 4,
    "model": "dall-e-2",
    "size": "512x512"
  }'
```

### Example 4: Generate and Download

Complete workflow to generate and save an image:

```bash
# 1. Generate image and save response
curl -s -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Beautiful sunset over the ocean", "model": "dall-e-3"}' \
  > response.json

# 2. Extract image ID from response
IMAGE_ID=$(cat response.json | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# 3. Download the image
curl http://openai-image-gen:5000/images/$IMAGE_ID --output sunset.png

echo "Image saved as sunset.png"
```

### Example 5: Using jq for JSON Parsing

If you have `jq` installed for better JSON handling:

```bash
# Generate image
RESPONSE=$(curl -s -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic cityscape", "model": "dall-e-3"}')

# Extract and download all images
echo "$RESPONSE" | jq -r '.images[].id' | while read image_id; do
  curl http://openai-image-gen:5000/images/$image_id --output "${image_id}.png"
  echo "Downloaded: ${image_id}.png"
done
```

## Model-Specific Parameters

### DALL-E 3

**Supported Sizes:**
- `1024x1024` (square, default)
- `1024x1792` (portrait)
- `1792x1024` (landscape)

**Quality Options:**
- `standard` (default) - Faster, lower cost
- `hd` - Higher detail, higher cost

**Style Options:**
- `vivid` (default) - More dramatic and vibrant
- `natural` - More natural and realistic

**Count:** Always 1 (service handles batching sequentially if you need multiple)

**Example:**
```bash
curl -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A peaceful zen garden",
    "model": "dall-e-3",
    "size": "1792x1024",
    "quality": "hd",
    "style": "natural"
  }'
```

### DALL-E 2

**Supported Sizes:**
- `256x256` (small)
- `512x512` (medium)
- `1024x1024` (large)

**Quality:** Not supported (always standard quality)

**Style:** Not supported

**Count:** 1-10 images per request (true batch generation)

**Example:**
```bash
curl -X POST http://openai-image-gen:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cute robot in a meadow",
    "model": "dall-e-2",
    "size": "256x256",
    "count": 3
  }'
```

## Configuration

### Default API URL

The service URL depends on where you're calling from:

**From Docker containers in the same network:**
```
http://openai-image-gen:5000
```

**From your host machine:**
```
http://localhost:5000
```

The examples in this documentation use `http://openai-image-gen:5000` for inter-container communication. If you're calling the API from your host machine (e.g., from a terminal or local script), replace `openai-image-gen` with `localhost`.

### Remote Service

If the service is running on a remote server, update the URL in your curl commands:

```bash
# Remote server example
curl -X POST http://your-server.com:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Mountain landscape"}'
```

### Image Storage Location

Generated images are automatically saved to:
- **Container:** `/app/images/`
- **Host:** `./images/` (relative to docker-compose.yml location)

Directory structure:
```
images/
└── {job-uuid}/
    ├── 001-{image-uuid}.png
    ├── 002-{image-uuid}.png
    └── metadata.json
```

You can access images directly from the `images/` directory or via the API endpoint.

## Error Handling

### Common Errors

**Service Not Running:**
```bash
$ curl http://openai-image-gen:5000/health
curl: (7) Failed to connect to openai-image-gen port 5000: Connection refused
```

**Solution:** Start the service with `docker compose up -d`

**API Key Not Configured:**
```json
{
  "status": "unhealthy",
  "api_key_configured": false
}
```

**Solution:** Check that `secrets/openai_api_key.txt` exists and contains your API key

**Invalid Parameters:**
```json
{
  "error": "Invalid size for model dall-e-3. Must be one of: 1024x1024, 1024x1792, 1792x1024",
  "status": "failed",
  "code": "VALIDATION_ERROR"
}
```

**Solution:** Use model-appropriate parameters (see Model-Specific Parameters above)

**Rate Limiting:**
```json
{
  "error": "Rate limit exceeded",
  "status": "failed",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

**Solution:** Wait for the time specified in the `Retry-After` header before retrying

**Image Not Found:**
```json
{
  "error": "Image not found",
  "status": "failed",
  "code": "IMAGE_NOT_FOUND"
}
```

**Solution:** Verify the image ID is correct and the image hasn't been deleted

### Error Response Format

All errors return JSON in this format:
```json
{
  "error": "Error message description",
  "status": "failed",
  "code": "ERROR_CODE"
}
```

**Error Codes:**
- `VALIDATION_ERROR` (HTTP 400) - Invalid request parameters
- `IMAGE_NOT_FOUND` (HTTP 404) - Image ID not found
- `RATE_LIMIT_EXCEEDED` (HTTP 429) - OpenAI API rate limit hit
- `SERVICE_ERROR` (HTTP 500) - Configuration or internal error

## Troubleshooting

### Service Health Check

Always start troubleshooting by checking service health:

```bash
curl http://openai-image-gen:5000/health
```

**If connection refused:**
1. Check if service is running: `docker compose ps`
2. Check service logs: `docker compose logs openai-image-gen`
3. Start service: `docker compose up -d`

**If api_key_configured is false:**
1. Verify secrets file exists: `cat secrets/openai_api_key.txt`
2. Check file permissions: `chmod 600 secrets/openai_api_key.txt`
3. Verify Docker can read secret: `docker compose exec openai-image-gen cat /run/secrets/openai_api_key`
4. Restart service: `docker compose restart openai-image-gen`

### Generation Failures

**Image generation times out:**
- Increase timeout in docker-compose.yml (default: 120s)
- Try with a simpler prompt
- Check OpenAI API status

**Invalid parameters error:**
- Verify size matches model (DALL-E 2: 256x256/512x512/1024x1024, DALL-E 3: 1024x1024/1024x1792/1792x1024)
- Don't use `quality` or `style` with DALL-E 2
- DALL-E 3 count must be 1

**Insufficient credits:**
- Check your OpenAI account balance at https://platform.openai.com/account/billing

### Port Conflicts

If port 5000 is already in use:

1. Edit `docker-compose.yml`:
   ```yaml
   ports:
     - "5001:5000"  # Change host port to 5001
   ```

2. Restart service:
   ```bash
   docker compose down
   docker compose up -d
   ```

3. Update API URL in your commands:
   ```bash
   # From host machine
   curl http://localhost:5001/health

   # From containers - still uses port 5000
   curl http://openai-image-gen:5000/health
   ```

### View Service Logs

Check logs for detailed error information:

```bash
# View all logs
docker compose logs openai-image-gen

# Follow logs in real-time
docker compose logs -f openai-image-gen

# View last 50 lines
docker compose logs --tail=50 openai-image-gen
```

## Security Features

This service demonstrates the "agent tools at arm's length" pattern:

- **Credential Isolation:** OpenAI API key stored only in Docker secrets, never exposed to clients
- **Network Boundary:** All API calls go through the controlled service, not directly to OpenAI
- **Audit Trail:** All image generation requests are logged by the service
- **Input Validation:** Request parameters are validated and sanitized
- **Path Traversal Prevention:** Image IDs are sanitized before file access
- **Unprivileged Execution:** Service runs as non-root user
- **No Privilege Escalation:** Security option prevents privilege escalation

This approach allows you to use AI image generation capabilities without exposing your API credentials to client applications or scripts.

## Advanced Usage

### Programmatic Access

While these examples use curl, you can call the REST API from any programming language:

**Python Example:**
```python
import requests

response = requests.post(
    'http://openai-image-gen:5000/generate',
    json={
        'prompt': 'A beautiful landscape',
        'model': 'dall-e-3',
        'quality': 'hd'
    }
)

data = response.json()
image_id = data['images'][0]['id']

# Download image
image_response = requests.get(f'http://openai-image-gen:5000/images/{image_id}')
with open('image.png', 'wb') as f:
    f.write(image_response.content)
```

**JavaScript Example:**
```javascript
// Generate image
const response = await fetch('http://openai-image-gen:5000/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'A beautiful landscape',
    model: 'dall-e-3',
    quality: 'hd'
  })
});

const data = await response.json();
const imageId = data.images[0].id;

// Download image
const imageBlob = await fetch(`http://openai-image-gen:5000/images/${imageId}`)
  .then(r => r.blob());
```

### Batch Processing

Process multiple prompts sequentially:

```bash
#!/bin/bash

# Array of prompts
prompts=(
  "A sunset over mountains"
  "A bustling city street"
  "A peaceful forest clearing"
)

# Generate images for each prompt
for prompt in "${prompts[@]}"; do
  echo "Generating: $prompt"
  curl -s -X POST http://openai-image-gen:5000/generate \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"$prompt\", \"model\": \"dall-e-3\"}" \
    | jq -r '.images[0].id' \
    | while read image_id; do
      curl http://openai-image-gen:5000/images/$image_id \
        --output "${image_id}.png"
      echo "Saved: ${image_id}.png"
    done
done
```

## Related Resources

- **Main Documentation:** [README.md](../../README.md)
- **OpenAI DALL-E Guide:** https://platform.openai.com/docs/guides/images
- **OpenAI API Reference:** https://platform.openai.com/docs/api-reference/images
- **Docker Documentation:** https://docs.docker.com/

## Support

For issues, questions, or contributions:
- **GitHub Issues:** https://github.com/briangershon/openai-image-gen/issues
- **Repository:** https://github.com/briangershon/openai-image-gen
