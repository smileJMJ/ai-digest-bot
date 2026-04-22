# AI Digest Bot

AI 관련 최신 뉴스와 정보를 자동으로 수집·요약하여 Slack 채널에 전송하는 봇입니다.

## 주요 기능

- **자동 수집**: RSS 피드 + Tavily 웹 검색으로 최신 AI 뉴스 수집
- **한국어 요약**: Groq(Llama 3.3 70B)로 각 기사를 500자 이내 한국어로 요약
- **인기순 필터링**: Tavily relevance score 기준으로 상위 10건만 선별
- **중복 방지**: SQLite로 최근 7일 전송 이력 관리
- **자동 스케줄**: GitHub Actions로 매일 KST 09:00 / 21:00 자동 실행 (완전 무료)

## 기술 스택

| 역할 | 기술 |
|---|---|
| 수집 | `feedparser` (RSS), Tavily API (웹 검색) |
| 요약 | Groq API (`llama-3.3-70b-versatile`) |
| 알림 | Slack Web API (`slack-sdk`) |
| 스케줄 | GitHub Actions |
| 설정 | `pydantic-settings` + `.env` |

## 수집 소스

- OpenAI Blog / Google AI Blog / HuggingFace Blog
- TechCrunch AI / Ars Technica / MIT Technology Review / VentureBeat
- Tavily 웹 검색 (AI 관련 쿼리 다수)

## 시작하기

### 1. 필수 계정 및 API 키 준비

| 서비스 | 발급 위치 | 무료 여부 |
|---|---|---|
| Slack Bot Token | [api.slack.com](https://api.slack.com/apps) | ✅ |
| Groq API Key | [console.groq.com](https://console.groq.com) | ✅ (14,400 req/day) |
| Tavily API Key | [app.tavily.com](https://app.tavily.com) | ✅ (1,000 req/month) |

### 2. Slack 앱 설정

1. [Slack API](https://api.slack.com/apps) → Create New App → From scratch
2. **OAuth & Permissions** → Bot Token Scopes 추가:
   - `channels:manage`, `channels:read`, `chat:write`, `chat:write.public`, `users:read`
3. Install App → Bot User OAuth Token 복사

### 3. 로컬 실행

```bash
# 의존성 설치
pip install -e .

# 환경변수 설정
cp .env.example .env
# .env 파일에 각 키 입력

# 즉시 1회 실행 (10건)
python -m src.main --run-now

# 테스트 실행 (1건만)
python -m src.main --test
```

### 4. GitHub Actions 배포 (무료 자동화)

1. 이 저장소를 Fork 또는 Clone 후 GitHub에 Push
2. **Settings → Secrets and variables → Actions** 에서 아래 Secret 추가:

| Secret | 설명 |
|---|---|
| `SLACK_BOT_TOKEN` | Slack Bot OAuth Token |
| `SLACK_CHANNEL_NAME` | 전송할 채널 이름 (예: `ai-digest`) |
| `GROQ_API_KEY` | Groq API Key |
| `TAVILY_API_KEY` | Tavily API Key |

3. **Actions → AI Digest Bot → Run workflow** 으로 수동 테스트 가능

## 환경변수

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_NAME=ai-digest
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...

# 선택 (기본값 사용 가능)
MAX_ITEMS_PER_DIGEST=10
MAX_SUMMARY_CHARS=500
```

## 실행 결과 예시

```
🤖 AI 다이제스트  |  2026년 04월 22일 09:00
최신 AI 소식 10건을 가져왔습니다.
━━━━━━━━━━━━━━━━━━━━━━━━
📌 OpenAI, GPT-5 출시 발표
구글 딥마인드와의 경쟁이 가속화되는 가운데, OpenAI가 차세대 모델 GPT-5를
공식 발표했다. 추론 능력이 크게 향상되었으며...
🔗 원문 보기
━━━━━━━━━━━━━━━━━━━━━━━━
```

## 스케줄

GitHub Actions 기준 (무료 플랜 사용 시 수 분 지연 가능):

| 실행 시각 | UTC |
|---|---|
| 매일 오전 09:00 KST | `0 0 * * *` |
| 매일 오후 09:00 KST | `0 12 * * *` |

## 라이선스

MIT
