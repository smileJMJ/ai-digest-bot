import logging

from src.collector import collect_all
from src.db import init_db, mark_sent
from src.filter import apply_filters
from src.slack.channel import get_or_create_channel
from src.slack.sender import send_digest
from src.summarizer.gemini import summarize_all

logger = logging.getLogger(__name__)


async def run_pipeline(max_items: int | None = None) -> None:
    """collect → filter → summarize → send → save URL 전체 파이프라인.

    Args:
        max_items: 처리할 최대 항목 수. None이면 설정값(기본 20) 사용.
    """
    logger.info("=== AI Digest 파이프라인 시작 ===")

    init_db()

    # 1. 수집
    raw_items = collect_all()
    if not raw_items:
        logger.warning("수집된 항목 없음 — 파이프라인 종료")
        return

    # 2. 필터링
    filtered = apply_filters(raw_items)
    if not filtered:
        logger.warning("필터 후 항목 없음 — 파이프라인 종료")
        return

    # 테스트 모드: 항목 수 제한
    if max_items is not None:
        filtered = filtered[:max_items]
        logger.info("테스트 모드: %d건으로 제한", max_items)

    # 3. 요약
    summarized = summarize_all(filtered)

    # 4. Slack 채널 확인/생성
    channel_id = get_or_create_channel()

    # 5. 전송
    send_digest(channel_id, summarized)

    # 6. 전송 URL 이력 저장
    for item, _ in summarized:
        mark_sent(item.url)

    logger.info("=== AI Digest 파이프라인 완료: %d건 ===", len(summarized))
