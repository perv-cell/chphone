from fastapi import HTTPException, status
from fastapi.param_functions import Depends
from repositories.number_repo import NumberRepository, get_db
from schemas.number import NumberSearch, NumberResponse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from repositories.models import ServiceType
from typing import Dict, Optional, Any, List
import datetime
from repositories.models import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.number import NumberSearch
import logging
import json
import aiohttp

logger = logging.getLogger("service.number")

class NumberService:
    """
    Сервис для работы с номерами телефонов и проверки их регистрации в соцсетях
    """

    def __init__(self, repo: NumberRepository):
        self.repo = repo
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Список поддерживаемых сервисов с их проверялками
        self.service_checkers = {
            ServiceType.VKONTAKTE: self._check_vkontakte,
            ServiceType.ODNOKLASSNIKI: self._check_odnoklassniki,
            ServiceType.TELEGRAM: self._check_telegram,
            ServiceType.WHATSAPP: self._check_whatsapp,
            ServiceType.VIBER: self._check_viber,
            ServiceType.INSTAGRAM: self._check_instagram,
            ServiceType.FACEBOOK: self._check_facebook,
            ServiceType.TIKTOK: self._check_tiktok,
            ServiceType.TWITTER: self._check_twitter,
            ServiceType.SIGNAL: self._check_signal,
        }

    # ============= ОСНОВНЫЕ ФУНКЦИИ =============

    async def check_phone_registration(self, number_search:NumberSearch):
        url = "https://api.vk.ru/method/restore.phoneCheck"

        payload = 'lang=0&v=5.83&app_id=0&device_id=JBuFiTjz5kamwggP8z2xB&unauth_id=3326488608&restore_session_id=1GgQIzceW9oA3N12bDNhb0pIApLHDVdDBZs6cz054Az&history%5B%5D=reset&platform=vkcom&phone=%2B79229018613&vkui=1'
        headers = {
          'Host': 'api.vk.ru',
          'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:153.0) Gecko/20100101 Firefox/153.0',
          'Accept': '*/*',
          'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Referer': 'https://id.vk.ru/',
          'Content-Type': 'application/x-www-form-urlencoded',
          'Origin': 'https://id.vk.ru',
          'Connection': 'keep-alive',
          'Cookie': 'remixlang=0; remixstlid=9050071956940505016_j1TAfZRvQB13HoE1DK4OptlIgEByv5BRGkSuFMQzVsz; remixuas=M2Q3MzFjNTIzMjM4ZjVjYzg5YWIwMTEw; remixstid=1104520118_bggs2j0OS68ApJ3rnwJcgqzgdxDdzriWDThm16Uh0zL; remixuacck=e6c9eb93c151384944; remixsuc=2%3A; remixnttpid=vk1.a.oIhn8mJfOMeOWIoELOLJehs7u0W_Idmg_YR06rDBY0MkYnUHa4_-15uA4ohGix5E2sh2SxMQXHdc1ry4-xubGTK_wrH8v_hxeTcMEA97JvB6XCOh8V6Q6hEo8lHI_u_5-ubCSb8TMHOTSPgrK3P7w9FIbXkF4iwPAXf3LFLtBUTPVwlRmeWq65J4sBNwmLjE; remixua=191%7C-1%7C333%7C3201899776; remixscreen_width=1600; remixscreen_height=900; remixscreen_dpr=1.2; remixscreen_depth=24; remixscreen_winzoom=1; remixdark_color_scheme=0; remixcolor_scheme_mode=auto; remixdt=0; remixsf=1; vkm_one_column_mode=1; remixseenads=2; remixscreen_orient=1; remixgp=9a140e9a523a56be6aacb1b9bc40c3ad; httoken=EfrR03fgFzLz9QFmZADcCOGd14VoYxveIGOOjqDeyU2zlp4xppbJay1IederpYdi_iULoGkvSImGzLIHXyi_Z0A4Vw6CInA_Lj8jD6aDDjrbbA3ZPBXJhTMDdTanPzC-3B0; remixlgck=4aee85adbf56404f4c; tmr_lvid=cd7833d252b84c7caf4b5e74dba04921; tmr_lvidTS=1785915853739; domain_sid=JTvHyvnkU7hLscmAwo8wr%3A1785915854573; remixnreg_sid=bb8f5c26a86f84f07a6a62e03ecf99a7',
          'Sec-Fetch-Dest': 'empty',
          'Sec-Fetch-Mode': 'cors',
          'Sec-Fetch-Site': 'same-site',
          'host': 'api.vk.ru'
        }
        cookies = {
            "remixlang": "0",
            "remixstlid": "9050071956940505016_j1TAfZRvQB13HoE1DK4OptlIgEByv5BRGkSuFMQzVsz",
            "remixuas": "M2Q3MzFjNTIzMjM4ZjVjYzg5YWIwMTEw",
            "remixstid": "1104520118_bggs2j0OS68ApJ3rnwJcgqzgdxDdzriWDThm16Uh0zL",
            "remixuacck": "e6c9eb93c151384944",
            "remixsuc": "2%3A",
            "remixnttpid": "vk1.a.oIhn8mJfOMeOWIoELOLJehs7u0W_Idmg_YR06rDBY0MkYnUHa4_-15uA4ohGix5E2sh2SxMQXHdc1ry4-xubGTK_wrH8v_hxeTcMEA97JvB6XCOh8V6Q6hEo8lHI_u_5-ubCSb8TMHOTSPgrK3P7w9FIbXkF4iwPAXf3LFLtBUTPVwlRmeWq65J4sBNwmLjE",
            "remixua": "191%7C-1%7C333%7C3201899776",
            "remixscreen_width": "1600",
            "remixscreen_height": "900",
            "remixscreen_dpr": "1.2",
            "remixscreen_depth": "24",
            "remixscreen_winzoom": "1",
            "remixdark_color_scheme": "0",
            "remixcolor_scheme_mode": "auto",
            "remixdt": "0",
            "remixsf": "1",
            "vkm_one_column_mode": "1",
            "remixseenads": "2",
            "remixscreen_orient": "1",
            "remixgp": "9a140e9a523a56be6aacb1b9bc40c3ad",
            "httoken": "EfrR03fgFzLz9QFmZADcCOGd14VoYxveIGOOjqDeyU2zlp4xppbJay1IederpYdi_iULoGkvSImGzLIHXyi_Z0A4Vw6CInA_Lj8jD6aDDjrbbA3ZPBXJhTMDdTanPzC-3B0",
            "remixlgck": "4aee85adbf56404f4c",
            "tmr_lvid": "cd7833d252b84c7caf4b5e74dba04921",
            "tmr_lvidTS": "1785915853739",
            "domain_sid": "JTvHyvnkU7hLscmAwo8wr%3A1785915854573",
            "remixnreg_sid": "bb8f5c26a86f84f07a6a62e03ecf99a7"
        }
        data = {
                "lang": "0",
                "v": "5.83",
                "app_id": "0",
                "device_id": "JBuFiTjz5kamwggP8z2xB",
                "unauth_id": "3326488608",
                "restore_session_id": "1GgQIzceW9oA3N12bDNhb0pIApLHDVdDBZs6cz054Az",
                "history[]": "reset",
                "platform": "vkcom",
                "phone": "+79229018613",
                "vkui": "1"
            }
        async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        url,
                        data=data,
                        headers=headers,
                        cookies=cookies
                    ) as response:

                        # Получаем ответ
                        response_text = await response.text()

                        # Проверяем статус
                        if response.status != 200:
                            return {
                                "success": False,
                                "error": f"HTTP {response.status}",
                                "raw_response": response_text
                            }

                        # Парсим JSON
                        try:
                            result = json.loads(response_text)
                        except json.JSONDecodeError:
                            return {
                                "success": False,
                                "error": "Invalid JSON response",
                                "raw_response": response_text
                            }

                        # Проверяем наличие ошибки в ответе API
                        if "error" in result:
                            error_msg = result["error"].get("error_msg", "Unknown error")
                            error_code = result["error"].get("error_code")

                            # Капча
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

                        # Успешный ответ
                        return {
                            "success": True,
                            "data": result.get("response", {}),
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

    async def check_phone_all_services(
        self,
        phone: str,
        services: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Проверить номер во всех поддерживаемых сервисах

        Args:
            phone: Номер телефона
            services: Список сервисов для проверки (если None - все)

        Returns:
            Dict с результатами проверки
        """
        # 1. Нормализуем номер
        normalized_phone = self._normalize_phone(phone)

        # 2. Проверяем или создаем запись в БД
        phone_record = await self._get_or_create_phone(normalized_phone)

        # 3. Определяем какие сервисы проверять
        services_to_check = services or list(self.service_checkers.keys())

        # 4. Проверяем все сервисы параллельно
        results = {}
        check_tasks = []

        for service in services_to_check:
            if service in self.service_checkers:
                # Проверяем, нужно ли обновить (старше 24 часов)
                need_update = await self._need_update(phone_record.id, service)
                if need_update:
                    task = self._check_service(phone_record, service)
                    check_tasks.append(task)
                else:
                    # Берем из БД
                    registration = await self._get_registration(phone_record.id, service)
                    results[service] = registration.to_dict() if registration else None

        # Запускаем проверки параллельно
        if check_tasks:
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
            for result in check_results:
                if isinstance(result, dict):
                    results[result['service']] = result

        # 5. Формируем ответ
        return {
            "phone": normalized_phone,
            "country_code": phone_record.country_code,
            "total_services_checked": len(results),
            "registered_count": sum(1 for r in results.values() if r and r.get('is_registered')),
            "results": results,
            "checked_at": datetime.utcnow().isoformat()
        }

    async def check_single_service(
        self,
        phone: str,
        service: str
    ) -> Dict[str, Any]:
        """
        Проверить номер в конкретном сервисе

        Args:
            phone: Номер телефона
            service: Название сервиса

        Returns:
            Dict с результатами проверки
        """
        normalized_phone = self._normalize_phone(phone)
        phone_record = await self._get_or_create_phone(normalized_phone)

        if service not in self.service_checkers:
            raise ValueError(f"Unsupported service: {service}")

        return await self._check_service(phone_record, service)

    async def check_phones_batch(
        self,
        phones: List[str],
        services: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Пакетная проверка нескольких номеров

        Args:
            phones: Список номеров телефонов
            services: Список сервисов для проверки

        Returns:
            Dict с результатами для каждого номера
        """
        results = {}
        tasks = []

        for phone in phones:
            task = self.check_phone_all_services(phone, services)
            tasks.append(task)

        # Запускаем проверки параллельно
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        for phone, result in zip(phones, check_results):
            if isinstance(result, Exception):
                results[phone] = {"error": str(result)}
            else:
                results[phone] = result

        return {
            "total": len(phones),
            "results": results
        }

    # ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

    async def _check_service(
        self,
        phone_record: PhoneNumber,
        service: str,
        db: AsyncSession = Depends(get_db)
    ) -> Dict[str, Any]:
        """Проверить номер в конкретном сервисе и сохранить результат"""
        try:
            # Вызываем конкретную проверялку
            checker = self.service_checkers.get(service)
            if not checker:
                raise ValueError(f"Unsupported service: {service}")

            # Проверяем
            result = await checker(phone_record.phone)

            # Сохраняем результат
            registration = await self.repo.create_or_update_registration(
                phone_id=phone_record.id,
                service=service,
                is_registered=result['is_registered'],
                db= db,
                metadata=result.get('metadata', {}),
                profile_url=result.get('profile_url'),
                username=result.get('username'),
                avatar_url=result.get('avatar_url'),

            )

            return {
                "service": service,
                "is_registered": result['is_registered'],
                "metadata": result.get('metadata', {}),
                "profile_url": result.get('profile_url'),
                "username": result.get('username'),
                "avatar_url": result.get('avatar_url'),
                "checked_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error checking {service} for {phone_record.phone}: {e}")
            return {
                "service": service,
                "is_registered": False,
                "error": str(e)
            }

    async def _get_or_create_phone(self, phone: str, db: AsyncSession = Depends(get_db)) -> PhoneNumber:
        """Получить или создать запись номера телефона"""


        phone_record = await self.repo.get_by_phone(phone,db)
        if not phone_record:
            # Определяем страну
            country_code = self._detect_country(phone)
            phone_record = await self.repo.create_phone(phone, country_code,db )
        return phone_record

    async def _need_update(self, phone_id: int, service: str, db: AsyncSession = Depends(get_db)) -> bool:
        """Проверить, нужно ли обновить данные (старше 24 часов)"""
        registration = await self.repo.get_registration(phone_id, service,db)
        if not registration:
            return True

        # Обновляем раз в сутки
        age = (datetime.utcnow() - registration.last_updated).total_seconds()
        return age > 86400  # 24 часа

    async def _get_registration(self, phone_id: int, service: str, db: AsyncSession = Depends(get_db)):
        """Получить регистрацию из БД"""
        return await self.repo.get_registration(phone_id, service, db)

    # ============= ФУНКЦИИ-ПРОВЕРЯЛКИ =============

    async def _check_vkontakte(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в VKontakte"""
        try:
            # Эмуляция API запроса
            # В реальности здесь был бы HTTP запрос к VK API
            # Например: https://api.vk.com/method/users.get?phone=...

            # Для примера - имитация
            is_registered = await self._mock_api_call("vkontakte", phone)

            if is_registered:
                return {
                    "is_registered": True,
                    "username": f"user_{phone[-4:]}",
                    "profile_url": f"https://vk.com/id{phone[-6:]}",
                    "metadata": {
                        "verified": True,
                        "public": True
                    }
                }
            else:
                return {
                    "is_registered": False,
                    "metadata": {"not_found": True}
                }
        except Exception as e:
            logger.error(f"VK check failed for {phone}: {e}")
            return {"is_registered": False, "error": str(e)}

    async def _check_odnoklassniki(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в Одноклассниках"""
        try:
            is_registered = await self._mock_api_call("odnoklassniki", phone)

            if is_registered:
                return {
                    "is_registered": True,
                    "username": f"ok_user_{phone[-4:]}",
                    "profile_url": f"https://ok.ru/profile/{phone[-6:]}",
                    "metadata": {
                        "public": True,
                        "age_verified": False
                    }
                }
            return {"is_registered": False}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_telegram(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в Telegram"""
        try:
            # В реальности: использовать Telethon или requests к Telegram API
            is_registered = await self._mock_api_call("telegram", phone)

            if is_registered:
                return {
                    "is_registered": True,
                    "username": f"tg_user_{phone[-4:]}",
                    "profile_url": f"https://t.me/user_{phone[-4:]}",
                    "metadata": {
                        "has_photo": True,
                        "is_bot": False
                    }
                }
            return {"is_registered": False}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_whatsapp(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в WhatsApp"""
        try:
            # В реальности: использовать WhatsApp Business API
            is_registered = await self._mock_api_call("whatsapp", phone)

            return {
                "is_registered": is_registered,
                "metadata": {
                    "has_whatsapp": is_registered,
                    "business_account": False
                }
            }
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_viber(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в Viber"""
        try:
            is_registered = await self._mock_api_call("viber", phone)
            return {"is_registered": is_registered}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_instagram(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в Instagram"""
        try:
            is_registered = await self._mock_api_call("instagram", phone)

            if is_registered:
                return {
                    "is_registered": True,
                    "profile_url": f"https://instagram.com/user_{phone[-4:]}",
                    "metadata": {
                        "is_private": False,
                        "has_stories": True
                    }
                }
            return {"is_registered": False}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_facebook(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в Facebook"""
        try:
            is_registered = await self._mock_api_call("facebook", phone)

            if is_registered:
                return {
                    "is_registered": True,
                    "profile_url": f"https://facebook.com/profile.php?id={phone[-6:]}",
                    "metadata": {
                        "is_public": True
                    }
                }
            return {"is_registered": False}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_tiktok(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в TikTok"""
        try:
            is_registered = await self._mock_api_call("tiktok", phone)
            return {"is_registered": is_registered}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_twitter(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в Twitter/X"""
        try:
            is_registered = await self._mock_api_call("twitter", phone)
            return {"is_registered": is_registered}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    async def _check_signal(self, phone: str) -> Dict[str, Any]:
        """Проверка регистрации в Signal"""
        try:
            is_registered = await self._mock_api_call("signal", phone)
            return {"is_registered": is_registered}
        except Exception as e:
            return {"is_registered": False, "error": str(e)}

    # ============= УТИЛИТЫ =============

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Нормализация номера телефона"""
        # Удаляем все не-цифры
        digits = ''.join(filter(str.isdigit, phone))

        # Если номер начинается с 8, заменяем на +7 (Россия)
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]

        # Добавляем + если нет
        if not phone.startswith('+'):
            phone = '+' + digits

        return phone

    @staticmethod
    def _detect_country(phone: str) -> str:
        """Определение страны по телефонному коду"""
        # Простая эмуляция
        country_codes = {
            '7': 'RU',
            '1': 'US',
            '44': 'GB',
            '49': 'DE',
            '86': 'CN',
            '81': 'JP',
        }

        # Убираем +
        phone_digits = phone.lstrip('+')

        # Проверяем коды
        for code, country in country_codes.items():
            if phone_digits.startswith(code):
                return country

        return 'UNKNOWN'

    async def _mock_api_call(self, service: str, phone: str) -> bool:
        """Имитация API вызова для демонстрации"""
        # В реальном коде здесь были бы реальные HTTP запросы
        await asyncio.sleep(0.1)  # Имитация задержки

        # Имитация результатов на основе номера
        # Для демонстрации - проверяем последнюю цифру
        last_digit = int(phone[-1]) if phone[-1].isdigit() else 0
        return last_digit % 2 == 0  # Четные - зарегистрированы
