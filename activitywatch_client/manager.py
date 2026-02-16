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

import os


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
class ActivityWatchManager:
    """Менеджер для установки и управления ActivityWatch"""

    # URL для скачивания (версия 0.13.2)
    DOWNLOAD_URLS = {
        "Windows": "https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-windows-x86_64-setup.exe",
        "Darwin": "https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-macos-x86_64.dmg",
        "Linux": "https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-linux-x86_64.zip",
    }

    def __init__(self):
        """Инициализация менеджера"""
        self.system = platform.system()
        self.machine = platform.machine()
        self.download_dir = Path(tempfile.gettempdir()) / "activitywatch_install"
        self.download_dir.mkdir(exist_ok=True)

        # Пути установки по умолчанию
        self.install_paths = {
            "Windows": Path(os.environ.get("LOCALAPPDATA", "")) / "activitywatch",
            "Darwin": Path.home() / "Applications" / "activitywatch",
            "Linux": Path.home() / ".local" / "share" / "activitywatch",
        }

        self.install_path = self.install_paths.get(
            self.system, Path.home() / "activitywatch"
        )
        self.python_path = sys.executable

    def check_activitywatch_installed(self) -> Tuple[bool, Optional[Path]]:
        """
        Проверяет, установлен ли ActivityWatch.

        Returns:
            Tuple[bool, Optional[Path]]: (Установлен ли, путь к исполняемому файлу)
        """
        logger.info(f"Проверка установки ActivityWatch на {self.system}")

        # Проверяем различные возможные пути
        possible_paths = []

        if self.system == "Windows":
            possible_paths = [
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "activitywatch"
                / "aw-server.exe",
                Path(os.environ.get("PROGRAMFILES", ""))
                / "activitywatch"
                / "aw-server.exe",
                Path.home() / "AppData" / "Local" / "activitywatch" / "aw-server.exe",
            ]
            # Также проверяем в PATH
            try:
                result = subprocess.run(
                    ["where", "aw-server"], capture_output=True, text=True, shell=True
                )
                if result.returncode == 0:
                    possible_paths.append(Path(result.stdout.strip()))
            except:
                pass

        elif self.system == "Darwin":
            possible_paths = [
                Path("/Applications/activitywatch.app/Contents/MacOS/aw-server"),
                Path.home()
                / "Applications"
                / "activitywatch.app"
                / "Contents"
                / "MacOS"
                / "aw-server",
                Path.home() / ".local" / "bin" / "aw-server",
            ]
            # Проверяем через which
            try:
                result = subprocess.run(
                    ["which", "aw-server"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    possible_paths.append(Path(result.stdout.strip()))
            except:
                pass

        elif self.system == "Linux":
            possible_paths = [
                Path("/usr/local/bin/aw-server"),
                Path("/usr/bin/aw-server"),
                Path.home() / ".local" / "bin" / "aw-server",
                Path.home() / "activitywatch" / "aw-server",
                self.install_path / "aw-server",  # Основной путь установки
            ]

            # Также рекурсивно ищем в install_path
            if self.install_path.exists():
                # Ищем aw-server в установочной директории и поддиректориях
                found_servers = list(self.install_path.rglob("aw-server"))
                possible_paths.extend(found_servers)

            # Проверяем через which
            try:
                result = subprocess.run(
                    ["which", "aw-server"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    possible_paths.append(Path(result.stdout.strip()))
            except:
                pass

        # Проверяем все возможные пути
        for path in possible_paths:
            if path and path.exists():
                logger.info(f"ActivityWatch найден: {path}")
                return True, path

        logger.info("ActivityWatch не найден")
        return False, None

    def check_activitywatch_running(self) -> bool:
        """
        Проверяет, запущен ли ActivityWatch.

        Returns:
            bool: True если запущен, иначе False
        """
        logger.info("Проверка запущен ли ActivityWatch...")

        try:
            # Пробуем подключиться к API
            response = requests.get("http://localhost:5600/api/0/info", timeout=3)
            if response.status_code == 200:
                logger.info("ActivityWatch запущен и доступен")
                return True
        except requests.RequestException:
            pass

        # Альтернативная проверка через процессы
        try:
            if self.system == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq aw-server.exe"],
                    capture_output=True,
                    text=True,
                    shell=True,
                )
                return "aw-server.exe" in result.stdout
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "aw-server"], capture_output=True, text=True
                )
                return result.returncode == 0
        except:
            pass

        logger.info("ActivityWatch не запущен")
        return False

    def download_activitywatch(self) -> Optional[Path]:
        """
        Скачивает ActivityWatch для текущей платформы.

        Returns:
            Optional[Path]: Путь к скачанному файлу или None при ошибке
        """
        url = self.DOWNLOAD_URLS.get(self.system)
        if not url:
            logger.error(f"Не поддерживаемая платформа: {self.system}")
            return None

        filename = url.split("/")[-1]
        download_path = self.download_dir / filename

        logger.info(f"Скачивание ActivityWatch для {self.system}...")
        logger.info(f"URL: {url}")
        logger.info(f"Сохраняю в: {download_path}")

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
    
                           

            logger.info(f"Скачивание завершено: {download_path}")
            return download_path

        except requests.RequestException as e:
            logger.error(f"Ошибка скачивания: {e}")
            return None

    def install_windows(self, installer_path: Path) -> bool:
        """
        Устанавливает ActivityWatch на Windows.

        Args:
            installer_path: Путь к установщику .exe

        Returns:
            bool: True если установка успешна, иначе False
        """
        logger.info("Установка ActivityWatch на Windows...")

        try:
            # Используем тихую установку
            cmd = [str(installer_path), "/S", "/D=" + str(self.install_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                logger.info("Установка на Windows завершена успешно")
                return True
            else:
                logger.error(f"Ошибка установки: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Таймаут установки")
            return False
        except Exception as e:
            logger.error(f"Ошибка при установке: {e}")
            return False

    def install_macos(self, dmg_path: Path) -> bool:
        """
        Устанавливает ActivityWatch на macOS.

        Args:
            dmg_path: Путь к файлу .dmg

        Returns:
            bool: True если установка успешна, иначе False
        """
        logger.info("Установка ActivityWatch на macOS...")

        try:
            # Монтируем DMG
            mount_cmd = ["hdiutil", "attach", str(dmg_path)]
            result = subprocess.run(mount_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Ошибка монтирования DMG: {result.stderr}")
                return False

            # Ищем смонтированный том
            for line in result.stdout.split("\n"):
                if "/Volumes/" in line and "activitywatch" in line.lower():
                    parts = line.split("\t")
                    if len(parts) > 1:
                        mount_point = parts[-1].strip()
                        break

            if not "mount_point" in locals():
                logger.error("Не найден смонтированный том ActivityWatch")
                return False

            # Копируем приложение
            app_source = Path(mount_point) / "activitywatch.app"
            app_dest = Path("/Applications") / "activitywatch.app"

            if app_dest.exists():
                shutil.rmtree(app_dest)

            shutil.copytree(app_source, app_dest)

            # Отмонтируем DMG
            subprocess.run(
                ["hdiutil", "detach", mount_point], capture_output=True, text=True
            )

            # Устанавливаем права
            subprocess.run(["chmod", "+x", str(app_dest / "Contents" / "MacOS" / "*")])

            logger.info("Установка на macOS завершена успешно")
            return True

        except Exception as e:
            logger.error(f"Ошибка при установке на macOS: {e}")
            return False

    def install_linux(self, zip_path: Path) -> bool:
        """
        Устанавливает ActivityWatch на Linux.
        """
        logger.info("Установка ActivityWatch на Linux...")

        try:
            # Создаем директорию для установки
            self.install_path.mkdir(parents=True, exist_ok=True)
            
            # Очищаем директорию, если что-то уже есть
            for item in self.install_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

            # Распаковываем архив
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Получаем список всех файлов в архиве
                all_files = zip_ref.namelist()
                
                # Находим корневую папку (первый элемент пути)
                root_dirs = set()
                for file in all_files:
                    parts = file.split('/')
                    if len(parts) > 1:
                        root_dirs.add(parts[0])
                
                # Извлекаем файлы
                zip_ref.extractall(self.install_path)
                
            logger.info(f"Структура установки: {list(self.install_path.iterdir())}")
            
            # ФИКС: Проверяем, не распаковался ли архив во вложенную папку
            items = list(self.install_path.iterdir())
            
            # Если только одна папка и она называется "activitywatch" или начинается с "activitywatch-"
            if len(items) == 1 and items[0].is_dir() and (
                items[0].name == "activitywatch" or 
                items[0].name.startswith("activitywatch-")
            ):
                logger.info(f"Обнаружена вложенная папка {items[0].name}. Исправляем структуру...")
                nested_dir = items[0]
                
                # Перемещаем все файлы из вложенной папки на уровень выше
                for item in nested_dir.iterdir():
                    target_path = self.install_path / item.name
                    if target_path.exists():
                        if target_path.is_dir():
                            shutil.rmtree(target_path)
                        else:
                            target_path.unlink()
                    shutil.move(str(item), str(self.install_path))
                
                # Удаляем пустую вложенную папку
                nested_dir.rmdir()
                
                logger.info("Структура исправлена")

            # После исправления структуры, снова показываем содержимое
            logger.info(f"Исправленная структура: {list(self.install_path.iterdir())}")
            
            # Ищем компоненты ActivityWatch
            components = {
                "server": self._find_component("aw-server"),
                "window_watcher": self._find_component("aw-watcher-window"),
                "afk_watcher": self._find_component("aw-watcher-afk"),
                "qt": self._find_component("aw-qt"),
            }

            # Устанавливаем права на выполнение
            for name, component_path in components.items():
                if component_path and component_path.exists():
                    # Если это директория, ищем исполняемый файл внутри
                    if component_path.is_dir():
                        # Ищем файл с таким же именем внутри директории
                        exe_file = component_path / component_path.name
                        if exe_file.exists():
                            component_path = exe_file
                        else:
                            # Ищем любой исполняемый файл
                            for file in component_path.iterdir():
                                if file.is_file() and os.access(file, os.X_OK):
                                    component_path = file
                                    break
                    
                    # Устанавливаем права
                    try:
                        component_path.chmod(0o755)
                        logger.info(f"Установлены права для {name}: {component_path}")
                        components[name] = component_path  # Обновляем путь
                    except Exception as e:
                        logger.warning(f"Не удалось установить права для {component_path}: {e}")
                else:
                    logger.warning(f"Не найден компонент {name}")

            # Создаем симлинки в ~/.local/bin
            local_bin = Path.home() / ".local" / "bin"
            local_bin.mkdir(parents=True, exist_ok=True)

            symlinks_created = 0
            for name, component_path in components.items():
                if component_path and component_path.exists() and component_path.is_file():
                    # Определяем имя для симлинка
                    if "server" in name:
                        symlink_name = "aw-server"
                    elif "window" in name:
                        symlink_name = "aw-watcher-window"
                    elif "afk" in name:
                        symlink_name = "aw-watcher-afk"
                    elif "qt" in name:
                        symlink_name = "aw-qt"
                    else:
                        continue

                    symlink_path = local_bin / symlink_name
                    
                    # Удаляем старый симлинк, если существует
                    if symlink_path.exists():
                        symlink_path.unlink()
                    
                    # Создаем симлинк на абсолютный путь
                    try:
                        abs_path = component_path.absolute()
                        symlink_path.symlink_to(abs_path)
                        logger.info(f"Создан симлинк: {symlink_path} -> {abs_path}")
                        symlinks_created += 1
                    except Exception as e:
                        logger.error(f"Ошибка создания симлинка {symlink_name}: {e}")

            if symlinks_created == 0:
                logger.error("Не удалось создать ни одного симлинка!")
                # Но не прерываем установку - может быть, симлинки не нужны
                
            logger.info("Установка на Linux завершена успешно")
            return True

        except Exception as e:
            logger.error(f"Ошибка при установке на Linux: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def install_activitywatch(self) -> bool:
        """
        Скачивает и устанавливает ActivityWatch.

        Returns:
            bool: True если установка успешна, иначе False
        """
        logger.info(f"Начинаем установку ActivityWatch для {self.system}")

        # Скачиваем
        installer_path = self.download_activitywatch()
        if not installer_path:
            return False

        # Устанавливаем в зависимости от платформы
        if self.system == "Windows":
            return self.install_windows(installer_path)
        elif self.system == "Darwin":
            return self.install_macos(installer_path)
        elif self.system == "Linux":
            return self.install_linux(installer_path)
        else:
            logger.error(f"Неподдерживаемая платформа: {self.system}")
            return False

    def _find_component(self, component_name: str) -> Optional[Path]:
        """
        Находит компонент ActivityWatch в установленной структуре.

        Args:
            component_name: Имя компонента (aw-server, aw-watcher-window, etc.)

        Returns:
            Path: Путь к исполняемому файлу компонента
        """
        # Ищем сначала в корне установки
        if (self.install_path / component_name).exists():
            path = self.install_path / component_name
            # Если это файл и он исполняемый (или хотя бы файл)
            if path.is_file() or (path.is_file() and os.access(path, os.X_OK)):
                return path
            # Если это директория, ищем внутри файл с тем же именем
            elif path.is_dir():
                # Вариант 1: файл с тем же именем внутри папки
                exe_file = path / path.name
                if exe_file.exists() and exe_file.is_file():
                    return exe_file
                
                # Вариант 2: любой исполняемый файл в папке
                for item in path.iterdir():
                    if item.is_file() and (os.access(item, os.X_OK) or item.name == component_name):
                        return item
        
        # Ищем в других возможных местах (старая структура)
        search_paths = [
            # Новая структура: файлы в корне
            self.install_path / component_name,
            # Старая структура: папка с компонентом, внутри файл
            self.install_path / component_name / component_name,
            # Возможно в activitywatch подпапке
            self.install_path / "activitywatch" / component_name,
            self.install_path / "activitywatch" / component_name / component_name,
        ]
        
        for path in search_paths:
            if path.exists():
                if path.is_dir():
                    # В папке ищем файл с именем папки
                    exe_file = path / path.name
                    if exe_file.exists():
                        return exe_file
                    
                    # Или любой исполняемый файл
                    for item in path.iterdir():
                        if item.is_file() and (os.access(item, os.X_OK) or item.name == component_name):
                            return item
                elif path.is_file():
                    return path
        
        # Рекурсивный поиск по всей директории
        logger.info(f"Рекурсивный поиск {component_name} в {self.install_path}")
        for item in self.install_path.rglob("*"):
            if item.is_file():
                # Проверяем имя файла (без расширения)
                if item.stem == component_name or item.name == component_name:
                    return item
                # Или если в имени содержится component_name
                elif component_name in item.name:
                    return item
        
        return None
    def start_activitywatch(self) -> bool:
        """
        Запускает ActivityWatch.
        """
        logger.info("Запуск ActivityWatch...")

        try:
            # Запускаем каждый компонент в его собственной директории
            components = {
                "aw-server": self._find_component("aw-server"),
                "aw-watcher-window": self._find_component("aw-watcher-window"),
                "aw-watcher-afk": self._find_component("aw-watcher-afk"),
            }

            processes = []

            for name, component_path in components.items():
                if not component_path or not component_path.exists():
                    logger.warning(f"Компонент {name} не найден")
                    continue

                # Определяем рабочую директорию (родительская директория файла)
                cwd = component_path.parent

                # Проверяем права
                if not os.access(component_path, os.X_OK):
                    logger.warning(f"Устанавливаем права для {component_path}")
                    component_path.chmod(0o755)

                logger.info(f"Запускаем {name} из {cwd}")

                # Запускаем процесс
                process = subprocess.Popen(
                    [str(component_path)],
                    cwd=str(cwd),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                )

                processes.append((name, process))

                # Небольшая задержка между запуском компонентов
                time.sleep(1)

            # Проверяем, что все процессы запустились
            time.sleep(3)

            # Проверяем статус процессов
            all_running = True
            for name, process in processes:
                if process.poll() is not None:  # Процесс завершился
                    stdout, stderr = process.communicate()
                    logger.error(
                        f"Процесс {name} завершился с кодом {process.returncode}"
                    )
                    if stderr:
                        logger.error(f"Ошибка {name}: {stderr}")
                    all_running = False
                else:
                    logger.info(f"Процесс {name} запущен (PID: {process.pid})")

            # Проверяем, доступен ли сервер
            if self.check_activitywatch_running():
                logger.info("ActivityWatch успешно запущен и доступен")
                return True
            elif all_running:
                logger.warning(
                    "Все процессы запущены, но сервер не отвечает на порту 5600"
                )
                # Даем еще время на запуск
                time.sleep(5)
                if self.check_activitywatch_running():
                    logger.info("Теперь ActivityWatch доступен!")
                    return True
                else:
                    logger.warning("Сервер все еще не отвечает")
                    return False
            else:
                logger.error("Не все компоненты запустились")
                return False

        except Exception as e:
            logger.error(f"Ошибка при запуске ActivityWatch: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def setup_autostart(self) -> bool:
        """
        Настраивает автозапуск ActivityWatch и этой утилиты.
        """
        logger.info("Настройка автозапуска...")
        
        try:
            # Проверяем, установлен ли ActivityWatch
            installed, aw_path = self.check_activitywatch_installed()
            if not installed:
                logger.error("ActivityWatch не установлен для настройки автозапуска")
                return False
            
            # Получаем текущий рабочий каталог
            current_dir = Path(__file__).parent.absolute()
            user = os.environ.get("USER", os.environ.get("LOGNAME", "user"))
            
            if self.system == "Linux":
                logger.info("Настройка автозапуска для Linux...")
                
                # Путь для systemd сервисов пользователя
                user_systemd_dir = Path.home() / ".config" / "systemd" / "user"
                user_systemd_dir.mkdir(parents=True, exist_ok=True)
                
                # 1. Service для ActivityWatch (запуск всех компонентов)
                aw_service_path = user_systemd_dir / "activitywatch.service"
                
                # Находим пути к компонентам
                aw_server = self._find_component("aw-server")
                aw_watcher_window = self._find_component("aw-watcher-window")
                aw_watcher_afk = self._find_component("aw-watcher-afk")
                
                if not aw_server:
                    logger.error("aw-server не найден!")
                    return False
                
                # Создаем скрипт запуска всех компонентов
                launch_script = current_dir / "start_activitywatch.sh"
                launch_script_content = f'''#!/bin/bash
    # Скрипт запуска всех компонентов ActivityWatch
    export DISPLAY=:0
    export XAUTHORITY=$HOME/.Xauthority
    export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

    # Запускаем сервер
    echo "Запуск aw-server..."
    {aw_server} &
    SERVER_PID=$!

    # Ждем запуска сервера
    sleep 5

    # Запускаем watchers если найдены
    if [ -f "{aw_watcher_window}" ]; then
        echo "Запуск aw-watcher-window..."
        {aw_watcher_window} &
        WINDOW_PID=$!
    fi

    if [ -f "{aw_watcher_afk}" ]; then
        echo "Запуск aw-watcher-afk..."
        {aw_watcher_afk} &
        AFK_PID=$!
    fi

    echo "ActivityWatch запущен. PID сервера: $SERVER_PID"

    # Ждем завершения (никогда не завершаемся)
    wait $SERVER_PID
    '''
                
                with open(launch_script, 'w') as f:
                    f.write(launch_script_content)
                
                # Устанавливаем права
                launch_script.chmod(0o755)
                
                aw_service_content = f"""[Unit]
    Description=ActivityWatch Time Tracker
    After=graphical-session.target
    Requires=graphical-session.target
    Wants=network-online.target

    [Service]
    Type=simple
    ExecStart={launch_script}
    Restart=on-failure
    RestartSec=10
    TimeoutStartSec=60
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=%h/.Xauthority
    Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus

    # Журналирование
    StandardOutput=journal
    StandardError=journal
    SyslogIdentifier=activitywatch

    [Install]
    WantedBy=default.target
    """
                
                with open(aw_service_path, 'w') as f:
                    f.write(aw_service_content)
                
                # 2. Service для синхронизатора (запускается через 2 минуты после ActivityWatch)
                sync_service_path = user_systemd_dir / "activitywatch-sync.service"
                
                sync_service_content = f"""[Unit]
    Description=ActivityWatch Sync Service
    After=activitywatch.service
    Requires=activitywatch.service
    StartLimitIntervalSec=0

    [Service]
    Type=simple
    # Ждем 120 секунд после запуска ActivityWatch
    ExecStartPre=/bin/sleep 120
    ExecStart={sys.executable} {current_dir}/run_sync_service.py
    Restart=always
    RestartSec=30
    StartLimitBurst=0

    # Журналирование
    StandardOutput=journal
    StandardError=journal
    SyslogIdentifier=activitywatch-sync

    # Окружение для работы
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=%h/.Xauthority
    Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus

    [Install]
    WantedBy=default.target
    """
                
                with open(sync_service_path, 'w') as f:
                    f.write(sync_service_content)
                
                # 3. Timer для периодической проверки
                timer_path = user_systemd_dir / "activitywatch-sync.timer"
                
                timer_content = f"""[Unit]
    Description=Daily restart of ActivityWatch sync service

    [Timer]
    # Запускаем каждый день в 8:00
    OnCalendar=*-*-* 08:00:00
    Persistent=true

    [Install]
    WantedBy=timers.target
    """
                
                with open(timer_path, 'w') as f:
                    f.write(timer_content)
                
                # Перезагружаем systemd
                subprocess.run(["systemctl", "--user", "daemon-reload"], 
                            capture_output=True)
                
                # Включаем и запускаем сервисы
                subprocess.run(["systemctl", "--user", "enable", "activitywatch.service"], 
                            capture_output=True)
                subprocess.run(["systemctl", "--user", "enable", "activitywatch-sync.service"], 
                            capture_output=True)
                subprocess.run(["systemctl", "--user", "enable", "activitywatch-sync.timer"], 
                            capture_output=True)
                
                # Запускаем сервисы
                subprocess.run(["systemctl", "--user", "start", "activitywatch.service"], 
                            capture_output=True)
                
                # Ждем и запускаем синхронизатор
                time.sleep(10)
                subprocess.run(["systemctl", "--user", "start", "activitywatch-sync.service"], 
                            capture_output=True)
                
                # Включаем лингер для запуска при загрузке
                subprocess.run(["loginctl", "enable-linger", user], 
                            capture_output=True)
                
                logger.info("✅ Systemd сервисы созданы и включены")
                
                # Создаем .desktop файл для автозапуска при входе (резервный метод)
                autostart_dir = Path.home() / ".config" / "autostart"
                autostart_dir.mkdir(parents=True, exist_ok=True)
                
                desktop_file = autostart_dir / "activitywatch-sync.desktop"
                desktop_content = f"""[Desktop Entry]
    Type=Application
    Name=ActivityWatch Sync
    Exec=/bin/bash -c "sleep 30 && {sys.executable} {current_dir}/run_sync_service.py"
    Hidden=false
    NoDisplay=false
    X-GNOME-Autostart-enabled=true
    Comment=ActivityWatch synchronization service
    """
                
                with open(desktop_file, 'w') as f:
                    f.write(desktop_content)
                
                logger.info(f"Создан .desktop файл: {desktop_file}")
                
                # Создаем скрипт для проверки статуса
                check_script = Path.home() / "check_activitywatch_status.sh"
                check_content = f"""#!/bin/bash
    echo "=== Проверка ActivityWatch Status ==="
    echo ""
    echo "1. Процессы:"
    ps aux | grep -E "(aw-|activitywatch|run_sync)" | grep -v grep | sort
    echo ""
    echo "2. Systemd сервисы:"
    systemctl --user status activitywatch.service --no-pager
    echo ""
    systemctl --user status activitywatch-sync.service --no-pager
    echo ""
    echo "3. Порты:"
    ss -tlnp | grep -E "5600|8000" | sort
    echo ""
    echo "4. Логи за последние 5 минут:"
    journalctl --user -u activitywatch.service -u activitywatch-sync.service --since "5 minutes ago" --no-pager
    echo ""
    echo "=== Проверка завершена ==="
    """
                
                with open(check_script, 'w') as f:
                    f.write(check_content)
                
                subprocess.run(["chmod", "+x", str(check_script)])
                
                # Показываем инструкции
                print("\n" + "="*70)
                print("АВТОЗАПУСК НАСТРОЕН УСПЕШНО!")
                print("="*70)
                print("Созданы:")
                print("  • activitywatch.service - трекинг активности")
                print("  • activitywatch-sync.service - синхронизация данных")
                print("  • activitywatch-sync.timer - ежедневный перезапуск в 8:00")
                print("  • ~/.config/autostart/activitywatch-sync.desktop - резервный запуск")
                print("\nКоманды для управления:")
                print("  systemctl --user start activitywatch.service")
                print("  systemctl --user start activitywatch-sync.service")
                print("  systemctl --user stop activitywatch.service")
                print("  systemctl --user stop activitywatch-sync.service")
                print("  systemctl --user status activitywatch.service")
                print("  systemctl --user status activitywatch-sync.service")
                print(f"\nПроверить статус: bash {check_script}")
                print("\nЛоги:")
                print("  journalctl --user -u activitywatch.service -f")
                print("  journalctl --user -u activitywatch-sync.service -f")
                print("="*70)
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при настройке автозапуска: {e}", exc_info=True)
            return False
                    
    def _create_windows_shortcut(
        self, target: str, shortcut_path: str, description: str
    ):
        """Создает ярлык на Windows"""
        try:
            import winshell
            from win32com.client import Dispatch

            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = str(Path(target).parent)
            shortcut.Description = description
            shortcut.save()

        except ImportError:
            # Альтернативный метод без дополнительных библиотек
            vbscript = f'''
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{shortcut_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{target}"
            oLink.WorkingDirectory = "{Path(target).parent}"
            oLink.Description = "{description}"
            oLink.Save
            '''

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".vbs", delete=False
            ) as f:
                f.write(vbscript)
                vbs_file = f.name

            subprocess.run(["cscript", vbs_file], capture_output=True)
            os.unlink(vbs_file)

    def _create_macos_launchd(self, command: str, plist_path: str, label: str):
        """Создает LaunchAgent для macOS"""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>{command}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""

        with open(plist_path, "w") as f:
            f.write(plist_content)

        # Устанавливаем правильные права
        subprocess.run(["chmod", "644", plist_path])

    def _create_systemd_service(
        self, command: str, service_path: str, description: str
    ):
        """Создает systemd service для Linux"""
        service_content = f"""[Unit]
Description={description}
After=network.target

[Service]
Type=simple
ExecStart={command}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""

        with open(service_path, "w") as f:
            f.write(service_content)

    def _create_linux_desktop_entry(self, command: str, desktop_path: str, name: str):
        """Создает .desktop файл для автозапуска на Linux"""
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={name}
Exec={command}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""

        with open(desktop_path, "w") as f:
            f.write(desktop_content)

        subprocess.run(["chmod", "+x", desktop_path])

    def full_setup(self) -> bool:
        """
        Выполняет полную настройку:
        1. Проверяет установку
        2. Устанавливает при необходимости
        3. Запускает ActivityWatch
        4. Настраивает автозапуск

        Returns:
            bool: True если все шаги успешны, иначе False
        """
        logger.info("=== НАЧАЛО ПОЛНОЙ НАСТРОЙКИ ===")

        # 1. Проверяем установку
        installed, _ = self.check_activitywatch_installed()
        if not installed:
            logger.info("ActivityWatch не установлен. Начинаем установку...")
            if not self.install_activitywatch():
                logger.error("Не удалось установить ActivityWatch")
                return False
        else:
            logger.info("ActivityWatch уже установлен")

        # 2. Проверяем запуск
        if not self.check_activitywatch_running():
            logger.info("ActivityWatch не запущен. Запускаем...")
            if not self.start_activitywatch():
                logger.error("Не удалось запустить ActivityWatch")
                return False
        else:
            logger.info("ActivityWatch уже запущен")

        # 3. Настраиваем автозапуск
        logger.info("Настраиваем автозапуск...")
        if not self.setup_autostart():
            logger.warning("Не удалось настроить автозапуск")
            # Не считаем это критической ошибкой

        logger.info("=== ПОЛНАЯ НАСТРОЙКА ЗАВЕРШЕНА ===")
        return True
