import threading
import time
from typing import Dict, Any
from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.exceptions import CacheMissError


class MemoryBackend(BaseBackend):
    """Thread-safe in-memory cache backend"""
    def __init__(self, max_entries=None):
        # store = "_collection_name" : {"key": "value"}
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._expire_times: Dict[str, float] = {}

        self.max_entries = max_entries

    def get(self, key: str, collection_name: str):
        with self._lock:
            self._store[collection_name] = self._store.get(collection_name, {})

            if key not in self._store[collection_name]:
                raise CacheMissError(f"Key '{key}' not found")

            expire_time = self._expire_times.get(key)
            if expire_time and time.time() > expire_time:
                self.delete(key, collection_name)
                raise CacheMissError(f"Key '{key}' expired")

            return self._store[collection_name][key]

    def set(self, key: str, value, ttl: int = None, collection_name: str = None):
        with self._lock:
            self._store[collection_name] = self._store.get(collection_name, {})

            if (
                self.max_entries
                and len(self._store[collection_name]) >= self.max_entries
            ):
                self._store[collection_name].pop(
                    next(iter(self._store[collection_name]))
                )

            self._store[collection_name][key] = value
            if ttl is not None:
                self._expire_times[key] = time.time() + ttl
            else:
                self._expire_times.pop(key, None)

    def delete(self, key: str, collection_name: str):
        with self._lock:
            self._store.get(collection_name, {}).pop(key, None)
            self._expire_times.pop(key, None)

    def clear(self, collection_name: str =None):
        with self._lock:
            if collection_name:
                del self._store[collection_name]
                return
            self._store.clear()
            self._expire_times.clear()
