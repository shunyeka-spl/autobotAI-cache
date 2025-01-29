class CacheError(Exception):
    """Base exception for all cache-related errors"""


class CacheMissError(CacheError):
    """Raised when a requested key is not found in the cache"""


class CacheBackendError(CacheError):
    """Raised when there's an error communicating with the cache backend"""


class SerializationError(CacheError):
    """Raised when there's an error serializing/deserializing data"""
