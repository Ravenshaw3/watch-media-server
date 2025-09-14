# Watch Media Server - Unraid Installation Guide

## 📋 Prerequisites

Before starting, ensure you have:
- Unraid server running (version 6.8+ recommended)
- Docker plugin installed and enabled
- At least 1GB of free RAM
- Media files organized in a directory on your Unraid server

## 🚀 Step-by-Step Installation

### Step 1: Prepare Your Media Directory

1. **Create Media Directory** (if not already done):
   - Open Unraid web interface
   - Go to **Main** tab
   - Navigate to your desired location (e.g., `/mnt/user/media/`)
   - Create folders for your media:
     ```
     /mnt/user/media/
     ├── Movies/
     ├── TV Shows/
     └── Other/
     ```

2. **Add Your Media Files**:
   - Copy your movies and TV shows to the appropriate folders
   - Supported formats: MP4, AVI, MKV, MOV, WMV, FLV, WebM

### Step 2: Download the Unraid Template

1. **Download Template File**:
   - Download `watch-template.xml` from the project
   - Save it to your local computer (not on Unraid server)

2. **Alternative: Manual Template Creation**:
   - If you prefer, you can manually create the container using the settings below

### Step 3: Install Watch Media Server

#### Option A: Using Template File (Recommended)

1. **Access Docker Tab**:
   - Open Unraid web interface
   - Click on **Docker** tab

2. **Add Container**:
   - Click **Add Container** button
   - Select **Template** from the dropdown

3. **Import Template**:
   - Click **Import** button
   - Browse and select the `watch-template.xml` file
   - Click **Import**

4. **Configure Container**:
   - The template will populate with default settings
   - Review and modify the following settings:

#### Option B: Manual Container Creation

1. **Add Container**:
   - Go to **Docker** tab
   - Click **Add Container**

2. **Basic Settings**:
   ```
   Name: watch-media-server
   Repository: watch-media-server:latest
   ```

3. **Network Settings**:
   ```
   Network Type: bridge
   Port: 8080 (Host) → 8080 (Container)
   ```

4. **Volume Mappings**:
   ```
   /mnt/user/media → /media (read-only)
   /mnt/user/appdata/watch → /app/data (read-write)
   /mnt/user/appdata/watch/config → /app/config (read-write)
   ```

5. **Environment Variables**:
   ```
   TZ = America/New_York (or your timezone)
   MEDIA_LIBRARY_PATH = /media
   ```

### Step 4: Configure Container Settings

1. **WebUI Port**:
   - Set to `8080` (or your preferred port)
   - Ensure the port is not in use by other containers

2. **Media Library Path**:
   - Set to `/mnt/user/media` (or your media directory)
   - This should be the parent directory containing your Movies/TV Shows folders

3. **Data Directory**:
   - Set to `/mnt/user/appdata/watch`
   - This stores the database and logs

4. **Config Directory**:
   - Set to `/mnt/user/appdata/watch/config`
   - This stores configuration files (optional)

### Step 5: Start the Container

1. **Apply Settings**:
   - Review all settings
   - Click **Apply** to save the configuration

2. **Start Container**:
   - Click **Start** button
   - Wait for the container to start (may take 1-2 minutes on first run)

3. **Verify Installation**:
   - Check container status in Docker tab
   - Should show "Up" status
   - Click the container name to view logs if needed

### Step 6: Access the Web Interface

1. **Open Web Interface**:
   - Open your web browser
   - Navigate to: `http://YOUR_UNRAID_IP:8080`
   - Example: `http://192.168.1.100:8080`

2. **Initial Setup**:
   - You should see the Watch Media Server dashboard
   - Click **Settings** to configure your preferences
   - Set your media library path if different from default

### Step 7: Scan Your Media Library

1. **Start Library Scan**:
   - Click **Scan Library** button on the main page
   - Wait for the scan to complete (time depends on library size)

2. **Monitor Progress**:
   - Watch the status messages at the top of the page
   - Check the statistics bar for file counts

3. **Verify Results**:
   - Browse your media using the tabs (Movies, TV Shows, All)
   - Test playback by clicking on a media file

## 🔧 Configuration Options

### Web Interface Settings

1. **Access Settings**:
   - Click the **Settings** button (gear icon)
   - Modify the following options:

2. **Library Settings**:
   ```
   Media Library Path: /media
   Auto Scan: Enabled/Disabled
   Scan Interval: 3600 seconds (1 hour)
   Supported Formats: mp4,avi,mkv,mov,wmv,flv,webm
   ```

3. **Playback Settings**:
   ```
   Transcoding: Enabled/Disabled
   Max Resolution: 1080p
   ```

### Console Interface (Advanced)

1. **Access Console**:
   - Go to Unraid Docker tab
   - Click on the Watch container
   - Click **Console** button

2. **Available Commands**:
   ```bash
   python app.py --console
   help                    # Show available commands
   scan                    # Scan media library
   list                    # List media files
   stats                   # Show library statistics
   search <query>          # Search for media
   settings                # Show current settings
   ```

## 🛠 Troubleshooting

### Common Issues

1. **Container Won't Start**:
   - Check if port 8080 is already in use
   - Verify all volume paths exist
   - Check container logs for error messages

2. **Media Not Appearing**:
   - Verify media library path is correct
   - Check file permissions on media directory
   - Ensure files are in supported formats
   - Run manual scan from web interface

3. **Playback Issues**:
   - Check browser compatibility
   - Verify file formats are supported
   - Try different media files
   - Check container logs for errors

4. **Performance Issues**:
   - Monitor RAM usage in Unraid dashboard
   - Consider increasing container memory limit
   - Check disk I/O performance

### Logs and Debugging

1. **View Container Logs**:
   - Docker tab → Watch container → Logs
   - Look for error messages or warnings

2. **Application Logs**:
   - Located in `/mnt/user/appdata/watch/watch.log`
   - Access via Unraid file manager or console

3. **Database**:
   - Located in `/mnt/user/appdata/watch/watch.db`
   - Can be accessed with SQLite tools if needed

## 🔄 Updates and Maintenance

### Updating the Container

1. **Check for Updates**:
   - Go to Docker tab
   - Look for update notifications
   - Or manually check for new versions

2. **Update Process**:
   - Stop the container
   - Delete the old container (keep data)
   - Recreate with new image
   - Start the container

### Backup Recommendations

1. **Database Backup**:
   - Regularly backup `/mnt/user/appdata/watch/watch.db`
   - This contains all your media metadata

2. **Configuration Backup**:
   - Backup `/mnt/user/appdata/watch/config/` directory
   - Contains your custom settings

## 📊 Performance Tips

1. **Optimize for Large Libraries**:
   - Increase scan interval for large libraries
   - Use SSD for appdata directory if possible
   - Consider RAM allocation for container

2. **Network Optimization**:
   - Use wired connection for best streaming performance
   - Consider network bandwidth for multiple concurrent streams

3. **Storage Optimization**:
   - Keep media files on fast storage (SSD recommended)
   - Use cache drives for frequently accessed files

## 🆘 Support

If you encounter issues:

1. **Check Logs**: Review container and application logs
2. **Verify Settings**: Ensure all paths and ports are correct
3. **Test Network**: Verify web interface accessibility
4. **Community Support**: Check Unraid forums or project repository

## ✅ Installation Complete!

Once everything is working:

- Your media library is automatically scanned and organized
- Access your media from any device with a web browser
- Use the console interface for advanced management
- Enjoy your personal media server!

---

**Need Help?** Check the main README.md for additional information and troubleshooting tips.
