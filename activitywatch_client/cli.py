import requests
import time
import platform
import logging
import os
from manager import ActivityWatchManager
from security import SecurityToken
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

def ensure_activitywatch_running():
    """Убедиться, что ActivityWatch запущен"""
    manager = ActivityWatchManager()

    # Проверяем установку
    installed, aw_path = manager.check_activitywatch_installed()
    if not installed:
        logger.warning("ActivityWatch не установлен. Пытаемся установить...")
        if not manager.install_activitywatch():
            logger.error("Не удалось установить ActivityWatch. Завершаем работу.")
            return False

    # Проверяем права на файлы
    if manager.system == "Linux" and aw_path:
        # Проверяем реальный файл (если симлинк)
        real_path = aw_path.resolve() if aw_path.is_symlink() else aw_path

        # Проверяем права
        if not os.access(real_path, os.X_OK):
            logger.warning(
                f"Файл {real_path} не имеет прав на выполнение. Исправляем..."
            )
            try:
                real_path.chmod(0o755)
                logger.info(f"Права исправлены для {real_path}")
            except Exception as e:
                logger.error(f"Не удалось установить права: {e}")

        # Проверяем директорию
        parent_dir = real_path.parent
        if not os.access(parent_dir, os.R_OK | os.X_OK):
            logger.warning(f"Директория {parent_dir} недоступна для чтения/выполнения")

    # Проверяем запуск
    if not manager.check_activitywatch_running():
        logger.warning("ActivityWatch не запущен. Пытаемся запустить...")

        # Попробуем несколько раз
        for attempt in range(3):
            logger.info(f"Попытка запуска {attempt + 1}/3")
            if manager.start_activitywatch():
                break
            time.sleep(2)
        else:
            logger.error(
                "Не удалось запустить ActivityWatch после 3 попыток. Завершаем работу."
            )
            return False

    return True

def main():
    """Основная функция запуска менеджера"""
    import argparse

    parser = argparse.ArgumentParser(description="ActivityWatch Installer and Manager")
    parser.add_argument(
        "--check", action="store_true", help="Проверить установку и запуск"
    )
    parser.add_argument(
        "--install", action="store_true", help="Установить ActivityWatch"
    )
    parser.add_argument("--start", action="store_true", help="Запустить ActivityWatch")
    parser.add_argument(
        "--setup-autostart", action="store_true", help="Настроить автозапуск"
    )
    parser.add_argument(
        "--full-setup", action="store_true", help="Выполнить полную настройку"
    )
    parser.add_argument(
        "--startup", action="store_true", help="Режим запуска при старте системы"
    )

    args = parser.parse_args()

    # Создаем менеджер ВНЕ условий (чтобы был доступен везде)
    manager = ActivityWatchManager()

    # Режим запуска при старте системы
    if args.startup:
        logger.info("Запуск в режиме старта системы")
        # Просто запускаем ActivityWatch
        manager.start_activitywatch()
        # Запускаем также вашу утилиту синхронизации
        # (добавьте здесь запуск вашего основного клиента синхронизации)
        return

    # Основные команды
    if args.check:
        print(f"\nПроверка ActivityWatch на {platform.system()}:")
        installed, path = manager.check_activitywatch_installed()
        print(f"  Установлен: {'Да' if installed else 'Нет'}")
        if installed:
            print(f"  Путь: {path}")

        running = manager.check_activitywatch_running()
        print(f"  Запущен: {'Да' if running else 'Нет'}")

    elif args.install:
        print("Установка ActivityWatch...")
        if manager.install_activitywatch():
            print("Установка завершена успешно!")
        else:
            print("Ошибка установки!")

    elif args.start:
        print("Запуск ActivityWatch...")
        if manager.start_activitywatch():
            print("ActivityWatch запущен успешно!")
        else:
            print("Ошибка запуска!")

    elif args.setup_autostart:
        print("Настройка автозапуска...")
        if manager.setup_autostart():
            print("Автозапуск настроен успешно!")
        else:
            print("Ошибка настройки автозапуска!")

    elif args.full_setup:
        print("Полная настройка ActivityWatch...")
        if manager.full_setup():
            print("Настройка завершена успешно!")
        else:
            print("Настройка завершена с ошибками!")

    else:
        # Интерактивный режим
        print(f"\n{'=' * 60}")
        print("ACTIVITYWATCH УСТАНОВЩИК И МЕНЕДЖЕР")
        print(f"{'=' * 60}")
        print(f"Система: {platform.system()} {platform.machine()}")
        print(f"{'=' * 60}")

        installed, path = manager.check_activitywatch_installed()
        running = manager.check_activitywatch_running()

        print(f"\nТекущее состояние:")
        print(f"  ActivityWatch установлен: {'✓' if installed else '✗'}")
        print(f"  ActivityWatch запущен: {'✓' if running else '✗'}")

        print(f"\nДоступные действия:")
        print("  1. Проверить состояние")
        print("  2. Установить/Обновить ActivityWatch")
        print("  3. Запустить ActivityWatch")
        print("  4. Настроить автозапуск")
        print("  5. Полная настройка")
        print("  0. Выход")

        try:
            security = SecurityToken()
            security.register_device()
            

            choice = input("\nВыберите действие (0-5): ").strip()

            if choice == "1":
                print(f"\nДетальная проверка:")
                print(f"  Установлен: {'Да' if installed else 'Нет'}")
                if installed:
                    print(f"  Путь: {path}")
                print(f"  Запущен: {'Да' if running else 'Нет'}")

                # Показываем статус API
                try:
                    response = requests.get(
                        "http://localhost:5600/api/0/info", timeout=2
                    )
                    if response.status_code == 200:
                        info = response.json()
                        print(f"  Версия сервера: {info.get('version', 'неизвестно')}")
                except:
                    print(f"  API недоступен")

            elif choice == "2":
                print("\nУстановка ActivityWatch...")
                if manager.install_activitywatch():
                    print("✓ Установка завершена успешно!")
                else:
                    print("✗ Ошибка установки!")

            elif choice == "3":
                print("\nЗапуск ActivityWatch...")
                if manager.start_activitywatch():
                    print("✓ ActivityWatch запущен успешно!")
                else:
                    print("✗ Ошибка запуска!")

            elif choice == "4":
                print("\nНастройка автозапуска...")
                print("Это настроит автоматический запуск:")
                print("  1. ActivityWatch - трекинг времени")
                print("  2. Менеджера синхронизации - отправка данных на сервер")
                print("\nОбе утилиты будут запускаться при входе в систему.")
                
                confirm = input("\nПродолжить? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Проверяем, установлен ли ActivityWatch
                    installed, _ = manager.check_activitywatch_installed()
                    if not installed:
                        print("ActivityWatch не установлен. Сначала установите его (пункт 2).")
                    else:
                        if manager.setup_autostart():
                            print("✓ Автозапуск настроен успешно!")
                        else:
                            print("✗ Ошибка настройки автозапуска!")
                else:
                    print("Отменено.")

            elif choice == "5":
                print("\nПолная настройка...")
                if manager.full_setup():
                    print("✓ Настройка завершена успешно!")
                else:
                    print("✗ Настройка завершена с ошибками!")

            elif choice == "0":
                print("\nВыход...")
                return

            else:
                print("\nНеверный выбор!")

        except KeyboardInterrupt:
            print("\n\nПрервано пользователем")

    print()


if __name__ == "__main__":
    main()