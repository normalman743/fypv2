from typing import Any, TypeVar, Generic
from pydantic import BaseModel

DataType = TypeVar("DataType")

class SuccessResponse(BaseModel, Generic[DataType]):
    success: bool = True
    data: DataType

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict
