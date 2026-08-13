from fastapi import APIRouter, Depends
from schemas.object_search import RequestProxy, ResponseProxy, ResponseHealthy
from service.services.common import CommonService
from service.services.email import EmailService
from service.services.healthy import HealthCheckerService
from service.depends import get_common_service, get_health_checker_service
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/free-proxy/", response_model=ResponseProxy, tags=["Proxy"],status_code=200)
async def check_free_proxy(
    data: RequestProxy,
    service: CommonService = Depends(get_common_service)
):
    count_proxy:int = data.count #type: ignore
    if count_proxy == 0:
        count_proxy = 5
    proxys = await service.checking_work_proxy()
    if len(proxys) < count_proxy:
        count_proxy = len(proxys)-1
    return ResponseProxy(
        proxys=proxys[:count_proxy]
    )

@router.post("/healthy", response_model=ResponseHealthy, tags=["Healthy"], status_code=200)
async def check_healthy_service(
    service: HealthCheckerService = Depends(get_health_checker_service)
):
    res = await service.check_healthy()
    return ResponseHealthy(
        status=res.get("status", "unrecognized"),
        status_code=res.get("status_code", "unrecognized"),
        components= res.get("components", "unrecognized"),
        errors=res.get("errors", "unrecognized"),
        warnings= res.get("warnings", "unrecognized"),
        timestamp= res.get("timestamp", "unrecognized"),
    )
