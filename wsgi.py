# WSGI Application for Watch Media Server
import os
import sys
from app import app, socketio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for production
os.environ.setdefault('FLASK_ENV', 'production')

# Create WSGI application
application = app

if __name__ == '__main__':
    # For development
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
