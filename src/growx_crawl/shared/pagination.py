"""
GrowX Platform Standard Pagination Primitives.
"""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool = False

    @classmethod
    def create(cls, items: List[T], total: int, limit: int, offset: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )
