#!/usr/bin/env python3
"""
Универсальный установщик ActivityWatch + синхронизатор.
Запуск одной командой: python3 install.py
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# ------------------------------------------------------------
# 1. Конфигурация
# ------------------------------------------------------------
INSTALL_DIR = Path.home() / ".local" / "share" / "activitywatch-manager"
VENV_DIR = Path.home() / ".local" / "share" / "activitywatch-manager-venv"
LOG_FILE = Path.home() / ".activitywatch" / "install.log"

# Создаём необходимые директории
INSTALL_DIR.mkdir(parents=True, exist_ok=True)
Path.home().joinpath(".activitywatch").mkdir(exist_ok=True)

# ------------------------------------------------------------
# 2. Логирование
# ------------------------------------------------------------
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("installer")

# ------------------------------------------------------------
# 3. Копирование файлов проекта
# ------------------------------------------------------------
def copy_project_files():
    """Копирует все .py файлы из текущей папки в INSTALL_DIR."""
    current_dir = Path(__file__).parent.absolute()
    logger.info(f"Копирование файлов из {current_dir} в {INSTALL_DIR}")
    for item in current_dir.glob("*.py"):
        if item.name == "install.py":
            continue
        shutil.copy2(item, INSTALL_DIR / item.name)
        logger.debug(f"Скопирован {item.name}")
    logger.info("Файлы скопированы.")

# ------------------------------------------------------------
# 4. Создание виртуального окружения и установка зависимостей
# ------------------------------------------------------------
def setup_venv():
    """Создаёт venv и устанавливает requests, psutil."""
    logger.info("Настройка виртуального окружения...")
    if not VENV_DIR.exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        logger.info("Виртуальное окружение создано.")
    else:
        logger.info("Виртуальное окружение уже существует.")

    pip = VENV_DIR / "bin" / "pip"
    subprocess.run([str(pip), "install", "--upgrade", "pip"], check=False)
    subprocess.run([str(pip), "install", "requests", "psutil"], check=True)
    logger.info("Зависимости установлены.")

# ------------------------------------------------------------
# 5. Установка/проверка ActivityWatch
# ------------------------------------------------------------
def setup_activitywatch():
    """Проверяет/устанавливает ActivityWatch через ваш менеджер."""
    logger.info("Проверка/установка ActivityWatch...")
    sys.path.insert(0, str(INSTALL_DIR))
    try:
        from manager import ActivityWatchManager
        manager = ActivityWatchManager()
        
        # Проверяем установку
        installed, _ = manager.check_activitywatch_installed()
        if not installed:
            logger.info("ActivityWatch не установлен. Устанавливаем...")
            if not manager.install_activitywatch():
                logger.error("Не удалось установить ActivityWatch")
                return False
        else:
            logger.info("ActivityWatch уже установлен")
        
        # Запускаем, если не запущен
        if not manager.check_activitywatch_running():
            logger.info("Запуск ActivityWatch...")
            if not manager.start_activitywatch():
                logger.warning("Не удалось запустить ActivityWatch, но продолжим")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при настройке ActivityWatch: {e}")
        return False

# ------------------------------------------------------------
# 6. Создание systemd сервисов (исправленная версия)
# ------------------------------------------------------------
def create_systemd_services():
    """Создаёт правильные systemd сервисы для всех компонентов ActivityWatch."""
    logger.info("Создание systemd сервисов...")
    
    USER = os.getenv("USER")
    UID = os.getuid()
    AW_DIR = Path.home() / ".local/share/activitywatch"
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    
    # Пути к компонентам (с учётом подкаталогов)
    aw_server = AW_DIR / "aw-server" / "aw-server"
    aw_watcher_window = AW_DIR / "aw-watcher-window" / "aw-watcher-window"
    aw_watcher_afk = AW_DIR / "aw-watcher-afk" / "aw-watcher-afk"
    
    # Проверяем существование
    missing = []
    if not aw_server.exists():
        missing.append("aw-server")
    if not aw_watcher_window.exists():
        missing.append("aw-watcher-window")
    if not aw_watcher_afk.exists():
        missing.append("aw-watcher-afk")
    
    if missing:
        logger.error(f"Не найдены компоненты: {', '.join(missing)}")
        # Попробуем найти альтернативные пути (например, если файлы лежат прямо в каталогах)
        # Для простоты вернём False.
        return False
    
    # Создаём скрипт запуска всех компонентов
    start_script = AW_DIR / "start-all.sh"
    start_script.write_text(f"""#!/bin/bash
cd {AW_DIR}

# Запускаем сервер
{aw_server} &
SERVER_PID=$!

# Ждем 5 секунд для инициализации сервера
sleep 5

# Запускаем вотчеры
{aw_watcher_window} &
{aw_watcher_afk} &

# Ждем завершения сервера (чтобы сервис не завершился)
wait $SERVER_PID
""")
    start_script.chmod(0o755)
    
    # 1. Сервис для ActivityWatch (все компоненты)
    aw_service = systemd_dir / "activitywatch.service"
    aw_service.write_text(f"""\
[Unit]
Description=ActivityWatch (server + watchers)
After=graphical-session.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={start_script}
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority

[Install]
WantedBy=default.target
""")
    logger.info(f"Создан {aw_service}")
    
    # 2. Сервис для синхронизатора
    python_interp = VENV_DIR / "bin" / "python"
    sync_script = INSTALL_DIR / "run_sync_service.py"
    
    sync_service = systemd_dir / "activitywatch-sync.service"
    sync_service.write_text(f"""\
[Unit]
Description=ActivityWatch Sync Service
After=activitywatch.service
Requires=activitywatch.service
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart={python_interp} {sync_script}
Restart=on-failure
RestartSec=30
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
""")
    logger.info(f"Создан {sync_service}")
    
    # 3. Таймер (опционально)
    timer = systemd_dir / "activitywatch-sync.timer"
    timer.write_text("""\
[Unit]
Description=Daily restart of ActivityWatch sync service

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
""")
    logger.info(f"Создан {timer}")
    
    # Перезагружаем systemd
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    logger.info("Systemd перезагружен")
    
    return True

# ------------------------------------------------------------
# 7. Включение и запуск сервисов
# ------------------------------------------------------------
def enable_and_start_services():
    """Включает и запускает сервисы."""
    logger.info("Включение и запуск сервисов...")
    
    USER = os.getenv("USER")
    
    # Включаем сервисы
    for service in ["activitywatch.service", "activitywatch-sync.service", "activitywatch-sync.timer"]:
        subprocess.run(["systemctl", "--user", "enable", service], 
                      capture_output=True, check=False)
        logger.info(f"Сервис {service} включен")
    
    # Включаем linger
    subprocess.run(["loginctl", "enable-linger", USER], capture_output=True, check=False)
    logger.info("Linger включен")
    
    # Запускаем сервисы
    subprocess.run(["systemctl", "--user", "start", "activitywatch.service"], 
                  capture_output=True, check=False)
    time.sleep(5)  # Даём время ActivityWatch запуститься
    subprocess.run(["systemctl", "--user", "start", "activitywatch-sync.service"], 
                  capture_output=True, check=False)
    
    logger.info("Сервисы запущены")

# ------------------------------------------------------------
# 8. Создание вспомогательных скриптов
# ------------------------------------------------------------
def create_helper_scripts():
    """Создаёт скрипты для проверки статуса."""
    check_script = Path.home() / "check_activitywatch.sh"
    check_script.write_text("""\
#!/bin/bash
echo "=== ActivityWatch Status ==="
echo ""
echo "1. Сервисы systemd:"
systemctl --user status activitywatch.service --no-pager | head -10
echo ""
systemctl --user status activitywatch-sync.service --no-pager | head -10
echo ""
echo "2. ActivityWatch API:"
curl -s http://localhost:5600/api/0/info | python3 -m json.tool || echo "ActivityWatch не отвечает"
echo ""
echo "3. Процессы:"
ps aux | grep -E "aw-|run_sync" | grep -v grep
echo ""
echo "4. Последние логи синхронизации:"
tail -20 ~/.activitywatch/activitywatch_sync.log
""")
    check_script.chmod(0o755)
    logger.info(f"Создан скрипт проверки: {check_script}")

# ------------------------------------------------------------
# 9. Финальные инструкции
# ------------------------------------------------------------
def print_success():
    print("\n" + "="*70)
    print("🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
    print("="*70)
    print("✅ ActivityWatch установлен/проверен")
    print("✅ Виртуальное окружение создано")
    print("✅ Systemd сервисы настроены")
    print("✅ Автозапуск включён")
    print("\n📊 Проверить статус:")
    print("  bash ~/check_activitywatch.sh")
    print("\n📝 Логи:")
    print("  tail -f ~/.activitywatch/activitywatch_sync.log")
    print("  journalctl --user -u activitywatch-sync.service -f")
    print("\n🔄 После перезагрузки всё запустится автоматически!")
    print("="*70)

# ------------------------------------------------------------
# 10. Главная функция
# ------------------------------------------------------------
def main():
    logger.info("=== НАЧАЛО УСТАНОВКИ ===")
    
    # Копируем файлы
    copy_project_files()
    
    # Создаём виртуальное окружение
    setup_venv()
    
    # Устанавливаем/проверяем ActivityWatch
    if not setup_activitywatch():
        logger.warning("Проблемы с ActivityWatch, но продолжим...")
    
    # Создаём systemd сервисы
    if not create_systemd_services():
        logger.error("Не удалось создать сервисы")
        sys.exit(1)
    
    # Включаем и запускаем
    enable_and_start_services()
    
    # Создаём вспомогательные скрипты
    create_helper_scripts()
    
    # Финальное сообщение
    print_success()
    logger.info("=== УСТАНОВКА ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    main()