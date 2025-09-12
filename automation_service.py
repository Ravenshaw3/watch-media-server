# Automation Service for Watch Media Server
import os
import json
import sqlite3
import schedule
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging
import subprocess
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.init_automation_tables()
        self.automation_tasks = {}
        self.scheduler_running = False
        self.start_scheduler()
    
    def init_automation_tables(self):
        """Initialize automation database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Automation tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                schedule_expression TEXT NOT NULL,
                task_config TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Automation logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                duration_ms INTEGER,
                output TEXT,
                error_message TEXT,
                FOREIGN KEY (task_id) REFERENCES automation_tasks (id)
            )
        ''')
        
        # File organization rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_organization_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                source_pattern TEXT NOT NULL,
                destination_pattern TEXT NOT NULL,
                file_types TEXT DEFAULT '[]',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Backup configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_name TEXT NOT NULL,
                backup_type TEXT NOT NULL,
                source_paths TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                schedule_expression TEXT NOT NULL,
                retention_days INTEGER DEFAULT 30,
                compression_enabled BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                last_backup TIMESTAMP,
                next_backup TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_scheduler(self):
        """Start the automation scheduler"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        def run_scheduler():
            while self.scheduler_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Automation scheduler started")
    
    def stop_scheduler(self):
        """Stop the automation scheduler"""
        self.scheduler_running = False
        schedule.clear()
        logger.info("Automation scheduler stopped")
    
    def create_automation_task(self, task_name: str, task_type: str, schedule_expression: str, 
                              task_config: Dict) -> int:
        """Create a new automation task"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate next run time
            next_run = self._calculate_next_run(schedule_expression)
            
            cursor.execute('''
                INSERT INTO automation_tasks 
                (task_name, task_type, schedule_expression, task_config, next_run)
                VALUES (?, ?, ?, ?, ?)
            ''', (task_name, task_type, schedule_expression, json.dumps(task_config), next_run))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Register task with scheduler
            self._register_scheduled_task(task_id, task_name, task_type, schedule_expression, task_config)
            
            return task_id
        except Exception as e:
            logger.error(f"Error creating automation task: {e}")
            return None
    
    def _calculate_next_run(self, schedule_expression: str) -> str:
        """Calculate next run time for schedule expression"""
        try:
            # Parse schedule expression (e.g., "daily at 02:00", "weekly on monday", "every 30 minutes")
            if "daily at" in schedule_expression:
                time_str = schedule_expression.split("daily at")[1].strip()
                hour, minute = map(int, time_str.split(":"))
                next_run = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= datetime.now():
                    next_run += timedelta(days=1)
            elif "weekly on" in schedule_expression:
                day = schedule_expression.split("weekly on")[1].strip().lower()
                days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
                       'friday': 4, 'saturday': 5, 'sunday': 6}
                if day in days:
                    days_ahead = days[day] - datetime.now().weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    next_run = datetime.now() + timedelta(days=days_ahead)
                    next_run = next_run.replace(hour=2, minute=0, second=0, microsecond=0)
            elif "every" in schedule_expression and "minutes" in schedule_expression:
                minutes = int(schedule_expression.split("every")[1].split("minutes")[0].strip())
                next_run = datetime.now() + timedelta(minutes=minutes)
            else:
                # Default to daily at 2 AM
                next_run = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
                if next_run <= datetime.now():
                    next_run += timedelta(days=1)
            
            return next_run.isoformat()
        except Exception as e:
            logger.error(f"Error calculating next run time: {e}")
            return (datetime.now() + timedelta(days=1)).isoformat()
    
    def _register_scheduled_task(self, task_id: int, task_name: str, task_type: str, 
                                schedule_expression: str, task_config: Dict):
        """Register task with Python schedule library"""
        try:
            # Create task function
            def task_wrapper():
                self._execute_automation_task(task_id, task_name, task_type, task_config)
            
            # Parse schedule and register
            if "daily at" in schedule_expression:
                time_str = schedule_expression.split("daily at")[1].strip()
                schedule.every().day.at(time_str).do(task_wrapper)
            elif "weekly on" in schedule_expression:
                day = schedule_expression.split("weekly on")[1].strip().lower()
                if day == 'monday':
                    schedule.every().monday.do(task_wrapper)
                elif day == 'tuesday':
                    schedule.every().tuesday.do(task_wrapper)
                elif day == 'wednesday':
                    schedule.every().wednesday.do(task_wrapper)
                elif day == 'thursday':
                    schedule.every().thursday.do(task_wrapper)
                elif day == 'friday':
                    schedule.every().friday.do(task_wrapper)
                elif day == 'saturday':
                    schedule.every().saturday.do(task_wrapper)
                elif day == 'sunday':
                    schedule.every().sunday.do(task_wrapper)
            elif "every" in schedule_expression and "minutes" in schedule_expression:
                minutes = int(schedule_expression.split("every")[1].split("minutes")[0].strip())
                schedule.every(minutes).minutes.do(task_wrapper)
            elif "every" in schedule_expression and "hours" in schedule_expression:
                hours = int(schedule_expression.split("every")[1].split("hours")[0].strip())
                schedule.every(hours).hours.do(task_wrapper)
            
            self.automation_tasks[task_id] = {
                'name': task_name,
                'type': task_type,
                'config': task_config,
                'function': task_wrapper
            }
            
            logger.info(f"Registered automation task: {task_name}")
        except Exception as e:
            logger.error(f"Error registering scheduled task: {e}")
    
    def _execute_automation_task(self, task_id: int, task_name: str, task_type: str, task_config: Dict):
        """Execute automation task"""
        start_time = time.time()
        status = 'success'
        output = ''
        error_message = ''
        
        try:
            logger.info(f"Executing automation task: {task_name}")
            
            if task_type == 'library_scan':
                output = self._execute_library_scan(task_config)
            elif task_type == 'database_cleanup':
                output = self._execute_database_cleanup(task_config)
            elif task_type == 'file_organization':
                output = self._execute_file_organization(task_config)
            elif task_type == 'backup':
                output = self._execute_backup(task_config)
            elif task_type == 'transcode_cleanup':
                output = self._execute_transcode_cleanup(task_config)
            elif task_type == 'metadata_update':
                output = self._execute_metadata_update(task_config)
            elif task_type == 'custom_script':
                output = self._execute_custom_script(task_config)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Update task statistics
            self._update_task_stats(task_id, True)
            
        except Exception as e:
            status = 'error'
            error_message = str(e)
            logger.error(f"Error executing automation task {task_name}: {e}")
            
            # Update task statistics
            self._update_task_stats(task_id, False)
        
        # Log execution
        duration_ms = int((time.time() - start_time) * 1000)
        self._log_task_execution(task_id, task_name, status, duration_ms, output, error_message)
    
    def _execute_library_scan(self, config: Dict) -> str:
        """Execute library scan automation"""
        try:
            # Import here to avoid circular imports
            from app import MediaManager
            
            manager = MediaManager()
            scan_path = config.get('scan_path', '/media')
            
            # Perform scan
            result = manager.scan_directory(scan_path)
            
            return f"Library scan completed. Found {len(result)} files."
        except Exception as e:
            raise Exception(f"Library scan failed: {e}")
    
    def _execute_database_cleanup(self, config: Dict) -> str:
        """Execute database cleanup automation"""
        try:
            from database_service import database_service
            
            days = config.get('retention_days', 30)
            cleanup_stats = database_service.cleanup_old_data(days)
            
            return f"Database cleanup completed: {cleanup_stats}"
        except Exception as e:
            raise Exception(f"Database cleanup failed: {e}")
    
    def _execute_file_organization(self, config: Dict) -> str:
        """Execute file organization automation"""
        try:
            source_pattern = config.get('source_pattern', '')
            destination_pattern = config.get('destination_pattern', '')
            file_types = config.get('file_types', [])
            
            if not source_pattern or not destination_pattern:
                raise ValueError("Source and destination patterns required")
            
            # Find files matching pattern
            source_path = Path(source_pattern)
            if not source_path.exists():
                raise ValueError(f"Source path does not exist: {source_pattern}")
            
            organized_count = 0
            
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    # Check file type
                    if file_types and file_path.suffix.lower() not in file_types:
                        continue
                    
                    # Generate destination path
                    dest_path = self._generate_destination_path(file_path, destination_pattern)
                    
                    # Create destination directory
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(str(file_path), str(dest_path))
                    organized_count += 1
            
            return f"File organization completed. Organized {organized_count} files."
        except Exception as e:
            raise Exception(f"File organization failed: {e}")
    
    def _generate_destination_path(self, source_path: Path, pattern: str) -> Path:
        """Generate destination path based on pattern"""
        # Simple pattern replacement (can be enhanced)
        # {year}, {month}, {day}, {filename}, {extension}
        now = datetime.now()
        
        replacements = {
            '{year}': str(now.year),
            '{month}': f"{now.month:02d}",
            '{day}': f"{now.day:02d}",
            '{filename}': source_path.stem,
            '{extension}': source_path.suffix
        }
        
        dest_pattern = pattern
        for placeholder, value in replacements.items():
            dest_pattern = dest_pattern.replace(placeholder, value)
        
        return Path(dest_pattern)
    
    def _execute_backup(self, config: Dict) -> str:
        """Execute backup automation"""
        try:
            from database_service import database_service
            
            backup_path = config.get('backup_path', './backups')
            compression = config.get('compression', True)
            
            # Create backup directory
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"watch_backup_{timestamp}.db"
            backup_file_path = backup_dir / backup_filename
            
            # Create database backup
            backup_path = database_service.backup_database(str(backup_file_path))
            
            # Compress if requested
            if compression:
                compressed_path = f"{backup_path}.gz"
                subprocess.run(['gzip', backup_path], check=True)
                backup_path = compressed_path
            
            return f"Backup completed: {backup_path}"
        except Exception as e:
            raise Exception(f"Backup failed: {e}")
    
    def _execute_transcode_cleanup(self, config: Dict) -> str:
        """Execute transcoding cleanup automation"""
        try:
            from transcoding_service import transcoding_service
            
            max_age_hours = config.get('max_age_hours', 24)
            transcoding_service.cleanup_old_transcodes(max_age_hours)
            
            return f"Transcoding cleanup completed (max age: {max_age_hours} hours)"
        except Exception as e:
            raise Exception(f"Transcoding cleanup failed: {e}")
    
    def _execute_metadata_update(self, config: Dict) -> str:
        """Execute metadata update automation"""
        try:
            from tmdb_service import tmdb_service
            
            # Get media files without metadata
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, year FROM media_files 
                WHERE tmdb_id IS NULL AND media_type = 'movie'
                LIMIT 10
            ''')
            
            media_files = cursor.fetchall()
            conn.close()
            
            updated_count = 0
            
            for media_id, title, year in media_files:
                try:
                    # Search for metadata
                    metadata = tmdb_service.search_media(title, 'movie', year)
                    if metadata:
                        # Update database
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE media_files 
                            SET tmdb_id = ?, poster_url = ?, backdrop_url = ?, 
                                overview = ?, genres = ?, rating = ?, runtime = ?, 
                                release_date = ?, imdb_id = ?
                            WHERE id = ?
                        ''', (
                            metadata.get('tmdb_id'),
                            metadata.get('poster_url'),
                            metadata.get('backdrop_url'),
                            metadata.get('overview'),
                            json.dumps(metadata.get('genres', [])),
                            metadata.get('rating'),
                            metadata.get('runtime'),
                            metadata.get('release_date'),
                            metadata.get('imdb_id'),
                            media_id
                        ))
                        conn.commit()
                        conn.close()
                        updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating metadata for media {media_id}: {e}")
            
            return f"Metadata update completed. Updated {updated_count} files."
        except Exception as e:
            raise Exception(f"Metadata update failed: {e}")
    
    def _execute_custom_script(self, config: Dict) -> str:
        """Execute custom script automation"""
        try:
            script_path = config.get('script_path', '')
            script_args = config.get('script_args', [])
            
            if not script_path:
                raise ValueError("Script path required")
            
            # Execute script
            result = subprocess.run(
                [script_path] + script_args,
                capture_output=True,
                text=True,
                timeout=config.get('timeout', 300)
            )
            
            if result.returncode != 0:
                raise Exception(f"Script failed with return code {result.returncode}: {result.stderr}")
            
            return f"Custom script executed successfully. Output: {result.stdout[:500]}"
        except Exception as e:
            raise Exception(f"Custom script execution failed: {e}")
    
    def _update_task_stats(self, task_id: int, success: bool):
        """Update task statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if success:
                cursor.execute('''
                    UPDATE automation_tasks 
                    SET run_count = run_count + 1, 
                        success_count = success_count + 1,
                        last_run = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (task_id,))
            else:
                cursor.execute('''
                    UPDATE automation_tasks 
                    SET run_count = run_count + 1, 
                        error_count = error_count + 1,
                        last_run = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (task_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating task stats: {e}")
    
    def _log_task_execution(self, task_id: int, task_name: str, status: str, 
                           duration_ms: int, output: str, error_message: str):
        """Log task execution"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO automation_logs 
                (task_id, task_name, execution_time, status, duration_ms, output, error_message)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            ''', (task_id, task_name, status, duration_ms, output, error_message))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging task execution: {e}")
    
    def get_automation_tasks(self) -> List[Dict]:
        """Get all automation tasks"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM automation_tasks 
                ORDER BY created_at DESC
            ''')
            
            results = []
            for row in cursor.fetchall():
                task = dict(row)
                try:
                    task['task_config'] = json.loads(task['task_config'])
                except:
                    task['task_config'] = {}
                results.append(task)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting automation tasks: {e}")
            return []
    
    def get_task_logs(self, task_id: int, limit: int = 50) -> List[Dict]:
        """Get logs for a specific task"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM automation_logs 
                WHERE task_id = ? 
                ORDER BY execution_time DESC 
                LIMIT ?
            ''', (task_id, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting task logs: {e}")
            return []
    
    def toggle_task(self, task_id: int, is_active: bool) -> bool:
        """Toggle task active status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE automation_tasks 
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (is_active, task_id))
            
            conn.commit()
            conn.close()
            
            # Update scheduler
            if is_active:
                # Re-register task
                task = self._get_task_by_id(task_id)
                if task:
                    self._register_scheduled_task(
                        task_id, task['task_name'], task['task_type'],
                        task['schedule_expression'], task['task_config']
                    )
            else:
                # Remove from scheduler
                if task_id in self.automation_tasks:
                    del self.automation_tasks[task_id]
            
            return True
        except Exception as e:
            logger.error(f"Error toggling task: {e}")
            return False
    
    def _get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Get task by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM automation_tasks WHERE id = ?', (task_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                task = dict(result)
                try:
                    task['task_config'] = json.loads(task['task_config'])
                except:
                    task['task_config'] = {}
                return task
            
            return None
        except Exception as e:
            logger.error(f"Error getting task by ID: {e}")
            return None
    
    def delete_task(self, task_id: int) -> bool:
        """Delete automation task"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete task logs first
            cursor.execute('DELETE FROM automation_logs WHERE task_id = ?', (task_id,))
            
            # Delete task
            cursor.execute('DELETE FROM automation_tasks WHERE id = ?', (task_id,))
            
            conn.commit()
            conn.close()
            
            # Remove from scheduler
            if task_id in self.automation_tasks:
                del self.automation_tasks[task_id]
            
            return True
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False

# Automation service instance
automation_service = AutomationService()
