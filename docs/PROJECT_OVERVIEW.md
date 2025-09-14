# Watch Media Server - Project Overview

## 🎬 Complete Media Library Management System

Watch is a comprehensive web-based media server designed to manage, format, and play movies and TV shows from a library. It's specifically optimized for Docker deployment on Unraid and other containerized environments.

## 📁 Project Structure

```
Watch/
├── app.py                 # Main Flask application
├── console.py             # Command-line interface
├── media_formatter.py     # File organization and formatting
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
├── watch-template.xml    # Unraid Docker template
├── setup.sh             # Linux/macOS setup script
├── setup.bat            # Windows setup script
├── README.md            # Comprehensive documentation
├── .gitignore           # Git ignore rules
├── .dockerignore        # Docker ignore rules
├── templates/
│   └── index.html       # Main web interface
└── static/
    ├── css/
    │   └── style.css    # Modern responsive styling
    ├── js/
    │   └── app.js       # Frontend JavaScript
    └── images/          # Static assets
```

## 🚀 Key Features

### Web Interface
- **Modern UI**: Responsive design with gradient backgrounds and smooth animations
- **Media Browsing**: Grid-based layout with filtering by type (Movies/TV Shows/All)
- **Search Functionality**: Real-time search through your media library
- **Built-in Player**: HTML5 video player with streaming capabilities
- **Statistics Dashboard**: Library size, file counts, and scan status
- **Settings Management**: Web-based configuration interface

### Media Management
- **Automatic Scanning**: Recursive directory scanning with configurable intervals
- **Metadata Extraction**: Uses FFprobe to extract video information
- **File Organization**: Automatic renaming and folder structure organization
- **Playlist Support**: Create and manage custom playlists
- **Database Storage**: SQLite database for fast queries and metadata storage

### Console Interface
- **Command-line Management**: Full CLI for advanced users
- **Library Statistics**: Detailed reports on your media collection
- **Search and Play**: Direct media playback from command line
- **Configuration**: Set and modify all settings via CLI
- **Database Maintenance**: Cleanup and optimization tools

### Docker & Unraid Support
- **Docker Optimized**: Multi-stage build with minimal image size
- **Unraid Template**: Ready-to-use template for Unraid Community Applications
- **Volume Mounting**: Flexible media and data directory configuration
- **Health Checks**: Built-in container health monitoring
- **Security**: Non-root user execution and read-only media mounting

## 🛠 Technology Stack

### Backend
- **Python 3.11**: Modern Python with type hints
- **Flask**: Lightweight web framework
- **Flask-SocketIO**: Real-time communication
- **SQLite**: Embedded database for metadata
- **FFmpeg**: Media metadata extraction

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with Flexbox/Grid
- **JavaScript ES6+**: Vanilla JS with modern features
- **Socket.IO**: Real-time updates
- **Font Awesome**: Icon library

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Unraid**: NAS integration
- **Nginx Ready**: Reverse proxy compatible

## 📋 Installation Options

### 1. Docker Compose (Recommended)
```bash
git clone <repository>
cd Watch
./setup.sh  # Linux/macOS
# or
setup.bat   # Windows
```

### 2. Unraid Template
1. Import `unraid-template.xml`
2. Configure media paths
3. Start container

### 3. Manual Docker
```bash
docker build -t watch-media-server .
docker run -d -p 8080:8080 -v /path/to/media:/media:ro watch-media-server
```

## 🎯 Use Cases

### Home Media Server
- Organize personal movie and TV show collections
- Stream content to any device with a web browser
- Create custom playlists for different viewing sessions

### Small Office/Studio
- Centralized media library for team access
- Professional file organization and naming
- Console interface for IT management

### Development/Testing
- Media file management for development projects
- API testing with real media files
- Containerized media processing workflows

## 🔧 Configuration

### Environment Variables
- `MEDIA_LIBRARY_PATH`: Path to media files
- `TZ`: Timezone setting
- `PORT`: Web interface port (default: 8080)

### Volume Mounts
- `/media`: Media library (read-only recommended)
- `/app/data`: Database and logs (persistent)
- `/app/config`: Configuration files

### Settings
- Auto-scan intervals
- Supported file formats
- Transcoding options
- Maximum resolution limits

## 🔒 Security Features

- Non-root container execution
- Read-only media mounting
- Input validation and sanitization
- SQL injection prevention
- XSS protection in templates

## 📊 Performance

- **Lightweight**: ~200MB Docker image
- **Fast Scanning**: Efficient file system traversal
- **Cached Metadata**: SQLite database for quick queries
- **Streaming**: Direct file serving without transcoding overhead
- **Responsive**: Modern CSS with hardware acceleration

## 🚀 Getting Started

1. **Quick Start**: Run `./setup.sh` or `setup.bat`
2. **Add Media**: Place files in the `media/` directory
3. **Access Web UI**: Open `http://localhost:8080`
4. **Scan Library**: Click "Scan Library" button
5. **Enjoy**: Browse and play your media!

## 📈 Future Enhancements

- User authentication and multi-user support
- Advanced transcoding with FFmpeg
- Subtitle support and management
- Mobile app development
- Integration with external metadata APIs
- Advanced playlist features
- Media recommendation engine

## 🤝 Contributing

The project is designed for easy contribution:
- Clean, documented codebase
- Modular architecture
- Comprehensive error handling
- Extensive logging
- Docker-based development environment

## 📄 License

Open source project - see LICENSE file for details.

---

**Watch Media Server** - Your personal media library, beautifully organized and easily accessible from anywhere.
