from autobotAI_cache.core.exceptions import CacheBackendError
from autobotAI_cache.core.models import CacheScope


def generate_scoped_context_key(arguments, scope: CacheScope = CacheScope.ORGANIZATION.value):
    # If Global Scope return 'global'
    if scope == CacheScope.GLOBAL.value:
        return CacheScope.GLOBAL.value
    
    context = None

    # Fetch The context object
    possible_context_key_names = ["ctx", "rctx", "_ctx", "_rctx", "request_context"]
    
    # fetching context through 'self'
    if "self" in arguments:
        for arg_name in possible_context_key_names:
            if hasattr(arguments["self"], arg_name):
                context = getattr(arguments["self"], arg_name)
                break
    
    if context is None:
        for arg_name in possible_context_key_names:
            if arg_name in arguments:
                context = arguments[arg_name]
                break

    if context is None and 'cls' in arguments:
        for arg_name in possible_context_key_names:
            if hasattr(arguments["cls"], arg_name):
                context = getattr(arguments["cls"], arg_name)
                break
    
    return get_context_scope_string(context, scope)


def get_context_scope_string(context, scope):
    if scope == CacheScope.GLOBAL.value:
        return CacheScope.GLOBAL.value
    if hasattr(context, "user_context"):
        # If Organizational Scope return 'organization_root_user_id'
        # If User Scope return 'user_id'
        if scope == CacheScope.USER.value:
            return f"{context.user_context.root_user.get('id', '')}:{context.user_context.user.get('id', '')}"
        elif scope == CacheScope.ORGANIZATION.value:
            return f"{context.user_context.root_user.get('id', '')}:"

    raise CacheBackendError(
        "Error: Couldn't find context in function parameters, Provide context or choose 'Global' scope instead"
    )
