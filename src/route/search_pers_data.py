from fastapi import APIRouter, Depends
from schemas.object_search import RequestSearchBreachesEmail, ResponceSearchBreachesEmail, ResultSearchEngine, \
ResponsResultsSearchEngine, RequestSearchEngine
from service.services.common import CommonService
from service.services.email import EmailService
from service.services.number import NumberService
from service.depends import get_common_service,get_email_service
import re

router = APIRouter(prefix="/search")

@router.post("/leakagel-email/", response_model=ResponceSearchBreachesEmail, status_code=200,tags=["Checking-leak"])
async def search_resources_leakage_email(
    data: RequestSearchBreachesEmail,
    service: EmailService = Depends(get_email_service)
):

    if not is_valid_email(data.email):
        return ResponceSearchBreachesEmail(
            email="",
            status=400,
            error="Некорректный email"
        )
    res1  =  await service.search_resources_leakage_email(data)
    return  res1


@router.post("/engine/personal_date/", tags=["Search engine"])
async def check_data_in_search_engine(
    data: RequestSearchEngine,
    service: CommonService = Depends(get_common_service)
):
    results =  await service.search_personal_data_in_search_engine(data)

    return results



#  были проблемы с импортами поэтому здесь
def is_valid_email(email: str) -> bool:
    """Проверяет email на валидность"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
