import re

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product import Product
from src.schemas.product import ProductCreate, ProductUpdate
from src.utils.pagination import PaginationParams

_SEARCH_PATTERN = re.compile(r"[^\w\s\-]")


async def list_products(
    db: AsyncSession,
    pagination: PaginationParams,
    search: str | None = None,
    category: str | None = None,
) -> tuple[list[Product], int]:
    query = select(Product).where(Product.is_active == True)  # noqa: E712
    count_query = (
        select(func.count()).select_from(Product).where(Product.is_active == True)
    )  # noqa: E712

    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
        count_query = count_query.where(Product.name.ilike(f"%{search}%"))

    if category:
        query = query.where(Product.category == category)
        count_query = count_query.where(Product.category == category)

    query = (
        query.order_by(Product.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query)
    products = list(result.scalars().all())

    return products, total


async def get_product(db: AsyncSession, product_id: int) -> Product:
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )  # noqa: E712
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession, product_id: int, payload: ProductUpdate
) -> Product:
    product = await get_product(db, product_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: int) -> None:
    product = await get_product(db, product_id)
    product.is_active = False
    await db.commit()
