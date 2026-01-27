from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.activitywatch.config import cfg

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хэширование пароля"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Создание JWT токена"""
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
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(
            token,
            cfg.security.jwt_secret_key,
            algorithms=[cfg.security.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None