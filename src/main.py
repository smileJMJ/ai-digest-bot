import argparse
import asyncio
import logging

import uvicorn

from src.config import settings
from src.db import init_db
from src.pipeline import run_pipeline
from src.scheduler import create_scheduler
from src.server import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def _serve() -> None:
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main(run_now: bool = False, test: bool = False) -> None:
    init_db()

    if test:
        logger.info("--test 플래그: 1건만 전송")
        await run_pipeline(max_items=1)
        return

    if run_now:
        logger.info("--run-now 플래그: 즉시 1회 실행")
        await run_pipeline()
        return

    scheduler = create_scheduler()
    scheduler.start()
    logger.info("스케줄러 시작 (KST 09:00 / 21:00)")
    logger.info("FastAPI 서버 시작 (port %d)", settings.port)

    try:
        await _serve()
    finally:
        scheduler.shutdown()
        logger.info("종료")


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
        help="1건만 전송 (Notion 버튼 등 기능 테스트용)",
    )
    args = parser.parse_args()
    asyncio.run(main(run_now=args.run_now, test=args.test))
