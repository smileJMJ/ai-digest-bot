import hashlib
import hmac
import logging
import time

from fastapi import FastAPI, Form, Header, HTTPException, Request

from src.config import settings
from src.slack.interactions import handle_interaction

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Digest Bot")


def _verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Slack 요청 서명을 검증한다."""
    # 5분 이상 지난 요청 거부 (replay attack 방지)
    if abs(time.time() - float(timestamp)) > 300:
        return False

    base = f"v0:{timestamp}:{body.decode()}"
    expected = "v0=" + hmac.new(
        settings.slack_signing_secret.encode(),
        base.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/slack/interactions")
async def slack_interactions(
    request: Request,
    payload: str = Form(...),
    x_slack_request_timestamp: str = Header(...),
    x_slack_signature: str = Header(...),
):
    body = await request.body()

    if not _verify_slack_signature(body, x_slack_request_timestamp, x_slack_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    import json
    data = json.loads(payload)
    await handle_interaction(data)

    # Slack은 3초 이내 200 응답을 요구함
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
