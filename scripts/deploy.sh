#!/bin/bash

# Watch Media Server Production Deployment Script

set -e

echo "🚀 Starting Watch Media Server Production Deployment..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs ssl grafana/provisioning grafana/dashboards

# Set proper permissions
chmod 755 data logs ssl
chmod 700 grafana/provisioning grafana/dashboards

# Check if environment file exists
if [ ! -f "env.production" ]; then
    echo "❌ env.production file not found. Please create it from env.example"
    exit 1
fi

# Load environment variables
source env.production

# Validate required environment variables
required_vars=("SECRET_KEY" "JWT_SECRET_KEY" "ADMIN_PASSWORD" "TMDB_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [[ "${!var}" == *"your-"* ]]; then
        echo "❌ Please set $var in env.production"
        exit 1
    fi
done

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
services=("watch-media" "redis" "nginx" "prometheus" "grafana")
for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        docker-compose -f docker-compose.prod.yml logs "$service"
        exit 1
    fi
done

# Initialize database
echo "🗄️ Initializing database..."
docker-compose -f docker-compose.prod.yml exec watch-media python -c "
from app import app, MediaManager
with app.app_context():
    manager = MediaManager()
    print('Database initialized successfully')
"

# Create admin user
echo "👤 Creating admin user..."
docker-compose -f docker-compose.prod.yml exec watch-media python -c "
from auth_service import AuthService
auth = AuthService()
print('Admin user created/verified')
"

echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Access your services:"
echo "  • Watch Media Server: http://localhost"
echo "  • API Documentation: http://localhost/api/docs"
echo "  • Grafana Dashboard: http://localhost:3000 (admin/$GRAFANA_PASSWORD)"
echo "  • Prometheus Metrics: http://localhost:9090"
echo ""
echo "🔧 Management commands:"
echo "  • View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  • Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  • Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  • Update services: docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "⚠️  Remember to:"
echo "  • Configure SSL certificates in ./ssl/"
echo "  • Set up proper firewall rules"
echo "  • Configure backup schedules"
echo "  • Monitor system resources"
