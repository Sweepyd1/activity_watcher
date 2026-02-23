# activitywatch/database/crud/users.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import select, text
from sqlalchemy import or_
from sqlalchemy.orm import noload
from src.activitywatch.database.models import Device, DevicePlatform

from src.activitywatch.database.db_manager import DatabaseManager

if TYPE_CHECKING:
    from . import CommonCRUD


class DevicesCRUD:
    db: DatabaseManager

    def __init__(self, db: DatabaseManager, common_crud: CommonCRUD) -> None:
        self.db = db
        self.common = common_crud

    async def new_device(
        self,
        user_id: int,
        device_name: str,
        platform: DevicePlatform = DevicePlatform.OTHER,
        platform_version: str = None,
    ) -> Device:
        """Создать новое устройство (без реального device_id)"""
        async with self.db.get_session() as session:
            device = Device(
                user_id=user_id,
                device_name=device_name,
                platform=platform,
                platform_version=platform_version,
                device_id=None,
                is_active=True,
                sync_enabled=True,
                meta_data={},
            )
            session.add(device)
            await session.commit()
            await session.refresh(device)
            return device

    async def get_user_devices(self, user_id: int) -> List[Device]:
        async with self.db.get_session() as session:
            stmt = select(Device).where(Device.user_id == user_id).options(
                noload(Device.user),
                noload(Device.tokens),
                noload(Device.sync_sessions),
                noload(Device.activity_events)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_device_by_id(
        self, device_id: int, user_id: int = None
    ) -> Optional[Device]:
        """Получить устройство по ID с опциональной проверкой владельца"""
        async with self.db.get_session() as session:
            stmt = select(Device).where(Device.id == device_id)
            if user_id:
                stmt = stmt.where(Device.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def update_device_registration(
        self,
        device_id: int,
        real_device_id: str,
        device_name: str,
        system: str,
        hostname: str,
        platform_version: Optional[str] = None,
        client_version: Optional[str] = None,

    ) -> Device:
        async with self.db.get_session() as session:
            stmt = select(Device).where(Device.id == device_id)
            result = await session.execute(stmt)
            device = result.scalar_one()

            # ✅ ЗАПОЛНЯЕМ ВСЕ ПОЛЯ
            device.device_id = real_device_id
            device.system = system
            device.hostname = hostname
            device.platform_version = platform_version or device.platform_version
            device.client_version = client_version
            device.platform_name = device_name  # дублируем для совместимости
            
            # Meta data
            device.meta_data.update({
           
                "registered_at": datetime.now(timezone.utc).isoformat(),
            })

            device.last_seen = datetime.now(timezone.utc)
            device.is_active = True

            await session.commit()
            await session.refresh(device)
            return device

    async def delete_device(self, device_id: int, user_id: int) -> bool:
        """Удалить устройство пользователя"""
        async with self.db.get_session() as session:
            # Находим устройство пользователя
            stmt = select(Device).where(
                Device.id == device_id, Device.user_id == user_id
            )
            result = await session.execute(stmt)
            device = result.scalar_one_or_none()

            if not device:
                return False

            await session.delete(device)
            await session.commit()
            return True

    async def update_device_last_seen(self, device_id: int) -> Optional[Device]:
        """Обновить время последней активности устройства"""
        async with self.db.get_session() as session:
            stmt = select(Device).where(Device.id == device_id)
            result = await session.execute(stmt)
            device = result.scalar_one_or_none()

            if device:
                device.last_seen = datetime.now(timezone.utc)
                device.is_active = True
                await session.commit()
                await session.refresh(device)

            return device
    async def find_device_by_identifier(self, device_identifier: str) -> Optional[Device]:
        """Ищет устройство по device_id (строка!)"""
        async with self.db.get_session() as session:
            stmt = select(Device).where(
                Device.device_id == device_identifier  # ← Строка!
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

