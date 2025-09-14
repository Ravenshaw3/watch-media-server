# External Services Integration Service for Watch Media Server
import os
import json
import requests
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode, parse_qs

# Optional imports for integrations
try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False

try:
    import facebook
    FACEBOOK_AVAILABLE = True
except ImportError:
    FACEBOOK_AVAILABLE = False

try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExternalServicesService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.init_external_services_tables()
        self.service_configs = self._get_service_configs()
    
    def init_external_services_tables(self):
        """Initialize external services database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # External service connections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS external_service_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at TIMESTAMP,
                service_data TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, service_name)
            )
        ''')
        
        # Webhook subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                webhook_url TEXT NOT NULL,
                event_types TEXT NOT NULL,
                secret_key TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_triggered TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Scheduled tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                schedule_expression TEXT NOT NULL,
                task_data TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Integration logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integration_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT DEFAULT '{}',
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_service_configs(self) -> Dict:
        """Get external service configurations"""
        return {
            'trakt': {
                'base_url': 'https://api.trakt.tv',
                'client_id': os.getenv('TRAKT_CLIENT_ID'),
                'client_secret': os.getenv('TRAKT_CLIENT_SECRET'),
                'auth_url': 'https://api.trakt.tv/oauth/authorize',
                'token_url': 'https://api.trakt.tv/oauth/token',
                'scopes': ['read', 'write']
            },
            'letterboxd': {
                'base_url': 'https://api.letterboxd.com',
                'api_key': os.getenv('LETTERBOXD_API_KEY'),
                'api_secret': os.getenv('LETTERBOXD_API_SECRET'),
                'auth_url': 'https://letterboxd.com/api/v0/auth',
                'scopes': ['read', 'write']
            },
            'imdb': {
                'base_url': 'https://imdb-api.com',
                'api_key': os.getenv('IMDB_API_KEY'),
                'scopes': ['read']
            },
            'dropbox': {
                'base_url': 'https://api.dropboxapi.com',
                'client_id': os.getenv('DROPBOX_CLIENT_ID'),
                'client_secret': os.getenv('DROPBOX_CLIENT_SECRET'),
                'auth_url': 'https://www.dropbox.com/oauth2/authorize',
                'token_url': 'https://api.dropboxapi.com/oauth2/token',
                'scopes': ['files.metadata.read', 'files.content.read']
            },
            'google_drive': {
                'base_url': 'https://www.googleapis.com/drive/v3',
                'client_id': os.getenv('GOOGLE_DRIVE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_DRIVE_CLIENT_SECRET'),
                'auth_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'scopes': ['https://www.googleapis.com/auth/drive.readonly']
            },
            'twitter': {
                'base_url': 'https://api.twitter.com/2',
                'api_key': os.getenv('TWITTER_API_KEY'),
                'api_secret': os.getenv('TWITTER_API_SECRET'),
                'bearer_token': os.getenv('TWITTER_BEARER_TOKEN'),
                'scopes': ['tweet.read', 'tweet.write', 'users.read']
            },
            'facebook': {
                'base_url': 'https://graph.facebook.com/v18.0',
                'app_id': os.getenv('FACEBOOK_APP_ID'),
                'app_secret': os.getenv('FACEBOOK_APP_SECRET'),
                'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'scopes': ['pages_manage_posts', 'pages_read_engagement']
            },
            'telegram': {
                'base_url': 'https://api.telegram.org/bot',
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'scopes': ['send_message', 'send_photo', 'send_video']
            }
        }
    
    def get_auth_url(self, service_name: str, user_id: int, redirect_uri: str) -> Optional[str]:
        """Get OAuth authorization URL for external service"""
        if service_name not in self.service_configs:
            return None
        
        config = self.service_configs[service_name]
        
        # Store state for security
        state = f"{user_id}_{service_name}_{int(datetime.now().timestamp())}"
        
        params = {
            'client_id': config.get('client_id') or config.get('api_key') or config.get('app_id'),
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': ' '.join(config.get('scopes', []))
        }
        
        # Service-specific parameters
        if service_name == 'trakt':
            params['response_type'] = 'code'
        elif service_name == 'google_drive':
            params['access_type'] = 'offline'
            params['prompt'] = 'consent'
        
        auth_url = config['auth_url'] + '?' + urlencode(params)
        
        # Store state in database for verification
        self._store_auth_state(user_id, service_name, state)
        
        return auth_url
    
    def _store_auth_state(self, user_id: int, service_name: str, state: str):
        """Store OAuth state for verification"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO external_service_connections 
                (user_id, service_name, service_type, service_data, updated_at)
                VALUES (?, ?, 'oauth', ?, CURRENT_TIMESTAMP)
            ''', (user_id, service_name, json.dumps({'auth_state': state})))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing auth state: {e}")
    
    def handle_oauth_callback(self, service_name: str, user_id: int, code: str, state: str) -> bool:
        """Handle OAuth callback and exchange code for tokens"""
        try:
            # Verify state
            if not self._verify_auth_state(user_id, service_name, state):
                return False
            
            config = self.service_configs[service_name]
            
            # Exchange code for tokens
            token_data = self._exchange_code_for_tokens(service_name, code, config)
            if not token_data:
                return False
            
            # Store tokens
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO external_service_connections 
                (user_id, service_name, service_type, access_token, refresh_token, 
                 token_expires_at, service_data, is_active, updated_at)
                VALUES (?, ?, 'oauth', ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', (
                user_id, service_name,
                token_data.get('access_token'),
                token_data.get('refresh_token'),
                token_data.get('expires_at'),
                json.dumps(token_data.get('service_data', {}))
            ))
            
            conn.commit()
            conn.close()
            
            # Log successful connection
            self._log_integration_event(service_name, 'oauth_success', {
                'user_id': user_id,
                'service': service_name
            }, 'success')
            
            return True
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            self._log_integration_event(service_name, 'oauth_error', {
                'user_id': user_id,
                'error': str(e)
            }, 'error', str(e))
            return False
    
    def _verify_auth_state(self, user_id: int, service_name: str, state: str) -> bool:
        """Verify OAuth state"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT service_data FROM external_service_connections 
                WHERE user_id = ? AND service_name = ? AND service_type = 'oauth'
            ''', (user_id, service_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                service_data = json.loads(result[0])
                return service_data.get('auth_state') == state
            
            return False
        except Exception as e:
            logger.error(f"Error verifying auth state: {e}")
            return False
    
    def _exchange_code_for_tokens(self, service_name: str, code: str, config: Dict) -> Optional[Dict]:
        """Exchange OAuth code for access tokens"""
        try:
            token_url = config['token_url']
            
            data = {
                'client_id': config.get('client_id') or config.get('api_key') or config.get('app_id'),
                'client_secret': config.get('client_secret') or config.get('api_secret'),
                'code': code,
                'grant_type': 'authorization_code'
            }
            
            # Service-specific token exchange
            if service_name == 'trakt':
                data['redirect_uri'] = config.get('redirect_uri')
            elif service_name == 'google_drive':
                data['redirect_uri'] = config.get('redirect_uri')
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return {
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': expires_at.isoformat(),
                'service_data': token_data
            }
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            return None
    
    def get_service_connection(self, user_id: int, service_name: str) -> Optional[Dict]:
        """Get user's connection to external service"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM external_service_connections 
                WHERE user_id = ? AND service_name = ? AND is_active = 1
            ''', (user_id, service_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                connection = dict(result)
                try:
                    connection['service_data'] = json.loads(connection['service_data'])
                except:
                    connection['service_data'] = {}
                return connection
            
            return None
        except Exception as e:
            logger.error(f"Error getting service connection: {e}")
            return None
    
    def sync_with_trakt(self, user_id: int) -> bool:
        """Sync watchlist and history with Trakt.tv"""
        try:
            connection = self.get_service_connection(user_id, 'trakt')
            if not connection:
                return False
            
            access_token = connection['access_token']
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'trakt-api-version': '2',
                'trakt-api-key': self.service_configs['trakt']['client_id']
            }
            
            # Get user's Trakt watchlist
            response = requests.get(
                f"{self.service_configs['trakt']['base_url']}/users/me/watchlist/movies",
                headers=headers
            )
            response.raise_for_status()
            
            trakt_watchlist = response.json()
            
            # Sync with local watchlist
            self._sync_trakt_watchlist(user_id, trakt_watchlist)
            
            # Get user's Trakt history
            response = requests.get(
                f"{self.service_configs['trakt']['base_url']}/users/me/history/movies",
                headers=headers
            )
            response.raise_for_status()
            
            trakt_history = response.json()
            
            # Sync with local history
            self._sync_trakt_history(user_id, trakt_history)
            
            self._log_integration_event('trakt', 'sync_success', {
                'user_id': user_id,
                'watchlist_count': len(trakt_watchlist),
                'history_count': len(trakt_history)
            }, 'success')
            
            return True
        except Exception as e:
            logger.error(f"Error syncing with Trakt: {e}")
            self._log_integration_event('trakt', 'sync_error', {
                'user_id': user_id,
                'error': str(e)
            }, 'error', str(e))
            return False
    
    def _sync_trakt_watchlist(self, user_id: int, trakt_watchlist: List[Dict]):
        """Sync Trakt watchlist with local watchlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for item in trakt_watchlist:
                movie = item.get('movie', {})
                trakt_id = movie.get('ids', {}).get('trakt')
                imdb_id = movie.get('ids', {}).get('imdb')
                
                if trakt_id:
                    # Find local media by Trakt ID or IMDb ID
                    cursor.execute('''
                        SELECT id FROM media_files 
                        WHERE tmdb_id = ? OR imdb_id = ?
                    ''', (trakt_id, imdb_id))
                    
                    result = cursor.fetchone()
                    if result:
                        media_id = result[0]
                        
                        # Add to local watchlist if not already there
                        cursor.execute('''
                            INSERT OR IGNORE INTO user_watchlists (user_id, media_id)
                            VALUES (?, ?)
                        ''', (user_id, media_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error syncing Trakt watchlist: {e}")
    
    def _sync_trakt_history(self, user_id: int, trakt_history: List[Dict]):
        """Sync Trakt history with local history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for item in trakt_history:
                movie = item.get('movie', {})
                trakt_id = movie.get('ids', {}).get('trakt')
                imdb_id = movie.get('ids', {}).get('imdb')
                watched_at = item.get('watched_at')
                
                if trakt_id and watched_at:
                    # Find local media by Trakt ID or IMDb ID
                    cursor.execute('''
                        SELECT id FROM media_files 
                        WHERE tmdb_id = ? OR imdb_id = ?
                    ''', (trakt_id, imdb_id))
                    
                    result = cursor.fetchone()
                    if result:
                        media_id = result[0]
                        
                        # Add to local history if not already there
                        cursor.execute('''
                            INSERT OR IGNORE INTO user_play_history 
                            (user_id, media_id, played_at, completed)
                            VALUES (?, ?, ?, 1)
                        ''', (user_id, media_id, watched_at, 1))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error syncing Trakt history: {e}")
    
    def share_to_twitter(self, user_id: int, media_id: int, message: str = None) -> bool:
        """Share media to Twitter"""
        try:
            connection = self.get_service_connection(user_id, 'twitter')
            if not connection:
                return False
            
            # Get media info
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT title, year, poster_url FROM media_files WHERE id = ?', (media_id,))
            media = cursor.fetchone()
            conn.close()
            
            if not media:
                return False
            
            title, year, poster_url = media
            
            # Create tweet text
            if not message:
                message = f"Just watched {title} ({year}) on my Watch Media Server! 🎬"
            
            # Post to Twitter
            headers = {
                'Authorization': f"Bearer {connection['access_token']}",
                'Content-Type': 'application/json'
            }
            
            tweet_data = {
                'text': message
            }
            
            response = requests.post(
                f"{self.service_configs['twitter']['base_url']}/tweets",
                headers=headers,
                json=tweet_data
            )
            response.raise_for_status()
            
            self._log_integration_event('twitter', 'share_success', {
                'user_id': user_id,
                'media_id': media_id,
                'tweet_id': response.json().get('data', {}).get('id')
            }, 'success')
            
            return True
        except Exception as e:
            logger.error(f"Error sharing to Twitter: {e}")
            self._log_integration_event('twitter', 'share_error', {
                'user_id': user_id,
                'media_id': media_id,
                'error': str(e)
            }, 'error', str(e))
            return False
    
    def send_telegram_notification(self, user_id: int, message: str, media_id: int = None) -> bool:
        """Send notification via Telegram"""
        try:
            bot_token = self.service_configs['telegram']['bot_token']
            if not bot_token:
                return False
            
            # Get user's Telegram chat ID (would be stored in user preferences)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT preferences FROM users WHERE id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False
            
            preferences = json.loads(result[0]) if result[0] else {}
            chat_id = preferences.get('telegram_chat_id')
            
            if not chat_id:
                return False
            
            # Send message
            url = f"{self.service_configs['telegram']['base_url']}{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            if media_id:
                # Get media info for rich message
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT title, year, poster_url FROM media_files WHERE id = ?', (media_id,))
                media = cursor.fetchone()
                conn.close()
                
                if media:
                    title, year, poster_url = media
                    data['text'] = f"🎬 <b>{title} ({year})</b>\n\n{message}"
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            self._log_integration_event('telegram', 'notification_sent', {
                'user_id': user_id,
                'media_id': media_id,
                'message_length': len(message)
            }, 'success')
            
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            self._log_integration_event('telegram', 'notification_error', {
                'user_id': user_id,
                'error': str(e)
            }, 'error', str(e))
            return False
    
    def create_webhook_subscription(self, user_id: int, webhook_url: str, event_types: List[str], secret_key: str = None) -> int:
        """Create webhook subscription"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO webhook_subscriptions 
                (user_id, webhook_url, event_types, secret_key)
                VALUES (?, ?, ?, ?)
            ''', (user_id, webhook_url, json.dumps(event_types), secret_key))
            
            webhook_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return webhook_id
        except Exception as e:
            logger.error(f"Error creating webhook subscription: {e}")
            return None
    
    def trigger_webhook(self, user_id: int, event_type: str, event_data: Dict):
        """Trigger webhook for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM webhook_subscriptions 
                WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            
            webhooks = cursor.fetchall()
            conn.close()
            
            for webhook in webhooks:
                webhook_id, user_id, webhook_url, event_types, secret_key, is_active, last_triggered, created_at = webhook
                
                # Check if event type is subscribed
                subscribed_events = json.loads(event_types)
                if event_type not in subscribed_events:
                    continue
                
                # Prepare webhook payload
                payload = {
                    'event_type': event_type,
                    'event_data': event_data,
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id
                }
                
                headers = {'Content-Type': 'application/json'}
                if secret_key:
                    headers['X-Webhook-Secret'] = secret_key
                
                # Send webhook
                response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
                
                # Update last triggered time
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE webhook_subscriptions 
                    SET last_triggered = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (webhook_id,))
                conn.commit()
                conn.close()
                
                # Log webhook trigger
                status = 'success' if response.status_code == 200 else 'error'
                self._log_integration_event('webhook', f'trigger_{status}', {
                    'webhook_id': webhook_id,
                    'event_type': event_type,
                    'status_code': response.status_code
                }, status)
        
        except Exception as e:
            logger.error(f"Error triggering webhook: {e}")
            self._log_integration_event('webhook', 'trigger_error', {
                'user_id': user_id,
                'event_type': event_type,
                'error': str(e)
            }, 'error', str(e))
    
    def _log_integration_event(self, service_name: str, event_type: str, event_data: Dict, status: str, error_message: str = None):
        """Log integration event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO integration_logs 
                (service_name, event_type, event_data, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (service_name, event_type, json.dumps(event_data), status, error_message))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging integration event: {e}")
    
    def get_integration_logs(self, service_name: str = None, limit: int = 100) -> List[Dict]:
        """Get integration logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM integration_logs'
            params = []
            
            if service_name:
                query += ' WHERE service_name = ?'
                params.append(service_name)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                log = dict(row)
                try:
                    log['event_data'] = json.loads(log['event_data'])
                except:
                    log['event_data'] = {}
                results.append(log)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting integration logs: {e}")
            return []

# External services instance - will be initialized in app.py
external_services_service = None
