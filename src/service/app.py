import sys
from pathlib import Path

# Добавляем корневую папку в пути поиска Python
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from route.number import router as number_router
from service.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0"
)

app.include_router(number_router)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}