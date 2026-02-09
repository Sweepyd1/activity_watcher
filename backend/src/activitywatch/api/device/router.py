from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from src.activitywatch.schemas.devices.schema import (
    CreateDeviceRequest,
    CreateTokenRequest,
    DeviceResponse,
    RegisterDeviceRequest,
    TokenResponse,
)
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
    try:
        
        device = await db.devices.get_device_by_id(
            device_id=request.device_id, user_id=current_user["id"]
        )

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
            )

        token_data = await db.tokens.create_token(
            user_id=current_user["id"],
            device_id=request.device_id,
            token_name=request.token_name,
        )

        return token_data
    except Exception as e:
        print(e)


@router.post("/register", response_model=DeviceResponse, status_code=201)
async def register_device(request: RegisterDeviceRequest):
    api_token = await db.tokens.validate_token(request.token)
    if not api_token:
        raise HTTPException(status_code=401, detail="Неверный токен")

    device = await db.devices.get_device_by_id(api_token.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    if device.device_id and device.device_id != request.device_id:
        raise HTTPException(status_code=400, detail="Устройство уже зарегистрировано")

    updated_device = await db.devices.update_device_registration(
        device_id=device.id,
        real_device_id=request.device_id,
        device_name=request.device_name or request.hostname,
        system=request.system,
        hostname=request.hostname,
        platform_version=request.platform_version,
        client_version=request.client_version,

    )

    return updated_device



@router.get("/{device_id}/tokens", response_model=List[TokenResponse])
async def get_device_tokens(
    device_id: int, current_user: dict = Depends(get_current_user)
):

    device = await db.devices.get_device_by_id(
        device_id=device_id, user_id=current_user["id"]
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
        )

    tokens = await db.api_tokens.get_device_tokens(device_id, current_user["id"])
    return tokens


@router.delete("/{device_id}/tokens/{token_id}")
async def revoke_token(
    device_id: int, token_id: int, current_user: dict = Depends(get_current_user)
):

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

    success = await db.devices.delete_device(device_id, current_user["id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Устройство не найдено"
        )

    return {"message": "Устройство удалено"}


@router.post("/create_token", response_model=DeviceResponse)
async def create_token(
    request: Request, current_user: dict = Depends(get_current_user)
):
    pass