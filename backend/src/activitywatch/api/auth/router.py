# activitywatch/api/routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any

from src.activitywatch.loader import db
from src.activitywatch.schemas.auth.schema import UserRegister, UserLogin, TokenResponse, UserResponse
from src.activitywatch.core.security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", response_model=Dict[str, Any])
async def register(
    user_data: UserRegister,
):
    """Регистрация нового пользователя"""
    try:
        # Создаем пользователя через db.users
        user = await db.users.create_user(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username
        )
        
        # Генерируем токен верификации (опционально)
        verification_token = create_access_token(
            data={"sub": user.email, "purpose": "verify_email"},
            expires_delta=timedelta(hours=24)
        )
        
        return {
            "message": "Пользователь успешно зарегистрирован",
            "user_id": user.id,
            "email": user.email,
            "verification_token": verification_token,
            "is_verified": user.is_verified
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при регистрации: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),

):
    """Аутентификация пользователя"""
    # Аутентифицируем пользователя через db.users
    user = await db.users.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        # Можно разрешить вход без верификации, но с ограничениями
        # Или отправить ошибку
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email не подтвержден. Проверьте вашу почту."
        )
    
    # Обновляем время последнего входа
    await db.users.update_user_last_login(user.id)
    
    # Создаем access токен
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email
    )


@router.get("/verify/{token}")
async def verify_email(
    token: str,

):
    """Подтверждение email по токену"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или просроченный токен"
        )
    
    email = payload.get("sub")
    purpose = payload.get("purpose")
    
    if not email or purpose != "verify_email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный токен"
        )
    
    # Подтверждаем email через db.users
    result = await db.users.verify_user_email(email)
    
    if result:
        return {"message": "Email успешно подтвержден"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),

):
    """Получение информации о текущем пользователе"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    
    # Получаем пользователя через db.users
    user = await db.users.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user

@router.post("/logout")
async def logout():
    """Выход пользователя"""
    return {"message": "Успешный выход из системы"}