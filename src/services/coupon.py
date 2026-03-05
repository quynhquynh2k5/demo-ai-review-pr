from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.coupon import Coupon
from src.schemas.coupon import CouponCreate


async def create_coupon(db: AsyncSession, payload: CouponCreate) -> Coupon:
    existing = await db.execute(select(Coupon).where(Coupon.code == payload.code))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Coupon code already exists"
        )

    coupon = Coupon(**payload.model_dump())
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon


async def validate_coupon(db: AsyncSession, code: str) -> Coupon:
    result = await db.execute(select(Coupon).where(Coupon.code == code))
    coupon = result.scalar_one_or_none()

    if coupon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found"
        )

    if not coupon.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is not active"
        )

    if coupon.current_uses >= coupon.max_uses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon has reached max uses",
        )

    if coupon.expires_at is not None and coupon.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon has expired"
        )

    return coupon


def compute_discount(subtotal: Decimal, coupon: Coupon) -> Decimal:
    discount = (subtotal * coupon.discount_percent / Decimal("100")).quantize(
        Decimal("0.01")
    )
    return min(discount, subtotal)


async def redeem_coupon(db: AsyncSession, coupon: Coupon) -> None:
    coupon.current_uses += 1
    await db.flush()
