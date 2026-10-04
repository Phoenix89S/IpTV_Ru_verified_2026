# ====================
# CINERAMA STREAM8 → STREAM1 SCAN + VERIFY
# ============================================================
# © Phoenix 89S. All rights reserved.

import os
import re
import time
import concurrent.futures
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

START_PORT = 0
END_PORT = 6000
REQUEST_TIMEOUT = 3
MAX_WORKERS = 50


def replace_group_title(extinf):
    pattern = r'group-title="[^"]*"'
    if re.search(pattern, extinf, flags=re.IGNORECASE):
        return re.sub(pattern, f'group-title="{NEW_GROUP}"', extinf, count=1, flags=re.IGNORECASE)

    comma_pos = extinf.find(",")
    if comma_pos != -1:
        return extinf[:comma_pos] + f' group-title="{NEW_GROUP}"' + extinf[comma_pos:]
    return extinf


def check_url(url):
    try:
        r = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        if 200 <= r.status_code < 300:
            return True, r.status_code, "HEAD"
    except Exception:
        pass

    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        if 200 <= r.status_code < 300:
            return True, r.status_code, "GET"
        return False, r.status_code, "GET"
    except Exception as e:
        return False, None, f"ERR:{type(e).__name__}"


def build_candidate_urls():
    return [
        (
            i,
            f"https://{OLD_HOST}/{i}/tracks-v1a1/mono.m3u8",
            f"https://{NEW_HOST}/{i}/tracks-v1a1/mono.m3u8",
        )
        for i in range(START_PORT, END_PORT + 1)
    ]


def main():
    print("==============================================")
    print(f"     CINERAMA STREAM8 → STREAM1 SCAN | {COPYRIGHT}")
    print("==============================================")
    print()
    print(f"[INFO] Генерируем и проверяем URL от {START_PORT} до {END_PORT}...")
    print(f"[INFO] Проверка: HEAD -> GET fallback, timeout={REQUEST_TIMEOUT}s, workers={MAX_WORKERS}")

    log = []
    log.append("=== CINERAMA STREAM8 → STREAM1 SCAN REPORT ===")
    log.append(f"Дата запуска: {datetime.utcnow()} UTC")
    log.append(f"Диапазон: {START_PORT}..{END_PORT}")
    log.append(f"Проверка: HEAD, затем GET fallback")
    log.append("")

    start_time = time.time()
    candidates = build_candidate_urls()

    good_items = []
    checked = 0
    old_ok = 0
    new_ok = 0
    total_olds = 0
    total_news = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}
        for idx, old_url, new_url in candidates:
            future_map[executor.submit(check_url, old_url)] = ("old", idx, old_url, new_url)
            future_map[executor.submit(check_url, new_url)] = ("new", idx, old_url, new_url)

        for future in concurrent.futures.as_completed(future_map):
            kind, idx, old_url, new_url = future_map[future]
            try:
                ok, status, method = future.result()
            except Exception as e:
                ok, status, method = False, None, f"ERR:{type(e).__name__}"

            checked += 1

            if kind == "old":
                total_olds += 1
                log.append(f"[OLD] #{idx}: {old_url} -> {ok} status={status} method={method}")
                if ok:
                    old_ok += 1
            else:
                total_news += 1
                log.append(f"[NEW] #{idx}: {new_url} -> {ok} status={status} method={method}")
                if ok:
                    new_ok += 1

                # Ваша логика: только если новый stream1 отвечает 200/2xx
                if ok:
                    # Проверяем старый тоже
                    old_status_result = {}
                    for future2 in [future_map.get(...)]:  # не используется, оставил для визуальной ясности
                        pass

    # Перепроверка: корректный вариант по вашему сценарию:
    # Сначала собираем список удачных "old"/"new" пар в одном цикле.
    old_results = {}
    new_results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}

        for idx, old_url, new_url in candidates:
            futures[executor.submit(check_url, old_url)] = ("old", idx, old_url)
            futures[executor.submit(check_url, new_url)] = ("new", idx, new_url)

        for future in concurrent.futures.as_completed(futures):
            kind, idx, url = futures[future]
            try:
                ok, status, method = future.result()
            except Exception as e:
                ok, status, method = False, None, f"ERR:{type(e).__name__}"

            if kind == "old":
                old_results[idx] = (ok, status, method, url)
            else:
                new_results[idx] = (ok, status, method, url)

    result = ["#EXTM3U", f"# Playlist optimized by {COPYRIGHT} - {NEW_GROUP}"]
    found = 0

    for idx in range(START_PORT, END_PORT + 1):
        old_ok_v, old_status, old_method, old_url = old_results.get(idx, (False, None, "N/A", ""))
        new_ok_v, new_status, new_method, new_url = new_results.get(idx, (False, None, "N/A", ""))

        # Обязательное правило: без fallback
        if new_ok_v:
            found += 1
            result.append(f'#EXTINF:-1 group-title="{NEW_GROUP}", Cinerama {idx}')
            result.append(new_url)

            log.append(f"[INCLUDE] #{idx}: добавлен в плейлист -> {new_url}")
        else:
            log.append(f"[SKIP] #{idx}: новый URL не ответил 200/2xx -> {new_url} (status={new_status})")

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(result) + "\n")
    except Exception as e:
        print(f"[ERROR] Ошибка записи M3U: {e}")
        return

    log.append("")
    log.append("=== ИТОГОВЫЙ ОТЧЁТ ===")
    log.append(f"Найдено и включено в итоговый плейлист: {found}")
    log.append(f"Обработано URL: {checked}")
    log.append(f"Успешный OLD_HOST: {old_ok}")
    log.append(f"Успешный NEW_HOST: {new_ok}")
    log.append(f"Время выполнения: {time.time() - start_time:.2f}s")
    log.append("=== Конец отчёта ===")

    with open(REPORT_FILE, "w", encoding="utf-8") as rep:
        rep.write("\n".join(log))

    print(f"[INFO] Файл успешно создан: {OUTPUT_FILE}")
    print(f"[INFO] Отчёт создан: {REPORT_FILE}")
    print()
    print("==============================================")
    print("[ OK ] ОБРАБОТКА ЗАВЕРШЕНА")
    print("==============================================")
    print(f" Автор / Copyright        : {COPYRIGHT}")
    print(f" Проверено URL            : {checked}")
    print(f" Включено в M3U           : {found}")
    print(f" Старая адресация         : {OLD_HOST}")
    print(f" Новая адресация          : {NEW_HOST}")
    print(f" Диапазон                 : {START_PORT}..{END_PORT}")
    print(f" Новая группа             : {NEW_GROUP}")
    print(f" Итоговый файл            : {OUTPUT_FILE}")
    print(f" Отчёт                    : {REPORT_FILE}")
    print("==============================================")


if __name__ == "__main__":
    main()
