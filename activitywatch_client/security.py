import uuid
import psutil
import requests
import json
import time
import platform
import socket
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import sys
import logging
from abc import ABC, abstractmethod
import os
import sys

import subprocess
import shutil
import tempfile
import zipfile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("activitywatch_manager.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".activitywatch-client"
CONFIG_FILE = CONFIG_DIR / "config.json"

class SecurityToken:
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_dir.mkdir(exist_ok=True)
        
    def generate_device_id(self) -> str:
        """Генерирует уникальный device_id через uuid4"""
        return str(uuid.uuid4())
    
    def get_system_info(self) -> dict:
        """Получает информацию о системе и устройстве"""
        try:
            hostname = socket.gethostname()
            return {
                "system": f"{platform.system()} {platform.release()} {platform.machine()}",
                "hostname": hostname,
                "device_name": hostname.split('.')[0] if '.' in hostname else hostname,
                "platform_version": platform.platform(),
            
            }
        except Exception as e:
            logger.error(f"Ошибка получения системной информации: {e}")
            return {
                "system": "Unknown",
                "hostname": "unknown",
                "device_name": "unknown",
                "platform_version": "unknown",
                "processor": "unknown",
                "memory_gb": 0
            }
    
    def save_config(self, token: str, device_id: str):
        """Сохраняет токен и device_id на диск"""
        config = {
            "token": token,
            "device_id": device_id,
            "created_at": str(uuid.uuid4()),  # для ротации
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)  # Только владелец может читать
        logger.info(f"Конфиг сохранен: {CONFIG_FILE}")
    
    def load_config(self) -> dict:
        """Читает сохраненные данные"""
        if not CONFIG_FILE.exists():
            return {}
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения конфига: {e}")
            return {}
    
    def clear_config(self):
        """Удаляет конфиг"""
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            logger.info("Конфиг удален")
    
    def register_device(self):
        """Главная функция регистрации устройства"""
        config = self.load_config()
        
        # ✅ Проверяем существующий токен
        if config.get('token') and config.get('device_id'):
            logger.info("Найден существующий токен, используем его")
            token = config['token']
            device_id = config['device_id']
        else:
            # Генерируем новый device_id
            device_id = self.generate_device_id()
            token = input("Введите токен: ").strip()
            
            if not token:
                logger.error("Токен не введен!")
                return False
            
            # Сохраняем
            self.save_config(token, device_id)
        
        # Получаем системную информацию
        sys_info = self.get_system_info()
        
        # Формируем payload
        payload = {
            "token": token,
            "device_id": device_id,
            **sys_info  # Система: Linux x86_64, устройство: sweepy-ms7d99
        }
        
        logger.info(f"Отправка запроса регистрации: {device_id[:8]}...")
        
        try:
            response = requests.post(
                "http://192.168.2.124:8000/devices/register",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info("✅ Устройство успешно зарегистрировано!")
                print(f"Device ID: {device_id}")
                return True
            else:
                logger.error(f"❌ Ошибка регистрации: {response.status_code}")
                print(f"Ошибка: {response.json()}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сети: {e}")
            return False