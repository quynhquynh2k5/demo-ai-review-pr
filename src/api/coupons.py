from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_current_admin, get_current_user
from src.models.user import User
from src.schemas.coupon import CouponApply, CouponCreate, CouponResponse
from src.services.coupon import create_coupon, validate_coupon

router = APIRouter(prefix="/coupons", tags=["coupons"])


@router.post("", response_model=CouponResponse, status_code=201)
async def create_coupon_endpoint(
    payload: CouponCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> CouponResponse:
    coupon = await create_coupon(db, payload)
    return CouponResponse.model_validate(coupon)


@router.post("/validate", response_model=CouponResponse)
async def validate_coupon_endpoint(
    payload: CouponApply,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CouponResponse:
    coupon = await validate_coupon(db, payload.code)
    return CouponResponse.model_validate(coupon)
