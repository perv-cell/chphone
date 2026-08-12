from fastapi import HTTPException, status
from fastapi.param_functions import Depends
from route.repositories.database.email import EmailRepository
from concurrent.futures import ThreadPoolExecutor
from route.repositories.models import ServiceType
from typing import Dict, Optional, Any, List
from route.repositories.models import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
from service.services.utils.services.restore_service import VKRestoreService
from service.services.utils.services.session_manager import VKSessionManager
from schemas.object_search import RequestSearchBreachesEmail, ResponceSearchBreachesEmail, RequestSearchRegistration , ResponseSearchRegistration
from holehe.core import import_submodules, get_functions
import asyncio
import re

class EmailService:
    def __init__(self, repo:EmailRepository):
        self.repo = repo
        self.executor = ThreadPoolExecutor(max_workers=10)


    async def check_email_registration(self, email: str, proxys:  Dict[str, Dict]) -> dict:
            """
            Проверка регистрации номера в VK (публичный эндпоинт, без авторизации)
            """

            is_valid_email = self._validate_email(email)
            if not is_valid_email:
                return {
                    "success": True,
                    "registered": False,
                    "message": "Email не валидный"
                }

            session_meneger = VKSessionManager(headless=True, proxys=proxys)
            # к сожадению так можно будет сделать 5 раз потом будет просить посторить попытку через 24 часа
            # как вариант проксировать с разных устройств но на каждое устройство будет по 5 попыток
            # можно продолжить кидать запросы по истечению часа не на 24 часа. поэтому постоянно меняя сервера можно добиться постоянной работы
            not_exists_number = session_meneger.check_registration_email_result(email)
            if not_exists_number:
                return {
                    "success": True,
                    "registered": False,
                    "message": "Email не зарегистрирован в VK"
                }
            else:
                return {
                    "success": True,
                    "registered": True,
                    "message": "Email зарегистрирован в VK"
                 }

    # деделать proxy для обращение к внешним ресурсам

    async def check_registration_email_sites_external_source(self, data: RequestSearchRegistration, proxys:  Dict[str, Dict]):
        #proxys необходимо разработать подключение к proxys как в check_email_registration
        _ = proxys
        """
        Проверка регистрации email на сторонних сайтах
        """
        all_modules = import_submodules("holehe.modules")
        check_functions = get_functions(all_modules)
        results = []
        checking_sites = []

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as client:
            tasks = []
            for func in check_functions:
                if data.details:
                    checking_sites.append(func.__name__)

                task = asyncio.create_task(
                    self._run_check_function(func, data.object_search, client, results)
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        found_accounts = []
        for result in results:
            if result.get("exists", False):
                found_accounts.append({
                    "site": result.get("name", "unknown"),  # Используем name как site
                    "domain": result.get("domain") or result.get("url", "").replace("https://", "").replace("http://", "").split("/")[0] or "unknown",
                    "recovery_email": result.get("emailrecovery"),
                    "phone": result.get("phoneNumber"),
                    "exists": True
                })

        return {
            "find_result": found_accounts,
            "cheking_site": checking_sites
        }

    async def _run_check_function(self, func, email, client, results):
        """
        Обёртка для выполнения одной функции проверки
        """
        try:
            # Вызываем функцию проверки
            await func(email, client, results)
        except Exception as e:
            # В случае ошибки добавляем результат с ошибкой
            results.append({
                "name": getattr(func, '__name__', 'unknown'),
                "exists": False,
                "error": str(e)
            })

    async def search_resources_leakage_email(self, data:RequestSearchBreachesEmail):
        """
        Проверка утечки электронной почты
        """
        email = data.email
        # url для проверки
        url = f"https://api.xposedornot.com/v1/check-email/{email}"

        if data.details:
            url+="?details=true"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as reposnse:

                    data = await reposnse.json()

                    if "Error" in data:
                        return ResponceSearchBreachesEmail(
                            status=status.HTTP_200_OK,
                            email="",
                            no_founed=True,
                        )

                    else:
                        return ResponceSearchBreachesEmail(
                            status=status.HTTP_200_OK,
                            email =email,
                            breaches=data.get("breaches", [None])[0],
                        )
            except Exception as e:
                    return ResponceSearchBreachesEmail(
                        status= status.HTTP_500_INTERNAL_SERVER_ERROR,
                        email="",
                        error=str(e)
                    )

    def _validate_email(self,email: str) -> bool:
        """
        Проверяет, является ли строка корректным email-адресом.

        Args:
            email: Строка для проверки

        Returns:
            True если email валидный, иначе False
        """
        # Регулярное выражение для проверки email (стандартный RFC 5322)
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not email or not isinstance(email, str):
            return False

        return bool(re.match(pattern, email.strip()))
