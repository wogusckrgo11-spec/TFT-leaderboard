# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

롤토체스(TFT) KR/JP/NA/EUW/VN 서버 상위 2000명 리더보드를 매일 자동 수집하고, 전날 대비 다음 세 가지 변동을 Discord로 알림하는 자동화 프로젝트.
- 순위 50위 이상 상승한 유저 (최대 10명)
- 신규 2000위 진입 유저 (최대 10명)
- LP 200점 이상 상승한 유저 (최대 10명)

## 주요 명령어

```bash
# 수동으로 오늘 데이터 수집 및 Discord 알림 실행
DISCORD_WEBHOOK=<url> python daily_leaderboard.py

# KR 서버 단건 수집 후 leaderboard_full.json 저장 (일회성 디버깅용)
python fetch_leaderboard.py

# GitHub Actions 수동 트리거
gh workflow run daily.yml --repo <owner>/TFT-leaderboard
```

## 아키텍처

### API
- 데이터 출처: `https://tft.dakgg.io/api/v1/leaderboards/summoners/{shard}`
- 서버별 shard 코드: `kr`, `jp1`, `na1`, `euw1`, `vn2`
- 페이지당 100명, 총 20페이지 (2000명), `queueId=1100` = 일반 랭크

### 핵심 로직 (`daily_leaderboard.py`)

```
fetch_all()       → API 전체 페이지 수집 (0.3초 간격)
load_snapshot()   → snapshots/{날짜}_{서버}.json 로드
analyze()         → 어제 스냅샷과 비교 → risers / newcomers / lp_risers 반환
build_embeds()    → 서버별 Discord embed 객체 생성
send_discord()    → 서버별 1개씩 개별 Webhook POST (Discord 6000자 제한 대응)
save_snapshot()   → 오늘 데이터 저장 (내일 비교용)
save_csv()        → leaderboard_{서버}.csv 갱신
```

**순위 계산 방식**: API의 `rank` 필드가 아닌, 응답 배열의 인덱스(0-based + 1)를 실제 순위로 사용.

**비교 기준**: 모두 `puuid` 기준으로 매칭. 어제 스냅샷에 없는 puuid는 신규 진입으로 분류.

**상수** (변경 시 이 값들을 수정):
- `RISE_THRESHOLD = 50` — 순위 상승 기준
- `LP_RISE_THRESHOLD = 200` — LP 상승 기준
- `EMBED_COLOR` — 서버별 Discord 임베드 색상

### 스냅샷
- 위치: `snapshots/{YYYY-MM-DD}_{서버}.json`
- 형식: API `summonerRankings` 배열 그대로 저장
- 첫 실행 시 어제 스냅샷 없음 → 저장만, 알림 없음 → 다음날부터 정상 작동
- 같은 날 여러 번 실행하면 당일 스냅샷이 덮어씌워짐 (git 히스토리에는 보존)

### 자동화
- GitHub Actions (`.github/workflows/daily.yml`): 매일 **12:00 KST** (= 03:00 UTC) 실행
- `permissions: contents: write` 설정으로 스냅샷 자동 커밋 & 푸시
- Discord Webhook URL은 GitHub Secret `DISCORD_WEBHOOK`에 저장, 환경변수 미설정 시 즉시 오류 발생
