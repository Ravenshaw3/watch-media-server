@echo off
REM Watch Media Server Setup Script for Windows
REM This script helps set up the Watch Media Server on Windows

echo Watch Media Server Setup
echo ========================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)
echo [INFO] Docker is installed
docker --version

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)
echo [INFO] Docker Compose is installed
docker-compose --version

echo.
echo [INFO] Creating directories...

REM Create necessary directories
if not exist "media" mkdir media
if not exist "data" mkdir data
if not exist "config" mkdir config

echo [INFO] Directories created:
echo   - media\ (for your media files)
echo   - data\ (for database and logs)
echo   - config\ (for configuration files)

echo.
echo [INFO] Setting up environment...

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo # Watch Media Server Environment Variables > .env
    echo MEDIA_LIBRARY_PATH=/media >> .env
    echo TZ=UTC >> .env
    echo. >> .env
    echo # Optional: Custom port (default is 8080) >> .env
    echo # PORT=8080 >> .env
    echo. >> .env
    echo # Optional: Enable debug mode >> .env
    echo # DEBUG=false >> .env
    echo [INFO] Created .env file with default settings
) else (
    echo [WARNING] .env file already exists, skipping creation
)

echo.
echo [INFO] Building Docker image...

REM Build Docker image
docker build -t watch-media-server .
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker image
    pause
    exit /b 1
)
echo [INFO] Docker image built successfully

echo.
echo [INFO] Starting Watch Media Server...

REM Start the application
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Watch Media Server
    pause
    exit /b 1
)

echo [INFO] Watch Media Server started successfully
echo.
echo [INFO] Access the web interface at: http://localhost:8080
echo [INFO] To view logs: docker-compose logs -f
echo [INFO] To stop: docker-compose down

echo.
echo ========================
echo Setup Complete!
echo ========================
echo.
echo Next steps:
echo 1. Add your media files to the 'media' directory
echo 2. Open http://localhost:8080 in your browser
echo 3. Click 'Scan Library' to index your media
echo 4. Enjoy your media library!
echo.
echo For Unraid users, see the unraid-template.xml file for setup instructions.
echo.
pause
