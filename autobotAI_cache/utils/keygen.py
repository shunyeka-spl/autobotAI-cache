import hashlib
import inspect

from autobotAI_cache.core.models import CacheScope
from autobotAI_cache.utils.helpers import generate_scoped_context_key


def generate_cache_key(
    func,
    args,
    kwargs,
    scope=CacheScope.ORGANIZATION.value,
    key_prefix=None,
    ignore_args=None,
    verbose=False,
):
    """
    Generates a unique cache key based on the function, arguments, and keyword arguments.

    :param func: The function being memoized
    :param args: Positional arguments passed to the function
    :param kwargs: Keyword arguments passed to the function
    :param scope: Scope level of generated key, default CacheScope.ORGANIZATION.value
    :param key_prefix: Optional prefix for the cache key
    :param ignore_args: List of argument names to exclude from key generation
    :return: The generated cache key
    """
    # Preevent context from being the part of key string
    ignore_args = set(ignore_args or [])
    ignore_args.update(["ctx", "rctx", "_ctx", "_rctx", "request_context"])
    bound = inspect.signature(func).bind(*args, **kwargs)
    bound.apply_defaults()

    key_components = []
    # Handle self/cls intelligently
    if "self" in bound.arguments and "self" not in ignore_args:
        key_components.append(f"self_id={id(bound.arguments['self'])}")
    elif "cls" in bound.arguments and "cls" not in ignore_args:
        key_components.append(f"cls_name={bound.arguments['cls'].__name__}")

    # Filter out ignored arguments
    filtered_args = {
        name: value
        for name, value in bound.arguments.items()
        if name not in ignore_args and name not in ["self", "cls"]
    }

    # Ensure consistent ordering for keyword arguments
    sorted_items = sorted(filtered_args.items())
    arg_str = "_".join(f"{name}={repr(value)}" for name, value in sorted_items)

    # String for key components
    key_components_str = "_".join(key_components)

    # Build a fully qualified function name (module and qualified name)
    func_qualname = f"{func.__module__}.{func.__qualname__}"

    key_str = f"{key_prefix or ''}{func_qualname}:{arg_str}_{key_components_str}"

    # scoped_context_key refers to user_id, root_user_id or global
    scoped_context_key = generate_scoped_context_key(bound.arguments, scope=scope)

    return f"{scoped_context_key}:{hashlib.sha256(key_str.encode()).hexdigest()}"
