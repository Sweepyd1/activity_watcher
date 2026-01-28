from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid
from sqlalchemy import select


from src.activitywatch.database.models import ApiToken

from src.activitywatch.database.db_manager import DatabaseManager

if TYPE_CHECKING:
    from . import CommonCRUD


class ApiTokensCRUD:
    db: DatabaseManager

    def __init__(self, db: DatabaseManager, common_crud: CommonCRUD) -> None:
        self.db = db
        self.common = common_crud

    async def create_token(
        self,
        user_id: int,
        device_id: int,
        token_name: str = "Основной токен",

    ) -> Dict[str, Any]:
        """Создать новый токен для устройства"""


        raw_token = f"tt_{uuid.uuid4().hex}"
        token_hash = self._hash_token(raw_token)

        async with self.db.get_session() as session:
            token = ApiToken(
                user_id=user_id,
                device_id=device_id,
                token_hash=token_hash,
                name=token_name,
            )
            session.add(token)
            await session.commit()
            await session.refresh(token)

            return {
                "id": token.id,
                "token": raw_token,  
                "name": token.name,
                "device_id": token.device_id,
                "created_at": token.created_at,

            }

    async def validate_token(self, token: str) -> Optional[ApiToken]:
        """Валидировать токен и вернуть информацию о нем"""
        token_hash = self._hash_token(token)

        async with self.db.get_session() as session:
            stmt = select(ApiToken).where(
                ApiToken.token_hash == token_hash
            )
            result = await session.execute(stmt)
            api_token = result.scalar_one_or_none()

            if not api_token:
                return None

            return api_token

    async def get_device_tokens(self, device_id: int, user_id: int) -> List[ApiToken]:
        """Получить все токены устройства"""
        async with self.db.get_session() as session:
            stmt = (
                select(ApiToken)
                .where(ApiToken.device_id == device_id, ApiToken.user_id == user_id)
                .order_by(ApiToken.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def revoke_token(self, token_id: int, user_id: int) -> bool:
        """Отозвать токен"""
        async with self.db.get_session() as session:
            stmt = select(ApiToken).where(
                ApiToken.id == token_id, ApiToken.user_id == user_id
            )
            result = await session.execute(stmt)
            token = result.scalar_one_or_none()

        

            return False

    def _hash_token(self, token: str) -> str:
        """Хэширование токена (используйте bcrypt в production!)"""
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()
