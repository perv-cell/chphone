import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from enum import Enum
from holehe.core import import_submodules, get_functions
from route.repositories.database.postgres import PostgresRepositories
from route.repositories.database.redis import CommonRepository

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckerService:
    """Класс для проверки здоровья всех компонентов"""

    def __init__(self,
        repoPostgr: PostgresRepositories,
        repoRedis: CommonRepository
    ):
        self.repoPostgr = repoPostgr
        self.repoRedis= repoRedis
        self.holehe_timeout = 30
        self.http_timeout = 5
        self.holehe_modules_limit = 20

    async def check_healthy(self) -> Dict[str, Any]:
        """
        Полная проверка здоровья системы
        """
        errors = []
        warnings = []
        components = {}

        redis_status = await self._check_redis()
        components["redis"] = redis_status
        if not redis_status["healthy"]:
            errors.append(redis_status["error"])

        postgres_status = await self._check_postgres()
        components["postgres"] = postgres_status
        if not postgres_status["healthy"]:
            errors.append(postgres_status["error"])

        openserp_status = await self._check_openserp()
        components["openserp"] = openserp_status
        if not openserp_status["healthy"]:
            errors.append(openserp_status["error"])
        elif openserp_status.get("warning"):
            warnings.append(openserp_status["warning"])

        if all(c["healthy"] for c in components.values() if c["healthy"] is not None):
            holehe_status = await self._check_holehe()
            components["holehe"] = holehe_status
            if not holehe_status["healthy"]:
                warnings.append(holehe_status.get("error", "Holehe check failed"))
        else:
            components["holehe"] = {
                "healthy": None,
                "error": "Skipped due to other component failures",
                "modules_checked": 0,
                "modules_found": 0
            }

        if errors:
            status = HealthStatus.UNHEALTHY
            status_code = 503
        elif warnings:
            status = HealthStatus.DEGRADED
            status_code = 200
        else:
            status = HealthStatus.HEALTHY
            status_code = 200

        return {
            "status": status,
            "status_code": status_code,
            "components": components,
            "errors": errors,
            "warnings": warnings,
            "timestamp": asyncio.get_event_loop().time()
        }


    async def _check_redis(self) -> Dict[str, Any]:
        """Проверка Redis"""
        result = {"healthy": False, "error": None}

        try:
            redis = self.repoRedis
            is_alive = await redis._is_connection_alive()
            if not is_alive:
                await redis.get_connection()
                is_alive = await redis._is_connection_alive()
                await redis.disconnect()

            if is_alive:
                result["healthy"] = True
            else:
                result["error"] = "The connection to the Redis repository was lost."

        except Exception as e:
            result["error"] = f"Redis check failed: {str(e)}"

        return result

    async def _check_postgres(self) -> Dict[str, Any]:
        """Проверка PostgreSQL"""
        result = {"healthy": False, "error": None}

        try:
            postgres = self.repoPostgr
            is_alive = await postgres._is_connection_alive()
            if not is_alive:
                await postgres.get_connection()
                is_alive = await postgres._is_connection_alive()
                await postgres.disconnect()

            if is_alive:
                result["healthy"] = True
            else:
                result["error"] = "The connection to the Postgres repository was lost."

        except Exception as e:
            result["error"] = f"PostgreSQL check failed: {str(e)}"

        return result

    async def _check_openserp(self) -> Dict[str, Any]:
        """Проверка OpenSerp"""
        result = {
            "healthy": False,
            "error": None,
            "warning": None,
            "engines": None
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.http_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("http://127.0.0.1:7000/health") as response:
                    if response.status != 200:
                        result["error"] = f"OpenSerp returned HTTP {response.status}"
                        return result

                    data = await response.json()
                    engines = data.get("engines", {})

                    if not engines:
                        result["error"] = "No engines available for search queries."
                        return result

                    working_engines = sum(
                        1 for engine in engines
                        if engine.get("initialized", False)
                    )

                    result["engines"] = {
                        "total": len(engines),
                        "working": working_engines
                    }

                    if working_engines == 0:
                        result["error"] = "No working search engines available."
                    elif working_engines < 3:
                        result["warning"] = f"Only {working_engines} search engines available (recommended: 3+)"
                        result["healthy"] = True
                    else:
                        result["healthy"] = True

        except asyncio.TimeoutError:
            result["error"] = "OpenSerp is not responding (Connection timeout)."
        except aiohttp.ClientConnectionError:
            result["error"] = "OpenSerp connection error."
        except Exception as e:
            result["error"] = f"OpenSerp check failed: {str(e)}"

        return result

    async def _check_holehe(self) -> Dict[str, Any]:
        """Проверка holehe модулей"""
        result = {
            "healthy": True,
            "error": None,
            "modules_found": 0,
            "modules_checked": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "sample_results": []  # Показываем пару примеров
        }

        try:
            all_modules = import_submodules("holehe.modules")
            check_functions = get_functions(all_modules)

            result["modules_found"] = len(check_functions)

            modules_to_check = check_functions[:self.holehe_modules_limit]
            result["modules_checked"] = len(modules_to_check)

            test_email = "test@example.com"
            results = []

            timeout = aiohttp.ClientTimeout(total=self.holehe_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as client:
                tasks = []

                for func in modules_to_check:
                    task = asyncio.create_task(
                        self._run_holehe_check(func, test_email, client, results)
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)

            successful = [r for r in results if r.get("success", False)]
            failed = [r for r in results if not r.get("success", False)]

            result["successful_checks"] = len(successful)
            result["failed_checks"] = len(failed)
            result["sample_results"] = successful[:5]

            if len(failed) > len(results) * 0.9:  # >70% ошибок
                result["healthy"] = False
                result["error"] = f"Too many failed holehe checks: {len(failed)}/{len(results)}"
            elif len(failed) > len(results) * 0.4:  # >40% ошибок
                result["warning"] = f"High failure rate in holehe checks: {len(failed)}/{len(results)}"

        except ImportError as e:
            result["healthy"] = False
            result["error"] = f"Failed to import holehe modules: {str(e)}"
        except Exception as e:
            result["healthy"] = False
            result["error"] = f"Holehe check failed: {str(e)}"

        return result

    async def _run_holehe_check(
        self,
        func,
        email: str,
        client: aiohttp.ClientSession,
        results: List[Dict]
    ) -> None:
        """
        Обертка для выполнения одного holehe модуля
        """
        module_name = getattr(func, '__name__', 'unknown')

        try:
            # Устанавливаем небольшой таймаут для каждого модуля
            async with asyncio.timeout(self.http_timeout):
                await func(email, client, results)

            # Отмечаем модуль как успешный
            results.append({
                "name": module_name,
                "success": True,
                "error": None
            })

        except asyncio.TimeoutError:
            results.append({
                "name": module_name,
                "success": False,
                "error": "Timeout"
            })
        except Exception as e:
            results.append({
                "name": module_name,
                "success": False,
                "error": str(e)
            })

    async def quick_check(self) -> bool:
        """
        Быстрая проверка: только критичные компоненты
        """
        try:
            redis_ok = await self._check_redis()
            postgres_ok = await self._check_postgres()
            openserp_ok = await self._check_openserp()

            return all([
                redis_ok["healthy"],
                postgres_ok["healthy"],
                openserp_ok["healthy"]
            ])
        except Exception:
            return False
