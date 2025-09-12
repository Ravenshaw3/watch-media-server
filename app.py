#!/usr/bin/env python3
"""
Watch - Media Library Management System
A web-based media server for managing, formatting, and playing movies and TV shows
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
import sqlite3
import hashlib
import mimetypes
from datetime import datetime
import threading
import time
import subprocess
import shutil

# Import our new services
from tmdb_service import TMDBService
from subtitle_service import SubtitleService
from search_service import SearchService

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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'watch-media-server-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
MEDIA_LIBRARY_PATH = os.environ.get('MEDIA_LIBRARY_PATH', '/media')
DATABASE_PATH = 'watch.db'
SCAN_IN_PROGRESS = False
MEDIA_FILES = []

# Initialize services
tmdb_service = TMDBService()
subtitle_service = SubtitleService()
search_service = SearchService(DATABASE_PATH)

class MediaManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Media files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                media_type TEXT,  -- 'movie' or 'tv_show'
                title TEXT,
                year INTEGER,
                season INTEGER,
                episode INTEGER,
                duration INTEGER,
                resolution TEXT,
                codec TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_played TIMESTAMP,
                play_count INTEGER DEFAULT 0,
                rating REAL,
                tags TEXT,
                metadata TEXT,  -- JSON string for additional metadata
                poster_url TEXT,
                backdrop_url TEXT,
                overview TEXT,
                genres TEXT,  -- JSON array of genres
                runtime INTEGER,
                release_date TEXT,
                imdb_id TEXT,
                tmdb_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add new columns if they don't exist (for existing databases)
        self.migrate_database()
        
        # Library settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS library_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL
            )
        ''')
        
        # Insert default settings
        default_settings = [
            ('library_path', MEDIA_LIBRARY_PATH),
            ('auto_scan', 'true'),
            ('scan_interval', '3600'),  # 1 hour
            ('supported_formats', 'mp4,avi,mkv,mov,wmv,flv,webm'),
            ('transcode_enabled', 'true'),
            ('max_resolution', '1080p')
        ]
        
        for key, value in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO library_settings (setting_key, setting_value)
                VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def migrate_database(self):
        """Migrate database schema for new features"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(media_files)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ('poster_url', 'TEXT'),
            ('backdrop_url', 'TEXT'),
            ('overview', 'TEXT'),
            ('genres', 'TEXT'),
            ('runtime', 'INTEGER'),
            ('release_date', 'TEXT'),
            ('imdb_id', 'TEXT'),
            ('tmdb_id', 'INTEGER'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE media_files ADD COLUMN {column_name} {column_type}")
                    print(f"Added column {column_name} to media_files table")
                except sqlite3.Error as e:
                    print(f"Error adding column {column_name}: {e}")
        
        # Create saved_searches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                search_term TEXT,
                filters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create subtitles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subtitles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER,
                file_path TEXT,
                language TEXT,
                format TEXT,
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key, default=None):
        """Get a setting value from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT setting_value FROM library_settings WHERE setting_key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default
    
    def set_setting(self, key, value):
        """Set a setting value in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO library_settings (setting_key, setting_value)
            VALUES (?, ?)
        ''', (key, value))
        conn.commit()
        conn.close()
    
    def scan_media_library(self):
        """Scan the media library for new files"""
        global SCAN_IN_PROGRESS
        if SCAN_IN_PROGRESS:
            return
        
        SCAN_IN_PROGRESS = True
        library_path = self.get_setting('library_path', MEDIA_LIBRARY_PATH)
        supported_formats = self.get_setting('supported_formats', 'mp4,avi,mkv,mov,wmv,flv,webm').split(',')
        
        logger.info(f"Starting media library scan in: {library_path}")
        
        try:
            for root, dirs, files in os.walk(library_path):
                for file in files:
                    if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                        file_path = os.path.join(root, file)
                        self.add_media_file(file_path)
        except Exception as e:
            logger.error(f"Error scanning media library: {e}")
        finally:
            SCAN_IN_PROGRESS = False
            logger.info("Media library scan completed")
    
    def add_media_file(self, file_path):
        """Add a media file to the database"""
        try:
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            
            # Extract metadata
            metadata = self.extract_metadata(file_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO media_files 
                (file_path, file_name, file_size, file_hash, media_type, title, year, 
                 season, episode, duration, resolution, codec, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_path,
                os.path.basename(file_path),
                file_size,
                file_hash,
                metadata.get('type', 'unknown'),
                metadata.get('title', ''),
                metadata.get('year'),
                metadata.get('season'),
                metadata.get('episode'),
                metadata.get('duration'),
                metadata.get('resolution'),
                metadata.get('codec'),
                json.dumps(metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding media file {file_path}: {e}")
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def extract_metadata(self, file_path):
        """Extract metadata from media file using ffprobe"""
        metadata = {
            'type': 'unknown',
            'title': '',
            'year': None,
            'season': None,
            'episode': None,
            'duration': None,
            'resolution': '',
            'codec': ''
        }
        
        try:
            # Use ffprobe to get media information
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                
                # Extract video stream info
                for stream in probe_data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        metadata['codec'] = stream.get('codec_name', '')
                        width = stream.get('width', 0)
                        height = stream.get('height', 0)
                        if width and height:
                            metadata['resolution'] = f"{width}x{height}"
                        break
                
                # Extract duration
                format_info = probe_data.get('format', {})
                duration = format_info.get('duration')
                if duration:
                    metadata['duration'] = int(float(duration))
                
                # Extract title from filename or metadata
                filename = os.path.basename(file_path)
                metadata['title'] = os.path.splitext(filename)[0]
                
                # Try to determine if it's a TV show or movie
                if any(keyword in filename.lower() for keyword in ['s01e01', 's1e1', 'season', 'episode']):
                    metadata['type'] = 'tv_show'
                else:
                    metadata['type'] = 'movie'
                
        except Exception as e:
            logger.error(f"Error extracting metadata for {file_path}: {e}")
        
        return metadata
    
    def get_media_files(self, media_type=None, limit=None, offset=0):
        """Get media files from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM media_files"
        params = []
        
        if media_type:
            query += " WHERE media_type = ?"
            params.append(media_type)
        
        query += " ORDER BY added_date DESC"
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def update_play_count(self, file_id):
        """Update play count and last played timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE media_files 
            SET play_count = play_count + 1, last_played = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (file_id,))
        conn.commit()
        conn.close()

# Initialize media manager
media_manager = MediaManager()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/media')
def api_get_media():
    """API endpoint to get media files"""
    media_type = request.args.get('type')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    files = media_manager.get_media_files(media_type, limit, offset)
    return jsonify(files)

@app.route('/api/scan', methods=['POST'])
def api_scan_library():
    """API endpoint to trigger library scan"""
    def scan_thread():
        global SCAN_IN_PROGRESS
        try:
            SCAN_IN_PROGRESS = True
            socketio.emit('scan_status', {
                'status': 'started',
                'message': 'Library scan started',
                'progress': 0
            })
            
            # Get current library path
            library_path = media_manager.get_setting('library_path', MEDIA_LIBRARY_PATH)
            
            # Count total files first
            supported_formats = media_manager.get_setting('supported_formats', 'mp4,avi,mkv,mov,wmv,flv,webm').split(',')
            total_files = 0
            processed_files = 0
            
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
                for file in files:
                    if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                        file_path = os.path.join(root, file)
                        media_manager.add_media_file(file_path)
                        processed_files += 1
                        
                        progress = int((processed_files / total_files) * 100) if total_files > 0 else 0
                        socketio.emit('scan_status', {
                            'status': 'scanning',
                            'message': f'Processing {file}',
                            'progress': progress,
                            'processed_files': processed_files,
                            'total_files': total_files,
                            'current_file': file
                        })
            
            socketio.emit('scan_complete', {
                'status': 'success',
                'message': f'Library scan completed. Processed {processed_files} files.',
                'progress': 100,
                'processed_files': processed_files,
                'total_files': total_files
            })
            
        except Exception as e:
            logger.error(f"Error during library scan: {e}")
            socketio.emit('scan_error', {
                'status': 'error',
                'message': f'Scan failed: {str(e)}',
                'progress': 0
            })
        finally:
            SCAN_IN_PROGRESS = False
    
    if not SCAN_IN_PROGRESS:
        threading.Thread(target=scan_thread, daemon=True).start()
        return jsonify({'status': 'started'})
    else:
        return jsonify({'status': 'already_running'})

@app.route('/api/settings')
def api_get_settings():
    """API endpoint to get settings"""
    settings = {}
    for key in ['library_path', 'auto_scan', 'scan_interval', 'supported_formats', 'transcode_enabled', 'max_resolution']:
        settings[key] = media_manager.get_setting(key)
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """API endpoint to update settings"""
    data = request.get_json()
    for key, value in data.items():
        media_manager.set_setting(key, str(value))
    
    # If library path changed, trigger a rescan
    if 'library_path' in data:
        socketio.emit('library_path_changed', {
            'new_path': data['library_path'],
            'message': 'Library path updated. Consider running a new scan.'
        })
    
    return jsonify({'status': 'success'})

@app.route('/api/scan/status')
def api_scan_status():
    """API endpoint to get current scan status"""
    return jsonify({
        'scan_in_progress': SCAN_IN_PROGRESS,
        'library_path': media_manager.get_setting('library_path', MEDIA_LIBRARY_PATH)
    })

@app.route('/api/library/info')
def api_library_info():
    """API endpoint to get library information"""
    library_path = media_manager.get_setting('library_path', MEDIA_LIBRARY_PATH)
    supported_formats = media_manager.get_setting('supported_formats', 'mp4,avi,mkv,mov,wmv,flv,webm').split(',')
    
    # Count files in library
    total_files = 0
    total_size = 0
    
    try:
        for root, dirs, files in os.walk(library_path):
            for file in files:
                if any(file.lower().endswith(f'.{fmt}') for fmt in supported_formats):
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_files += 1
                        total_size += os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting library info: {e}")
    
    return jsonify({
        'library_path': library_path,
        'total_files': total_files,
        'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
        'supported_formats': supported_formats,
        'exists': os.path.exists(library_path)
    })

@app.route('/api/play/<int:file_id>')
def api_play_media(file_id):
    """API endpoint to play media file"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        file_path = result[0]
        if os.path.exists(file_path):
            media_manager.update_play_count(file_id)
            return send_file(file_path)
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/stream/<int:file_id>')
def api_stream_media(file_id):
    """API endpoint to stream media file"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        file_path = result[0]
        if os.path.exists(file_path):
            media_manager.update_play_count(file_id)
            return send_file(file_path, as_attachment=False)
    
    return jsonify({'error': 'File not found'}), 404

# ===== HIGH-IMPACT FEATURES API ENDPOINTS =====

@app.route('/api/search')
def api_search():
    """Advanced search endpoint"""
    search_term = request.args.get('q', '')
    filters = {}
    
    # Parse filters from query parameters
    if request.args.get('year_start'):
        filters['year_range'] = [int(request.args.get('year_start')), None]
    if request.args.get('year_end'):
        if 'year_range' not in filters:
            filters['year_range'] = [None, int(request.args.get('year_end'))]
        else:
            filters['year_range'][1] = int(request.args.get('year_end'))
    
    if request.args.get('genres'):
        filters['genres'] = request.args.get('genres').split(',')
    
    if request.args.get('rating_min'):
        filters['rating_min'] = float(request.args.get('rating_min'))
    if request.args.get('rating_max'):
        filters['rating_max'] = float(request.args.get('rating_max'))
    
    if request.args.get('media_type'):
        filters['media_type'] = request.args.get('media_type')
    
    if request.args.get('has_subtitles'):
        filters['has_subtitles'] = request.args.get('has_subtitles').lower() == 'true'
    
    if request.args.get('has_poster'):
        filters['has_poster'] = request.args.get('has_poster').lower() == 'true'
    
    sort_by = request.args.get('sort_by', 'title')
    sort_order = request.args.get('sort_order', 'ASC')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    results = search_service.search_media(search_term, filters, sort_by, sort_order, limit, offset)
    return jsonify(results)

@app.route('/api/search/suggestions')
def api_search_suggestions():
    """Get search suggestions"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    suggestions = search_service.get_search_suggestions(query, limit)
    return jsonify(suggestions)

@app.route('/api/recently-added')
def api_recently_added():
    """Get recently added media"""
    days = int(request.args.get('days', 7))
    limit = int(request.args.get('limit', 20))
    
    results = search_service.get_recently_added(days, limit)
    return jsonify(results)

@app.route('/api/trending')
def api_trending():
    """Get trending media"""
    days = int(request.args.get('days', 30))
    limit = int(request.args.get('limit', 20))
    
    results = search_service.get_trending_media(days, limit)
    return jsonify(results)

@app.route('/api/continue-watching')
def api_continue_watching():
    """Get continue watching list"""
    limit = int(request.args.get('limit', 20))
    
    results = search_service.get_continue_watching(limit)
    return jsonify(results)

@app.route('/api/recommendations/<int:media_id>')
def api_recommendations(media_id):
    """Get recommendations for a media item"""
    limit = int(request.args.get('limit', 10))
    
    results = search_service.get_recommendations(media_id, limit)
    return jsonify(results)

@app.route('/api/search/filters')
def api_search_filters():
    """Get available search filters"""
    filters = search_service.get_search_filters()
    return jsonify(filters)

@app.route('/api/subtitles/<int:media_id>')
def api_get_subtitles(media_id):
    """Get subtitles for a media file"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (media_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'Media not found'}), 404
    
    file_path = result[0]
    subtitles = subtitle_service.find_subtitles(file_path)
    return jsonify(subtitles)

@app.route('/api/subtitle/<path:filename>')
def api_get_subtitle(filename):
    """Get subtitle file content"""
    # Find the subtitle file
    subtitle_path = None
    for root, dirs, files in os.walk(MEDIA_LIBRARY_PATH):
        if filename in files:
            subtitle_path = os.path.join(root, filename)
            break
    
    if not subtitle_path or not os.path.exists(subtitle_path):
        return jsonify({'error': 'Subtitle not found'}), 404
    
    format_type = request.args.get('format', 'vtt')
    content = subtitle_service.get_subtitle_content(subtitle_path, format_type)
    
    if format_type == 'vtt':
        return content, 200, {'Content-Type': 'text/vtt; charset=utf-8'}
    else:
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/api/metadata/<int:media_id>')
def api_get_metadata(media_id):
    """Get or update metadata for a media file"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM media_files WHERE id = ?', (media_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'Media not found'}), 404
    
    # Get current metadata
    media_data = dict(zip([desc[0] for desc in cursor.description], result))
    
    # If requested, fetch fresh metadata from TMDB
    if request.args.get('refresh') == 'true':
        file_path = media_data['file_path']
        media_type = media_data.get('media_type', 'movie')
        
        # Get metadata from TMDB
        metadata = tmdb_service.get_media_metadata(file_path, media_type)
        
        # Update database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE media_files SET 
                title = ?, poster_url = ?, backdrop_url = ?, overview = ?,
                rating = ?, genres = ?, runtime = ?, release_date = ?,
                imdb_id = ?, tmdb_id = ?
            WHERE id = ?
        """, (
            metadata['title'], metadata['poster_url'], metadata['backdrop_url'],
            metadata['overview'], metadata['rating'], json.dumps(metadata['genres']),
            metadata['runtime'], metadata['release_date'], metadata['imdb_id'],
            metadata['tmdb_id'], media_id
        ))
        conn.commit()
        conn.close()
        
        # Update media_data with new metadata
        media_data.update(metadata)
    
    return jsonify(media_data)

@app.route('/api/bulk/update-metadata', methods=['POST'])
def api_bulk_update_metadata():
    """Bulk update metadata for multiple media files"""
    data = request.get_json()
    media_ids = data.get('media_ids', [])
    
    if not media_ids:
        return jsonify({'error': 'No media IDs provided'}), 400
    
    updated_count = 0
    errors = []
    
    for media_id in media_ids:
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path, media_type FROM media_files WHERE id = ?', (media_id,))
            result = cursor.fetchone()
            
            if result:
                file_path, media_type = result
                metadata = tmdb_service.get_media_metadata(file_path, media_type)
                
                cursor.execute("""
                    UPDATE media_files SET 
                        title = ?, poster_url = ?, backdrop_url = ?, overview = ?,
                        rating = ?, genres = ?, runtime = ?, release_date = ?,
                        imdb_id = ?, tmdb_id = ?
                    WHERE id = ?
                """, (
                    metadata['title'], metadata['poster_url'], metadata['backdrop_url'],
                    metadata['overview'], metadata['rating'], json.dumps(metadata['genres']),
                    metadata['runtime'], metadata['release_date'], metadata['imdb_id'],
                    metadata['tmdb_id'], media_id
                ))
                conn.commit()
                updated_count += 1
            else:
                errors.append(f"Media ID {media_id} not found")
            
            conn.close()
            
        except Exception as e:
            errors.append(f"Error updating media ID {media_id}: {str(e)}")
    
    return jsonify({
        'updated_count': updated_count,
        'errors': errors
    })

@app.route('/api/bulk/delete', methods=['POST'])
def api_bulk_delete():
    """Bulk delete media files"""
    data = request.get_json()
    media_ids = data.get('media_ids', [])
    delete_files = data.get('delete_files', False)
    
    if not media_ids:
        return jsonify({'error': 'No media IDs provided'}), 400
    
    deleted_count = 0
    errors = []
    
    for media_id in media_ids:
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (media_id,))
            result = cursor.fetchone()
            
            if result:
                file_path = result[0]
                
                # Delete file if requested
                if delete_files and os.path.exists(file_path):
                    os.remove(file_path)
                
                # Remove from database
                cursor.execute('DELETE FROM media_files WHERE id = ?', (media_id,))
                conn.commit()
                deleted_count += 1
            else:
                errors.append(f"Media ID {media_id} not found")
            
            conn.close()
            
        except Exception as e:
            errors.append(f"Error deleting media ID {media_id}: {str(e)}")
    
    return jsonify({
        'deleted_count': deleted_count,
        'errors': errors
    })

@app.route('/api/saved-searches', methods=['GET', 'POST'])
def api_saved_searches():
    """Manage saved searches"""
    if request.method == 'GET':
        searches = search_service.get_saved_searches()
        return jsonify(searches)
    
    elif request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        search_term = data.get('search_term', '')
        filters = data.get('filters', {})
        
        if not name:
            return jsonify({'error': 'Search name is required'}), 400
        
        success = search_service.save_search(name, search_term, filters)
        if success:
            return jsonify({'message': 'Search saved successfully'})
        else:
            return jsonify({'error': 'Failed to save search'}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'scan_in_progress': SCAN_IN_PROGRESS})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

def start_auto_scan():
    """Start automatic library scanning"""
    while True:
        if media_manager.get_setting('auto_scan') == 'true':
            media_manager.scan_media_library()
        
        interval = int(media_manager.get_setting('scan_interval', '3600'))
        time.sleep(interval)

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Watch - Media Library Management System')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--console', action='store_true', help='Start console interface')
    
    args = parser.parse_args()
    
    if args.console:
        # Start console interface
        from console import ConsoleInterface
        console = ConsoleInterface(media_manager)
        console.run()
    else:
        # Start web interface
        logger.info(f"Starting Watch Media Server on {args.host}:{args.port}")
        
        # Start auto-scan thread
        scan_thread = threading.Thread(target=start_auto_scan, daemon=True)
        scan_thread.start()
        
        # Start web server
        socketio.run(app, host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
