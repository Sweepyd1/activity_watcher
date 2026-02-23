from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.activitywatch.config import cfg
from fastapi import  status


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=cfg.security.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        cfg.security.jwt_secret_key,
        algorithm=cfg.security.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            cfg.security.jwt_secret_key,
            algorithms=[cfg.security.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
    
async def get_current_user(request: Request):
    from src.activitywatch.loader import db
    try:
        token = request.cookies.get("token")
        print(f"Получен токен из куки: {token[:50] if token else 'None'}...")

        if not token:
            print("Токен не найден в куках")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован"
            )

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

        if token_type != "access":
            print(f"Неправильный тип токена: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена"
            )

        print(f"Ищем пользователя с ID: {user_id}")

        user = await db.users.get_user_by_id(user_id)

        if not user:
            print("Пользователь не найден в БД")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
            )

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "devices_count": user.devices_count
            if hasattr(user, "devices_count")
            else 0,
        }

    except HTTPException as he:
        print(f"HTTP Exception в get_current_user: {he.detail}")
        raise he
    except Exception as e:
        print(f"Ошибка в get_current_user: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при получении данных пользователя",
        )