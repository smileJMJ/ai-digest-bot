import logging

from .rss import FeedItem, fetch_all_rss
from .search import search_ai_news

logger = logging.getLogger(__name__)


def collect_all(test_mode: bool = False) -> list[FeedItem]:
    """RSS + 웹 검색 결과를 병합하고 URL 기준 중복을 제거해 반환한다.

    Args:
        test_mode: True이면 Tavily 1건만 가져오고 RSS는 건너뜀.
    """
    if test_mode:
        search_items = search_ai_news(test_mode=True)
        logger.info("테스트 모드: Tavily %d건만 수집", len(search_items))
        return search_items

    rss_items = fetch_all_rss()
    search_items = search_ai_news()

    seen: set[str] = set()
    merged: list[FeedItem] = []

    for item in rss_items + search_items:
        if item.url in seen:
            continue
        seen.add(item.url)
        merged.append(item)

    logger.info("수집 완료: RSS %d건 + 검색 %d건 → 중복 제거 후 %d건",
                len(rss_items), len(search_items), len(merged))
    return merged
