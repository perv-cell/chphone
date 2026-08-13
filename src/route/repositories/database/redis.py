from multiprocessing import Lock
from typing import Optional
from config import get_settings
from route.repositories.models import PhoneNumber, ServiceRegistration
from sqlalchemy import text
from typing import Optional, Any, Dict, List
from schemas.object_search import AnswerProxy ,Protocol
import redis.asyncio as redis
import asyncio
import json

settings = get_settings()

class CommonRepository:
    def __init__(self):
        self._r = None
        self._lock = asyncio.Lock()

    async def get_connection(self):
        async with self._lock:
            # Проверяем, живо ли соединение
            if self._r is None or not await self._is_connection_alive():
                self._r = await self._create_connection()
            return self._r

    async def _is_connection_alive(self):
        if self._r is None:
            return False
        try:
            await self._r.ping()
            return True
        except Exception:
            return False



    async def _create_connection(self):
        return redis.from_url(
            url=settings.DATABASE_REDIS_URL,
            max_connections=20,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=2,
            retry_on_timeout=True
        )

    async def disconnect(self):
        async with self._lock:
            if self._r is None:
                return
            try:
                await self._r.aclose()
                print(" Redis connection closed")
            except redis.ConnectionError as e:
                print(f" Redis connection already closed: {e}")
            except Exception as e:
                print(f"Error closing Redis connection: {e}")
            finally:
                self._r = None

    async def add_proxy(self, key: str, value: str) -> bool:
        """
        Добавляет прокси с nx=True
        Возвращаем True если уже создано
        """
        r = await self.get_connection()
        result = await r.set(
            key,
            value,
            ex=settings.EXP_KEY_PROXY,
            nx=True
        )
        return result is True

    async def get_proxy(self, key: str) -> Optional[str]:
        """Получает прокси по ключу"""
        r = await self.get_connection()
        return await r.get(key)


    async def add_proxies_batch(self, proxies: List[AnswerProxy]) -> List[Dict[str, Any]]:
        """
        Добавляет несколько прокси через pipeline
        Принимает список AnswerProxy
        Возвращает отчет по каждому прокси
        """
        if not proxies:
            return []
        r = await self.get_connection()
        pipeline = r.pipeline()

        for proxy in proxies:
            key = proxy.ip

            value = json.dumps({
                "port": proxy.port,
                "protocol": proxy.protocol.value,
                "hostname": proxy.hostname
            })

            pipeline.set(
                key,
                value,
                ex=settings.EXP_KEY_PROXY,
                nx=True
            )

        results = await pipeline.execute()

        report = []
        for proxy, result in zip(proxies, results):
            report.append({
                "ip": proxy.ip,
                "port": proxy.port,
                "protocol": proxy.protocol.value,
                "hostname": proxy.hostname,
                "success": result is True,
                "created": result is True,
                "already_exists": result is None,
                "result": result
            })

        return report

    async def get_all_proxies(self) -> List[AnswerProxy]:
        """
        Выгружает все прокси из Redis и возвращает список AnswerProxy
        """
        r = await self.get_connection()
        keys = await r.keys("*")

        if not keys:
            return []

        pipeline = r.pipeline()
        for key in keys:
            pipeline.get(key)
        values = await pipeline.execute()

        proxies = []
        for key, value in zip(keys, values):
            if value:
                try:
                    proxy_dict = json.loads(value)
                    proxies.append(AnswerProxy(
                        ip=key,
                        port=proxy_dict["port"],
                        hostname=proxy_dict["hostname"],
                        protocol=Protocol(proxy_dict["protocol"])
                    ))
                except (json.JSONDecodeError, KeyError) as e:
                    print(f" Ошибка парсинга для ключа {key}: {e}")
                    continue

        return proxies
