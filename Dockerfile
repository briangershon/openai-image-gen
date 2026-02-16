FROM python:3.11-slim

# Install system dependencies (minimal, following agent pattern)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tini \
  && rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN useradd -m -s /bin/bash imagegen

# Copy application code
COPY --chown=imagegen:imagegen image-gen/ /app/

# Install Python dependencies
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Create images directory
RUN mkdir -p /app/images && chown imagegen:imagegen /app/images

USER imagegen

EXPOSE 5000

# Use tini for signal handling (project pattern)
ENTRYPOINT ["tini", "--"]

# Run with gunicorn (2 workers, 120s timeout for slow image generation)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
