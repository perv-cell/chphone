from fastapi.param_functions import Depends
from route.repositories.database.postgres import PostgresRepositories
import asyncio
from concurrent.futures import ThreadPoolExecutor
from route.repositories.models import ServiceType
from typing import Dict, Optional, Any, List
import datetime
from route.repositories.models import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import aiohttp
from selenium import webdriver
from schemas.object_search import RequestSearchEngine
from service.services.utils.services.restore_service import VKRestoreService
from service.services.utils.services.session_manager import VKSessionManager
import re

logger = logging.getLogger("service.number")

class NumberService:
    """
    Сервис для работы с номерами телефонов и проверки их регистрации в соцсетях
    """

    def __init__(self, repo: PostgresRepositories):
        self.repo = repo
        self.executor = ThreadPoolExecutor(max_workers=10)


    async def check_phone_registration(self, phone: str, proxys: Dict[str, Dict]) -> dict:
            """
            Проверка регистрации номера в VK (публичный эндпоинт, без авторизации)
            """

            phone = self._normalize_phone(phone)
            session_meneger = VKSessionManager(headless=False, proxys=proxys)

            result = session_meneger.check_registration_number_result(phone)
            if result.get("not_defined", False):
                return {
                    "success": False,
                    "registered": False,
                    "message": "Не удалось проскрапить"
                }

            if result.get("registration", False):
                return {
                    "success": True,
                    "registered": True,
                    "message": "Номер телефона зарегистрирован в VK"
                }
            else:
                return {
                    "success": True,
                    "registered": False,
                    "message": "Номер не зарегистрирован в VK"
                }


    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Нормализация номера телефона"""
            # Убираем все кроме цифр
        cleaned = re.sub(r'[^\d]', '', phone)

            # Если начинается с 8, заменяем на 7
        if cleaned.startswith('8'):
                cleaned = '7' + cleaned[1:]

        if not cleaned.startswith('7'):
            cleaned = '7' + cleaned

        return cleaned
