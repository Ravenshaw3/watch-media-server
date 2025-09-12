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
from auth_service import AuthService, require_auth, require_admin
from pwa_service import PWAService
from transcoding_service import TranscodingService
from cache_service import cache_service, cached, cache_invalidate, CacheKeys
from monitoring_service import performance_monitor, monitor_performance, track_active_requests
from database_service import database_service
from api_docs_service import api_docs_service

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
auth_service = AuthService(DATABASE_PATH)
pwa_service = PWAService()
transcoding_service = TranscodingService(DATABASE_PATH)

# Initialize technical services
app.performance_monitor = performance_monitor

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

# ===== GAME-CHANGING FEATURES API ENDPOINTS =====

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """User login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = auth_service.authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = auth_service.generate_token(user['id'], user['username'], user['role'])
    
    response = jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'preferences': user['preferences']
        }
    })
    
    # Set secure cookie
    response.set_cookie('access_token', token, httponly=True, secure=True, samesite='Strict')
    
    return response

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """User registration endpoint"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'Username, email, and password required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    user = auth_service.create_user(username, email, password)
    if not user:
        return jsonify({'error': 'Username or email already exists'}), 409
    
    token = auth_service.generate_token(user['id'], user['username'], user['role'])
    
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def api_logout():
    """User logout endpoint"""
    response = jsonify({'message': 'Logged out successfully'})
    response.set_cookie('access_token', '', expires=0)
    return response

@app.route('/api/auth/me')
@require_auth
def api_get_current_user():
    """Get current user info"""
    user_id = request.current_user['user_id']
    user = auth_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'role': user['role'],
        'preferences': user['preferences'],
        'created_at': user['created_at'],
        'last_login': user['last_login']
    })

@app.route('/api/auth/preferences', methods=['PUT'])
@require_auth
def api_update_preferences():
    """Update user preferences"""
    user_id = request.current_user['user_id']
    preferences = request.get_json()
    
    success = auth_service.update_user_preferences(user_id, preferences)
    if success:
        return jsonify({'message': 'Preferences updated successfully'})
    else:
        return jsonify({'error': 'Failed to update preferences'}), 500

# Watchlist endpoints
@app.route('/api/watchlist')
@require_auth
def api_get_watchlist():
    """Get user's watchlist"""
    user_id = request.current_user['user_id']
    watchlist = auth_service.get_user_watchlist(user_id)
    return jsonify(watchlist)

@app.route('/api/watchlist/<int:media_id>', methods=['POST'])
@require_auth
def api_add_to_watchlist(media_id):
    """Add media to watchlist"""
    user_id = request.current_user['user_id']
    success = auth_service.add_to_watchlist(user_id, media_id)
    
    if success:
        return jsonify({'message': 'Added to watchlist'})
    else:
        return jsonify({'error': 'Failed to add to watchlist'}), 500

@app.route('/api/watchlist/<int:media_id>', methods=['DELETE'])
@require_auth
def api_remove_from_watchlist(media_id):
    """Remove media from watchlist"""
    user_id = request.current_user['user_id']
    success = auth_service.remove_from_watchlist(user_id, media_id)
    
    if success:
        return jsonify({'message': 'Removed from watchlist'})
    else:
        return jsonify({'error': 'Failed to remove from watchlist'}), 500

# Play history endpoints
@app.route('/api/play-history', methods=['POST'])
@require_auth
def api_record_play():
    """Record a play event"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    
    media_id = data.get('media_id')
    duration_watched = data.get('duration_watched', 0)
    completed = data.get('completed', False)
    
    if not media_id:
        return jsonify({'error': 'Media ID required'}), 400
    
    success = auth_service.record_play(user_id, media_id, duration_watched, completed)
    
    if success:
        return jsonify({'message': 'Play recorded successfully'})
    else:
        return jsonify({'error': 'Failed to record play'}), 500

@app.route('/api/play-history')
@require_auth
def api_get_play_history():
    """Get user's play history"""
    user_id = request.current_user['user_id']
    limit = int(request.args.get('limit', 50))
    
    history = auth_service.get_user_play_history(user_id, limit)
    return jsonify(history)

@app.route('/api/continue-watching')
@require_auth
def api_get_continue_watching():
    """Get user's continue watching list"""
    user_id = request.current_user['user_id']
    limit = int(request.args.get('limit', 20))
    
    continue_list = auth_service.get_continue_watching(user_id, limit)
    return jsonify(continue_list)

# Recommendations endpoint
@app.route('/api/recommendations')
@require_auth
def api_get_recommendations():
    """Get personalized recommendations"""
    user_id = request.current_user['user_id']
    limit = int(request.args.get('limit', 20))
    
    recommendations = auth_service.generate_recommendations(user_id, limit)
    return jsonify(recommendations)

# PWA endpoints
@app.route('/manifest.json')
def api_manifest():
    """PWA manifest endpoint"""
    return jsonify(pwa_service.get_manifest())

@app.route('/sw.js')
def api_service_worker():
    """Service worker endpoint"""
    from flask import Response
    return Response(
        pwa_service.service_worker_script,
        mimetype='application/javascript'
    )

@app.route('/offline')
def api_offline_page():
    """Offline page endpoint"""
    from flask import Response
    return Response(
        pwa_service.offline_page,
        mimetype='text/html'
    )

# Transcoding endpoints
@app.route('/api/transcode/<int:media_id>')
@require_auth
def api_start_transcode(media_id):
    """Start transcoding for a media file"""
    quality = request.args.get('quality', '720p')
    
    if quality not in transcoding_service.quality_presets:
        return jsonify({'error': 'Invalid quality'}), 400
    
    # Get media file path
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (media_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'Media not found'}), 404
    
    file_path = result[0]
    if not os.path.exists(file_path):
        return jsonify({'error': 'Media file not found'}), 404
    
    # Check if already cached
    cached_path = transcoding_service.get_cached_transcode(media_id, quality)
    if cached_path:
        return jsonify({
            'status': 'completed',
            'url': f'/api/stream/{media_id}?quality={quality}'
        })
    
    # Queue transcoding
    job_id = transcoding_service.queue_transcode(media_id, file_path, quality)
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': 'Transcoding queued'
    })

@app.route('/api/transcode/status/<int:job_id>')
@require_auth
def api_transcode_status(job_id):
    """Get transcoding job status"""
    status = transcoding_service.get_transcode_status(job_id)
    return jsonify(status)

@app.route('/api/transcode/qualities/<int:media_id>')
@require_auth
def api_get_available_qualities(media_id):
    """Get available transcoded qualities for media"""
    qualities = transcoding_service.get_available_qualities(media_id)
    return jsonify(qualities)

# Enhanced streaming endpoint with transcoding
@app.route('/api/stream/<int:file_id>')
@require_auth
def api_stream_media_enhanced(file_id):
    """Enhanced streaming endpoint with quality selection"""
    quality = request.args.get('quality', '720p')
    job_id = request.args.get('job_id')
    
    # Get media info
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'File not found'}), 404
    
    file_path = result[0]
    
    # Check for transcoded version
    if quality != 'original':
        cached_path = transcoding_service.get_cached_transcode(file_id, quality)
        if cached_path:
            file_path = cached_path
        elif job_id:
            # Check if transcoding is complete
            status = transcoding_service.get_transcode_status(int(job_id))
            if status.get('status') == 'completed' and status.get('output_path'):
                file_path = status['output_path']
            else:
                return jsonify({
                    'error': 'Transcoding in progress',
                    'status': status.get('status'),
                    'progress': status.get('progress', 0)
                }), 202
    
    if os.path.exists(file_path):
        # Record play
        user_id = request.current_user['user_id']
        auth_service.record_play(user_id, file_id)
        
        return send_file(file_path, as_attachment=False)
    
    return jsonify({'error': 'File not found'}), 404

# Admin endpoints
@app.route('/api/admin/users')
@require_auth
@require_admin
def api_get_all_users():
    """Get all users (admin only)"""
    admin_user_id = request.current_user['user_id']
    users = auth_service.get_all_users(admin_user_id)
    return jsonify(users)

@app.route('/api/admin/transcode/cleanup', methods=['POST'])
@require_auth
@require_admin
def api_cleanup_transcodes():
    """Clean up old transcoded files (admin only)"""
    max_age = int(request.args.get('max_age_hours', 24))
    transcoding_service.cleanup_old_transcodes(max_age)
    return jsonify({'message': 'Cleanup completed'})

# ===== TECHNICAL IMPROVEMENTS API ENDPOINTS =====

# Performance monitoring endpoints
@app.route('/api/monitoring/health')
@monitor_performance
def api_health_check():
    """System health check endpoint"""
    health_status = performance_monitor.get_health_status()
    return jsonify(health_status)

@app.route('/api/monitoring/performance')
@require_auth
@monitor_performance
def api_performance_summary():
    """Get performance summary"""
    summary = performance_monitor.get_performance_summary()
    return jsonify(summary)

@app.route('/api/monitoring/metrics')
@require_auth
@monitor_performance
def api_detailed_metrics():
    """Get detailed performance metrics"""
    hours = int(request.args.get('hours', 24))
    metrics = performance_monitor.get_detailed_metrics(hours)
    return jsonify(metrics)

@app.route('/api/monitoring/prometheus')
@monitor_performance
def api_prometheus_metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# Database management endpoints
@app.route('/api/admin/database/stats')
@require_auth
@require_admin
@monitor_performance
def api_database_stats():
    """Get database statistics"""
    stats = database_service.get_database_stats()
    return jsonify(stats)

@app.route('/api/admin/database/analyze')
@require_auth
@require_admin
@monitor_performance
def api_database_analyze():
    """Analyze database performance"""
    analysis = database_service.analyze_database()
    return jsonify(analysis)

@app.route('/api/admin/database/vacuum', methods=['POST'])
@require_auth
@require_admin
@monitor_performance
def api_database_vacuum():
    """Vacuum database to reclaim space"""
    success = database_service.vacuum_database()
    if success:
        return jsonify({'message': 'Database vacuum completed'})
    else:
        return jsonify({'error': 'Database vacuum failed'}), 500

@app.route('/api/admin/database/cleanup', methods=['POST'])
@require_auth
@require_admin
@monitor_performance
def api_database_cleanup():
    """Clean up old database data"""
    days = int(request.args.get('days', 30))
    cleanup_stats = database_service.cleanup_old_data(days)
    return jsonify(cleanup_stats)

@app.route('/api/admin/database/backup', methods=['POST'])
@require_auth
@require_admin
@monitor_performance
def api_database_backup():
    """Create database backup"""
    try:
        backup_path = database_service.backup_database()
        return jsonify({
            'message': 'Backup created successfully',
            'backup_path': backup_path
        })
    except Exception as e:
        return jsonify({'error': f'Backup failed: {str(e)}'}), 500

@app.route('/api/admin/database/restore', methods=['POST'])
@require_auth
@require_admin
@monitor_performance
def api_database_restore():
    """Restore database from backup"""
    data = request.get_json()
    backup_path = data.get('backup_path')
    
    if not backup_path:
        return jsonify({'error': 'Backup path required'}), 400
    
    success = database_service.restore_database(backup_path)
    if success:
        return jsonify({'message': 'Database restored successfully'})
    else:
        return jsonify({'error': 'Database restore failed'}), 500

# Cache management endpoints
@app.route('/api/admin/cache/stats')
@require_auth
@require_admin
@monitor_performance
def api_cache_stats():
    """Get cache statistics"""
    stats = cache_service.get_stats()
    return jsonify(stats)

@app.route('/api/admin/cache/clear', methods=['POST'])
@require_auth
@require_admin
@monitor_performance
def api_cache_clear():
    """Clear all cache data"""
    success = cache_service.clear_all()
    if success:
        return jsonify({'message': 'Cache cleared successfully'})
    else:
        return jsonify({'error': 'Cache clear failed'}), 500

@app.route('/api/admin/cache/clear-pattern', methods=['POST'])
@require_auth
@require_admin
@monitor_performance
def api_cache_clear_pattern():
    """Clear cache by pattern"""
    data = request.get_json()
    pattern = data.get('pattern')
    
    if not pattern:
        return jsonify({'error': 'Pattern required'}), 400
    
    deleted_count = cache_service.delete_pattern(pattern)
    return jsonify({
        'message': f'Cleared {deleted_count} cache entries',
        'deleted_count': deleted_count
    })

# API documentation endpoints
@app.route('/api/docs')
@monitor_performance
def api_docs():
    """API documentation page"""
    from flask import Response
    return Response(api_docs_service.get_api_docs_html(), mimetype='text/html')

@app.route('/api/docs/openapi.json')
@monitor_performance
def api_openapi_spec():
    """OpenAPI specification"""
    return jsonify(api_docs_service.get_openapi_spec())

# Enhanced media endpoints with caching
@app.route('/api/media')
@monitor_performance
@track_active_requests
@cached(ttl=300, key_prefix=CacheKeys.MEDIA_LIST)  # Cache for 5 minutes
def api_get_media_cached():
    """Get media library with caching"""
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
    
    media_files = database_service.execute_query(query, tuple(params))
    
    # Parse JSON fields
    for media in media_files:
        if media.get('genres'):
            try:
                media['genres'] = json.loads(media['genres']) if isinstance(media['genres'], str) else media['genres']
            except:
                media['genres'] = []
    
    return jsonify(media_files)

# Enhanced search with caching
@app.route('/api/search')
@monitor_performance
@track_active_requests
@cached(ttl=600, key_prefix=CacheKeys.SEARCH_RESULTS)  # Cache for 10 minutes
def api_search_cached():
    """Enhanced search with caching"""
    search_term = request.args.get('q', '')
    media_type = request.args.get('type')
    year_from = request.args.get('year_from')
    year_to = request.args.get('year_to')
    genres = request.args.get('genres')
    rating_min = request.args.get('rating_min')
    limit = int(request.args.get('limit', 50))
    
    filters = {
        'query': search_term,
        'media_type': media_type,
        'year_from': int(year_from) if year_from else None,
        'year_to': int(year_to) if year_to else None,
        'genres': genres.split(',') if genres else None,
        'rating_min': float(rating_min) if rating_min else None,
        'limit': limit
    }
    
    results = search_service.search_media(filters)
    return jsonify(results)

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
