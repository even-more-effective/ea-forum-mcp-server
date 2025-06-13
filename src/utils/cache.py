from cachetools import TTLCache
from typing import Any, Optional, Dict
import threading
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class PostCache:
    """Thread-safe cache for EA Forum posts"""

    def __init__(self, ttl: int = 3600, maxsize: int = 100):
        """
        Initialize the cache

        Args:
            ttl: Time to live in seconds
            maxsize: Maximum number of items in cache
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()

    def _generate_key(self, key_parts: Dict[str, Any]) -> str:
        """Generate a cache key from dictionary of parameters"""
        # Sort keys for consistent hashing
        sorted_items = sorted(key_parts.items())
        key_string = json.dumps(sorted_items, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get an item from cache"""
        with self._lock:
            value = self._cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return value

    def set(self, key: str, value: Any) -> None:
        """Set an item in cache"""
        with self._lock:
            self._cache[key] = value
            logger.debug(f"Cached value for key: {key}")

    def get_search_key(
        self,
        query: str,
        date_range: Optional[str] = None,
        limit: int = 10,
        page: int = 0,
        **kwargs,
    ) -> str:
        """Generate cache key for search results"""
        key_parts = {
            "type": "search",
            "query": query,
            "date_range": date_range,
            "limit": limit,
            "page": page,
            **kwargs,
        }
        return self._generate_key(key_parts)

    def get_post_key(self, post_id: str) -> str:
        """Generate cache key for a single post"""
        return f"post:{post_id}"

    def clear(self) -> None:
        """Clear all items from cache"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)


# Global cache instance
_cache_instance = None
_cache_lock = threading.Lock()


def get_cache(ttl: int = 3600, maxsize: int = 100) -> PostCache:
    """Get or create the global cache instance"""
    global _cache_instance
    with _cache_lock:
        if _cache_instance is None:
            _cache_instance = PostCache(ttl=ttl, maxsize=maxsize)
        return _cache_instance