from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# Схема для создания (POST)
class NumberCreate(BaseModel):
    value: int = Field(..., ge=0, description="Число должно быть >= 0")
    description: Optional[str] = Field(None, max_length=100)

# Схема для обновления (PUT/PATCH)
class NumberUpdate(BaseModel):
    value: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=100)

# Схема для ответа (GET) — включает ID и даты
class NumberResponse(BaseModel):
    id: int
    value: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Для работы с ORM (SQLAlchemy) — говорим Pydantic принимать объекты БД
    model_config = ConfigDict(from_attributes=True)

# Схема для пагинированного ответа
class NumberListResponse(BaseModel):
    items: list[NumberResponse]
    total: int
    page: int
    size: int