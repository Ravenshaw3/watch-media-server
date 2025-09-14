# Watch Media Server - Unraid Setup Guide

## Prerequisites

- Unraid server running (IP: 192.168.254.14)
- SSH access to the Unraid server
- Media files located at `/mnt/user/media`
- App data will be stored at `/mnt/user/appdata/watch-media-server`

## Step 1: Install Docker on Unraid

SSH into your Unraid server and install Docker:

```bash
ssh root@192.168.254.14

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Start Docker service
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
```

## Step 2: Transfer Project Files

From your local Windows machine, run the transfer script:

```powershell
# In PowerShell, from the Watch project directory
.\scripts\transfer-to-unraid.ps1
```

Or manually transfer files using SCP:

```bash
# Transfer the entire project (excluding test files)
scp -r -o "StrictHostKeyChecking=no" \
  --exclude='test-data' \
  --exclude='test-media' \
  --exclude='*.log' \
  . root@192.168.254.14:/tmp/watch-build/
```

## Step 3: Build and Deploy

On your Unraid server:

```bash
# Navigate to build directory
cd /tmp/watch-build

# Make setup script executable
chmod +x scripts/setup-unraid.sh

# Run setup script
bash scripts/setup-unraid.sh

# Start the application
cd /mnt/user/appdata/watch-media-server
docker-compose up -d
```

## Step 4: Access the Application

Open your web browser and navigate to:
```
http://192.168.254.14:8080
```

## Step 5: Initial Setup

1. **Register a new user account** or use the default admin credentials
2. **Configure your media library path** in settings
3. **Start a media library scan** to index your files
4. **Enjoy your media server!**

## Alternative: Using Unraid Docker Template

If you prefer using the Unraid web interface:

1. Copy `watch-template-unraid.xml` to your Unraid server
2. In the Unraid web interface, go to Docker tab
3. Click "Add Container" → "Template"
4. Import the template file
5. Configure the paths and start the container

## Directory Structure on Unraid

```
/mnt/user/
├── media/                          # Your media files
│   ├── Movies/
│   ├── TV Shows/
│   └── ...
└── appdata/
    └── watch-media-server/         # Application data
        ├── watch.db               # SQLite database
        ├── docker-compose.yml     # Docker configuration
        └── logs/                  # Application logs
```

## Troubleshooting

### Check Container Status
```bash
docker ps
docker logs watch-media-server
```

### Restart Container
```bash
cd /mnt/user/appdata/watch-media-server
docker-compose restart
```

### Update Application
```bash
cd /tmp/watch-build
git pull  # or re-transfer files
docker build -t watch-media-server:latest .
cd /mnt/user/appdata/watch-media-server
docker-compose down
docker-compose up -d
```

### Check Media Library
```bash
# Verify media files are accessible
ls -la /mnt/user/media/
```

## Performance Tips

1. **Use SSD for appdata** - Store the database on an SSD for better performance
2. **Enable hardware transcoding** - If your CPU supports it
3. **Optimize network** - Use wired connection for best streaming performance
4. **Monitor resources** - Check CPU and memory usage during transcoding

## Security Considerations

1. **Change default passwords** - Update admin credentials
2. **Use HTTPS** - Consider setting up reverse proxy with SSL
3. **Firewall rules** - Restrict access to trusted networks only
4. **Regular updates** - Keep the application updated

## Support

- **GitHub Issues**: https://github.com/Ravenshaw3/watch-media-server/issues
- **Documentation**: Check the `docs/` directory
- **Logs**: Check container logs for troubleshooting

## Next Steps

After successful deployment:

1. **Add media files** to `/mnt/user/media/`
2. **Configure users** and permissions
3. **Set up automated scanning** schedules
4. **Explore advanced features** like transcoding and metadata management
5. **Set up monitoring** and backups
