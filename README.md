# OpenAI Image Generation Service

A production-ready Flask REST API for OpenAI DALL-E image generation, running in an isolated Docker container. Generate high-quality images using DALL-E 2 and DALL-E 3 models through a simple HTTP API.

## Features

- ✅ **RESTful HTTP API** - Simple endpoints for image generation and management
- ✅ **DALL-E 2 & 3 Support** - Full support for both OpenAI image models
- ✅ **Batch Generation** - Create multiple image variations in a single request
- ✅ **Persistent Storage** - Images saved with metadata for later retrieval
- ✅ **Production Ready** - Gunicorn with multiple workers, proper error handling
- ✅ **Security Hardened** - Unprivileged execution, input validation, secrets management
- ✅ **Minimal Dependencies** - Pure stdlib for OpenAI API calls, no official SDK needed
- ✅ **Docker Native** - Easy deployment with Docker or docker-compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/briangershon/openai-image-gen.git
   cd openai-image-gen
   ```

2. **Set your OpenAI API key**

   ```bash
   echo "OPENAI_API_KEY=sk-proj-your-key-here" > .env
   ```

3. **Start the service**

   ```bash
   docker-compose up -d
   ```

4. **Test the service**
   ```bash
   curl http://localhost:5000/health
   ```

That's it! The service is now running at `http://localhost:5000`.

### Using Pre-built Image

Pull and run the pre-built image from GitHub Container Registry:

```bash
docker pull ghcr.io/briangershon/openai-image-gen:latest

docker run -d \
  -p 5000:5000 \
  -e OPENAI_API_KEY=your-key-here \
  -v $(pwd)/images:/app/images-host \
  --name openai-image-gen \
  ghcr.io/briangershon/openai-image-gen:latest
```

## API Reference

### Health Check

Check service status and API key configuration:

```bash
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "api_key_configured": true,
  "timestamp": "2026-02-16T10:30:00.000000"
}
```

### Generate Images

Generate one or more images from a text prompt:

```bash
POST /generate
Content-Type: application/json

{
  "prompt": "A serene mountain landscape at sunset",
  "count": 1,
  "model": "dall-e-3",
  "size": "1024x1024",
  "quality": "standard",
  "style": "vivid"
}
```

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

### Retrieve Image

Download a generated image by its ID:

```bash
GET /images/<image_id>
```

Returns: Binary PNG image data

**Example:**

```bash
curl http://localhost:5000/images/7c9e6679-7425-40de-944b-e07fc1f90ae7 \
  --output myimage.png
```

### Delete Image

Remove a generated image:

```bash
DELETE /images/<image_id>
```

**Response:**

```json
{
  "status": "success",
  "message": "Image 7c9e6679-7425-40de-944b-e07fc1f90ae7 deleted"
}
```

## Usage Examples

### Generate HD Quality Image (DALL-E 3)

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A photorealistic portrait of a wise old tree",
    "model": "dall-e-3",
    "size": "1024x1792",
    "quality": "hd",
    "style": "natural"
  }'
```

### Generate Multiple Variations (DALL-E 2)

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Abstract geometric patterns",
    "count": 4,
    "model": "dall-e-2",
    "size": "512x512"
  }'
```

### Download and Save Image

```bash
# Generate image and extract ID
RESPONSE=$(curl -s -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Beautiful sunset", "model": "dall-e-2"}')

IMAGE_ID=$(echo $RESPONSE | jq -r '.images[0].id')

# Download the image
curl http://localhost:5000/images/$IMAGE_ID --output sunset.png
```

## Model-Specific Parameters

### DALL-E 3

- **Sizes**: `1024x1024`, `1024x1792`, `1792x1024`
- **Quality**: `standard` (default), `hd`
- **Style**: `vivid` (default), `natural`
- **Count**: 1 image per request (service handles sequential batching)

### DALL-E 2

- **Sizes**: `256x256`, `512x512`, `1024x1024`
- **Quality**: Not applicable
- **Style**: Not applicable
- **Count**: Up to 10 images per request (true batch generation)

## Configuration

### Environment Variables

| Variable         | Required | Description         | Default |
| ---------------- | -------- | ------------------- | ------- |
| `OPENAI_API_KEY` | Yes      | Your OpenAI API key | None    |

### Docker Compose Configuration

The `docker-compose.yml` file includes:

- **Port Mapping**: Exposes port 5000 to host
- **Volume Mounts**:
  - Named volume `image-data` for persistent storage
  - Bind mount `./images` for easy host access
- **Security**: No new privileges, tmpfs for temporary files
- **Restart Policy**: Automatically restarts unless stopped

### Image Storage

Generated images are stored in two locations:

1. **Named Volume** (`image-data`): Persistent storage across container restarts
2. **Host Mount** (`./images`): Direct access from your host machine

File structure:

```
images/
└── <job-uuid>/
    ├── 001-<image-uuid>.png
    ├── 002-<image-uuid>.png
    └── metadata.json
```

Each job creates a directory containing all generated images and a metadata file with generation parameters.

## Development

### Project Structure

```
openai-image-gen/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Compose configuration
├── .dockerignore          # Build optimization
├── image-gen/             # Application code
│   ├── app.py            # Flask REST API
│   ├── image_generator.py # OpenAI integration
│   └── requirements.txt   # Python dependencies
├── .github/
│   └── workflows/
│       └── docker-publish.yml  # CI/CD pipeline
└── images/                # Generated images (host mount)
```

### Building Locally

```bash
# Build the image
docker build -t openai-image-gen .

# Run the container
docker run -d \
  -p 5000:5000 \
  -e OPENAI_API_KEY=your-key-here \
  -v $(pwd)/images:/app/images-host \
  --name openai-image-gen \
  openai-image-gen
```

### Local Development Without Docker

```bash
cd image-gen

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY=your-key-here

# Run with Flask development server
flask run --host=0.0.0.0 --port=5000

# Or run with Gunicorn (production)
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
```

### Running Tests

```bash
# Health check
curl http://localhost:5000/health

# Generate test image
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test image", "model": "dall-e-2", "size": "256x256"}'

# Verify image was saved
ls -lh images/
```

## Security Features

- ✅ **Unprivileged Execution** - Runs as user `imagegen`, not root
- ✅ **No Privilege Escalation** - `no-new-privileges:true` security option
- ✅ **Input Validation** - All request parameters validated and sanitized
- ✅ **Path Traversal Prevention** - Image IDs sanitized before file access
- ✅ **Environment-based Secrets** - API key from environment, not hardcoded
- ✅ **Isolated Temp Files** - Temporary files in isolated tmpfs mount
- ✅ **Minimal Dependencies** - Only Flask, Werkzeug, and Gunicorn required
- ✅ **No OpenAI SDK** - Uses stdlib urllib for minimal attack surface

## Error Handling

The service returns standardized JSON error responses:

```json
{
  "error": "Error message",
  "status": "failed",
  "code": "ERROR_CODE"
}
```

### Error Codes

| Code                  | HTTP Status | Description                     |
| --------------------- | ----------- | ------------------------------- |
| `VALIDATION_ERROR`    | 400         | Invalid request parameters      |
| `IMAGE_NOT_FOUND`     | 404         | Image ID not found              |
| `RATE_LIMIT_EXCEEDED` | 429         | OpenAI API rate limit hit       |
| `SERVICE_ERROR`       | 500         | Configuration or internal error |

### Rate Limiting

When hitting OpenAI's rate limits, the response includes a `Retry-After` header indicating when to retry.

## Troubleshooting

### Service Not Responding

Check container status and logs:

```bash
docker-compose ps
docker-compose logs openai-image-gen

# Restart the service
docker-compose restart openai-image-gen
```

### API Key Issues

Verify your API key is configured correctly:

```bash
# Check health endpoint
curl http://localhost:5000/health

# If api_key_configured is false, check your .env file
cat .env

# Restart after fixing
docker-compose restart openai-image-gen
```

### Image Generation Fails

Common issues and solutions:

1. **Invalid parameters** - Check model-specific size requirements
2. **Rate limiting** - Wait for the time specified in `Retry-After` header
3. **Insufficient credits** - Check your OpenAI account balance
4. **Timeout** - Increase Gunicorn timeout for large batches (default: 120s)

### Port Already in Use

If port 5000 is already in use, change it in `docker-compose.yml`:

```yaml
ports:
  - "5001:5000" # Change host port to 5001
```

### Permission Issues

If you encounter permission errors with mounted volumes:

```bash
# Fix directory permissions
chmod 755 images/
```

## Logging

View container logs:

```bash
# View all logs
docker-compose logs openai-image-gen

# Follow logs in real-time
docker-compose logs -f openai-image-gen

# View last 50 lines
docker-compose logs --tail=50 openai-image-gen
```

Log format:

```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:5000
[INFO] Using worker: sync
[INFO] Booting worker with pid: 8
[INFO] Booting worker with pid: 9
```

## Dependencies

- **Python 3.11** - Base runtime
- **Flask 3.0.0** - Web framework
- **Werkzeug 3.0.1** - WSGI utility library
- **Gunicorn 21.2.0** - Production WSGI server
- **No OpenAI SDK** - Direct API calls using stdlib

Minimal dependencies reduce attack surface and simplify maintenance.

## Architecture

```
┌─────────────────────────────────────────┐
│ Client (curl, browser, script)          │
└──────────────┬──────────────────────────┘
               │ HTTP
               ▼
┌─────────────────────────────────────────┐
│ Docker Container                         │
│  ┌───────────────────────────────────┐  │
│  │ Gunicorn (2 workers)              │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ Flask App (app.py)          │  │  │
│  │  │  └─ OpenAI API Integration  │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
│               │                          │
│               ▼                          │
│  ┌───────────────────────────────────┐  │
│  │ Image Storage (/app/images)       │  │
│  └───────────────────────────────────┘  │
│               │                          │
└───────────────┼──────────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Host Filesystem       │
    │ (./images/)           │
    └───────────────────────┘
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/docker-publish.yml`) that:

- **Triggers on**:
  - Push to `main` branch
  - Version tags (`v*.*.*`)
  - Pull requests (build only, no push)

- **Publishes to**: GitHub Container Registry (`ghcr.io/briangershon/openai-image-gen`)

- **Image Tags**:
  - `main` - Latest main branch build
  - `main-sha-abc1234` - Specific commit
  - `1.2.3`, `1.2`, `1` - Semantic version tags
  - `pr-123` - Pull request builds (not pushed)

- **Features**:
  - Docker Buildx for multi-platform builds
  - Layer caching for faster builds
  - Automatic metadata extraction
  - PR validation without publishing

### Creating a Release

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# GitHub Actions will automatically build and publish
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/briangershon/openai-image-gen/issues)
- **Documentation**: See this README for comprehensive usage guide
- **OpenAI API**: Check [OpenAI's documentation](https://platform.openai.com/docs/api-reference/images) for API details

## Related Links

- [OpenAI Platform](https://platform.openai.com/)
- [DALL-E Documentation](https://platform.openai.com/docs/guides/images)
- [Docker Documentation](https://docs.docker.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
