import pytest # type: ignore
from autobotAI_cache.core.config import settings  # noqa: F401
from autobotAI_cache.core.decorators import memoize
import time
from helpers import timeit_return


class TestInMemory:  # Use a class to group related tests
    def test_basic(self):
        @timeit_return
        @memoize()
        def my_function():
            time.sleep(2)  # Simulate some work
            return "Hello, World!"

        res, exc_time = my_function()
        assert res == "Hello, World!"
        assert exc_time == pytest.approx(2, abs=1)
        res, exc_time = my_function()
        assert res == "Hello, World!"
        assert exc_time < 1
