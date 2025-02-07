import redis
from typing import Optional

from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.models import CacheScope, UserContext


class RedisBackend(BaseBackend):
    def __init__(self, host="localhost", port=6379, db=0, **kwargs):
        """Initialize Redis client"""
        self.client = redis.Redis(host=host, port=port, db=db, **kwargs)

    def get(self, key: str):
        """Get a value from cache by key"""
        return self.client.get(key)

    def set(self, key: str, value, ttl: int = None):
        """Set a value in cache with optional TTL"""
        if ttl is not None:
            self.client.setex(key, ttl, value)
        else:
            self.client.set(key, value)

    def delete(self, key: str):
        """Delete a value from cache by key"""
        self.client.delete(key)

    def clear(
        self,
        collection_name: str = None,
        context: Optional[UserContext] = None,
        scope: CacheScope = CacheScope.ORGANIZATION.value
    ) -> None:
        """Clear cache entries based on collection name and context

        Args:
            collection_name: Optional collection/prefix to filter keys by
            context: UserContext containing user and root_user string IDs
            scope: CacheScope determining which context attribute to use
        """
        # If no context provided, clear everything matching collection
        if context is None:
            pattern = f"{collection_name}:*" if collection_name else "*"
            self._delete_by_pattern(pattern)
            return

        # Build pattern based on scope and context
        if scope == CacheScope.GLOBAL.value:
            pattern = f"{collection_name}:global:*" if collection_name else "global:*"
        elif scope == CacheScope.ORGANIZATION.value and context.root_user:
            # Use root_user string ID for organization scope
            pattern = f"{collection_name}:{context.root_user}:*" if collection_name else f"{context.root_user}:*"
        elif scope == CacheScope.USER.value and context.user:
            # Use user string ID for user scope
            pattern = f"{collection_name}:{context.user}:*" if collection_name else f"{context.user}:*"
        else:
            return

        self._delete_by_pattern(pattern)

    def _delete_by_pattern(self, pattern: str) -> None:
        """Helper method to delete keys matching a pattern"""
        cursor = 0
        while True:
            cursor, keys = self.client.scan(cursor, match=pattern)
            for key in keys:
                self.client.delete(key)
            if cursor == 0:
                break