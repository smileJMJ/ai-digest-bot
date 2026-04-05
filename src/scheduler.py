import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # KST 09:00 / 21:00 실행
    for hour in (9, 21):
        scheduler.add_job(
            run_pipeline,
            trigger=CronTrigger(hour=hour, minute=0, timezone="Asia/Seoul"),
            id=f"digest_{hour:02d}00",
            name=f"AI Digest {hour:02d}:00 KST",
            misfire_grace_time=300,  # 5분 내 재실행 허용
        )
        logger.info("스케줄 등록: 매일 %02d:00 KST", hour)

    return scheduler
