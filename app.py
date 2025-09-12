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
                metadata TEXT  -- JSON string for additional metadata
            )
        ''')
        
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
        media_manager.scan_media_library()
        socketio.emit('scan_complete', {'status': 'success'})
    
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
    return jsonify({'status': 'success'})

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
