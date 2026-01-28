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
from abc import ABC, abstractmethod
import os
import sys

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

CONFIG_DIR = Path.home() / ".activitywatch-client"
CONFIG_FILE = CONFIG_DIR / "config.json"

class SecurityToken:
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_dir.mkdir(exist_ok=True)
        
    def generate_device_id(self) -> str:
        """Генерирует уникальный device_id через uuid4"""
        return str(uuid.uuid4())
    
    def get_system_info(self) -> dict:
        """Получает информацию о системе и устройстве"""
        try:
            hostname = socket.gethostname()
            return {
                "system": f"{platform.system()} {platform.release()} {platform.machine()}",
                "hostname": hostname,
                "device_name": hostname.split('.')[0] if '.' in hostname else hostname,
                "platform_version": platform.platform(),
            
            }
        except Exception as e:
            logger.error(f"Ошибка получения системной информации: {e}")
            return {
                "system": "Unknown",
                "hostname": "unknown",
                "device_name": "unknown",
                "platform_version": "unknown",
                "processor": "unknown",
                "memory_gb": 0
            }
    
    def save_config(self, token: str, device_id: str):
        """Сохраняет токен и device_id на диск"""
        config = {
            "token": token,
            "device_id": device_id,
            "created_at": str(uuid.uuid4()),  # для ротации
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)  # Только владелец может читать
        logger.info(f"Конфиг сохранен: {CONFIG_FILE}")
    
    def load_config(self) -> dict:
        """Читает сохраненные данные"""
        if not CONFIG_FILE.exists():
            return {}
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения конфига: {e}")
            return {}
    
    def clear_config(self):
        """Удаляет конфиг"""
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            logger.info("Конфиг удален")
    
    def register_device(self):
        """Главная функция регистрации устройства"""
        config = self.load_config()
        
        # ✅ Проверяем существующий токен
        if config.get('token') and config.get('device_id'):
            logger.info("Найден существующий токен, используем его")
            token = config['token']
            device_id = config['device_id']
        else:
            # Генерируем новый device_id
            device_id = self.generate_device_id()
            token = input("Введите токен: ").strip()
            
            if not token:
                logger.error("Токен не введен!")
                return False
            
            # Сохраняем
            self.save_config(token, device_id)
        
        # Получаем системную информацию
        sys_info = self.get_system_info()
        
        # Формируем payload
        payload = {
            "token": token,
            "device_id": device_id,
            **sys_info  # Система: Linux x86_64, устройство: sweepy-ms7d99
        }
        
        logger.info(f"Отправка запроса регистрации: {device_id[:8]}...")
        
        try:
            response = requests.post(
                "http://localhost:8000/devices/register",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info("✅ Устройство успешно зарегистрировано!")
                print(f"Device ID: {device_id}")
                return True
            else:
                logger.error(f"❌ Ошибка регистрации: {response.status_code}")
                print(f"Ошибка: {response.json()}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сети: {e}")
            return False

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

        Returns:
            bool: True если настройка успешна, иначе False
        """
        logger.info("Настройка автозапуска...")

        try:
            installed, aw_path = self.check_activitywatch_installed()
            if not installed:
                logger.error("ActivityWatch не установлен для настройки автозапуска")
                return False

            # Путь к этой утилите
            this_script = Path(sys.argv[0]).absolute()

            if self.system == "Windows":
                # Используем реестр или папку автозагрузки
                startup_folder = (
                    Path(os.environ.get("APPDATA", ""))
                    / "Microsoft"
                    / "Windows"
                    / "Start Menu"
                    / "Programs"
                    / "Startup"
                )

                # Ярлык для ActivityWatch
                aw_shortcut = startup_folder / "ActivityWatch.lnk"
                self._create_windows_shortcut(
                    str(aw_path.parent / "aw-server.exe"),
                    str(aw_shortcut),
                    "ActivityWatch Server",
                )

                # Ярлык для этой утилиты
                util_shortcut = startup_folder / "ActivityWatchManager.lnk"
                self._create_windows_shortcut(
                    str(this_script), str(util_shortcut), "ActivityWatch Manager"
                )

            elif self.system == "Darwin":
                # Используем LaunchAgents
                launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
                launch_agents_dir.mkdir(exist_ok=True)

                # Plist для ActivityWatch
                aw_plist = launch_agents_dir / "com.activitywatch.server.plist"
                self._create_macos_launchd(
                    str(aw_path), str(aw_plist), "ActivityWatch Server"
                )

                # Plist для этой утилиты
                util_plist = launch_agents_dir / "com.activitywatch.manager.plist"
                self._create_macos_launchd(
                    f"python3 {this_script} --startup",
                    str(util_plist),
                    "ActivityWatch Manager",
                )

            elif self.system == "Linux":
                # Используем systemd или autostart директорию
                if shutil.which("systemctl"):
                    # Создаем systemd service
                    service_dir = Path.home() / ".config" / "systemd" / "user"
                    service_dir.mkdir(parents=True, exist_ok=True)

                    # Service для ActivityWatch
                    aw_service = service_dir / "activitywatch.service"
                    self._create_systemd_service(
                        str(aw_path), str(aw_service), "ActivityWatch Server"
                    )

                    # Service для этой утилиты
                    util_service = service_dir / "activitywatch-manager.service"
                    self._create_systemd_service(
                        f"python3 {this_script} --startup",
                        str(util_service),
                        "ActivityWatch Manager",
                    )

                    # Включаем и запускаем
                    subprocess.run(
                        ["systemctl", "--user", "enable", "activitywatch.service"]
                    )
                    subprocess.run(
                        [
                            "systemctl",
                            "--user",
                            "enable",
                            "activitywatch-manager.service",
                        ]
                    )

                else:
                    # Используем .config/autostart
                    autostart_dir = Path.home() / ".config" / "autostart"
                    autostart_dir.mkdir(parents=True, exist_ok=True)

                    # Desktop entry для ActivityWatch
                    aw_desktop = autostart_dir / "activitywatch.desktop"
                    self._create_linux_desktop_entry(
                        str(aw_path), str(aw_desktop), "ActivityWatch Server"
                    )

                    # Desktop entry для этой утилиты
                    util_desktop = autostart_dir / "activitywatch-manager.desktop"
                    self._create_linux_desktop_entry(
                        f"python3 {this_script} --startup",
                        str(util_desktop),
                        "ActivityWatch Manager",
                    )

            logger.info("Автозапуск настроен успешно")
            return True

        except Exception as e:
            logger.error(f"Ошибка при настройке автозапуска: {e}")
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
                if manager.setup_autostart():
                    print("✓ Автозапуск настроен успешно!")
                else:
                    print("✗ Ошибка настройки автозапуска!")

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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("activitywatch_sync.log"), logging.StreamHandler()],
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

    def __init__(
        self,
        api_url: str = "http://localhost:5600/api/0",
        server_url: str = "http://localhost:8000",
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
        device_id = config.get('device_id')
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
            "device_id": device_id  # ✅ Теперь точно строка!
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
                f"{self.server_url}/receive_daily_summary", json=summary, timeout=15
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


def main():
    """Основная функция запуска клиента."""
    import argparse

    parser = argparse.ArgumentParser(description="ActivityWatch Sync Client")
    parser.add_argument(
        "--mode",
        choices=["once", "continuous"],
        default="continuous",
        help="Режим работы (once - один раз, continuous - непрерывно)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="Интервал синхронизации в минутах (для непрерывного режима)",
    )
    parser.add_argument(
        "--health", action="store_true", help="Проверить состояние ActivityWatch"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Сбросить состояние синхронизации"
    )
    parser.add_argument(
        "--status", action="store_true", help="Показать статус синхронизации"
    )

    args = parser.parse_args()

    # Проверка здоровья ActivityWatch
    if args.health:
        print("\n" + "=" * 60)
        print("ПРОВЕРКА ЗДОРОВЬЯ ACTIVITYWATCH")
        print("=" * 60)

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
                    timestamp = event.get("timestamp", "")
                    if timestamp:
                        try:
                            if "Z" in timestamp:
                                dt = datetime.fromisoformat(
                                    timestamp.replace("Z", "+00:00")
                                )
                            else:
                                dt = datetime.fromisoformat(timestamp)
                            age = (
                                datetime.now(timezone.utc)
                                - dt.replace(tzinfo=timezone.utc)
                            ).total_seconds() / 60
                            print(f"    Последнее событие: {age:.1f} минут назад")
                        except:
                            print(f"    Есть события (время неизвестно)")
        else:
            print("✗ ActivityWatch недоступен")
            print("\nУбедитесь, что ActivityWatch запущен:")
            print("  aw-server &")
            print("  aw-watcher-window &")
            print("  aw-watcher-afk &")

        print("=" * 60)
        return

    # Показать статус
    if args.status:
        state_file = Path.home() / ".activitywatch_sync_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)

                print("\n" + "=" * 60)
                print("СТАТУС СИНХРОНИЗАЦИИ")
                print("=" * 60)

                device_id = state.get("device_id", socket.gethostname())
                print(f"Устройство: {device_id}")

                last_sync = state.get("last_sync_time")
                if last_sync:
                    try:
                        if "Z" in last_sync:
                            dt = datetime.fromisoformat(
                                last_sync.replace("Z", "+00:00")
                            )
                        else:
                            dt = datetime.fromisoformat(last_sync)
                        age = (
                            datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)
                        ).total_seconds() / 60
                        print(f"Последняя синхронизация: {age:.1f} минут назад")
                    except:
                        print(f"Последняя синхронизация: {last_sync}")
                else:
                    print("Последняя синхронизация: Никогда")

                print(f"Обработано событий: {state.get('processed_events_count', 0)}")
                print(f"Хэшей в памяти: {len(state.get('last_event_hashes', []))}")
                print(
                    f"Последний дневной отчет: {state.get('last_daily_report', 'Не отправлялся')}"
                )

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

            backup_file = state_file.with_suffix(".json.backup")
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
        last_sync_str = state_manager.state.last_sync_time.strftime("%Y-%m-%d %H:%M:%S")
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


if __name__ == "__main__":
    if not ensure_activitywatch_running():
        sys.exit(1)
    main()
