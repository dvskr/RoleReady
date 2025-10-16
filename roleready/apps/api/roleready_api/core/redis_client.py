"""
Redis client for caching and session management
"""

import redis
import json
import logging
from typing import Optional, Dict, Any, List
from roleready_api.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        
        try:
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                logger.info("Redis connection established")
            else:
                logger.warning("Redis URL not configured, caching disabled")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, caching disabled")

    def is_enabled(self) -> bool:
        """Check if Redis is available"""
        return self.enabled and self.redis_client is not None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.is_enabled():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in Redis"""
        if not self.is_enabled():
            return False
        
        try:
            json_value = json.dumps(value)
            result = self.redis_client.set(key, json_value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.is_enabled():
            return False
        
        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_enabled():
            return False
        
        try:
            result = self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        if not self.is_enabled():
            return False
        
        try:
            result = self.redis_client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from Redis"""
        if not self.is_enabled():
            return {}
        
        try:
            values = self.redis_client.mget(keys)
            result = {}
            for i, key in enumerate(keys):
                if values[i]:
                    try:
                        result[key] = json.loads(values[i])
                    except json.JSONDecodeError:
                        result[key] = values[i]
            return result
        except Exception as e:
            logger.error(f"Redis mget error for keys {keys}: {e}")
            return {}

    async def set_multiple(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set multiple values in Redis"""
        if not self.is_enabled():
            return False
        
        try:
            json_mapping = {k: json.dumps(v) for k, v in mapping.items()}
            result = self.redis_client.mset(json_mapping)
            
            if expire:
                for key in mapping.keys():
                    self.redis_client.expire(key, expire)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Redis mset error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter in Redis"""
        if not self.is_enabled():
            return None
        
        try:
            result = self.redis_client.incrby(key, amount)
            return result
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None

    async def list_push(self, key: str, value: Any) -> bool:
        """Push value to list in Redis"""
        if not self.is_enabled():
            return False
        
        try:
            json_value = json.dumps(value)
            result = self.redis_client.lpush(key, json_value)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis list push error for key {key}: {e}")
            return False

    async def list_pop(self, key: str) -> Optional[Any]:
        """Pop value from list in Redis"""
        if not self.is_enabled():
            return None
        
        try:
            value = self.redis_client.rpop(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis list pop error for key {key}: {e}")
            return None

    async def list_length(self, key: str) -> int:
        """Get length of list in Redis"""
        if not self.is_enabled():
            return 0
        
        try:
            result = self.redis_client.llen(key)
            return result or 0
        except Exception as e:
            logger.error(f"Redis list length error for key {key}: {e}")
            return 0

# Cache key generators
def get_session_key(user_id: str) -> str:
    """Generate session cache key"""
    return f"session:{user_id}"

def get_resume_cache_key(resume_id: str) -> str:
    """Generate resume cache key"""
    return f"resume:{resume_id}"

def get_embeddings_cache_key(content_hash: str) -> str:
    """Generate embeddings cache key"""
    return f"embeddings:{content_hash}"

def get_translation_cache_key(text_hash: str, target_lang: str) -> str:
    """Generate translation cache key"""
    return f"translation:{text_hash}:{target_lang}"

def get_feedback_stats_key(user_id: str) -> str:
    """Generate feedback stats cache key"""
    return f"feedback_stats:{user_id}"

def get_analytics_cache_key(team_id: str, period: str) -> str:
    """Generate analytics cache key"""
    return f"analytics:{team_id}:{period}"

# Global instance
redis_client = RedisClient()
