from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_current_user
from src.models.user import User
from src.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from src.services.cart import add_item, compute_cart_subtotal, get_or_create_cart, remove_item, update_item

router = APIRouter(prefix="/cart", tags=["cart"])


def _build_cart_response(cart, subtotal: Decimal) -> CartResponse:
    from src.schemas.cart import CartItemResponse
    from src.schemas.product import ProductResponse

    return CartResponse(
        id=cart.id,
        items=[
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                product=ProductResponse.model_validate(item.product),
            )
            for item in cart.items
        ],
        subtotal=subtotal,
    )


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    cart = await get_or_create_cart(db, current_user.id)
    return _build_cart_response(cart, compute_cart_subtotal(cart))


@router.post("/items", response_model=CartResponse, status_code=201)
async def add_cart_item(
    payload: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    cart = await add_item(db, current_user.id, payload.product_id, payload.quantity)
    return _build_cart_response(cart, compute_cart_subtotal(cart))


@router.put("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    cart = await update_item(db, current_user.id, item_id, payload.quantity)
    return _build_cart_response(cart, compute_cart_subtotal(cart))


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    cart = await remove_item(db, current_user.id, item_id)
    return _build_cart_response(cart, compute_cart_subtotal(cart))
