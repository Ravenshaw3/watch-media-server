#!/bin/bash

# Watch Media Server Setup Script
# This script helps set up the Watch Media Server on various platforms

set -e

echo "Watch Media Server Setup"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Docker is installed
check_docker() {
    if command -v docker &> /dev/null; then
        print_status "Docker is installed"
        docker --version
    else
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Check if Docker Compose is installed
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        print_status "Docker Compose is installed"
        docker-compose --version
    else
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    print_header "Creating directories..."
    
    mkdir -p media
    mkdir -p data
    mkdir -p config
    
    print_status "Directories created:"
    echo "  - media/ (for your media files)"
    echo "  - data/ (for database and logs)"
    echo "  - config/ (for configuration files)"
}

# Set up environment file
setup_env() {
    print_header "Setting up environment..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# Watch Media Server Environment Variables
MEDIA_LIBRARY_PATH=/media
TZ=UTC

# Optional: Custom port (default is 8080)
# PORT=8080

# Optional: Enable debug mode
# DEBUG=false
EOF
        print_status "Created .env file with default settings"
    else
        print_warning ".env file already exists, skipping creation"
    fi
}

# Build Docker image
build_image() {
    print_header "Building Docker image..."
    
    if docker build -t watch-media-server .; then
        print_status "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Start the application
start_application() {
    print_header "Starting Watch Media Server..."
    
    if docker-compose up -d; then
        print_status "Watch Media Server started successfully"
        echo ""
        print_status "Access the web interface at: http://localhost:8080"
        print_status "To view logs: docker-compose logs -f"
        print_status "To stop: docker-compose down"
    else
        print_error "Failed to start Watch Media Server"
        exit 1
    fi
}

# Setup for Unraid
setup_unraid() {
    print_header "Unraid Setup Instructions"
    echo ""
    echo "1. Copy the unraid-template.xml file to your Unraid server"
    echo "2. In Unraid, go to Docker tab"
    echo "3. Click 'Add Container' and select 'Template'"
    echo "4. Import the unraid-template.xml file"
    echo "5. Configure the following paths:"
    echo "   - Media Library: /mnt/user/media (or your media path)"
    echo "   - Data Directory: /mnt/user/appdata/watch"
    echo "   - Config Directory: /mnt/user/appdata/watch/config"
    echo "6. Set the WebUI port (default: 8080)"
    echo "7. Start the container"
    echo ""
    print_status "Unraid template is ready to use"
}

# Main setup function
main() {
    print_header "Watch Media Server Setup"
    echo ""
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Create directories
    create_directories
    
    # Setup environment
    setup_env
    
    # Build image
    build_image
    
    # Start application
    start_application
    
    echo ""
    print_header "Setup Complete!"
    echo ""
    echo "Next steps:"
    echo "1. Add your media files to the 'media' directory"
    echo "2. Open http://localhost:8080 in your browser"
    echo "3. Click 'Scan Library' to index your media"
    echo "4. Enjoy your media library!"
    echo ""
    echo "For Unraid users, see the unraid-template.xml file for setup instructions."
}

# Handle command line arguments
case "${1:-}" in
    "unraid")
        setup_unraid
        ;;
    "build")
        check_docker
        build_image
        ;;
    "start")
        check_docker
        check_docker_compose
        start_application
        ;;
    "stop")
        docker-compose down
        print_status "Watch Media Server stopped"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no command)  - Full setup (default)"
        echo "  unraid        - Show Unraid setup instructions"
        echo "  build         - Build Docker image only"
        echo "  start         - Start the application"
        echo "  stop          - Stop the application"
        echo "  logs          - View application logs"
        echo "  help          - Show this help message"
        ;;
    *)
        main
        ;;
esac
