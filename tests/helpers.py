import time
import functools
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


def timeit_return(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time  # return the result and execution time

    return wrapper


class UserContext(BaseModel):
    is_root: bool = False
    root_user: Optional[dict] = None
    user: Optional[dict] = None


class RequestContext(BaseModel):
    config: dict
    logger: Optional[Any] = None
    user_context: Optional[UserContext] = None
    user_email: Optional[str] = None
    integration_context: Optional[Any] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)
    meta: Optional[dict] = None
