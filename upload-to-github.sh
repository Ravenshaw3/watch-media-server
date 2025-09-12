#!/bin/bash

# Watch Media Server - GitHub Upload Script
# This script helps upload your project to GitHub

echo "Watch Media Server - GitHub Upload"
echo "=================================="
echo

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git is not installed. Please install Git first."
    echo "Installation instructions:"
    echo "  Ubuntu/Debian: sudo apt install git"
    echo "  macOS: brew install git"
    echo "  Or download from: https://git-scm.com/downloads"
    exit 1
fi

echo "[INFO] Git is installed"
git --version

echo
echo "[INFO] Initializing Git repository..."

# Initialize Git repository
git init

echo
echo "[INFO] Adding all files to Git..."

# Add all files
git add .

echo
echo "[INFO] Creating initial commit..."

# Create initial commit
git commit -m "Initial commit: Watch Media Server v1.0.0"

echo
echo "[INFO] Git repository initialized successfully!"
echo

echo "Next steps:"
echo "1. Go to GitHub.com and create a new repository named 'watch-media-server'"
echo "2. Copy the repository URL (e.g., https://github.com/username/watch-media-server.git)"
echo "3. Run the following commands:"
echo
echo "   git remote add origin YOUR_REPOSITORY_URL"
echo "   git branch -M main"
echo "   git push -u origin main"
echo

echo "[INFO] Repository is ready for GitHub upload!"
echo
echo "For detailed instructions, see GITHUB_SETUP.md"
echo
