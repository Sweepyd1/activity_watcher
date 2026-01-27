import json
from fastapi import APIRouter, Request
from activitywatch.schemas.tracker.schema import ActivityBatch
router = APIRouter(prefix="/tracker", tags=["отслеживание активностей"])

@router.post("/receive")
async def receive_activitywatch_data(batch: ActivityBatch):
    """Получаем данные от ActivityWatch и красиво выводим в консоль"""
    
    print("\n" + "="*60)
    print(f"📥 ПОЛУЧЕНЫ ДАННЫЕ ОТ УСТРОЙСТВА: {batch.device_name or batch.device_id}")
    print(f"📊 Количество событий: {len(batch.events)}")
    print("="*60)
    
    for i, event in enumerate(batch.events, 1):
        # Преобразуем timestamp в читаемый формат
        try:
            dt = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = event.timestamp
        
        # Получаем данные
        app_name = event.data.get('app', 'Неизвестно')
        title = event.data.get('title', 'Без названия')
        duration_minutes = round(event.duration / 60, 1)
        
        # Красивый вывод
        print(f"\n📋 Событие #{i}:")
        print(f"   ⏰ Время: {time_str}")
        print(f"   ⏱️  Длительность: {duration_minutes} мин ({event.duration} сек)")
        print(f"   🖥️  Приложение: {app_name}")
        print(f"   📄 Название окна: {title}")
        
        # URL если есть
        if 'url' in event.data:
            print(f"   🔗 URL: {event.data['url']}")
        
        # Дополнительные данные
        if 'afk' in event.data:
            print(f"   😴 AFK: {'Да' if event.data['afk'] else 'Нет'}")
    
    print("\n" + "="*60)
    print(f"✅ ВСЕГО ОБРАБОТАНО: {len(batch.events)} событий")
    print("="*60)
    
    # Сохраняем в памяти
    received_data.append({
        "timestamp": datetime.now().isoformat(),
        "device": batch.device_name or batch.device_id,
        "events_count": len(batch.events),
        "data": batch.dict()
    })
    
    return {
        "status": "success",
        "received": len(batch.events),
        "message": f"Получено {len(batch.events)} событий от {batch.device_name or batch.device_id}",
        "server_time": datetime.now().isoformat()
    }

@router.get("/data")
async def get_all_data():
    """Посмотреть все полученные данные"""
    return {
        "total_batches": len(received_data),
        "batches": received_data
    }

@router.get("/clear")
async def clear_data():
    """Очистить все данные"""
    global received_data
    count = len(received_data)
    received_data = []
    return {"message": f"Очищено {count} пакетов данных"}

@router.post("/receive_comprehensive")
async def receive_comprehensive_data(request: Request):
    """Получаем ВСЕ данные от клиента"""
    data = await request.json()
    
    print("\n" + "="*80)
    print(f"📥 ПОЛУЧЕНЫ ПОЛНЫЕ ДАННЫЕ ОТ УСТРОЙСТВА")
    print("="*80)
    
    # Информация об устройстве
    device_info = data.get("device_info", {})
    print(f"🖥️  УСТРОЙСТВО: {device_info.get('device_name', 'Unknown')}")
    print(f"🆔 ID: {device_info.get('device_id', 'Unknown')}")
    print(f"💻 СИСТЕМА: {device_info.get('system', {}).get('system', 'Unknown')} "
          f"{device_info.get('system', {}).get('release', '')}")
    print(f"👤 Хост: {device_info.get('system', {}).get('hostname', 'Unknown')}")
    print(f"⏰ Время синхронизации: {device_info.get('sync_time', 'Unknown')}")
    
    # Сводка по данным
    raw_data = data.get("raw_data", {})
    print(f"\n📊 СВОДКА ДАННЫХ:")
    print(f"   📋 Событий окон: {raw_data.get('total_window_events', 0)}")
    print(f"   😴 Событий AFK: {raw_data.get('total_afk_events', 0)}")
    
    # Статистика
    stats = data.get("aggregated_stats", {})
    window_stats = stats.get("window_activity", {})
    
    print(f"\n⏱️  ВРЕМЯ АКТИВНОСТИ:")
    print(f"   Активность: {window_stats.get('total_duration', 0) / 60:.1f} мин")
    print(f"   AFK время: {stats.get('total_afk_time', 0) / 60:.1f} мин")
    
    # Топ приложений
    print(f"\n🏆 ТОП-5 ПРИЛОЖЕНИЙ:")
    for i, (app, app_data) in enumerate(window_stats.get('top_applications', [])[:5]):
        duration_min = app_data.get('duration', 0) / 60
        print(f"   {i+1}. {app}: {duration_min:.1f} мин ({app_data.get('count', 0)} раз)")
    
    # Топ заголовков окон
    print(f"\n🏷️  ТОП-5 ЗАГОЛОВКОВ ОКОН:")
    for i, (title, title_data) in enumerate(window_stats.get('top_window_titles', [])[:5]):
        duration_min = title_data.get('duration', 0) / 60
        print(f"   {i+1}. {title[:50]}...: {duration_min:.1f} мин")
    
    # Категории
    categories = data.get("categories_analysis", {}).get('categories', {})
    print(f"\n📁 КАТЕГОРИИ АКТИВНОСТИ:")
    for category, cat_data in categories.items():
        duration_min = cat_data.get('duration', 0) / 60
        percentage = (cat_data.get('duration', 0) / window_stats.get('total_duration', 1)) * 100
        print(f"   • {category}: {duration_min:.1f} мин ({percentage:.1f}%)")
    
    # Примеры событий
    print(f"\n📋 ПРИМЕРЫ СОБЫТИЙ:")
    events = raw_data.get('window_events', [])
    for i, event in enumerate(events[:3]):  # Показываем первые 3 события
        timestamp = event.get('timestamp', '')
        app = event.get('data', {}).get('app', 'Unknown')
        title = event.get('data', {}).get('title', 'Unknown')
        duration = event.get('duration', 0) / 60
        
        # Парсим время
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp[:19]
        
        print(f"   {i+1}. [{time_str}] {app}: {title[:40]}... ({duration:.1f} мин)")
    
    print("\n" + "="*80)
    print(f"✅ ВСЕГО ОБРАБОТАНО: {len(events)} событий")
    print("="*80)
    
    # Сохраняем в файл для отладки
    with open(f"activity_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return {"status": "success", "message": f"Получено {len(events)} событий"}
from datetime import datetime, date
from collections import defaultdict

# Хранилище данных в памяти (в production используйте БД)
daily_data = defaultdict(dict)

@router.post("/receive_incremental")
async def receive_incremental(request: Request):
    """Получаем инкрементальные обновления"""
    data = await request.json()
    print(data)
    
    device_id = data.get("device_info", {}).get("device_id")
    events = data.get("events", [])
    
    print(f"\n📥 Инкрементальное обновление от {device_id}")
    print(f"📊 Количество новых событий: {len(events)}")
    
    # Обрабатываем каждое событие
    for event in events:
        event_time = event.get("timestamp")
        if not event_time:
            continue
        
        try:
            # Получаем дату события
            dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            event_date = dt.strftime("%Y-%m-%d")
            event_hour = dt.strftime("%H:00")
            
            app = event.get("data", {}).get("app", "Unknown")
            duration = event.get("duration", 0)
            
            # Инициализируем структуру для даты, если нужно
            if event_date not in daily_data:
                daily_data[event_date] = {
                    "device_id": device_id,
                    "hourly": defaultdict(lambda: defaultdict(float)),
                    "applications": defaultdict(float),
                    "total_time": 0
                }
            
            # Добавляем данные
            daily_data[event_date]["hourly"][event_hour][app] += duration
            daily_data[event_date]["applications"][app] += duration
            daily_data[event_date]["total_time"] += duration
            
        except Exception as e:
            print(f"⚠️  Ошибка обработки события: {e}")
    
    return {"status": "success", "message": f"Обработано {len(events)} событий"}

@router.post("/receive_daily_summary")
async def receive_daily_summary(request: Request):
    """Получаем дневной суммарный отчет"""
    data = await request.json()
    print(data)
    
    date_str = data.get("date")
    device_info = data.get("device_info", {})
    
    print("\n" + "="*80)
    print(f"📅 ДНЕВНОЙ ОТЧЕТ ЗА {date_str}")
    print("="*80)
    
    print(f"🖥️  Устройство: {device_info.get('device_name')} ({device_info.get('system')})")
    print(f"⏱️  Общее активное время: {data.get('total_active_time', 0) / 3600:.2f} ч")
    print(f"😴 AFK время: {data.get('total_afk_time', 0) / 3600:.2f} ч")
    
    # Топ приложений
    applications = data.get("applications", {})
    if applications:
        print(f"\n🏆 ТОП-5 ПРИЛОЖЕНИЙ:")
        sorted_apps = sorted(applications.items(), key=lambda x: x[1], reverse=True)[:5]
        for app, duration in sorted_apps:
            hours = duration / 3600
            print(f"   • {app}: {hours:.2f} ч")
    
    # Категории
    categories = data.get("categories", {})
    if categories:
        print(f"\n📁 КАТЕГОРИИ:")
        total = sum(categories.values()) or 1
        for category, duration in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total) * 100
            print(f"   • {category}: {percentage:.1f}%")
    
    # Почасовая активность
    hourly = data.get("hourly_data", {})
    if hourly:
        print(f"\n🕐 ПОЧАСОВАЯ АКТИВНОСТЬ:")
        for hour, hour_data in sorted(hourly.items()):
            total_minutes = hour_data.get("total_time", 0) / 60
            if total_minutes > 0:
                apps = hour_data.get("applications", {})
                top_app = max(apps.items(), key=lambda x: x[1])[0] if apps else "Нет данных"
                print(f"   • {hour}: {total_minutes:.0f} мин (основное: {top_app})")
    
    print("="*80)
    
    # Сохраняем в файл
    filename = f"daily_report_{date_str}_{device_info.get('device_id', 'unknown')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return {"status": "success", "message": "Дневной отчет получен"}

@router.get("/summary/{date}")
async def get_daily_summary(date: str):
    """Получаем сводку за конкретный день"""
    if date in daily_data:
        return daily_data[date]
    return {"error": "Данные за эту дату не найдены"}

@router.get("/device_info")
async def get_all_devices():
    """Получаем информацию обо всех устройствах"""
    devices = {}
    for date_str, data in daily_data.items():
        device_id = data.get("device_id")
        if device_id not in devices:
            devices[device_id] = {
                "last_update": date_str,
                "total_days": 0,
                "total_hours": 0
            }
        
        devices[device_id]["total_days"] += 1
        devices[device_id]["total_hours"] += data.get("total_time", 0) / 3600
    
    return devices