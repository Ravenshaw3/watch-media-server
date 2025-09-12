@echo off
REM Trigger Docker Build via GitHub Actions

echo Triggering Docker Build via GitHub Actions
echo ==========================================
echo.

REM Check if Git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed. Please install Git first.
    pause
    exit /b 1
)

echo [INFO] Git is available
git --version

echo.
echo [INFO] Adding all changes...

REM Add all changes
git add .

echo.
echo [INFO] Creating commit to trigger build...

REM Create commit
git commit -m "Trigger Docker build - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

echo.
echo [INFO] Pushing to GitHub to trigger build...

REM Push to GitHub
git push origin main

if %errorlevel% neq 0 (
    echo [ERROR] Failed to push to GitHub
    echo Make sure you have set up the repository correctly
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Changes pushed to GitHub!
echo.
echo Next steps:
echo 1. Go to https://github.com/Ravenshaw3/watch-media-server/actions
echo 2. Watch the workflow build your Docker image
echo 3. Check https://hub.docker.com/r/ravenshaw3/watch-media-server
echo 4. Your image will be available for Unraid users!
echo.
pause
