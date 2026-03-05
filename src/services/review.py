from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product
from src.models.review import Review
from src.schemas.review import ReviewCreate
from src.utils.pagination import PaginationParams


async def create_review(db: AsyncSession, user_id: int, product_id: int, payload: ReviewCreate) -> Review:
    product_result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)  # noqa: E712
    )
    if product_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing_result = await db.execute(select(Review).where(Review.user_id == user_id, Review.product_id == product_id))
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product",
        )

    review = Review(user_id=user_id, product_id=product_id, **payload.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def get_product_reviews(
    db: AsyncSession,
    product_id: int,
    pagination: PaginationParams,
) -> tuple[list[Review], int, float | None]:
    product_result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)  # noqa: E712
    )
    if product_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    count_result = await db.execute(select(func.count()).select_from(Review).where(Review.product_id == product_id))
    total = count_result.scalar_one()

    avg_result = await db.execute(select(func.avg(Review.rating)).where(Review.product_id == product_id))
    avg_rating = avg_result.scalar_one()
    average_rating = float(avg_rating) if avg_rating is not None else None

    result = await db.execute(
        select(Review)
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    reviews = list(result.scalars().all())
    return reviews, total, average_rating
