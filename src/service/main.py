from fastapi import FastAPI, status
from route.number import router as number_router
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

@app.get("/")
async def root():
    return {
    "status_code":status.HTTP_200_OK,
    "message": "Welcome to the microservice for checking registration in various services by phone number and email."
    }
