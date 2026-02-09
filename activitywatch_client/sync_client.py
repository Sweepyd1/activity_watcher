
import json
import time

import socket

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from pathlib import Path

import logging



from config import BaseSyncClient, SyncState
from service import ActivityWatchClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("activitywatch_manager.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

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
            device_id=socket.gethostname(), first_sync=datetime.now(timezone.utc)
        )

        if not self.state_file.exists():
            return default_state

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)

            state = SyncState()
            for key, value in data.items():
                if hasattr(state, key):
                    if key.endswith("_time") and value:
                        # Парсим datetime
                        try:
                            if "Z" in value:
                                dt = datetime.fromisoformat(
                                    value.replace("Z", "+00:00")
                                ).replace(tzinfo=timezone.utc)
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
                if not key.startswith("_"):
                    value = getattr(self.state, key)
                    if isinstance(value, datetime):
                        # Убедимся, что datetime в UTC
                        if value.tzinfo is None:
                            value = value.replace(tzinfo=timezone.utc)
                        state_dict[key] = value.isoformat().replace("+00:00", "Z")
                    elif value is not None:
                        state_dict[key] = value

            with open(self.state_file, "w") as f:
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
            logger.info(
                f"Первая синхронизация, начинаем с {last_sync.strftime('%H:%M')}"
            )

        # Получаем события
        events, actual_start = self.client.get_events_safe(bucket_id, last_sync)

        if not events:
            logger.info("Нет новых событий")
            return True

        # Фильтруем только новые события
        new_events, new_hashes = self.client.filter_new_events(
            events, self.state.state.last_sync_time, self.state.state.last_event_hashes
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

        last_sync = self.state.state.last_sync_time or datetime.now(
            timezone.utc
        ) - timedelta(hours=1)
        events, _ = self.client.get_events_safe(bucket_id, last_sync)

        return events

    def continuous_sync(self, interval_minutes: int = 1):
        """
        Запускает непрерывную синхронизацию.

        Args:
            interval_minutes: Интервал между синхронизациями в минутах
        """
        logger.info(
            f"Запуск непрерывной синхронизации с интервалом {interval_minutes} минут"
        )

        try:
            while True:
                logger.info("Начало цикла синхронизации")
                self.sync()

                logger.info(
                    f"Ожидание {interval_minutes} минут до следующей синхронизации"
                )
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

