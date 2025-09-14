# Configuration for Watch Media Server
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'watch-media-server-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Database Configuration
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'watch.db')
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '10'))
    DB_OPTIMIZATION_ENABLED = os.environ.get('DB_OPTIMIZATION_ENABLED', 'true').lower() == 'true'
    
    # Media Library Configuration
    MEDIA_LIBRARY_PATH = os.environ.get('MEDIA_LIBRARY_PATH', '/media')
    MAX_RESOLUTION = os.environ.get('MAX_RESOLUTION', '1080p')
    SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v']
    SUPPORTED_AUDIO_FORMATS = ['mp3', 'aac', 'flac', 'ogg', 'wav', 'm4a']
    
    # Authentication Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_EXPIRATION_HOURS', '24')))
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = os.environ.get('JWT_COOKIE_SECURE', 'true').lower() == 'true'
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_CHECK_FORM = True
    
    # Default admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@watch.local')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # TMDB API Configuration
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    TMDB_BASE_URL = 'https://api.themoviedb.org/3'
    TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p'
    
    # Redis/Cache Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_DEFAULT_TTL = int(os.environ.get('CACHE_DEFAULT_TTL', '3600'))  # 1 hour
    
    # Transcoding Configuration
    MAX_CONCURRENT_TRANSCODES = int(os.environ.get('MAX_CONCURRENT_TRANSCODES', '2'))
    TRANSCODE_TEMP_DIR = os.environ.get('TRANSCODE_TEMP_DIR', '/tmp/watch_transcode')
    TRANSCODE_CACHE_TTL = int(os.environ.get('TRANSCODE_CACHE_TTL', '86400'))  # 24 hours
    
    # Performance Monitoring Configuration
    MONITORING_ENABLED = os.environ.get('MONITORING_ENABLED', 'true').lower() == 'true'
    METRICS_RETENTION_DAYS = int(os.environ.get('METRICS_RETENTION_DAYS', '7'))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security Configuration
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '100 per hour')
    RATE_LIMIT_STORAGE_URL = REDIS_URL
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '100 * 1024 * 1024'))  # 100MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/watch_uploads')
    
    # Auto-scan Configuration
    AUTO_SCAN = os.environ.get('AUTO_SCAN', 'true').lower() == 'true'
    SCAN_INTERVAL = int(os.environ.get('SCAN_INTERVAL', '3600'))  # 1 hour
    
    # Socket.IO Configuration
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS
    
    # Compression Configuration
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CACHE_ENABLED = False
    MONITORING_ENABLED = False
    JWT_COOKIE_SECURE = False
    RATE_LIMIT_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    CACHE_ENABLED = True
    MONITORING_ENABLED = True
    JWT_COOKIE_SECURE = True
    RATE_LIMIT_ENABLED = True
    
    # Production-specific settings
    DB_POOL_SIZE = 20
    MAX_CONCURRENT_TRANSCODES = 4
    CACHE_DEFAULT_TTL = 7200  # 2 hours
    METRICS_RETENTION_DAYS = 30

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = ':memory:'
    CACHE_ENABLED = False
    MONITORING_ENABLED = False
    JWT_COOKIE_SECURE = False
    RATE_LIMIT_ENABLED = False
    AUTO_SCAN = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
