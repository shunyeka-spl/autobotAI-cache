# AutobotAI Cache: A Flexible and Efficient Caching Library

AutobotAI Cache is a versatile and high-performance caching library that supports multiple backend implementations, providing developers with a robust solution for optimizing application performance through efficient data caching.

This library offers a unified interface for interacting with various cache backends, including in-memory, Redis, and MongoDB. It features a flexible configuration system, intelligent key generation, and support for multi-tenancy and organization-level access control.

## Repository Structure

```
.
├── autobotAI_cache/
│   ├── backends/
│   ├── config/
│   ├── core/
│   └── utils/
├── tests/
├── devfile.yaml
├── LICENSE
├── README.md
├── requirements.txt
├── run1.py
├── run2.py
└── setup.py
```

Key Files:
- `autobotAI_cache/`: Main package directory containing the core functionality
- `tests/`: Directory containing test files
- `devfile.yaml`: Development environment configuration
- `requirements.txt`: Project dependencies
- `setup.py`: Package setup and distribution configuration

## Usage Instructions

### Installation

Prerequisites:
- Python 3.11 or higher

To install AutobotAI Cache, run the following command:

```bash
pip install -r requirements.txt
```

### Getting Started

1. Import the necessary modules:

```python
from autobotAI_cache.core.config import settings
from autobotAI_cache.core.decorators import memoize
```

2. Configure the cache backend (optional, as it uses in-memory cache by default):

```python
settings.configure(
    BACKEND="mongo",
    BACKEND_OPTIONS={
        "host": "localhost",
        "port": 27017,
        "database": "cache_db"
    }
)
```

3. Use the `@memoize` decorator to cache function results:

```python
@memoize(ttl=3600)  # Cache results for 1 hour
def expensive_operation(x, y):
    # Perform expensive computation
    return x + y

result = expensive_operation(5, 10)  # This will be cached
```

4. Advanced usage of the `@memoize` decorator:

```python
# Cache with a custom key prefix
@memoize(key_prefix="user_data")
def get_user_info(user_id):
    # Fetch user info from database
    return user_info

# Cache with specific arguments to ignore
@memoize(ignore_args=["request"])
def process_request(request, user_id):
    # Process the request
    return result

# Cache with verbose option for debugging
@memoize(verbose=True)
def debug_operation():
    # Perform operation with debug output
    return result

# Cache with specific scope
@memoize(scope="user")
def user_specific_operation(user_id):
    # Perform user-specific operation
    return result

# Cache with fail_silently option
@memoize(fail_silently=True)
def fallback_operation():
    # Perform operation that might fail
    return result
```

### Configuration Options

- `BACKEND`: Choose between "memory" (default), "redis", or "mongo"
- `BACKEND_OPTIONS`: Backend-specific configuration options
- `DEFAULT_TTL`: Default time-to-live for cached items (in seconds)
- `MAX_SIZE`: Maximum number of items to store in the cache (for memory backend)

Note: The default cache backend is set to "memory" if not specified.

### Common Use Cases

1. Caching database queries:

```python
@memoize(ttl=300, scope="global")  # Cache for 5 minutes, global scope
def get_user_profile(user_id):
    # Fetch user profile from database
    return user_profile

profile = get_user_profile(123)  # Cached after first call
```

2. Caching API responses:

```python
@memoize(ttl=3600, scope="organization")
def fetch_weather_data(city, org_id):
    # Make API call to weather service
    return weather_data

weather = fetch_weather_data("New York", org_id=456)  # Cached for 1 hour, scoped to organization
```

3. Clearing the cache:

```python
from autobotAI_cache.core.models import UserContext, CacheScope

def clear_cache(collection_name=None, user_context=None, scope=CacheScope.ORGANIZATION):
    settings.backend.clear(
        collection_name=collection_name,
        context=user_context,
        scope=scope
    )

# Clear entire cache
clear_cache()

# Clear specific collection
clear_cache(collection_name="weather_data")

# Clear cache for a specific user
user_context = UserContext(user_id=123, org_id=456)
clear_cache(user_context=user_context, scope=CacheScope.USER)
```

### Integration Patterns

To integrate AutobotAI Cache with your existing application:

1. Initialize the cache in your application's startup code:

```python
from autobotAI_cache.core.config import settings

def initialize_cache():
    settings.configure(
        BACKEND="redis",
        BACKEND_OPTIONS={
            "host": "redis.example.com",
            "port": 6379,
            "db": 0
        }
    )

# Call this function during application startup
initialize_cache()
```

2. Use the `@memoize` decorator on functions or methods that benefit from caching:

```python
from autobotAI_cache.core.decorators import memoize
from autobotAI_cache.core.models import UserContext

class UserService:
    @memoize(ttl=600, scope="organization")  # Cache for 10 minutes, scoped to organization
    def get_user_permissions(self, user_id, org_id):
        # Fetch and compute user permissions
        return permissions

    def get_permissions(self, user_id, org_id):
        user_context = UserContext(user_id=user_id, org_id=org_id)
        return self.get_user_permissions(user_id, org_id, context=user_context)
```

### Testing & Quality

To run the test suite:

```bash
python -m pytest tests/
```

### Troubleshooting

Common Issue: Cache Miss
- Problem: Cached data is not being retrieved as expected.
- Solution:
  1. Check the TTL settings for your cached items.
  2. Verify that the cache key generation is consistent across calls.
  3. Ensure that the backend is properly configured and connected.
  4. Check if the scope and context are correctly set for multi-tenant scenarios.

Debugging:
- Enable debug logging by setting the `DEBUG` environment variable:
  ```bash
  export DEBUG=1
  ```
- Use the `verbose=True` option in the `@memoize` decorator for additional debug output.
- Check the application logs for detailed cache operations and any error messages.

Performance Optimization:
- Monitor cache hit rates using the backend's built-in statistics.
- For Redis and MongoDB backends, use their respective monitoring tools to track cache performance.
- Consider adjusting TTL values based on data volatility and access patterns.
- Use appropriate scopes (global, organization, user) to optimize cache usage and prevent unnecessary cache misses.

## Data Flow

The request data flow through AutobotAI Cache follows these steps:

1. Application code calls a function decorated with `@memoize`.
2. The decorator generates a unique cache key based on the function name, arguments, scope, and context.
3. The cache backend is queried for the generated key.
4. If the key exists in the cache (cache hit):
   - The cached value is returned immediately.
5. If the key does not exist (cache miss):
   - The original function is executed.
   - The result is stored in the cache with the specified TTL and scope.
   - The result is returned to the caller.

```
[Application] -> [Memoize Decorator] -> [Cache Key Generation]
    |                                           |
    v                                           v
[Cache Backend Query] <- - - - - - - - - [Cache Key]
    |
    v
[Cache Hit?] - Yes -> [Return Cached Value]
    |
    No
    |
    v
[Execute Original Function]
    |
    v
[Store Result in Cache]
    |
    v
[Return Result]
```

Note: The cache backend (Memory, Redis, or MongoDB) handles the actual storage and retrieval of cached data, while the core AutobotAI Cache logic manages the caching process, key generation, and scoping.