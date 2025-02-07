from abc import ABC, abstractmethod
from typing import Optional

from autobotAI_cache.core.models import CacheScope, UserContext


class BaseBackend(ABC):
    """
    Abstract base class for all cache backend implementations
    """

    @abstractmethod
    def get(
        self,
        key: str,
        collection_name: str = None
    ) -> bytes:
        """
        Retrieve a value from the cache by its key.

        This method retrieves a cached value associated with the given key. The retrieval can be
        scoped to a specific collection and user context for organization-level access control.

        :param key: Cache key to look up
        :param collection_name: Name of the collection to query. If not provided uses default collection name configured
        :return: The cached value as bytes
        :raises CacheMissError: If the key is not found in the cache
        :raises CacheError: For other backend errors like connection issues
        """
        raise NotImplementedError

    @abstractmethod
    def set(
        self,
        key: str,
        value: bytes,
        ttl: int = None,
        collection_name: str = None
    ) -> None:
        """
        Store a value in the cache with an optional TTL (Time-To-Live).

        This method stores data in the cache with the specified key. The data can be scoped to 
        specific collections and user contexts, with optional expiration time.

        :param key: Cache key to store the value under
        :param value: Serialized data to cache (must be in bytes format)
        :param ttl: Time-to-live in seconds. If None, the value will not expire
        :param collection_name: Name of the collection to store in. If not provided uses default collection name
        :raises CacheError: For backend errors like connection issues or storage failures
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        key: str,
        collection_name: str = None
    ) -> None:
        """
        Delete a value from the cache by its key.

        This method removes a cached value associated with the given key. The deletion operation
        respects collection and user context scoping rules.

        :param key: Cache key to delete
        :param collection_name: Name of the collection to delete from. If not provided uses default collection
        :raises CacheError: For backend errors like connection issues or deletion failures
        """
        raise NotImplementedError

    @abstractmethod
    def clear(
        self,
        collection_name: str = None,
        context: Optional[UserContext] = None,
        scope: CacheScope = CacheScope.ORGANIZATION.value
    ) -> None:
        """
        Clear items from the cache, optionally filtered by collection.

        This method removes all cached items that match the specified criteria. When no collection
        name is provided, it clears all collections. The operation respects the user context and
        scope settings for access control.

        :param collection_name: Name of collection to clear. If None, clears all collections
        :param context: Optional user context containing authentication and authorization details
        :param scope: Cache scope level (e.g. ORGANIZATION, USER) that determines access boundaries
        :raises CacheError: For backend errors like connection issues or clearing failures
        """
        raise NotImplementedError
