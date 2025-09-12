# Authentication Service for Watch Media Server
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import sqlite3
import json
from functools import wraps
from flask import request, jsonify, current_app

class AuthService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'watch-media-server-secret-key')
        self.jwt_expiration = int(os.getenv('JWT_EXPIRATION_HOURS', '24')) * 3600
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialize authentication-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                preferences TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                avatar_url TEXT
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User watchlists table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_watchlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                media_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                watched BOOLEAN DEFAULT 0,
                rating INTEGER,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id),
                UNIQUE(user_id, media_id)
            )
        ''')
        
        # User play history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_play_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                media_id INTEGER,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_watched INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        # User recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                media_id INTEGER,
                score REAL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        # Create default admin user if no users exist
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            self.create_default_admin()
        
        conn.commit()
        conn.close()
    
    def create_default_admin(self):
        """Create default admin user"""
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@watch.local')
        
        self.create_user(
            username='admin',
            email=admin_email,
            password=admin_password,
            role='admin'
        )
        print(f"Created default admin user: admin / {admin_password}")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> Optional[Dict]:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                conn.close()
                return None
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return self.get_user_by_id(user_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, role, preferences, is_active
                FROM users WHERE username = ? OR email = ?
            ''', (username, username))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return None
            
            user_id, db_username, email, password_hash, role, preferences, is_active = result
            
            if not is_active:
                conn.close()
                return None
            
            if not self.verify_password(password, password_hash):
                conn.close()
                return None
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
            
            return {
                'id': user_id,
                'username': db_username,
                'email': email,
                'role': role,
                'preferences': json.loads(preferences) if preferences else {},
                'is_active': bool(is_active)
            }
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def generate_token(self, user_id: int, username: str, role: str) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(seconds=self.jwt_expiration),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, preferences, created_at, last_login, is_active, avatar_url
                FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return None
            
            user_id, username, email, role, preferences, created_at, last_login, is_active, avatar_url = result
            
            conn.close()
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'preferences': json.loads(preferences) if preferences else {},
                'created_at': created_at,
                'last_login': last_login,
                'is_active': bool(is_active),
                'avatar_url': avatar_url
            }
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """Update user preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET preferences = ? WHERE id = ?
            ''', (json.dumps(preferences), user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False
    
    def add_to_watchlist(self, user_id: int, media_id: int) -> bool:
        """Add media to user's watchlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_watchlists (user_id, media_id)
                VALUES (?, ?)
            ''', (user_id, media_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding to watchlist: {e}")
            return False
    
    def remove_from_watchlist(self, user_id: int, media_id: int) -> bool:
        """Remove media from user's watchlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM user_watchlists WHERE user_id = ? AND media_id = ?
            ''', (user_id, media_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error removing from watchlist: {e}")
            return False
    
    def get_user_watchlist(self, user_id: int) -> List[Dict]:
        """Get user's watchlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.*, wl.added_at, wl.watched, wl.rating, wl.notes
                FROM user_watchlists wl
                JOIN media_files m ON wl.media_id = m.id
                WHERE wl.user_id = ?
                ORDER BY wl.added_at DESC
            ''', (user_id,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                if result.get('genres'):
                    try:
                        result['genres'] = json.loads(result['genres']) if isinstance(result['genres'], str) else result['genres']
                    except:
                        result['genres'] = []
                results.append(result)
            
            conn.close()
            return results
        except Exception as e:
            print(f"Error getting watchlist: {e}")
            return []
    
    def record_play(self, user_id: int, media_id: int, duration_watched: int = 0, completed: bool = False):
        """Record a play event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_play_history (user_id, media_id, duration_watched, completed)
                VALUES (?, ?, ?, ?)
            ''', (user_id, media_id, duration_watched, completed))
            
            # Update watchlist if completed
            if completed:
                cursor.execute('''
                    UPDATE user_watchlists SET watched = 1 WHERE user_id = ? AND media_id = ?
                ''', (user_id, media_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error recording play: {e}")
            return False
    
    def get_user_play_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's play history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.*, ph.played_at, ph.duration_watched, ph.completed
                FROM user_play_history ph
                JOIN media_files m ON ph.media_id = m.id
                WHERE ph.user_id = ?
                ORDER BY ph.played_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('genres'):
                    try:
                        result['genres'] = json.loads(result['genres']) if isinstance(result['genres'], str) else result['genres']
                    except:
                        result['genres'] = []
                results.append(result)
            
            conn.close()
            return results
        except Exception as e:
            print(f"Error getting play history: {e}")
            return []
    
    def get_continue_watching(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's continue watching list"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.*, ph.duration_watched, ph.played_at
                FROM user_play_history ph
                JOIN media_files m ON ph.media_id = m.id
                WHERE ph.user_id = ? AND ph.completed = 0
                ORDER BY ph.played_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('genres'):
                    try:
                        result['genres'] = json.loads(result['genres']) if isinstance(result['genres'], str) else result['genres']
                    except:
                        result['genres'] = []
                results.append(result)
            
            conn.close()
            return results
        except Exception as e:
            print(f"Error getting continue watching: {e}")
            return []
    
    def generate_recommendations(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Generate recommendations for user based on watch history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get user's watched genres
            cursor.execute('''
                SELECT DISTINCT m.genres
                FROM user_play_history ph
                JOIN media_files m ON ph.media_id = m.id
                WHERE ph.user_id = ? AND ph.completed = 1
            ''', (user_id,))
            
            watched_genres = set()
            for row in cursor.fetchall():
                if row['genres']:
                    try:
                        genres = json.loads(row['genres']) if isinstance(row['genres'], str) else row['genres']
                        watched_genres.update(genres)
                    except:
                        pass
            
            if not watched_genres:
                # If no history, return popular media
                cursor.execute('''
                    SELECT m.*, COUNT(ph.id) as play_count
                    FROM media_files m
                    LEFT JOIN user_play_history ph ON m.id = ph.media_id
                    WHERE m.id NOT IN (
                        SELECT media_id FROM user_play_history WHERE user_id = ?
                    )
                    GROUP BY m.id
                    ORDER BY play_count DESC, m.rating DESC
                    LIMIT ?
                ''', (user_id, limit))
            else:
                # Find similar content
                genre_conditions = []
                params = [user_id]
                for genre in list(watched_genres)[:5]:  # Limit to top 5 genres
                    genre_conditions.append("m.genres LIKE ?")
                    params.append(f"%{genre}%")
                
                params.append(limit)
                
                cursor.execute(f'''
                    SELECT m.*, COUNT(ph.id) as play_count
                    FROM media_files m
                    LEFT JOIN user_play_history ph ON m.id = ph.media_id
                    WHERE m.id NOT IN (
                        SELECT media_id FROM user_play_history WHERE user_id = ?
                    ) AND ({' OR '.join(genre_conditions)})
                    GROUP BY m.id
                    ORDER BY play_count DESC, m.rating DESC
                    LIMIT ?
                ''', params)
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('genres'):
                    try:
                        result['genres'] = json.loads(result['genres']) if isinstance(result['genres'], str) else result['genres']
                    except:
                        result['genres'] = []
                results.append(result)
            
            conn.close()
            return results
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def get_all_users(self, admin_user_id: int) -> List[Dict]:
        """Get all users (admin only)"""
        try:
            # Verify admin
            admin_user = self.get_user_by_id(admin_user_id)
            if not admin_user or admin_user['role'] != 'admin':
                return []
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            ''')
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            conn.close()
            return results
        except Exception as e:
            print(f"Error getting users: {e}")
            return []

# Decorator for protected routes
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        # Check for token in cookies
        if not token:
            token = request.cookies.get('access_token')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            auth_service = AuthService()
            payload = auth_service.verify_token(token)
            if not payload:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            
            # Add user info to request context
            request.current_user = payload
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Token verification failed'}), 401
    
    return decorated_function

# Decorator for admin-only routes
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function
