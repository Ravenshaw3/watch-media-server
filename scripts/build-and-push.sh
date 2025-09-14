#!/bin/bash

# Build and Push Watch Media Server to Docker Hub

echo "Building and Pushing Watch Media Server to Docker Hub"
echo "====================================================="
echo

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not running."
    echo "Please install Docker and start the Docker service."
    exit 1
fi

echo "[INFO] Docker is running"
docker --version

echo
echo "[INFO] Building Docker image..."

# Build the image
docker build -t ravenshaw3/watch-media-server:latest .

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to build Docker image"
    exit 1
fi

echo "[INFO] Docker image built successfully!"

echo
echo "[INFO] Tagging image for Docker Hub..."
docker tag ravenshaw3/watch-media-server:latest ravenshaw3/watch-media-server:1.0.0

echo
echo "[INFO] Logging into Docker Hub..."
echo "Please enter your Docker Hub credentials when prompted:"
docker login

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to login to Docker Hub"
    exit 1
fi

echo
echo "[INFO] Pushing images to Docker Hub..."

# Push latest tag
docker push ravenshaw3/watch-media-server:latest

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to push latest image"
    exit 1
fi

# Push version tag
docker push ravenshaw3/watch-media-server:1.0.0

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to push versioned image"
    exit 1
    fi

echo
echo "[SUCCESS] Docker images pushed to Docker Hub successfully!"
echo
echo "Your images are now available at:"
echo "- https://hub.docker.com/r/ravenshaw3/watch-media-server"
echo
echo "Unraid users can now use your template to automatically download the image."
echo
