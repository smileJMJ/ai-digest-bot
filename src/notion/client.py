import logging
from datetime import datetime, timedelta, timezone

from notion_client import Client
from notion_client.errors import APIResponseError

from src.config import settings

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))


class DuplicateURLError(Exception):
    """이미 Notion DB에 저장된 URL일 때 발생."""


_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(auth=settings.notion_api_key)
    return _client


def _is_duplicate(url: str) -> bool:
    """동일 URL이 DB에 이미 존재하는지 확인한다."""
    try:
        result = _get_client().databases.query(
            database_id=settings.notion_database_id,
            filter={
                "property": "URL",
                "url": {"equals": url},
            },
        )
        return len(result["results"]) > 0
    except APIResponseError as e:
        logger.warning("Notion 중복 확인 실패: %s", e)
        return False


def save_to_notion(
    title: str,
    summary: str,
    url: str,
    source: str,
) -> str:
    """
    Notion Database에 새 페이지를 생성한다.
    중복 URL이면 DuplicateURLError를 발생시킨다.
    성공 시 생성된 페이지 URL을 반환한다.
    """
    if _is_duplicate(url):
        raise DuplicateURLError(url)

    now_kst = datetime.now(KST).strftime("%Y-%m-%d")

    try:
        page = _get_client().pages.create(
            parent={"database_id": settings.notion_database_id},
            properties={
                "Title": {
                    "title": [{"text": {"content": title[:200]}}]
                },
                "Summary": {
                    "rich_text": [{"text": {"content": summary[:2000]}}]
                },
                "URL": {
                    "url": url
                },
                "Saved At": {
                    "date": {"start": now_kst}
                },
                "Source": {
                    "select": {"name": source}
                },
            },
        )
        page_url = page.get("url", "")
        logger.info("Notion 저장 완료: %s", title[:40])
        return page_url
    except APIResponseError as e:
        logger.error("Notion 저장 실패 [%s]: %s", url, e)
        raise
