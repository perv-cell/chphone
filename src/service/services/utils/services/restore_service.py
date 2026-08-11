import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import pickle
import os
import logging
from service.services.utils.services.session_manager import VKSessionManager
from schemas.object_search import RequestSearchRegistration

logger = logging.getLogger("restore_service")


class VKRestoreService:
    """Сервис для работы с API восстановления VK"""

    def __init__(self, session_manager: Optional[VKSessionManager] = None):
        self.session_manager = session_manager or VKSessionManager()

        # Загружаем куки
        if not self.session_manager.load_cookies_from_file(): #type: ignore
            logger.warning("Куки не найдены. Нужна авторизация.")

        self.cookies = self.session_manager.get_cookies() #type: ignore

        # Заголовки (БЕЗ zstd в Accept-Encoding!)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:153.0) Gecko/20100101 Firefox/153.0",
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",  # Убираем br и zstd
            "Referer": "https://id.vk.ru/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://id.vk.ru",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        # Базовые параметры
        self.base_params = {
            "lang": "0",
            "v": "5.83",
            "app_id": "0",
            "device_id": "JBuFiTjz5kamwggP8z2xB",
            "unauth_id": "3326488608",
            "restore_session_id": "1GgQIzceW9oA3N12bDNhb0pIApLHDVdDBZs6cz054Az",
            "history[]": "reset",
            "platform": "vkcom",
            "vkui": "1"
        }

    async def check_phone_registration(self, number_search: RequestSearchRegistration) -> Dict[str, Any]:
        """
        Проверка регистрации номера телефона в VK

        Args:
            number_search: Объект с номером телефона

        Returns:
            Результат проверки
        """
        url = "https://api.vk.ru/method/restore.phoneCheck"

        # Проверяем наличие кук
        if not self.cookies:
            return {
                "success": False,
                "error": "No valid cookies. Please login first.",
                "needs_login": True
            }

        # Формируем данные
        data = self.base_params.copy()
        data["phone"] = number_search.phone # type: ignore

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    data=data,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=30
                ) as response:

                    response_text = await response.text()

                    if response.status != 200:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "raw_response": response_text
                        }

                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "error": "Invalid JSON response",
                            "raw_response": response_text
                        }

                    # Проверяем ошибку сессии
                    if "response" in result:
                        response_data = result["response"]

                        if isinstance(response_data, dict) and "error_code" in response_data:
                            error_code = response_data["error_code"]

                            if error_code == "session_is_not_valid":
                                return {
                                    "success": False,
                                    "error": "Session expired",
                                    "needs_login": True
                                }

                            return {
                                "success": False,
                                "error": f"VK API error: {error_code}",
                                "error_code": error_code
                            }

                        # Успешный ответ
                        is_registered = False
                        if isinstance(response_data, dict):
                            is_registered = response_data.get("registered", False)

                        return {
                            "success": True,
                            "registered": is_registered,
                            "data": response_data,
                            "raw_response": response_text
                        }

                    # Проверяем ошибку в ответе
                    if "error" in result:
                        error_msg = result["error"].get("error_msg", "Unknown error")
                        error_code = result["error"].get("error_code")

                        if "captcha_sid" in result["error"]:
                            return {
                                "success": False,
                                "error": error_msg,
                                "error_code": error_code,
                                "captcha_required": True,
                                "captcha_sid": result["error"]["captcha_sid"],
                                "captcha_img": result["error"].get("captcha_img")
                            }

                        return {
                            "success": False,
                            "error": error_msg,
                            "error_code": error_code,
                            "raw_response": response_text
                        }

                    return {
                        "success": False,
                        "error": "Unknown response format",
                        "raw_response": response_text
                    }

            except aiohttp.ClientError as e:
                return {
                    "success": False,
                    "error": f"Network error: {str(e)}"
                }
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "error": "Request timeout"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}"
                }
