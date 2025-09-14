FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    mediainfo \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy Docker environment file
COPY env.docker .env

# Set environment variables from .env file
ENV DATABASE_PATH=/app/data/watch.db
ENV MEDIA_LIBRARY_PATH=/media
ENV CACHE_ENABLED=false

# Create media and data directories
RUN mkdir -p /media /app/data

# Create non-root user
RUN useradd -m -u 1000 watch && chown -R watch:watch /app /media /app/data

# Ensure data directory has proper permissions
RUN chmod 755 /app/data

# Create startup script to fix permissions
RUN echo '#!/bin/bash\nif [ -d "/app/data" ]; then\n    chown -R watch:watch /app/data\n    chmod 755 /app/data\nfi\nsu - watch -c "cd /app && python app.py --host 0.0.0.0 --port 8080"' > /start.sh && chmod +x /start.sh

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/settings || exit 1

# Default command
CMD ["/start.sh"]
