from decimal import Decimal

from pydantic import BaseModel, Field

from src.schemas.product import ProductResponse


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0, le=100)


class CartItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    product_id: int
    quantity: int
    product: ProductResponse


class CartResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    items: list[CartItemResponse]
    subtotal: Decimal
