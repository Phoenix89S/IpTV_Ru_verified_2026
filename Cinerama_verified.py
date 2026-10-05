# ============================================================
#       CINERAMA VERIFIED 1
# ============================================================
# © Phoenix 89S. All rights reserved.

import os
import re
import requests

from datetime import datetime
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# НАСТРОЙКИ
# ============================================================

MAX_THREADS = 50
TIMEOUT = 2

START_ID = 1
END_ID = 6000

STREAM8_BASE = "https://stream8.cinerama.uz"

VERIFY_GROUP = "Verify 1"
COPYRIGHT = "© Phoenix 89S"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# ФАЙЛЫ
# ============================================================

PREVIOUS_M3U_FILE = os.path.join(
    BASE_DIR,
    "CINERAMA_VERIFIED.m3u"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "cinerama_Verified_1.m3u"
)

REPORT_FILE = os.path.join(
    BASE_DIR,
    "SKALA_DREG_REPORT.txt"
)


# ============================================================
# HTTP
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Referer": "https://github.com/"
}


# ============================================================
# URL
# ============================================================

def build_stream_url(stream, cid):
    return (
        f"https://{stream}.cinerama.uz/"
        f"{cid}/tracks-v1a1/mono.m3u8"
    )


# ============================================================
# STREAM
# ============================================================

def get_stream_group(url):
    url = url.lower()

    if "stream8.cinerama.uz" in url:
        return "Stream8"

    if "stream0.cinerama.uz" in url:
        return "Stream0"

    if "stream1.cinerama.uz" in url:
        return "Stream1"

    return "Unknown"


# ============================================================
# ID
# ============================================================

def extract_cinerama_id(url):
    match = re.search(
        r"cinerama\.uz/(\d+)(?:/|$)",
        url,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None


# ============================================================
# ПОЛУЧЕНИЕ НАЗВАНИЯ КАНАЛА
# ============================================================

def extract_channel_name(text):
    if not text:
        return None

    for line in text.splitlines():
        line = line.strip()

        if not line.startswith("#EXTINF:"):
            continue

        if "," not in line:
            continue

        name = line.split(",", 1)[1].strip()

        if name:
            return name

    return None


# ============================================================
# ПРОВЕРКА STREAM8
# ============================================================

def check_stream8(stream_id):

    url = build_stream_url(
        "stream8",
        stream_id
    )

    session = requests.Session()
    session.headers.update(HEADERS)

    try:

        # ----------------------------------------------------
        # Сначала HEAD — быстрая проверка
        # ----------------------------------------------------

        response = session.head(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        if response.status_code != 200:
            return None

        # ----------------------------------------------------
        # Затем GET — получаем название
        # ----------------------------------------------------

        response = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        if response.status_code not in (200, 206):
            return None

        name = extract_channel_name(
            response.text
        )

        if not name:
            return None

        return {
            "id": stream_id,
            "name": name,
            "url": url,
            "group": "Stream8"
        }

    except Exception:
        return None

    finally:
        try:
            session.close()
        except Exception:
            pass


# ============================================================
# МНОГОПОТОЧНЫЙ СКАНЕР STREAM8
# ============================================================

def scan_stream8(log):

    found = []

    total = END_ID - START_ID + 1

    print()
    print("================================================")
    print("        МНОГОПОТОЧНАЯ ПРОВЕРКА STREAM8")
    print("================================================")
    print(f"ID: {START_ID} → {END_ID}")
    print(f"Потоков: {MAX_THREADS}")
    print(f"Всего ID: {total}")
    print()

    log.append("")
    log.append("=== МНОГОПОТОЧНЫЙ ПРОХОД STREAM8 ===")
    log.append(f"Диапазон: {START_ID} → {END_ID}")
    log.append(f"MAX_THREADS: {MAX_THREADS}")
    log.append(f"TIMEOUT: {TIMEOUT}")

    completed = 0

    with ThreadPoolExecutor(
        max_workers=MAX_THREADS
    ) as executor:

        futures = {
            executor.submit(
                check_stream8,
                stream_id
            ): stream_id
            for stream_id in range(
                START_ID,
                END_ID + 1
            )
        }

        for future in as_completed(futures):

            completed += 1

            try:
                result = future.result()
            except Exception:
                result = None

            if result:

                found.append(result)

                print(
                    f"\n[FOUND] Stream8 "
                    f"ID={result['id']:<5} "
                    f"{result['name']}"
                )

                log.append(
                    f"[FOUND] Stream8 | "
                    f"ID={result['id']} | "
                    f"{result['name']} | "
                    f"{result['url']}"
                )

            print(
                f"Прогресс: {completed}/{total}",
                end="\r"
            )

    found.sort(
        key=lambda x: x["id"]
    )

    print()
    print(
        f"[SCAN] Найдено Stream8: {len(found)}"
    )

    log.append(
        f"Найдено Stream8: {len(found)}"
    )

    return found


# ============================================================
# СОЗДАНИЕ STREAM0 + STREAM1
# ============================================================

def create_mirrors(
    stream8_entries,
    log
):

    stream0_entries = []
    stream1_entries = []

    log.append("")
    log.append(
        "=== СОЗДАНИЕ STREAM0 + STREAM1 ==="
    )

    for item in stream8_entries:

        cid = item["id"]
        name = item["name"]

        # ----------------------------------------------------
        # Stream0
        # ----------------------------------------------------

        stream0_item = {
            "id": cid,
            "name": name,
            "url": build_stream_url(
                "stream0",
                cid
            ),
            "group": "Stream0"
        }

        stream0_entries.append(
            stream0_item
        )

        # ----------------------------------------------------
        # Stream1
        # ----------------------------------------------------

        stream1_item = {
            "id": cid,
            "name": name,
            "url": build_stream_url(
                "stream1",
                cid
            ),
            "group": "Stream1"
        }

        stream1_entries.append(
            stream1_item
        )

        log.append(
            f"[MIRROR] ID={cid} | "
            f"{name} | "
            f"Stream8 → Stream0 + Stream1"
        )

    log.append(
        f"Stream0 создано: {len(stream0_entries)}"
    )

    log.append(
        f"Stream1 создано: {len(stream1_entries)}"
    )

    return (
        stream0_entries,
        stream1_entries
    )


# ============================================================
# КЛЮЧ ЗАПИСИ
# ============================================================

def make_key(item):
    return (
        item["group"],
        item["id"]
    )


# ============================================================
# ЧТЕНИЕ СТАРОГО M3U
# ============================================================

def load_previous_m3u(
    text,
    log
):

    previous = OrderedDict()

    if not text:
        return previous

    current_extinf = None

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):

            current_extinf = line
            continue

        if (
            current_extinf
            and line.startswith(
                ("http://", "https://")
            )
        ):

            url = line

            cid = extract_cinerama_id(url)
            group = get_stream_group(url)

            if (
                cid is not None
                and group != "Unknown"
            ):

                if "," in current_extinf:
                    name = (
                        current_extinf
                        .split(",", 1)[1]
                        .strip()
                    )
                else:
                    name = ""

                item = {
                    "id": cid,
                    "name": name,
                    "url": url,
                    "group": group
                }

                previous[
                    make_key(item)
                ] = item

            current_extinf = None

    log.append(
        f"[OLD] Старый M3U: "
        f"{len(previous)} записей"
    )

    return previous


# ============================================================
# ФОРМИРОВАНИЕ ТЕКУЩЕГО НАБОРА
# ============================================================

def build_current(
    stream8_entries,
    stream0_entries,
    stream1_entries,
    log
):

    current = OrderedDict()

    # ОРИГИНАЛЬНЫЙ STREAM8
    for item in stream8_entries:
        current[
            make_key(item)
        ] = item

    # STREAM0
    for item in stream0_entries:
        current[
            make_key(item)
        ] = item

    # STREAM1
    for item in stream1_entries:
        current[
            make_key(item)
        ] = item

    log.append("")
    log.append(
        "=== ТЕКУЩИЙ НАБОР ==="
    )

    log.append(
        f"Всего записей: {len(current)}"
    )

    return current


# ============================================================
# СРАВНЕНИЕ
# ============================================================

def compare_results(
    previous,
    current,
    log
):

    match = []
    changed = []
    new = []
    missing = []

    all_keys = sorted(
        set(previous.keys()) |
        set(current.keys()),
        key=lambda x: (
            x[1],
            x[0]
        )
    )

    log.append("")
    log.append(
        "================================================"
    )
    log.append(
        "             СРАВНЕНИЕ ПРОХОДОВ"
    )
    log.append(
        "================================================"
    )

    for key in all_keys:

        old = previous.get(key)
        cur = current.get(key)

        if old and cur:

            if (
                old["name"] == cur["name"]
                and old["url"] == cur["url"]
                and old["group"] == cur["group"]
            ):

                match.append(cur)

                log.append(
                    f"[MATCH] "
                    f"{cur['group']} "
                    f"ID={cur['id']} | "
                    f"{cur['name']}"
                )

            else:

                changed.append({
                    "old": old,
                    "new": cur
                })

                log.append(
                    f"[CHANGED] "
                    f"{cur['group']} "
                    f"ID={cur['id']}"
                )

                log.append(
                    f"  OLD NAME: {old['name']}"
                )

                log.append(
                    f"  OLD URL : {old['url']}"
                )

                log.append(
                    f"  NEW NAME: {cur['name']}"
                )

                log.append(
                    f"  NEW URL : {cur['url']}"
                )

        elif cur:

            new.append(cur)

            log.append(
                f"[NEW] "
                f"{cur['group']} "
                f"ID={cur['id']} | "
                f"{cur['name']}"
            )

        elif old:

            missing.append(old)

            log.append(
                f"[MISSING] "
                f"{old['group']} "
                f"ID={old['id']} | "
                f"{old['name']}"
            )

    return (
        match,
        changed,
        new,
        missing
    )


# ============================================================
# EXTINF
# ============================================================

def make_extinf(
    item,
    channel_number
):

    return (
        f'#EXTINF:-1 '
        f'tvg-chno="{channel_number}" '
        f'tvg-id="cinerama_{item["id"]}" '
        f'group-title="{item["group"]}",'
        f'{item["name"]}'
    )


# ============================================================
# ЗАПИСЬ M3U
# ============================================================

def write_playlist(current):

    stream_order = {
        "Stream8": 0,
        "Stream0": 1,
        "Stream1": 2
    }

    sorted_items = sorted(
        current.values(),
        key=lambda x: (
            x["id"],
            stream_order.get(
                x["group"],
                99
            )
        )
    )

    result = [
        "#EXTM3U",
        (
            f"# Playlist verified by "
            f"{COPYRIGHT} - {VERIFY_GROUP}"
        )
    ]

    for index, item in enumerate(
        sorted_items,
        start=1
    ):

        result.append(
            make_extinf(
                item,
                index
            )
        )

        result.append(
            item["url"]
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as f:

        f.write(
            "\n".join(result)
            + "\n"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "================================================"
    )
    print(
        f"      CINERAMA VERIFIED 1 | {COPYRIGHT}"
    )
    print(
        "================================================"
    )
    print()

    log = []

    log.append(
        "=== CINERAMA VERIFIED 1 REPORT ==="
    )

    log.append(
        f"Дата запуска: "
        f"{datetime.utcnow()} UTC"
    )

    log.append("")

    # ========================================================
    # 1. ЗАГРУЗКА СТАРОГО M3U
    # ========================================================

    previous = OrderedDict()

    print(
        "[INFO] Проверяем предыдущий M3U..."
    )

    if os.path.exists(
        PREVIOUS_M3U_FILE
    ):

        try:

            with open(
                PREVIOUS_M3U_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                previous_text = f.read()

            previous = load_previous_m3u(
                previous_text,
                log
            )

            print(
                f"[INFO] Загружено старых "
                f"записей: {len(previous)}"
            )

        except Exception as e:

            print(
                f"[WARN] Ошибка старого M3U: {e}"
            )

            log.append(
                f"[WARN] {e}"
            )

    else:

        print(
            "[INFO] Старый M3U не найден"
        )

        log.append(
            "[INFO] Старый M3U не найден"
        )

    # ========================================================
    # 2. МНОГОПОТОЧНАЯ ПРОВЕРКА STREAM8
    # ========================================================

    stream8_entries = scan_stream8(
        log
    )

    # ========================================================
    # 3. СОЗДАЁМ STREAM0 + STREAM1
    # ========================================================

    (
        stream0_entries,
        stream1_entries
    ) = create_mirrors(
        stream8_entries,
        log
    )

    # ========================================================
    # 4. СОХРАНЯЕМ ВСЕ ТРИ STREAM
    # ========================================================

    current = build_current(
        stream8_entries,
        stream0_entries,
        stream1_entries,
        log
    )

    # ========================================================
    # 5. СРАВНЕНИЕ СО СТАРЫМ
    # ========================================================

    (
        match,
        changed,
        new,
        missing
    ) = compare_results(
        previous,
        current,
        log
    )

    # ========================================================
    # 6. СОЗДАНИЕ НОВОГО M3U
    # ========================================================

    try:

        write_playlist(
            current
        )

    except Exception as e:

        print(
            f"[ERROR] Ошибка записи "
            f"{OUTPUT_FILE}: {e}"
        )

        log.append(
            f"[ERROR] OUTPUT: {e}"
        )

        return

    # ========================================================
    # 7. СТАТИСТИКА
    # ========================================================

    stream8_count = sum(
        1
        for item in current.values()
        if item["group"] == "Stream8"
    )

    stream0_count = sum(
        1
        for item in current.values()
        if item["group"] == "Stream0"
    )

    stream1_count = sum(
        1
        for item in current.values()
        if item["group"] == "Stream1"
    )

    final_count = len(current)

    log.append("")
    log.append(
        "================================================"
    )
    log.append(
        "                  ИТОГ"
    )
    log.append(
        "================================================"
    )

    log.append(
        f"Старый M3U     : {len(previous)}"
    )

    log.append(
        f"Stream8        : {stream8_count}"
    )

    log.append(
        f"Stream0        : {stream0_count}"
    )

    log.append(
        f"Stream1        : {stream1_count}"
    )

    log.append(
        f"ВСЕГО ПОТОКОВ  : {final_count}"
    )

    log.append(
        f"MATCH          : {len(match)}"
    )

    log.append(
        f"CHANGED        : {len(changed)}"
    )

    log.append(
        f"NEW            : {len(new)}"
    )

    log.append(
        f"MISSING        : {len(missing)}"
    )

    log.append("")

    log.append(
        "Старый M3U используется "
        "только для сравнения."
    )

    log.append(
        "Старые записи не переносятся "
        "в новый результат."
    )

    log.append(
        "Каждый найденный Stream8 "
        "сохраняется как оригинал."
    )

    log.append(
        "Для каждого найденного Stream8 "
        "создаются Stream0 и Stream1."
    )

    log.append(
        f"Итоговый файл: {OUTPUT_FILE}"
    )

    log.append(
        f"Отчёт: {REPORT_FILE}"
    )

    # ========================================================
    # 8. ОТЧЁТ
    # ========================================================

    try:

        with open(
            REPORT_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "\n".join(log)
            )

    except Exception as e:

        print(
            f"[WARN] Ошибка записи отчёта: {e}"
        )

    # ========================================================
    # 9. ФИНАЛ
    # ========================================================

    print()

    print(
        "================================================"
    )
    print(
        "[ OK ] CINERAMA VERIFIED 1 ЗАВЕРШЁН"
    )
    print(
        "================================================"
    )

    print(
        f" Stream8        : {stream8_count}"
    )

    print(
        f" Stream0        : {stream0_count}"
    )

    print(
        f" Stream1        : {stream1_count}"
    )

    print(
        f" ВСЕГО ПОТОКОВ  : {final_count}"
    )

    print(
        f" MATCH          : {len(match)}"
    )

    print(
        f" CHANGED        : {len(changed)}"
    )

    print(
        f" NEW            : {len(new)}"
    )

    print(
        f" MISSING        : {len(missing)}"
    )

    print()

    print(
        f"Плейлист: {OUTPUT_FILE}"
    )

    print(
        f"Отчёт:    {REPORT_FILE}"
    )

    print(
        "================================================"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()