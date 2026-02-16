
import sys
import os
import logging
import time
import atexit
from pathlib import Path

# Добавляем путь к текущей директории ДО импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Настройка логирования
log_dir = Path.home() / ".activitywatch"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "activitywatch_sync.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(log_file)),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

def cleanup():
    """Очистка при завершении"""
    logger.info("Очистка ресурсов перед завершением")

def wait_for_activitywatch(timeout=120):
    """Ждем запуска ActivityWatch"""
    import requests
    import time as t
    
    start = t.time()
    while t.time() - start < timeout:
        try:
            response = requests.get("http://localhost:5600/api/0/info", timeout=5)
            if response.status_code == 200:
                logger.info("ActivityWatch доступен!")
                return True
        except:
            pass
        logger.info(f"Ожидание ActivityWatch... ({int(t.time() - start)} сек)")
        t.sleep(5)
    
    logger.warning(f"ActivityWatch не запустился за {timeout} секунд")
    return False

def main():
    """Основная функция для systemd сервиса"""
    atexit.register(cleanup)
    logger.info("=== Запуск сервиса синхронизации ActivityWatch ===")
    
    # Ждем ActivityWatch
    if not wait_for_activitywatch():
        logger.error("ActivityWatch не запущен. Завершение.")
        return 1
    
    try:
        # Импортируем компоненты
        from sync_client import ActivityWatchSyncService, ActivityWatchClient, SyncStateManager
        
        logger.info("Инициализация клиентов...")
        
        # Создаем клиент ActivityWatch
        client = ActivityWatchClient()
        
        # Проверяем доступность ActivityWatch
        if not client.check_activitywatch_connection():
            logger.error("ActivityWatch недоступен после ожидания!")
            return 1
        
        # Проверяем сервер
        if not client.check_server_connection():
            logger.warning("Сервер недоступен, но продолжаем...")
        
        # Создаем менеджер состояния и сервис
        state_manager = SyncStateManager(client.state_file)
        sync_service = ActivityWatchSyncService(client, state_manager)
        
        logger.info("✅ Все компоненты инициализированы")
        logger.info(f"Device ID: {client.device_info.device_id}")
        
        # Непрерывная синхронизация (более надежная версия)
        sync_interval = 60  # минут
        logger.info(f"Запуск непрерывной синхронизации (интервал {sync_interval} секунд)...")
        
        while True:
            try:
                success = sync_service.sync()
                if not success:
                    logger.warning("Синхронизация завершилась с ошибкой")
                
                logger.info(f"Ожидание {sync_interval} секунд до следующей синхронизации")
                time.sleep(sync_interval)
                
            except KeyboardInterrupt:
                logger.info("Остановлено пользователем")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле синхронизации: {e}", exc_info=True)
                time.sleep(60)  # Ждем минуту перед повторной попыткой
        
        return 0
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)