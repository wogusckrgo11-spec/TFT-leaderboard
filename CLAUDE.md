# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

롤토체스(TFT) KR/JP/NA/EUW/VN 서버 상위 2000명 리더보드를 매일 자동 수집하고, 전날 대비 20위 이상 상승한 유저와 신규 2000위 진입 유저를 Discord로 알림하는 자동화 프로젝트.

## 주요 명령어

```bash
# 수동으로 오늘 데이터 수집 및 Discord 알림 실행
python daily_leaderboard.py

# 특정 서버 단건 수집 및 CSV 저장 (KR만, 일회성 용도)
python fetch_leaderboard.py
```

## 아키텍처

### API
- 데이터 출처: `https://tft.dakgg.io/api/v1/leaderboards/summoners/{shard}`
- 서버별 shard 코드: `kr`, `jp1`, `na1`, `euw1`, `vn2`
- 페이지당 100명, 총 20페이지 (2000명)
- `queueId=1100` = 일반 랭크

### 핵심 로직 (`daily_leaderboard.py`)

```
fetch_all()       → API 전체 페이지 수집
load_snapshot()   → snapshots/{날짜}_{서버}.json 로드
analyze()         → 어제 스냅샷과 비교, risers/newcomers 분류
build_embeds()    → Discord embed 객체 생성
send_discord()    → Webhook POST (embed 최대 10개 제한으로 청크 분할)
save_snapshot()   → 오늘 데이터 저장 (내일 비교용)
```

**순위 계산 방식**: API의 `rank` 필드(로마숫자 티어)가 아닌, 응답 배열의 인덱스(0-based + 1)를 실제 리더보드 순위로 사용.

**신규 진입 판별**: `puuid` 기준으로 어제 스냅샷에 없으면 신규 진입으로 분류.

### 스냅샷
- 위치: `snapshots/{YYYY-MM-DD}_{서버}.json`
- 형식: API `summonerRankings` 배열 그대로 저장
- 첫 실행 시 어제 스냅샷 없음 → 저장만, 알림 없음 → 다음날부터 정상 작동

### 자동화
- GitHub Actions (`.github/workflows/daily.yml`): 매일 00:00 UTC (= 09:00 KST) 실행
- 실행 후 오늘 스냅샷을 자동 커밋하여 레포에 누적 저장
- Discord Webhook URL은 GitHub Secret `DISCORD_WEBHOOK`에 저장, 환경변수 미설정 시 즉시 오류 발생
- 로컬 실행 시 `DISCORD_WEBHOOK=<url> python daily_leaderboard.py` 형태로 직접 전달 필요
