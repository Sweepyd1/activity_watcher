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
from .aw_manager import ActivityWatchManager
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('activitywatch_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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


class ActivityWatchClient:
    """
    Клиент для работы с ActivityWatch API.
    
    Обеспечивает:
    - Получение данных о активности окон и приложений
    - Инкрементальную синхронизацию
    - Обработку периодов без данных
    - Отправку данных на сервер
    
    Attributes:
        api_url (str): URL API ActivityWatch
        server_url (str): URL целевого сервера
        device_info (DeviceInfo): Информация об устройстве
        state_file (Path): Путь к файлу состояния
    """
    
    def __init__(self, api_url: str = "http://localhost:5600/api/0",
                 server_url: str = "http://localhost:8000"):
        """
        Инициализация клиента.
        
        Args:
            api_url: URL ActivityWatch API (по умолчанию: http://localhost:5600/api/0)
            server_url: URL целевого сервера (по умолчанию: http://localhost:8000)
        """
        self.api_url = api_url
        self.server_url = server_url
        
        # Инициализация информации об устройстве
        self.device_info = self._collect_device_info()
        
        # Файл состояния синхронизации
        self.state_file = Path.home() / ".activitywatch_sync_state.json"
        
        # Сессия HTTP для повторного использования соединений
        self.session = requests.Session()
        self.session.timeout = 10
        
        logger.info(f"Инициализирован клиент для устройства: {self.device_info.device_name}")
    
    def _collect_device_info(self) -> DeviceInfo:
        """
        Собирает информацию об устройстве и системе.
        
        Returns:
            DeviceInfo: Объект с информацией об устройстве
        """
        return DeviceInfo(
            hostname=platform.node(),
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
            machine=platform.machine(),
            processor=platform.processor(),
            device_id=socket.gethostname(),
            device_name=platform.node(),
            python_version=platform.python_version()
        )
    
    def check_activitywatch_connection(self) -> bool:
        """
        Проверяет подключение к ActivityWatch.
        
        Returns:
            bool: True если подключение успешно, иначе False
        """
        try:
            response = self.session.get(f"{self.api_url}/info", timeout=3)
            if response.status_code == 200:
                logger.info("Подключение к ActivityWatch успешно")
                return True
        except requests.RequestException as e:
            logger.error(f"Ошибка подключения к ActivityWatch: {e}")
        return False
    
    def check_server_connection(self) -> bool:
        """
        Проверяет подключение к целевому серверу.
        
        Returns:
            bool: True если подключение успешно, иначе False
        """
        try:
            response = self.session.get(f"{self.server_url}", timeout=3)
            if response.status_code == 200:
                logger.info("Подключение к серверу успешно")
                return True
        except requests.RequestException as e:
            logger.error(f"Ошибка подключения к серверу: {e}")
        return False
    
    def get_buckets(self) -> Dict[str, Any]:
        """
        Получает список всех buckets из ActivityWatch.
        
        Returns:
            Dict: Словарь с информацией о buckets
        """
        try:
            response = self.session.get(f"{self.api_url}/buckets")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка получения buckets: {e}")
            return {}
    
    def find_window_bucket(self) -> Optional[str]:
        """
        Находит bucket с данными окон.
        
        Returns:
            Optional[str]: Идентификатор bucket или None если не найден
        """
        buckets = self.get_buckets()
        if not buckets:
            return None
        
        # Ищем bucket с окнами
        for bucket_id in buckets.keys():
            if 'window' in bucket_id.lower():
                return bucket_id
        
        # Если не нашли, возвращаем первый доступный
        return list(buckets.keys())[0] if buckets else None
    
    def get_events(self, bucket_id: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, limit: int = 1000) -> List[Dict]:
        """
        Получает события из указанного bucket.
        
        Args:
            bucket_id: Идентификатор bucket
            start_time: Начальное время (опционально)
            end_time: Конечное время (опционально)
            limit: Максимальное количество событий
        
        Returns:
            List[Dict]: Список событий
        """
        params = {"limit": limit}
        
        if start_time:
            # Приводим к UTC и ISO формату
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            params["start"] = start_time.isoformat().replace('+00:00', 'Z')
        
        if end_time:
            # Приводим к UTC и ISO формату
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            params["end"] = end_time.isoformat().replace('+00:00', 'Z')
        
        try:
            response = self.session.get(
                f"{self.api_url}/buckets/{bucket_id}/events",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500:
                logger.warning(f"ActivityWatch вернул 500 для периода "
                             f"{start_time if start_time else 'None'} - {end_time if end_time else 'None'}")
                return []
            else:
                logger.error(f"Ошибка получения событий: {response.status_code}")
                return []
        except requests.RequestException as e:
            logger.error(f"Ошибка запроса событий: {e}")
            return []
    
    def get_events_safe(self, bucket_id: str, target_start: datetime,
                       max_hours_back: int = 24) -> Tuple[List[Dict], datetime]:
        """
        Безопасное получение событий с обработкой случаев отсутствия данных.
        
        Args:
            bucket_id: Идентификатор bucket
            target_start: Целевое время начала
            max_hours_back: Максимальный период назад в часах
        
        Returns:
            Tuple[List[Dict], datetime]: События и фактическое время начала
        """
        current_time = datetime.now(timezone.utc)
        
        # Убедимся, что target_start в UTC
        if target_start.tzinfo is None:
            target_start = target_start.replace(tzinfo=timezone.utc)
        
        # Проверяем, не слишком ли старое время
        time_diff_hours = (current_time - target_start).total_seconds() / 3600
        
        if time_diff_hours > max_hours_back:
            logger.warning(f"Запрос слишком старого времени ({time_diff_hours:.1f} часов), ограничиваю {max_hours_back} часами")
            target_start = current_time - timedelta(hours=max_hours_back)
        
        # Пробуем получить данные
        events = self.get_events(bucket_id, target_start, current_time)
        
        if events:
            return events, target_start
        
        # Если данных нет, пробуем найти ближайшие доступные
        logger.info("Поиск ближайших доступных данных...")
        
        # Пробуем различные стратегии поиска
        search_strategies = [
            ("последний час", timedelta(hours=1)),
            ("последние 3 часа", timedelta(hours=3)),
            ("последние 6 часов", timedelta(hours=6)),
        ]
        
        for strategy_name, time_delta in search_strategies:
            new_start = current_time - time_delta
            
            if new_start < target_start:
                new_start = target_start
            
            logger.info(f"Пробую стратегию: {strategy_name} (с {new_start.strftime('%H:%M')})")
            events = self.get_events(bucket_id, new_start, current_time)
            
            if events:
                logger.info(f"Данные найдены по стратегии: {strategy_name}")
                return events, new_start
        
        # Если ничего не нашли, возвращаем пустой список
        return [], target_start
    
    def _ensure_utc(self, dt: datetime) -> datetime:
        """
        Убеждается, что datetime находится в UTC.
        
        Args:
            dt: Входной datetime
        
        Returns:
            datetime: datetime в UTC
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    
    def calculate_event_hash(self, event: Dict) -> str:
        """
        Вычисляет уникальный хэш события для дедупликации.
        
        Args:
            event: Событие
        
        Returns:
            str: Хэш события
        """
        event_data = event.get('data', {})
        event_str = (
            f"{self.device_info.device_id}_"
            f"{event.get('timestamp', '')}_"
            f"{event_data.get('app', '')}_"
            f"{event_data.get('title', '')}"
        )
        return hashlib.md5(event_str.encode()).hexdigest()
    
    def filter_new_events(self, events: List[Dict],
                         last_sync_time: Optional[datetime],
                         known_hashes: List[str]) -> Tuple[List[Dict], List[str]]:
        """
        Фильтрует только новые события.
        
        Args:
            events: Список всех событий
            last_sync_time: Время последней синхронизации
            known_hashes: Известные хэши событий
        
        Returns:
            Tuple[List[Dict], List[str]]: Новые события и их хэши
        """
        new_events = []
        new_hashes = []
        
        if not last_sync_time:
            # Первая синхронизация - все события новые
            for event in events:
                event_hash = self.calculate_event_hash(event)
                new_events.append(event)
                new_hashes.append(event_hash)
            return new_events, new_hashes
        
        # Убедимся, что last_sync_time в UTC
        last_sync_time = self._ensure_utc(last_sync_time)
        
        for event in events:
            # Проверка по времени
            event_time = event.get('timestamp')
            if event_time:
                try:
                    # Парсим время события (ActivityWatch отдает в UTC)
                    if 'Z' in event_time:
                        event_dt = datetime.fromisoformat(event_time.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                    else:
                        event_dt = datetime.fromisoformat(event_time)
                        if event_dt.tzinfo is None:
                            event_dt = event_dt.replace(tzinfo=timezone.utc)
                    
                    if event_dt <= last_sync_time:
                        continue
                except ValueError as e:
                    logger.warning(f"Ошибка парсинга времени события: {e}")
                    continue
            
            # Проверка по хэшу
            event_hash = self.calculate_event_hash(event)
            if event_hash in known_hashes:
                continue
            
            new_events.append(event)
            new_hashes.append(event_hash)
        
        return new_events, new_hashes
    
    def categorize_application(self, app_name: str) -> str:
        """
        Категоризирует приложение по его названию.
        
        Args:
            app_name: Название приложения
        
        Returns:
            str: Категория приложения
        """
        if not app_name:
            return 'unknown'
        
        app_lower = app_name.lower()
        
        categories = {
            'browser': ['chrome', 'firefox', 'edge', 'safari', 'browser', 'opera'],
            'development': ['code', 'pycharm', 'vscode', 'intellij', 'studio', 'visual studio'],
            'communication': ['slack', 'discord', 'teams', 'zoom', 'telegram', 'whatsapp'],
            'terminal': ['terminal', 'cmd', 'powershell', 'bash', 'zsh'],
            'media': ['spotify', 'music', 'vlc', 'player', 'netflix'],
            'office': ['excel', 'word', 'powerpoint', 'office', 'libreoffice'],
            'system': ['explorer', 'finder', 'nautilus', 'dolphin']
        }
        
        for category, keywords in categories.items():
            if any(keyword in app_lower for keyword in keywords):
                return category
        
        return 'other'
    
    def prepare_daily_summary(self, events: List[Dict]) -> Dict:
        """
        Подготавливает дневную сводку по событиям.
        
        Args:
            events: Список событий за день
        
        Returns:
            Dict: Дневная сводка
        """
        summary = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "device_info": asdict(self.device_info),
            "hourly_data": {},
            "applications": {},
            "categories": {},
            "total_active_time": 0,
            "total_events": len(events)
        }
        
        for event in events:
            # Извлекаем время события
            event_time = event.get('timestamp')
            if not event_time:
                continue
            
            try:
                # Парсим время события
                if 'Z' in event_time:
                    dt = datetime.fromisoformat(event_time.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                else:
                    dt = datetime.fromisoformat(event_time)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                
                hour_key = dt.strftime("%Y-%m-%d %H:00")
            except ValueError:
                continue
            
            # Извлекаем данные приложения
            app = event.get('data', {}).get('app', 'Unknown')
            duration = event.get('duration', 0)
            
            # Обновляем почасовые данные
            if hour_key not in summary["hourly_data"]:
                summary["hourly_data"][hour_key] = {
                    "applications": {},
                    "total_time": 0
                }
            
            hour_data = summary["hourly_data"][hour_key]
            hour_data["applications"][app] = hour_data["applications"].get(app, 0) + duration
            hour_data["total_time"] += duration
            
            # Обновляем данные по приложениям
            summary["applications"][app] = summary["applications"].get(app, 0) + duration
            
            # Обновляем общее время
            summary["total_active_time"] += duration
        
        # Категоризируем приложения
        for app, duration in summary["applications"].items():
            category = self.categorize_application(app)
            summary["categories"][category] = summary["categories"].get(category, 0) + duration
        
        return summary
    
    def send_incremental_update(self, events: List[Dict]) -> bool:
        """
        Отправляет инкрементальное обновление на сервер.
        
        Args:
            events: Список новых событий
        
        Returns:
            bool: True если отправка успешна, иначе False
        """
        if not events:
            logger.info("Нет событий для отправки")
            return True
        
        payload = {
            "type": "incremental_update",
            "device_info": asdict(self.device_info),
            "events": events,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(events)
        }
        
        try:
            response = self.session.post(
                f"{self.server_url}/receive_incremental",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"Отправлено {len(events)} новых событий")
                return True
            else:
                logger.error(f"Ошибка отправки: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"Ошибка подключения при отправке: {e}")
            return False
    
    def send_daily_summary(self, summary: Dict) -> bool:
        """
        Отправляет дневную сводку на сервер.
        
        Args:
            summary: Дневная сводка
        
        Returns:
            bool: True если отправка успешна, иначе False
        """
        try:
            response = self.session.post(
                f"{self.server_url}/receive_daily_summary",
                json=summary,
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"Дневная сводка отправлена за {summary['date']}")
                return True
            else:
                logger.error(f"Ошибка отправки сводки: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"Ошибка подключения при отправке сводки: {e}")
            return False


class SyncStateManager:
    """
    Менеджер состояния синхронизации.
    
    Управляет сохранением и загрузкой состояния синхронизации.
    """
    
    def __init__(self, state_file: Path):
        """
        Инициализация менеджера состояния.
        
        Args:
            state_file: Путь к файлу состояния
        """
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> SyncState:
        """
        Загружает состояние из файла.
        
        Returns:
            SyncState: Объект состояния
        """
        default_state = SyncState(
            device_id=socket.gethostname(),
            first_sync=datetime.now(timezone.utc)
        )
        
        if not self.state_file.exists():
            return default_state
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            
            state = SyncState()
            for key, value in data.items():
                if hasattr(state, key):
                    if key.endswith('_time') and value:
                        # Парсим datetime
                        try:
                            if 'Z' in value:
                                dt = datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
                            else:
                                dt = datetime.fromisoformat(value)
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                            setattr(state, key, dt)
                        except ValueError:
                            setattr(state, key, value)
                    else:
                        setattr(state, key, value)
            
            return state
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Ошибка загрузки состояния: {e}")
            return default_state
    
    def save_state(self) -> bool:
        """
        Сохраняет состояние в файл.
        
        Returns:
            bool: True если сохранение успешно, иначе False
        """
        try:
            # Конвертируем datetime в строки
            state_dict = {}
            for key in dir(self.state):
                if not key.startswith('_'):
                    value = getattr(self.state, key)
                    if isinstance(value, datetime):
                        # Убедимся, что datetime в UTC
                        if value.tzinfo is None:
                            value = value.replace(tzinfo=timezone.utc)
                        state_dict[key] = value.isoformat().replace('+00:00', 'Z')
                    elif value is not None:
                        state_dict[key] = value
            
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2, default=str)
            
            return True
        except IOError as e:
            logger.error(f"Ошибка сохранения состояния: {e}")
            return False
    
    def update_sync_time(self, sync_time: datetime):
        """
        Обновляет время последней синхронизации.
        
        Args:
            sync_time: Время синхронизации
        """
        # Убедимся, что sync_time в UTC
        if sync_time.tzinfo is None:
            sync_time = sync_time.replace(tzinfo=timezone.utc)
        
        self.state.last_sync_time = sync_time
        self.state.processed_events_count += 1
        self.save_state()
    
    def add_event_hashes(self, hashes: List[str], max_hashes: int = 1000):
        """
        Добавляет хэши событий в состояние.
        
        Args:
            hashes: Список хэшей событий
            max_hashes: Максимальное количество хранимых хэшей
        """
        self.state.last_event_hashes.extend(hashes)
        # Ограничиваем количество хранимых хэшей
        self.state.last_event_hashes = self.state.last_event_hashes[-max_hashes:]
        self.save_state()


class ActivityWatchSyncService(BaseSyncClient):
    """
    Сервис синхронизации ActivityWatch.
    
    Координирует процесс сбора и отправки данных.
    """
    
    def __init__(self, client: ActivityWatchClient, state_manager: SyncStateManager):
        """
        Инициализация сервиса синхронизации.
        
        Args:
            client: Клиент ActivityWatch
            state_manager: Менеджер состояния
        """
        self.client = client
        self.state = state_manager
        self.daily_cache = []
    
    def sync(self) -> bool:
        """
        Выполняет одну итерацию синхронизации.
        
        Returns:
            bool: True если синхронизация успешна, иначе False
        """
        # Проверяем подключения
        if not self.client.check_activitywatch_connection():
            logger.warning("ActivityWatch недоступен")
            return False
        
        if not self.client.check_server_connection():
            logger.warning("Сервер недоступен")
            return False
        
        # Получаем bucket с данными окон
        bucket_id = self.client.find_window_bucket()
        if not bucket_id:
            logger.warning("Bucket окон не найден")
            return False
        
        # Определяем время начала запроса
        last_sync = self.state.state.last_sync_time
        current_time = datetime.now(timezone.utc)
        
        if not last_sync:
            # Первая синхронизация - берем последний час
            last_sync = current_time - timedelta(hours=1)
            logger.info(f"Первая синхронизация, начинаем с {last_sync.strftime('%H:%M')}")
        
        # Получаем события
        events, actual_start = self.client.get_events_safe(bucket_id, last_sync)
        
        if not events:
            logger.info("Нет новых событий")
            return True
        
        # Фильтруем только новые события
        new_events, new_hashes = self.client.filter_new_events(
            events,
            self.state.state.last_sync_time,
            self.state.state.last_event_hashes
        )
        
        if not new_events:
            logger.info("Все события уже были обработаны")
            return True
        
        # Отправляем инкрементальное обновление
        success = self.client.send_incremental_update(new_events)
        
        if success:
            # Обновляем состояние
            self.state.update_sync_time(current_time)
            self.state.add_event_hashes(new_hashes)
            
            # Добавляем события в дневной кэш
            self.daily_cache.extend(new_events)
            
            # Проверяем, нужно ли отправить дневной отчет
            self._check_and_send_daily_report()
        
        return success
    
    def _check_and_send_daily_report(self):
        """Проверяет и отправляет дневной отчет при необходимости."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if self.state.state.last_daily_report != today and self.daily_cache:
            logger.info(f"Отправка дневного отчета за {today}")
            
            summary = self.client.prepare_daily_summary(self.daily_cache)
            success = self.client.send_daily_summary(summary)
            
            if success:
                self.state.state.last_daily_report = today
                self.state.save_state()
                self.daily_cache = []  # Очищаем кэш
    
    def get_available_data(self) -> List[Dict]:
        """Получить доступные данные для синхронизации."""
        bucket_id = self.client.find_window_bucket()
        if not bucket_id:
            return []
        
        last_sync = self.state.state.last_sync_time or datetime.now(timezone.utc) - timedelta(hours=1)
        events, _ = self.client.get_events_safe(bucket_id, last_sync)
        
        return events
    
    def continuous_sync(self, interval_minutes: int = 1):
        """
        Запускает непрерывную синхронизацию.
        
        Args:
            interval_minutes: Интервал между синхронизациями в минутах
        """
        logger.info(f"Запуск непрерывной синхронизации с интервалом {interval_minutes} минут")
        
        try:
            while True:
                logger.info("Начало цикла синхронизации")
                self.sync()
                
                logger.info(f"Ожидание {interval_minutes} минут до следующей синхронизации")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Синхронизация остановлена пользователем")
            
            # Отправляем оставшиеся данные перед выходом
            if self.daily_cache:
                logger.info("Отправка накопленных данных перед выходом")
                summary = self.client.prepare_daily_summary(self.daily_cache)
                self.client.send_daily_summary(summary)
        
        except Exception as e:
            logger.error(f"Критическая ошибка в непрерывной синхронизации: {e}")
            raise


def main():
    """Основная функция запуска клиента."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ActivityWatch Sync Client")
    parser.add_argument("--mode", choices=["once", "continuous"], default="continuous",
                       help="Режим работы (once - один раз, continuous - непрерывно)")
    parser.add_argument("--interval", type=int, default=1,
                       help="Интервал синхронизации в минутах (для непрерывного режима)")
    parser.add_argument("--health", action="store_true",
                       help="Проверить состояние ActivityWatch")
    parser.add_argument("--reset", action="store_true",
                       help="Сбросить состояние синхронизации")
    parser.add_argument("--status", action="store_true",
                       help="Показать статус синхронизации")
    
    args = parser.parse_args()
    
    # Проверка здоровья ActivityWatch
    if args.health:
        print("\n" + "="*60)
        print("ПРОВЕРКА ЗДОРОВЬЯ ACTIVITYWATCH")
        print("="*60)
        
        client = ActivityWatchClient()
        if client.check_activitywatch_connection():
            print("✓ ActivityWatch доступен")
            
            # Проверяем сервер
            if client.check_server_connection():
                print("✓ Сервер доступен")
            else:
                print("✗ Сервер недоступен")
            
            # Показываем buckets
            buckets = client.get_buckets()
            print(f"\nНайдено buckets: {len(buckets)}")
            for bucket_id in buckets.keys():
                print(f"  - {bucket_id}")
                
                # Показываем последнее событие
                events = client.get_events(bucket_id, limit=1)
                if events:
                    event = events[0]
                    timestamp = event.get('timestamp', '')
                    if timestamp:
                        try:
                            if 'Z' in timestamp:
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            else:
                                dt = datetime.fromisoformat(timestamp)
                            age = (datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)).total_seconds() / 60
                            print(f"    Последнее событие: {age:.1f} минут назад")
                        except:
                            print(f"    Есть события (время неизвестно)")
        else:
            print("✗ ActivityWatch недоступен")
            print("\nУбедитесь, что ActivityWatch запущен:")
            print("  aw-server &")
            print("  aw-watcher-window &")
            print("  aw-watcher-afk &")
        
        print("="*60)
        return
    
    # Показать статус
    if args.status:
        state_file = Path.home() / ".activitywatch_sync_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                print("\n" + "="*60)
                print("СТАТУС СИНХРОНИЗАЦИИ")
                print("="*60)
                
                device_id = state.get('device_id', socket.gethostname())
                print(f"Устройство: {device_id}")
                
                last_sync = state.get('last_sync_time')
                if last_sync:
                    try:
                        if 'Z' in last_sync:
                            dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                        else:
                            dt = datetime.fromisoformat(last_sync)
                        age = (datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)).total_seconds() / 60
                        print(f"Последняя синхронизация: {age:.1f} минут назад")
                    except:
                        print(f"Последняя синхронизация: {last_sync}")
                else:
                    print("Последняя синхронизация: Никогда")
                
                print(f"Обработано событий: {state.get('processed_events_count', 0)}")
                print(f"Хэшей в памяти: {len(state.get('last_event_hashes', []))}")
                print(f"Последний дневной отчет: {state.get('last_daily_report', 'Не отправлялся')}")
                
            except Exception as e:
                print(f"Ошибка чтения состояния: {e}")
        else:
            print("Файл состояния не найден (синхронизация еще не запускалась)")
        return
    
    # Сброс состояния
    if args.reset:
        state_file = Path.home() / ".activitywatch_sync_state.json"
        if state_file.exists():
            import shutil
            backup_file = state_file.with_suffix('.json.backup')
            shutil.copy2(state_file, backup_file)
            state_file.unlink()
            print(f"Состояние сброшено (резервная копия: {backup_file})")
        else:
            print("Файл состояния не найден")
        return
    
    # Запуск синхронизации
    client = ActivityWatchClient()
    state_manager = SyncStateManager(client.state_file)
    sync_service = ActivityWatchSyncService(client, state_manager)
    
    print(f"\nЗапуск синхронизации для устройства: {client.device_info.device_name}")
    
    if state_manager.state.last_sync_time:
        last_sync_str = state_manager.state.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"Последняя синхронизация: {last_sync_str}")
    else:
        print("Последняя синхронизация: Никогда")
    
    if args.mode == "once":
        print("\nВыполнение однократной синхронизации...")
        success = sync_service.sync()
        if success:
            print("Синхронизация успешно завершена")
        else:
            print("Синхронизация завершена с ошибками")
    else:
        print(f"\nЗапуск непрерывной синхронизации с интервалом {args.interval} минут")
        print("Нажмите Ctrl+C для остановки")
        sync_service.continuous_sync(args.interval)

def ensure_activitywatch_running():
    """Убедиться, что ActivityWatch запущен"""
    manager = ActivityWatchManager()
    
    # Проверяем установку
    installed, _ = manager.check_activitywatch_installed()
    if not installed:
        logger.warning("ActivityWatch не установлен. Пытаемся установить...")
        if not manager.install_activitywatch():
            logger.error("Не удалось установить ActivityWatch. Завершаем работу.")
            return False
    
    # Проверяем запуск
    if not manager.check_activitywatch_running():
        logger.warning("ActivityWatch не запущен. Пытаемся запустить...")
        if not manager.start_activitywatch():
            logger.error("Не удалось запустить ActivityWatch. Завершаем работу.")
            return False
    
    return True
if __name__ == "__main__":
    if not ensure_activitywatch_running():
        sys.exit(1)
    main()