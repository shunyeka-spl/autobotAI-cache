from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.backends.memory import MemoryBackend
from autobotAI_cache.backends.mongo import MongoDBBackend


class BackendRegistry:
    """
    Registry for cache backends.
    """

    _backends = {
        "memory": MemoryBackend,
        # "redis": RedisBackend,
        "mongo": MongoDBBackend,
        # Add more backends here
    }

    @classmethod
    def get_backend(cls, backend_name: str) -> BaseBackend:
        """
        Returns the class of the specified backend.

        :param backend_name: Name of the backend to retrieve
        :return: Class of the backend
        :raises ValueError: If the specified backend is not registered
        """
        if backend_name not in cls._backends:
            raise ValueError(f"Backend '{backend_name}' is not registered.")
        return cls._backends[backend_name]
