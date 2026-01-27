# activitywatch/api/routers/auth.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any

from src.activitywatch.loader import db
from src.activitywatch.schemas.auth.schema import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
)
from src.activitywatch.core.security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Dict[str, Any])
async def register(user_data: UserRegister, response: Response):
    """Регистрация нового пользователя"""
    try:
        # Создаем пользователя через db.users
        user = await db.users.create_user(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username,
        )

        print(f"Создан пользователь: {user.id}, {user.email}")

        # Генерируем access токен с user_id для авторизации
        access_token = create_access_token(
            data={
                "sub": user.email,
                "user_id": user.id,
                "type": "access",  # Тип токена: access
            },
            expires_delta=timedelta(days=30),  # Токен на 30 дней
        )

        # Генерируем токен верификации email
        verification_token = create_access_token(
            data={
                "sub": user.email,
                "user_id": user.id,
                "type": "verify_email",  # Тип токена: для верификации
            },
            expires_delta=timedelta(hours=24),
        )

        # Устанавливаем access токен в куки для авторизации
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=False,  # True в production с HTTPS
            samesite="lax",
            max_age=30 * 24 * 60 * 60,  # 30 дней
            path="/",
        )

        return {
            "success": True,
            "message": "Пользователь успешно зарегистрирован",
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "verification_token": verification_token,  # Отправляем клиенту для верификации email
            "access_token": access_token,  # Также возвращаем в ответе (опционально)
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Ошибка при регистрации: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при регистрации: {str(e)}",
        )


@router.post("/login", response_model=Dict[str, Any])
async def login(user_data: UserLogin, response: Response):
    """Аутентификация пользователя (простая проверка)"""
    try:
        print(f"Попытка входа: {user_data.email}")

        user = await db.users.authenticate_user(
            email=user_data.email, password=user_data.password
        )

        if not user:
            print("Пользователь не найден или неверный пароль")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        print(f"Пользователь найден: {user.id}, {user.email}")

        # Создаем access токен с user_id
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "type": "access"},
            expires_delta=timedelta(days=30),  # Токен на 30 дней
        )

        # Устанавливаем токен в куки
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=False,  # True в production с HTTPS
            samesite="lax",
            max_age=30 * 24 * 60 * 60,  # 30 дней
            path="/",
        )

        return {
            "success": True,
            "message": "Вход выполнен успешно",
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "access_token": access_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
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
            detail="Неверный или просроченный токен",
        )

    email = payload.get("sub")
    user_id = payload.get("user_id")
    purpose = payload.get("type")  # Используем type вместо purpose

    if not email or purpose != "verify_email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный токен"
        )

    # Подтверждаем email через db.users
    result = await db.users.verify_user_email(email)

    if result:
        return {"success": True, "message": "Email успешно подтвержден"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )


@router.post("/me")
async def get_current_user(request: Request):
    """Получение информации о текущем пользователе через куки"""
    try:
        # Получаем токен из куки
        token = request.cookies.get("token")
        print(f"Получен токен из куки: {token[:50] if token else 'None'}...")

        if not token:
            print("Токен не найден в куках")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован"
            )

        # Декодируем токен
        payload = decode_access_token(token)
        if not payload:
            print("Не удалось декодировать токен или токен истек")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или истекший токен",
            )

        print(f"Декодированный payload: {payload}")

        user_id = payload.get("user_id")
        token_type = payload.get("type")

        if not user_id:
            print("user_id не найден в токене")
            print(f"Токен содержит: {payload}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен: отсутствует user_id",
            )

        # Проверяем тип токена (должен быть access)
        if token_type != "access":
            print(f"Неправильный тип токена: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена"
            )

        print(f"Ищем пользователя с ID: {user_id}")

        # Получаем пользователя через db.users
        user = await db.users.get_user_by_id(user_id)

        if not user:
            print("Пользователь не найден в БД")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
            )

        print(f"Найден пользователь: {user.email}")

        return {
            "success": True,
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    except HTTPException as he:
        print(f"HTTP Exception в /me: {he.detail}")
        raise he
    except Exception as e:
        print(f"Ошибка в /me: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при получении данных пользователя",
        )


@router.post("/logout")
async def logout(response: Response):
    """Выход пользователя (удаление куки)"""
    try:
        # Удаляем куку с токеном
        response.delete_cookie(key="token", path="/")
        return {"success": True, "message": "Выход выполнен успешно"}
    except Exception as e:
        print(f"Ошибка при выходе: {str(e)}")
        return {"success": True, "message": "Выход выполнен"}
