import functools
from typing import Optional, List
from autobotAI_cache.core.config import settings
from autobotAI_cache.core.exceptions import CacheBackendError, CacheMissError
from autobotAI_cache.core.models import CacheScope
from autobotAI_cache.utils.keygen import generate_cache_key
from autobotAI_cache.utils.serializers import serialize, deserialize


def memoize(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    ignore_args: Optional[List[str]] = None,
    fail_silently: bool = False,
    scope: Optional[CacheScope] = CacheScope.GLOBAL.value,
    verbose: bool = False,
):
    """
    Memoization decorator that caches function results using configured backend

    :param ttl: Time-to-live in seconds (default 300) # 5 minutes
    :param key_prefix: Custom prefix for cache keys
    :param ignore_args: List of argument names to exclude from cache key
    :param fail_silently: Return uncached result on backend errors if True
    :param scope: CacheScope, i.e. CacheScope.GLOBAL.value
    :param verbose: verbose logs
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(
                func=func,
                args=args,
                kwargs=kwargs,
                scope=scope,
                key_prefix=key_prefix,
                ignore_args=ignore_args,
                verbose=verbose
            )

            if verbose:
                print(f"Cache Key Hash: {cache_key}")

            # Attempt to retrieve cached value
            try:
                cached = settings.backend.get(cache_key)
                if cached is not None:
                    if verbose:
                        print(f"Cache hit for key: {cache_key}")
                    return deserialize(cached, settings.SERIALIZER)
            except CacheMissError:
                pass
            except Exception as e:
                if verbose:
                    print(f"Cache error: {e}")
                if not fail_silently:
                    raise CacheBackendError from e

            # Compute result if not found in cache
            result = func(*args, **kwargs)

            # Store result in cache
            try:

                if verbose:
                    print(f"Cache miss for key: {cache_key}")
                    print(f"Storing result in cache for key: {cache_key}")

                serialized = serialize(result, settings.SERIALIZER)
                effective_ttl = ttl if ttl is not None else settings.DEFAULT_TTL
                settings.backend.set(cache_key, serialized, ttl=effective_ttl)
                
            except Exception as e:
                if verbose:
                    print(f"Cache error: {e}")
                if not fail_silently:
                    raise CacheBackendError from e

            return result

        return wrapper

    return decorator
