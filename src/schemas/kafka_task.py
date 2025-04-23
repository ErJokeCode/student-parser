from enum import Enum
from pydantic import BaseModel


class TypeTask(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    AUTH = "auth"


class KafkaTask(BaseModel):
    type: TypeTask
    id: str
    collect: str
