# -*- coding: utf-8 -*-
"""대연롯데캐슬레전드 33평 매물·실거래 수집기.

호갱노노 공개 화면이 쓰는 데이터를 가져와 data/db.json 에 쌓고,
대시보드가 읽는 web/data.js 를 다시 만든다.
- 매물: 매번 현재 목록을 찍어 두고(스냅샷) 처음 본 날/사라진 날을 기록한다.
- 실거래: 최근 3년치를 받아 id 기준으로 누적한다.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

APT = "aNmbc"          # 호갱노노 단지 코드 (대연롯데캐슬레전드)
AREA_NO = 9            # 호갱노노 33평 면적 번호
PRIVATE_MIN, PRIVATE_MAX = 84.0, 86.0   # 33평 = 전용 84㎡대
BASE = "https://hogangnono.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) personal-apt-tracker",
    "Referer": f"{BASE}/apt/{APT}",
    "Accept": "application/json",
}
KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "data", "db.json")
OUT_PATH = os.path.join(ROOT, "web", "data.js")
LOG_PATH = os.path.join(ROOT, "data", "collect.log")


def log(msg):
    line = f"[{datetime.now(KST):%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get(path):
    for attempt in range(3):
        try:
            req = urllib.request.Request(BASE + path, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                body = json.load(r)
            time.sleep(0.6)  # 사이트에 부담 주지 않도록 천천히
            return body["data"]
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                raise
            log(f"재시도 {attempt + 1}: {path} ({e})")
            time.sleep(3)


def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"units": {}, "items": {}, "trades": {}, "snapshots": []}


def save_db(db):
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, DB_PATH)


def parse_floor(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def floor_band(floor_txt):
    """저층 1~10, 중층 11~22, 고층 23~ / 숫자 없이 '저·중·고'만 있으면 그대로."""
    n = parse_floor(floor_txt)
    if n is None:
        return {"저": "저층", "중": "중층", "고": "고층"}.get(str(floor_txt), "미상")
    if n <= 10:
        return "저층"
    if n <= 22:
        return "중층"
    return "고층"


def collect_trades(db):
    data = get(f"/api/v2/apts/{APT}/monthly-reports?tradeType=0&areaNo={AREA_NO}")
    added = 0
    for month in data.get("shortTermReport", []):
        # date 는 해당 월 1일 0시(KST)를 UTC 로 적은 값
        d = datetime.fromisoformat(month["date"].replace("Z", "+00:00")).astimezone(KST)
        for t in month.get("trades", []):
            key = str(t["id"])
            if key in db["trades"] or t.get("isAuction") or "day" not in t:
                continue  # 경매 낙찰 건은 일반 거래가 아니므로 뺀다
            db["trades"][key] = {
                "date": f"{d.year:04d}-{d.month:02d}-{int(t['day']):02d}",
                "price": t["price"],           # 만원
                "floor": t.get("floor"),
                "cancel": bool(t.get("isCanceled") or t.get("canceled")),
            }
            added += 1
    return added


ASIL_URL = ("https://asil.kr/app/data/data_offer_sum.jsp?apt=109359&area=2629010600&c_apt=&c_area=&c_apt2=&c_area2="
            "&deal=123&mode=2&sSize=&eSize=&sY=2015&sM=1&eY={y}&eM=12")


def collect_asil(db):
    """아실 '매물 추이': 단지 전체(모든 평형) 일별 매매·전세·월세 매물 수. 평형 구분은 없다."""
    import re
    url = ASIL_URL.format(y=datetime.now(KST).year)
    req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"],
                                               "Referer": "https://asil.kr/app/offer_sum_chart.jsp"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    rows = [json.loads(m) for m in re.findall(r"chartData\[\d+\]=(\{[^}]*\})", text)]
    store = db.setdefault("asil", {})
    for row in rows:
        yy, mm, dd = (int(x) for x in row["Date"].split("/"))
        store[f"20{yy:02d}-{mm:02d}-{dd:02d}"] = [row.get("VM"), row.get("VJ"), row.get("VW")]
    return len(rows)


def collect_all_trades(db, now):
    """단지 전체(모든 평형) 매매 실거래. 평형 번호를 차례로 훑어 거래 id 로 중복을 없앤다.
    요청이 많아 6시간에 한 번만 한다."""
    last = db.get("tradesAllAt")
    if last and (now - datetime.fromisoformat(last)).total_seconds() < 6 * 3600:
        return 0
    store = db.setdefault("tradesAll", {})
    added, misses = 0, 0
    for area_no in range(0, 30):
        try:
            data = get(f"/api/v2/apts/{APT}/monthly-reports?tradeType=0&areaNo={area_no}")
        except Exception:  # noqa: BLE001
            data = None
        months = (data or {}).get("shortTermReport") or []
        if not months:
            misses += 1
            if misses >= 3:
                break
            continue
        misses = 0
        for month in months:
            d = datetime.fromisoformat(month["date"].replace("Z", "+00:00")).astimezone(KST)
            for t in month.get("trades", []):
                key = str(t["id"])
                if key in store or t.get("isAuction") or "day" not in t:
                    continue
                store[key] = f"{d.year:04d}-{d.month:02d}-{int(t['day']):02d}"
                added += 1
    db["tradesAllAt"] = now.isoformat(timespec="minutes")
    return added


def collect_listings(db, now_iso):
    # 1) 단지 전체 매물 요약을 페이지로 모두 받기
    summaries, offset = [], 0
    while True:
        page = get(f"/api/v2/item-catalogs/summaries?aptHash={APT}&isAptDetail=false&offset={offset}&limit=100")
        rows = page.get("itemCatalogSummaries", [])
        summaries += rows
        offset += len(rows)
        if not rows or offset >= page.get("itemCatalogTotalCount", 0):
            break

    # 2) 33평 매매만 고르기
    targets = [s for s in summaries
               if s.get("tradeType") == 0 and PRIVATE_MIN <= (s.get("privateArea") or 0) < PRIVATE_MAX]

    seen_now = set()
    for s in targets:
        hid = str(s["areaHoId"])
        item_ids = sorted(str(i["itemId"]) for i in s.get("itemIds", []))
        unit = db["units"].get(hid)
        known = all(i in db["items"] for i in item_ids)
        detail_items = {}
        if unit is None or not known:
            # 새 집(호)이거나 새 매물이 붙었으면 상세를 받아 향·층·가격 확인
            det = get(f"/api/v2/item-catalogs/{hid}?tradeType=0&offset=0&limit=20")
            ho = det.get("hoInfo") or {}
            unit = {
                "dong": ho.get("aptDongName") or s.get("aptDongName"),
                "floor": ho.get("floor") or s.get("floor"),
                "buildingFloor": ho.get("buildingFloor"),
                "direction": ho.get("direction"),
                "type": ho.get("danjiRoomType") or s.get("danjiRoomType"),
            }
            db["units"][hid] = unit
            for it in det.get("items", []):
                detail_items[str(it["itemId"])] = it
        for iid in item_ids:
            seen_now.add(iid)
            rec = db["items"].get(iid)
            it = detail_items.get(iid)
            price = (it or {}).get("deposit") or s.get("deposit")
            if rec is None:
                req = (it or {}).get("itemRequiredInfo") or {}
                rec = {
                    "hoId": hid,
                    "dong": unit["dong"],
                    "floor": req.get("floor") or unit["floor"],
                    "direction": req.get("direction") or unit["direction"],
                    "type": unit["type"],
                    "firstSeen": now_iso,
                    "lastSeen": now_iso,
                    "goneAt": None,
                    "price": price,
                    "priceHistory": [[now_iso, price]],
                    "title": (it or {}).get("itemTitle") or s.get("itemTitle"),
                }
                db["items"][iid] = rec
            else:
                rec["lastSeen"] = now_iso
                rec["goneAt"] = None
                if it and it.get("deposit") and it["deposit"] != rec["price"]:
                    rec["price"] = it["deposit"]
                    rec["priceHistory"].append([now_iso, it["deposit"]])
                elif not it and len(item_ids) == 1 and s.get("deposit") and s["deposit"] != rec["price"]:
                    rec["price"] = s["deposit"]
                    rec["priceHistory"].append([now_iso, s["deposit"]])

    # 3) 이번에 안 보인 매물은 내려간 것으로 표시
    for iid, rec in db["items"].items():
        if iid not in seen_now and rec["goneAt"] is None:
            rec["goneAt"] = now_iso

    # 4) 스냅샷 (지금 떠 있는 매물 요약)
    active = [db["items"][i] for i in seen_now]
    by_unit = {}
    for r in active:  # 같은 집을 여러 중개사가 올리면 한 집으로 묶고 가장 싼 호가를 쓴다
        if r["price"]:
            by_unit[r["hoId"]] = min(by_unit.get(r["hoId"], r["price"]), r["price"])
    prices = list(by_unit.values())
    db["snapshots"].append({
        "t": now_iso,
        "count": len(by_unit),      # 집(호) 기준 매물 수
        "items": len(active),       # 중개사 등록 건수(중복 포함)
        "avg": round(sum(prices) / len(prices)) if prices else None,
        "min": min(prices) if prices else None,
    })
    return len(by_unit)


def month_counts(dates):
    out = {}
    for d in dates:
        out[d[:7]] = out.get(d[:7], 0) + 1
    return dict(sorted(out.items()))


def group_by_unit(db):
    """중개사별 매물을 집(호) 하나로 묶는다. 하나라도 떠 있으면 살아 있는 매물."""
    units = {}
    for v in db["items"].values():
        u = units.setdefault(v["hoId"], {"items": []})
        u["items"].append(v)
    result = []
    for hid, u in units.items():
        its = u["items"]
        live = [i for i in its if i["goneAt"] is None]
        pool = live or its
        prices = [i["price"] for i in pool if i["price"]]
        first = min(i["firstSeen"] for i in its)
        gone = None if live else max(i["goneAt"] for i in its)
        # 집 기준 호가 이력: 시점마다 그때 떠 있던 중개사 매물 중 가장 싼 값
        hist = []
        for t in sorted({p[0] for i in its for p in i["priceHistory"]} | {i["goneAt"] for i in its if i["goneAt"]}):
            vals = []
            for i in its:
                if i["firstSeen"] <= t and (i["goneAt"] is None or i["goneAt"] > t):
                    pv = [p[1] for p in i["priceHistory"] if p[0] <= t and p[1]]
                    if pv:
                        vals.append(pv[-1])
            if vals and (not hist or hist[-1][1] != min(vals)):
                hist.append([t, min(vals)])
        ref = its[0]
        floor = next((i["floor"] for i in its if parse_floor(i["floor"]) is not None), ref["floor"])
        result.append({
            "hoId": hid, "dong": ref["dong"], "floor": floor, "band": floor_band(floor),
            "dir": ref["direction"], "type": ref["type"],
            "price": min(prices) if prices else None,
            "agents": len(live), "firstSeen": first, "goneAt": gone,
            "priceHistory": hist,
        })
    return result


def build_output(db, now_iso):
    out = {
        "updatedAt": now_iso,
        "apt": "대연롯데캐슬레전드",
        "area": "33평 (전용 84㎡)",
        "sources": {
            "hogangnono": f"{BASE}/apt/{APT}/0/{AREA_NO}",
            "asil": "https://asil.kr/asil/index.jsp",
        },
        "trades": sorted(
            ({"id": k, **v, "band": floor_band(v["floor"])} for k, v in db["trades"].items()),
            key=lambda x: x["date"]),
        "listings": group_by_unit(db),
        "snapshots": db["snapshots"],
        "asil": [[d, *v] for d, v in sorted(db.get("asil", {}).items())],
        # 단지 전체 월별 매매 거래 건수 {YYYY-MM: 건수}
        "allMonthly": month_counts(db.get("tradesAll", {}).values()),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("window.DATA = ")
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = load_db()
    now = datetime.now(KST)
    now_iso = now.isoformat(timespec="minutes")
    # 예약 실행은 GitHub 사정으로 자주 빠지므로 20분마다 깨우고, 직전 수집이 가까우면 건너뛴다.
    min_gap = float(os.environ.get("MIN_GAP_MINUTES") or 0)
    last = db["snapshots"][-1]["t"] if db.get("snapshots") else None
    if min_gap and last and (now - datetime.fromisoformat(last)).total_seconds() < min_gap * 60:
        print(f"직전 수집({last})이 {min_gap:.0f}분 안이라 건너뜀")
        return
    try:
        added = collect_trades(db)
        active = collect_listings(db, now_iso)
    except Exception as e:  # noqa: BLE001
        log(f"수집 실패: {e}")
        sys.exit(1)
    try:
        collect_asil(db)
    except Exception as e:  # noqa: BLE001  아실이 안 돼도 호갱노노 자료는 저장
        log(f"아실 매물 추이 실패: {e}")
    try:
        collect_all_trades(db, datetime.now(KST))
    except Exception as e:  # noqa: BLE001
        log(f"단지 전체 실거래 실패: {e}")
    save_db(db)
    build_output(db, now_iso)
    log(f"완료: 현재 33평 매매 매물 {active}건, 새 실거래 {added}건 (누적 {len(db['trades'])}건)")


if __name__ == "__main__":
    main()
