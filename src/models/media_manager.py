"""
Media Manager Model
Handles media file operations, database management, and metadata extraction
"""

import os
import sqlite3
import json
import hashlib
import subprocess
import logging

logger = logging.getLogger(__name__)


class MediaManager:
    def __init__(self, db_path, media_library_path):
        self.db_path = db_path
        self.media_library_path = media_library_path
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
            ('library_path', self.media_library_path),
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
        library_path = self.get_setting('library_path', self.media_library_path)
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
