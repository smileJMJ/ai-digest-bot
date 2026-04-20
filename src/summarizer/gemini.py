import logging
import re
import time

from google import genai
from google.genai import types

from src.collector.rss import FeedItem
from src.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


class GeminiQuotaExhaustedError(Exception):
    """일일 Gemini API 할당량이 소진되었을 때 발생."""


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


def _is_daily_quota_error(err: str) -> bool:
    """일일 할당량 소진 에러인지 확인 (RPM 초과와 구분)."""
    return "GenerateRequestsPerDayPerProjectPerModel" in err


def summarize(item: FeedItem, retry: int = 3) -> str:
    """
    Gemini API로 FeedItem을 한국어로 요약한다.
    - RPM(분당 요청) 초과 시: 대기 후 재시도
    - 일일 할당량 소진 시: 즉시 GeminiQuotaExhaustedError 발생 (재시도 없음)
    """
    # snippet이 없으면 제목 번역 fallback
    if not item.snippet.strip():
        return _translate_title(item.title)

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
            if "429" not in err:
                logger.warning("Gemini 요약 실패 [%s]: %s — 제목 번역 fallback", item.url, e)
                return _translate_title(item.title)

            # 일일 할당량 소진 → 재시도 없이 즉시 중단
            if _is_daily_quota_error(err):
                logger.error("Gemini 일일 할당량 소진 — 파이프라인 중단")
                raise GeminiQuotaExhaustedError("일일 API 할당량 소진")

            # RPM 초과 → 대기 후 재시도
            if attempt < retry - 1:
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", err)
                wait = int(float(match.group(1))) + 2 if match else 60
                logger.warning("Gemini RPM 초과 — %d초 후 재시도 (%d/%d)", wait, attempt + 1, retry)
                time.sleep(wait)
            else:
                logger.warning("Gemini 요약 실패 [%s]: RPM 초과, 재시도 소진 — 제목 번역 fallback", item.url)
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
    """모든 항목을 순차 요약하고 (item, summary) 튜플 리스트로 반환한다.

    Raises:
        GeminiQuotaExhaustedError: 일일 할당량 소진 시 즉시 발생.
    """
    results = []
    for i, item in enumerate(items):
        if i > 0:
            time.sleep(4)  # 15 RPM 한도 준수 (60초 / 15 = 4초 간격)
        summary = summarize(item)  # GeminiQuotaExhaustedError는 그대로 전파
        results.append((item, summary))
        logger.debug("요약 완료 (%d/%d): %s", i + 1, len(items), item.title[:40])
    logger.info("요약 완료: 총 %d건", len(results))
    return results
