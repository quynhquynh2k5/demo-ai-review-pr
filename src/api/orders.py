from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.schemas.order import CheckoutRequest, OrderListResponse, OrderResponse
from src.services.order import cancel_order, checkout, get_order, get_orders
from src.utils.pagination import PaginationParams, paginate_response

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderResponse, status_code=201)
async def checkout_endpoint(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = await checkout(db, current_user, payload)
    return OrderResponse.model_validate(order)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderListResponse:
    orders, total = await get_orders(db, current_user.id, pagination)
    return OrderListResponse(
        **paginate_response(
            [OrderResponse.model_validate(o) for o in orders],
            total,
            pagination,
        )
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = await get_order(db, order_id, current_user.id)
    return OrderResponse.model_validate(order)


@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order_endpoint(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = await cancel_order(db, order_id, current_user.id)
    return OrderResponse.model_validate(order)
