# Watch Media Server

A comprehensive web-based media library management system for movies and TV shows, designed to run in Docker on Unraid or any Docker-compatible system.

## Features

- **Web Interface**: Modern, responsive web interface for browsing and playing media
- **Library Management**: Automatic scanning and organization of media files
- **Metadata Extraction**: Automatic extraction of media metadata using FFprobe
- **Streaming**: Built-in video streaming with HTML5 player
- **Console Interface**: Command-line interface for advanced management
- **File Organization**: Automatic file organization and renaming
- **Playlists**: Create and manage custom playlists
- **Docker Support**: Full Docker and Unraid template support
- **Real-time Updates**: WebSocket-based real-time updates

## Quick Start

### Docker Compose (Recommended)

1. Clone or download this repository
2. Create a `media` directory and place your movies/TV shows there
3. Run with Docker Compose:

```bash
docker-compose up -d
```

4. Open your browser to `http://localhost:8080`

### Unraid Template

1. Download the `watch-template.xml` file
2. In Unraid, go to Docker tab
3. Click "Add Container" and select "Template"
4. Import the template file
5. Configure your media library path
6. Start the container

### Manual Docker

```bash
# Build the image
docker build -t watch-media-server .

# Run the container
docker run -d \
  --name watch-media-server \
  -p 8080:8080 \
  -v /path/to/your/media:/media:ro \
  -v /path/to/data:/app/data \
  watch-media-server
```

## Configuration

### Environment Variables

- `MEDIA_LIBRARY_PATH`: Path to your media library (default: `/media`)
- `TZ`: Timezone (default: `UTC`)

### Volume Mounts

- `/media`: Your media library (read-only recommended)
- `/app/data`: Database and logs (persistent)
- `/app/config`: Configuration files (optional)

## Usage

### Web Interface

1. **Dashboard**: View your media library with statistics
2. **Browse**: Filter by movies, TV shows, or view all
3. **Search**: Search through your media collection
4. **Play**: Click any media to play in the built-in player
5. **Stream**: Download or stream media files
6. **Settings**: Configure library paths and scan intervals

### Console Interface

Access the console interface by running:

```bash
python app.py --console
```

Available commands:
- `help` - Show available commands
- `scan` - Scan media library
- `list` - List media files
- `stats` - Show library statistics
- `search <query>` - Search for media
- `play <id>` - Play media by ID
- `settings` - Show current settings
- `set <key> <value>` - Set configuration
- `cleanup` - Clean up database

### API Endpoints

- `GET /api/media` - Get media files
- `POST /api/scan` - Trigger library scan
- `GET /api/settings` - Get settings
- `POST /api/settings` - Update settings
- `GET /api/stream/<id>` - Stream media file
- `GET /api/play/<id>` - Play media file

## File Organization

Watch can automatically organize your media files:

### Movies
- **Pattern**: `Title (Year)/Title (Year).ext`
- **Example**: `The Matrix (1999)/The Matrix (1999).mp4`

### TV Shows
- **Pattern**: `Show Name/Season XX/Show Name - SXXEXX.ext`
- **Example**: `Breaking Bad/Season 01/Breaking Bad - S01E01.mp4`

## Supported Formats

Default supported formats:
- MP4, AVI, MKV, MOV, WMV, FLV, WebM

You can modify the supported formats in the settings.

## Requirements

- Docker (or Python 3.11+)
- FFmpeg (for metadata extraction)
- At least 1GB RAM
- Sufficient storage for your media library

## Troubleshooting

### Common Issues

1. **Media not appearing**: Check that your media path is correctly mounted and contains supported file formats
2. **Playback issues**: Ensure your browser supports the video format, or enable transcoding
3. **Scan not working**: Check file permissions and ensure FFmpeg is installed
4. **Performance issues**: Consider enabling transcoding for better compatibility

### Logs

Check the application logs:
```bash
docker logs watch-media-server
```

Or view the log file in the data directory: `watch.log`

### Database

The SQLite database is stored in the data directory. You can access it directly if needed for troubleshooting.

## Development

### Local Development

1. Install Python 3.11+
2. Install dependencies: `pip install -r requirements.txt`
3. Install FFmpeg
4. Run: `python app.py`

### Building

```bash
docker build -t watch-media-server .
```

## Security Considerations

- The application runs as a non-root user in Docker
- Media files are mounted read-only by default
- No authentication is implemented (add reverse proxy with auth if needed)
- Consider using HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. See the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Open an issue on GitHub

## Changelog

### Version 1.0.0
- Initial release
- Web interface with media browsing and playback
- Console interface for management
- Docker and Unraid support
- Automatic library scanning
- File organization features
- Playlist support
