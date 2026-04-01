# AI Digest Bot — CLAUDE.md

## Project Overview
AI 관련 최신 뉴스/정보/지식을 수집하여 Slack 채널에 12시간마다 자동으로 전송하는 봇.

## Tech Stack
- **Language**: Python 3.11+
- **Slack**: `slack-sdk` (Web API) + Interactive Components
- **Web Server**: `fastapi` + `uvicorn` (Slack 버튼 이벤트 수신)
- **Scheduling**: `APScheduler`
- **AI Summarization**: Google Gemini API (`google-genai` SDK)
- **Notion**: `notion-client` SDK
- **Web Search**: Tavily API (또는 Google Custom Search API)
- **RSS/Feed Parsing**: `feedparser`
- **HTTP**: `httpx` (async)
- **Summarization Model**: `gemini-2.0-flash` (비용 효율 최우선)
- **Config**: `pydantic-settings` + `.env`

## Project Structure
```
ai-digest-bot/
├── CLAUDE.md
├── PRD.md
├── Tasks.md
├── .env.example
├── pyproject.toml
├── src/
│   ├── main.py           # 진입점: 스케줄러 + FastAPI 서버 동시 실행
│   ├── config.py         # 환경변수/설정 관리
│   ├── db.py             # SQLite 초기화 및 URL 이력 관리
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── search.py     # 웹 검색 (Tavily API)
│   │   ├── rss.py        # RSS 피드 수집
│   │   └── sources.py    # 수집 소스 목록 정의
│   ├── summarizer/
│   │   ├── __init__.py
│   │   └── gemini.py     # Gemini API로 요약 생성
│   ├── slack/
│   │   ├── __init__.py
│   │   ├── channel.py    # 채널 생성/조회
│   │   ├── sender.py     # Block Kit 메시지 전송 (버튼 포함)
│   │   └── interactions.py  # 버튼 클릭 이벤트 처리
│   ├── notion/
│   │   ├── __init__.py
│   │   └── client.py     # Notion DB에 페이지 저장
│   ├── scheduler.py      # APScheduler 작업 정의
│   └── server.py         # FastAPI 앱: POST /slack/interactions
└── tests/
    └── ...
```

## Key Conventions
- 모든 Slack 메시지는 **한국어**로 작성
- 메시지 본문은 **500자 이내** 요약
- 1회 전송 시 최대 **20개** 항목
- 추측/개인 의견이 포함된 콘텐츠는 필터링
- 수집 기준: **최근 48시간 이내** + **인기도 기반** 정렬

## Environment Variables
`.env` 파일에 다음 키를 설정해야 한다:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...       # Interactive Components 요청 서명 검증용
SLACK_CHANNEL_NAME=ai-digest
GEMINI_API_KEY=AIza...
TAVILY_API_KEY=tvly-...
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=...         # 저장 대상 Notion Database ID
SCHEDULE_INTERVAL_HOURS=12
MAX_ITEMS_PER_DIGEST=20
MAX_SUMMARY_CHARS=500
PORT=8000                      # FastAPI 서버 포트
```

## Running the Bot
```bash
# 의존성 설치
pip install -e .

# 봇 실행 (스케줄러 상시 가동)
python -m src.main

# 즉시 1회 실행 (테스트용)
python -m src.main --run-now
```

## Important Notes
- Slack 앱 필요 scope: `channels:manage`, `channels:read`, `chat:write`, `chat:write.public`
- Slack Interactive Components 활성화 필수 → Interactivity Request URL 설정 필요
  - 로컬: `ngrok http 8000` 후 `https://<id>.ngrok.io/slack/interactions` 입력
- Notion Integration 생성 후 대상 Database에 반드시 Integration을 공유(Share)해야 함
- Gemini API 요약 시 `gemini-2.0-flash` 모델 사용 (비용 효율)
- 동일 URL 중복 전송 방지를 위해 로컬 SQLite로 이력 관리
- 버튼 클릭 payload에 title, summary, url, source를 `action_id` 또는 `value`에 인코딩하여 전달
