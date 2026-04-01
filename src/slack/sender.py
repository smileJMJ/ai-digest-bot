import json
import logging
from datetime import datetime, timedelta, timezone

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.collector.rss import FeedItem
from src.config import settings

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client
    if _client is None:
        _client = WebClient(token=settings.slack_bot_token)
    return _client


def _build_item_blocks(item: FeedItem, summary: str) -> list[dict]:
    """항목 1개에 대한 Block Kit 블록을 반환한다."""
    # 버튼에 전달할 데이터 (512자 제한)
    value = json.dumps({
        "title": item.title[:100],
        "summary": summary[:400],
        "url": item.url,
        "source": item.source,
    }, ensure_ascii=False)

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📌 {item.title}*\n{summary}",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔗 원문 보기"},
                    "url": item.url,
                    "action_id": "open_url",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📎 Notion에 저장"},
                    "action_id": "save_to_notion",
                    "value": value,
                    "style": "primary",
                },
            ],
        },
        {"type": "divider"},
    ]


def send_digest(channel_id: str, items_with_summaries: list[tuple[FeedItem, str]]) -> None:
    """
    헤더 메시지 + 각 항목을 Slack 채널에 전송한다.
    """
    client = _get_client()
    now = datetime.now(KST).strftime("%Y년 %m월 %d일 %H:%M")
    count = len(items_with_summaries)

    # 헤더
    try:
        client.chat_postMessage(
            channel=channel_id,
            text=f"🤖 AI 다이제스트 | {now}",
            blocks=[
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"🤖 AI 다이제스트  |  {now}"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"최신 AI 소식 *{count}건*을 가져왔습니다.",
                    },
                },
                {"type": "divider"},
            ],
        )
    except SlackApiError as e:
        logger.error("헤더 메시지 전송 실패: %s", e.response["error"])

    # 각 항목
    success = 0
    for item, summary in items_with_summaries:
        try:
            blocks = _build_item_blocks(item, summary)
            client.chat_postMessage(
                channel=channel_id,
                text=f"📌 {item.title}",  # 알림 fallback 텍스트
                blocks=blocks,
            )
            success += 1
        except SlackApiError as e:
            logger.warning("항목 전송 실패 [%s]: %s", item.url, e.response["error"])

    logger.info("Slack 전송 완료: %d/%d건", success, count)
