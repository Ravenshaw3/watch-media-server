"""
Watch Media Server - Main Application Entry Point
"""

import argparse
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Watch Media Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create application
    app, socketio = create_app()
    
    # Run application
    if args.debug:
        socketio.run(app, host=args.host, port=args.port, debug=True)
    else:
        socketio.run(app, host=args.host, port=args.port, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
