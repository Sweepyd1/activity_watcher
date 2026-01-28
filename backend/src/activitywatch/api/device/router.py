# activitywatch/api/routers/devices.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from src.activitywatch.loader import db
from src.activitywatch.database.models import DevicePlatform, TokenPermission
from src.activitywatch.core.security import decode_access_token

router = APIRouter(prefix="/devices", tags=["devices"])


# Функция для получения текущего пользователя из куки
async def get_current_user(request: Request):
    """Получение информации о текущем пользователе через куки"""
    try:
        # Получаем токен из куки
        token = request.cookies.get("token")
        print(f"Получен токен из куки: {token[:50] if token else 'None'}...")

        if not token:
            print("Токен не найден в куках")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован"
            )

        # Декодируем токен
        payload = decode_access_token(token)
        if not payload:
            print("Не удалось декодировать токен или токен истек")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный или истекший токен",
            )

        print(f"Декодированный payload: {payload}")

        user_id = payload.get("user_id")
        token_type = payload.get("type")

        if not user_id:
            print("user_id не найден в токене")
            print(f"Токен содержит: {payload}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен: отсутствует user_id",
            )

        # Проверяем тип токена (должен быть access)
        if token_type != "access":
            print(f"Неправильный тип токена: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена"
            )

        print(f"Ищем пользователя с ID: {user_id}")

        # Получаем пользователя через db.users
        user = await db.users.get_user_by_id(user_id)

        if not user:
            print("Пользователь не найден в БД")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
            )

        print(f"Найден пользователь: {user.email}")

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "devices_count": user.devices_count
            if hasattr(user, "devices_count")
            else 0,
        }

    except HTTPException as he:
        print(f"HTTP Exception в get_current_user: {he.detail}")
        raise he
    except Exception as e:
        print(f"Ошибка в get_current_user: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при получении данных пользователя",
        )


# Pydantic модели для запросов
class CreateDeviceRequest(BaseModel):
    device_name: str
    platform: DevicePlatform = DevicePlatform.OTHER
    platform_version: str = None


class CreateTokenRequest(BaseModel):
    device_id: int
    token_name: str = "Основной токен"
    permissions: List[TokenPermission] = None
    expires_in_days: int = 30


class RegisterDeviceRequest(BaseModel):
    token: str
    device_id: str = None  # заглушка
    platform_version: str = None
    client_version: str = None


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
    expires_at: datetime = None
    permissions: List[str]


@router.post("/new", response_model=DeviceResponse)
async def create_device(
    request: CreateDeviceRequest, current_user: dict = Depends(get_current_user)
):
    """Создать новое устройство (через веб-интерфейс)"""
    device = await db.devices.new_device(
        user_id=current_user["id"],
        device_name=request.device_name,
        platform=request.platform,
        platform_version=request.platform_version,
    )
    return device


@router.get("/", response_model=List[DeviceResponse])
async def get_devices(current_user: dict = Depends(get_current_user)):
    """Получить все устройства пользователя"""
    devices = await db.devices.get_user_devices(current_user["id"])
    return devices


@router.post("/tokens", response_model=TokenResponse)
async def create_device_token(
    request: CreateTokenRequest, current_user: dict = Depends(get_current_user)
):
    """Создать токен для устройства"""
    # Проверяем, что устройство принадлежит пользователю
    device = await db.devices.get_device_by_id(
        device_id=request.device_id, user_id=current_user["id"]
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
        )

    # Создаем токен
    token_data = await db.tokens.create_token(
        user_id=current_user["id"],
        device_id=request.device_id,
        token_name=request.token_name,
        permissions=[
            p.value for p in (request.permissions or [TokenPermission.WRITE_ACTIVITY])
        ],
        expires_in_days=request.expires_in_days,
    )

    return token_data


@router.post("/register", response_model=DeviceResponse)
async def register_device(request: RegisterDeviceRequest, response: Response):
    """Регистрация устройства клиентом"""
    # Валидируем токен
    api_token = await db.tokens.validate_token(request.token)

    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен",
        )

    # Получаем устройство
    device = await db.devices.get_device_by_id(api_token.device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
        )

    # Проверяем, что устройство еще не зарегистрировано
    if device.device_id and device.device_id != request.device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Устройство уже зарегистрировано с другим ID",
        )

    # Обновляем регистрацию устройства
    updated_device = await db.devices.update_device_registration(
        device_id=device.id,
        real_device_id=request.device_id,
        platform_version=request.platform_version,
        client_version=request.client_version,
    )

    return updated_device


@router.get("/{device_id}/tokens", response_model=List[TokenResponse])
async def get_device_tokens(
    device_id: int, current_user: dict = Depends(get_current_user)
):
    """Получить все токены устройства"""
    # Проверяем владельца устройства
    device = await db.devices.get_device_by_id(
        device_id=device_id, user_id=current_user["id"]
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
        )

    tokens = await db.api_tokens.get_device_tokens(device_id, current_user["id"])
    # Возвращаем токены (включая сам токен только для нового создания)
    # Для существующих токенов не показываем сам токен, только метаданные
    return tokens


@router.delete("/{device_id}/tokens/{token_id}")
async def revoke_token(
    device_id: int, token_id: int, current_user: dict = Depends(get_current_user)
):
    """Отозвать токен устройства"""
    # Проверяем владельца устройства
    device = await db.devices.get_device_by_id(
        device_id=device_id, user_id=current_user["id"]
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
        )

    success = await db.api_tokens.revoke_token(token_id, current_user["id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден"
        )

    return {"message": "Токен отозван"}


@router.delete("/{device_id}")
async def delete_device(device_id: int, current_user: dict = Depends(get_current_user)):
    """Удалить устройство"""
    success = await db.devices.delete_device(device_id, current_user["id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
        )

    return {"message": "Устройство удалено"}
