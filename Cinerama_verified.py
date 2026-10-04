# ============================================================
#              CINERAMA STREAM8 → STREAM1
# ============================================================
# © Phoenix 89S. All rights reserved.

import re
import requests

SOURCE_URL = (
    "https://raw.githubusercontent.com/IPTVRU2026/IPTVMIR/"
    "refs/heads/main/IPTV_MEGA_PLAYLIST.m3u"
)

OUTPUT_FILE = "CINERAMA_VERIFIED.m3u"

OLD_HOST = "stream8.cinerama.uz"
NEW_HOST = "stream1.cinerama.uz"
NEW_GROUP = "Verified channels"
COPYRIGHT = "© Phoenix 89S"


def replace_group_title(extinf):
    """
    Меняет ТОЛЬКО значение group-title или добавляет его,
    если атрибут отсутствует.
    """
    pattern = r'group-title="[^"]*"'

    if re.search(pattern, extinf, flags=re.IGNORECASE):
        return re.sub(
            pattern,
            f'group-title="{NEW_GROUP}"',
            extinf,
            count=1,
            flags=re.IGNORECASE
        )

    comma_pos = extinf.find(",")
    if comma_pos != -1:
        return (
            extinf[:comma_pos]
            + f' group-title="{NEW_GROUP}"'
            + extinf[comma_pos:]
        )

    return extinf


def main():
    print("==============================================")
    print(f"     CINERAMA STREAM8 → STREAM1 | {COPYRIGHT}")
    print("==============================================")
    print()
    print("[INFO] Загружаем исходный M3U...")

    try:
        response = requests.get(
            SOURCE_URL,
            timeout=60,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Не удалось загрузить плейлист: {e}")
        return

    lines = response.text.splitlines()
    total_lines = len(lines)

    # Инициализация плейлиста с добавлением копирайта в шапку
    result = [
        "#EXTM3U",
        f"# Playlist optimized by {COPYRIGHT} - {NEW_GROUP}"
    ]
    
    found = 0
    i = 0

    print(f"[INFO] Сканирование и обработка потоков ({total_lines} строк)...")

    while i < total_lines:
        line = lines[i].strip()

        if OLD_HOST in line:
            if i > 0 and lines[i - 1].strip().startswith("#EXTINF:"):
                extinf = replace_group_title(lines[i - 1].strip())
                
                # Замена хоста
                url = line.replace(
                    f"https://{OLD_HOST}",
                    f"https://{NEW_HOST}"
                )

                result.append(extinf)
                result.append(url)
                found += 1

        i += 1

    # Запись результата с копирайтом
    try:
        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8",
            newline="\n"
        ) as f:
            f.write("\n".join(result) + "\n")
    except IOError as e:
        print(f"\n[ERROR] Ошибка записи файла: {e}")
        return

    # Итоговый отчёт со шкалой статуса и копирайтом
    print()
    print("==============================================")
    print("[ OK ] ОБРАБОТКА УСПЕШНО ЗАВЕРШЕНА")
    print("==============================================")
    print(f" Автор / Copyright        : {COPYRIGHT}")
    print(f" Найдено Cinerama потоков : {found}")
    print(f" Старая адресация         : {OLD_HOST}")
    print(f" Новая адресация          : {NEW_HOST}")
    print(f" Новая группа             : {NEW_GROUP}")
    print(f" Итоговый файл            : {OUTPUT_FILE}")
    print("==============================================")


if __name__ == "__main__":
    main()
