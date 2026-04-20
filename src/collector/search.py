import logging
from datetime import datetime, timedelta, timezone

from tavily import TavilyClient

from src.config import settings
from .rss import FeedItem
from .sources import SEARCH_QUERIES

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))

_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


def search_ai_news(test_mode: bool = False) -> list[FeedItem]:
    """Tavily로 AI 뉴스를 검색한다.

    Args:
        test_mode: True이면 첫 번째 쿼리에서 1건만 가져오고 나머지 쿼리는 건너뜀.
    """
    client = _get_client()
    results: list[FeedItem] = []

    queries = SEARCH_QUERIES[:1] if test_mode else SEARCH_QUERIES
    max_results = 1 if test_mode else 10

    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
            )
        except Exception as e:
            logger.warning("Tavily 검색 실패 [%s]: %s", query, e)
            continue

        for r in response.get("results", []):
            url = r.get("url", "")
            if not url:
                continue
            results.append(FeedItem(
                title=r.get("title", "").strip(),
                url=url,
                snippet=r.get("content", "").strip()[:1000],
                source="Search",
                published_at=datetime.now(KST),
                score=float(r.get("score", 0.0)),
            ))

        logger.debug("검색 [%s]: %d건", query, len(response.get("results", [])))

    logger.info("Tavily 검색 전체: %d건", len(results))
    return results
