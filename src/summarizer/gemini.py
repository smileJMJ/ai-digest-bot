import logging
import re
import time

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


def summarize(item: FeedItem, retry: int = 3) -> str:
    """
    Gemini API로 FeedItem을 한국어로 요약한다.
    429(속도 제한) 시 최대 retry회 재시도하며, 최종 실패 시 제목을 한국어로 번역해 반환한다.
    """
    prompt = _PROMPT_TEMPLATE.format(
        max_chars=settings.max_summary_chars,
        title=item.title,
        snippet=item.snippet[:2000],
        url=item.url,
    )
    for attempt in range(retry):
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
            err = str(e)
            if "429" in err and attempt < retry - 1:
                # 에러 메시지에서 실제 대기 시간 파싱 ("Please retry in X.XXs")
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", err)
                wait = int(float(match.group(1))) + 2 if match else 60
                logger.warning("Gemini 속도 제한 — %d초 후 재시도 (%d/%d)", wait, attempt + 1, retry)
                time.sleep(wait)
            else:
                logger.warning("Gemini 요약 실패 [%s]: %s — 제목 번역 fallback", item.url, e)
                return _translate_title(item.title)

    return _translate_title(item.title)


def _translate_title(title: str) -> str:
    """제목을 한국어로 번역한다. 실패 시 원문 반환."""
    try:
        resp = _get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=f"다음 제목을 한국어로 번역해줘. 번역문만 출력해:\n{title}",
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=100),
        )
        return resp.text.strip()
    except Exception:
        return title


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
