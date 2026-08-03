from fastapi import HTTPException, status
from repositories.number_repo import NumberRepository
from schemas.number import NumberCreate, NumberUpdate, NumberResponse, NumberListResponse

class NumberService:
    def __init__(self, repo: NumberRepository):
        self.repo = repo

    async def create_number(self, data: NumberCreate) -> NumberResponse:
        """Создать число с проверкой дубликатов (пример бизнес-логики)"""
        # Пример бизнес-правила: не создаем число, если оно уже есть
        all_items = await self.repo.get_all(limit=1000)
        if any(item["value"] == data.value for item in all_items):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Number {data.value} already exists"
            )
        
        created = await self.repo.create(data)
        return NumberResponse(**created)

    async def get_number(self, item_id: int) -> NumberResponse:
        """Получить число по ID"""
        item = await self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Number with id {item_id} not found"
            )
        return NumberResponse(**item)

    async def get_numbers(self, page: int = 1, size: int = 10) -> NumberListResponse:
        """Получить список с пагинацией"""
        skip = (page - 1) * size
        items = await self.repo.get_all(skip=skip, limit=size)
        total = await self.repo.count()
        
        return NumberListResponse(
            items=[NumberResponse(**item) for item in items],
            total=total,
            page=page,
            size=size
        )

    async def update_number(self, item_id: int, data: NumberUpdate) -> NumberResponse:
        """Обновить число"""
        updated = await self.repo.update(item_id, data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Number with id {item_id} not found"
            )
        return NumberResponse(**updated)

    async def delete_number(self, item_id: int) -> None:
        """Удалить число"""
        deleted = await self.repo.delete(item_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Number with id {item_id} not found"
            )