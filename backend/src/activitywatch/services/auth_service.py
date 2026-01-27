# app/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from activitywatch.db.repositories.user_repository import UserRepository
from app.core.config import settings
from app.core.security import create_access_token, verify_password


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Регистрация нового пользователя"""
        # Проверка минимальной длины пароля
        if len(password) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        
        # Создание пользователя
        user = self.user_repo.create(
            email=email,
            password=password,
            username=username
        )
        
        # Генерация токена верификации (опционально)
        verification_token = self._create_verification_token(user.email)
        
        # TODO: Отправка email для верификации
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_verified": user.is_verified
            },
            "verification_token": verification_token,
            "message": "Регистрация успешна. Проверьте ваш email для подтверждения."
        }

    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Аутентификация пользователя"""
        # Проверка учетных данных
        user = self.user_repo.authenticate(email, password)
        if not user:
            raise ValueError("Неверный email или пароль")
        
        if not user.is_verified:
            # Можно разрешить вход без верификации, но ограничить функциональность
            # Или отправить новый токен верификации
            raise ValueError("Email не подтвержден. Проверьте вашу почту.")
        
        # Создание access токена
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        # Обновление времени последнего входа (если есть такое поле)
        self.user_repo.update(user.id, last_login=datetime.now(timezone.utc))
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_verified": user.is_verified
            }
        }

    def verify_email(self, token: str) -> bool:
        """Подтверждение email по токену"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                return False
            
            return self.user_repo.verify_user(email)
        except JWTError:
            return False

    def _create_verification_token(self, email: str) -> str:
        """Создание токена для верификации email"""
        to_encode = {"sub": email}
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
        to_encode.update({"exp": expire})
        
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    def reset_password_request(self, email: str) -> Dict[str, Any]:
        """Запрос на сброс пароля"""
        user = self.user_repo.get_by_email(email)
        if not user:
            # Для безопасности не сообщаем, что пользователь не найден
            return {
                "message": "Если email существует, на него будет отправлена инструкция"
            }
        
        # Создание токена для сброса пароля
        reset_token = create_access_token(
            data={"sub": user.email, "purpose": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # TODO: Отправка email со ссылкой для сброса пароля
        
        return {
            "reset_token": reset_token,
            "message": "Инструкция по сбросу пароля отправлена на email"
        }

    def reset_password(self, token: str, new_password: str) -> bool:
        """Сброс пароля по токену"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            email: str = payload.get("sub")
            purpose: str = payload.get("purpose")
            
            if email is None or purpose != "password_reset":
                return False
            
            user = self.user_repo.get_by_email(email)
            if not user:
                return False
            
            # Обновление пароля
            self.user_repo.update(
                user.id,
                password_hash=get_password_hash(new_password)
            )
            return True
            
        except JWTError:
            return False