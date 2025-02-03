from enum import Enum

class CacheScope(str, Enum):
    USER = "user" # Cache will differ by user id 
    ORGANIZATION = "organization" # Cache will differ by root_user_id
    GLOBAL = "global" # cache will be same everywhere

    def __str__(self):
        return self.value
