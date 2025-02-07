from enum import Enum
from typing import Optional

from pydantic import BaseModel

class CacheScope(str, Enum):
    USER = "user" # Cache will differ by user id 
    ORGANIZATION = "organization" # Cache will differ by root_user_id
    GLOBAL = "global" # cache will be same everywhere

    def __str__(self):
        return self.value

class UserContext(BaseModel):
    is_root: bool = False
    root_user: Optional[dict] = None
    user: Optional[dict] = None
