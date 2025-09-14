#!/usr/bin/env python3
"""
Media Formatter and Organizer
Handles file organization, renaming, and metadata enhancement
"""

import os
import re
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)

class MediaFormatter:
    def __init__(self, media_manager):
        self.media_manager = media_manager
        self.organize_rules = {
            'movies': {
                'pattern': r'^(.*?)\s*\((\d{4})\)',
                'folder_structure': '{title} ({year})',
                'file_naming': '{title} ({year}){extension}'
            },
            'tv_shows': {
                'pattern': r'^(.*?)\s*-\s*[Ss](\d+)[Ee](\d+)',
                'folder_structure': '{title}/Season {season:02d}',
                'file_naming': '{title} - S{season:02d}E{episode:02d}{extension}'
            }
        }
    
    def organize_library(self, dry_run=True):
        """Organize the entire media library according to naming conventions"""
        logger.info(f"Starting library organization (dry_run={dry_run})")
        
        conn = sqlite3.connect(self.media_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media_files")
        files = cursor.fetchall()
        conn.close()
        
        organized_count = 0
        errors = []
        
        for file_data in files:
            try:
                file_id, file_path, file_name, media_type = file_data[0], file_data[1], file_data[2], file_data[5]
                
                if self.organize_file(file_path, media_type, dry_run):
                    organized_count += 1
                    
            except Exception as e:
                error_msg = f"Error organizing {file_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Organization complete. {organized_count} files processed, {len(errors)} errors")
        return {
            'organized_count': organized_count,
            'errors': errors,
            'dry_run': dry_run
        }
    
    def organize_file(self, file_path, media_type, dry_run=True):
        """Organize a single file according to its type"""
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return False
        
        file_name = os.path.basename(file_path)
        file_dir = os.path.dirname(file_path)
        file_ext = os.path.splitext(file_name)[1]
        
        # Extract metadata from filename
        metadata = self.extract_filename_metadata(file_name, media_type)
        
        if not metadata:
            logger.warning(f"Could not extract metadata from: {file_name}")
            return False
        
        # Generate new path
        new_path = self.generate_organized_path(file_dir, metadata, file_ext, media_type)
        
        if new_path == file_path:
            logger.info(f"File already organized: {file_name}")
            return True
        
        if dry_run:
            logger.info(f"Would move: {file_path} -> {new_path}")
            return True
        
        # Create directory if it doesn't exist
        new_dir = os.path.dirname(new_path)
        os.makedirs(new_dir, exist_ok=True)
        
        # Move file
        try:
            shutil.move(file_path, new_path)
            logger.info(f"Moved: {file_path} -> {new_path}")
            
            # Update database
            self.update_file_path_in_db(file_path, new_path)
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {file_path}: {e}")
            return False
    
    def extract_filename_metadata(self, filename, media_type):
        """Extract metadata from filename"""
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        if media_type == 'movie':
            return self.extract_movie_metadata(name_without_ext)
        elif media_type == 'tv_show':
            return self.extract_tv_metadata(name_without_ext)
        
        return None
    
    def extract_movie_metadata(self, filename):
        """Extract movie metadata from filename"""
        # Common movie patterns
        patterns = [
            r'^(.*?)\s*\((\d{4})\)',  # Title (Year)
            r'^(.*?)\s*\[(\d{4})\]',  # Title [Year]
            r'^(.*?)\s*\.(\d{4})',    # Title.Year
            r'^(.*?)\s*(\d{4})',      # Title Year
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                year = int(match.group(2))
                
                # Clean up title
                title = re.sub(r'[._-]', ' ', title)
                title = re.sub(r'\s+', ' ', title).strip()
                
                return {
                    'title': title,
                    'year': year,
                    'type': 'movie'
                }
        
        # Fallback: use entire filename as title
        title = re.sub(r'[._-]', ' ', filename)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return {
            'title': title,
            'year': None,
            'type': 'movie'
        }
    
    def extract_tv_metadata(self, filename):
        """Extract TV show metadata from filename"""
        # Common TV show patterns
        patterns = [
            r'^(.*?)\s*-\s*[Ss](\d+)[Ee](\d+)',  # Title - S01E01
            r'^(.*?)\s*[Ss](\d+)[Ee](\d+)',      # Title S01E01
            r'^(.*?)\s*\.(\d+)\.(\d+)',          # Title.1.1
            r'^(.*?)\s*(\d+)x(\d+)',             # Title 1x1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                season = int(match.group(2))
                episode = int(match.group(3))
                
                # Clean up title
                title = re.sub(r'[._-]', ' ', title)
                title = re.sub(r'\s+', ' ', title).strip()
                
                return {
                    'title': title,
                    'season': season,
                    'episode': episode,
                    'type': 'tv_show'
                }
        
        # Fallback: use entire filename as title
        title = re.sub(r'[._-]', ' ', filename)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return {
            'title': title,
            'season': None,
            'episode': None,
            'type': 'tv_show'
        }
    
    def generate_organized_path(self, base_dir, metadata, extension, media_type):
        """Generate organized file path"""
        if media_type == 'movie':
            return self.generate_movie_path(base_dir, metadata, extension)
        elif media_type == 'tv_show':
            return self.generate_tv_path(base_dir, metadata, extension)
        
        return None
    
    def generate_movie_path(self, base_dir, metadata, extension):
        """Generate organized movie path"""
        title = metadata['title']
        year = metadata.get('year')
        
        # Clean title for filesystem
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        if year:
            folder_name = f"{clean_title} ({year})"
            file_name = f"{clean_title} ({year}){extension}"
        else:
            folder_name = clean_title
            file_name = f"{clean_title}{extension}"
        
        return os.path.join(base_dir, folder_name, file_name)
    
    def generate_tv_path(self, base_dir, metadata, extension):
        """Generate organized TV show path"""
        title = metadata['title']
        season = metadata.get('season')
        episode = metadata.get('episode')
        
        # Clean title for filesystem
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        if season and episode:
            folder_name = f"{clean_title}/Season {season:02d}"
            file_name = f"{clean_title} - S{season:02d}E{episode:02d}{extension}"
        else:
            folder_name = clean_title
            file_name = f"{clean_title}{extension}"
        
        return os.path.join(base_dir, folder_name, file_name)
    
    def update_file_path_in_db(self, old_path, new_path):
        """Update file path in database"""
        conn = sqlite3.connect(self.media_manager.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE media_files SET file_path = ? WHERE file_path = ?",
            (new_path, old_path)
        )
        conn.commit()
        conn.close()
    
    def create_playlist(self, name, media_ids, description=""):
        """Create a playlist from media IDs"""
        conn = sqlite3.connect(self.media_manager.db_path)
        cursor = conn.cursor()
        
        # Create playlists table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                media_ids TEXT NOT NULL,  -- JSON array of media IDs
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert playlist
        cursor.execute('''
            INSERT OR REPLACE INTO playlists (name, description, media_ids)
            VALUES (?, ?, ?)
        ''', (name, description, json.dumps(media_ids)))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created playlist: {name} with {len(media_ids)} items")
    
    def get_playlists(self):
        """Get all playlists"""
        conn = sqlite3.connect(self.media_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM playlists ORDER BY name')
        columns = [description[0] for description in cursor.description]
        playlists = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return playlists
    
    def add_to_playlist(self, playlist_name, media_id):
        """Add media to playlist"""
        conn = sqlite3.connect(self.media_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT media_ids FROM playlists WHERE name = ?', (playlist_name,))
        result = cursor.fetchone()
        
        if result:
            media_ids = json.loads(result[0])
            if media_id not in media_ids:
                media_ids.append(media_id)
                cursor.execute(
                    'UPDATE playlists SET media_ids = ?, last_modified = CURRENT_TIMESTAMP WHERE name = ?',
                    (json.dumps(media_ids), playlist_name)
                )
                conn.commit()
        
        conn.close()
    
    def remove_from_playlist(self, playlist_name, media_id):
        """Remove media from playlist"""
        conn = sqlite3.connect(self.media_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT media_ids FROM playlists WHERE name = ?', (playlist_name,))
        result = cursor.fetchone()
        
        if result:
            media_ids = json.loads(result[0])
            if media_id in media_ids:
                media_ids.remove(media_id)
                cursor.execute(
                    'UPDATE playlists SET media_ids = ?, last_modified = CURRENT_TIMESTAMP WHERE name = ?',
                    (json.dumps(media_ids), playlist_name)
                )
                conn.commit()
        
        conn.close()
    
    def generate_report(self):
        """Generate library organization report"""
        conn = sqlite3.connect(self.media_manager.db_path)
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM media_files")
        total_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT media_type, COUNT(*) FROM media_files GROUP BY media_type")
        by_type = dict(cursor.fetchall())
        
        cursor.execute("SELECT SUM(file_size) FROM media_files")
        total_size = cursor.fetchone()[0] or 0
        
        # Get files that need organization
        cursor.execute("SELECT file_path, media_type FROM media_files")
        files = cursor.fetchall()
        
        needs_organization = []
        for file_path, media_type in files:
            if not self.is_properly_organized(file_path, media_type):
                needs_organization.append((file_path, media_type))
        
        conn.close()
        
        report = {
            'total_files': total_files,
            'by_type': by_type,
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'needs_organization': len(needs_organization),
            'files_needing_organization': needs_organization[:10],  # First 10
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def is_properly_organized(self, file_path, media_type):
        """Check if file is properly organized"""
        filename = os.path.basename(file_path)
        dirname = os.path.basename(os.path.dirname(file_path))
        
        if media_type == 'movie':
            # Check if it follows "Title (Year)" pattern
            return bool(re.search(r'\((\d{4})\)', dirname))
        elif media_type == 'tv_show':
            # Check if it's in a Season folder and has proper episode naming
            return ('Season' in dirname and 
                   bool(re.search(r'[Ss]\d+[Ee]\d+', filename)))
        
        return False
