# Smart Home Integration Service for Watch Media Server
import os
import json
import requests
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Optional async imports
try:
    import asyncio
    import aiohttp
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

logger = logging.getLogger(__name__)

class SmartHomeService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.init_smart_home_tables()
        self.device_configs = self._get_device_configs()
    
    def init_smart_home_tables(self):
        """Initialize smart home database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Smart home devices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_home_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                device_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                device_data TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, device_id)
            )
        ''')
        
        # Automation rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                rule_name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_conditions TEXT NOT NULL,
                actions TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                last_triggered TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Voice commands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                command_text TEXT NOT NULL,
                command_type TEXT NOT NULL,
                parameters TEXT DEFAULT '{}',
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Smart home logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS smart_home_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT DEFAULT '{}',
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_device_configs(self) -> Dict:
        """Get smart home device configurations"""
        return {
            'alexa': {
                'base_url': 'https://api.amazonalexa.com',
                'client_id': os.getenv('ALEXA_CLIENT_ID'),
                'client_secret': os.getenv('ALEXA_CLIENT_SECRET'),
                'skill_id': os.getenv('ALEXA_SKILL_ID'),
                'supported_commands': [
                    'play_movie', 'pause_movie', 'resume_movie',
                    'search_movie', 'add_to_watchlist', 'get_recommendations'
                ]
            },
            'google_home': {
                'base_url': 'https://homegraph.googleapis.com',
                'api_key': os.getenv('GOOGLE_HOME_API_KEY'),
                'project_id': os.getenv('GOOGLE_HOME_PROJECT_ID'),
                'supported_commands': [
                    'play_media', 'pause_media', 'resume_media',
                    'search_media', 'add_to_list', 'get_suggestions'
                ]
            },
            'home_assistant': {
                'base_url': os.getenv('HOME_ASSISTANT_URL', 'http://localhost:8123'),
                'api_token': os.getenv('HOME_ASSISTANT_TOKEN'),
                'supported_entities': [
                    'media_player', 'light', 'switch', 'sensor',
                    'automation', 'script', 'scene'
                ]
            },
            'philips_hue': {
                'base_url': os.getenv('PHILIPS_HUE_BRIDGE_URL'),
                'username': os.getenv('PHILIPS_HUE_USERNAME'),
                'supported_lights': ['ambient', 'accent', 'task']
            },
            'sonos': {
                'base_url': os.getenv('SONOS_BASE_URL'),
                'api_key': os.getenv('SONOS_API_KEY'),
                'supported_actions': ['play', 'pause', 'volume', 'group']
            }
        }
    
    def register_device(self, user_id: int, device_name: str, device_type: str, 
                       device_id: str, platform: str, device_data: Dict = None) -> int:
        """Register a smart home device"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO smart_home_devices 
                (user_id, device_name, device_type, device_id, platform, device_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, device_name, device_type, device_id, platform, json.dumps(device_data or {})))
            
            device_db_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return device_db_id
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return None
    
    def get_user_devices(self, user_id: int, platform: str = None) -> List[Dict]:
        """Get user's smart home devices"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM smart_home_devices WHERE user_id = ? AND is_active = 1'
            params = [user_id]
            
            if platform:
                query += ' AND platform = ?'
                params.append(platform)
            
            query += ' ORDER BY device_name'
            
            cursor.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                device = dict(row)
                try:
                    device['device_data'] = json.loads(device['device_data'])
                except:
                    device['device_data'] = {}
                results.append(device)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting user devices: {e}")
            return []
    
    def create_automation_rule(self, user_id: int, rule_name: str, trigger_type: str, 
                              trigger_conditions: Dict, actions: List[Dict]) -> int:
        """Create automation rule"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO automation_rules 
                (user_id, rule_name, trigger_type, trigger_conditions, actions)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, rule_name, trigger_type, json.dumps(trigger_conditions), json.dumps(actions)))
            
            rule_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return rule_id
        except Exception as e:
            logger.error(f"Error creating automation rule: {e}")
            return None
    
    def handle_voice_command(self, user_id: int, command_text: str, platform: str = 'alexa') -> Dict:
        """Handle voice command from smart home device"""
        try:
            # Parse command
            command_data = self._parse_voice_command(command_text, platform)
            
            if not command_data:
                return {
                    'success': False,
                    'response': 'Sorry, I didn\'t understand that command.',
                    'command_type': 'unknown'
                }
            
            # Execute command
            result = self._execute_voice_command(user_id, command_data)
            
            # Log command
            self._log_voice_command(user_id, command_text, command_data['type'], 
                                  command_data.get('parameters', {}), result.get('response', ''))
            
            return result
        except Exception as e:
            logger.error(f"Error handling voice command: {e}")
            return {
                'success': False,
                'response': 'Sorry, there was an error processing your command.',
                'command_type': 'error'
            }
    
    def _parse_voice_command(self, command_text: str, platform: str) -> Optional[Dict]:
        """Parse voice command text into structured data"""
        command_text = command_text.lower().strip()
        
        # Play media commands
        if any(word in command_text for word in ['play', 'start', 'watch']):
            if 'movie' in command_text or 'film' in command_text:
                # Extract movie title
                title = self._extract_title_from_command(command_text, ['play', 'start', 'watch', 'movie', 'film'])
                return {
                    'type': 'play_movie',
                    'parameters': {'title': title},
                    'platform': platform
                }
            elif 'tv show' in command_text or 'series' in command_text:
                title = self._extract_title_from_command(command_text, ['play', 'start', 'watch', 'tv', 'show', 'series'])
                return {
                    'type': 'play_tv_show',
                    'parameters': {'title': title},
                    'platform': platform
                }
        
        # Control commands
        elif any(word in command_text for word in ['pause', 'stop']):
            return {
                'type': 'pause_media',
                'parameters': {},
                'platform': platform
            }
        elif any(word in command_text for word in ['resume', 'continue']):
            return {
                'type': 'resume_media',
                'parameters': {},
                'platform': platform
            }
        
        # Search commands
        elif 'search' in command_text:
            query = self._extract_title_from_command(command_text, ['search', 'for'])
            return {
                'type': 'search_media',
                'parameters': {'query': query},
                'platform': platform
            }
        
        # Watchlist commands
        elif 'add to watchlist' in command_text or 'save' in command_text:
            title = self._extract_title_from_command(command_text, ['add', 'to', 'watchlist', 'save'])
            return {
                'type': 'add_to_watchlist',
                'parameters': {'title': title},
                'platform': platform
            }
        
        # Recommendation commands
        elif any(word in command_text for word in ['recommend', 'suggest', 'what should i watch']):
            return {
                'type': 'get_recommendations',
                'parameters': {},
                'platform': platform
            }
        
        # Volume commands
        elif 'volume' in command_text:
            if 'up' in command_text or 'increase' in command_text:
                return {
                    'type': 'volume_up',
                    'parameters': {},
                    'platform': platform
                }
            elif 'down' in command_text or 'decrease' in command_text:
                return {
                    'type': 'volume_down',
                    'parameters': {},
                    'platform': platform
                }
        
        return None
    
    def _extract_title_from_command(self, command_text: str, exclude_words: List[str]) -> str:
        """Extract media title from voice command"""
        words = command_text.split()
        title_words = []
        
        for word in words:
            if word not in exclude_words:
                title_words.append(word)
        
        return ' '.join(title_words).strip()
    
    def _execute_voice_command(self, user_id: int, command_data: Dict) -> Dict:
        """Execute parsed voice command"""
        command_type = command_data['type']
        parameters = command_data.get('parameters', {})
        
        try:
            if command_type == 'play_movie':
                return self._handle_play_movie_command(user_id, parameters)
            elif command_type == 'play_tv_show':
                return self._handle_play_tv_show_command(user_id, parameters)
            elif command_type == 'pause_media':
                return self._handle_pause_media_command(user_id)
            elif command_type == 'resume_media':
                return self._handle_resume_media_command(user_id)
            elif command_type == 'search_media':
                return self._handle_search_media_command(user_id, parameters)
            elif command_type == 'add_to_watchlist':
                return self._handle_add_to_watchlist_command(user_id, parameters)
            elif command_type == 'get_recommendations':
                return self._handle_get_recommendations_command(user_id)
            elif command_type == 'volume_up':
                return self._handle_volume_up_command(user_id)
            elif command_type == 'volume_down':
                return self._handle_volume_down_command(user_id)
            else:
                return {
                    'success': False,
                    'response': 'Command not implemented yet.',
                    'command_type': command_type
                }
        except Exception as e:
            logger.error(f"Error executing voice command: {e}")
            return {
                'success': False,
                'response': 'Sorry, there was an error executing your command.',
                'command_type': command_type
            }
    
    def _handle_play_movie_command(self, user_id: int, parameters: Dict) -> Dict:
        """Handle play movie voice command"""
        title = parameters.get('title', '')
        
        if not title:
            return {
                'success': False,
                'response': 'What movie would you like to watch?',
                'command_type': 'play_movie'
            }
        
        # Search for movie in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, year FROM media_files 
            WHERE media_type = 'movie' AND title LIKE ? 
            ORDER BY year DESC LIMIT 1
        ''', (f'%{title}%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            media_id, movie_title, year = result
            return {
                'success': True,
                'response': f'Playing {movie_title} ({year})',
                'command_type': 'play_movie',
                'media_id': media_id,
                'action': 'play'
            }
        else:
            return {
                'success': False,
                'response': f'Sorry, I couldn\'t find "{title}" in your library.',
                'command_type': 'play_movie'
            }
    
    def _handle_play_tv_show_command(self, user_id: int, parameters: Dict) -> Dict:
        """Handle play TV show voice command"""
        title = parameters.get('title', '')
        
        if not title:
            return {
                'success': False,
                'response': 'What TV show would you like to watch?',
                'command_type': 'play_tv_show'
            }
        
        # Search for TV show in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, year FROM media_files 
            WHERE media_type = 'tv_show' AND title LIKE ? 
            ORDER BY year DESC LIMIT 1
        ''', (f'%{title}%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            media_id, show_title, year = result
            return {
                'success': True,
                'response': f'Playing {show_title} ({year})',
                'command_type': 'play_tv_show',
                'media_id': media_id,
                'action': 'play'
            }
        else:
            return {
                'success': False,
                'response': f'Sorry, I couldn\'t find "{title}" in your library.',
                'command_type': 'play_tv_show'
            }
    
    def _handle_pause_media_command(self, user_id: int) -> Dict:
        """Handle pause media voice command"""
        return {
            'success': True,
            'response': 'Pausing playback',
            'command_type': 'pause_media',
            'action': 'pause'
        }
    
    def _handle_resume_media_command(self, user_id: int) -> Dict:
        """Handle resume media voice command"""
        return {
            'success': True,
            'response': 'Resuming playback',
            'command_type': 'resume_media',
            'action': 'resume'
        }
    
    def _handle_search_media_command(self, user_id: int, parameters: Dict) -> Dict:
        """Handle search media voice command"""
        query = parameters.get('query', '')
        
        if not query:
            return {
                'success': False,
                'response': 'What would you like to search for?',
                'command_type': 'search_media'
            }
        
        # Search in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, year, media_type FROM media_files 
            WHERE title LIKE ? 
            ORDER BY year DESC LIMIT 5
        ''', (f'%{query}%',))
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            titles = [f"{title} ({year})" for _, title, year, _ in results]
            response = f"I found {len(results)} results: {', '.join(titles[:3])}"
            if len(results) > 3:
                response += f" and {len(results) - 3} more"
            
            return {
                'success': True,
                'response': response,
                'command_type': 'search_media',
                'results': results
            }
        else:
            return {
                'success': False,
                'response': f'Sorry, I couldn\'t find anything matching "{query}"',
                'command_type': 'search_media'
            }
    
    def _handle_add_to_watchlist_command(self, user_id: int, parameters: Dict) -> Dict:
        """Handle add to watchlist voice command"""
        title = parameters.get('title', '')
        
        if not title:
            return {
                'success': False,
                'response': 'What would you like to add to your watchlist?',
                'command_type': 'add_to_watchlist'
            }
        
        # Find media and add to watchlist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title FROM media_files 
            WHERE title LIKE ? 
            ORDER BY year DESC LIMIT 1
        ''', (f'%{title}%',))
        
        result = cursor.fetchone()
        
        if result:
            media_id, media_title = result
            
            # Add to watchlist
            cursor.execute('''
                INSERT OR IGNORE INTO user_watchlists (user_id, media_id)
                VALUES (?, ?)
            ''', (user_id, media_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'response': f'Added {media_title} to your watchlist',
                'command_type': 'add_to_watchlist',
                'media_id': media_id
            }
        else:
            conn.close()
            return {
                'success': False,
                'response': f'Sorry, I couldn\'t find "{title}" in your library',
                'command_type': 'add_to_watchlist'
            }
    
    def _handle_get_recommendations_command(self, user_id: int) -> Dict:
        """Handle get recommendations voice command"""
        # Get recent recommendations (simplified)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, year FROM media_files 
            ORDER BY rating DESC, created_at DESC 
            LIMIT 3
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            titles = [f"{title} ({year})" for _, title, year in results]
            response = f"Here are some recommendations: {', '.join(titles)}"
            
            return {
                'success': True,
                'response': response,
                'command_type': 'get_recommendations',
                'recommendations': results
            }
        else:
            return {
                'success': False,
                'response': 'Sorry, I don\'t have any recommendations right now',
                'command_type': 'get_recommendations'
            }
    
    def _handle_volume_up_command(self, user_id: int) -> Dict:
        """Handle volume up voice command"""
        return {
            'success': True,
            'response': 'Turning volume up',
            'command_type': 'volume_up',
            'action': 'volume_up'
        }
    
    def _handle_volume_down_command(self, user_id: int) -> Dict:
        """Handle volume down voice command"""
        return {
            'success': True,
            'response': 'Turning volume down',
            'command_type': 'volume_down',
            'action': 'volume_down'
        }
    
    def _log_voice_command(self, user_id: int, command_text: str, command_type: str, 
                          parameters: Dict, response: str):
        """Log voice command"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO voice_commands 
                (user_id, command_text, command_type, parameters, response)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, command_text, command_type, json.dumps(parameters), response))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging voice command: {e}")
    
    def control_home_assistant_entity(self, user_id: int, entity_id: str, action: str, 
                                    parameters: Dict = None) -> bool:
        """Control Home Assistant entity"""
        try:
            config = self.device_configs['home_assistant']
            api_token = config['api_token']
            base_url = config['base_url']
            
            if not api_token or not base_url:
                return False
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            # Prepare service call
            service_data = {
                'entity_id': entity_id
            }
            
            if parameters:
                service_data.update(parameters)
            
            # Determine service based on action
            if action == 'turn_on':
                service = 'homeassistant.turn_on'
            elif action == 'turn_off':
                service = 'homeassistant.turn_off'
            elif action == 'toggle':
                service = 'homeassistant.toggle'
            else:
                service = f'homeassistant.{action}'
            
            # Call Home Assistant service
            response = requests.post(
                f'{base_url}/api/services/{service.replace(".", "/")}',
                headers=headers,
                json=service_data
            )
            
            response.raise_for_status()
            
            # Log action
            self._log_smart_home_event(entity_id, 'control', {
                'action': action,
                'parameters': parameters,
                'user_id': user_id
            }, 'success')
            
            return True
        except Exception as e:
            logger.error(f"Error controlling Home Assistant entity: {e}")
            self._log_smart_home_event(entity_id, 'control_error', {
                'action': action,
                'error': str(e),
                'user_id': user_id
            }, 'error')
            return False
    
    def set_philips_hue_scene(self, user_id: int, scene_name: str) -> bool:
        """Set Philips Hue scene"""
        try:
            config = self.device_configs['philips_hue']
            base_url = config['base_url']
            username = config['username']
            
            if not base_url or not username:
                return False
            
            # Get scenes
            response = requests.get(f'{base_url}/api/{username}/scenes')
            response.raise_for_status()
            
            scenes = response.json()
            
            # Find scene by name
            scene_id = None
            for scene_id_key, scene_data in scenes.items():
                if scene_data.get('name', '').lower() == scene_name.lower():
                    scene_id = scene_id_key
                    break
            
            if not scene_id:
                return False
            
            # Activate scene
            response = requests.put(
                f'{base_url}/api/{username}/groups/0/action',
                json={'scene': scene_id}
            )
            response.raise_for_status()
            
            # Log action
            self._log_smart_home_event('philips_hue', 'set_scene', {
                'scene_name': scene_name,
                'scene_id': scene_id,
                'user_id': user_id
            }, 'success')
            
            return True
        except Exception as e:
            logger.error(f"Error setting Philips Hue scene: {e}")
            self._log_smart_home_event('philips_hue', 'set_scene_error', {
                'scene_name': scene_name,
                'error': str(e),
                'user_id': user_id
            }, 'error')
            return False
    
    def _log_smart_home_event(self, device_id: str, event_type: str, event_data: Dict, status: str):
        """Log smart home event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO smart_home_logs 
                (device_id, event_type, event_data, status)
                VALUES (?, ?, ?, ?)
            ''', (device_id, event_type, json.dumps(event_data), status))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging smart home event: {e}")
    
    def get_voice_command_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get voice command history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM voice_commands 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                command = dict(row)
                try:
                    command['parameters'] = json.loads(command['parameters'])
                except:
                    command['parameters'] = {}
                results.append(command)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting voice command history: {e}")
            return []

# Smart home service instance
# Smart home service instance - will be initialized in app.py
smart_home_service = None
