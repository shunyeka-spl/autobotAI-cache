from autobotAI_cache.utils.keygen import generate_cache_key
import pytest
from pydantic import BaseModel # type: ignore


def keyed(key_generator=generate_cache_key):  # Decorator
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = key_generator(func, args, kwargs)
            return key

        return wrapper

    return decorator

# Test Cases
# It works with Argument types
# int, float, str, bool, list, tuple, dict, set, instance, pydantic model

# It works with kw argument types
# int, float, str, bool, list, tuple, dict, set, instance, pydantic model

# It works with Static Method, Class Method


# For testing with Pydantic models
class DummyModel(BaseModel):
    id: int
    name: str


# Tests to ensure key generation doesn't break with various input types
class TestKeyGeneration:
    def test_function_no_error(self):
        @keyed()
        def my_func(a, b=1):
            return a + b

        key = my_func(2, b=3)
        # We don't assert the key's correctness, just that it's generated as a string.
        assert isinstance(key, str)

    def test_mixed_argument_types(self):
        @keyed()
        def func(a, b, c, d, e, f, g, h):
            return a

        key = func(1, 2.0, "three", True, [1, 2], (3, 4), {"x": 5}, {6, 7})
        assert isinstance(key, str)

    def test_keyword_argument_types(self):
        @keyed()
        def func(**kwargs):
            return kwargs

        args = {
            "a": 1,
            "b": 2.0,
            "c": "three",
            "d": True,
            "e": [1, 2],
            "f": (3, 4),
            "g": {"x": 5},
            "h": {6, 7},
        }
        key = func(**args)
        assert isinstance(key, str)

    def test_instance_argument(self):
        class Dummy:
            def __repr__(self):
                return "<Dummy>"

        @keyed()
        def func(obj):
            return obj

        dummy = Dummy()
        key = func(dummy)
        assert isinstance(key, str)

    def test_pydantic_model_argument(self):
        @keyed()
        def func(model):
            return model

        model = DummyModel(id=1, name="Test")
        key = func(model)
        assert isinstance(key, str)

    def test_static_method(self):
        class MyClass:
            @staticmethod
            @keyed()
            def static_func(x, y):
                return x + y

        key = MyClass.static_func(3, 4)
        assert isinstance(key, str)

    def test_class_method(self):
        class MyClass:
            @classmethod
            @keyed()
            def class_func(cls, x):
                return x

        key = MyClass.class_func(5)
        assert isinstance(key, str)
