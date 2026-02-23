import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

from src.activitywatch.core.security import get_current_user
from src.activitywatch.database.db_manager import DatabaseManager
from src.activitywatch.loader import db
from aiocache import cached
from aiocache.serializers import JsonSerializer
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import Query, HTTPException
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) 


router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/overview")
async def get_overview_statistics(
    days: int = Query(7, description="Количество дней для анализа"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Получить общую статистику (для карточек)"""
    try:
        user_id = current_user["id"]
        overview = await db.statistics.get_overview_stats(user_id, days)

        # Форматируем для фронтенда
        stats_cards = [
            {
                "id": "total",
                "label": "Общее время",
                "value": overview["total_time"],
                "trend": 0,  # Пока без трендов
                "color": "blue",
                "icon": "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
            },
            {
                "id": "average",
                "label": "Среднее в день",
                "value": overview["average_daily"],
                "trend": 0,
                "color": "purple",
                "icon": "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
            },
            {
                "id": "productive",
                "label": "Продуктивное время",
                "value": overview["productive_time"],
                "trend": 0,
                "color": "green",
                "icon": "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
            },
            {
                "id": "devices",
                "label": "Активных устройств",
                "value": str(overview["active_devices"]),
                "trend": 0,
                "color": "orange",
                "icon": "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z",
            },
        ]

        return {"success": True, "stats_cards": stats_cards, "details": overview}

    except Exception as e:
        logger.error(f"Error getting overview statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-chart")
async def get_daily_chart_data(
    days: int = Query(7, description="Количество дней для графика"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Данные для графика по дням"""
    try:
        user_id = current_user["id"]
        chart_data = await db.statistics.get_daily_activity_chart(user_id, days)

        return {"success": True, "chart_data": chart_data, "max_days": days}

    except Exception as e:
        logger.error(f"Error getting daily chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platform-distribution")
async def get_platform_distribution(
    days: int = Query(30, description="Количество дней для анализа"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Распределение времени по платформам"""
    try:
        user_id = current_user["id"]
        distribution = await db.statistics.get_platform_distribution(user_id, days)

        # Форматируем для фронтенда
        device_data = []
        for i, item in enumerate(distribution["distribution"]):
            device_data.append(
                {
                    "id": i + 1,
                    "name": item["platform"].upper(),
                    "percentage": item["percentage"],
                    "color": item["color"],
                    "hours": item["hours"],
                }
            )

        return {
            "success": True,
            "device_data": device_data,
            "total_hours": distribution["total_hours"],
            "period_days": distribution["period_days"],
        }

    except Exception as e:
        logger.error(f"Error getting platform distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-apps")
async def get_top_applications(
    limit: int = Query(10, description="Количество приложений в топе"),
    days: int = Query(7, description="Количество дней для анализа"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Топ приложений по времени использования"""
    try:
        user_id = current_user["id"]
        top_apps = await db.statistics.get_top_apps(user_id, limit, days)

        # Форматируем для фронтенда
        formatted_apps = []
        for app in top_apps:
            formatted_apps.append(
                {
                    "id": app["id"],
                    "name": app["name"],
                    "original_name": app["original_name"],
                    "category": app["category"],
                    "time": app["time_formatted"],
                    "time_hours": app["time_hours"],
                    "percentage": app["percentage"],
                    "platforms": app["platforms"],
                }
            )

        return {
            "success": True,
            "top_apps": formatted_apps,
            "limit": limit,
            "days": days,
        }

    except Exception as e:
        logger.error(f"Error getting top apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detailed-daily")
async def get_detailed_daily_stats(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Подробная статистика по дням"""
    try:
        user_id = current_user["id"]

        # Парсим даты
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )

        daily_stats = await db.statistics.get_user_daily_stats(
            user_id, start_dt, end_dt
        )

        return {
            "success": True,
            "daily_stats": daily_stats,
            "period": {"start": start_date, "end": end_date},
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Error getting detailed daily stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/summary")
# @cached(
#     ttl=300,
#     serializer=JsonSerializer(),
#     key_builder=lambda f, *a, **kw: f"summary_{kw['current_user']['id']}_{kw['period']}",
# )
async def get_complete_summary(
    period: str = Query("week", description="Период: week, month, quarter, year"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    
    overall_start = time.time()
    user_id = current_user["id"]
    logger.info(f"Начало формирования сводки для пользователя {user_id}, период={period}")

    days_map = {"week": 7, "month": 30, "quarter": 90, "year": 365}
    days = days_map.get(period.lower(), 7)

    try:
        # Вспомогательная функция для замера времени выполнения корутины
        async def timed_task(coro, task_name: str):
            task_start = time.time()
            logger.debug(f"Задача '{task_name}' стартовала")
            try:
                result = await coro
                elapsed = time.time() - task_start
                logger.info(f"Задача '{task_name}' завершена за {elapsed:.3f} с")
                return result
            except Exception as e:
                elapsed = time.time() - task_start
                logger.error(f"Задача '{task_name}' упала через {elapsed:.3f} с: {e}")
                raise

        # Собираем задачи без изменения существующих вызовов (сессии создаются внутри методов)
        tasks = [
            timed_task(db.statistics.get_overview_stats(user_id, days), "overview_stats"),
            timed_task(db.statistics.get_daily_activity_chart(user_id, days), "daily_activity_chart"),
            timed_task(db.statistics.get_platform_distribution(user_id, days), "platform_distribution"),
            timed_task(db.statistics.get_top_apps(user_id, 5, days), "top_apps"),
            timed_task(db.statistics.get_trends(user_id, period), "trends"),
            timed_task(db.statistics.get_category_distribution(user_id, days), "category_distribution"),
            timed_task(db.statistics.get_hourly_activity(user_id, days), "hourly_activity"),
        ]

        # Параллельный запуск
        results = await asyncio.gather(*tasks)
        (
            overview,
            chart_data,
            platform_dist,
            top_apps,
            trends,
            categories,
            heatmap,
        ) = results

        total_elapsed = time.time() - overall_start
        logger.info(f"Полная сводка сформирована за {total_elapsed:.3f} с")
        print(results)
        return {
            "success": True,
            "period": period,
            "days": days,
            "overview": overview,
            "chart_data": chart_data,
            "platform_distribution": platform_dist.get("distribution", []),
            "top_apps": top_apps,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "trends": trends,
            "categories": categories,
            "heatmap": heatmap,
        }

    except Exception as e:
        total_elapsed = time.time() - overall_start
        logger.error(f"Ошибка при формировании сводки (прошло {total_elapsed:.3f} с): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hourly-heatmap")
async def get_hourly_heatmap(
    days: int = Query(7, description="Количество дней для анализа"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Почасовая активность для тепловой карты"""
    try:
        user_id = current_user["id"]
        # Метод в db.statistics, который вернёт матрицу 7x24
        heatmap = await db.statistics.get_hourly_activity(user_id, days)
        return {"success": True, "heatmap": heatmap}
    except Exception as e:
        logger.error(f"Error getting hourly heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category-distribution")
async def get_category_distribution(
    days: int = Query(7, description="Количество дней"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Распределение времени по категориям (продуктивность, развлечения и т.д.)"""
    try:
        user_id = current_user["id"]
        categories = await db.statistics.get_category_distribution(user_id, days)
        return {"success": True, "categories": categories}
    except Exception as e:
        logger.error(f"Error getting category distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_trends(
    period: str = Query("week", description="week, month"),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Сравнение текущего периода с предыдущим (тренды)"""
    try:
        user_id = current_user["id"]
        trends = await db.statistics.get_trends(user_id, period)
        return {"success": True, "trends": trends}
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-breakdown/{date}")
async def get_daily_breakdown(
    date: str, current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Активности за конкретный день (для детального просмотра)"""
    try:
        user_id = current_user["id"]
        day_date = datetime.strptime(date, "%Y-%m-%d").date()
        activities = await db.statistics.get_daily_activities(user_id, day_date)
        return {"success": True, "date": date, "activities": activities}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        logger.error(f"Error getting daily breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))
