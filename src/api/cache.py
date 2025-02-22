import redis
from typing import Optional, Any
import json
import logging
from functools import wraps
import os

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = redis.from_StrictRedis.from_url(self.redis_url)
        self.default_timeout = 3600  # 1 hour default

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {str(e)}")
            return None

    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        """Set value in cache"""
        try:
            json_value = json.dumps(value)
            self.client.set(key, json_value, ex=timeout or self.default_timeout)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return False

    def clear(self) -> bool:
        """Clear all cache"""
        try:
            self.client.flushall()
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHALL error: {str(e)}")
            return False

# Cache decorator for API endpoints
def cache_response(timeout: int = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = RedisCache()
            
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # If not in cache, execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for key: {cache_key}")
            return result
            
        return wrapper
    return decorator

# Initialize Redis cache
cache = RedisCache()