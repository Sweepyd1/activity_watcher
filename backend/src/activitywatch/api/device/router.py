from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from src.activitywatch.schemas.devices.schema import CreateDeviceRequest, CreateTokenRequest, DeviceResponse, RegisterDeviceRequest, TokenResponse
from src.activitywatch.loader import db
from src.activitywatch.database.models import DevicePlatform, TokenPermission
from src.activitywatch.core.security import get_current_user

router = APIRouter(prefix="/devices", tags=["devices"])

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
