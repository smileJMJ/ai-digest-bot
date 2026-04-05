import json
import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.config import settings
from src.notion.client import DuplicateURLError, save_to_notion

logger = logging.getLogger(__name__)

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client
    if _client is None:
        _client = WebClient(token=settings.slack_bot_token)
    return _client


def _replace_button_with_saved(channel: str, ts: str, original_blocks: list) -> None:
    """'📎 Notion에 저장' 버튼을 '✅ 저장됨' 텍스트로 교체한다."""
    new_blocks = []
    for block in original_blocks:
        if block.get("type") == "actions":
            elements = [
                e for e in block["elements"]
                if e.get("action_id") != "save_to_notion"
            ]
            elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "✅ 저장됨"},
                "action_id": "already_saved",
            })
            new_blocks.append({**block, "elements": elements})
        else:
            new_blocks.append(block)

    try:
        _get_client().chat_update(
            channel=channel,
            ts=ts,
            blocks=new_blocks,
            text="Notion에 저장됨",
        )
    except SlackApiError as e:
        logger.warning("메시지 업데이트 실패: %s", e.response["error"])


def _send_ephemeral(channel: str, user_id: str, text: str) -> None:
    try:
        _get_client().chat_postEphemeral(
            channel=channel,
            user=user_id,
            text=text,
        )
    except SlackApiError as e:
        logger.warning("ephemeral 메시지 전송 실패: %s", e.response["error"])


async def handle_interaction(payload: dict) -> None:
    actions = payload.get("actions", [])
    if not actions:
        return

    action = actions[0]
    if action.get("action_id") != "save_to_notion":
        return

    channel = payload["channel"]["id"]
    user_id = payload["user"]["id"]
    ts = payload["message"]["ts"]
    original_blocks = payload["message"].get("blocks", [])

    try:
        data = json.loads(action["value"])
    except (KeyError, json.JSONDecodeError) as e:
        logger.error("payload 파싱 실패: %s", e)
        _send_ephemeral(channel, user_id, "⚠️ 저장 중 오류가 발생했습니다.")
        return

    try:
        save_to_notion(
            title=data["title"],
            summary=data["summary"],
            url=data["url"],
            source=data.get("source", "Unknown"),
        )
        _replace_button_with_saved(channel, ts, original_blocks)
        logger.info("Notion 저장 성공: %s", data["url"])

    except DuplicateURLError:
        _send_ephemeral(channel, user_id, "ℹ️ 이미 Notion에 저장된 항목입니다.")

    except Exception as e:
        logger.error("Notion 저장 실패: %s", e)
        _send_ephemeral(channel, user_id, "⚠️ Notion 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
