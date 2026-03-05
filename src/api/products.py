from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_current_admin
from src.models.user import User
from src.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from src.services.product import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)
from src.utils.pagination import PaginationParams, paginate_response

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products_endpoint(
    search: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    products, total = await list_products(
        db, pagination, search=search, category=category
    )
    return ProductListResponse(
        **paginate_response(
            [ProductResponse.model_validate(p) for p in products],
            total,
            pagination,
        )
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_endpoint(
    product_id: int, db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    product = await get_product(db, product_id)
    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product_endpoint(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> ProductResponse:
    product = await create_product(db, payload)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product_endpoint(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> ProductResponse:
    product = await update_product(db, product_id, payload)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=204)
async def delete_product_endpoint(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> None:
    await delete_product(db, product_id)
