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

# Старый рабочий файл — используется только для сравнения
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
            headers=HEADERS
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
    if not m3u_text:
        return []

    result = []

    matches = re.findall(
        r'#EXTINF.*?,(.*?)(?:\n|$)',
        m3u_text,
        flags=re.S
    )

    for block in matches:
        name = block.strip()

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
    if "stream8.cinerama.uz" in url:
        return "Stream8"
    if "stream0.cinerama.uz" in url:
        return "Stream0"
    if "stream1.cinerama.uz" in url:
        return "Stream1"
    return "Unknown"


# ============================================================
# ИЗВЛЕЧЕНИЕ ID
# ============================================================

def extract_cinerama_id(url):
    match = re.search(
        r'cinerama\.uz/(\d+)/',
        url,
        flags=re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None


# ============================================================
# ЧТЕНИЕ СТАРОГО M3U
# ============================================================

def load_previous_m3u(text, log):
    previous = OrderedDict()
    lines = text.splitlines()
    current_extinf = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current_extinf = line
            continue

        if current_extinf and line.startswith(("http://", "https://")):
            url = line
            cid = extract_cinerama_id(url)

            if cid is not None:
                if "," in current_extinf:
                    name = current_extinf.split(",", 1)[1].strip()
                else:
                    name = ""

                previous[cid] = {
                    "id": cid,
                    "name": name,
                    "url": url,
                    "group": get_stream_group(url)
                }

            current_extinf = None

    log.append(f"[OLD] Предыдущий M3U: {len(previous)} Cinerama записей")
    return previous


# ============================================================
# НОВЫЙ ПРОХОД: STREAM8
# ============================================================

def scan_stream8(session, base, start_id, end_id, log):
    found = []

    print()
    print(f"[SCAN] Stream8: {start_id} → {end_id}")

    log.append("")
    log.append("=== НОВЫЙ ПРОХОД Stream8 ===")
    log.append(f"Диапазон: {start_id} → {end_id}")

    for cid in range(start_id, end_id + 1):
        url = build_stream_url(base, cid)
        text = fetch_text(session, url)

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

        print(f"[FOUND] Stream8 ID={cid:<5} {name}")

    log.append(f"Найдено Stream8: {len(found)}")
    return found


# ============================================================
# ЗЕРКАЛА: Stream8 → Stream0 / Stream1
# ============================================================

def create_mirror_streams(stream8_entries, log):
    stream0_entries = []
    stream1_entries = []

    log.append("")
    log.append("=== РАСХОЖДЕНИЕ Stream8 → Stream0 + Stream1 ===")

    for item in stream8_entries:
        item0 = item.copy()
        item0["url"] = item["url"].replace(
            "stream8.cinerama.uz",
            "stream0.cinerama.uz"
        )
        item0["group"] = "Stream0"
        stream0_entries.append(item0)

        item1 = item.copy()
        item1["url"] = item["url"].replace(
            "stream8.cinerama.uz",
            "stream1.cinerama.uz"
        )
        item1["group"] = "Stream1"
        stream1_entries.append(item1)

    log.append(f"Stream0 создано: {len(stream0_entries)}")
    log.append(f"Stream1 создано: {len(stream1_entries)}")

    return stream0_entries, stream1_entries


# ============================================================
# СРАВНЕНИЕ
# ============================================================

def compare_results(previous, current, log):
    match = []
    changed = []
    new = []
    missing = []

    all_ids = sorted(set(previous.keys()) | set(current.keys()))

    log.append("")
    log.append("==============================================")
    log.append("             СРАВНЕНИЕ ПРОХОДОВ")
    log.append("==============================================")

    for cid in all_ids:
        old = previous.get(cid)
        cur = current.get(cid)

        if old and cur:
            if old["url"] == cur["url"] and old["name"] == cur["name"]:
                match.append(cur)
                log.append(f"[MATCH] ID={cid} | {cur['name']} | {cur['url']}")
            else:
                changed.append({"old": old, "new": cur})
                log.append(f"[CHANGED] ID={cid}")
                log.append(f"  OLD NAME : {old['name']}")
                log.append(f"  OLD URL  : {old['url']}")
                log.append(f"  NEW NAME : {cur['name']}")
                log.append(f"  NEW URL  : {cur['url']}")

        elif cur and not old:
            new.append(cur)
            log.append(f"[NEW] ID={cid} | {cur['name']} | {cur['url']}")

        elif old and not cur:
            missing.append(old)
            log.append(f"[MISSING] ID={cid} | {old['name']} | {old['url']}")

    return match, changed, new, missing


# ============================================================
# MAIN
# ============================================================

def main():
    print("==============================================")
    print(f"     CINERAMA VERIFIED 1 | {COPYRIGHT}")
    print("==============================================")
    print()

    log = []
    log.append("=== SCALA-DREG STREAM PROCESSOR REPORT ===")
    log.append(f"Дата запуска: {datetime.utcnow()} UTC")
    log.append("")

    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. Предыдущий локальный M3U для сравнения
    previous = {}

    print("[INFO] Загружаем предыдущий M3U...")
    if os.path.exists(PREVIOUS_M3U_FILE):
        try:
            with open(PREVIOUS_M3U_FILE, "r", encoding="utf-8") as f:
                previous_text = f.read()

            previous = load_previous_m3u(previous_text, log)
            print(f"[INFO] Загружено {len(previous)} записей")
        except Exception as e:
            print(f"[WARN] Ошибка загрузки старого M3U: {e}")
            log.append(f"[WARN] PREVIOUS_M3U: {e}")
    else:
        print("[WARN] Предыдущий M3U не найден, сравнение пропускается")
        log.append("[WARN] PREVIOUS_M3U не найден")

    # 2. Сканируем Stream8
    stream8_entries = scan_stream8(
        session,
        STREAM8_BASE,
        START_ID,
        END_ID,
        log
    )

    # 3. Создаём Stream0 и Stream1
    stream0_entries, stream1_entries = create_mirror_streams(
        stream8_entries,
        log
    )

    # 4. Объединяем Stream0 + Stream1
    current_by_id = OrderedDict()

    for item in sorted(stream0_entries, key=lambda x: x["id"]):
        cid = item["id"]
        if cid not in current_by_id:
            current_by_id[cid] = item

    for item in sorted(stream1_entries, key=lambda x: x["id"]):
        cid = item["id"]
        if cid not in current_by_id:
            current_by_id[cid] = item

    # 5. Сравнение с предыдущим проходом
    match, changed, new, missing = compare_results(
        previous,
        current_by_id,
        log
    )

    # 6. Создаём новый M3U
    result = [
        "#EXTM3U",
        f"# Playlist verified by {COPYRIGHT} - {VERIFY_GROUP}"
    ]

    for cid in sorted(current_by_id.keys()):
        item = current_by_id[cid]

        result.append(
            f'#EXTINF:-1 '
            f'tvg-id="cinerama_{item["id"]}" '
            f'group-title="{item["group"]}",'
            f'{item["name"]}'
        )
        result.append(item["url"])

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(result) + "\n")
    except Exception as e:
        print(f"[ERROR] Ошибка записи Verify 1: {e}")
        return

    # 7. Статистика
    previous_count = len(previous)
    final_count = len(current_by_id)

    log.append("")
    log.append("==============================================")
    log.append("              ИТОГОВАЯ СТАТИСТИКА")
    log.append("==============================================")
    log.append(f"Предыдущий M3U : {previous_count}")
    log.append(f"Stream8        : {len(stream8_entries)}")
    log.append(f"Stream0        : {len(stream0_entries)}")
    log.append(f"Stream1        : {len(stream1_entries)}")
    log.append(f"MATCH          : {len(match)}")
    log.append(f"CHANGED        : {len(changed)}")
    log.append(f"NEW            : {len(new)}")
    log.append(f"MISSING        : {len(missing)}")
    log.append(f"VERIFY 1       : {final_count}")
    log.append("")
    log.append("Старый M3U используется только для сравнения.")
    log.append("В итоговый Verify 1 старые записи не переносятся.")
    log.append(f"Итоговый файл: {OUTPUT_FILE}")
    log.append(f"Группа: {VERIFY_GROUP}")
    log.append("")
    log.append("=== Конец отчёта ===")

    # 8. Запись отчёта
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as rep:
            rep.write("\n".join(log))
    except Exception as e:
        print(f"[WARN] Ошибка записи отчёта: {e}")

    # 9. Финал
    print()
    print("==============================================")
    print("[ OK ] VERIFY 1 ЗАВЕРШЁН")
    print("==============================================")
    print(f" Предыдущий M3U : {previous_count}")
    print(f" Stream8        : {len(stream8_entries)}")
    print(f" Stream0        : {len(stream0_entries)}")
    print(f" Stream1        : {len(stream1_entries)}")
    print(f" MATCH          : {len(match)}")
    print(f" CHANGED        : {len(changed)}")
    print(f" NEW            : {len(new)}")
    print(f" MISSING        : {len(missing)}")
    print(f" VERIFY 1       : {final_count}")
    print(f" Файл           : {OUTPUT_FILE}")
    print(f" Отчёт          : {REPORT_FILE}")
    print("==============================================")


if __name__ == "__main__":
    main()