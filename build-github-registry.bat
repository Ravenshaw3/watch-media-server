@echo off
REM Build and Push Watch Media Server to GitHub Container Registry

echo Building and Pushing to GitHub Container Registry
echo ================================================
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [INFO] Docker is running
docker --version

echo.
echo [INFO] Building Docker image...

REM Build the image for GitHub Container Registry
docker build -t ghcr.io/ravenshaw3/watch-media-server:latest .

if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker image
    pause
    exit /b 1
)

echo [INFO] Docker image built successfully!

echo.
echo [INFO] Tagging image for GitHub Container Registry...
docker tag ghcr.io/ravenshaw3/watch-media-server:latest ghcr.io/ravenshaw3/watch-media-server:1.0.0

echo.
echo [INFO] Logging into GitHub Container Registry...
echo Please enter your GitHub Personal Access Token when prompted:
echo (Username: ravenshaw3, Password: your_github_token)
docker login ghcr.io

if %errorlevel% neq 0 (
    echo [ERROR] Failed to login to GitHub Container Registry
    echo Make sure you have a GitHub Personal Access Token with packages:write permission
    pause
    exit /b 1
)

echo.
echo [INFO] Pushing images to GitHub Container Registry...

REM Push latest tag
docker push ghcr.io/ravenshaw3/watch-media-server:latest

if %errorlevel% neq 0 (
    echo [ERROR] Failed to push latest image
    pause
    exit /b 1
)

REM Push version tag
docker push ghcr.io/ravenshaw3/watch-media-server:1.0.0

if %errorlevel% neq 0 (
    echo [ERROR] Failed to push versioned image
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Docker images pushed to GitHub Container Registry successfully!
echo.
echo Your images are now available at:
echo - https://github.com/Ravenshaw3/watch-media-server/pkgs/container/watch-media-server
echo.
echo Note: You'll need to update the template to use ghcr.io/ravenshaw3/watch-media-server:latest
echo.
pause
