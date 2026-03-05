from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse
from src.services.review import create_review, get_product_reviews
from src.utils.pagination import PaginationParams

router = APIRouter(prefix="/products", tags=["reviews"])


@router.post("/{product_id}/reviews", response_model=ReviewResponse, status_code=201)
async def create_review_endpoint(
    product_id: int,
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    review = await create_review(db, current_user.id, product_id, payload)
    return ReviewResponse.model_validate(review)


@router.get("/{product_id}/reviews", response_model=ReviewListResponse)
async def list_reviews_endpoint(
    product_id: int,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ReviewListResponse:
    reviews, total, average_rating = await get_product_reviews(
        db, product_id, pagination
    )
    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        average_rating=average_rating,
    )
