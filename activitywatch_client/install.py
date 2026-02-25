#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Универсальный установщик ActivityWatch + синхронизатор.
Поддерживает Linux (systemd) и Windows (планировщик задач).
Запуск: python install.py
"""

import os
import sys
import subprocess
import shutil
import time
import platform
import ctypes  # для проверки прав администратора
from pathlib import Path

# ------------------------------------------------------------
# Проверка прав администратора (только для Windows)
# ------------------------------------------------------------
def is_admin():
    """Проверяет, запущен ли скрипт с правами администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапускает скрипт с правами администратора"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

# ------------------------------------------------------------
# 1. Конфигурация (общая)
# ------------------------------------------------------------
SYSTEM = platform.system()

# Для Windows проверяем права администратора до начала установки
if SYSTEM == "Windows":
    if not is_admin():
        print("🔐 Запрос прав администратора для создания задачи в планировщике...")
        run_as_admin()
        sys.exit(0)  # Этот экземпляр завершится, новый запустится с правами

# Базовые директории (зависят от ОС)
if SYSTEM == "Windows":
    BASE_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    INSTALL_DIR = BASE_DIR / "activitywatch-manager"
    VENV_DIR = BASE_DIR / "activitywatch-manager-venv"
    LOG_DIR = Path.home() / ".activitywatch"
    PYTHON_EXE = VENV_DIR / "Scripts" / "python.exe"
    PIP_EXE = VENV_DIR / "Scripts" / "pip.exe"
elif SYSTEM == "Darwin":
    BASE_DIR = Path.home() / "Library/Application Support"
    INSTALL_DIR = BASE_DIR / "activitywatch-manager"
    VENV_DIR = BASE_DIR / "activitywatch-manager-venv"
    LOG_DIR = Path.home() / ".activitywatch"
    PYTHON_EXE = VENV_DIR / "bin" / "python"
    PIP_EXE = VENV_DIR / "bin" / "pip"
else:  # Linux
    BASE_DIR = Path.home() / ".local/share"
    INSTALL_DIR = BASE_DIR / "activitywatch-manager"
    VENV_DIR = BASE_DIR / "activitywatch-manager-venv"
    LOG_DIR = Path.home() / ".activitywatch"
    PYTHON_EXE = VENV_DIR / "bin" / "python"
    PIP_EXE = VENV_DIR / "bin" / "pip"

LOG_FILE = LOG_DIR / "install.log"

# Создаём необходимые директории
INSTALL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 2. Логирование
# ------------------------------------------------------------
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
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
    count = 0
    for item in current_dir.glob("*.py"):
        if item.name == "install.py":
            continue
        shutil.copy2(item, INSTALL_DIR / item.name)
        count += 1
        logger.debug(f"Скопирован {item.name}")
    
    # Копируем .sh, если есть (только для Linux)
    if SYSTEM == "Linux":
        for item in current_dir.glob("*.sh"):
            shutil.copy2(item, INSTALL_DIR / item.name)
            count += 1
    
    logger.info(f"Скопировано {count} файлов.")

# ------------------------------------------------------------
# 4. Создание виртуального окружения и установка зависимостей
# ------------------------------------------------------------
def setup_venv():
    """Создаёт venv и устанавливает requests, psutil."""
    logger.info("Настройка виртуального окружения...")
    
    # Проверяем, существует ли уже venv
    venv_exists = VENV_DIR.exists()
    
    if not venv_exists:
        try:
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True, capture_output=True)
            logger.info("Виртуальное окружение создано.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Не удалось создать виртуальное окружение: {e}")
            return False
    else:
        logger.info("Виртуальное окружение уже существует.")

    # Проверяем, что pip работает
    try:
        # Обновляем pip (игнорируем ошибки)
        subprocess.run([str(PIP_EXE), "install", "--upgrade", "pip"], 
                      capture_output=True, timeout=60, check=False)
        
        # Устанавливаем зависимости
        logger.info("Установка зависимостей (requests, psutil)...")
        result = subprocess.run([str(PIP_EXE), "install", "requests", "psutil"], 
                               capture_output=True, text=True, timeout=120, check=False)
        
        if result.returncode != 0:
            logger.error(f"Ошибка установки зависимостей: {result.stderr}")
            return False
            
        logger.info("Зависимости установлены.")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Таймаут при установке зависимостей")
        return False
    except Exception as e:
        logger.error(f"Ошибка при установке зависимостей: {e}")
        return False

# ------------------------------------------------------------
# 5. Проверка доступности модулей в venv
# ------------------------------------------------------------
def check_module_available(module_name):
    """Проверяет, доступен ли модуль в виртуальном окружении."""
    try:
        cmd = [
            str(PYTHON_EXE), 
            "-c", 
            f"import {module_name}; print('OK')"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0 and "OK" in result.stdout
    except:
        return False

# ------------------------------------------------------------
# 6. Регистрация устройства (вызов security)
# ------------------------------------------------------------
def register_device():
    """Запускает регистрацию устройства (если нужно)."""
    logger.info("Проверка регистрации устройства...")
    
    # Проверяем, что psutil доступен
    if not check_module_available("psutil"):
        logger.warning("Модуль psutil не доступен в виртуальном окружении. Регистрация отложена.")
        logger.info(f"Вы сможете зарегистрировать устройство позже командой:")
        logger.info(f'  "{PYTHON_EXE}" "{INSTALL_DIR / "security.py"}"')
        return False
    
    try:
        # Добавляем путь к INSTALL_DIR в PYTHONPATH
        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{INSTALL_DIR}{os.pathsep}{pythonpath}"
        
        # Запускаем регистрацию через security.py напрямую
        cmd = [str(PYTHON_EXE), "-c", "from security import SecurityToken; SecurityToken().register_device()"]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info("Устройство успешно зарегистрировано.")
            return True
        else:
            logger.warning(f"Регистрация не удалась: {result.stderr}")
            logger.info("Вы сможете зарегистрировать устройство позже вручную.")
            return False
            
    except subprocess.TimeoutExpired:
        logger.warning("Таймаут при регистрации")
        return False
    except Exception as e:
        logger.warning(f"Ошибка при регистрации: {e}")
        return False

# ------------------------------------------------------------
# 7. Установка/проверка ActivityWatch (Linux)
# ------------------------------------------------------------
def setup_activitywatch_linux():
    """Проверяет/устанавливает ActivityWatch через менеджер (только Linux)."""
    logger.info("Проверка/установка ActivityWatch...")
    
    try:
        # Добавляем путь к INSTALL_DIR
        sys.path.insert(0, str(INSTALL_DIR))
        from manager import ActivityWatchManager
        
        manager = ActivityWatchManager()
        # Передаём путь к python из venv для использования в сервисах
        manager.python_path = str(PYTHON_EXE)
        
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
            manager.start_activitywatch()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при настройке ActivityWatch: {e}")
        return False
# ------------------------------------------------------------
# 7b. Установка/проверка ActivityWatch (macOS)
# ------------------------------------------------------------
def setup_activitywatch_macos():
    """Проверяет/устанавливает ActivityWatch через менеджер (только macOS)."""
    logger.info("Проверка/установка ActivityWatch...")
    
    try:
        # Добавляем путь к INSTALL_DIR в sys.path для импорта manager
        sys.path.insert(0, str(INSTALL_DIR))
        from manager import ActivityWatchManager
        
        manager = ActivityWatchManager()
        # Передаём путь к python из venv для использования в сервисах
        manager.python_path = str(PYTHON_EXE)
        
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
            manager.start_activitywatch()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при настройке ActivityWatch: {e}")
        return False
# ------------------------------------------------------------
# 8. Настройка автозапуска для Linux (systemd)
# ------------------------------------------------------------
def setup_autostart_linux():
    """Создаёт systemd-сервисы для ActivityWatch и синхронизатора."""
    logger.info("Настройка автозапуска для Linux...")

    AW_DIR = Path.home() / ".local/share/activitywatch"
    systemd_dir = Path.home() / ".config/systemd/user"
    systemd_dir.mkdir(parents=True, exist_ok=True)

    # Проверяем наличие компонентов
    aw_server = AW_DIR / "aw-server/aw-server"
    aw_watcher_window = AW_DIR / "aw-watcher-window/aw-watcher-window"
    aw_watcher_afk = AW_DIR / "aw-watcher-afk/aw-watcher-afk"

    if not aw_server.exists():
        logger.error(f"aw-server не найден в {aw_server}")
        return False

    # Создаём скрипт запуска всех компонентов
    start_script = AW_DIR / "start-all.sh"
    start_script.write_text(f"""#!/bin/bash
cd {AW_DIR}
# Запускаем сервер
{aw_server} &
SERVER_PID=$!
sleep 15
# Запускаем вотчеры
{aw_watcher_window} --host localhost --port 5600 &
{aw_watcher_afk} --host localhost --port 5600 &
wait $SERVER_PID
""")
    start_script.chmod(0o755)

    # Сервис ActivityWatch
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
# Для Wayland эти переменные могут не помочь, но оставим

[Install]
WantedBy=default.target
""")

    # Сервис синхронизатора
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
ExecStart={PYTHON_EXE} {INSTALL_DIR}/run_sync_service.py
Restart=on-failure
RestartSec=30
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
""")

    # Таймер (опционально)
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

    try:
        # Перезагружаем systemd
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=30)

        # Включаем сервисы
        for name in ["activitywatch.service", "activitywatch-sync.service", "activitywatch-sync.timer"]:
            subprocess.run(["systemctl", "--user", "enable", name], capture_output=True, timeout=30)

        # Включаем linger
        user = os.environ.get("USER", os.environ.get("LOGNAME"))
        subprocess.run(["loginctl", "enable-linger", user], capture_output=True, timeout=30)

        # Запускаем сейчас
        subprocess.run(["systemctl", "--user", "start", "activitywatch.service"], timeout=30)
        logger.info("Linux-сервисы созданы и запущены.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при настройке systemd: {e}")
        return False

# ------------------------------------------------------------
# 9. Настройка автозапуска для Windows (планировщик задач)
# ------------------------------------------------------------
def setup_autostart_windows():
    """Создаёт задачу в планировщике Windows для запуска синхронизатора при входе."""
    logger.info("Настройка автозапуска для Windows...")

    python_exe = PYTHON_EXE
    sync_script = INSTALL_DIR / "run_sync_service.py"

    if not python_exe.exists():
        logger.error(f"Интерпретатор не найден: {python_exe}")
        return False
    if not sync_script.exists():
        logger.error(f"Скрипт синхронизации не найден: {sync_script}")
        return False

    task_name = "ActivityWatchSync"
    username = os.environ.get("USERNAME", os.environ.get("USER"))

    # Удаляем старую задачу, если есть (игнорируем ошибки)
    subprocess.run(f'schtasks /delete /tn "{task_name}" /f', 
                   shell=True, capture_output=True, timeout=30)

    # Создаём задачу при входе пользователя
    cmd = (
        f'schtasks /create /tn "{task_name}" '
        f'/tr "\'{python_exe}\' \'{sync_script}\'" '
        f'/sc onlogon /ru "{username}" /rl highest /f'
    )
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                                timeout=60, encoding='cp866', errors='ignore')

        if result.returncode == 0:
            logger.info("Задача в планировщике успешно создана.")
            
            # Пытаемся запустить задачу сейчас (опционально)
            try:
                subprocess.run(f'schtasks /run /tn "{task_name}"', 
                             shell=True, capture_output=True, timeout=30)
            except:
                pass
            return True
        else:
            error_msg = result.stderr or "Неизвестная ошибка"
            logger.error(f"Ошибка создания задачи: {error_msg}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Таймаут при создании задачи")
        return False
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {e}")
        return False
# ------------------------------------------------------------
# 9b. Настройка автозапуска для macOS (launchd)
# ------------------------------------------------------------
def setup_autostart_macos():
    """Создаёт агенты launchd для ActivityWatch и синхронизатора."""
    logger.info("Настройка автозапуска для macOS...")

    # Директория для агентов launchd
    launch_agents_dir = Path.home() / "Library/LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)

    # Импортируем менеджер для поиска компонентов
    sys.path.insert(0, str(INSTALL_DIR))
    from manager import ActivityWatchManager
    manager = ActivityWatchManager()

    # --------------------------------------------------------
    # 1. Создание скрипта запуска ActivityWatch (все компоненты)
    # --------------------------------------------------------
    aw_script = INSTALL_DIR / "run_activitywatch_macos.sh"
    
    # Находим пути к компонентам
    aw_server = manager._find_component("aw-server")
    aw_watcher_window = manager._find_component("aw-watcher-window")
    aw_watcher_afk = manager._find_component("aw-watcher-afk")
    
    if not aw_server:
        logger.error("aw-server не найден. Убедитесь, что ActivityWatch установлен корректно.")
        return False

    # Формируем скрипт запуска (аналогично Linux)
    script_content = f"""#!/bin/bash
# Скрипт запуска ActivityWatch (macOS)
cd {INSTALL_DIR}

# Запускаем сервер
"{aw_server}" &
SERVER_PID=$!

sleep 10

# Запускаем вотчеры, если они есть
if [ -f "{aw_watcher_window}" ]; then
    "{aw_watcher_window}" &
fi
if [ -f "{aw_watcher_afk}" ]; then
    "{aw_watcher_afk}" &
fi

# Ждём завершения сервера (никогда не завершается)
wait $SERVER_PID
"""
    with open(aw_script, "w") as f:
        f.write(script_content)
    aw_script.chmod(0o755)
    logger.info(f"Создан скрипт запуска ActivityWatch: {aw_script}")

    # --------------------------------------------------------
    # 2. Создание plist для ActivityWatch
    # --------------------------------------------------------
    aw_plist = launch_agents_dir / "local.activitywatch.plist"
    aw_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>local.activitywatch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{aw_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{LOG_DIR}/activitywatch_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{LOG_DIR}/activitywatch_stderr.log</string>
</dict>
</plist>"""
    with open(aw_plist, "w") as f:
        f.write(aw_plist_content)
    logger.info(f"Создан plist для ActivityWatch: {aw_plist}")

    # --------------------------------------------------------
    # 3. Создание plist для синхронизатора
    # --------------------------------------------------------
    sync_plist = launch_agents_dir / "local.activitywatch-sync.plist"
    sync_script = INSTALL_DIR / "run_sync_service.py"
    if not sync_script.exists():
        logger.error(f"Скрипт синхронизации не найден: {sync_script}")
        return False

    sync_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>local.activitywatch-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_EXE}</string>
        <string>{sync_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{LOG_DIR}/sync_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{LOG_DIR}/sync_stderr.log</string>
</dict>
</plist>"""
    with open(sync_plist, "w") as f:
        f.write(sync_plist_content)
    logger.info(f"Создан plist для синхронизатора: {sync_plist}")

    # --------------------------------------------------------
    # 4. Загрузка агентов в launchd
    # --------------------------------------------------------
    try:
        # Выгружаем, если уже загружены (игнорируем ошибки)
        subprocess.run(["launchctl", "unload", str(aw_plist)], capture_output=True)
        subprocess.run(["launchctl", "unload", str(sync_plist)], capture_output=True)

        # Загружаем с флагом -w (постоянная загрузка)
        subprocess.run(["launchctl", "load", "-w", str(aw_plist)], check=True)
        subprocess.run(["launchctl", "load", "-w", str(sync_plist)], check=True)

        logger.info("Агенты launchd успешно загружены.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка загрузки агентов launchd: {e}")
        return False
# ------------------------------------------------------------
# 10. Создание вспомогательных скриптов
# ------------------------------------------------------------
def create_helper_scripts():
    """Создаёт скрипты для проверки статуса."""
    if SYSTEM == "Linux":
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

    elif SYSTEM == "Windows":
        check_bat = Path.home() / "check_activitywatch.bat"
        check_bat.write_text(f"""\
        @echo off
        echo === ActivityWatch Status ===
        echo.
        echo 1. Задача в планировщике:
        schtasks /query /tn ActivityWatchSync 2>nul
        if %errorlevel% neq 0 echo Задача не найдена
        echo.
        echo 2. ActivityWatch API (требуется curl):
        curl -s http://localhost:5600/api/0/info 2>nul | python -m json.tool 2>nul
        if %errorlevel% neq 0 echo ActivityWatch не отвечает
        echo.
        echo 3. Процессы:
        tasklist | findstr python
        echo.
        echo 4. Последние логи синхронизации:
        type "%USERPROFILE%\\.activitywatch\\activitywatch_sync.log" 2>nul
        """)
        logger.info(f"Создан скрипт проверки: {check_bat}")
    
    elif SYSTEM == "Darwin":
        check_script = Path.home() / "check_activitywatch.command"
        check_script.write_text(f"""\
        #!/bin/bash
        echo "=== ActivityWatch Status (macOS) ==="
        echo ""
        echo "1. Агенты launchd:"
        launchctl list | grep activitywatch
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
# 11. Проверка наличия ActivityWatch на Windows
# ------------------------------------------------------------
def check_activitywatch_windows():
    """Проверяет, установлен ли ActivityWatch на Windows."""
    logger.info("Проверка наличия ActivityWatch...")
    
    # Типичные пути установки ActivityWatch на Windows
    possible_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "activitywatch",
        Path(os.environ.get("PROGRAMFILES", "")) / "activitywatch",
        Path.home() / "AppData/Local/activitywatch",
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "aw-qt.exe").exists():
            logger.info(f"ActivityWatch найден в {path}")
            return True
    
    logger.warning("ActivityWatch не найден. Убедитесь, что он установлен.")
    logger.info("Скачать можно с: https://activitywatch.net/downloads/")
    return False

# ------------------------------------------------------------
# 12. Финальные инструкции
# ------------------------------------------------------------
def print_success():
    print("\n" + "="*70)
    print("🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
    print("="*70)
    print(f"✅ Система: {SYSTEM}")
    print("✅ Виртуальное окружение создано")
    print("✅ Файлы скопированы")
    
    if SYSTEM == "Linux":
        print("✅ Systemd сервисы настроены")
        print("✅ Автозапуск включён (linger)")
        print("\n📊 Проверить статус:")
        print("  bash ~/check_activitywatch.sh")
        print("\n📝 Логи:")
        print("  tail -f ~/.activitywatch/activitywatch_sync.log")
        print("  journalctl --user -u activitywatch-sync.service -f")
        
    elif SYSTEM == "Windows":
        print("✅ Задача в планировщике создана")
        print("\n📊 Проверить статус:")
        print("  check_activitywatch.bat (в домашней папке)")
        print("\n📝 Логи:")
        print("  type %USERPROFILE%\\.activitywatch\\activitywatch_sync.log")
    elif SYSTEM == "Darwin":
        print("✅ Агенты launchd настроены")
        print("✅ Автозапуск включён")
        print("\n📊 Проверить статус:")
        print("  open ~/check_activitywatch.command (или запустить в терминале)")
        print("\n📝 Логи:")
        print("  tail -f ~/.activitywatch/activitywatch_sync.log")
        print("  tail -f ~/.activitywatch/activitywatch_stdout.log")
    print("\n🔄 После перезагрузки всё запустится автоматически!")
    print("="*70)

# ------------------------------------------------------------
# 13. Главная функция
# ------------------------------------------------------------
def main():
    logger.info(f"=== НАЧАЛО УСТАНОВКИ на {SYSTEM} ===")
    
    try:
        # Копируем файлы проекта
        copy_project_files()
        
        # Создаём виртуальное окружение
        if not setup_venv():
            logger.error("Не удалось настроить виртуальное окружение")
            sys.exit(1)
        
        # Регистрируем устройство (если получится)
        logger.info("Попытка регистрации устройства...")
        register_device()
        
        # Действия в зависимости от ОС
        if SYSTEM == "Linux":
            # Проверяем/устанавливаем ActivityWatch
            setup_activitywatch_linux()
            
            # Настраиваем systemd
            if not setup_autostart_linux():
                logger.error("Не удалось настроить автозапуск для Linux")
                sys.exit(1)
                
        elif SYSTEM == "Windows":
            # Проверяем наличие ActivityWatch
            check_activitywatch_windows()
            
            # Настраиваем автозапуск синхронизатора
            if not setup_autostart_windows():
                logger.error("Не удалось настроить автозапуск для Windows")
                sys.exit(1)
        elif SYSTEM == "Darwin":
            # Проверяем/устанавливаем ActivityWatch
            setup_activitywatch_macos()
            
            # Настраиваем автозапуск через launchd
            if not setup_autostart_macos():
                logger.error("Не удалось настроить автозапуск для macOS")
                sys.exit(1)
        else:
            logger.error(f"Неподдерживаемая ОС: {SYSTEM}")
            sys.exit(1)
        
        # Создаём вспомогательные скрипты
        create_helper_scripts()
        
        # Финальное сообщение
        print_success()
        logger.info("=== УСТАНОВКА ЗАВЕРШЕНА ===")
        
    except KeyboardInterrupt:
        logger.info("\nУстановка прервана пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()