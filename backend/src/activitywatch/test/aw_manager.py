#!/usr/bin/env python3
"""
ActivityWatch Installer and Manager
===================================
Кросс-платформенная утилита для автоматической установки и управления ActivityWatch.
"""

import os
import sys
import platform
import subprocess
import shutil
import tempfile
import zipfile
import tarfile
from pathlib import Path
import requests
import json
import time
from datetime import datetime
import logging
from typing import Optional, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('activitywatch_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ActivityWatchManager:
    """Менеджер для установки и управления ActivityWatch"""
    
    # URL для скачивания (версия 0.13.2)
    DOWNLOAD_URLS = {
        'Windows': 'https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-windows-x86_64-setup.exe',
        'Darwin': 'https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-macos-x86_64.dmg',
        'Linux': 'https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-linux-x86_64.zip'
    }
    
    def __init__(self):
        """Инициализация менеджера"""
        self.system = platform.system()
        self.machine = platform.machine()
        self.download_dir = Path(tempfile.gettempdir()) / 'activitywatch_install'
        self.download_dir.mkdir(exist_ok=True)
        
        # Пути установки по умолчанию
        self.install_paths = {
            'Windows': Path(os.environ.get('LOCALAPPDATA', '')) / 'activitywatch',
            'Darwin': Path.home() / 'Applications' / 'activitywatch',
            'Linux': Path.home() / '.local' / 'share' / 'activitywatch'
        }
        
        self.install_path = self.install_paths.get(self.system, Path.home() / 'activitywatch')
        
    def check_activitywatch_installed(self) -> Tuple[bool, Optional[Path]]:
        """
        Проверяет, установлен ли ActivityWatch.
        
        Returns:
            Tuple[bool, Optional[Path]]: (Установлен ли, путь к исполняемому файлу)
        """
        logger.info(f"Проверка установки ActivityWatch на {self.system}")
        
        # Проверяем различные возможные пути
        possible_paths = []
        
        if self.system == 'Windows':
            possible_paths = [
                Path(os.environ.get('LOCALAPPDATA', '')) / 'activitywatch' / 'aw-server.exe',
                Path(os.environ.get('PROGRAMFILES', '')) / 'activitywatch' / 'aw-server.exe',
                Path.home() / 'AppData' / 'Local' / 'activitywatch' / 'aw-server.exe',
            ]
            # Также проверяем в PATH
            try:
                result = subprocess.run(['where', 'aw-server'], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    possible_paths.append(Path(result.stdout.strip()))
            except:
                pass
                
        elif self.system == 'Darwin':
            possible_paths = [
                Path('/Applications/activitywatch.app/Contents/MacOS/aw-server'),
                Path.home() / 'Applications' / 'activitywatch.app' / 'Contents' / 'MacOS' / 'aw-server',
                Path.home() / '.local' / 'bin' / 'aw-server',
            ]
            # Проверяем через which
            try:
                result = subprocess.run(['which', 'aw-server'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    possible_paths.append(Path(result.stdout.strip()))
            except:
                pass
                
        elif self.system == 'Linux':
            possible_paths = [
                Path('/usr/local/bin/aw-server'),
                Path('/usr/bin/aw-server'),
                Path.home() / '.local' / 'bin' / 'aw-server',
                Path.home() / 'activitywatch' / 'aw-server',
            ]
            # Проверяем через which
            try:
                result = subprocess.run(['which', 'aw-server'], 
                                      capture_output=True, text=True)
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
            response = requests.get('http://localhost:5600/api/0/info', timeout=3)
            if response.status_code == 200:
                logger.info("ActivityWatch запущен и доступен")
                return True
        except requests.RequestException:
            pass
        
        # Альтернативная проверка через процессы
        try:
            if self.system == 'Windows':
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq aw-server.exe'], 
                                      capture_output=True, text=True, shell=True)
                return 'aw-server.exe' in result.stdout
            else:
                result = subprocess.run(['pgrep', '-f', 'aw-server'], 
                                      capture_output=True, text=True)
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
        
        filename = url.split('/')[-1]
        download_path = self.download_dir / filename
        
        logger.info(f"Скачивание ActivityWatch для {self.system}...")
        logger.info(f"URL: {url}")
        logger.info(f"Сохраняю в: {download_path}")
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            logger.info(f"Прогресс: {percent:.1f}%")
            
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
            cmd = [str(installer_path), '/S', '/D=' + str(self.install_path)]
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
            mount_cmd = ['hdiutil', 'attach', str(dmg_path)]
            result = subprocess.run(mount_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Ошибка монтирования DMG: {result.stderr}")
                return False
            
            # Ищем смонтированный том
            for line in result.stdout.split('\n'):
                if '/Volumes/' in line and 'activitywatch' in line.lower():
                    parts = line.split('\t')
                    if len(parts) > 1:
                        mount_point = parts[-1].strip()
                        break
            
            if not 'mount_point' in locals():
                logger.error("Не найден смонтированный том ActivityWatch")
                return False
            
            # Копируем приложение
            app_source = Path(mount_point) / 'activitywatch.app'
            app_dest = Path('/Applications') / 'activitywatch.app'
            
            if app_dest.exists():
                shutil.rmtree(app_dest)
            
            shutil.copytree(app_source, app_dest)
            
            # Отмонтируем DMG
            subprocess.run(['hdiutil', 'detach', mount_point], 
                          capture_output=True, text=True)
            
            # Устанавливаем права
            subprocess.run(['chmod', '+x', str(app_dest / 'Contents' / 'MacOS' / '*')])
            
            logger.info("Установка на macOS завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при установке на macOS: {e}")
            return False
    
    def install_linux(self, zip_path: Path) -> bool:
        """
        Устанавливает ActivityWatch на Linux.
        
        Args:
            zip_path: Путь к архиву .zip
        
        Returns:
            bool: True если установка успешна, иначе False
        """
        logger.info("Установка ActivityWatch на Linux...")
        
        try:
            # Создаем директорию для установки
            self.install_path.mkdir(parents=True, exist_ok=True)
            
            # Распаковываем архив
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.install_path)
            
            # Делаем файлы исполняемыми
            for exe_file in ['aw-server', 'aw-watcher-window', 'aw-watcher-afk']:
                exe_path = self.install_path / exe_file
                if exe_path.exists():
                    exe_path.chmod(0o755)
            
            # Создаем симлинки в ~/.local/bin
            local_bin = Path.home() / '.local' / 'bin'
            local_bin.mkdir(parents=True, exist_ok=True)
            
            for exe_file in ['aw-server', 'aw-watcher-window', 'aw-watcher-afk']:
                source = self.install_path / exe_file
                dest = local_bin / exe_file
                
                if source.exists():
                    if dest.exists():
                        dest.unlink()
                    dest.symlink_to(source)
            
            logger.info("Установка на Linux завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при установке на Linux: {e}")
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
        if self.system == 'Windows':
            return self.install_windows(installer_path)
        elif self.system == 'Darwin':
            return self.install_macos(installer_path)
        elif self.system == 'Linux':
            return self.install_linux(installer_path)
        else:
            logger.error(f"Неподдерживаемая платформа: {self.system}")
            return False
    
    def start_activitywatch(self) -> bool:
        """
        Запускает ActivityWatch.
        
        Returns:
            bool: True если запуск успешен, иначе False
        """
        logger.info("Запуск ActivityWatch...")
        
        try:
            installed, aw_path = self.check_activitywatch_installed()
            if not installed:
                logger.error("ActivityWatch не установлен")
                return False
            
            if self.system == 'Windows':
                # Запускаем aw-server
                subprocess.Popen([str(aw_path.parent / 'aw-server.exe')], 
                               creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                
                # Запускаем watchers
                time.sleep(2)
                subprocess.Popen([str(aw_path.parent / 'aw-watcher-window.exe')],
                               creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                subprocess.Popen([str(aw_path.parent / 'aw-watcher-afk.exe')],
                               creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                
            elif self.system in ['Darwin', 'Linux']:
                # Запускаем в фоновом режиме
                subprocess.Popen([str(aw_path)], start_new_session=True)
                
                # Ищем путь к watchers
                watcher_dir = aw_path.parent
                
                # Запускаем watchers
                time.sleep(2)
                window_watcher = watcher_dir / 'aw-watcher-window'
                afk_watcher = watcher_dir / 'aw-watcher-afk'
                
                if window_watcher.exists():
                    subprocess.Popen([str(window_watcher)], start_new_session=True)
                if afk_watcher.exists():
                    subprocess.Popen([str(afk_watcher)], start_new_session=True)
            
            # Ждем и проверяем запуск
            time.sleep(5)
            
            if self.check_activitywatch_running():
                logger.info("ActivityWatch успешно запущен")
                return True
            else:
                logger.warning("ActivityWatch не запустился автоматически")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при запуске ActivityWatch: {e}")
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
            
            if self.system == 'Windows':
                # Используем реестр или папку автозагрузки
                startup_folder = Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
                
                # Ярлык для ActivityWatch
                aw_shortcut = startup_folder / 'ActivityWatch.lnk'
                self._create_windows_shortcut(
                    str(aw_path.parent / 'aw-server.exe'),
                    str(aw_shortcut),
                    'ActivityWatch Server'
                )
                
                # Ярлык для этой утилиты
                util_shortcut = startup_folder / 'ActivityWatchManager.lnk'
                self._create_windows_shortcut(
                    str(this_script),
                    str(util_shortcut),
                    'ActivityWatch Manager'
                )
                
            elif self.system == 'Darwin':
                # Используем LaunchAgents
                launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
                launch_agents_dir.mkdir(exist_ok=True)
                
                # Plist для ActivityWatch
                aw_plist = launch_agents_dir / 'com.activitywatch.server.plist'
                self._create_macos_launchd(
                    str(aw_path),
                    str(aw_plist),
                    'ActivityWatch Server'
                )
                
                # Plist для этой утилиты
                util_plist = launch_agents_dir / 'com.activitywatch.manager.plist'
                self._create_macos_launchd(
                    f'python3 {this_script} --startup',
                    str(util_plist),
                    'ActivityWatch Manager'
                )
                
            elif self.system == 'Linux':
                # Используем systemd или autostart директорию
                if shutil.which('systemctl'):
                    # Создаем systemd service
                    service_dir = Path.home() / '.config' / 'systemd' / 'user'
                    service_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Service для ActivityWatch
                    aw_service = service_dir / 'activitywatch.service'
                    self._create_systemd_service(
                        str(aw_path),
                        str(aw_service),
                        'ActivityWatch Server'
                    )
                    
                    # Service для этой утилиты
                    util_service = service_dir / 'activitywatch-manager.service'
                    self._create_systemd_service(
                        f'python3 {this_script} --startup',
                        str(util_service),
                        'ActivityWatch Manager'
                    )
                    
                    # Включаем и запускаем
                    subprocess.run(['systemctl', '--user', 'enable', 'activitywatch.service'])
                    subprocess.run(['systemctl', '--user', 'enable', 'activitywatch-manager.service'])
                    
                else:
                    # Используем .config/autostart
                    autostart_dir = Path.home() / '.config' / 'autostart'
                    autostart_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Desktop entry для ActivityWatch
                    aw_desktop = autostart_dir / 'activitywatch.desktop'
                    self._create_linux_desktop_entry(
                        str(aw_path),
                        str(aw_desktop),
                        'ActivityWatch Server'
                    )
                    
                    # Desktop entry для этой утилиты
                    util_desktop = autostart_dir / 'activitywatch-manager.desktop'
                    self._create_linux_desktop_entry(
                        f'python3 {this_script} --startup',
                        str(util_desktop),
                        'ActivityWatch Manager'
                    )
            
            logger.info("Автозапуск настроен успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при настройке автозапуска: {e}")
            return False
    
    def _create_windows_shortcut(self, target: str, shortcut_path: str, description: str):
        """Создает ярлык на Windows"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            shell = Dispatch('WScript.Shell')
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False) as f:
                f.write(vbscript)
                vbs_file = f.name
            
            subprocess.run(['cscript', vbs_file], capture_output=True)
            os.unlink(vbs_file)
    
    def _create_macos_launchd(self, command: str, plist_path: str, label: str):
        """Создает LaunchAgent для macOS"""
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
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
</plist>'''
        
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        # Устанавливаем правильные права
        subprocess.run(['chmod', '644', plist_path])
    
    def _create_systemd_service(self, command: str, service_path: str, description: str):
        """Создает systemd service для Linux"""
        service_content = f'''[Unit]
Description={description}
After=network.target

[Service]
Type=simple
ExecStart={command}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
'''
        
        with open(service_path, 'w') as f:
            f.write(service_content)
    
    def _create_linux_desktop_entry(self, command: str, desktop_path: str, name: str):
        """Создает .desktop файл для автозапуска на Linux"""
        desktop_content = f'''[Desktop Entry]
Type=Application
Name={name}
Exec={command}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
'''
        
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        
        subprocess.run(['chmod', '+x', desktop_path])
    
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
    
    parser = argparse.ArgumentParser(description='ActivityWatch Installer and Manager')
    parser.add_argument('--check', action='store_true', help='Проверить установку и запуск')
    parser.add_argument('--install', action='store_true', help='Установить ActivityWatch')
    parser.add_argument('--start', action='store_true', help='Запустить ActivityWatch')
    parser.add_argument('--setup-autostart', action='store_true', help='Настроить автозапуск')
    parser.add_argument('--full-setup', action='store_true', help='Выполнить полную настройку')
    parser.add_argument('--startup', action='store_true', help='Режим запуска при старте системы')
    
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
        print(f"\n{'='*60}")
        print("ACTIVITYWATCH УСТАНОВЩИК И МЕНЕДЖЕР")
        print(f"{'='*60}")
        print(f"Система: {platform.system()} {platform.machine()}")
        print(f"{'='*60}")
        
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
            choice = input("\nВыберите действие (0-5): ").strip()
            
            if choice == '1':
                print(f"\nДетальная проверка:")
                print(f"  Установлен: {'Да' if installed else 'Нет'}")
                if installed:
                    print(f"  Путь: {path}")
                print(f"  Запущен: {'Да' if running else 'Нет'}")
                
                # Показываем статус API
                try:
                    response = requests.get('http://localhost:5600/api/0/info', timeout=2)
                    if response.status_code == 200:
                        info = response.json()
                        print(f"  Версия сервера: {info.get('version', 'неизвестно')}")
                except:
                    print(f"  API недоступен")
            
            elif choice == '2':
                print("\nУстановка ActivityWatch...")
                if manager.install_activitywatch():
                    print("✓ Установка завершена успешно!")
                else:
                    print("✗ Ошибка установки!")
            
            elif choice == '3':
                print("\nЗапуск ActivityWatch...")
                if manager.start_activitywatch():
                    print("✓ ActivityWatch запущен успешно!")
                else:
                    print("✗ Ошибка запуска!")
            
            elif choice == '4':
                print("\nНастройка автозапуска...")
                if manager.setup_autostart():
                    print("✓ Автозапуск настроен успешно!")
                else:
                    print("✗ Ошибка настройки автозапуска!")
            
            elif choice == '5':
                print("\nПолная настройка...")
                if manager.full_setup():
                    print("✓ Настройка завершена успешно!")
                else:
                    print("✗ Настройка завершена с ошибками!")
            
            elif choice == '0':
                print("\nВыход...")
                return
            
            else:
                print("\nНеверный выбор!")
        
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем")
    
    print()


if __name__ == "__main__":
    main()