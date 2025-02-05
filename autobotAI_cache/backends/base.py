from abc import ABC, abstractmethod


class BaseBackend(ABC):
    """
    Abstract base class for all cache backend implementations
    """
    @abstractmethod
    def get(self, key: str, collection_name: str = None) -> bytes:
        """
        Retrieve a value from the cache by its key

        :param key: Cache key
        :param collection__name: If not provided uses default collection name configured
        :raises CacheMissError: If the key is not found
        :raises CacheError: For other backend errors
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: bytes, ttl: int = None, collection_name: str = None) -> None:
        """
        Store a value in the cache with an optional TTL

        :param key: Cache key
        :param value: Serialized data to cache
        :param ttl: Time-to-live in seconds (optional)
        :param collection__name: If not provided uses default collection name configured
        :raises CacheError: For backend errors
        """
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, key: str, collection_name: str = None) -> None:
        """
        Delete a value from the cache by its key

        :param key: Cache key
        :param collection__name: If not provided uses default collection name configured
        :raises CacheError: For backend errors
        """
        raise NotImplementedError
    
    @abstractmethod
    def clear(self, collection_name: str = None) -> None:
        """
        Clears the Cache.

        collection_name:
            'None': clears all collections
            'colleection_name': provide collection name which you want to clear
        """
        raise NotImplementedError
