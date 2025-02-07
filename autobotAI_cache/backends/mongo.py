from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.exceptions import CacheMissError
from autobotAI_cache.core.models import CacheScope, UserContext


class MongoDBBackend(BaseBackend):
    def __init__(
        self,
        mongo_client: MongoClient,
        db_name: str = "mongo_memoize",
        max_entries: Optional[int] = None,
    ):
        if not self._is_client_active(mongo_client):
            raise ConnectionError("MongoDB client is not active.")
        self.mongo_client = mongo_client
        self.db_name = db_name
        self.max_entries = max_entries
        self._collection = None
        self._db = None

        self._ensure_db()

    def _is_client_active(self, client: MongoClient) -> bool:
        try:
            client.admin.command("ping")  # More robust ping
            return True
        except ConnectionFailure:
            return False
        except Exception as e:
            print(f"A unexpected error occured while checking connection {e}")
            return False
    
    def _ensure_db(self):
        if self.db_name not in self.mongo_client.list_database_names():
            self.mongo_client[self.db_name]

        self._db = self.mongo_client[self.db_name]

    def _ensure_collection_and_indexes(self, collection_name: str) -> None:
        """Ensures the collection, and indexes exist."""
        if collection_name not in self._db.list_collection_names():
            self._db.create_collection(collection_name)

        collection = self._db[collection_name]
        indexes = collection.index_information()
        if "expire_at_1" not in indexes:
            collection.create_index(
                [("expire_at", pymongo.ASCENDING)], expireAfterSeconds=0
            )
        self._collection = collection

    def get(self, key: str, collection_name: str) -> Any:
        self._ensure_collection_and_indexes(collection_name)

        doc = self._collection.find_one({"_id": key})
        if not doc:
            raise CacheMissError(f"Key '{key}' not found")
        expire_at = doc.get("expire_at")
        if expire_at:
            if (
                isinstance(expire_at, datetime) and expire_at.tzinfo is None
            ):
                expire_at = expire_at.replace(
                    tzinfo=timezone.utc
                )
            if expire_at < datetime.now(timezone.utc):
                self._collection.delete_one({"_id": key})
                raise CacheMissError(f"Key '{key}' expired")

        return doc["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None, collection_name: str = None) -> None:
        self._ensure_collection_and_indexes(collection_name)

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
        count = self._collection.count_documents({})
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

    def delete(self, key: str, collection_name: str) -> None:
        self._collection = self._db[collection_name]
        result = self._collection.delete_one({"_id": key})
        if result.deleted_count == 0:
            raise CacheMissError(f"Key '{key}' not found")

    def clear(
        self,
        collection_name: str = None,
        context: Optional[UserContext] = None,
        scope: CacheScope = CacheScope.ORGANIZATION.value,
    ) -> None:
        if collection_name:
            self._db.drop_collection(collection_name)
        else:
            self.mongo_client.drop_database(self.db_name)
