# Unit tests for cache_utils module
import pytest
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache_utils import SimpleCache, CacheEntry, get_cache, cached, invalidate_cache_pattern


class TestCacheEntry:
    """Tests for CacheEntry class"""

    def test_create_entry(self):
        entry = CacheEntry("test_data", ttl_seconds=10)
        assert entry.data == "test_data"
        assert entry.ttl_seconds == 10
        assert not entry.is_expired()

    def test_not_expired(self):
        entry = CacheEntry("data", ttl_seconds=10)
        assert not entry.is_expired()

    def test_expired(self):
        entry = CacheEntry("data", ttl_seconds=0)
        time.sleep(0.01)  # Small delay to ensure expiration
        assert entry.is_expired()

    def test_get_age(self):
        entry = CacheEntry("data", ttl_seconds=10)
        time.sleep(0.1)
        age = entry.get_age()
        assert age >= 0.1
        assert age < 1.0


class TestSimpleCache:
    """Tests for SimpleCache class"""

    def setup_method(self):
        """Create a fresh cache for each test"""
        self.cache = SimpleCache()

    def test_set_and_get(self):
        self.cache.set("key1", "value1", ttl_seconds=10)
        assert self.cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        assert self.cache.get("nonexistent") is None

    def test_cache_expiration(self):
        self.cache.set("key1", "value1", ttl_seconds=0)
        time.sleep(0.01)
        assert self.cache.get("key1") is None

    def test_invalidate_key(self):
        self.cache.set("key1", "value1")
        self.cache.invalidate("key1")
        assert self.cache.get("key1") is None

    def test_invalidate_nonexistent_key(self):
        # Should not raise error
        self.cache.invalidate("nonexistent")

    def test_clear_cache(self):
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None

    def test_cleanup_expired(self):
        self.cache.set("key1", "value1", ttl_seconds=10)
        self.cache.set("key2", "value2", ttl_seconds=0)
        time.sleep(0.01)
        self.cache.cleanup_expired()
        assert self.cache.get("key1") == "value1"
        assert self.cache.get("key2") is None

    def test_cache_stats_empty(self):
        stats = self.cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['total_requests'] == 0
        assert stats['hit_rate'] == 0
        assert stats['cached_items'] == 0

    def test_cache_stats_hit(self):
        self.cache.set("key1", "value1")
        self.cache.get("key1")
        stats = self.cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 100.0

    def test_cache_stats_miss(self):
        self.cache.get("nonexistent")
        stats = self.cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.0

    def test_cache_stats_mixed(self):
        self.cache.set("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("nonexistent")  # Miss
        self.cache.get("key1")  # Hit
        stats = self.cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == pytest.approx(66.67, rel=0.1)


class TestGetCache:
    """Tests for global cache instance"""

    def test_get_cache_returns_same_instance(self):
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_get_cache_is_simple_cache(self):
        cache = get_cache()
        assert isinstance(cache, SimpleCache)


class TestCachedDecorator:
    """Tests for @cached decorator"""

    def setup_method(self):
        """Clear cache before each test"""
        get_cache().clear()
        self.call_count = 0

    def test_caches_function_result(self):
        @cached(ttl_seconds=10)
        def expensive_function(x):
            self.call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert self.call_count == 1  # Function only called once

    def test_different_args_different_cache(self):
        @cached(ttl_seconds=10)
        def function(x):
            self.call_count += 1
            return x * 2

        result1 = function(5)
        result2 = function(10)

        assert result1 == 10
        assert result2 == 20
        assert self.call_count == 2  # Function called twice for different args

    def test_respects_ttl(self):
        @cached(ttl_seconds=0)
        def function(x):
            self.call_count += 1
            return x * 2

        result1 = function(5)
        time.sleep(0.01)
        result2 = function(5)

        assert result1 == 10
        assert result2 == 10
        assert self.call_count == 2  # Called twice due to expiration

    def test_custom_key_prefix(self):
        @cached(ttl_seconds=10, key_prefix="custom_")
        def function(x):
            return x * 2

        result = function(5)
        assert result == 10

        # Check that cache key includes prefix
        cache = get_cache()
        found_custom_key = any("custom_" in key for key in cache._cache.keys())
        assert found_custom_key

    def test_with_kwargs(self):
        @cached(ttl_seconds=10)
        def function(x, y=10):
            self.call_count += 1
            return x + y

        result1 = function(5, y=10)
        result2 = function(5, y=10)
        result3 = function(5, y=20)

        assert result1 == 15
        assert result2 == 15
        assert result3 == 25
        assert self.call_count == 2  # Called once for each unique kwarg combo


class TestInvalidateCachePattern:
    """Tests for invalidate_cache_pattern function"""

    def setup_method(self):
        """Setup cache with test data"""
        cache = get_cache()
        cache.clear()
        cache.set("prefix_key1", "value1")
        cache.set("prefix_key2", "value2")
        cache.set("other_key", "value3")

    def test_invalidate_matching_pattern(self):
        invalidate_cache_pattern("prefix_")

        cache = get_cache()
        assert cache.get("prefix_key1") is None
        assert cache.get("prefix_key2") is None
        assert cache.get("other_key") == "value3"

    def test_invalidate_no_matches(self):
        invalidate_cache_pattern("nonexistent_")

        cache = get_cache()
        assert cache.get("prefix_key1") == "value1"
        assert cache.get("prefix_key2") == "value2"
        assert cache.get("other_key") == "value3"

    def test_invalidate_all_with_empty_pattern(self):
        invalidate_cache_pattern("")  # Empty string matches all

        cache = get_cache()
        assert cache.get("prefix_key1") is None
        assert cache.get("prefix_key2") is None
        assert cache.get("other_key") is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
