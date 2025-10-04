# Caching utilities for the Server Monitoring Dashboard
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)


class CacheEntry:
    """Represents a single cache entry with TTL"""

    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        age = datetime.now() - self.created_at
        return age.total_seconds() > self.ttl_seconds

    def get_age(self) -> float:
        """Get age of cache entry in seconds"""
        return (datetime.now() - self.created_at).total_seconds()


class SimpleCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self):
        self._cache = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if it exists and hasn't expired"""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self._hits += 1
                logging.debug(f"Cache hit for key: {key} (age: {entry.get_age():.1f}s)")
                return entry.data
            else:
                # Remove expired entry
                logging.debug(f"Cache expired for key: {key}")
                del self._cache[key]

        self._misses += 1
        logging.debug(f"Cache miss for key: {key}")
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 900):
        """Set value in cache with TTL (default 15 minutes)"""
        self._cache[key] = CacheEntry(value, ttl_seconds)
        logging.debug(f"Cache set for key: {key} (TTL: {ttl_seconds}s)")

    def invalidate(self, key: str):
        """Remove specific key from cache"""
        if key in self._cache:
            del self._cache[key]
            logging.info(f"Cache invalidated for key: {key}")

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logging.info("Cache cleared completely")

    def cleanup_expired(self):
        """Remove all expired entries"""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logging.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self._hits,
            'misses': self._misses,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'cached_items': len(self._cache)
        }


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance"""
    return _cache


def cached(ttl_seconds: int = 900, key_prefix: str = ""):
    """
    Decorator to cache function results

    Args:
        ttl_seconds: Time to live in seconds (default 15 minutes)
        key_prefix: Optional prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}"
            if args:
                cache_key += f"_{hash(str(args))}"
            if kwargs:
                cache_key += f"_{hash(str(sorted(kwargs.items())))}"

            # Try to get from cache
            cache = get_cache()
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate all cache keys matching a pattern"""
    cache = get_cache()
    matching_keys = [k for k in cache._cache.keys() if pattern in k]
    for key in matching_keys:
        cache.invalidate(key)
    logging.info(f"Invalidated {len(matching_keys)} cache entries matching pattern: {pattern}")
