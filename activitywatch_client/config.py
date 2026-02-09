from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class DeviceInfo:
    """Информация об устройстве"""

    hostname: str
    system: str
    release: str
    version: str
    machine: str
    processor: str
    device_id: str
    device_name: str
    python_version: str
    client_version: str = "2.0"


@dataclass
class SyncState:
    """Состояние синхронизации"""

    last_sync_time: Optional[datetime] = None
    last_event_hashes: List[str] = field(default_factory=list)
    device_id: str = ""
    first_sync: Optional[datetime] = None
    last_daily_report: Optional[str] = None
    processed_events_count: int = 0


class BaseSyncClient(ABC):
    """Базовый класс клиента синхронизации"""

    @abstractmethod
    def sync(self) -> bool:
        """Выполнить синхронизацию"""
        pass

    @abstractmethod
    def get_available_data(self) -> List[Dict]:
        """Получить доступные данные для синхронизации"""
        pass