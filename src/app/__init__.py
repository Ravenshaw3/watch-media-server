"""
Watch Media Server Application Factory
Creates and configures the Flask application
"""

import os
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
from src.models.media_manager import MediaManager
from src.services.auth_service import AuthService
from src.api.auth_routes import init_auth_routes
from src.api.media_routes import init_media_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory function"""
    # Get the directory where this file is located
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the src directory, then up to the project root
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))
    app.config['SECRET_KEY'] = 'watch-media-server-secret-key'
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Environment variables
    media_library_path = os.environ.get('MEDIA_LIBRARY_PATH', '/media')
    database_path = os.environ.get('DATABASE_PATH', 'watch.db')
    
    # Ensure database directory exists and has proper permissions
    import stat
    db_dir = os.path.dirname(database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        # Ensure the directory is writable
        os.chmod(db_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
    
    # Initialize services
    media_manager = MediaManager(database_path, media_library_path)
    auth_service = AuthService(database_path)
    
    # Global variables for scan status
    scan_in_progress = [False]
    
    # Initialize API routes
    init_auth_routes(app, auth_service)
    init_media_routes(app, media_manager, socketio, scan_in_progress)
    
    # Main route
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('index.html')
    
    # Version endpoint
    @app.route('/api/version', methods=['GET'])
    def api_get_version():
        """Get application version information"""
        import sys
        try:
            return {
                'version': "1.0.0",
                'build_date': "2025-09-13",
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }
        except Exception as e:
            return {'error': str(e)}, 500
    
    # Store services in app context for access in routes
    app.media_manager = media_manager
    app.auth_service = auth_service
    app.socketio = socketio
    app.scan_in_progress = scan_in_progress
    
    return app, socketio
