from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class ReviewResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    product_id: int
    rating: int
    comment: str
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    average_rating: float | None
