from fastapi import APIRouter, Depends
from schemas.object_search import RequestSearchRegistration, ResponseSearchRegistration, SuccessSearchRegistration,DetailsRegistration,SearchMethod
from service.services.number import NumberService
from service.services.email import EmailService
from service.services.common import CommonService
from service.depends import get_number_service, get_email_service, get_common_service
import logging

router = APIRouter(prefix="/registration", tags=["Checking-reg"])

logger = logging.getLogger(__name__)


@router.post("/number/", response_model=ResponseSearchRegistration, status_code=200)
async def check_registration_number(
    data: RequestSearchRegistration,
    service: NumberService = Depends(get_number_service,use_cache=True),
    service_proxy: CommonService = Depends(get_common_service,use_cache=True),
):
    count_sites = data.count_site
    depth_search = data.depth_search
    type_search = data.type_search
    result = {}
    res_check_parser_vk = {}
    cheking_site = []
    details = None
    registered = False
    undefined = True

    proxys = await service_proxy.get_works_proxy()
    if proxys == {}:
        logger.info("запрос будет осуществлен без прокси")

    if depth_search == True:
        type_search = SearchMethod.HYBRID

    cheking_site.append("https://vk.ru/")
    if type_search in (SearchMethod.SCRAPING, SearchMethod.HYBRID):
        res_check_parser_vk = await service.check_phone_registration(data.object_search, proxys)
        vk_registered = res_check_parser_vk.get("registered", False)
        if vk_registered:
            result["https://vk.ru/"] = SuccessSearchRegistration(
                domain="https://vk.ru/",
                recovery_email=None,
                phone=data.object_search,
                exists=True,
            )

    registered = len(result) > 0

    undefined = not registered and not res_check_parser_vk.get("registered", False)

    if data.details:
        details = DetailsRegistration(
            cheking_sites=cheking_site,
            search_type=data.type_search
        )

    """if result:
        if len(result) < count_sites:
            count_sites = len(result)

        result = dict(list(result.items())[:count_sites])"""

    return ResponseSearchRegistration(
        success=True,
        search_object=data.object_search,
        sites=result,
        total_found=len(result),
        error=None,
        undefined=undefined,
        registered=registered,
        details=details,
    )


@router.post("/email/", response_model=ResponseSearchRegistration, status_code=200)
async def check_registration_email(
    data: RequestSearchRegistration,
    service: EmailService = Depends(get_email_service,use_cache=True),
    service_proxy: CommonService = Depends(get_common_service,use_cache=True),
):
    count_sites = data.count_site
    depth_search = data.depth_search
    type_search = data.type_search
    result = {}
    res_check_parser_vk = {}
    cheking_site = []
    details = None
    registered = False
    undefined = True

    if depth_search == True:
        type_search = SearchMethod.HYBRID

    proxys = await service_proxy.get_works_proxy()
    if proxys == {}:
        logger.info("запрос будет осуществлен без прокси")


    if type_search in (SearchMethod.SCRAPING, SearchMethod.HYBRID):
        res_check_parser_vk = await service.check_email_registration(data.object_search, proxys)
        vk_registered = res_check_parser_vk.get("registered", False)
        cheking_site.append("https://vk.ru/")
        if vk_registered:
            result["https://vk.ru/"] = SuccessSearchRegistration(
                domain="https://vk.ru/",
                recovery_email=data.object_search,
                phone=None,
                exists=True
            )

    if type_search in (SearchMethod.PASSIVE, SearchMethod.HYBRID):
        finally_answer = await service.check_registration_email_sites_external_source(data,proxys)

        sites = finally_answer.get("find_result", [])
        cheking_site = finally_answer.get("cheking_site", [])

        for site in sites:
            site_key = site.get("site", "unknown")
            result[site_key] = SuccessSearchRegistration(
                domain=site.get("domain", "unknown"),
                recovery_email=site.get("recovery_email"),
                phone=site.get("phone"),
                exists=site.get("exists", False)
            )

    registered = len(result) > 0

    undefined = not registered and not res_check_parser_vk.get("registered", False)

    if data.details:
        details = DetailsRegistration(
            cheking_sites=cheking_site,
            search_type=data.type_search
        )

    """if len(result) < count_sites:
        count_sites = len(result)
        result = result[:count_sites]"""

    return ResponseSearchRegistration(
        success=True,
        search_object=data.object_search,
        sites=result,
        total_found=len(result),
        error=None,
        undefined=undefined,
        registered=registered,
        details=details,
    )
