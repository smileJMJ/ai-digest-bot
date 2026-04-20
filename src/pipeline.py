import logging

from src.collector import collect_all
from src.db import init_db, mark_sent
from src.filter import apply_filters
from src.slack.channel import get_or_create_channel
from src.slack.sender import send_digest
from src.summarizer.gemini import summarize_all

logger = logging.getLogger(__name__)


async def run_pipeline(max_items: int | None = None, test_mode: bool = False) -> None:
    """collect → filter → summarize → send → save URL 전체 파이프라인.

    Args:
        max_items: 처리할 최대 항목 수. None이면 설정값(기본 10) 사용.
        test_mode: True이면 Tavily 1건만 수집하고 RSS는 건너뜀.
    """
    logger.info("=== AI Digest 파이프라인 시작 ===")

    init_db()

    # 1. 수집
    raw_items = collect_all(test_mode=test_mode)
    if not raw_items:
        logger.warning("수집된 항목 없음 — 파이프라인 종료")
        return

    # 2. 필터링
    filtered = apply_filters(raw_items, test_mode=test_mode)
    if not filtered:
        logger.warning("필터 후 항목 없음 — 파이프라인 종료")
        return

    if test_mode:
        filtered = filtered[:1]

    # 3. 요약 (실패 시 원문 + "(gemini api 호출 실패)" 반환, 항상 전송)
    summarized = summarize_all(filtered)

    # 4. Slack 채널 확인/생성
    channel_id = get_or_create_channel()

    # 5. 전송
    send_digest(channel_id, summarized)

    # 6. 전송 URL 이력 저장
    for item, _ in summarized:
        mark_sent(item.url)

    logger.info("=== AI Digest 파이프라인 완료: %d건 ===", len(summarized))
