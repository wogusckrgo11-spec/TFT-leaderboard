import csv
import requests
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
TODAY = NOW.strftime("%Y-%m-%d")
YESTERDAY = (NOW - timedelta(days=1)).strftime("%Y-%m-%d")

BASE_DIR = Path(__file__).parent
SNAPSHOT_DIR = BASE_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)

import os
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

SERVERS = {
    "KR":  ("kr",   "🇰🇷"),
    "JP":  ("jp1",  "🇯🇵"),
    "NA":  ("na1",  "🇺🇸"),
    "EUW": ("euw1", "🇪🇺"),
    "VN":  ("vn2",  "🇻🇳"),
}

API_BASE = "https://tft.dakgg.io/api/v1/leaderboards/summoners/{shard}"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://lolchess.gg/"}
PARAMS_BASE = {"hl": "ko", "tier": "ALL", "queueId": 1100}
RISE_THRESHOLD = 20
EMBED_COLOR = {"KR": 0xE84057, "JP": 0xFF6B6B, "NA": 0x3B82F6, "EUW": 0x6366F1, "VN": 0xF59E0B}


def fetch_all(shard: str) -> list:
    first = requests.get(
        API_BASE.format(shard=shard),
        params={**PARAMS_BASE, "page": 1},
        headers=HEADERS, timeout=10
    ).json()

    meta = first["meta"]
    total = meta["totalCount"]
    per_page = len(first["summonerRankings"])
    total_pages = (total + per_page - 1) // per_page

    players = first["summonerRankings"]
    for page in range(2, total_pages + 1):
        r = requests.get(
            API_BASE.format(shard=shard),
            params={**PARAMS_BASE, "page": page},
            headers=HEADERS, timeout=10
        )
        players.extend(r.json()["summonerRankings"])
        time.sleep(0.3)

    return players


def load_snapshot(date: str, server: str) -> list | None:
    path = SNAPSHOT_DIR / f"{date}_{server}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_snapshot(date: str, server: str, players: list):
    path = SNAPSHOT_DIR / f"{date}_{server}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False)


def save_csv(server: str, players: list):
    path = BASE_DIR / f"leaderboard_{server.lower()}.csv"
    rows = [
        {
            "rank": idx + 1,
            "gameName": p.get("gameName"),
            "tagLine": p.get("tagLine"),
            "tier": p.get("tier"),
            "leaguePoints": p.get("leaguePoints"),
            "plays": p.get("plays"),
            "wins": p.get("wins"),
            "tops": p.get("tops"),
            "winRate": round(p["wins"] / p["plays"] * 100, 1) if p.get("plays") else 0,
            "top4Rate": round(p["tops"] / p["plays"] * 100, 1) if p.get("plays") else 0,
        }
        for idx, p in enumerate(players)
    ]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def analyze(today_players: list, yesterday_players: list | None):
    today_rank = {p["puuid"]: idx + 1 for idx, p in enumerate(today_players)}
    yesterday_rank = (
        {p["puuid"]: idx + 1 for idx, p in enumerate(yesterday_players)}
        if yesterday_players else {}
    )

    risers = []
    newcomers = []

    for idx, p in enumerate(today_players):
        puuid = p["puuid"]
        t_rank = idx + 1
        name = f"{p['gameName']}#{p['tagLine']}"
        tier = p.get("tier", "")
        lp = p.get("leaguePoints", 0)

        if puuid in yesterday_rank:
            y_rank = yesterday_rank[puuid]
            diff = y_rank - t_rank  # 양수 = 상승
            if diff >= RISE_THRESHOLD:
                risers.append({
                    "name": name, "tier": tier, "lp": lp,
                    "yesterday_rank": y_rank, "today_rank": t_rank, "diff": diff,
                })
        else:
            newcomers.append({
                "name": name, "tier": tier, "lp": lp, "today_rank": t_rank,
            })

    risers.sort(key=lambda x: x["diff"], reverse=True)
    newcomers.sort(key=lambda x: x["today_rank"])
    return risers, newcomers


def build_embeds(results: dict) -> list:
    embeds = []
    today_str = NOW.strftime("%Y년 %m월 %d일")

    for server, (risers, newcomers) in results.items():
        _, emoji = SERVERS[server]
        fields = []

        if risers:
            lines = [
                f"`{r['today_rank']:4}위` **{r['name']}**  "
                f"{r['yesterday_rank']}위 → {r['today_rank']}위  `+{r['diff']}`"
                for r in risers[:15]
            ]
            fields.append({
                "name": "📈 순위 20위 이상 상승",
                "value": "\n".join(lines),
                "inline": False,
            })

        if newcomers:
            lines = [
                f"`{n['today_rank']:4}위` **{n['name']}**  {n['tier']} {n['lp']}LP"
                for n in newcomers[:15]
            ]
            fields.append({
                "name": "🆕 신규 2000위 진입",
                "value": "\n".join(lines),
                "inline": False,
            })

        if not fields:
            continue

        embeds.append({
            "title": f"{emoji} {server} 서버 — {today_str}",
            "color": EMBED_COLOR[server],
            "fields": fields,
            "footer": {"text": f"상승 {len(risers)}명 · 신규 진입 {len(newcomers)}명"},
        })

    return embeds


def send_discord(embeds: list, has_data: bool):
    today_str = NOW.strftime("%Y년 %m월 %d일")

    if not has_data:
        payload = {
            "username": "TFT 리더보드 알리미",
            "embeds": [{
                "title": f"📊 TFT 리더보드 — {today_str}",
                "description": "오늘은 20위 이상 상승하거나 신규 진입한 플레이어가 없습니다.",
                "color": 0x808080,
            }],
        }
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10).raise_for_status()
        return

    # Discord 메시지당 전체 임베드 문자 합계 6000자 제한으로, 서버별 1개씩 개별 전송
    for embed in embeds:
        payload = {
            "username": "TFT 리더보드 알리미",
            "embeds": [embed],
        }
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10).raise_for_status()
        time.sleep(1)


def main():
    print(f"[{NOW.strftime('%Y-%m-%d %H:%M:%S KST')}] 리더보드 수집 시작")
    results = {}

    for server, (shard, _) in SERVERS.items():
        print(f"  [{server}] 수집 중...", end=" ", flush=True)
        today_players = fetch_all(shard)
        yesterday_players = load_snapshot(YESTERDAY, server)

        if yesterday_players is None:
            print(f"어제 스냅샷 없음 → 오늘 저장만 (내일부터 비교)")
        else:
            risers, newcomers = analyze(today_players, yesterday_players)
            results[server] = (risers, newcomers)
            print(f"상승 {len(risers)}명 / 신규 진입 {len(newcomers)}명")

        save_snapshot(TODAY, server, today_players)
        save_csv(server, today_players)

    if results:
        embeds = build_embeds(results)
        send_discord(embeds, has_data=bool(embeds))
        print("Discord 알림 전송 완료")
    else:
        print("어제 스냅샷이 없어 오늘은 알림 없음 — 내일부터 정상 작동")


if __name__ == "__main__":
    main()
