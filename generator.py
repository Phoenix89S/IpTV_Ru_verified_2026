from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Настройки
MAX_THREADS = 50  # Количество одновременных потоков (можно увеличить до 100 для скорости)
TIMEOUT = 2       # Таймаут запроса в секундах
START_ID = 1
END_ID = 3000

base_url = "https://stream1.cinerama.uz/{}/tracks-v1a1/mono.m3u8"
valid_channels = []

print(f"Запуск проверки ID с {START_ID} по {END_ID} в {MAX_THREADS} потоков...")

def check_stream(stream_id):
    url = base_url.format(stream_id)
    try:
        # Используем HEAD-запрос для быстрой проверки доступности
        response = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return stream_id, url
    except Exception:
        pass
    return None

# Многопоточный обход
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = {executor.submit(check_stream, sid): sid for sid in range(START_ID, END_ID + 1)}
    
    completed = 0
    total = len(futures)
    
    for future in as_completed(futures):
        completed += 1
        print(f"Прогресс: {completed}/{total}", end="\r")
        
        result = future.result()
        if result:
            sid, url = result
            valid_channels.append((sid, url))

# Сортируем каналы по ID, чтобы плейлист шел по порядку
valid_channels.sort(key=lambda x: x[0])

# Генерация M3U файла
playlist_content = "#EXTM3U\n"

for index, (sid, url) in enumerate(valid_channels, start=1):
    # Динамически подставляем порядковый номер канала и название
    channel_name = f"Канал {sid}"
    logo_svg = (
        "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='28' height='28'>"
        "<rect width='28' height='28' rx='3' fill='%230b1018'/>"
        "<text x='14' y='19' font-size='10' text-anchor='middle' fill='%232a3848' font-family='monospace'>TV</text></svg>"
    )
    
    playlist_content += (
        f'#EXTINF:-1 tvg-chno="{index}" '
        f'tvg-logo="{logo_svg}" '
        f'group-title="Verified channels",{channel_name}\n'
        f'{url}\n'
    )

# Сохраняем в файл
output_filename = "playlist.m3u"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(playlist_content)

print(f"\n\nГотово! Найдено рабочих каналов: {len(valid_channels)}")
print(f"Плейлист сохранен в файл: {output_filename}")
