# ====================
# CINERAMA STREAM8 → STREAM1
# © Phoenix 89S. All rights reserved.
# ====================

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


def replace_group_title(extinf: str) -> str:
    """Меняет или добавляет group-title."""
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
    print("==============================================\n")

    print("[INFO] Загружаем исходный M3U...")

    try:
        response = requests.get(
            SOURCE_URL,
            timeout=60,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить плейлист: {e}")
        return

    lines = response.text.splitlines()
    total_lines = len(lines)

    result = [
        "#EXTM3U",
        f"# Playlist optimized by {COPYRIGHT} - {NEW_GROUP}"
    ]

    found = 0

    print(f"[INFO] Сканирование и обработка потоков ({total_lines} строк)...")

    for i in range(1, total_lines):
        line = lines[i].strip()

        if OLD_HOST in line:
            extinf = lines[i - 1].strip()
            if extinf.startswith("#EXTINF:"):
                extinf = replace_group_title(extinf)
                url = line.replace(
                    f"https://{OLD_HOST}",
                    f"https://{NEW_HOST}"
                )
                result.append(extinf)
                result.append(url)
                found += 1

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(result) + "\n")
    except Exception as e:
        print(f"[ERROR] Ошибка записи файла: {e}")
        return

    print("\n==============================================")
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