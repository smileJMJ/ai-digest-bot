# Tasks — AI Digest Bot

## Phase 1: 프로젝트 기반 세팅

- [x] **T-01** `pyproject.toml` 작성 (의존성: `google-genai`, `slack-sdk`, `apscheduler`, `feedparser`, `httpx`, `tavily-python`, `pydantic-settings`, `notion-client`, `fastapi`, `uvicorn`)
- [x] **T-02** `.env.example` 파일 작성 (필요한 환경변수 목록 문서화)
- [x] **T-03** `src/config.py` 작성 — `pydantic-settings`로 환경변수 로드 및 검증
- [x] **T-04** SQLite 초기화 모듈 작성 — `sent_urls` 테이블 생성 (url, sent_at)

---

## Phase 2: 정보 수집 (Collector)

- [x] **T-05** `src/collector/sources.py` 작성 — RSS 피드 URL 목록 정의
  - OpenAI Blog, Google AI Blog, HuggingFace Blog, TechCrunch AI, Ars Technica AI
- [x] **T-06** `src/collector/rss.py` 작성 — `feedparser`로 RSS 피드 파싱, 최근 48시간 필터 적용
- [x] **T-07** `src/collector/search.py` 작성 — Tavily API로 "AI latest news" 웹 검색, 상위 결과 반환
- [x] **T-08** 수집 결과를 통합하는 `collect_all()` 함수 작성 — RSS + 검색 결과 병합 후 중복 URL 제거

---

## Phase 3: 필터링

- [ ] **T-09** 이미 전송된 URL 필터 구현 — SQLite `sent_urls` 조회 후 제외
- [ ] **T-10** 품질 필터 구현 — 제목/본문에 추측성 표현 키워드 포함 시 제외 (예: "rumor", "allegedly", "I think")
- [ ] **T-11** 최대 20개 항목으로 슬라이싱 로직 추가

---

## Phase 4: 요약 생성 (Summarizer)

- [ ] **T-12** `src/summarizer/gemini.py` 작성 — Google Gemini API(`gemini-2.0-flash`) 호출
- [ ] **T-13** 요약 프롬프트 설계
  - 입력: 기사 제목 + 본문(또는 스니펫) + URL
  - 출력: 500자 이내 한국어 요약
  - 제약: 추측/의견 배제, 사실만 요약
- [ ] **T-14** 요약 실패(API 오류) 시 fallback 처리 — 원본 스니펫을 그대로 사용

---

## Phase 5: Slack 연동

- [ ] **T-15** Slack 앱 생성 및 권한 설정
  - Scopes: `channels:manage`, `channels:read`, `chat:write`, `chat:write.public`
  - Bot Token 및 Signing Secret 발급
  - Interactive Components 활성화 및 Request URL 설정
- [ ] **T-16** `src/slack/channel.py` 작성 — `ai-digest` 채널 존재 확인 및 없을 경우 자동 생성
- [ ] **T-17** `src/slack/sender.py` 작성 — Block Kit 메시지 전송 함수 구현
  - 헤더 메시지 (날짜, 총 항목 수)
  - 각 항목: 제목 + 한국어 요약 + "🔗 원문 보기" 링크 버튼 + "📎 Notion에 저장" 액션 버튼
- [ ] **T-18** Block Kit JSON 구조 설계
  - `section` 블록: 요약 텍스트
  - `actions` 블록: 원문 링크 버튼(url 타입) + Notion 저장 버튼(button 타입, value에 JSON 인코딩)
  - `divider` 블록: 항목 구분선

---

## Phase 6: Notion 연동

- [ ] **T-19** Notion Integration 생성 및 Database 설정
  - Notion 내 새 Database 생성 (Title, Summary, URL, Saved At, Source 컬럼)
  - Integration을 Database에 Share
  - API Key 및 Database ID 수집
- [ ] **T-20** `src/notion/client.py` 작성 — `notion-client`로 Database에 페이지 생성
  - 입력: title, summary, url, source
  - 중복 URL 체크 후 이미 존재하면 예외 반환

---

## Phase 7: Slack Interactivity 웹훅 서버

- [ ] **T-21** `src/server.py` 작성 — FastAPI 앱 정의
  - `POST /slack/interactions` 엔드포인트
  - Slack Signing Secret으로 요청 서명 검증
- [ ] **T-22** `src/slack/interactions.py` 작성 — 버튼 클릭 이벤트 처리 로직
  - `action_id: save_to_notion` 인식
  - payload의 `value`에서 title, summary, url, source 파싱
  - `notion/client.py` 호출하여 저장
  - 저장 성공: `chat.update`로 버튼을 "✅ 저장됨" 텍스트로 교체
  - 저장 실패 / 중복: ephemeral 메시지로 사용자에게 안내

---

## Phase 8: 스케줄러 및 통합 실행

- [ ] **T-23** `src/scheduler.py` 작성 — APScheduler CronTrigger 설정
  - KST 기준 09:00 / 21:00 실행 (UTC 00:00 / 12:00)
- [ ] **T-24** `src/main.py` 작성 — 스케줄러 + FastAPI 서버 동시 실행 (`asyncio`)
  - `--run-now` 플래그 지원 (즉시 1회 실행)
- [ ] **T-25** 전체 파이프라인 연결 — collect → filter → summarize → send → save URL

---

## Phase 9: 로깅 및 에러 처리

- [ ] **T-26** Python `logging` 모듈 설정 — 단계별 로그 (수집 N건, 필터 후 N건, 전송 N건, Notion 저장 N건)
- [ ] **T-27** 단계별 예외처리 — 수집/요약/전송 중 일부 항목 실패 시 나머지 계속 진행
- [ ] **T-28** 전송 완료된 URL SQLite에 저장 (sent_at 타임스탬프 포함)

---

## Phase 10: 테스트 및 배포

- [ ] **T-29** 단위 테스트 작성 — 필터링 로직, Block Kit 버튼 payload 형식, Notion 저장 검증
- [ ] **T-30** 통합 테스트 — `--run-now`로 실제 Slack 전송 및 Notion 저장 버튼 동작 확인
- [ ] **T-31** 배포 환경 결정 및 설정 (Railway / Fly.io 권장 — 공개 HTTPS 엔드포인트 필수)
- [ ] **T-32** README.md 작성 — 설치/설정/실행 방법 및 ngrok 로컬 개발 방법 문서화

---

## 의존성 맵

```
T-01 → T-03 → T-04
T-05 → T-06 → T-08
T-07 → T-08
T-08 → T-09 → T-11
T-09, T-10 → T-11
T-11 → T-12 → T-13 → T-14
T-15 → T-16 → T-17 → T-18
T-19 → T-20
T-11, T-14, T-18 → T-25
T-03, T-25 → T-23 → T-24
T-15, T-20 → T-21 → T-22
T-22, T-24 → T-26 → T-27 → T-28
T-28 → T-29 → T-30 → T-31 → T-32
```
