@echo off
REM Build and Push Watch Media Server to Docker Hub

echo Building and Pushing Watch Media Server to Docker Hub
echo =====================================================
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

REM Build the image
docker build -t ravenshaw3/watch-media-server:latest .

if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker image
    pause
    exit /b 1
)

echo [INFO] Docker image built successfully!

echo.
echo [INFO] Tagging image for Docker Hub...
docker tag ravenshaw3/watch-media-server:latest ravenshaw3/watch-media-server:1.0.0

echo.
echo [INFO] Logging into Docker Hub...
echo Please enter your Docker Hub credentials when prompted:
docker login

if %errorlevel% neq 0 (
    echo [ERROR] Failed to login to Docker Hub
    pause
    exit /b 1
)

echo.
echo [INFO] Pushing images to Docker Hub...

REM Push latest tag
docker push ravenshaw3/watch-media-server:latest

if %errorlevel% neq 0 (
    echo [ERROR] Failed to push latest image
    pause
    exit /b 1
)

REM Push version tag
docker push ravenshaw3/watch-media-server:1.0.0

if %errorlevel% neq 0 (
    echo [ERROR] Failed to push versioned image
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Docker images pushed to Docker Hub successfully!
echo.
echo Your images are now available at:
echo - https://hub.docker.com/r/ravenshaw3/watch-media-server
echo.
echo Unraid users can now use your template to automatically download the image.
echo.
pause
