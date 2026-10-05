# ====================
#       CINERAMA VERIFIED 1
# ============================================================
# © Phoenix 89S. All rights reserved.

import os
import re
import requests
from datetime import datetime
from collections import OrderedDict


# ============================================================
# НАСТРОЙКИ
# ============================================================

SOURCE_URL = (
    "https://raw.githubusercontent.com/IPTVRU2026/IPTVMIR/"
    "refs/heads/main/IPTV_MEGA_PLAYLIST.m3u"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Старый рабочий файл — используется ТОЛЬКО для сравнения
PREVIOUS_M3U_FILE = os.path.join(
    BASE_DIR,
    "CINERAMA_VERIFIED.m3u"
)

# Новый итоговый файл
OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "cinerama_Verified_1.m3u"
)

REPORT_FILE = os.path.join(
    BASE_DIR,
    "SKALA_DREG_REPORT.txt"
)

START_ID = 0
END_ID = 6000


# ============================================================
# CINERAMA
# ============================================================

STREAM8_BASE = "http://stream8.cinerama.uz"

VERIFY_GROUP = "Verify 1"
COPYRIGHT = "© Phoenix 89S"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Referer": "https://github.com/"
}


# ============================================================
# ЗАГРУЗКА
# ============================================================

def fetch_text(session, url, timeout=10):
    try:
        response = session.get(
            url,
            timeout=timeout,
            headers=HEADERS,
            allow_redirects=True
        )

        if response.status_code in (200, 206):
            return response.text

    except requests.RequestException:
        pass
    except Exception:
        pass

    return None


# ============================================================
# EXTINF
# ============================================================

def extract_extinf_names(m3u_text):
    """
    Извлекает названия каналов из EXTINF.
    Работает построчно, чтобы случайные переносы
    внутри M3U не ломали результат.
    """

    if not m3u_text:
        return []

    result = []

    for line in m3u_text.splitlines():
        line = line.strip()

        if not line.startswith("#EXTINF:"):
            continue

        if "," not in line:
            continue

        name = line.split(",", 1)[1].strip()

        if name and not name.startswith("http"):
            result.append(name)

    return result


# ============================================================
# URL
# ============================================================

def build_stream_url(base, cid):
    return f"{base}/{cid}/tracks-v1a1/mono.m3u8"


# ============================================================
# ОПРЕДЕЛЕНИЕ STREAM
# ============================================================

def get_stream_group(url):
    url_lower = url.lower()

    if "stream8.cinerama.uz" in url_lower:
        return "Stream8"

    if "stream0.cinerama.uz" in url_lower:
        return "Stream0"

    if "stream1.cinerama.uz" in url_lower:
        return "Stream1"

    return "Unknown"


# ============================================================
# ИЗВЛЕЧЕНИЕ ID
# ============================================================

def extract_cinerama_id(url):
    """
    Поддерживает:
        stream8.cinerama.uz/123/...
        stream0.cinerama.uz/123/...
        stream1.cinerama.uz/123/...
    """

    match = re.search(
        r'cinerama\.uz/(\d+)(?:/|$)',
        url,
        flags=re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None


# ============================================================
# КЛЮЧ ЗАПИСИ
# ============================================================

def make_key(item):
    """
    Ключ теперь содержит STREAM + ID.

    Это КРИТИЧНО.

    Раньше:
        123

    Теперь:
        ("Stream8", 123)
        ("Stream0", 123)
        ("Stream1", 123)

    Поэтому три потока одного канала
    больше не уничтожают друг друга.
    """

    return (
        item["group"],
        item["id"]
    )


# ============================================================
# ЧТЕНИЕ СТАРОГО M3U
# ============================================================

def load_previous_m3u(text, log):
    previous = OrderedDict()

    if not text:
        return previous

    lines = text.splitlines()
    current_extinf = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current_extinf = line
            continue

        if (
            current_extinf
            and line.startswith(("http://", "https://"))
        ):
            url = line

            cid = extract_cinerama_id(url)
            group = get_stream_group(url)

            if cid is not None and group != "Unknown":

                if "," in current_extinf:
                    name = current_extinf.split(",", 1)[1].strip()
                else:
                    name = ""

                item = {
                    "id": cid,
                    "name": name,
                    "url": url,
                    "group": group
                }

                key = make_key(item)

                previous[key] = item

            current_extinf = None

    stream8_count = sum(
        1 for item in previous.values()
        if item["group"] == "Stream8"
    )

    stream0_count = sum(
        1 for item in previous.values()
        if item["group"] == "Stream0"
    )

    stream1_count = sum(
        1 for item in previous.values()
        if item["group"] == "Stream1"
    )

    log.append(
        f"[OLD] Предыдущий M3U: {len(previous)} записей"
    )

    log.append(
        f"[OLD] Stream8={stream8_count} | "
        f"Stream0={stream0_count} | "
        f"Stream1={stream1_count}"
    )

    return previous


# ============================================================
# НОВЫЙ ПРОХОД: STREAM8
# ============================================================

def scan_stream8(session, base, start_id, end_id, log):

    found = []

    print()
    print(
        f"[SCAN] Stream8: "
        f"{start_id} → {end_id}"
    )

    log.append("")
    log.append("=== НОВЫЙ ПРОХОД Stream8 ===")
    log.append(
        f"Диапазон: {start_id} → {end_id}"
    )

    for cid in range(start_id, end_id + 1):

        url = build_stream_url(base, cid)

        text = fetch_text(
            session,
            url
        )

        if not text:
            continue

        names = extract_extinf_names(text)

        if not names:
            continue

        name = names[0].strip()

        if not name:
            continue

        item = {
            "id": cid,
            "name": name,
            "url": url,
            "group": "Stream8"
        }

        found.append(item)

        print(
            f"[FOUND] Stream8 "
            f"ID={cid:<5} {name}"
        )

        log.append(
            f"[FOUND] Stream8 "
            f"ID={cid} | {name} | {url}"
        )

    log.append(
        f"Найдено Stream8: {len(found)}"
    )

    return found


# ============================================================
# ЗЕРКАЛА
# Stream8 → Stream0
# Stream8 → Stream1
# ============================================================

def create_mirror_streams(stream8_entries, log):

    stream0_entries = []
    stream1_entries = []

    log.append("")
    log.append(
        "=== РАСХОЖДЕНИЕ Stream8 → Stream0 + Stream1 ==="
    )

    for item in stream8_entries:

        # ----------------------------------------------------
        # Stream0
        # ----------------------------------------------------

        item0 = {
            "id": item["id"],
            "name": item["name"],
            "url": item["url"].replace(
                "stream8.cinerama.uz",
                "stream0.cinerama.uz"
            ),
            "group": "Stream0"
        }

        stream0_entries.append(item0)

        # ----------------------------------------------------
        # Stream1
        # ----------------------------------------------------

        item1 = {
            "id": item["id"],
            "name": item["name"],
            "url": item["url"].replace(
                "stream8.cinerama.uz",
                "stream1.cinerama.uz"
            ),
            "group": "Stream1"
        }

        stream1_entries.append(item1)

        log.append(
            f"[MIRROR] ID={item['id']} | "
            f"{item['name']} | "
            f"Stream8 → Stream0 + Stream1"
        )

    log.append(
        f"Stream0 создано: {len(stream0_entries)}"
    )

    log.append(
        f"Stream1 создано: {len(stream1_entries)}"
    )

    return stream0_entries, stream1_entries


# ============================================================
# ФОРМИРОВАНИЕ ВСЕХ ТРЁХ STREAM
# ============================================================

def build_current_entries(
    stream8_entries,
    stream0_entries,
    stream1_entries,
    log
):
    """
    ВАЖНО:

    Итог содержит ВСЕ ТРИ потока:

        Stream8
        Stream0
        Stream1

    Один ID не удаляет остальные потоки.
    """

    current = OrderedDict()

    # --------------------------------------------------------
    # Сначала оригинальный Stream8
    # --------------------------------------------------------

    for item in stream8_entries:

        key = make_key(item)

        if key not in current:
            current[key] = item

    # --------------------------------------------------------
    # Затем Stream0
    # --------------------------------------------------------

    for item in stream0_entries:

        key = make_key(item)

        if key not in current:
            current[key] = item

    # --------------------------------------------------------
    # Затем Stream1
    # --------------------------------------------------------

    for item in stream1_entries:

        key = make_key(item)

        if key not in current:
            current[key] = item

    # --------------------------------------------------------
    # Статистика
    # --------------------------------------------------------

    stream8_count = sum(
        1 for item in current.values()
        if item["group"] == "Stream8"
    )

    stream0_count = sum(
        1 for item in current.values()
        if item["group"] == "Stream0"
    )

    stream1_count = sum(
        1 for item in current.values()
        if item["group"] == "Stream1"
    )

    log.append("")
    log.append("=== ФОРМИРОВАНИЕ VERIFY 1 ===")
    log.append(
        f"Итоговый Stream8: {stream8_count}"
    )
    log.append(
        f"Итоговый Stream0: {stream0_count}"
    )
    log.append(
        f"Итоговый Stream1: {stream1_count}"
    )
    log.append(
        f"Всего потоков: {len(current)}"
    )

    return current


# ============================================================
# СРАВНЕНИЕ
# ============================================================

def compare_results(previous, current, log):

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
        "=============================================="
    )
    log.append(
        "             СРАВНЕНИЕ ПРОХОДОВ"
    )
    log.append(
        "=============================================="
    )

    for key in all_keys:

        old = previous.get(key)
        cur = current.get(key)

        if old and cur:

            if (
                old["url"] == cur["url"]
                and old["name"] == cur["name"]
                and old["group"] == cur["group"]
            ):
                match.append(cur)

                log.append(
                    f"[MATCH] "
                    f"{cur['group']} "
                    f"ID={cur['id']} | "
                    f"{cur['name']} | "
                    f"{cur['url']}"
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
                    f"  OLD NAME : {old['name']}"
                )

                log.append(
                    f"  OLD URL  : {old['url']}"
                )

                log.append(
                    f"  NEW NAME : {cur['name']}"
                )

                log.append(
                    f"  NEW URL  : {cur['url']}"
                )

        elif cur and not old:

            new.append(cur)

            log.append(
                f"[NEW] "
                f"{cur['group']} "
                f"ID={cur['id']} | "
                f"{cur['name']} | "
                f"{cur['url']}"
            )

        elif old and not cur:

            missing.append(old)

            log.append(
                f"[MISSING] "
                f"{old['group']} "
                f"ID={old['id']} | "
                f"{old['name']} | "
                f"{old['url']}"
            )

    return (
        match,
        changed,
        new,
        missing
    )


# ============================================================
# СТРОКА EXTINF
# ============================================================

def make_extinf(item):

    return (
        f'#EXTINF:-1 '
        f'tvg-id="cinerama_{item["id"]}" '
        f'group-title="{item["group"]}",'
        f'{item["name"]}'
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=============================================="
    )
    print(
        f"     CINERAMA VERIFIED 1 | {COPYRIGHT}"
    )
    print(
        "=============================================="
    )
    print()

    log = []

    log.append(
        "=== SCALA-DREG STREAM PROCESSOR REPORT ==="
    )

    log.append(
        f"Дата запуска: {datetime.utcnow()} UTC"
    )

    log.append("")

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    # ========================================================
    # 1. ПРЕДЫДУЩИЙ M3U
    # ========================================================

    previous = OrderedDict()

    print(
        "[INFO] Загружаем предыдущий M3U..."
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
                f"[INFO] Загружено "
                f"{len(previous)} записей"
            )

        except Exception as e:

            print(
                f"[WARN] Ошибка загрузки "
                f"старого M3U: {e}"
            )

            log.append(
                f"[WARN] PREVIOUS_M3U: {e}"
            )

    else:

        print(
            "[WARN] Предыдущий M3U не найден"
        )

        log.append(
            "[WARN] PREVIOUS_M3U не найден"
        )

    # ========================================================
    # 2. СКАНИРУЕМ ОРИГИНАЛЬНЫЙ STREAM8
    # ========================================================

    stream8_entries = scan_stream8(
        session,
        STREAM8_BASE,
        START_ID,
        END_ID,
        log
    )

    # ========================================================
    # 3. СОЗДАЁМ STREAM0 + STREAM1
    # ========================================================

    stream0_entries, stream1_entries = (
        create_mirror_streams(
            stream8_entries,
            log
        )
    )

    # ========================================================
    # 4. ФОРМИРУЕМ НОВЫЙ НАБОР
    #
    # ОБЯЗАТЕЛЬНО:
    # Stream8 + Stream0 + Stream1
    # ========================================================

    current = build_current_entries(
        stream8_entries,
        stream0_entries,
        stream1_entries,
        log
    )

    # ========================================================
    # 5. СРАВНЕНИЕ
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
    # 6. СОЗДАЁМ НОВЫЙ M3U
    # ========================================================

    result = [
        "#EXTM3U",
        f"# Playlist verified by "
        f"{COPYRIGHT} - {VERIFY_GROUP}"
    ]

    # Сначала сортируем по ID,
    # внутри ID порядок:
    # Stream8 → Stream0 → Stream1

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

    for item in sorted_items:

        result.append(
            make_extinf(item)
        )

        result.append(
            item["url"]
        )

    # ========================================================
    # 7. ЗАПИСЬ M3U
    # ========================================================

    try:

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

    except Exception as e:

        print(
            f"[ERROR] Ошибка записи "
            f"Verify 1: {e}"
        )

        return

    # ========================================================
    # 8. СТАТИСТИКА
    # ========================================================

    previous_count = len(previous)
    final_count = len(current)

    final_stream8 = sum(
        1
        for item in current.values()
        if item["group"] == "Stream8"
    )

    final_stream0 = sum(
        1
        for item in current.values()
        if item["group"] == "Stream0"
    )

    final_stream1 = sum(
        1
        for item in current.values()
        if item["group"] == "Stream1"
    )

    log.append("")
    log.append(
        "=============================================="
    )
    log.append(
        "              ИТОГОВАЯ СТАТИСТИКА"
    )
    log.append(
        "=============================================="
    )

    log.append(
        f"Предыдущий M3U : {previous_count}"
    )

    log.append(
        f"Stream8        : {final_stream8}"
    )

    log.append(
        f"Stream0        : {final_stream0}"
    )

    log.append(
        f"Stream1        : {final_stream1}"
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

    log.append(
        f"VERIFY 1       : {final_count}"
    )

    log.append("")

    log.append(
        "Старый M3U используется "
        "только для сравнения."
    )

    log.append(
        "Старые записи автоматически "
        "не переносятся в новый результат."
    )

    log.append(
        "Для каждого найденного Stream8 "
        "создаются три независимые записи:"
    )

    log.append(
        "  1. Stream8 — оригинал"
    )

    log.append(
        "  2. Stream0 — зеркало"
    )

    log.append(
        "  3. Stream1 — зеркало"
    )

    log.append(
        f"Итоговый файл: {OUTPUT_FILE}"
    )

    log.append(
        f"Группа: {VERIFY_GROUP}"
    )

    log.append("")

    log.append(
        "=== Конец отчёта ==="
    )

    # ========================================================
    # 9. ОТЧЁТ
    # ========================================================

    try:

        with open(
            REPORT_FILE,
            "w",
            encoding="utf-8"
        ) as rep:

            rep.write(
                "\n".join(log)
            )

    except Exception as e:

        print(
            f"[WARN] Ошибка записи отчёта: {e}"
        )

    # ========================================================
    # 10. ФИНАЛ
    # ========================================================

    print()

    print(
        "=============================================="
    )

    print(
        "[ OK ] VERIFY 1 ЗАВЕРШЁН"
    )

    print(
        "=============================================="
    )

    print(
        f" Предыдущий M3U : {previous_count}"
    )

    print(
        f" Stream8        : {final_stream8}"
    )

    print(
        f" Stream0        : {final_stream0}"
    )

    print(
        f" Stream1        : {final_stream1}"
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

    print(
        f" Файл           : {OUTPUT_FILE}"
    )

    print(
        f" Отчёт          : {REPORT_FILE}"
    )

    print(
        "==============================================" 
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()