# 📁 src/activitywatch/api/router.py (обновленная версия)
import json
from datetime import datetime, date, timezone
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.activitywatch.database.models import SyncStatus, Device
from src.activitywatch.loader import db

router = APIRouter(prefix="/tracker", tags=["отслеживание активностей"])

@router.post("/receive_incremental")
async def receive_incremental(
    request: Request,
):

    try:
        data = await request.json()
        print(f"📥 Получены инкрементальные данные: {len(data.get('events', []))} событий")
        
        device_info = data.get("device_info", {})
        device_identifier = device_info.get("device_id") or device_info.get("hostname")
        
        if not device_identifier:
            raise HTTPException(
                status_code=400, 
                detail="Device identifier not found in request"
            )
        
        # Находим устройство в БД
        device = await db.devices.find_device_by_identifier(device_identifier)
        if not device:
            print(f"⚠️  Устройство не найдено: {device_identifier}")
            return {
                "status": "error",
                "message": f"Device {device_identifier} not registered"
            }
        
        print(f"✅ Найдено устройство: {device.device_name} (ID: {device.id})")
        

        sync_session = await db.sync.create_sync_session(
            device_id=device.id,
            status=SyncStatus.IN_PROGRESS
        )
        
        print(f"📊 Создана сессия синхронизации: {sync_session.id}")
        
        # Сохраняем события
        events_data = data.get("events", [])
        events = await db.activity.create_events_batch(
            
            device_id=device.id,
            sync_session_id=sync_session.id,
            events_data=events_data
        )
        
        print(f"💾 Сохранено событий: {len(events)}")
        
        # Завершаем сессию
        # await db.sync.complete_sync_session(

        #     sync_session_id=sync_session.id,
        #     events_count=len(events),
        #     status=SyncStatus.SUCCESS
        # )
        
        # Обновляем время последней активности устройства
        device.last_seen = datetime.now(timezone.utc)
      
        
        
        
        return {
            "status": "success",
            "message": f"Saved {len(events)} events",
            "device_id": device.id,
            "sync_session_id": sync_session.id,
            "events_count": len(events)
        }
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении данных: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/receive_daily_summary")
async def receive_daily_summary(
    request: Request,
):

    try:
        data = await request.json()
        print(f"📥 Получены инкрементальные данные: {len(data.get('events', []))} событий")
        
        device_info = data.get("device_info", {})
        device_identifier = device_info.get("device_id") or device_info.get("hostname")
        
        if not device_identifier:
            raise HTTPException(
                status_code=400, 
                detail="Device identifier not found in request"
            )
        
        # Находим устройство в БД
        device = await db.devices.find_device_by_identifier(device_identifier)
        if not device:
            print(f"⚠️  Устройство не найдено: {device_identifier}")
            return {
                "status": "error",
                "message": f"Device {device_identifier} not registered"
            }
        
        print(f"✅ Найдено устройство: {device.device_name} (ID: {device.id})")
        

        sync_session = await db.sync.create_sync_session(
            device_id=device.id,
            status=SyncStatus.IN_PROGRESS
        )
        
        print(f"📊 Создана сессия синхронизации: {sync_session.id}")
        
        # Сохраняем события
        events_data = data.get("events", [])
        events = await db.activity.create_events_batch(
            
            device_id=device.id,
            sync_session_id=sync_session.id,
            events_data=events_data
        )
        
        print(f"💾 Сохранено событий: {len(events)}")
        
        # Завершаем сессию
        # await db.sync.complete_sync_session(

        #     sync_session_id=sync_session.id,
        #     events_count=len(events),
        #     status=SyncStatus.SUCCESS
        # )
        
        # Обновляем время последней активности устройства
        device.last_seen = datetime.now(timezone.utc)
      
        
        
        
        return {
            "status": "success",
            "message": f"Saved {len(events)} events",
            "device_id": device.id,
            "sync_session_id": sync_session.id,
            "events_count": len(events)
        }
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении данных: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
