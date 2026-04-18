import argparse
import asyncio
import logging

from src.db import init_db
from src.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main(run_now: bool = False, test: bool = False) -> None:
    init_db()

    if test:
        logger.info("--test 플래그: 1건만 전송")
        await run_pipeline(max_items=1)
        return

    logger.info("파이프라인 실행")
    await run_pipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Digest Bot")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="즉시 1회 파이프라인 실행 후 종료 (최대 20건)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="1건만 전송 (기능 테스트용)",
    )
    args = parser.parse_args()
    asyncio.run(main(run_now=args.run_now, test=args.test))
