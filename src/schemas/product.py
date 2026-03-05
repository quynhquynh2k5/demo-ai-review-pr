from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    price: Decimal = Field(gt=0, decimal_places=2)
    stock: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=100)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str
    price: Decimal
    stock: int
    category: str
    is_active: bool
    created_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int
