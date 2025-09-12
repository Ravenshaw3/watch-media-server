FROM python:3.11-slim

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

# Create media directory
RUN mkdir -p /media

# Create non-root user
RUN useradd -m -u 1000 watch && chown -R watch:watch /app /media
USER watch

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/settings || exit 1

# Default command
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "8080"]
