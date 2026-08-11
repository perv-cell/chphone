from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from service.depends import get_common_service, get_common_db
from fastapi import FastAPI
import datetime


@asynccontextmanager
async def lifespan(app:FastAPI):

    schedular = BackgroundScheduler()

    repo_proxy = get_common_db()
    proxy_service = get_common_service(repo_proxy)

    schedular.add_job(

    )
