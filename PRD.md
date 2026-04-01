# PRD — AI Digest Bot

## 1. 목적 (Purpose)
AI 분야의 최신 뉴스, 기술 동향, 연구 지식을 자동으로 수집·요약하여 Slack 채널에 정기 전송함으로써, 사용자가 별도 탐색 없이 AI 트렌드를 파악할 수 있도록 한다.

---

## 2. 배경 (Background)
- AI 관련 정보는 매일 방대하게 생산되며 블로그, SNS, 논문, 뉴스 등에 분산되어 있음
- 핵심 내용만 빠르게 파악하고 싶지만 직접 탐색하는 데 시간이 많이 소요됨
- Slack은 이미 일상적으로 사용하는 도구이므로 별도 앱 없이 정보 수신 가능

---

## 3. 범위 (Scope)

### In-scope
- AI 관련 뉴스/기술/연구 콘텐츠 자동 수집
- Google Gemini API를 통한 한국어 요약 생성 (500자 이내)
- Slack 채널 자동 생성 및 메시지 전송 (12시간 간격)
- 중복 콘텐츠 필터링
- Slack 메시지 내 "Notion에 저장" 버튼 — 클릭 시 요약 + URL을 Notion DB에 저장

### Out-of-scope
- 개인화 추천 알고리즘
- 웹 UI / 관리자 대시보드
- 다중 사용자/팀 지원

---

## 4. 사용자 스토리 (User Stories)

| # | As a... | I want to... | So that... |
|---|---------|--------------|------------|
| 1 | 사용자 | Slack에서 AI 뉴스를 받아보고 싶다 | 별도 탐색 없이 트렌드를 파악할 수 있다 |
| 2 | 사용자 | 요약된 내용과 원문 링크를 함께 받고 싶다 | 관심 있는 항목은 원문으로 이동할 수 있다 |
| 3 | 사용자 | 하루 2번(12시간 간격) 정보를 받고 싶다 | 오전/오후 정기적으로 업데이트를 확인할 수 있다 |
| 4 | 사용자 | 정확하고 검증된 정보만 받고 싶다 | 추측이나 루머가 아닌 신뢰할 수 있는 정보를 소비한다 |
| 5 | 사용자 | 한국어로 요약된 내용을 받고 싶다 | 영어 원문 해독 없이 빠르게 이해할 수 있다 |
| 6 | 사용자 | 중요한 기사를 Notion에 버튼 한 번으로 저장하고 싶다 | Slack 90일 보관 제한과 무관하게 영구 아카이빙할 수 있다 |

---

## 5. 기능 요구사항 (Functional Requirements)

### FR-01: 정보 수집
- **수집 소스**: 웹 검색(Tavily), RSS 피드(TechCrunch AI, Google AI Blog, OpenAI Blog, HuggingFace Blog, Ars Technica AI)
- **수집 주기**: 12시간마다 자동 실행
- **대상 기간**: 최근 48시간 이내에 게시된 콘텐츠 우선
- **인기도 정렬**: 검색 랭킹 / 피드 게시 순서 기반 상위 항목 선택

### FR-02: 콘텐츠 필터링
- **제외 조건**:
  - 추측성/의견성 콘텐츠 (예: "~일 것 같다", "개인적으로 생각하기에")
  - AI와 무관한 콘텐츠
  - 이미 전송된 URL (SQLite 이력 DB 기반 중복 제거)
- **포함 조건**:
  - 사실 기반 뉴스, 공식 발표, 연구 논문, 기술 튜토리얼

### FR-03: 요약 생성
- Google Gemini API(`gemini-2.0-flash`) 사용
- 요약 언어: 한국어
- 요약 길이: 500자 이내
- 요약 형식:
  ```
  📌 [제목]
  [500자 이내 한국어 요약]
  🔗 [원문 URL]
  ```

### FR-04: Slack 전송
- **채널**: `ai-digest` (없을 경우 자동 생성)
- **전송 주기**: 매일 오전 9시 / 오후 9시 (KST, UTC+9)
- **메시지 수**: 최대 20개/회
- **메시지 포맷**: Slack Block Kit 사용, 각 항목 하단에 버튼 포함
  ```
  📌 [제목]
  [500자 이내 한국어 요약]
  🔗 원문 보기  |  📎 Notion에 저장
  ───────────────────────────────
  ```
- **헤더 메시지**: 전송 시작 시 날짜/시간 + "AI 다이제스트" 알림 포함

### FR-05: 중복 방지
- SQLite DB에 전송된 URL과 타임스탬프 저장
- 동일 URL은 최소 7일 내 재전송 금지

### FR-06: Notion 저장
- **트리거**: Slack 메시지의 "📎 Notion에 저장" 버튼 클릭
- **저장 데이터**:
  - 제목 (Title)
  - 한국어 요약 (Summary)
  - 원문 URL (URL)
  - 저장 일시 (Saved At)
  - 출처 구분 (Source: RSS / Search)
- **Notion 대상**: 사전 지정한 Notion Database (환경변수 `NOTION_DATABASE_ID`)
- **버튼 클릭 후 피드백**: 저장 성공 시 해당 Slack 메시지의 버튼을 "✅ 저장됨"으로 교체, 실패 시 에러 ephemeral 메시지 표시
- **중복 저장 방지**: 동일 URL이 이미 Notion DB에 있을 경우 "이미 저장된 항목입니다" 안내

### FR-07: Slack Interactivity 웹훅 서버
- Slack 버튼 클릭 이벤트는 HTTP POST 요청으로 전달되므로 **FastAPI 웹 서버** 필요
- 엔드포인트: `POST /slack/interactions`
- Slack 요청 서명 검증 (`SLACK_SIGNING_SECRET`) 필수
- 스케줄러와 웹 서버를 단일 프로세스에서 동시 실행 (`asyncio` 기반)

---

## 6. 비기능 요구사항 (Non-Functional Requirements)

| 항목 | 요구사항 |
|------|----------|
| 안정성 | 수집/요약/전송 단계별 예외처리, 부분 실패 시 나머지 항목 계속 처리 |
| 비용 | Gemini API 호출 최소화 (배치 요약, `gemini-2.0-flash` 모델 사용) |
| 보안 | API 키는 `.env`로 관리, 코드에 하드코딩 금지 |
| 확장성 | 수집 소스를 설정 파일(sources.py)에서 쉽게 추가/제거 가능 |
| 로깅 | 각 실행 단계 로그 기록 (수집 건수, 필터링 건수, 전송 건수) |

---

## 7. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                   단일 프로세스 (asyncio)              │
│                                                     │
│  [Scheduler: APScheduler]                           │
│          │ (12시간마다, KST 09:00 / 21:00)           │
│          ▼                                          │
│  [Collector]                                        │
│    ├── search.py   → Tavily API 웹 검색              │
│    └── rss.py      → RSS 피드 파싱                   │
│          │ (raw items)                              │
│          ▼                                          │
│  [Filter] → 중복 제거 (SQLite) + 품질 필터            │
│          │ (filtered items, max 20)                 │
│          ▼                                          │
│  [Summarizer: Gemini API]                           │
│    └── gemini-2.0-flash, 한국어 요약 500자 이내       │
│          │ (formatted messages + 버튼 포함)           │
│          ▼                                          │
│  [Slack Sender] → Block Kit 메시지 + "Notion에 저장" 버튼
│          │                                          │
│          ▼                                          │
│  [SQLite] ← 전송 URL 이력 저장                       │
│                                                     │
│  [FastAPI 웹 서버] ← POST /slack/interactions        │
│    └── 버튼 클릭 이벤트 수신                          │
│          │ (action_id: save_to_notion)              │
│          ▼                                          │
│  [Notion Client]                                    │
│    └── notion-client → Notion Database에 페이지 생성  │
│          │                                          │
│          ▼                                          │
│  [Slack API] → 버튼을 "✅ 저장됨"으로 업데이트          │
└─────────────────────────────────────────────────────┘
```

### Notion Database 스키마
| 컬럼 | 타입 | 설명 |
|------|------|------|
| Title | title | 기사 제목 |
| Summary | rich_text | 한국어 요약 (500자 이내) |
| URL | url | 원문 링크 |
| Saved At | date | 저장 일시 (KST) |
| Source | select | RSS / Search |

---

## 8. 성공 지표 (Success Metrics)
- 12시간 간격 전송 성공률 ≥ 99%
- 전송 메시지 중 AI 관련성 ≥ 95%
- 중복 메시지 발생률 = 0%
- 평균 요약 생성 소요 시간 ≤ 30초

---

## 9. 제약사항 (Constraints)
- Slack 무료 플랜 사용 시 메시지 보관 기간 제한 (90일) → Notion 저장으로 영구 보관 보완
- Tavily API 무료 플랜: 월 1,000회 검색 (12시간 기준 약 60회/월 → 여유 있음)
- Gemini API 비용: `gemini-2.0-flash` 모델로 비용 최소화 (Google AI Studio 무료 티어 또는 구독 크레딧 활용)
- Slack Interactive Components는 공개 접근 가능한 HTTPS 엔드포인트 필요
  - 로컬 개발: `ngrok` 터널 사용
  - 프로덕션: Railway / Fly.io 등 클라우드 배포 필수
- Notion API: Integration 생성 후 대상 Database에 Integration을 공유(Share) 해야 함
