from fastapi import FastAPI, status
from route.registration_info import router as number_router
from route.search_pers_data import router as search_data
from route.common import router as common_router
from config import get_settings
import logging.config
from utils.handlers.middlewares import LoggingMiddleware
from utils.logger.config_logger import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)
logger =  logging.getLogger()

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version=settings.APP_VERSION
)
app.middleware("http")(
    LoggingMiddleware()
)
app.include_router(number_router)
app.include_router(search_data)
app.include_router(common_router)
@app.get("/")
async def root():
    return {
    "status_code":status.HTTP_200_OK,
    "message": "Welcome to the microservice for checking registration in various services by phone number and email."
    }
