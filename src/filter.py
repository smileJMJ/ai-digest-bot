import logging
import re

from src.collector.rss import FeedItem
from src.config import settings
from src.db import is_sent

logger = logging.getLogger(__name__)

# 추측성/의견성 표현 — 해당 키워드가 제목에 포함된 항목 제외
_SPECULATIVE_PATTERNS = re.compile(
    r"\b(rumor|rumour|allegedly|unconfirmed|leak|leaks|leaked"
    r"|could be|might be|may be|possibly|apparently"
    r"|개인적으로|추측|루머|카더라|~인 것 같|~일 수도)\b",
    re.IGNORECASE,
)


def _is_speculative(item: FeedItem) -> bool:
    return bool(_SPECULATIVE_PATTERNS.search(item.title + " " + item.snippet))


def apply_filters(items: list[FeedItem]) -> list[FeedItem]:
    """
    1. 이미 전송된 URL 제거 (sent_urls DB, 7일 이내)
    2. 추측성/의견성 콘텐츠 제거
    3. score(인기/관련도) 내림차순 정렬
    4. 최대 MAX_ITEMS_PER_DIGEST 개로 슬라이싱
    """
    before = len(items)

    # 1. 전송 이력 필터
    items = [i for i in items if not is_sent(i.url)]
    logger.debug("전송 이력 필터: %d → %d건", before, len(items))

    # 2. 품질 필터 (추측성 제거)
    before = len(items)
    items = [i for i in items if not _is_speculative(i)]
    logger.debug("품질 필터: %d → %d건", before, len(items))

    # 3. 인기/관련도 높은 순 정렬 (Tavily score 기준, RSS는 0.0)
    items.sort(key=lambda x: x.score, reverse=True)

    # 4. 최대 개수 슬라이싱
    items = items[: settings.max_items_per_digest]
    logger.info("필터 완료: 최종 %d건", len(items))

    return items
