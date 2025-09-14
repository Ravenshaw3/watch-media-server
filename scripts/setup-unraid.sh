#!/bin/bash

# Watch Media Server - Unraid Setup Script
# Run this script on your Unraid server (192.168.254.14)

set -e

echo "Setting up Watch Media Server on Unraid..."

# Create directories
echo "Creating directories..."
mkdir -p /mnt/user/media
mkdir -p /mnt/user/appdata/watch-media-server
mkdir -p /tmp/watch-build

# Set permissions
echo "Setting permissions..."
chmod 755 /mnt/user/media
chmod 755 /mnt/user/appdata/watch-media-server

# Clone or copy the repository
echo "Setting up build environment..."
cd /tmp/watch-build

# If you have git installed, you can clone:
# git clone https://github.com/your-username/watch-media-server.git .

# Or copy files from your local machine:
echo "Please copy the project files to /tmp/watch-build on your Unraid server"
echo "You can use scp, rsync, or any other method to transfer files"

# Install build dependencies
echo "Installing build dependencies..."
apt-get update
apt-get install -y git curl

# Build the Docker image
echo "Building Docker image..."
docker build -t watch-media-server:latest .

# Create docker-compose file for easy management
cat > /mnt/user/appdata/watch-media-server/docker-compose.yml << EOF
version: '3.8'

services:
  watch-media-server:
    image: watch-media-server:latest
    container_name: watch-media-server
    ports:
      - "8080:8080"
    volumes:
      - /mnt/user/media:/media
      - /mnt/user/appdata/watch-media-server:/app/data
    environment:
      - DATABASE_PATH=/app/data/watch.db
      - MEDIA_LIBRARY_PATH=/media
      - CACHE_ENABLED=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

echo "Setup complete!"
echo "To start the application:"
echo "cd /mnt/user/appdata/watch-media-server"
echo "docker-compose up -d"
echo ""
echo "To access the application:"
echo "http://192.168.254.14:8080"
