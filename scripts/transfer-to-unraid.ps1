# PowerShell script to transfer files to Unraid server
# Run this from your local Windows machine

$unraidIP = "192.168.254.14"
$unraidUser = "root"
$localPath = "P:\Watch"
$remotePath = "/tmp/watch-build"

Write-Host "Transferring Watch Media Server files to Unraid server..." -ForegroundColor Green

# Create remote directory
Write-Host "Creating remote directory..." -ForegroundColor Yellow
ssh $unraidUser@$unraidIP "mkdir -p $remotePath"

# Transfer files using rsync (if available) or scp
Write-Host "Transferring files..." -ForegroundColor Yellow

# Try rsync first (faster and more efficient)
try {
    rsync -avz --exclude='.git' --exclude='test-data' --exclude='test-media' --exclude='*.log' $localPath/ $unraidUser@$unraidIP`:$remotePath/
    Write-Host "Files transferred successfully using rsync!" -ForegroundColor Green
} catch {
    Write-Host "rsync not available, using scp..." -ForegroundColor Yellow
    
    # Fallback to scp for individual files
    $filesToTransfer = @(
        "main.py",
        "requirements.txt",
        "Dockerfile",
        "env.docker",
        "wsgi.py"
    )
    
    foreach ($file in $filesToTransfer) {
        if (Test-Path "$localPath\$file") {
            Write-Host "Transferring $file..." -ForegroundColor Yellow
            scp "$localPath\$file" $unraidUser@$unraidIP`:$remotePath/
        }
    }
    
    # Transfer directories
    $dirsToTransfer = @(
        "src",
        "static",
        "templates",
        "tests"
    )
    
    foreach ($dir in $dirsToTransfer) {
        if (Test-Path "$localPath\$dir") {
            Write-Host "Transferring $dir directory..." -ForegroundColor Yellow
            scp -r "$localPath\$dir" $unraidUser@$unraidIP`:$remotePath/
        }
    }
    
    Write-Host "Files transferred successfully using scp!" -ForegroundColor Green
}

Write-Host "Transfer complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. SSH into your Unraid server: ssh $unraidUser@$unraidIP" -ForegroundColor White
Write-Host "2. Run the setup script: bash $remotePath/scripts/setup-unraid.sh" -ForegroundColor White
Write-Host "3. Start the application: cd /mnt/user/appdata/watch-media-server && docker-compose up -d" -ForegroundColor White
