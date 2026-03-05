from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies import get_current_admin
from src.models.user import User
from src.schemas.user import UserResponse, UserUpdate
from src.services.admin import delete_user, list_users, update_user
from src.utils.pagination import PaginationParams, paginate_response

router = APIRouter(prefix="/admin", tags=["admin"])


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


@router.get("/users", response_model=UserListResponse)
async def list_users_endpoint(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> UserListResponse:
    users, total = await list_users(db, pagination)
    return UserListResponse(
        **paginate_response(
            [UserResponse.model_validate(u) for u in users],
            total,
            pagination,
        )
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> UserResponse:
    user = await update_user(db, user_id, payload)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> None:
    await delete_user(db, user_id)
