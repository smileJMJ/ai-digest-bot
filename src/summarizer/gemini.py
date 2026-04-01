import logging

from google import genai
from google.genai import types

from src.collector.rss import FeedItem
from src.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


_PROMPT_TEMPLATE = """\
아래 기사를 {max_chars}자 이내의 한국어로 요약해줘.

규칙:
- 사실만 포함하고 추측·개인 의견은 절대 쓰지 마
- 핵심 내용(무엇이, 왜 중요한지)을 간결하게
- 원문의 주요 수치·고유명사는 그대로 유지
- 요약문만 출력하고 다른 말은 붙이지 마

제목: {title}
본문: {snippet}
URL: {url}
"""


def summarize(item: FeedItem) -> str:
    """
    Gemini API로 FeedItem을 한국어 요약한다.
    실패 시 snippet 앞 max_chars 자를 fallback으로 반환한다.
    """
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
        # 혹시 max_chars 초과 시 자르기
        if len(summary) > settings.max_summary_chars:
            summary = summary[: settings.max_summary_chars - 1] + "…"
        return summary
    except Exception as e:
        logger.warning("Gemini 요약 실패 [%s]: %s — fallback 사용", item.url, e)
        fallback = item.snippet[: settings.max_summary_chars]
        return fallback if fallback else item.title


def summarize_all(items: list[FeedItem]) -> list[tuple[FeedItem, str]]:
    """모든 항목을 요약하고 (item, summary) 튜플 리스트로 반환한다."""
    results = []
    for item in items:
        summary = summarize(item)
        results.append((item, summary))
        logger.debug("요약 완료: %s", item.title[:40])
    logger.info("요약 완료: 총 %d건", len(results))
    return results
