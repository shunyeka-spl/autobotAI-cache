import functools
import logging
from typing import Optional, List
from autobotAI_cache.core.config import settings
from autobotAI_cache.core.exceptions import CacheBackendError, CacheMissError, SerializationError
from autobotAI_cache.core.models import CacheScope
from autobotAI_cache.utils.keygen import generate_cache_key
from autobotAI_cache.utils.serializers import serialize, deserialize


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)

def memoize(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    ignore_args: Optional[List[str]] = None,
    fail_silently: bool = False,
    scope: str = CacheScope.GLOBAL.value,
    verbose: bool = False,
    collection_name: Optional[str] = None,
):
    """
    Memoization decorator that caches function results using configured backend

    :param ttl: Time-to-live in seconds (default 300) # 5 minutes
    :param key_prefix: Custom prefix for cache keys
    :param ignore_args: List of argument names to exclude from cache key
    :param fail_silently: Return uncached result on backend errors if True
    :param scope: CacheScope, i.e. CacheScope.ORGANIZATION.value
    :param verbose: verbose logs
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                cache_key = generate_cache_key(
                    func=func,
                    args=args,
                    kwargs=kwargs,
                    scope=scope,
                    key_prefix=key_prefix,
                    ignore_args=ignore_args,
                    verbose=verbose,
                )

                if verbose:
                    logger.info(f"Generated cache key: {cache_key}")

                cache_collection_name = (
                    collection_name
                    if collection_name is not None
                    else settings.DEFAULT_COLLECTION
                )

                try:
                    cached = settings.backend.get(
                        cache_key, collection_name=cache_collection_name
                    )
                    if cached is not None:
                        if verbose:
                            logger.info(f"Cache hit for key: {cache_key}")
                        return deserialize(cached, settings.SERIALIZER)
                
                except CacheMissError:
                    if verbose:
                        logger.info(f"Cache miss for key: {cache_key}")
                
                except CacheBackendError as e:
                    if verbose:
                        logger.error(f"Cache backend error during get: {str(e)}")
                    if not fail_silently:
                        raise

                result = func(*args, **kwargs)

                try:
                    serialized = serialize(result, settings.SERIALIZER)
                    effective_ttl = ttl if ttl is not None else settings.DEFAULT_TTL
                    
                    settings.backend.set(
                        cache_key,
                        serialized,
                        ttl=effective_ttl,
                        collection_name=cache_collection_name,
                    )
                    
                    if verbose:
                        logger.info(f"Successfully cached result with key: {cache_key}")
                
                except (CacheBackendError, SerializationError) as e:
                    if verbose:
                        logger.error(f"Error caching result: {str(e)}")
                    if not fail_silently:
                        raise

                return result
                
            except Exception as e:
                if verbose:
                    logger.error(f"Unexpected error in memoize decorator: {str(e)}")
                if not fail_silently:
                    raise
                return func(*args, **kwargs)

        return wrapper

    return decorator
