from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.models.order import Order, OrderItem
from src.models.product import Product
from src.models.user import User
from src.schemas.order import CheckoutRequest
from src.services.cart import clear_cart, compute_cart_subtotal, get_or_create_cart
from src.services.coupon import compute_discount, redeem_coupon, validate_coupon
from src.utils.pagination import PaginationParams


async def checkout(db: AsyncSession, user: User, payload: CheckoutRequest) -> Order:
    cart = await get_or_create_cart(db, user.id)

    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty"
        )

    coupon = None
    if payload.coupon_code:
        coupon = await validate_coupon(db, payload.coupon_code)

    async with db.begin_nested():
        product_ids = [item.product_id for item in cart.items]
        locked_result = await db.execute(
            select(Product).where(Product.id.in_(product_ids)).with_for_update()
        )
        products_by_id = {p.id: p for p in locked_result.scalars().all()}

        for cart_item in cart.items:
            product = products_by_id[cart_item.product_id]
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product '{product.name}' is no longer available",
                )
            if product.stock < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient stock for '{product.name}'",
                )

        subtotal = compute_cart_subtotal(cart)
        discount_amount = Decimal("0.00")
        if coupon is not None:
            discount_amount = compute_discount(subtotal, coupon)

        taxable_amount = subtotal - discount_amount
        tax_amount = (taxable_amount * Decimal(str(settings.tax_rate))).quantize(
            Decimal("0.01")
        )
        total_amount = taxable_amount + tax_amount

        order = Order(
            user_id=user.id,
            status="confirmed",
            total_amount=total_amount,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
        )
        db.add(order)
        await db.flush()

        for cart_item in cart.items:
            product = products_by_id[cart_item.product_id]
            product.stock -= cart_item.quantity
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=product.price,
            )
            db.add(order_item)

        if coupon is not None:
            await redeem_coupon(db, coupon)

    await clear_cart(db, user.id)
    await db.commit()

    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    return result.scalar_one()


async def get_orders(
    db: AsyncSession, user_id: int, pagination: PaginationParams
) -> tuple[list[Order], int]:
    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count()).select_from(Order).where(Order.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    orders = list(result.scalars().all())
    return orders, total


async def get_order(db: AsyncSession, order_id: int, user_id: int) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return order


async def cancel_order(db: AsyncSession, order_id: int, user_id: int) -> Order:
    order = await get_order(db, order_id, user_id)

    if order.status not in ("pending", "confirmed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status '{order.status}'",
        )

    async with db.begin_nested():
        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        order_items = items_result.scalars().all()

        product_ids = [item.product_id for item in order_items]
        products_result = await db.execute(
            select(Product).where(Product.id.in_(product_ids)).with_for_update()
        )
        products_by_id = {p.id: p for p in products_result.scalars().all()}

        for item in order_items:
            products_by_id[item.product_id].stock += item.quantity

        order.status = "cancelled"

    await db.commit()
    await db.refresh(order)
    return order
