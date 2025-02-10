from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from autobotAI_cache.backends.base import BaseBackend
from autobotAI_cache.core.exceptions import CacheMissError
from autobotAI_cache.core.models import CacheScope, UserContext
from autobotAI_cache.utils.helpers import get_context_scope_string


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

        except Exception as exc:
            print(f"A unexpected error occured while checking connection {exc}")
            return False

    def _ensure_db(self):
        if self.db_name not in self.mongo_client.list_database_names():
            self.mongo_client[self.db_name]

        self._db = self.mongo_client[self.db_name]

    def _ensure_collection_and_indexes(self, collection_name: str) -> None:
        """Ensures the collection, and indexes exist."""

        collection = self._db[collection_name]

        if collection.name not in self._db.list_collection_names():
            if self.max_entries is None:
                # Create regular (non-capped) collection
                self._db.create_collection(collection.name)
            else:
                # Create capped collection with both size and max parameters
                self._db.create_collection(
                    collection.name,
                    capped=True,
                    size=self.max_entries * 1024,  # Size in bytes
                    max=self.max_entries,
                )

        # Ensure all required indexes exist
        collection.create_index(
            [
                ("key_hash", pymongo.ASCENDING),
                ("scope", pymongo.ASCENDING),
                ("root_user_id", pymongo.ASCENDING),
                ("user_id", pymongo.ASCENDING),
            ],
            unique=True,
            sparse=True,
        )

        collection.create_index(
            [("expire_at", pymongo.ASCENDING)], expireAfterSeconds=0
        )
        collection.create_index([("created_at", pymongo.ASCENDING)])

        self._collection = collection

    def _parse_key(
        self, key: str
    ) -> tuple[str, Optional[str], Optional[str], CacheScope]:
        parts = [part for part in key.split(":", 2) if part]
        if len(parts) == 3:  # root_user_id:user_id:key_hash
            return parts[2], parts[0], parts[1], CacheScope.USER
        elif len(parts) == 2:
            if parts[0] == CacheScope.GLOBAL.value:  # global:key_hash
                return parts[1], None, None, CacheScope.GLOBAL
            return (
                parts[1],
                parts[0],
                None,
                CacheScope.ORGANIZATION,
            )  # root_user_id::key_hash

    def get(self, key: str, collection_name: str) -> Any:
        self._ensure_collection_and_indexes(collection_name)

        key_hash, root_user_id, user_id, scope = self._parse_key(key)

        query = {"key_hash": key_hash}
        if scope == CacheScope.GLOBAL:
            query["scope"] = CacheScope.GLOBAL.value
        elif scope == CacheScope.ORGANIZATION:
            query.update(
                {"root_user_id": root_user_id, "scope": CacheScope.ORGANIZATION.value}
            )
        else:  # USER scope
            query.update(
                {
                    "root_user_id": root_user_id,
                    "user_id": user_id,
                    "scope": CacheScope.USER.value,
                }
            )

        doc = self._collection.find_one(query)
        if not doc:
            raise CacheMissError(f"Key '{key}' not found")

        expire_at = doc.get("expire_at")
        if expire_at:
            if isinstance(expire_at, datetime) and expire_at.tzinfo is None:
                expire_at = expire_at.replace(tzinfo=timezone.utc)
            if expire_at < datetime.now(timezone.utc):
                self._collection.delete_one(query)
                raise CacheMissError(f"Key '{key}' expired")

        return doc["value"]

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        collection_name: str = None,
    ) -> None:
        self._ensure_collection_and_indexes(collection_name)

        key_hash, root_user_id, user_id, scope = self._parse_key(key)

        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(seconds=ttl) if ttl is not None else None

        # Build the document to insert
        document = {
            "key_hash": key_hash,
            "value": value,
            "created_at": now,
            "expire_at": expire_at,
            "scope": scope.value,
        }
        if root_user_id:
            document["root_user_id"] = root_user_id
        if user_id:
            document["user_id"] = user_id

        try:
            self._collection.insert_one(document)
        except pymongo.errors.DuplicateKeyError:
            # This should not happen since get() ensures absence
            print(f"Key '{key}' already exists. Insertion skipped.")
        except pymongo.errors.PyMongoError as e:
            print(f"Error inserting cache: {e}")

        if self.max_entries is not None:
            if not self._collection.options().get("capped", False):
                self._enforce_max_entries()

    def _enforce_max_entries(self) -> None:
        try:
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
        except pymongo.errors.PyMongoError as e:
            print(f"Error enforcing max entries: {e}")

    def delete(self, key: str, collection_name: str) -> None:
        self._ensure_collection_and_indexes(collection_name)

        key_hash, root_user_id, user_id, scope = self._parse_key(key)

        query = {"key_hash": key_hash}
        if scope == CacheScope.GLOBAL:
            query["scope"] = CacheScope.GLOBAL.value
        elif scope == CacheScope.ORGANIZATION:
            query.update(
                {"root_user_id": root_user_id, "scope": CacheScope.ORGANIZATION.value}
            )
        else:  # USER scope
            query.update(
                {
                    "root_user_id": root_user_id,
                    "user_id": user_id,
                    "scope": CacheScope.USER.value,
                }
            )

        result = self._collection.delete_one(query)
        if result.deleted_count == 0:
            raise CacheMissError(f"Key '{key}' not found")

    def clear(
        self,
        collection_name: str = None,
        context: Optional[UserContext] = None,
        scope: CacheScope = CacheScope.ORGANIZATION,
    ) -> None:
        context_scope_str = get_context_scope_string(context, scope)
        collections = [collection_name] if collection_name else self._db.list_collection_names()
        for collection in collections:
            query = {}
            if scope == CacheScope.ORGANIZATION:
                query["root_user_id"] = context_scope_str.split(":")[0]
            elif scope == CacheScope.USER:
                query["root_user_id"] = context_scope_str.split(":")[0]
                query["user_id"] = context_scope_str.split(":")[1]
            
            self._collection = self._db[collection]
            self._collection.delete_many(query)
            print(f"Cache cleared for collection: {collection}")
