# activitywatch/database/crud/users.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.activitywatch.database.models import User
from src.activitywatch.core.security import verify_password, get_password_hash
from src.activitywatch.database.db_manager import DatabaseManager

if TYPE_CHECKING:
    from . import CommonCRUD


class UsersCRUD:
    db: DatabaseManager

    def __init__(self, db: DatabaseManager, common_crud: CommonCRUD) -> None:
        self.db = db
        self.common = common_crud

    async def create_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> User:
        """Создание нового пользователя"""
        async with self.db.get_session() as session:
            # Проверяем, существует ли пользователь с таким email
            existing_user = await self.get_user_by_email(email, session=session)
            if existing_user:
                raise ValueError("Пользователь с таким email уже существует")
            
            # Проверяем username, если указан
            if username:
                existing_username = await self.get_user_by_username(username, session=session)
                if existing_username:
                    raise ValueError("Пользователь с таким именем уже существует")
            
            # Хэшируем пароль
            password_hash = get_password_hash(password)
            
            # Создаем пользователя
            new_user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                settings=settings or {},
                is_active=True,
                is_verified=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

    async def get_user_by_email(
        self, 
        email: str, 
        session: Optional[AsyncSession] = None
    ) -> Optional[User]:
        """Получение пользователя по email"""
        if session:
            stmt = select(User).where(User.email == email.lower())
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        
        async with self.db.get_session() as session:
            stmt = select(User).where(User.email == email.lower())
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_username(
        self, 
        username: str, 
        session: Optional[AsyncSession] = None
    ) -> Optional[User]:
        """Получение пользователя по имени пользователя"""
        if session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        
        async with self.db.get_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """Аутентификация пользователя"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not user.password_hash:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        return user

    async def update_user_last_login(
        self,
        user_id: int
    ) -> None:
        """Обновление времени последнего входа"""
        async with self.db.get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                user.updated_at = datetime.now(timezone.utc)
                await session.commit()


    async def update_user_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """Обновление пароля пользователя"""
        async with self.db.get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            user.password_hash = get_password_hash(new_password)
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return True

    async def get_user_by_id(
        self,
        user_id: int,
        session: Optional[AsyncSession] = None
    ) -> Optional[User]:
        """Получение пользователя по ID"""
        if session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        
        async with self.db.get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        
