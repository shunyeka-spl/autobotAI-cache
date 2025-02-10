import redis
from datetime import timedelta
from typing import Optional, Any
from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.exceptions import CacheMissError
from autobotAI_cache.core.models import CacheScope, UserContext
from autobotAI_cache.utils.helpers import get_context_scope_string


class RedisBackend(BaseBackend):
    def __init__(
        self,
        host="localhost",
        port=6379,
        db=0,
        max_entries: Optional[int] = None,
        **kwargs,
    ):
        """Initialize Redis client"""
        self.client = redis.Redis(host=host, port=port, db=db, **kwargs)
        self.max_entries = max_entries

    def get(self, key: str, collection_name: str) -> bytes:
        """Get a value from cache by key"""
        namespaced_key = self._get_namespaced_key(key, collection_name)
        value = self.client.get(namespaced_key)
        if value is None:
            raise CacheMissError(
                f"Key '{key}' not found in collection '{collection_name}'"
            )
        return value

    def set(self, key: str, value: Any, collection_name: str, ttl: int = None) -> None:
        """Set a value in cache with optional TTL"""
        namespaced_key = self._get_namespaced_key(key, collection_name)
        # Set with or without TTL based on the provided value
        if ttl:
            self.client.setex(namespaced_key, timedelta(seconds=ttl), value)
        else:
            self.client.set(namespaced_key, value)

        # Enforce max_entries limit if specified
        if self.max_entries is not None:
            self._enforce_max_entries(collection_name)

    def delete(self, key: str, collection_name: str) -> None:
        """Delete a value from cache by key"""
        namespaced_key = self._get_namespaced_key(key, collection_name)
        result = self.client.delete(namespaced_key)
        if result == 0:
            raise CacheMissError(
                f"Key '{key}' not found in collection '{collection_name}'"
            )

    def clear(
        self,
        collection_name: str = None,
        context: Optional[UserContext] = None,
        scope: CacheScope = CacheScope.ORGANIZATION.value,
    ) -> None:
        """Clear the cache for a specific collection and scope"""
        pattern = self._get_namespaced_pattern(collection_name, context, scope)
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
            print(f"Cache cleared for pattern: {pattern}")
        else:
            print(f"No matching keys found for pattern: {pattern}")

    def _get_namespaced_key(self, key: str, collection_name: str) -> str:
        """Generate a namespaced key for Redis storage"""
        return f"{collection_name}:{key}"

    def _get_namespaced_pattern(
        self, collection_name: str, context: Optional[UserContext], scope: CacheScope
    ) -> str:
        """Generate a pattern to match keys for clearing the cache"""
        if collection_name is None:
            collection_name = "*"
        scope_str = get_context_scope_string(context, scope).strip(":") if context else "*"
        scope_str = scope_str.strip(":")
        return f"{collection_name}:{scope_str}:*"

    def _enforce_max_entries(self, collection_name: str) -> None:
        """Enforce the max_entries limit by removing the oldest entries"""
        keys_pattern = f"{collection_name}:*"
        keys = self.client.keys(keys_pattern)
        if len(keys) > self.max_entries:
            sorted_keys = sorted(keys, key=lambda k: self.client.ttl(k) or float("inf"))
            excess = len(sorted_keys) - self.max_entries
            keys_to_remove = sorted_keys[:excess]
            if keys_to_remove:
                self.client.delete(*keys_to_remove)
