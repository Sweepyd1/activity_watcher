# src/activitywatch/database/crud/statistics.py

from datetime import datetime, timedelta, timezone
import os
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import array_agg

from src.activitywatch.database.db_manager import DatabaseManager
from src.activitywatch.database.models import ActivityEvent, Device

if TYPE_CHECKING:
    from . import CommonCRUD


class StatisticsCRUD:
    db: DatabaseManager

    def __init__(self, db: DatabaseManager, common_crud: "CommonCRUD") -> None:
        self.db = db
        self.common = common_crud

    
    async def get_overview_stats(
        self,
        user_id: int,
        days: int = 7,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        if session is None:
            async with self.db.get_session() as session:
                return await self._get_overview_stats(session, user_id, days)
        return await self._get_overview_stats(session, user_id, days)

    async def get_daily_activity_chart(
        self,
        user_id: int,
        days: int = 7,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        if session is None:
            async with self.db.get_session() as session:
                return await self._get_daily_activity_chart(session, user_id, days)
        return await self._get_daily_activity_chart(session, user_id, days)

    async def get_platform_distribution(
        self,
        user_id: int,
        days: int = 30,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        if session is None:
            async with self.db.get_session() as session:
                return await self._get_platform_distribution(session, user_id, days)
        return await self._get_platform_distribution(session, user_id, days)

    async def get_top_apps(
        self,
        user_id: int,
        limit: int = 10,
        days: int = 7,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        if session is None:
            async with self.db.get_session() as session:
                return await self._get_top_apps(session, user_id, limit, days)
        return await self._get_top_apps(session, user_id, limit, days)

    async def get_hourly_activity(
        self,
        user_id: int,
        days: int = 7,
        session: Optional[AsyncSession] = None,
    ) -> List[List[int]]:
        if session is None:
            async with self.db.get_session() as session:
                return await self._get_hourly_activity(session, user_id, days)
        return await self._get_hourly_activity(session, user_id, days)

    async def get_category_distribution(
        self,
        user_id: int,
        days: int = 7,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        if session is None:
            async with self.db.get_session() as session:
                return await self._get_category_distribution(session, user_id, days)
        return await self._get_category_distribution(session, user_id, days)

    async def get_trends(
        self,
        user_id: int,
        period: str = "week",
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        if session is None:
            async with self.db.get_session() as session:
                return await self._get_trends(session, user_id, period)
        return await self._get_trends(session, user_id, period)

    # ---------- Приватные реализации ----------
    async def _get_overview_stats(
        self, session: AsyncSession, user_id: int, days: int
    ) -> Dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        productive_keywords = [
            "code",
            "vscode",
            "pycharm",
            "intellij",
            "terminal",
            "git",
            "github",
            "jupyter",
            "docs",
            "notion",
        ]

        # 1. Подзапрос для суммы по дням (используется для вычисления среднего)
        daily_subq = (
            select(func.sum(ActivityEvent.duration_seconds).label("daily_total"))
            .join(Device, ActivityEvent.device_id == Device.id)
            .where(and_(Device.user_id == user_id, ActivityEvent.timestamp >= cutoff))
            .group_by(func.date_trunc("day", ActivityEvent.timestamp))
            .subquery()
        )

        # 2. Среднее значение по дням на основе предыдущего подзапроса
        daily_avg_subq = select(func.avg(daily_subq.c.daily_total)).scalar_subquery()

        # 3. Подзапрос количества активных устройств
        active_devices_subq = (
            select(func.count(func.distinct(Device.id)))
            .where(
                Device.user_id == user_id,
                Device.is_active == True,
                Device.id.in_(
                    select(ActivityEvent.device_id).where(
                        ActivityEvent.timestamp >= cutoff
                    )
                ),
            )
            .scalar_subquery()
            .label("active_devices")
        )

        # 4. Подзапрос продуктивного времени
        productive_subq = (
            select(func.coalesce(func.sum(ActivityEvent.duration_seconds), 0))
            .join(Device, ActivityEvent.device_id == Device.id)
            .where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff,
                    func.lower(ActivityEvent.app).in_(
                        [kw.lower() for kw in productive_keywords]
                    ),
                )
            )
            .scalar_subquery()
            .label("productive_seconds")
        )

        # 5. Основной запрос (итоговые показатели)
        stmt = (
            select(
                func.coalesce(func.sum(ActivityEvent.duration_seconds), 0).label(
                    "total_seconds"
                ),
                func.count(ActivityEvent.id).label("event_count"),
                func.coalesce(daily_avg_subq, 0).label("avg_daily_seconds"),
                active_devices_subq,
                productive_subq,
            )
            .select_from(ActivityEvent)
            .join(Device, ActivityEvent.device_id == Device.id)
            .where(and_(Device.user_id == user_id, ActivityEvent.timestamp >= cutoff))
        )

        result = await session.execute(stmt)
        row = result.one()

        total_seconds = row.total_seconds or 0
        avg_daily_seconds = row.avg_daily_seconds or 0
        productive_seconds = row.productive_seconds or 0

        return {
            "total_time": self._format_hours(total_seconds / 3600),
            "total_seconds": total_seconds,
            "average_daily": self._format_hours(avg_daily_seconds / 3600),
            "active_devices": row.active_devices or 0,
            "productive_time": self._format_hours(productive_seconds / 3600),
            "productive_percentage": round(
                (productive_seconds / total_seconds * 100) if total_seconds > 0 else 0,
                1,
            ),
            "event_count": row.event_count,
            "days_analyzed": days,
        }

    async def _get_daily_activity_chart(
        self, session: AsyncSession, user_id: int, days: int
    ) -> List[Dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Создаем выражение для даты и даем ему метку
        date_col = func.date_trunc("day", ActivityEvent.timestamp).label("date")

        stmt = (
            select(
                date_col,
                func.sum(ActivityEvent.duration_seconds).label("total_seconds"),
            )
            .join(Device, ActivityEvent.device_id == Device.id)
            .where(and_(Device.user_id == user_id, ActivityEvent.timestamp >= cutoff))
            .group_by(date_col)  # Используем тот же объект с меткой
            .order_by(date_col)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        if not rows:
            return []

        max_seconds = max(r.total_seconds for r in rows)
        weekdays_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

        chart_data = []
        for row in rows:
            date = row.date
            hours = row.total_seconds / 3600
            percentage = (row.total_seconds / max_seconds * 100) if max_seconds else 0
            chart_data.append(
                {
                    "label": weekdays_ru[date.weekday()],
                    "date": date.strftime("%Y-%m-%d"),
                    "hours": round(hours, 1),
                    "percentage": round(percentage, 2),
                    "value": round(percentage, 1),
                }
            )
        return chart_data

    async def _get_platform_distribution(
        self, session: AsyncSession, user_id: int, days: int
    ) -> Dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                Device.platform,
                func.coalesce(func.sum(ActivityEvent.duration_seconds), 0).label(
                    "total_seconds"
                ),
            )
            .join(ActivityEvent, Device.id == ActivityEvent.device_id)
            .where(and_(Device.user_id == user_id, ActivityEvent.timestamp >= cutoff))
            .group_by(Device.platform)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        total_seconds = sum(row.total_seconds for row in rows)
        distribution = []
        for row in rows:
            seconds = row.total_seconds
            percentage = (seconds / total_seconds * 100) if total_seconds > 0 else 0
            distribution.append(
                {
                    "platform": row.platform.value,
                    "hours": round(seconds / 3600, 1),
                    "percentage": round(percentage, 1),
                    "color": self._get_platform_color(row.platform.value),
                }
            )

        return {
            "distribution": sorted(
                distribution, key=lambda x: x["percentage"], reverse=True
            ),
            "total_hours": round(total_seconds / 3600, 1),
            "period_days": days,
        }

    async def _get_top_apps(
        self, session: AsyncSession, user_id: int, limit: int, days: int
    ) -> List[Dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                ActivityEvent.app,
                func.coalesce(func.sum(ActivityEvent.duration_seconds), 0).label(
                    "total_seconds"
                ),
                func.count(ActivityEvent.id).label("event_count"),
                array_agg(func.distinct(Device.platform)).label("platforms"),
            )
            .join(Device, ActivityEvent.device_id == Device.id)
            .where(and_(Device.user_id == user_id, ActivityEvent.timestamp >= cutoff))
            .group_by(ActivityEvent.app)
            .order_by(func.sum(ActivityEvent.duration_seconds).desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        total_seconds_all = sum(row.total_seconds for row in rows) or 1
        top_apps = []
        for i, row in enumerate(rows):
            hours = row.total_seconds / 3600
            percentage = (
                (row.total_seconds / total_seconds_all * 100)
                if total_seconds_all > 0
                else 0
            )
            top_apps.append(
                {
                    "id": i + 1,
                    "name": self._format_app_name(row.app),
                    "original_name": row.app,
                    "category": self._detect_category(row.app),
                    "platforms": list(row.platforms) if row.platforms else [],
                    "time_hours": round(hours, 1),
                    "time_formatted": self._format_hours(hours),
                    "percentage": round(percentage, 1),
                    "event_count": row.event_count,
                }
            )
        return top_apps

    async def _get_hourly_activity(
        self, session: AsyncSession, user_id: int, days: int
    ) -> List[List[int]]:
        # Используем сырой SQL для производительности
        query = text("""
            SELECT EXTRACT(DOW FROM ae.timestamp) as day_of_week,
                   EXTRACT(HOUR FROM ae.timestamp) as hour,
                   SUM(ae.duration_seconds) as total_seconds
            FROM activity_events ae
            JOIN devices d ON ae.device_id = d.id
            WHERE d.user_id = :user_id
              AND ae.timestamp >= NOW() - (:days * INTERVAL '1 day')
            GROUP BY day_of_week, hour
            ORDER BY day_of_week, hour
        """)
        result = await session.execute(query, {"user_id": user_id, "days": days})
        rows = result.fetchall()

        heatmap = [[0] * 24 for _ in range(7)]
        for row in rows:
            dow = int(row[0])  # 0-6 (воскресенье=0)
            hour = int(row[1])
            minutes = row[2] / 60  # переводим секунды в минуты
            heatmap[dow][hour] = int(minutes)
        return heatmap

    async def _get_category_distribution(
        self, session: AsyncSession, user_id: int, days: int
    ) -> List[Dict[str, Any]]:
        # Здесь нужна таблица категорий, если её нет – используем упрощённый вариант
        # В текущей схеме нет поля category в ActivityEvent, поэтому этот метод требует доработки.
        # Пока заглушка.
        return []

    async def _get_trends(
        self, session: AsyncSession, user_id: int, period: str
    ) -> Dict[str, Any]:
        days_map = {"week": 7, "month": 30}
        days = days_map.get(period, 7)
        # Получаем данные за текущий и предыдущий период
        current = await self._get_overview_stats(session, user_id, days)
        # Для предыдущего сдвигаем cutoff на days назад
        previous = await self._get_overview_stats(
            session, user_id, days
        )  # нужно реализовать

        # Упрощённо – пока пустой ответ
        return {}

    # ---------- Вспомогательные методы ----------
    def _get_platform_color(self, platform: str) -> str:
        colors = {
            "windows": "#0078d4",
            "linux": "#ff9900",
            "macos": "#555555",
            "android": "#3ddc84",
            "ios": "#000000",
        }
        return colors.get(platform.lower(), "#64748b")

    def _format_app_name(self, app_name: str) -> str:
        if not app_name:
            return "Unknown"
        base_name = os.path.basename(app_name)
        name_without_ext = os.path.splitext(base_name)[0]
        return name_without_ext if name_without_ext else base_name

    def _detect_category(self, app_name: str) -> str:
        app_lower = app_name.lower()
        categories = {
            "development": [
                "vscode",
                "code",
                "pycharm",
                "intellij",
                "terminal",
                "git",
                "github",
                "gitlab",
            ],
            "browser": ["chrome", "firefox", "safari", "edge", "brave"],
            "communication": [
                "whatsapp",
                "telegram",
                "discord",
                "slack",
                "zoom",
                "teams",
            ],
            "social": ["instagram", "facebook", "twitter", "tiktok", "reddit"],
            "entertainment": ["youtube", "netflix", "spotify", "twitch", "steam"],
            "productivity": ["notion", "trello", "asana", "calendar", "notes"],
            "design": ["figma", "photoshop", "illustrator", "sketch"],
        }
        for category, keywords in categories.items():
            if any(keyword in app_lower for keyword in keywords):
                return category
        return "other"

    def _format_hours(self, hours: float) -> str:
        if hours <= 0:
            return "0ч"
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes}м"
        whole_hours = int(hours)
        minutes = int((hours - whole_hours) * 60)
        if minutes == 0:
            return f"{whole_hours}ч"
        return f"{whole_hours}ч {minutes}м"
