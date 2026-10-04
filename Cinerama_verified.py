# ====================
#              CINERAMA STREAM8 → STREAM1
# ============================================================
# © Phoenix 89S. All rights reserved.

import os
import re
import requests
from datetime import datetime

SOURCE_URL = (
    "https://raw.githubusercontent.com/IPTVRU2026/IPTVMIR/"
    "refs/heads/main/IPTV_MEGA_PLAYLIST.m3u"
)

BASE_DIR = os.path.dirname(__file__)
OUTPUT_FILE = os.path.join(BASE_DIR, "CINERAMA_VERIFIED.m3u")
REPORT_FILE = os.path.join(BASE_DIR, "SKALA_DREG_REPORT.txt")

OLD_HOST = "stream8.cinerama.uz"
NEW_HOST = "stream1.cinerama.uz"
NEW_GROUP = "Verified channels"
COPYRIGHT = "© Phoenix 89S"


def replace_group_title(extinf):
    pattern = r'group-title="[^"]*"'
    if re.search(pattern, extinf, flags=re.IGNORECASE):
        return re.sub(pattern, f'group-title="{NEW_GROUP}"', extinf, count=1, flags=re.IGNORECASE)

    comma_pos = extinf.find(",")
    if comma_pos != -1:
        return extinf[:comma_pos] + f' group-title="{NEW_GROUP}"' + extinf[comma_pos:]
    return extinf


def main():
    print("==============================================")
    print(f"     CINERAMA STREAM8 → STREAM1 | {COPYRIGHT}")
    print("==============================================")
    print()
    print("[INFO] Загружаем исходный M3U...")

    log = []
    log.append("=== SCALA‑DREG STREAM PROCESSOR REPORT ===")
    log.append(f"Дата запуска: {datetime.utcnow()} UTC")
    log.append("")

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
    processed = 0
    skipped = 0
    needs_review = 0

    print(f"[INFO] Сканирование и обработка потоков ({total_lines} строк)...")

    for i in range(1, total_lines):
        line = lines[i].strip()

        if OLD_HOST in line:
            extinf = lines[i - 1].strip()

            if extinf.startswith("#EXTINF:"):
                processed += 1
                log.append(f"[DREG] Обработка EXTINF → {extinf}")

                extinf_new = replace_group_title(extinf)
                url_new = line.replace(f"https://{OLD_HOST}", f"https://{NEW_HOST}")

                log.append(f"[DREG] Замена хоста: {OLD_HOST} → {NEW_HOST}")
                log.append(f"[DREG] Итоговый URL: {url_new}")
                log.append("")

                result.append(extinf_new)
                result.append(url_new)
                found += 1
            else:
                skipped += 1
                log.append(f"[WARN] Найден поток без EXTINF → {line}")
                needs_review += 1

    # Запись M3U
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(result) + "\n")
    except Exception as e:
        print(f"[ERROR] Ошибка записи файла: {e}")
        return

    # Проверка создания файла
    if not os.path.exists(OUTPUT_FILE):
        print(f"[ERROR] Файл не создан: {OUTPUT_FILE}")
        return

    print(f"[INFO] Файл успешно создан: {OUTPUT_FILE}")

    # Итоговый SKALA‑DREG отчёт
    log.append("=== ИТОГОВЫЙ ОТЧЁТ SCALA‑DREG ===")
    log.append(f"Получено ссылок: {found + skipped}")
    log.append(f"Обработано ссылок: {processed}")
    log.append(f"Не обработано ссылок: {skipped}")
    log.append(f"Требует перепроверки: {needs_review}")
    log.append("")
    log.append("=== Конец отчёта ===")

    # Запись отчёта
    with open(REPORT_FILE, "w", encoding="utf-8") as rep:
        rep.write("\n".join(log))

    print(f"[INFO] Отчёт создан: {REPORT_FILE}")

    # Финальный вывод
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
    print(f" Отчёт SCALA‑DREG         : {REPORT_FILE}")
    print("==============================================")


if __name__ == "__main__":
    main()