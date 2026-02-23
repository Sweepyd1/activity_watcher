from aw_client import ActivityWatchClient
from datetime import timedelta


def format_duration(seconds: float) -> str:
    """Форматирует секунды в читаемый вид."""
    delta = timedelta(seconds=seconds)
    hours = delta.days * 24 + delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    secs = delta.seconds % 60

    if hours > 0:
        return f"{hours} ч {minutes:02d} мин {secs:02d} сек"
    elif minutes > 0:
        return f"{minutes} мин {secs:02d} сек"
    else:
        return f"{secs} сек"


client = ActivityWatchClient(client_name="my_script", testing=False)

# Получить список всех bucket'ов
buckets = client.get_buckets()
total_time_all_buckets = 0.0

for bucket_id, bucket_info in buckets.items():
    print(f"\nBucket: {bucket_id} ({bucket_info['type']})")

    # Получить все события
    events = client.get_events(bucket_id, limit=-1)

    if not events:
        print("  Нет событий")
        continue

    # Считаем общее время для этого bucket'а
    bucket_total = sum(event.duration.total_seconds() for event in events)
    total_time_all_buckets += bucket_total

    print(f"  Событий: {len(events)}")
    print(f"  Общее время: {format_duration(bucket_total)}")

    # Покажем первые 3 события как пример
    print("  Примеры событий:")
    for event in events[:3]:
        duration_sec = event.duration.total_seconds()
        print(
            f"    • {event.timestamp.strftime('%Y-%m-%d %H:%M')} - "
            f"{format_duration(duration_sec)}: {event.data}"
        )

# Итоговая статистика
print("\n" + "=" * 50)
print("ИТОГОВАЯ СТАТИСТИКА")
print("=" * 50)
print(f"Всего bucket'ов: {len(buckets)}")
print(
    f"Общее суммарное время по всем bucket'ам: {format_duration(total_time_all_buckets)}"
)
print(f"Общее время в секундах: {total_time_all_buckets:.2f} сек")
print(f"Общее время в часах: {total_time_all_buckets / 3600:.2f} ч")
