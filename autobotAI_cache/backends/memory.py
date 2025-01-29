from typing import Dict
from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.exceptions import CacheMissError


class MemoryBackend(BaseBackend):
    """
    Simple in-memory cache backend
    """

    def __init__(self):
        self._cache: Dict[str, bytes] = {}

    def get(self, key: str) -> bytes:
        if key in self._cache:
            return self._cache[key]
        raise CacheMissError(f"Key '{key}' not found")

    def set(self, key: str, value: bytes, ttl: int = None) -> None:
        self._cache[key] = value