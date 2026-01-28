from typing import TYPE_CHECKING, Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from sqlalchemy.orm import selectinload
import hashlib
import uuid
from src.activitywatch.database.models import ActivityEvent, Device, SyncSession
from src.activitywatch.database.db_manager import DatabaseManager
if TYPE_CHECKING:
    from . import CommonCRUD


class ActivityEventsCRUD:
    db: DatabaseManager
    
    def __init__(self, db: DatabaseManager, common_crud: "CommonCRUD"):
        self.db = db
        self.common = common_crud
        
    
    async def create_event(
        self,

        device_id: int,
        sync_session_id: Optional[int],
        event_data: Dict[str, Any]
    ) -> ActivityEvent:
        """Создание нового события активности из данных ActivityWatch"""
        async with self.db.get_session() as session:        
            # Извлекаем данные из события
            event_id = event_data.get("id") or str(uuid.uuid4())
            event_id = str(event_id)
            timestamp = event_data.get("timestamp")
            duration = event_data.get("duration", 0)
            data = event_data.get("data", {})
            
            # Преобразуем timestamp в datetime
            if isinstance(timestamp, str):
                try:
                    if timestamp.endswith('Z'):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.fromisoformat(timestamp)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            
            # Извлекаем данные приложения
            app = data.get("app", "unknown")
            window_title = data.get("title")
            url = data.get("url")
            
            # Определяем категорию
           
            
            # Проверяем дубликат
            existing = await self.get_event_by_unique(
                device_id=device_id,
                event_id=event_id,
                timestamp=timestamp
            )
            
            if existing:
                return existing
            
            # Создаем событие
            event = ActivityEvent(
                device_id=device_id,
                sync_session_id=sync_session_id,
                event_id=event_id,
                timestamp=timestamp or datetime.now(timezone.utc),
                duration_seconds=duration,
                app=app,
                window_title=window_title,
                url=url,
                data=data
            )
            
            session.add(event)
            await session.commit()
            await session.refresh(event)
            
            return event
        
    async def create_events_batch(
        self,

        device_id: int,
        sync_session_id: Optional[int],
        events_data: List[Dict[str, Any]]
    ) -> List[ActivityEvent]:
        """Создать несколько событий активности"""
        async with self.db.get_session() as session:
            events = []
            
            for event_data in events_data:
                try:
                    event = await self.create_event(device_id, sync_session_id, event_data)
                    events.append(event)
                except Exception as e:
                    # Логируем ошибку, но продолжаем обработку остальных событий
                    print(f"Error creating event: {e}")
                    continue
            
            return events
    
    async def get_event_by_unique(
        self,

        device_id: int,
        event_id: str,
        timestamp: datetime
    ) -> Optional[ActivityEvent]:
        """Найти событие по уникальному сочетанию (device_id, event_id, timestamp)"""
        async with self.db.get_session() as session:            
            stmt = select(ActivityEvent).where(
                and_(
                    ActivityEvent.device_id == device_id,
                    ActivityEvent.event_id == event_id,
                    ActivityEvent.timestamp == timestamp
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_device_events(
        self,

        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[ActivityEvent]:
        """Получить события устройства за период"""
        async with self.db.get_session() as session:        
            stmt = select(ActivityEvent).where(ActivityEvent.device_id == device_id)
            
            if start_time:
                stmt = stmt.where(ActivityEvent.timestamp >= start_time)
            if end_time:
                stmt = stmt.where(ActivityEvent.timestamp <= end_time)
            
            stmt = stmt.order_by(desc(ActivityEvent.timestamp)).limit(limit)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
        
    async def get_daily_stats(
        self,

        device_id: int,
        date: datetime
    ) -> Dict[str, Any]:
        """Получить статистику за день"""
        async with self.db.get_session() as session:        
            # Начало и конец дня
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
            
            # Общая статистика
            stmt = select(
                func.count(ActivityEvent.id).label("total_events"),
                func.sum(ActivityEvent.duration_seconds).label("total_duration"),
                func.avg(ActivityEvent.duration_seconds).label("avg_duration")
            ).where(
                and_(
                    ActivityEvent.device_id == device_id,
                    ActivityEvent.timestamp >= start_of_day,
                    ActivityEvent.timestamp <= end_of_day
                )
            )
            
            result = await session.execute(stmt)
            stats = result.fetchone()
            
            # Статистика по приложениям
            app_stmt = select(
                ActivityEvent.app,
                func.count(ActivityEvent.id).label("count"),
                func.sum(ActivityEvent.duration_seconds).label("duration")
            ).where(
                and_(
                    ActivityEvent.device_id == device_id,
                    ActivityEvent.timestamp >= start_of_day,
                    ActivityEvent.timestamp <= end_of_day
                )
            ).group_by(ActivityEvent.app).order_by(func.sum(ActivityEvent.duration_seconds).desc())
            
            app_result = await session.execute(app_stmt)
            apps_stats = [
                {"app": app, "count": count, "duration": duration}
                for app, count, duration in app_result.fetchall()
            ]
            
            # Статистика по категориям
            category_stmt = select(
                ActivityEvent.category,
                func.count(ActivityEvent.id).label("count"),
                func.sum(ActivityEvent.duration_seconds).label("duration")
            ).where(
                and_(
                    ActivityEvent.device_id == device_id,
                    ActivityEvent.timestamp >= start_of_day,
                    ActivityEvent.timestamp <= end_of_day
                )
            ).group_by(ActivityEvent.category).order_by(func.sum(ActivityEvent.duration_seconds).desc())
            
            category_result = await session.execute(category_stmt)
            categories_stats = [
                {"category": category, "count": count, "duration": duration}
                for category, count, duration in category_result.fetchall()
            ]
            
            return {
                "date": date.strftime("%Y-%m-%d"),
                "device_id": device_id,
                "total_events": stats.total_events or 0,
                "total_duration": stats.total_duration or 0,
                "avg_duration": stats.avg_duration or 0,
                "applications": apps_stats,
                "categories": categories_stats
            }
    
    async def get_recent_events(
        self,

        device_id: int,
        hours: int = 24
    ) -> List[ActivityEvent]:
        """Получить недавние события (последние N часов)"""
        async with self.db.get_session() as session:        
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            stmt = select(ActivityEvent).where(
                and_(
                    ActivityEvent.device_id == device_id,
                    ActivityEvent.timestamp >= cutoff_time
                )
            ).order_by(desc(ActivityEvent.timestamp))
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
        
       