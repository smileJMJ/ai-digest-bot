import logging
import time

from google import genai
from google.genai import types

from src.collector.rss import FeedItem
from src.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

_FAIL_SUFFIX = "\n_(gemini api 호출 실패)_"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


_PROMPT_TEMPLATE = """\
아래 기사를 반드시 한국어로 {max_chars}자 이내로 요약해줘. 영어로 출력하면 안 돼.

규칙:
- 반드시 한국어로만 작성
- 사실만 포함하고 추측·개인 의견은 절대 쓰지 마
- 핵심 내용(무엇이, 왜 중요한지)을 간결하게
- 원문의 주요 수치·고유명사는 그대로 유지
- 요약문만 출력하고 다른 말은 붙이지 마

제목: {title}
본문: {snippet}
URL: {url}
"""


def _fallback_text(item: FeedItem) -> str:
    """Gemini 실패 시 원문 snippet(또는 제목)을 그대로 반환."""
    text = item.snippet.strip() or item.title
    if len(text) > settings.max_summary_chars:
        text = text[: settings.max_summary_chars - 1] + "…"
    return text + _FAIL_SUFFIX


def summarize(item: FeedItem) -> str:
    """
    Gemini API로 FeedItem을 한국어로 요약한다.
    실패(할당량 소진, 오류 등) 시 재시도 없이 원문 내용 + "(gemini api 호출 실패)" 반환.
    """
    if not item.snippet.strip():
        try:
            resp = _get_client().models.generate_content(
                model="gemini-2.0-flash",
                contents=f"다음 제목을 한국어로 번역해줘. 번역문만 출력해:\n{item.title}",
                config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=100),
            )
            return resp.text.strip()
        except Exception as e:
            logger.warning("Gemini 제목 번역 실패 [%s]: %s", item.url, e)
            return _fallback_text(item)

    prompt = _PROMPT_TEMPLATE.format(
        max_chars=settings.max_summary_chars,
        title=item.title,
        snippet=item.snippet[:2000],
        url=item.url,
    )
    try:
        response = _get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=600,
            ),
        )
        summary = response.text.strip()
        if len(summary) > settings.max_summary_chars:
            summary = summary[: settings.max_summary_chars - 1] + "…"
        return summary
    except Exception as e:
        logger.warning("Gemini 요약 실패 [%s]: %s — 원문 전송", item.url, e)
        return _fallback_text(item)


def summarize_all(items: list[FeedItem]) -> list[tuple[FeedItem, str]]:
    """모든 항목을 순차 요약하고 (item, summary) 튜플 리스트로 반환한다."""
    results = []
    for i, item in enumerate(items):
        if i > 0:
            time.sleep(4)  # 15 RPM 한도 준수 (60초 / 15 = 4초 간격)
        summary = summarize(item)
        results.append((item, summary))
        logger.debug("요약 완료 (%d/%d): %s", i + 1, len(items), item.title[:40])
    logger.info("요약 완료: 총 %d건", len(results))
    return results
