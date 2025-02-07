import threading
import time
from typing import Dict, Optional
from collections import OrderedDict

from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.exceptions import CacheMissError
from autobotAI_cache.core.models import CacheScope, UserContext
from autobotAI_cache.utils.helpers import get_context_scope_string


class MemoryBackend(BaseBackend):
    """Thread-safe in-memory cache backend with per-collection locking and efficient cleanup"""
    
    def __init__(self, max_entries=None):
        # store = {collection_name: {key: (value, expire_time)}}
        self._store: Dict[str, Dict[str, tuple]] = {}
        # Use separate locks per collection for better concurrency
        self._collection_locks: Dict[str, threading.RLock] = {}
        self._collection_locks_lock = threading.Lock()
        
        self.max_entries = max_entries
        self._last_cleanup = time.time()

    def _get_collection_lock(self, collection_name: str) -> threading.RLock:
        """Get or create a lock for a specific collection"""
        with self._collection_locks_lock:
            if collection_name not in self._collection_locks:
                self._collection_locks[collection_name] = threading.RLock()
            return self._collection_locks[collection_name]
    
    def _cleanup_expired(self, collection_name: str):
        """Remove expired entries from a collection"""
        now = time.time()
            
        collection = self._store.get(collection_name, {})
        expired_keys = [
            key for key, (_, expire_time) in collection.items()
            if expire_time and expire_time <= now
        ]
        for key in expired_keys:
            collection.pop(key, None)
        
        if not collection:
            with self._collection_locks_lock:
                self._collection_locks.pop(collection_name, None)
        
        self._last_cleanup = now

    def get(
        self,
        key: str,
        collection_name: str,
    ) -> bytes:
        collection_name = collection_name
        
        with self._get_collection_lock(collection_name):
            self._cleanup_expired(collection_name)
            
            if collection_name not in self._store:
                raise CacheMissError(f"Key '{key}' not found")
                
            collection = self._store[collection_name]
            if key not in collection:
                raise CacheMissError(f"Key '{key}' not found")
                
            value, expire_time = collection[key]
            if expire_time and time.time() > expire_time:
                collection.pop(key)
                raise CacheMissError(f"Key '{key}' expired")
                
            return value

    def set(
        self,
        key: str,
        value: bytes,
        collection_name: str,
        ttl: int = None,
    ) -> None:
        collection_name = collection_name
        expire_time = time.time() + ttl if ttl is not None else None
        
        with self._get_collection_lock(collection_name):
            if collection_name not in self._store:
                self._store[collection_name] = OrderedDict()
            
            collection = self._store[collection_name]
            
            # Enforce max entries limit using FIFO
            if (
                self.max_entries 
                and len(collection) >= self.max_entries 
                and key not in collection
            ):
                collection.popitem(last=False)
            
            collection[key] = (value, expire_time)
            self._cleanup_expired(collection_name)

    def delete(
        self,
        key: str,
        collection_name: str
    ) -> None:
        collection_name = collection_name or "default"
        
        with self._get_collection_lock(collection_name):
            if collection_name in self._store:
                self._store[collection_name].pop(key, None)
            self._cleanup_expired(collection_name)

    def clear(
        self,
        collection_name: str = None,
        context: Optional[UserContext] = None,
        scope: CacheScope = CacheScope.ORGANIZATION.value
    ) -> None:
        context_scope_str = get_context_scope_string(context, scope)
        collections = [collection_name] if collection_name else list(self._store.keys())
        for collection_name in collections:
            with self._get_collection_lock(collection_name):
                if scope == CacheScope.GLOBAL.value:
                    self._store.pop(collection_name, None)
                    with self._collection_locks_lock:
                        self._collection_locks.pop(collection_name, None)
                    continue
                self._store[collection_name] = OrderedDict({
                    k: v for k, v in self._store.get(collection_name, {}).items()
                    if not k.startswith(context_scope_str)
                })