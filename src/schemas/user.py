from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    is_admin: bool
    balance: Decimal
    created_at: datetime


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_admin: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
