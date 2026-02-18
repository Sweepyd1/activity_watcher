import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platform
import socket
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
from pathlib import Path

import logging


from config import DeviceInfo
from security import SecurityToken

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("activitywatch_manager.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        api_url: str = "http://localhost:5600/api/0",
        server_url: str = "http://192.168.2.126:8000",
    ):
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

        logger.info(
            f"Инициализирован клиент для устройства: {self.device_info.device_name}"
        )

    def get_earliest_event_time(self, bucket_id: str) -> Optional[datetime]:
        """Возвращает время самого раннего события в bucket."""
        # Запрашиваем одно событие после очень ранней даты
        very_early = datetime(2000, 1, 1, tzinfo=timezone.utc)
        events = self.get_events(bucket_id, start_time=very_early, limit=1)
        if events:
            ts = events[0].get("timestamp")
            if ts:
                # Преобразуем строку в datetime (как в filter_new_events)
                return self._parse_timestamp(ts)  # нужно реализовать
        return None

    def _parse_timestamp(self, ts_str: str) -> datetime:
        if "Z" in ts_str:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

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
            python_version=platform.python_version(),
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
            if "window" in bucket_id.lower():
                return bucket_id

        # Если не нашли, возвращаем первый доступный
        return list(buckets.keys())[0] if buckets else None

    def get_events(
        self,
        bucket_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict]:
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
            params["start"] = start_time.isoformat().replace("+00:00", "Z")

        if end_time:
            # Приводим к UTC и ISO формату
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            params["end"] = end_time.isoformat().replace("+00:00", "Z")

        try:
            response = self.session.get(
                f"{self.api_url}/buckets/{bucket_id}/events", params=params
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500:
                logger.warning(
                    f"ActivityWatch вернул 500 для периода "
                    f"{start_time if start_time else 'None'} - {end_time if end_time else 'None'}"
                )
                return []
            else:
                logger.error(f"Ошибка получения событий: {response.status_code}")
                return []
        except requests.RequestException as e:
            logger.error(f"Ошибка запроса событий: {e}")
            return []

    def get_events_safe(
        self, bucket_id: str, target_start: datetime, max_hours_back: int = 24
    ) -> Tuple[List[Dict], datetime]:
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
            logger.warning(
                f"Запрос слишком старого времени ({time_diff_hours:.1f} часов), ограничиваю {max_hours_back} часами"
            )
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

            logger.info(
                f"Пробую стратегию: {strategy_name} (с {new_start.strftime('%H:%M')})"
            )
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
        event_data = event.get("data", {})
        event_str = (
            f"{self.device_info.device_id}_"
            f"{event.get('timestamp', '')}_"
            f"{event_data.get('app', '')}_"
            f"{event_data.get('title', '')}"
        )
        return hashlib.md5(event_str.encode()).hexdigest()

    def filter_new_events(
        self,
        events: List[Dict],
        last_sync_time: Optional[datetime],
        known_hashes: List[str],
    ) -> Tuple[List[Dict], List[str]]:
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
            event_time = event.get("timestamp")
            if event_time:
                try:
                    # Парсим время события (ActivityWatch отдает в UTC)
                    if "Z" in event_time:
                        event_dt = datetime.fromisoformat(
                            event_time.replace("Z", "+00:00")
                        ).replace(tzinfo=timezone.utc)
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
            return "unknown"

        app_lower = app_name.lower()

        categories = {
            "browser": ["chrome", "firefox", "edge", "safari", "browser", "opera"],
            "development": [
                "code",
                "pycharm",
                "vscode",
                "intellij",
                "studio",
                "visual studio",
            ],
            "communication": [
                "slack",
                "discord",
                "teams",
                "zoom",
                "telegram",
                "whatsapp",
            ],
            "terminal": ["terminal", "cmd", "powershell", "bash", "zsh"],
            "media": ["spotify", "music", "vlc", "player", "netflix"],
            "office": ["excel", "word", "powerpoint", "office", "libreoffice"],
            "system": ["explorer", "finder", "nautilus", "dolphin"],
        }

        for category, keywords in categories.items():
            if any(keyword in app_lower for keyword in keywords):
                return category

        return "other"

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
            "total_events": len(events),
        }

        for event in events:
            # Извлекаем время события
            event_time = event.get("timestamp")
            if not event_time:
                continue

            try:
                # Парсим время события
                if "Z" in event_time:
                    dt = datetime.fromisoformat(
                        event_time.replace("Z", "+00:00")
                    ).replace(tzinfo=timezone.utc)
                else:
                    dt = datetime.fromisoformat(event_time)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)

                hour_key = dt.strftime("%Y-%m-%d %H:00")
            except ValueError:
                continue

            # Извлекаем данные приложения
            app = event.get("data", {}).get("app", "Unknown")
            duration = event.get("duration", 0)

            # Обновляем почасовые данные
            if hour_key not in summary["hourly_data"]:
                summary["hourly_data"][hour_key] = {"applications": {}, "total_time": 0}

            hour_data = summary["hourly_data"][hour_key]
            hour_data["applications"][app] = (
                hour_data["applications"].get(app, 0) + duration
            )
            hour_data["total_time"] += duration

            # Обновляем данные по приложениям
            summary["applications"][app] = (
                summary["applications"].get(app, 0) + duration
            )

            # Обновляем общее время
            summary["total_active_time"] += duration

        # Категоризируем приложения
        for app, duration in summary["applications"].items():
            category = self.categorize_application(app)
            summary["categories"][category] = (
                summary["categories"].get(category, 0) + duration
            )

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
        sec = SecurityToken()
        config = sec.load_config()

        # ✅ ПРОВЕРКА + ОТЛАДКА
        print(f"🔍 Полный конфиг: {config}")
        device_id = config.get("device_id")
        print(f"🔍 device_id: '{device_id}' (type: {type(device_id)})")

        if not device_id:
            print("❌ ERROR: device_id не найден в конфиге!")
            print("Запустите регистрацию: python client.py")
            return

        payload = {
            "type": "incremental_update",
            "device_info": asdict(self.device_info),
            "events": events,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(events),
            "device_id": device_id,  # ✅ Теперь точно строка!
        }

        try:
            response = self.session.post(
                f"{self.server_url}/tracker/receive_incremental",
                json=payload,
                timeout=15,
            )

            if response.status_code == 200:
                logger.info(f"Отправлено {len(events)} новых событий")
                return True
            else:
                logger.error(
                    f"Ошибка отправки: {response.status_code} - {response.text}"
                )
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
                f"{self.server_url}/tracker/receive_daily_summary",
                json=summary,
                timeout=15,
            )

            if response.status_code == 200:
                logger.info(f"Дневная сводка отправлена за {summary['date']}")
                return True
            else:
                logger.error(
                    f"Ошибка отправки сводки: {response.status_code} - {response.text}"
                )
                return False
        except requests.RequestException as e:
            logger.error(f"Ошибка подключения при отправке сводки: {e}")
            return False
