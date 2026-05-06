# TFT 리더보드 알리미

롤토체스(TFT) 5개 서버 상위 2000명 리더보드를 매일 자동 수집하여, 전날 대비 순위가 크게 오른 플레이어를 Discord로 알림하는 자동화 프로젝트입니다.

## 기능

- **매일 09:00 KST** GitHub Actions 자동 실행
- 5개 서버 동시 수집: 🇰🇷 KR / 🇯🇵 JP / 🇺🇸 NA / 🇪🇺 EUW / 🇻🇳 VN
- **20위 이상 상승**한 플레이어 Discord 알림
- **신규 2000위 진입** 플레이어 Discord 알림
- 매일 스냅샷을 레포에 자동 커밋하여 날짜별 데이터 보관

## 알림 예시

![Discord 알림 예시](https://i.imgur.com/placeholder.png)

```
🇰🇷 KR 서버 — 2026년 05월 07일

📈 순위 20위 이상 상승
 312위  작은거인#SOOP   450위 → 312위  +138
  87위  띵 땡#KR1      152위 →  87위   +65

🆕 신규 2000위 진입
1847위  뉴비챌린저#KR1  MASTER 421LP
```

## 구조

```
snapshots/          # 날짜별 서버 스냅샷 (JSON)
daily_leaderboard.py  # 메인 스크립트
.github/workflows/daily.yml  # GitHub Actions 자동화
```

## 설정

### 필요 환경변수

| 변수명 | 설명 |
|---|---|
| `DISCORD_WEBHOOK` | Discord 채널 웹훅 URL |

GitHub 레포 → Settings → Secrets → `DISCORD_WEBHOOK` 등록

### 로컬 실행

```bash
pip install -r requirements.txt
DISCORD_WEBHOOK=<웹훅_URL> python daily_leaderboard.py
```

## 데이터 출처

[lolchess.gg](https://lolchess.gg) / [tft.dakgg.io](https://tft.dakgg.io)
