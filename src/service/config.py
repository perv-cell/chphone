from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, field_validator
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Настройки приложения."""
    
    APP_NAME: str = Field(default="Number API", description="Название приложения")
    APP_VERSION: str = Field(default="1.0.0", description="Версия API")
    DEBUG: bool = Field(default=False, description="Режим отладки")
    ENVIRONMENT: str = Field(default="development", description="Окружение: development/staging/production")
    
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+psycopg2://postgres:password@localhost:5432/search_data",
        description="URL подключения к PostgreSQL"
    )
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=100, description="Размер пула соединений")
    DB_ECHO: bool = Field(default=False, description="Логировать SQL-запросы")
    
    SECRET_KEY: str = Field(..., description="Секретный ключ для JWT", min_length=32)
    ALGORITHM: str = Field(default="HS256", description="Алгоритм шифрования JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, description="Время жизни токена (минуты)")
    
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Разрешенные CORS-источники"
    )
    
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Максимум запросов")
    RATE_LIMIT_PERIOD: int = Field(default=60, description="Период (секунды)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True 
        extra = "ignore"  
        
        json_loads = lambda x: x  

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        """Проверяем, что URL БД валидный."""
        if isinstance(v, str):
            if not v.startswith(("postgresql", "postgres")):
                raise ValueError("Only PostgreSQL is supported")
        return v
    
    @field_validator("ENVIRONMENT", mode="after")
    @classmethod
    def validate_environment(cls, v):
        """Проверяем, что окружение корректное."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

@lru_cache()
def get_settings() -> Settings:
    """Возвращает объект настроек (синглтон)."""
    return Settings()