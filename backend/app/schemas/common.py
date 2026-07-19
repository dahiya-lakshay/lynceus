from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    page: int
    size: int
    total: int
    total_pages: int
    items: list[T]

    @classmethod
    def create(
        cls,
        *,
        page: int,
        size: int,
        total: int,
        items: list[T],
    ):
        return cls(
            page=page,
            size=size,
            total=total,
            total_pages=ceil(total / size) if total else 0,
            items=items,
        )