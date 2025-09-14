# Changelog

All notable changes to Watch Media Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline
- Security scanning with Trivy
- Automated Docker builds
- Release automation

## [1.0.0] - 2024-12-09

### Added
- **Web Interface**
  - Modern, responsive design with gradient backgrounds
  - Media browsing with filtering (Movies/TV Shows/All)
  - Built-in HTML5 video player with streaming
  - Real-time search functionality
  - Statistics dashboard and settings management
  - WebSocket-based real-time updates

- **Media Management**
  - Automatic media library scanning with configurable intervals
  - Metadata extraction using FFprobe
  - SQLite database for fast queries and metadata storage
  - File organization and renaming capabilities
  - Playlist creation and management
  - Support for multiple media formats (MP4, AVI, MKV, MOV, WMV, FLV, WebM)

- **Console Interface**
  - Full command-line management system
  - Library statistics and reporting
  - Direct media playback from CLI
  - Configuration management
  - Database maintenance tools

- **Docker & Unraid Support**
  - Complete Docker configuration with multi-stage build
  - Unraid template ready for Community Applications
  - Docker Compose setup for easy deployment
  - Health checks and security best practices
  - Non-root user execution and read-only media mounting

- **Media Formatting & Organization**
  - Automatic file organization by type
  - Smart naming conventions:
    - Movies: "Title (Year)/Title (Year).ext"
    - TV Shows: "Show/Season XX/Show - SXXEXX.ext"
  - Metadata extraction and enhancement
  - Library cleanup and maintenance tools

- **API Endpoints**
  - `GET /api/media` - Get media files
  - `POST /api/scan` - Trigger library scan
  - `GET /api/settings` - Get settings
  - `POST /api/settings` - Update settings
  - `GET /api/stream/<id>` - Stream media file
  - `GET /api/play/<id>` - Play media file

- **Documentation**
  - Comprehensive README with installation instructions
  - Detailed Unraid installation guide
  - Project overview and feature documentation
  - Contributing guidelines
  - Download instructions

### Technical Details
- **Backend**: Python 3.11+, Flask, Flask-SocketIO, SQLite
- **Frontend**: HTML5, CSS3, JavaScript ES6+, Socket.IO
- **Infrastructure**: Docker, Docker Compose, Unraid support
- **Security**: Non-root execution, input validation, XSS protection
- **Performance**: Lightweight (~200MB Docker image), efficient scanning

### Installation Options
- Docker Compose (recommended)
- Unraid Community Applications template
- Manual Docker deployment
- Local Python development

### Supported Platforms
- Linux (Ubuntu, Debian, CentOS, etc.)
- Windows (with Docker Desktop)
- macOS (with Docker Desktop)
- Unraid NAS systems
- Any Docker-compatible system

## [0.1.0] - 2024-12-09

### Added
- Initial project structure
- Basic Flask application
- Docker configuration
- Unraid template
- Core media management functionality

---

## Version Numbering

- **Major version** (X.0.0): Incompatible API changes
- **Minor version** (0.X.0): New functionality in a backwards compatible manner
- **Patch version** (0.0.X): Backwards compatible bug fixes

## Release Process

1. Update version numbers in relevant files
2. Update CHANGELOG.md with new version
3. Create Git tag for the version
4. Create GitHub release with changelog
5. Update Docker images and templates

## Future Roadmap

### Planned Features
- User authentication and authorization
- Advanced transcoding with FFmpeg
- Subtitle support and management
- Mobile app development
- Integration with external metadata APIs
- Advanced playlist features
- Media recommendation engine
- Plugin system for extensibility

### Known Issues
- None at this time

### Deprecated Features
- None at this time
