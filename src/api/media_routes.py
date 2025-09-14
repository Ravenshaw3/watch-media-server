"""
Media API Routes
Handles media file operations, scanning, and library management
"""

from flask import Blueprint, request, jsonify
import sqlite3
import json
import os
import threading
from src.models.media_manager import MediaManager

media_bp = Blueprint('media', __name__, url_prefix='/api')


def init_media_routes(app, media_manager, socketio, scan_in_progress):
    """Initialize media routes"""
    
    @media_bp.route('/media')
    def api_get_media():
        """Get media files from database"""
        media_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Use database service for optimized queries
        query = "SELECT * FROM media_files"
        params = []
        
        if media_type:
            query += " WHERE media_type = ?"
            params.append(media_type)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Get database path from media_manager
        db_path = media_manager.db_path
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        
        columns = [description[0] for description in cursor.description]
        media_files = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse JSON fields
        for media in media_files:
            if media.get('genres'):
                try:
                    media['genres'] = json.loads(media['genres']) if isinstance(media['genres'], str) else media['genres']
                except:
                    media['genres'] = []
        
        conn.close()
        return jsonify(media_files)

    @media_bp.route('/scan', methods=['POST'])
    def api_scan_library():
        """API endpoint to trigger library scan"""
        def scan_thread():
            try:
                scan_in_progress[0] = True
                
                # Get current library path
                library_path = media_manager.get_setting('library_path', media_manager.media_library_path)
                
                socketio.emit('scan_status', {
                    'status': 'started',
                    'message': f'Library scan started in: {library_path}',
                    'progress': 0,
                    'scan_directory': library_path
                })
                
                # Count total files first
                supported_formats = media_manager.get_setting('supported_formats', 'mp4,avi,mkv,mov,wmv,flv,webm').split(',')
                total_files = 0
                processed_files = 0
                
                # Check if library path exists
                if not os.path.exists(library_path):
                    socketio.emit('scan_error', {
                        'status': 'error',
                        'message': f'Library path does not exist: {library_path}'
                    })
                    return
                
                # Count files
                for root, dirs, files in os.walk(library_path):
                    for file in files:
                        if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                            total_files += 1
                
                socketio.emit('scan_status', {
                    'status': 'counting',
                    'message': f'Found {total_files} media files to scan',
                    'progress': 0,
                    'total_files': total_files
                })
                
                # Scan files with progress updates
                for root, dirs, files in os.walk(library_path):
                    current_dir = os.path.relpath(root, library_path) if root != library_path else "."
                    
                    for file in files:
                        if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                            file_path = os.path.join(root, file)
                            media_manager.add_media_file(file_path)
                            processed_files += 1
                            
                            progress = int((processed_files / total_files) * 100) if total_files > 0 else 0
                            socketio.emit('scan_status', {
                                'status': 'scanning',
                                'message': f'Scanning {current_dir}: {file}',
                                'progress': progress,
                                'processed_files': processed_files,
                                'total_files': total_files,
                                'current_file': file,
                                'current_directory': current_dir,
                                'scan_directory': library_path
                            })
                
                socketio.emit('scan_complete', {
                    'status': 'success',
                    'message': f'Library scan completed. Processed {processed_files} files.',
                    'processed_files': processed_files,
                    'total_files': total_files
                })
                
            except Exception as e:
                socketio.emit('scan_error', {
                    'status': 'error',
                    'message': f'Scan failed: {str(e)}'
                })
            finally:
                scan_in_progress[0] = False
        
        # Start scan in background thread
        thread = threading.Thread(target=scan_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Library scan started'})

    @media_bp.route('/library/info')
    def api_get_library_info():
        """Get library information and statistics"""
        library_path = media_manager.get_setting('library_path', media_manager.media_library_path)
        
        # Calculate library size and file count
        total_files = 0
        total_size = 0
        supported_formats = media_manager.get_setting('supported_formats', 'mp4,avi,mkv,mov,wmv,flv,webm').split(',')
        
        if os.path.exists(library_path):
            for root, dirs, files in os.walk(library_path):
                for file in files:
                    if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                        total_files += 1
                        try:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                        except:
                            pass
        
        # Get media counts from database
        movies_count = 0
        tv_shows_count = 0
        try:
            conn = sqlite3.connect(media_manager.db_path)
            cursor = conn.cursor()
            # Count movies (files without episode information)
            cursor.execute("SELECT COUNT(*) FROM media_files WHERE episode IS NULL OR episode = ''")
            movies_count = cursor.fetchone()[0]
            # Count TV shows (files with episode information)
            cursor.execute("SELECT COUNT(*) FROM media_files WHERE episode IS NOT NULL AND episode != ''")
            tv_shows_count = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            print(f"Error getting media counts: {e}")
        
        return jsonify({
            'library_path': library_path,
            'total_files': total_files,
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
            'movies_count': movies_count,
            'tv_shows_count': tv_shows_count,
            'supported_formats': supported_formats,
            'exists': os.path.exists(library_path)
        })

    @media_bp.route('/settings', methods=['GET', 'POST'])
    def api_settings():
        """Get or update application settings"""
        if request.method == 'GET':
            # Return current settings
            settings = {
                'library_path': media_manager.get_setting('library_path', media_manager.media_library_path),
                'auto_scan': media_manager.get_setting('auto_scan', 'true'),
                'scan_interval': media_manager.get_setting('scan_interval', '3600'),
                'supported_formats': media_manager.get_setting('supported_formats', 'mp4,avi,mkv,mov,wmv,flv,webm'),
                'transcode_enabled': media_manager.get_setting('transcode_enabled', 'true'),
                'max_resolution': media_manager.get_setting('max_resolution', '1080p')
            }
            return jsonify(settings)
        else:
            # Update settings
            data = request.get_json()
            for key, value in data.items():
                media_manager.set_setting(key, str(value))
            return jsonify({'message': 'Settings updated successfully'})

    # Register the blueprint
    app.register_blueprint(media_bp)
