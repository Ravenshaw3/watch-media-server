# Caching Service for Watch Media Server
import os
import json
import time
import hashlib
from typing import Any, Optional, Dict, List
from functools import wraps
from flask import current_app, request
import logging

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL')
        self.redis_client = None
        self.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true' and REDIS_AVAILABLE
        self.default_ttl = int(os.getenv('CACHE_DEFAULT_TTL', '3600'))  # 1 hour
        
        # Don't try to connect if cache is disabled or no Redis URL is provided
        if self.cache_enabled and self.redis_url and not self.redis_url.startswith('#'):
            self.connect()
        else:
            logger.info("Caching disabled - Redis URL not configured or cache disabled")
    
    def connect(self):
        """Connect to Redis server"""
        if not self.cache_enabled or not REDIS_AVAILABLE:
            logger.info("Caching disabled - Redis not available")
            return
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.cache_enabled = False
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ':'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        if not self.is_connected():
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_connected():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
        
        return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def get_or_set(self, key: str, func, ttl: int = None, *args, **kwargs):
        """Get from cache or set using function"""
        value = self.get(key)
        if value is not None:
            return value
        
        value = func(*args, **kwargs)
        if value is not None:
            self.set(key, value, ttl)
        
        return value
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache"""
        if not self.is_connected():
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache expire error: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.is_connected():
            return {'connected': False}
        
        try:
            info = self.redis_client.info()
            return {
                'connected': True,
                'used_memory': info.get('used_memory_human', '0B'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {'connected': False, 'error': str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    def clear_all(self) -> bool:
        """Clear all cache data"""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

# Cache decorators
def cached(ttl: int = 3600, key_prefix: str = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_service = CacheService()
            
            # Generate cache key
            if key_prefix:
                cache_key = cache_service._generate_key(key_prefix, *args, **kwargs)
            else:
                cache_key = cache_service._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_service.set(cache_key, result, ttl)
                logger.debug(f"Cached result for {cache_key}")
            
            return result
        
        return wrapper
    return decorator

def cache_invalidate(pattern: str = None):
    """Decorator to invalidate cache after function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            cache_service = CacheService()
            if pattern:
                cache_service.delete_pattern(pattern)
            else:
                # Invalidate by function name
                cache_key = cache_service._generate_key(func.__name__, *args, **kwargs)
                cache_service.delete(cache_key)
            
            return result
        
        return wrapper
    return decorator

# Specific cache keys for media server
class CacheKeys:
    MEDIA_LIST = "media:list"
    MEDIA_DETAILS = "media:details"
    SEARCH_RESULTS = "search:results"
    TMDB_METADATA = "tmdb:metadata"
    USER_WATCHLIST = "user:watchlist"
    USER_HISTORY = "user:history"
    RECOMMENDATIONS = "user:recommendations"
    TRANSCODE_STATUS = "transcode:status"
    LIBRARY_STATS = "library:stats"
    API_RESPONSE = "api:response"

# Cache service instance
cache_service = CacheService()
