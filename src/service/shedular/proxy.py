from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from service.depends import get_common_service, get_common_db
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from fastapi import FastAPI
import logging

logger = logging.getLogger("shedular.proxy")

async def fetch_and_save_proxies():
    try:
        repo_proxy = get_common_db()
        proxy_service = get_common_service(repo_proxy)
        proxys = await proxy_service.checking_work_proxy()
        await proxy_service.save_works_proxys(proxys)

        logger.info(f"Данные redis успешно обновились новыми прокси")
    except Exception as e:
        logger.error(str(e))

@asynccontextmanager
async def lifespan(app:FastAPI):

    jobstores = {
            'default': MemoryJobStore()
        }
    executors = {
        'default': AsyncIOExecutor()
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        timezone='Europe/Moscow'
    )

    scheduler.add_job(
        fetch_and_save_proxies,
        trigger=CronTrigger(hour=12, minute=0),
        id="daily_proxy_update",
        replace_existing=True
    )

    scheduler.start()

    yield

    scheduler.shutdown()
