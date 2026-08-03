from typing import Optional
from datetime import datetime
from schemas.number import NumberCreate, NumberUpdate

# Имитация БД (в реальном проекте — SQLAlchemy или raw SQL)
class NumberRepository:
    def __init__(self):
        self._storage = {}  # {id: {"id": id, "value": ..., "description": ..., "created_at": ..., "updated_at": ...}}
        self._counter = 1

    async def create(self, data: NumberCreate) -> dict:
        """Создать новую запись"""
        item = {
            "id": self._counter,
            "value": data.value,
            "description": data.description,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        self._storage[self._counter] = item
        self._counter += 1
        return item

    async def get_by_id(self, item_id: int) -> Optional[dict]:
        """Получить запись по ID"""
        return self._storage.get(item_id)

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[dict]:
        """Получить список с пагинацией"""
        items = list(self._storage.values())
        return items[skip:skip + limit]

    async def update(self, item_id: int, data: NumberUpdate) -> Optional[dict]:
        """Обновить запись"""
        item = self._storage.get(item_id)
        if not item:
            return None
        
        if data.value is not None:
            item["value"] = data.value
        if data.description is not None:
            item["description"] = data.description
        item["updated_at"] = datetime.now()
        return item

    async def delete(self, item_id: int) -> bool:
        """Удалить запись"""
        if item_id in self._storage:
            del self._storage[item_id]
            return True
        return False

    async def count(self) -> int:
        """Общее количество записей"""
        return len(self._storage)