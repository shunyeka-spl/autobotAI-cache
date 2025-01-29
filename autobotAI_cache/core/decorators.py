import functools
from typing import Optional, List
from autobotAI_cache.core.config import settings
from autobotAI_cache.core.exceptions import CacheBackendError, CacheMissError
from autobotAI_cache.utils.keygen import generate_cache_key
from autobotAI_cache.utils.serializers import serialize, deserialize


def memoize(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    ignore_args: Optional[List[str]] = None,
    fail_silently: bool = False,
):
    """
    Memoization decorator that caches function results using configured backend

    :param ttl: Time-to-live in seconds (overrides default)
    :param key_prefix: Custom prefix for cache keys
    :param ignore_args: List of argument names to exclude from cache key
    :param fail_silently: Return uncached result on backend errors if True
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(
                func=func,
                args=args,
                kwargs=kwargs,
                key_prefix=key_prefix,
                ignore_args=ignore_args,
            )

            # Attempt to retrieve cached value
            try:
                cached = settings.backend.get(cache_key)
                if cached is not None:
                    return deserialize(cached, settings.SERIALIZER)
            except CacheMissError:
                pass
            except Exception as e:
                if not fail_silently:
                    raise CacheBackendError from e

            # Compute result if not found in cache
            result = func(*args, **kwargs)

            # Store result in cache
            try:
                serialized = serialize(result, settings.SERIALIZER)
                effective_ttl = ttl if ttl is not None else settings.DEFAULT_TTL
                settings.backend.set(cache_key, serialized, ttl=effective_ttl)
            except Exception as e:
                if not fail_silently:
                    raise CacheBackendError from e

            return result

        return wrapper

    return decorator
