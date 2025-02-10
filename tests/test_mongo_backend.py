import os
import pytest  # type: ignore
from autobotAI_cache.core.config import settings  # noqa: F401
from autobotAI_cache.core.decorators import memoize
import time
from autobotAI_cache.core.models import CacheScope
from helpers import RequestContext, UserContext, timeit_return
import threading
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)  # autouse=True runs automatically
def setup_my_library():
    print("Setting up my library...")
    load_dotenv()
    client = MongoClient(os.environ.get("MONGO_URL"), server_api=ServerApi("1"))
    settings.configure(
        BACKEND="mongo",
        BACKEND_OPTIONS={
            "mongo_client": client,
            # "max_entries": 200
        },
        DEFAULT_TTL=180,  # 3 minutes
    )
    print("My library setup complete.")


class TestMongoMemory:  # Use a class to group related tests
    def teardown_method(self):
        settings.backend.clear(scope=CacheScope.GLOBAL.value)

    @classmethod
    def teardown_class(cls):
        settings.reset()

    def test_basic(self):
        @timeit_return
        @memoize(
            verbose=True, scope=CacheScope.GLOBAL.value, collection_name="my_collection"
        )
        def my_function():
            time.sleep(2)  # Simulate some work
            return "Hello, World!"

        res, exc_time = my_function()
        assert res == "Hello, World!"
        assert exc_time == pytest.approx(2, abs=1)  # Allow some tolerance
        res, exc_time = my_function()
        assert res == "Hello, World!"
        assert exc_time < 1  # Should be much faster (cached)
        settings.backend.clear(scope=CacheScope.GLOBAL.value)

    def test_ttl(self):
        @timeit_return
        @memoize(
            verbose=True,
            ttl=5,
            scope=CacheScope.GLOBAL.value
        )  # TTL of 1 second
        def my_function():
            time.sleep(2)  # Simulate some work
            return "Hello"

        res, exc_time = my_function()
        assert res == "Hello"
        assert exc_time > 2
        res, exc_time = my_function()
        assert res == "Hello"
        assert exc_time < 1
        time.sleep(10)  # Wait for TTL to expire
        res, exc_time = my_function()  # Should compute again
        assert res == "Hello"
        assert exc_time > 2  # should take more time than cached

    def test_capacity(self):
        client = MongoClient(os.environ.get("MONGO_URL"), server_api=ServerApi("1"))
        settings.configure(
            BACKEND="mongo",
            BACKEND_OPTIONS={"mongo_client": client, "max_entries": 2},
            DEFAULT_TTL=300,  # 3 minutes
        )

        @timeit_return
        @memoize(
            verbose=True,
            scope=CacheScope.GLOBAL.value
        )
        def my_function(x):
            time.sleep(2)  # Simulate some work
            return x * 2

        res, exc_time = my_function(1)
        assert res == 2
        assert exc_time > 1

        res, exc_time = my_function(1)
        assert res == 2
        assert exc_time < 1

        res, exc_time = my_function(2)
        assert res == 4
        assert exc_time > 1

        res, exc_time = my_function(3)
        assert res == 6
        assert exc_time > 1

        res, exc_time = my_function(1)
        assert res == 2
        assert exc_time > 1

        settings.configure(
            BACKEND="mongo",
            BACKEND_OPTIONS={"mongo_client": client, "max_entries": None},
            DEFAULT_TTL=300,  # 3 minutes
        )

    def test_ignore_args(self):
        @timeit_return
        @memoize(
            verbose=True,
            ignore_args=["y"],
            scope=CacheScope.GLOBAL.value
        )
        def my_function(x, y):
            time.sleep(2)
            return x * 2

        res, exc_time = my_function(2, 3)
        assert res == 4
        assert exc_time > 1

        res, exc_time = my_function(2, 4)
        assert res == 4
        assert exc_time < 1
        settings.backend.clear(scope=CacheScope.GLOBAL.value)

    def test_concurrency(self):
        @memoize(
            verbose=True,
            scope=CacheScope.GLOBAL.value
        )
        def my_function(x):
            time.sleep(0.1)  # Simulate some work
            return x * 2

        num_threads = 10
        num_operations = 100

        results = []

        def worker():
            for i in range(num_operations):
                result = my_function(i)
                results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Basic check - you might want more specific assertions depending on your concurrency requirements.
        assert len(results) == num_threads * num_operations
        # Check for exceptions (add more detailed checks as needed)
        assert all(
            r is not None for r in results
        )  # check that function didn't return None
        settings.backend.clear(scope=CacheScope.GLOBAL.value)

    def test_collection_name(self):
        @timeit_return
        @memoize(verbose=True, collection_name="my_cole",scope=CacheScope.GLOBAL.value)
        def my_function():
            time.sleep(2)  # Simulate some work
            return "Hello, World!"

        res, exc_time = my_function()
        assert res == "Hello, World!"
        assert exc_time == pytest.approx(2, abs=1)  # Allow some tolerance
        res, exc_time = my_function()
        assert res == "Hello, World!"
        assert exc_time < 1  # Should be much faster (cached)
        settings.backend.clear(scope=CacheScope.GLOBAL.value)

    def test_multitenet_org(self):
        @timeit_return
        @memoize(verbose=True, collection_name="my_cole", scope=CacheScope.ORGANIZATION.value)
        def my_function(ctx):
            time.sleep(2)  # Simulate some work
            return "Hello, World!"

        # Root user context tenet 1
        ctx1 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=True,
                root_user={"id": "ritin@gmail.com"},
                user={"id": "ritin@gmail.com"},
            ),
        )

        subctx1 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=False,
                root_user={"id": "ritin@gmail.com"},
                user={"id": "sub_ritin@gmail.com"},
            ),
        )

        # Root user context tenet 2
        ctx2 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=True,
                root_user={"id": "ritik@gmail.com"},
                user={"id": "ritik@gmail.com"},
            ),
        )

        subctx2 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=False,
                root_user={"id": "ritik@gmail.com"},
                user={"id": "sub_ritik@gmail.com"},
            ),
        )

        res, time_tool1 = my_function(ctx1)
        res, time_tool2 = my_function(ctx2)
        res, time_tool3 = my_function(subctx1)
        res, time_tool4 = my_function(subctx2)
        assert time_tool1 > 2
        assert time_tool2 > 2
        assert time_tool3 < 1
        assert time_tool4 < 1
        res, time_tool1 = my_function(ctx1)
        res, time_tool2 = my_function(ctx2)
        res, time_tool3 = my_function(subctx1)
        res, time_tool4 = my_function(subctx2)
        assert time_tool1 < 1
        assert time_tool2 < 1
        assert time_tool3 < 1
        assert time_tool4 < 1
        settings.backend.clear(
            collection_name="my_cole",
            context=subctx1,
            scope=CacheScope.ORGANIZATION.value,
        )
        res, time_tool1 = my_function(ctx1)
        assert time_tool1 > 2
        res, time_tool2 = my_function(ctx2)
        assert time_tool2 < 1
        res, time_tool3 = my_function(subctx1)
        assert time_tool3 < 1
        res, time_tool4 = my_function(subctx2)
        assert time_tool4 < 1
        settings.backend.clear(
            collection_name="my_cole",
            context=subctx1,
            scope=CacheScope.USER.value,
        )
        res, time_tool1 = my_function(ctx1)
        assert time_tool1 < 1
        res, time_tool2 = my_function(ctx2)
        assert time_tool2 < 1
        res, time_tool3 = my_function(subctx1)
        assert time_tool3 < 1
        res, time_tool4 = my_function(subctx2)
        assert time_tool4 < 1
    
    def test_multitenet_usr(self):
        @timeit_return
        @memoize(
            verbose=True, collection_name="my_cole", scope=CacheScope.USER.value
        )
        def my_function(ctx):
            time.sleep(2)  # Simulate some work
            return "Hello, World!"

        # Root user context tenet 1
        ctx1 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=True,
                root_user={"id": "ritin@gmail.com"},
                user={"id": "ritin@gmail.com"},
            ),
        )

        subctx1 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=False,
                root_user={"id": "ritin@gmail.com"},
                user={"id": "sub_ritin@gmail.com"},
            ),
        )

        # Root user context tenet 2
        ctx2 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=True,
                root_user={"id": "ritik@gmail.com"},
                user={"id": "ritik@gmail.com"},
            ),
        )

        subctx2 = RequestContext(
            config={},
            user_context=UserContext(
                is_root=False,
                root_user={"id": "ritik@gmail.com"},
                user={"id": "sub_ritik@gmail.com"},
            ),
        )

        res, time_tool1 = my_function(ctx1)
        res, time_tool2 = my_function(ctx2)
        res, time_tool3 = my_function(subctx1)
        res, time_tool4 = my_function(subctx2)
        assert time_tool1 > 2
        assert time_tool2 > 2
        assert time_tool3 > 2
        assert time_tool4 > 2
        res, time_tool1 = my_function(ctx1)
        res, time_tool2 = my_function(ctx2)
        res, time_tool3 = my_function(subctx1)
        res, time_tool4 = my_function(subctx2)
        assert time_tool1 < 1
        assert time_tool2 < 1
        assert time_tool3 < 1
        assert time_tool4 < 1
        settings.backend.clear(
            collection_name="my_cole",
            context=subctx1,
            scope=CacheScope.ORGANIZATION.value,
        )
        res, time_tool1 = my_function(ctx1)
        assert time_tool1 > 2
        res, time_tool2 = my_function(ctx2)
        assert time_tool2 < 1
        res, time_tool3 = my_function(subctx1)
        assert time_tool3 > 2
        res, time_tool4 = my_function(subctx2)
        assert time_tool4 < 1
        settings.backend.clear(
            collection_name="my_cole",
            context=subctx1,
            scope=CacheScope.USER.value,
        )
        res, time_tool1 = my_function(ctx1)
        assert time_tool1 < 1
        res, time_tool2 = my_function(ctx2)
        assert time_tool2 < 1
        res, time_tool3 = my_function(subctx1)
        assert time_tool3 > 2
        res, time_tool4 = my_function(subctx2)
        assert time_tool4 < 1

    def test_fail_silently(self):
        @memoize(verbose=True, collection_name="my_cole", scope=CacheScope.GLOBAL.value)
        def my_function():
            print("\n Running Fail funtion")
            return 8 / 1

        res = my_function()
        assert res == 8
        settings.backend.clear(collection_name="my_cole", scope=CacheScope.GLOBAL.value)
