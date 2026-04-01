import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser

from .sources import RSS_SOURCES, RSSSource

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
FETCH_WINDOW_HOURS = 48


@dataclass
class FeedItem:
    title: str
    url: str
    snippet: str
    source: str
    published_at: datetime


def _parse_published(entry) -> datetime | None:
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(KST)
            except Exception:
                pass
    return None


def _is_recent(dt: datetime | None) -> bool:
    if dt is None:
        return True  # 날짜 파싱 실패 시 일단 포함
    cutoff = datetime.now(KST) - timedelta(hours=FETCH_WINDOW_HOURS)
    return dt >= cutoff


def fetch_rss(source: RSSSource) -> list[FeedItem]:
    try:
        feed = feedparser.parse(source.url)
    except Exception as e:
        logger.warning("RSS 파싱 실패 [%s]: %s", source.name, e)
        return []

    items: list[FeedItem] = []
    for entry in feed.entries:
        published_at = _parse_published(entry)
        if not _is_recent(published_at):
            continue

        url = entry.get("link", "")
        if not url:
            continue

        snippet = entry.get("summary", "") or entry.get("description", "")
        # HTML 태그 간단 제거
        import re
        snippet = re.sub(r"<[^>]+>", "", snippet).strip()[:1000]

        items.append(FeedItem(
            title=entry.get("title", "").strip(),
            url=url,
            snippet=snippet,
            source="RSS",
            published_at=published_at or datetime.now(KST),
        ))

    logger.debug("[%s] %d건 수집", source.name, len(items))
    return items


def fetch_all_rss() -> list[FeedItem]:
    results: list[FeedItem] = []
    for source in RSS_SOURCES:
        results.extend(fetch_rss(source))
    logger.info("RSS 전체 수집: %d건", len(results))
    return results
