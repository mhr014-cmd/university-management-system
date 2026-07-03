"""
Shared response schemas used across multiple domains — currently just the
paginated list envelope (see docs/API_Contract.md's list-endpoint responses,
and CLAUDE.md §11: list endpoints must support pagination).
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
