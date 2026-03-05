from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.cart import Cart, CartItem
from src.models.product import Product


async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.scalar_one_or_none()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
        cart.items = []
    return cart


async def add_item(
    db: AsyncSession, user_id: int, product_id: int, quantity: int
) -> Cart:
    product_result = await db.execute(
        select(Product).where(
            Product.id == product_id, Product.is_active == True
        )  # noqa: E712
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if product.stock < quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Insufficient stock"
        )

    cart = await get_or_create_cart(db, user_id)

    existing_result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id, CartItem.product_id == product_id
        )
    )
    existing_item = existing_result.scalar_one_or_none()

    if existing_item is not None:
        new_qty = existing_item.quantity + quantity
        if product.stock < new_qty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Insufficient stock"
            )
        existing_item.quantity = new_qty
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.add(cart_item)

    await db.commit()
    return await get_or_create_cart(db, user_id)


async def update_item(
    db: AsyncSession, user_id: int, item_id: int, quantity: int
) -> Cart:
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(CartItem.id == item_id, Cart.user_id == user_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found"
        )

    product_result = await db.execute(
        select(Product).where(Product.id == item.product_id)
    )
    product = product_result.scalar_one_or_none()
    if product is None or product.stock < quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Insufficient stock"
        )

    item.quantity = quantity
    await db.commit()
    return await get_or_create_cart(db, user_id)


async def remove_item(db: AsyncSession, user_id: int, item_id: int) -> Cart:
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(CartItem.id == item_id, Cart.user_id == user_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found"
        )

    await db.delete(item)
    await db.commit()
    return await get_or_create_cart(db, user_id)


async def clear_cart(db: AsyncSession, user_id: int) -> None:
    cart_result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = cart_result.scalar_one_or_none()
    if cart is None:
        return
    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    for item in items_result.scalars().all():
        await db.delete(item)
    await db.commit()


def compute_cart_subtotal(cart: Cart) -> Decimal:
    return sum(item.product.price * item.quantity for item in cart.items)
