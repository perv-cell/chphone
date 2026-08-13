import asyncio
from typing import Optional
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, TimeoutError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine)

from config import get_settings

settings = get_settings()

async_engine = create_async_engine(
    settings.DATABASE_URL.unicode_string(),
    echo=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False
)

class PostgresRepositories:
    """Репозиторий для работы с PostgreSQL"""

    def __init__(self):
        self._engine: AsyncEngine = async_engine
        self._lock = asyncio.Lock()
        self._is_closing: bool = False
        self._session_factory = async_session_factory

    async def get_connection(self) -> AsyncEngine:
        """
        Получить соединение с проверкой живости
        """
        async with self._lock:
            if self._is_closing:
                self._is_closing = False

            if not await self._is_connection_alive():
                await self._reconnect()

            return self._engine

    async def _is_connection_alive(self) -> bool:
        """
        Проверка живости соединения с PostgreSQL
        """
        if self._engine is None:
            return False

        try:
            async with asyncio.timeout(3):
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                    return True

        except asyncio.TimeoutError:
            print(" Таймаут при проверке соединения с БД")
            return False

        except (OperationalError, TimeoutError) as e:
            print(f" Ошибка БД: {e}")
            return False

        except Exception as e:
            print(f"❌ Неожиданная ошибка: {type(e).__name__}: {e}")
            return False

    async def _reconnect(self) -> None:
        """
        Пересоздает engine при проблемах с соединением
        """
        if self._is_closing:
            return

        try:

            if self._engine:
                await self._engine.dispose()
                print(" Старый Engine закрыт")

            self._engine = create_async_engine(
                settings.DATABASE_URL.unicode_string(),
                echo=True,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True
            )

            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False
            )

            print("✅ Engine пересоздан")

        except Exception as e:
            print(f"❌ Ошибка при пересоздании engine: {e}")
            raise

    async def disconnect(self) -> None:
        """
        Принудительное отключение от PostgreSQL
        """
        async with self._lock:
            if self._is_closing:
                return

            self._is_closing = True

            try:
                if self._engine:
                    await self._engine.dispose()
                    print("✅ PostgreSQL connection closed")
            except Exception as e:
                print(f"⚠️ Error closing PostgreSQL: {e}")
            finally:
                self._engine = None
                self._session_factory = None
                self._is_closing = False

    async def get_session(self) -> AsyncSession:
        """
        Получить новую сессию с проверкой соединения
        """
        if self._is_closing:
            raise RuntimeError("PostgreSQL repository is closing")

        await self.get_connection()

        if self._session_factory is None:
            raise RuntimeError("Session factory is not initialized")

        return self._session_factory()

    async def health_check(self) -> dict:
        """
        Дополнительный метод для проверки здоровья (опционально)
        """
        result = {
            "status": "unknown",
            "connected": False,
            "error": None
        }

        try:
            is_alive = await self._is_connection_alive()
            result["connected"] = is_alive

            if is_alive and self._engine:
                pool = self._engine.pool
                result["pool"] = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "overflow": pool.overflow()
                }
                result["status"] = "healthy"
            else:
                result["status"] = "unhealthy"
                result["error"] = "Connection is not alive"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result
