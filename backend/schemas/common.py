"""
backend/models/common.py

Shared Pydantic response wrappers and pagination models for API standardization.
All endpoints should return SuccessResponse or ErrorResponse.
"""

from typing import Any, Optional, Generic, TypeVar, List
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Standard success wrapper."""
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error wrapper."""
    success: bool = False
    error: str
    detail: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    success: bool = True
    data: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False


class MessageResponse(BaseModel):
    """Simple message-only response."""
    success: bool = True
    message: str

