from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    status: str
    total_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    created_at: datetime
    items: list[OrderItemResponse]


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


class CheckoutRequest(BaseModel):
    coupon_code: str | None = None
