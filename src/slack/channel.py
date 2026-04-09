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


def _get_bot_user_id() -> str | None:
    try:
        resp = _get_client().auth_test()
        return resp["user_id"]
    except SlackApiError:
        return None


def _invite_all_members(channel_id: str) -> None:
    """워크스페이스의 일반 사용자를 채널에 초대한다."""
    client = _get_client()
    bot_user_id = _get_bot_user_id()

    try:
        resp = client.users_list()
        user_ids = [
            u["id"] for u in resp["members"]
            if not u.get("is_bot")
            and not u.get("deleted")
            and u["id"] != "USLACKBOT"
            and u["id"] != bot_user_id
        ]
        if user_ids:
            client.conversations_invite(channel=channel_id, users=",".join(user_ids))
            logger.info("채널 초대 완료: %d명", len(user_ids))
    except SlackApiError as e:
        logger.warning("채널 초대 실패: %s", e.response["error"])


def get_or_create_channel() -> str:
    """
    ai-digest 채널 ID를 반환한다.
    채널이 없으면 생성 + 멤버 초대 후 ID를 반환한다.
    이미 있으면 봇이 참여(join)한 뒤 ID를 반환한다.
    """
    client = _get_client()
    channel_name = settings.slack_channel_name

    # 1. 기존 채널 탐색
    try:
        for page in client.conversations_list(types="public_channel", limit=200):
            for ch in page["channels"]:
                if ch["name"] == channel_name:
                    channel_id = ch["id"]
                    logger.debug("채널 발견: #%s (%s)", channel_name, channel_id)
                    # 봇이 멤버가 아니면 참여
                    if not ch.get("is_member"):
                        client.conversations_join(channel=channel_id)
                    return channel_id
    except SlackApiError as e:
        logger.error("채널 목록 조회 실패: %s", e.response["error"])
        raise

    # 2. 없으면 생성 후 멤버 초대
    try:
        resp = client.conversations_create(name=channel_name, is_private=False)
        channel_id = resp["channel"]["id"]
        logger.info("채널 생성: #%s (%s)", channel_name, channel_id)
        _invite_all_members(channel_id)
        return channel_id
    except SlackApiError as e:
        logger.error("채널 생성 실패: %s", e.response["error"])
        raise
