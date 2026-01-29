from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
from sqlalchemy import func, and_, select, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.activitywatch.database.db_manager import DatabaseManager
from src.activitywatch.database.models import (
    ActivityEvent, 
    Device, 
    User,
    DevicePlatform
)
if TYPE_CHECKING:
    from . import CommonCRUD



class StatisticsCRUD:
    db: DatabaseManager
    
    def __init__(self, db: DatabaseManager, common_crud: "CommonCRUD") -> None:
        self.db = db
        self.common = common_crud
    
    async def get_user_daily_stats(
        self, 
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Статистика по дням для пользователя"""
        async with self.db.get_session() as session:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # Используем подзапрос для обхода проблемы GROUP BY
            subquery = select(
                ActivityEvent.timestamp,
                ActivityEvent.duration_seconds,
                ActivityEvent.app,
                Device.platform,
                Device.user_id
            ).join(
                Device, ActivityEvent.device_id == Device.id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= start_date,
                    ActivityEvent.timestamp <= end_date
                )
            ).subquery()
            
            stmt = select(
                func.date_trunc('day', subquery.c.timestamp).label('date'),
                subquery.c.platform,
                func.sum(subquery.c.duration_seconds).label('total_seconds'),
                func.count().label('event_count')
            ).group_by(
                func.date_trunc('day', subquery.c.timestamp),
                subquery.c.platform
            ).order_by(
                func.date_trunc('day', subquery.c.timestamp).desc()
            )
            
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            # Форматируем результат
            stats_by_day = {}
            for date, platform, total_seconds, event_count in rows:
                date_str = date.strftime('%Y-%m-%d')
                if date_str not in stats_by_day:
                    stats_by_day[date_str] = {
                        'date': date_str,
                        'total_hours': 0,
                        'by_platform': {},
                        'events_count': 0
                    }
                
                hours = total_seconds / 3600 if total_seconds else 0
                stats_by_day[date_str]['total_hours'] += hours
                stats_by_day[date_str]['events_count'] += event_count
                stats_by_day[date_str]['by_platform'][platform.value] = hours
            
            return list(stats_by_day.values())
    
    async def get_platform_distribution(
        self, 
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Распределение по платформам"""
        async with self.db.get_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Суммарное время по платформам
            stmt = select(
                Device.platform,
                func.sum(ActivityEvent.duration_seconds).label('total_seconds')
            ).join(
                Device, ActivityEvent.device_id == Device.id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff
                )
            ).group_by(Device.platform)
            
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            total_seconds = sum(row[1] or 0 for row in rows)
            
            distribution = []
            for platform, seconds in rows:
                if seconds:
                    percentage = (seconds / total_seconds * 100) if total_seconds > 0 else 0
                    distribution.append({
                        'platform': platform.value,
                        'hours': round(seconds / 3600, 1),
                        'percentage': round(percentage, 1),
                        'color': self._get_platform_color(platform.value)
                    })
            
            return {
                'distribution': sorted(distribution, key=lambda x: x['percentage'], reverse=True),
                'total_hours': round(total_seconds / 3600, 1),
                'period_days': days
            }
    
    async def get_top_apps(
        self, 
        user_id: int,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Топ приложений за период"""
        async with self.db.get_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            stmt = select(
                ActivityEvent.app,
                Device.platform,
                func.sum(ActivityEvent.duration_seconds).label('total_seconds'),
                func.count(ActivityEvent.id).label('event_count')
            ).join(
                Device, ActivityEvent.device_id == Device.id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff
                )
            ).group_by(ActivityEvent.app, Device.platform)
            
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            # Агрегируем по приложениям (суммируем время на всех платформах)
            app_stats = {}
            for app, platform, seconds, count in rows:
                if not seconds:
                    continue
                    
                if app not in app_stats:
                    app_stats[app] = {
                        'app': app,
                        'total_seconds': 0,
                        'platforms': set(),
                        'event_count': 0
                    }
                
                app_stats[app]['total_seconds'] += seconds
                app_stats[app]['platforms'].add(platform.value)
                app_stats[app]['event_count'] += count
            
            # Сортируем и форматируем
            sorted_apps = sorted(
                app_stats.values(), 
                key=lambda x: x['total_seconds'], 
                reverse=True
            )[:limit]
            
            top_apps = []
            total_seconds_all = sum(app['total_seconds'] for app in sorted_apps) if sorted_apps else 1
            
            for i, app in enumerate(sorted_apps):
                hours = app['total_seconds'] / 3600
                percentage = (app['total_seconds'] / total_seconds_all * 100) if total_seconds_all > 0 else 0
                
                top_apps.append({
                    'id': i + 1,
                    'name': self._format_app_name(app['app']),
                    'original_name': app['app'],
                    'category': self._detect_category(app['app']),
                    'platforms': list(app['platforms']),
                    'time_hours': round(hours, 1),
                    'time_formatted': self._format_hours(hours),
                    'percentage': round(percentage, 1),
                    'event_count': app['event_count']
                })
            
            return top_apps
    
    async def get_overview_stats(
        self, 
        user_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Общая статистика для карточек"""
        async with self.db.get_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Общее время
            stmt_total = select(
                func.sum(ActivityEvent.duration_seconds).label('total_seconds'),
                func.count(ActivityEvent.id).label('event_count')
            ).join(
                Device, ActivityEvent.device_id == Device.id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff
                )
            )
            
            result_total = await session.execute(stmt_total)
            total_row = result_total.fetchone()
            total_seconds = total_row[0] if total_row and total_row[0] else 0
            event_count = total_row[1] if total_row else 0
            
            # Среднее в день - исправленный запрос
            # Создаем подзапрос с вычисленным днем
            subquery = select(
                ActivityEvent.timestamp,
                ActivityEvent.duration_seconds,
                Device.user_id,
                func.date_trunc('day', ActivityEvent.timestamp).label('day_group')
            ).join(
                Device, ActivityEvent.device_id == Device.id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff
                )
            ).subquery()
            
            stmt_daily = select(
                subquery.c.day_group.label('date'),
                func.sum(subquery.c.duration_seconds).label('daily_seconds')
            ).group_by(subquery.c.day_group)
            
            result_daily = await session.execute(stmt_daily)
            daily_rows = result_daily.fetchall()
            daily_seconds_list = [row[1] for row in daily_rows if row[1]]
            
            avg_daily_seconds = sum(daily_seconds_list) / len(daily_seconds_list) if daily_seconds_list else 0
            
            # Активные устройства
            stmt_devices = select(
                func.count(func.distinct(Device.id))
            ).join(
                ActivityEvent, Device.id == ActivityEvent.device_id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff,
                    Device.is_active == True
                )
            )
            
            result_devices = await session.execute(stmt_devices)
            active_devices = result_devices.scalar() or 0
            
            # Продуктивное время (упрощённо: всё кроме развлекательных приложений)
            productive_keywords = ['code', 'vscode', 'pycharm', 'terminal', 'git', 'github', 'jupyter', 'docs', 'notion']
            
            stmt_productive = select(
                func.sum(ActivityEvent.duration_seconds)
            ).join(
                Device, ActivityEvent.device_id == Device.id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff,
                    func.lower(ActivityEvent.app).in_([kw.lower() for kw in productive_keywords])
                )
            )
            
            result_productive = await session.execute(stmt_productive)
            productive_seconds = result_productive.scalar() or 0
            
            return {
                'total_time': self._format_hours(total_seconds / 3600),
                'total_seconds': total_seconds,
                'average_daily': self._format_hours(avg_daily_seconds / 3600),
                'active_devices': active_devices,
                'productive_time': self._format_hours(productive_seconds / 3600),
                'productive_percentage': round((productive_seconds / total_seconds * 100) if total_seconds > 0 else 0, 1),
                'event_count': event_count,
                'days_analyzed': len(daily_seconds_list)
            }
    
    async def get_daily_activity_chart(
        self, 
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Данные для графика по дням недели"""
        async with self.db.get_session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Используем подзапрос
            subquery = select(
                ActivityEvent.timestamp,
                ActivityEvent.duration_seconds,
                Device.user_id,
                func.date_trunc('day', ActivityEvent.timestamp).label('day_group')
            ).join(
                Device, ActivityEvent.device_id == Device.id
            ).where(
                and_(
                    Device.user_id == user_id,
                    ActivityEvent.timestamp >= cutoff
                )
            ).subquery()
            
            # Группируем по вычисленному дню
            stmt = select(
                subquery.c.day_group.label('date'),
                func.sum(subquery.c.duration_seconds).label('total_seconds')
            ).group_by(subquery.c.day_group)
            
            result = await session.execute(stmt)
            rows = result.fetchall()
            
            # Преобразуем в удобный формат для графика
            chart_data = []
            max_hours = max((row[1] or 0) / 3600 for row in rows) if rows else 1
            
            # Дни недели на русском
            weekdays_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            
            for date, seconds in rows:
                if seconds:
                    hours = seconds / 3600
                    # Процент от максимального значения для высоты столбца
                    percentage = (hours / max_hours * 100) if max_hours > 0 else 0
                    
                    # Определяем день недели
                    weekday_num = date.weekday()
                    weekday_label = weekdays_ru[weekday_num]
                    
                    chart_data.append({
                        'label': weekday_label,
                        'date': date.strftime('%Y-%m-%d'),
                        'hours': round(hours, 1),
                        'percentage': round(percentage, 2),
                        'value': round(percentage, 1)  # для совместимости с фронтендом
                    })
            
            # Сортируем по дате
            chart_data.sort(key=lambda x: x['date'])
            
            # Если данных мало, добавляем недостающие дни
            if len(chart_data) < 7:
                for i in range(7):
                    date = (datetime.now(timezone.utc) - timedelta(days=i)).date()
                    date_str = date.strftime('%Y-%m-%d')
                    if not any(d['date'] == date_str for d in chart_data):
                        weekday_num = date.weekday()
                        weekday_label = weekdays_ru[weekday_num]
                        chart_data.append({
                            'label': weekday_label,
                            'date': date_str,
                            'hours': 0,
                            'percentage': 0,
                            'value': 0
                        })
            
            return sorted(chart_data, key=lambda x: x['date'])
    
    # Вспомогательные методы
    def _get_platform_color(self, platform: str) -> str:
        """Цвет для платформы"""
        colors = {
            'windows': '#0078d4',
            'linux': '#ff9900',
            'macos': '#555555',
            'android': '#3ddc84',
            'ios': '#000000'
        }
        return colors.get(platform.lower(), '#64748b')
    
    def _format_app_name(self, app_name: str) -> str:
        """Форматирование названия приложения"""
        # Убираем package names для Android
        if '.' in app_name and not any(x in app_name.lower() for x in ['chrome', 'firefox']):
            # Для Android: com.whatsapp -> WhatsApp
            parts = app_name.split('.')
            if len(parts) > 1:
                last_part = parts[-1]
                if last_part == 'android':
                    last_part = parts[-2] if len(parts) > 2 else parts[-1]
                return last_part.title()
        return app_name
    
    def _detect_category(self, app_name: str) -> str:
        """Определение категории приложения"""
        app_lower = app_name.lower()
        
        categories = {
            'development': ['vscode', 'code', 'pycharm', 'intellij', 'terminal', 'git', 'github', 'gitlab'],
            'browser': ['chrome', 'firefox', 'safari', 'edge', 'brave'],
            'communication': ['whatsapp', 'telegram', 'discord', 'slack', 'zoom', 'teams'],
            'social': ['instagram', 'facebook', 'twitter', 'tiktok', 'reddit'],
            'entertainment': ['youtube', 'netflix', 'spotify', 'twitch', 'steam'],
            'productivity': ['notion', 'trello', 'asana', 'calendar', 'notes'],
            'design': ['figma', 'photoshop', 'illustrator', 'sketch']
        }
        
        for category, keywords in categories.items():
            if any(keyword in app_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def _format_hours(self, hours: float) -> str:
        """Форматирование времени"""
        if hours <= 0:
            return "0ч"
            
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes}м"
        
        whole_hours = int(hours)
        minutes = int((hours - whole_hours) * 60)
        
        if minutes == 0:
            return f"{whole_hours}ч"
        else:
            return f"{whole_hours}ч {minutes}м"