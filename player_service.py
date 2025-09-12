# Advanced Media Player Service for Watch Media Server
import os
import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PlayerService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.init_player_tables()
    
    def init_player_tables(self):
        """Initialize player-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Playlists table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                is_public BOOLEAN DEFAULT 0,
                media_count INTEGER DEFAULT 0,
                total_duration INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Playlist items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id),
                UNIQUE(playlist_id, media_id)
            )
        ''')
        
        # Play queues table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS play_queues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                queue_name TEXT DEFAULT 'default',
                queue_data TEXT NOT NULL,
                current_position INTEGER DEFAULT 0,
                shuffle_mode BOOLEAN DEFAULT 0,
                repeat_mode TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Playback sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playback_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_time REAL DEFAULT 0,
                duration REAL DEFAULT 0,
                playback_rate REAL DEFAULT 1.0,
                volume REAL DEFAULT 1.0,
                is_paused BOOLEAN DEFAULT 0,
                quality TEXT DEFAULT 'auto',
                subtitles_enabled BOOLEAN DEFAULT 0,
                subtitle_track TEXT,
                audio_track TEXT,
                session_data TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        # Playback history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playback_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                session_id TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_watched REAL DEFAULT 0,
                total_duration REAL DEFAULT 0,
                completion_percentage REAL DEFAULT 0,
                quality_used TEXT,
                device_info TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        # Bookmarks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                bookmark_name TEXT,
                time_position REAL NOT NULL,
                thumbnail_url TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        # Player settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_name TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, setting_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_playlist(self, user_id: int, name: str, description: str = None, is_public: bool = False) -> int:
        """Create a new playlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO playlists 
                (user_id, name, description, is_public)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, description, is_public))
            
            playlist_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return playlist_id
        except Exception as e:
            logger.error(f"Error creating playlist: {e}")
            return None
    
    def add_to_playlist(self, playlist_id: int, media_id: int, position: int = None) -> bool:
        """Add media to playlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get next position if not specified
            if position is None:
                cursor.execute('''
                    SELECT COALESCE(MAX(position), 0) + 1 
                    FROM playlist_items 
                    WHERE playlist_id = ?
                ''', (playlist_id,))
                position = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO playlist_items 
                (playlist_id, media_id, position)
                VALUES (?, ?, ?)
            ''', (playlist_id, media_id, position))
            
            # Update playlist stats
            cursor.execute('''
                UPDATE playlists 
                SET media_count = (
                    SELECT COUNT(*) FROM playlist_items WHERE playlist_id = ?
                ),
                total_duration = (
                    SELECT COALESCE(SUM(mf.duration), 0) 
                    FROM playlist_items pi 
                    JOIN media_files mf ON pi.media_id = mf.id 
                    WHERE pi.playlist_id = ?
                ),
                updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (playlist_id, playlist_id, playlist_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding to playlist: {e}")
            return False
    
    def get_playlist(self, playlist_id: int, user_id: int = None) -> Optional[Dict]:
        """Get playlist with items"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get playlist info
            query = '''
                SELECT p.*, u.username 
                FROM playlists p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = ?
            '''
            params = [playlist_id]
            
            if user_id:
                query += ' AND (p.user_id = ? OR p.is_public = 1)'
                params.append(user_id)
            
            cursor.execute(query, params)
            playlist = cursor.fetchone()
            
            if not playlist:
                conn.close()
                return None
            
            playlist_dict = dict(playlist)
            
            # Get playlist items
            cursor.execute('''
                SELECT pi.*, mf.*
                FROM playlist_items pi
                JOIN media_files mf ON pi.media_id = mf.id
                WHERE pi.playlist_id = ?
                ORDER BY pi.position
            ''', (playlist_id,))
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                # Parse JSON fields
                if item.get('genres'):
                    try:
                        item['genres'] = json.loads(item['genres']) if isinstance(item['genres'], str) else item['genres']
                    except:
                        item['genres'] = []
                items.append(item)
            
            playlist_dict['items'] = items
            conn.close()
            return playlist_dict
        except Exception as e:
            logger.error(f"Error getting playlist: {e}")
            return None
    
    def get_user_playlists(self, user_id: int, include_public: bool = True) -> List[Dict]:
        """Get user's playlists"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM playlists 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if include_public:
                query += ' OR is_public = 1'
            
            query += ' ORDER BY updated_at DESC'
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting user playlists: {e}")
            return []
    
    def create_play_queue(self, user_id: int, queue_name: str, media_ids: List[int]) -> bool:
        """Create or update play queue"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            queue_data = {
                'media_ids': media_ids,
                'created_at': datetime.now().isoformat()
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO play_queues 
                (user_id, queue_name, queue_data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, queue_name, json.dumps(queue_data)))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating play queue: {e}")
            return False
    
    def get_play_queue(self, user_id: int, queue_name: str = 'default') -> Optional[Dict]:
        """Get play queue"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM play_queues 
                WHERE user_id = ? AND queue_name = ?
            ''', (user_id, queue_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                queue = dict(result)
                try:
                    queue['queue_data'] = json.loads(queue['queue_data'])
                except:
                    queue['queue_data'] = {}
                return queue
            
            return None
        except Exception as e:
            logger.error(f"Error getting play queue: {e}")
            return None
    
    def start_playback_session(self, user_id: int, media_id: int, session_id: str = None) -> str:
        """Start a new playback session"""
        try:
            if not session_id:
                session_id = f"{user_id}_{media_id}_{int(datetime.now().timestamp())}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # End any existing session for this user
            cursor.execute('''
                UPDATE playback_sessions 
                SET end_time = CURRENT_TIMESTAMP
                WHERE user_id = ? AND end_time IS NULL
            ''', (user_id,))
            
            # Create new session
            cursor.execute('''
                INSERT OR REPLACE INTO playback_sessions 
                (user_id, media_id, session_id, start_time, last_activity)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, media_id, session_id))
            
            conn.commit()
            conn.close()
            return session_id
        except Exception as e:
            logger.error(f"Error starting playback session: {e}")
            return None
    
    def update_playback_session(self, session_id: str, **kwargs) -> bool:
        """Update playback session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query
            update_fields = []
            params = []
            
            for key, value in kwargs.items():
                if key in ['current_time', 'duration', 'playback_rate', 'volume', 'is_paused', 
                          'quality', 'subtitles_enabled', 'subtitle_track', 'audio_track']:
                    update_fields.append(f"{key} = ?")
                    params.append(value)
                elif key == 'session_data':
                    update_fields.append("session_data = ?")
                    params.append(json.dumps(value))
            
            if update_fields:
                update_fields.append("last_activity = CURRENT_TIMESTAMP")
                params.append(session_id)
                
                query = f"UPDATE playback_sessions SET {', '.join(update_fields)} WHERE session_id = ?"
                cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating playback session: {e}")
            return False
    
    def end_playback_session(self, session_id: str) -> bool:
        """End playback session and record history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session data
            cursor.execute('''
                SELECT * FROM playback_sessions 
                WHERE session_id = ?
            ''', (session_id,))
            
            session = cursor.fetchone()
            if not session:
                conn.close()
                return False
            
            # Calculate completion percentage
            duration_watched = session[6]  # current_time
            total_duration = session[7]    # duration
            completion_percentage = (duration_watched / total_duration * 100) if total_duration > 0 else 0
            
            # Record in history
            cursor.execute('''
                INSERT INTO playback_history 
                (user_id, media_id, session_id, start_time, end_time, 
                 duration_watched, total_duration, completion_percentage, quality_used)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            ''', (session[1], session[2], session_id, session[3], 
                  duration_watched, total_duration, completion_percentage, session[9]))
            
            # Update session
            cursor.execute('''
                UPDATE playback_sessions 
                SET end_time = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error ending playback session: {e}")
            return False
    
    def get_playback_session(self, session_id: str) -> Optional[Dict]:
        """Get playback session"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM playback_sessions 
                WHERE session_id = ?
            ''', (session_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                session = dict(result)
                try:
                    session['session_data'] = json.loads(session['session_data'])
                except:
                    session['session_data'] = {}
                return session
            
            return None
        except Exception as e:
            logger.error(f"Error getting playback session: {e}")
            return None
    
    def create_bookmark(self, user_id: int, media_id: int, time_position: float, 
                       bookmark_name: str = None, notes: str = None) -> int:
        """Create a bookmark"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO media_bookmarks 
                (user_id, media_id, bookmark_name, time_position, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, media_id, bookmark_name, time_position, notes))
            
            bookmark_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return bookmark_id
        except Exception as e:
            logger.error(f"Error creating bookmark: {e}")
            return None
    
    def get_media_bookmarks(self, media_id: int, user_id: int = None) -> List[Dict]:
        """Get bookmarks for media"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT mb.*, u.username, up.display_name
                FROM media_bookmarks mb
                JOIN users u ON mb.user_id = u.id
                LEFT JOIN user_profiles up ON u.id = up.user_id
                WHERE mb.media_id = ?
            '''
            params = [media_id]
            
            if user_id:
                query += ' AND mb.user_id = ?'
                params.append(user_id)
            
            query += ' ORDER BY mb.time_position'
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting media bookmarks: {e}")
            return []
    
    def get_player_settings(self, user_id: int) -> Dict:
        """Get player settings for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT setting_name, setting_value 
                FROM player_settings 
                WHERE user_id = ?
            ''', (user_id,))
            
            settings = {}
            for row in cursor.fetchall():
                try:
                    settings[row['setting_name']] = json.loads(row['setting_value'])
                except:
                    settings[row['setting_name']] = row['setting_value']
            
            conn.close()
            return settings
        except Exception as e:
            logger.error(f"Error getting player settings: {e}")
            return {}
    
    def update_player_setting(self, user_id: int, setting_name: str, setting_value: Any) -> bool:
        """Update player setting"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO player_settings 
                (user_id, setting_name, setting_value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, setting_name, json.dumps(setting_value)))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating player setting: {e}")
            return False
    
    def get_playback_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's playback history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ph.*, mf.filename, mf.title, mf.poster_url
                FROM playback_history ph
                JOIN media_files mf ON ph.media_id = mf.id
                WHERE ph.user_id = ?
                ORDER BY ph.start_time DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                history = dict(row)
                try:
                    history['device_info'] = json.loads(history['device_info'])
                except:
                    history['device_info'] = {}
                results.append(history)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting playback history: {e}")
            return []
    
    def get_continue_watching(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get continue watching list"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT ps.media_id, ps.current_time, ps.duration, 
                       ps.last_activity, mf.filename, mf.title, mf.poster_url
                FROM playback_sessions ps
                JOIN media_files mf ON ps.media_id = mf.id
                WHERE ps.user_id = ? AND ps.end_time IS NULL 
                AND ps.current_time > 0 AND ps.current_time < ps.duration
                ORDER BY ps.last_activity DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting continue watching: {e}")
            return []

# Player service instance
player_service = PlayerService()
