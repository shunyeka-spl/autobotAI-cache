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

    # Extract function name and module
    func_name = func.__name__
    module_name = inspect.getmodule(func).__name__

    # Prepare argument string
    arg_str = ""
    for i, arg in enumerate(args):
        arg_str += f"{i}={arg}_"

    for key, value in kwargs.items():
        if ignore_args and key in ignore_args:
            continue
        arg_str += f"{key}={value}_"

    # Combine elements and hash
    key_str = f"{key_prefix or ''}{module_name}:{func_name}:{arg_str}"
    return hashlib.sha256(key_str.encode()).hexdigest()
