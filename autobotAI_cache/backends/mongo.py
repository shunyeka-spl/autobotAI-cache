from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.exceptions import CacheMissError


class MongoDBBackend(BaseBackend):
    def __init__(
        self,
        mongo_client: MongoClient,
        db_name: str = "mongo_memoize",
        collection_name: str = "cache_collection",
        max_entries: Optional[int] = None,
    ):
        if not self._is_client_active(mongo_client):
            raise ConnectionError("MongoDB client is not active.")

        self.mongo_client = mongo_client
        self.db_name = db_name
        self.collection_name = collection_name
        self.max_entries = max_entries

        self._collection = None
        self._db = None
        self._ensure_db_and_collection_and_indexes()

    def _is_client_active(self, client: MongoClient) -> bool:
        try:
            client.admin.command("ping")  # More robust ping
            return True
        except ConnectionFailure:
            return False
        except Exception as e:
            print(f"A unexpected error occured while checking connection {e}")
            return False

    def _ensure_db_and_collection_and_indexes(self) -> None:
        """Ensures the database, collection, and indexes exist."""
        if self.db_name not in self.mongo_client.list_database_names():
            self.mongo_client[self.db_name]

        db = self.mongo_client[self.db_name]
        if self.collection_name not in db.list_collection_names():
            db.create_collection(self.collection_name)

        collection = db[self.collection_name]
        indexes = collection.index_information()
        if "expire_at_1" not in indexes:
            collection.create_index(
                [("expire_at", pymongo.ASCENDING)], expireAfterSeconds=0
            )
        self._collection = collection
        self._db = db

    def get(self, key: str) -> Any:
        doc = self._collection.find_one({"_id": key})
        if not doc:
            raise CacheMissError(f"Key '{key}' not found")

        if doc.get("expire_at") and doc["expire_at"] < datetime.now(timezone.utc):
            self._collection.delete_one({"_id": key})
            raise CacheMissError(f"Key '{key}' expired")

        return doc["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(seconds=ttl) if ttl is not None else None

        update_data = {
            "value": value,
            "updated_at": now,
            "expire_at": expire_at,
        }

        if not self._collection.find_one({"_id": key}):
            update_data["created_at"] = now

        self._collection.update_one({"_id": key}, {"$set": update_data}, upsert=True)

        if self.max_entries is not None:
            self._enforce_max_entries()

    def _enforce_max_entries(self) -> None:
        count = self.c_ollection.count_documents({})
        if count > self.max_entries:
            excess = count - self.max_entries
            oldest_docs = list(
                self._collection.find({}, {"_id": 1, "created_at": 1})
                .sort("created_at", 1)
                .limit(excess)
            )
            oldest_ids = [doc["_id"] for doc in oldest_docs]
            if oldest_ids:
                self._collection.delete_many(
                    {"_id": {"$in": oldest_ids}}
                )  # Delete in bulk

    def delete(self, key: str) -> None:
        result = self._collection.delete_one({"_id": key})
        if result.deleted_count == 0:
            raise CacheMissError(f"Key '{key}' not found")

    def clear(self) -> None:
        self._collection.delete_many({})
