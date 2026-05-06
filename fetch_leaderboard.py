import requests
import json
import time

BASE_URL = "https://tft.dakgg.io/api/v1/leaderboards/summoners/kr"
PARAMS = {
    "hl": "ko",
    "tier": "ALL",
    "queueId": 1100,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://lolchess.gg/",
}


def fetch_page(page: int) -> dict:
    params = {**PARAMS, "page": page}
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    # 1페이지 먼저 가져와서 메타 정보 확인
    first = fetch_page(1)
    meta = first["meta"]
    total = meta["totalCount"]
    per_page = len(first["summonerRankings"])
    total_pages = (total + per_page - 1) // per_page

    print(f"서버: {meta['shard'].upper()} | 시즌: {meta['season']} | 전체 플레이어: {total}명 | 총 페이지: {total_pages}")
    print(f"티어 컷오프: {first['summonerTierCutoffs']}")
    print("-" * 60)

    all_players = first["summonerRankings"]

    # 2페이지 ~ 전체 페이지 수집 (필요 시 범위 조정)
    # 전체 수집 시 total_pages 사용, 테스트 시 소규모로
    pages_to_fetch = total_pages  # 전체 수집
    for page in range(2, pages_to_fetch + 1):
        data = fetch_page(page)
        all_players.extend(data["summonerRankings"])
        print(f"  {page}/{pages_to_fetch} 페이지 수집 완료 ({len(all_players)}명)")
        time.sleep(0.3)  # 서버 부하 방지

    # 정리된 데이터로 변환
    rows = []
    for p in all_players:
        rows.append({
            "rank": p.get("rank"),
            "gameName": p.get("gameName"),
            "tagLine": p.get("tagLine"),
            "tier": p.get("tier"),
            "leaguePoints": p.get("leaguePoints"),
            "plays": p.get("plays"),
            "wins": p.get("wins"),
            "tops": p.get("tops"),
            "winRate": round(p["wins"] / p["plays"] * 100, 1) if p.get("plays") else 0,
            "top4Rate": round(p["tops"] / p["plays"] * 100, 1) if p.get("plays") else 0,
            "rankDiff": p.get("rankDiff"),
        })

    # JSON 저장
    output = {
        "meta": meta,
        "tierCutoffs": first["summonerTierCutoffs"],
        "players": rows,
    }
    with open("leaderboard_full.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(rows)}명 데이터를 leaderboard_full.json에 저장했습니다.")

    # 상위 20명 출력
    print("\n=== 상위 20명 ===")
    print(f"{'순위':>4}  {'소환사명':<20} {'티어':<12} {'LP':>6} {'게임':>5} {'승률':>6} {'TOP4':>6}")
    print("-" * 70)
    for p in rows[:20]:
        name = f"{p['gameName']}#{p['tagLine']}"
        print(f"{p['rank']:>4}  {name:<20} {p['tier']:<12} {p['leaguePoints']:>6} {p['plays']:>5} {p['winRate']:>5}%  {p['top4Rate']:>5}%")


if __name__ == "__main__":
    main()
