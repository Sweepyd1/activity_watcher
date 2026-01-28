# 📁 src/activitywatch/cruds/sync_crud.py
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, desc

from src.activitywatch.database.models import SyncSession, SyncStatus
from src.activitywatch.database.db_manager import DatabaseManager

if TYPE_CHECKING:
    from . import CommonCRUD


class SyncSessionsCRUD:
    """CRUD для сессий синхронизации"""
    db: DatabaseManager
    
    def __init__(self, db: DatabaseManager, common_crud: "CommonCRUD"):
        self.db = db
        self.common = common_crud

    async def create_sync_session(
        self,
        device_id: int,
        token_id: Optional[int] = None,
        status: SyncStatus = SyncStatus.PENDING
    ) -> SyncSession:
        """Создать новую сессию синхронизации"""
        async with self.db.get_session() as session:        
            sync_session = SyncSession(
                device_id=device_id,
                token_id=token_id,
                start_time=datetime.now(timezone.utc),
                status=status,
                meta_data={"source": "activitywatch"}
            )
            
            session.add(sync_session)
            await session.commit()
            await session.refresh(sync_session)
            
            return sync_session
        
    # async def complete_sync_session(
    #     self,
    #     sync_session_id: int,
    #     events_count: int,
    #     status: SyncStatus = SyncStatus.SUCCESS,
    #     error_message: Optional[str] = None
    # ) -> SyncSession:
    #     """Завершить сессию синхронизации"""
    #     async with self.db.get_session() as session:
            
    #         sync_session = await self.common.get_by_id(session, sync_session_id)
    #         if not sync_session:
    #             raise ValueError(f"Sync session {sync_session_id} not found")
            
    #         sync_session.end_time = datetime.now(timezone.utc)
    #         sync_session.events_count = events_count
    #         sync_session.status = status
    #         sync_session.error_message = error_message
            
    #         await session.commit()
    #         await session.refresh(sync_session)
            
    #         return sync_session
    
    async def get_device_sessions(
        self,
        device_id: int,
        limit: int = 50
    ) -> List[SyncSession]:
        """Получить сессии синхронизации устройства"""
        async with self.db.get_session() as session:
            stmt = select(SyncSession).where(
                SyncSession.device_id == device_id
            ).order_by(desc(SyncSession.start_time)).limit(limit)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_active_sync_session(
        self,
        device_id: int
    ) -> Optional[SyncSession]:
        """Получить активную (незавершенную) сессию синхронизации"""
        async with self.db.get_session() as session:
            stmt = select(SyncSession).where(
                and_(
                    SyncSession.device_id == device_id,
                    SyncSession.end_time.is_(None),
                    SyncSession.status.in_([SyncStatus.PENDING, SyncStatus.IN_PROGRESS])
                )
            ).order_by(desc(SyncSession.start_time))
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()