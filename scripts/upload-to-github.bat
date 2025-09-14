@echo off
REM Watch Media Server - GitHub Upload Script
REM This script helps upload your project to GitHub

echo Watch Media Server - GitHub Upload
echo ==================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed. Please install Git first.
    echo Download from: https://git-scm.com/downloads
    pause
    exit /b 1
)
echo [INFO] Git is installed
git --version

echo.
echo [INFO] Initializing Git repository...

REM Initialize Git repository
git init

echo.
echo [INFO] Adding all files to Git...

REM Add all files
git add .

echo.
echo [INFO] Creating initial commit...

REM Create initial commit
git commit -m "Initial commit: Watch Media Server v1.0.0"

echo.
echo [INFO] Git repository initialized successfully!
echo.

echo Next steps:
echo 1. Go to GitHub.com and create a new repository named 'watch-media-server'
echo 2. Copy the repository URL (e.g., https://github.com/username/watch-media-server.git)
echo 3. Run the following commands:
echo.
echo    git remote add origin https://github.com/Ravenshaw3/watch-media-server
echo    git branch -M main
echo    git push -u origin main
echo.

echo [INFO] Repository is ready for GitHub upload!
echo.
echo For detailed instructions, see GITHUB_SETUP.md
echo.
pause
