from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    discount_percent: Decimal = Field(gt=0, le=100, decimal_places=2)
    max_uses: int = Field(gt=0)
    expires_at: datetime | None = None


class CouponApply(BaseModel):
    code: str


class CouponResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    code: str
    discount_percent: Decimal
    max_uses: int
    current_uses: int
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
