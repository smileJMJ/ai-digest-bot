import logging
import time

from groq import Groq

from src.collector.rss import FeedItem
from src.config import settings

logger = logging.getLogger(__name__)

_client: Groq | None = None

_FAIL_SUFFIX = "\n_(ai 요약 호출 실패)_"

_MODEL = "llama-3.3-70b-versatile"


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
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
    text = item.snippet.strip() or item.title
    if len(text) > settings.max_summary_chars:
        text = text[: settings.max_summary_chars - 1] + "…"
    return text + _FAIL_SUFFIX


def summarize(item: FeedItem) -> str:
    """Groq API로 FeedItem을 한국어로 요약한다. 실패 시 원문 + 실패 메시지 반환."""
    if not item.snippet.strip():
        try:
            resp = _get_client().chat.completions.create(
                model=_MODEL,
                messages=[{"role": "user", "content": f"다음 제목을 한국어로 번역해줘. 번역문만 출력해:\n{item.title}"}],
                temperature=0.1,
                max_tokens=100,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("Groq 제목 번역 실패 [%s]: %s", item.url, e)
            return _fallback_text(item)

    prompt = _PROMPT_TEMPLATE.format(
        max_chars=settings.max_summary_chars,
        title=item.title,
        snippet=item.snippet[:2000],
        url=item.url,
    )
    try:
        resp = _get_client().chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        summary = resp.choices[0].message.content.strip()
        if len(summary) > settings.max_summary_chars:
            summary = summary[: settings.max_summary_chars - 1] + "…"
        return summary
    except Exception as e:
        logger.warning("Groq 요약 실패 [%s]: %s — 원문 전송", item.url, e)
        return _fallback_text(item)


def summarize_all(items: list[FeedItem]) -> list[tuple[FeedItem, str]]:
    """모든 항목을 순차 요약하고 (item, summary) 튜플 리스트로 반환한다."""
    results = []
    for i, item in enumerate(items):
        if i > 0:
            time.sleep(1)  # Groq rate limit 여유
        summary = summarize(item)
        results.append((item, summary))
        logger.debug("요약 완료 (%d/%d): %s", i + 1, len(items), item.title[:40])
    logger.info("요약 완료: 총 %d건", len(results))
    return results
