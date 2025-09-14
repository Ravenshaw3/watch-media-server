# Database Optimization Service for Watch Media Server
import os
import sqlite3
import logging
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.connection_pool = []
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.pool_lock = threading.Lock()
        self.optimization_enabled = os.getenv('DB_OPTIMIZATION_ENABLED', 'true').lower() == 'true'
        
        # Initialize connection pool
        self._initialize_pool()
        
        # Create indexes if optimization is enabled
        if self.optimization_enabled:
            self._create_indexes()
            self._optimize_database()
    
    def _initialize_pool(self):
        """Initialize database connection pool"""
        try:
            for _ in range(self.pool_size):
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                # Enable WAL mode for better concurrency
                conn.execute('PRAGMA journal_mode=WAL')
                # Enable foreign keys
                conn.execute('PRAGMA foreign_keys=ON')
                # Set busy timeout
                conn.execute('PRAGMA busy_timeout=30000')
                # Optimize for performance
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=10000')
                conn.execute('PRAGMA temp_store=MEMORY')
                
                self.connection_pool.append(conn)
            
            logger.info(f"Database connection pool initialized with {self.pool_size} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        conn = None
        try:
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                else:
                    # Create new connection if pool is empty
                    conn = sqlite3.connect(
                        self.db_path,
                        check_same_thread=False,
                        timeout=30.0
                    )
                    conn.execute('PRAGMA journal_mode=WAL')
                    conn.execute('PRAGMA foreign_keys=ON')
                    conn.execute('PRAGMA busy_timeout=30000')
            
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.commit()
                    with self.pool_lock:
                        if len(self.connection_pool) < self.pool_size:
                            self.connection_pool.append(conn)
                        else:
                            conn.close()
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
                    conn.close()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        indexes = [
            # Media files indexes
            "CREATE INDEX IF NOT EXISTS idx_media_files_type ON media_files(media_type)",
            "CREATE INDEX IF NOT EXISTS idx_media_files_extension ON media_files(file_extension)",
            "CREATE INDEX IF NOT EXISTS idx_media_files_size ON media_files(file_size)",
            "CREATE INDEX IF NOT EXISTS idx_media_files_created ON media_files(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_media_files_rating ON media_files(rating)",
            "CREATE INDEX IF NOT EXISTS idx_media_files_genres ON media_files(genres)",
            "CREATE INDEX IF NOT EXISTS idx_media_files_tmdb_id ON media_files(tmdb_id)",
            
            # User-related indexes
            "CREATE INDEX IF NOT EXISTS idx_user_watchlists_user_id ON user_watchlists(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_watchlists_media_id ON user_watchlists(media_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_watchlists_added_at ON user_watchlists(added_at)",
            
            "CREATE INDEX IF NOT EXISTS idx_user_play_history_user_id ON user_play_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_play_history_media_id ON user_play_history(media_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_play_history_played_at ON user_play_history(played_at)",
            "CREATE INDEX IF NOT EXISTS idx_user_play_history_completed ON user_play_history(completed)",
            
            "CREATE INDEX IF NOT EXISTS idx_user_recommendations_user_id ON user_recommendations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_recommendations_score ON user_recommendations(score)",
            
            # Transcoding indexes
            "CREATE INDEX IF NOT EXISTS idx_transcoding_jobs_media_id ON transcoding_jobs(media_id)",
            "CREATE INDEX IF NOT EXISTS idx_transcoding_jobs_status ON transcoding_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_transcoding_jobs_created ON transcoding_jobs(created_at)",
            
            "CREATE INDEX IF NOT EXISTS idx_transcoding_cache_media_id ON transcoding_cache(media_id)",
            "CREATE INDEX IF NOT EXISTS idx_transcoding_cache_quality ON transcoding_cache(quality)",
            "CREATE INDEX IF NOT EXISTS idx_transcoding_cache_last_accessed ON transcoding_cache(last_accessed)",
            
            # Search indexes
            "CREATE INDEX IF NOT EXISTS idx_saved_searches_user_id ON saved_searches(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_saved_searches_created ON saved_searches(created_at)",
            
            # Subtitles indexes
            "CREATE INDEX IF NOT EXISTS idx_subtitles_media_id ON subtitles(media_id)",
            "CREATE INDEX IF NOT EXISTS idx_subtitles_language ON subtitles(language)",
        ]
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if tables exist before creating indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                for index_sql in indexes:
                    # Extract table name from index SQL
                    table_name = None
                    if 'media_files' in index_sql:
                        table_name = 'media_files'
                    elif 'user_watchlists' in index_sql:
                        table_name = 'user_watchlists'
                    elif 'user_play_history' in index_sql:
                        table_name = 'user_play_history'
                    elif 'user_recommendations' in index_sql:
                        table_name = 'user_recommendations'
                    elif 'transcoding_jobs' in index_sql:
                        table_name = 'transcoding_jobs'
                    elif 'transcoding_cache' in index_sql:
                        table_name = 'transcoding_cache'
                    elif 'saved_searches' in index_sql:
                        table_name = 'saved_searches'
                    elif 'subtitles' in index_sql:
                        table_name = 'subtitles'
                    
                    # Only create index if table exists
                    if table_name is None or table_name in existing_tables:
                        cursor.execute(index_sql)
                    else:
                        logger.debug(f"Skipping index creation for {table_name} - table does not exist yet")
                
                conn.commit()
                logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def _optimize_database(self):
        """Optimize database settings"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Analyze tables for query optimization
                cursor.execute('ANALYZE')
                
                # Set optimal page size
                cursor.execute('PRAGMA page_size=4096')
                
                # Enable query optimization
                cursor.execute('PRAGMA optimize')
                
                conn.commit()
                logger.info("Database optimization completed")
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get table sizes
                cursor.execute("""
                    SELECT name, 
                           (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as table_count
                    FROM sqlite_master m 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = cursor.fetchall()
                
                table_stats = {}
                for table_name, _ in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    table_stats[table_name] = count
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                # Get WAL file size
                wal_size = 0
                wal_path = f"{self.db_path}-wal"
                if os.path.exists(wal_path):
                    wal_size = os.path.getsize(wal_path)
                
                # Get connection pool info
                with self.pool_lock:
                    pool_size = len(self.connection_pool)
                
                return {
                    'database_size_mb': round(db_size / 1024 / 1024, 2),
                    'wal_size_mb': round(wal_size / 1024 / 1024, 2),
                    'total_size_mb': round((db_size + wal_size) / 1024 / 1024, 2),
                    'table_counts': table_stats,
                    'connection_pool_size': pool_size,
                    'optimization_enabled': self.optimization_enabled
                }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}
    
    def vacuum_database(self) -> bool:
        """Vacuum database to reclaim space"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('VACUUM')
                conn.commit()
                logger.info("Database vacuum completed")
                return True
        except Exception as e:
            logger.error(f"Error vacuuming database: {e}")
            return False
    
    def analyze_database(self) -> Dict:
        """Analyze database for optimization opportunities"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get query plan for common queries
                queries = [
                    "SELECT * FROM media_files WHERE media_type = 'movie' LIMIT 1",
                    "SELECT * FROM user_watchlists WHERE user_id = 1 LIMIT 1",
                    "SELECT * FROM user_play_history WHERE user_id = 1 ORDER BY played_at DESC LIMIT 1"
                ]
                
                query_plans = {}
                for i, query in enumerate(queries):
                    try:
                        cursor.execute(f"EXPLAIN QUERY PLAN {query}")
                        plan = cursor.fetchall()
                        query_plans[f"query_{i+1}"] = {
                            'sql': query,
                            'plan': plan
                        }
                    except Exception as e:
                        query_plans[f"query_{i+1}"] = {
                            'sql': query,
                            'error': str(e)
                        }
                
                # Get index usage statistics
                cursor.execute("""
                    SELECT name, sql 
                    FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                indexes = cursor.fetchall()
                
                return {
                    'query_plans': query_plans,
                    'indexes': [{'name': name, 'sql': sql} for name, sql in indexes],
                    'analysis_timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error analyzing database: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days: int = 30) -> Dict:
        """Clean up old data from database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleanup_stats = {}
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean up old transcoding jobs
                cursor.execute("""
                    DELETE FROM transcoding_jobs 
                    WHERE created_at < ? AND status IN ('completed', 'failed')
                """, (cutoff_date.isoformat(),))
                cleanup_stats['transcoding_jobs'] = cursor.rowcount
                
                # Clean up old play history (keep last 1000 per user)
                cursor.execute("""
                    DELETE FROM user_play_history 
                    WHERE id NOT IN (
                        SELECT id FROM user_play_history 
                        WHERE user_id = user_play_history.user_id 
                        ORDER BY played_at DESC 
                        LIMIT 1000
                    )
                """)
                cleanup_stats['play_history'] = cursor.rowcount
                
                # Clean up old transcoding cache (unused for 7 days)
                cache_cutoff = datetime.now() - timedelta(days=7)
                cursor.execute("""
                    DELETE FROM transcoding_cache 
                    WHERE last_accessed < ?
                """, (cache_cutoff.isoformat(),))
                cleanup_stats['transcoding_cache'] = cursor.rowcount
                
                conn.commit()
                logger.info(f"Database cleanup completed: {cleanup_stats}")
                return cleanup_stats
        except Exception as e:
            logger.error(f"Error cleaning up database: {e}")
            return {'error': str(e)}
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create database backup"""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            with self.get_connection() as conn:
                # Use backup API for efficient backup
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            raise
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Close all connections
            with self.pool_lock:
                for conn in self.connection_pool:
                    conn.close()
                self.connection_pool.clear()
            
            # Copy backup to main database
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            # Reinitialize connection pool
            self._initialize_pool()
            
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    # Parse JSON fields
                    for key, value in result.items():
                        if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                            try:
                                result[key] = json.loads(value)
                            except:
                                pass
                    results.append(result)
                
                return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_batch(self, queries: List[tuple]) -> bool:
        """Execute batch of queries in transaction"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for query, params in queries:
                    cursor.execute(query, params)
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error executing batch queries: {e}")
            return False
    
    def close_all_connections(self):
        """Close all database connections"""
        with self.pool_lock:
            for conn in self.connection_pool:
                conn.close()
            self.connection_pool.clear()
        logger.info("All database connections closed")

# Database service instance
database_service = DatabaseService()
