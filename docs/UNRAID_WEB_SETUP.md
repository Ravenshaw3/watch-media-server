# Watch Media Server - Unraid Web Interface Setup

## Method 1: Using Docker Template (Recommended)

### Step 1: Download Template
1. Copy the `watch-template-unraid.xml` file to your local machine
2. Access your Unraid web interface at `http://192.168.254.14`
3. Go to the **Docker** tab

### Step 2: Add Container
1. Click **Add Container**
2. Click **Template** (at the bottom)
3. Click **Import** and select the `watch-template-unraid.xml` file
4. The template will be imported with all the correct settings

### Step 3: Configure Paths
The template should already have these paths configured:
- **Media Library**: `/mnt/user/media` → `/media`
- **App Data**: `/mnt/user/appdata/watch-media-server` → `/app/data`
- **Port**: `8080`

### Step 4: Start Container
1. Click **Apply** to create the container
2. The container will start automatically
3. Access the application at `http://192.168.254.14:8080`

## Method 2: Manual Container Creation

### Step 1: Add Container
1. Go to **Docker** tab in Unraid web interface
2. Click **Add Container**
3. Fill in the following details:

**Basic Settings:**
- **Name**: `watch-media-server`
- **Repository**: `ravenshaw3/watch-media-server:latest`
- **Icon URL**: `https://raw.githubusercontent.com/Ravenshaw3/watch-media-server/main/static/images/icon.svg`

**Network Type**: `bridge`

**Port Mappings:**
- **Container Port**: `8080`
- **Host Port**: `8080`
- **Protocol**: `TCP`

**Path Mappings:**
- **Host Path**: `/mnt/user/media`
- **Container Path**: `/media`
- **Access Mode**: `Read/Write`

- **Host Path**: `/mnt/user/appdata/watch-media-server`
- **Container Path**: `/app/data`
- **Access Mode**: `Read/Write`

**Environment Variables:**
- **Variable**: `DATABASE_PATH`
- **Value**: `/app/data/watch.db`

- **Variable**: `MEDIA_LIBRARY_PATH`
- **Value**: `/media`

- **Variable**: `CACHE_ENABLED`
- **Value**: `false`

### Step 2: Advanced Settings
- **Restart Policy**: `Unless Stopped`
- **Enable Auto-Start**: `Yes`

### Step 3: Create and Start
1. Click **Apply** to create the container
2. The container will start automatically

## Method 3: Using Docker Compose (Advanced)

If you want to use docker-compose on Unraid:

### Step 1: Install Docker Compose Plugin
SSH into your Unraid server and install docker-compose:

```bash
ssh root@192.168.254.14

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Step 2: Create Docker Compose File
Create `/mnt/user/appdata/watch-media-server/docker-compose.yml`:

```yaml
version: '3.8'

services:
  watch-media-server:
    image: ravenshaw3/watch-media-server:latest
    container_name: watch-media-server
    ports:
      - "8080:8080"
    volumes:
      - /mnt/user/media:/media
      - /mnt/user/appdata/watch-media-server:/app/data
    environment:
      - DATABASE_PATH=/app/data/watch.db
      - MEDIA_LIBRARY_PATH=/media
      - CACHE_ENABLED=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Step 3: Start with Docker Compose
```bash
cd /mnt/user/appdata/watch-media-server
docker-compose up -d
```

## Accessing the Application

Once the container is running:

1. **Web Interface**: `http://192.168.254.14:8080`
2. **Default Admin**: 
   - Username: `admin`
   - Password: `admin123`

## Troubleshooting

### Check Container Status
In Unraid web interface:
1. Go to **Docker** tab
2. Click on **watch-media-server** container
3. Check **Logs** tab for any errors

### Common Issues

**Container won't start:**
- Check if port 8080 is already in use
- Verify the image exists: `ravenshaw3/watch-media-server:latest`
- Check logs for specific error messages

**Can't access web interface:**
- Verify the container is running
- Check port mapping (should be 8080:8080)
- Try accessing from the Unraid server itself: `http://localhost:8080`

**Media files not showing:**
- Verify media path mapping: `/mnt/user/media` → `/media`
- Check if media files exist in `/mnt/user/media`
- Start a library scan in the web interface

### Updating the Application

To update to the latest version:

1. **Stop the container** in Unraid web interface
2. **Remove the container** (this won't delete your data)
3. **Pull the latest image**: `docker pull ravenshaw3/watch-media-server:latest`
4. **Recreate the container** using the same settings

## Next Steps

After successful deployment:

1. **Add media files** to `/mnt/user/media/`
2. **Configure your media library** in the web interface
3. **Start a library scan** to index your files
4. **Create user accounts** and configure permissions
5. **Explore the features** and customize settings
