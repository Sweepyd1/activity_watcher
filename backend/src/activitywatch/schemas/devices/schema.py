from datetime import datetime

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


from src.activitywatch.database.models import DevicePlatform, TokenPermission


class CreateDeviceRequest(BaseModel):
    device_name: str


class CreateTokenRequest(BaseModel):
    device_id: int
    token_name: str = "Основной токен"



class RegisterDeviceRequest(BaseModel):
    token: str
    device_id: str
    system: str
    hostname: str
    device_name: Optional[str] = None
    platform_version: Optional[str] = None
    client_version: Optional[str] = None



class DeviceResponse(BaseModel):
    id: int
    device_name: str
    device_id: Optional[str] = None  # Может быть None
    platform: DevicePlatform
    platform_version: Optional[str] = None
    client_version: Optional[str] = None  # Добавьте если есть
    is_active: bool
    sync_enabled: bool  # Добавьте если нужно
    last_seen: Optional[datetime] = None  # Может быть None
    first_seen: datetime
    # created_at: datetime  # УДАЛИТЕ - в Device нет этого поля

    # Добавьте конфигурацию для работы с ORM объектами
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    id: int
    token: str  # Только при создании!
    name: str
    device_id: int
    created_at: datetime

