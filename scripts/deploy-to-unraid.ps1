# Deploy Watch Media Server to Unraid
# This script copies the updated template to your Unraid server

$unraidIP = "192.168.254.14"
$unraidUser = "root"
$templateFile = "watch-template-unraid.xml"

Write-Host "Deploying Watch Media Server template to Unraid..." -ForegroundColor Green

# Check if template file exists
if (-not (Test-Path $templateFile)) {
    Write-Host "Error: Template file $templateFile not found!" -ForegroundColor Red
    exit 1
}

# Copy template to Unraid server
Write-Host "Copying template to Unraid server..." -ForegroundColor Yellow
scp $templateFile $unraidUser@$unraidIP`:/tmp/

if ($LASTEXITCODE -eq 0) {
    Write-Host "Template copied successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Access your Unraid web interface: http://$unraidIP" -ForegroundColor White
    Write-Host "2. Go to Docker tab" -ForegroundColor White
    Write-Host "3. Click 'Add Container' -> 'Template'" -ForegroundColor White
    Write-Host "4. Click 'Import' and select the template file" -ForegroundColor White
    Write-Host "5. Configure paths and start the container" -ForegroundColor White
    Write-Host "6. Access the application at: http://$unraidIP`:8080" -ForegroundColor White
} else {
    Write-Host "Error copying template file!" -ForegroundColor Red
    Write-Host "Please check your SSH connection to the Unraid server." -ForegroundColor Yellow
}
