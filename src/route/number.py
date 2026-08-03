from fastapi import APIRouter, Depends, Query
from schemas.number import NumberCreate, NumberUpdate, NumberResponse, NumberListResponse
from service.number import NumberService
from service.depends import get_number_service

router = APIRouter(prefix="/numbers", tags=["numbers"])

@router.post("/", response_model=NumberResponse, status_code=201)
async def create_number(
    data: NumberCreate,
    service: NumberService = Depends(get_number_service)
):
    """Создать новое число"""
    return await service.create_number(data)

@router.get("/{item_id}", response_model=NumberResponse)
async def get_number(
    item_id: int,
    service: NumberService = Depends(get_number_service)
):
    """Получить число по ID"""
    return await service.get_number(item_id)

@router.get("/", response_model=NumberListResponse)
async def get_numbers(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    service: NumberService = Depends(get_number_service)
):
    """Получить список чисел с пагинацией"""
    return await service.get_numbers(page=page, size=size)

@router.put("/{item_id}", response_model=NumberResponse)
async def update_number(
    item_id: int,
    data: NumberUpdate,
    service: NumberService = Depends(get_number_service)
):
    """Обновить число"""
    return await service.update_number(item_id, data)

@router.delete("/{item_id}", status_code=204)
async def delete_number(
    item_id: int,
    service: NumberService = Depends(get_number_service)
):
    """Удалить число"""
    await service.delete_number(item_id)