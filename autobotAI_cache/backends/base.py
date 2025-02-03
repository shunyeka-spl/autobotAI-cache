from abc import ABC, abstractmethod


class BaseBackend(ABC):
    """
    Abstract base class for all cache backend implementations
    """
    @abstractmethod
    def get(self, key: str) -> bytes:
        """
        Retrieve a value from the cache by its key

        :param key: Cache key
        :raises CacheMissError: If the key is not found
        :raises CacheError: For other backend errors
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: bytes, ttl: int = None) -> None:
        """
        Store a value in the cache with an optional TTL

        :param key: Cache key
        :param value: Serialized data to cache
        :param ttl: Time-to-live in seconds (optional)
        :raises CacheError: For backend errors
        """
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache by its key

        :param key: Cache key
        :raises CacheError: For backend errors
        """
        raise NotImplementedError
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear all values from the cache

        :raises CacheError: For backend errors
        """
        raise NotImplementedError
