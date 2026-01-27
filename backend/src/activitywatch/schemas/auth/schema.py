from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
