# Unraid Installation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    UNRAID INSTALLATION FLOW                 │
└─────────────────────────────────────────────────────────────┘

1. PREPARATION
   ├── Ensure Unraid 6.8+ is running
   ├── Verify Docker plugin is installed
   ├── Create media directory: /mnt/user/media/
   └── Add your movies and TV shows to the directory

2. DOWNLOAD TEMPLATE
   ├── Download watch-template.xml
   └── Save to your local computer

3. ACCESS UNRAID DOCKER
   ├── Open Unraid web interface
   ├── Click "Docker" tab
   └── Click "Add Container"

4. IMPORT TEMPLATE
   ├── Select "Template" from dropdown
   ├── Click "Import" button
   ├── Browse and select watch-template.xml
   └── Click "Import"

5. CONFIGURE CONTAINER
   ├── Name: watch-media-server
   ├── Repository: watch-media-server:latest
   ├── Network: bridge
   ├── Port: 8080:8080
   ├── Volumes:
   │   ├── /mnt/user/media → /media (ro)
   │   ├── /mnt/user/appdata/watch → /app/data (rw)
   │   └── /mnt/user/appdata/watch/config → /app/config (rw)
   └── Environment:
       ├── TZ = Your_Timezone
       └── MEDIA_LIBRARY_PATH = /media

6. START CONTAINER
   ├── Click "Apply" to save settings
   ├── Click "Start" button
   └── Wait for container to start (1-2 minutes)

7. ACCESS WEB INTERFACE
   ├── Open browser
   ├── Navigate to: http://YOUR_UNRAID_IP:8080
   └── You should see the Watch dashboard

8. INITIAL SETUP
   ├── Click "Settings" to configure preferences
   ├── Verify media library path
   └── Click "Scan Library" to index your media

9. VERIFY INSTALLATION
   ├── Check that media files appear in the interface
   ├── Test playback by clicking on a media file
   └── Browse using Movies/TV Shows/All tabs

┌─────────────────────────────────────────────────────────────┐
│                    TROUBLESHOOTING                          │
└─────────────────────────────────────────────────────────────┘

Common Issues:
├── Container won't start
│   ├── Check if port 8080 is in use
│   ├── Verify volume paths exist
│   └── Check container logs
├── Media not appearing
│   ├── Verify media library path
│   ├── Check file permissions
│   ├── Ensure supported file formats
│   └── Run manual scan
└── Playback issues
    ├── Check browser compatibility
    ├── Verify file formats
    └── Check container logs

┌─────────────────────────────────────────────────────────────┐
│                    CONFIGURATION SUMMARY                    │
└─────────────────────────────────────────────────────────────┘

Container Settings:
├── Name: watch-media-server
├── Image: watch-media-server:latest
├── Network: bridge
├── Port: 8080:8080
├── Volumes:
│   ├── Media: /mnt/user/media → /media (read-only)
│   ├── Data: /mnt/user/appdata/watch → /app/data (read-write)
│   └── Config: /mnt/user/appdata/watch/config → /app/config (read-write)
└── Environment:
    ├── TZ: Your timezone (e.g., America/New_York)
    └── MEDIA_LIBRARY_PATH: /media

Web Interface:
├── URL: http://YOUR_UNRAID_IP:8080
├── Default port: 8080
└── Access: Any device with web browser

Console Interface:
├── Access: Docker tab → Container → Console
├── Command: python app.py --console
└── Features: Library management, statistics, direct playback
