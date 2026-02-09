#!/usr/bin/env python3
import sys
import argparse
from .cli import main as cli_main
from sync_client import ActivityWatchSyncService, ActivityWatchClient, SyncStateManager

def sync_service():
    """Запуск сервиса синхронизации (без интерактивных элементов)"""
    from .service import ActivityWatchClient, SyncStateManager, ActivityWatchSyncService
    
    client = ActivityWatchClient()
    state_manager = SyncStateManager(client.state_file)
    sync_service = ActivityWatchSyncService(client, state_manager)
    
    # Используем аргументы командной строки
    import sys
    interval = 1  # по умолчанию
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--interval="):
                try:
                    interval = int(arg.split("=")[1])
                except:
                    pass
    
    sync_service.continuous_sync(interval)

def main():
    parser = argparse.ArgumentParser(description="ActivityWatch Client")
    parser.add_argument("--cli", action="store_true", help="Запустить CLI режим")
    parser.add_argument("--service", action="store_true", help="Запустить сервис синхронизации")
    parser.add_argument("--interval", type=int, default=5, help="Интервал синхронизации в минутах")
    
    args = parser.parse_args()
    
    if args.service:
        # Запускаем сервис синхронизации
        client = ActivityWatchClient()
        state_manager = SyncStateManager(client.state_file)
        sync_service = ActivityWatchSyncService(client, state_manager)
        sync_service.continuous_sync(args.interval)
    else:
        # По умолчанию запускаем CLI
        cli_main()

if __name__ == "__main__":
    main()