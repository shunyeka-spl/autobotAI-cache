import hashlib
import inspect


def generate_cache_key(func, args, kwargs, key_prefix=None, ignore_args=None):
    """
    Generates a unique cache key based on the function, arguments, and keyword arguments.

    :param func: The function being memoized
    :param args: Positional arguments passed to the function
    :param kwargs: Keyword arguments passed to the function
    :param key_prefix: Optional prefix for the cache key
    :param ignore_args: List of argument names to exclude from key generation
    :return: The generated cache key
    """
    ignore_args = set(ignore_args or [])
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    # Filter out ignored arguments
    filtered_args = {
        name: value
        for name, value in bound.arguments.items()
        if name not in ignore_args
    }

    # Ensure consistent ordering for keyword arguments
    sorted_items = sorted(filtered_args.items())
    arg_str = "_".join(f"{name}={repr(value)}" for name, value in sorted_items)

    # Build a fully qualified function name (module and qualified name)
    func_qualname = f"{func.__module__}.{func.__qualname__}"

    key_str = f"{key_prefix or ''}{func_qualname}:{arg_str}"
    return hashlib.sha256(key_str.encode()).hexdigest()
