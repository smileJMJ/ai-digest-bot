import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.config import settings

logger = logging.getLogger(__name__)

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client
    if _client is None:
        _client = WebClient(token=settings.slack_bot_token)
    return _client


def get_or_create_channel() -> str:
    """
    ai-digest 채널 ID를 반환한다.
    채널이 없으면 생성 후 ID를 반환한다.
    """
    client = _get_client()
    channel_name = settings.slack_channel_name

    # 1. 기존 채널 목록에서 탐색
    try:
        for page in client.conversations_list(types="public_channel", limit=200):
            for ch in page["channels"]:
                if ch["name"] == channel_name:
                    logger.debug("채널 발견: #%s (%s)", channel_name, ch["id"])
                    return ch["id"]
    except SlackApiError as e:
        logger.error("채널 목록 조회 실패: %s", e.response["error"])
        raise

    # 2. 없으면 생성
    try:
        resp = client.conversations_create(name=channel_name, is_private=False)
        channel_id = resp["channel"]["id"]
        logger.info("채널 생성: #%s (%s)", channel_name, channel_id)
        return channel_id
    except SlackApiError as e:
        logger.error("채널 생성 실패: %s", e.response["error"])
        raise
