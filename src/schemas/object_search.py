from pydantic import BaseModel, Field, ConfigDict
from typing import Optional,Literal
from typing import Dict, Any,List
from enum import Enum

class SearchMethod(str, Enum):
    SCRAPING = "scraping"
    PASSIVE = "passive search"
    HYBRID = "hybrid"

class Protocol(str, Enum):
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

def get_version_protocol(protocol: Protocol) -> int | None:
    # Исключаем SKCS, если он есть
    if protocol == getattr(Protocol, "SKCS", None):
        return None

    # Извлекаем число из строки (убираем "socks")
    if protocol.value.startswith("socks"):
        return int(protocol.value.replace("socks", ""))

    # Если это SKCS или что-то другое — возвращаем None
    return None


class DetailsSite(BaseModel):
    site_name: Optional[str] = None
    site_url: Optional[str] = None
    found_at: Optional[str] = None  # дата/время находки
    additional_info: Optional[Dict[str, Any]] = None

class SuccessSearchRegistration(BaseModel):
    """Информация о найденном аккаунте на одном сайте"""
    domain: Optional[str] = None
    recovery_email: Optional[str] = None
    phone: Optional[str] = None
    exists: Optional[bool] = True


class DetailsRegistration(BaseModel):
    cheking_sites: List[str]
    search_type: Optional[SearchMethod] = SearchMethod.HYBRID

class ResponseSearchRegistration(BaseModel):
    """Полный ответ после проверки email на всех сайтах"""
    success: bool
    search_object: str
    sites: Optional[Dict[str, SuccessSearchRegistration]] = None
    total_found: Optional[int] = 0
    error: Optional[str] = None
    undefined: Optional[bool] = None
    registered: Optional[bool] = None
    details: Optional[DetailsRegistration] = None


class RequestSearchRegistration(BaseModel):
    object_search:str
    depth_search: Optional[bool] = False
    count_site: int = 5
    details: Optional[bool] = False
    type_search: Optional[SearchMethod] = SearchMethod.HYBRID


class RequestSearchBreachesEmail(BaseModel):
    email:str
    details:Optional[bool] = None

class ResponceSearchBreachesEmail(BaseModel):
    breaches: Optional[list] = None
    email: str
    no_founed:Optional[bool] = None
    status: Optional[int] = None
    error: Optional[str] = None


class RequestProxy(BaseModel):
    count: Optional[int] = None


class AnswerProxy(BaseModel):
    ip: str
    port: int
    hostname: str
    protocol: Protocol

class ResponseProxy(BaseModel):
    proxys: List[AnswerProxy]

class NameEngine(BaseModel):
    google: Optional[Literal[0, 1]] = 0
    yandex: Optional[Literal[0, 1]] = 1
    baidu: Optional[Literal[0, 1]] = 0
    bing: Optional[Literal[0, 1]] = None
    duckduckgo: Optional[Literal[0, 1]] = 1
    ecosia: Optional[Literal[0, 1]] = 1

class RequestSearchEngine(BaseModel):
    text: str
    limit: int = 5
    count_results: int = limit
    engins: Optional[NameEngine] = None
    operators: Optional[List[str]] = None
    domains: Optional[List[str]] = None

class ResultSearchEngine(BaseModel):
    title:Optional[str] =""
    snippet: Optional[str] = ""
    description: Optional[str] = ""
    summary: str
    error: Optional[str] = None

class ResponsResultsSearchEngine(BaseModel):
    results: Optional[List[ResultSearchEngine]] = None
    count: int
    lead_time: float

class ErrorComponents(BaseModel):
    redis: str = ""
    openserp: str = ""
    postgres: str = ""
    holehe:str = ""
    phoneinfoga: str = ""


class ResponseHealthy(BaseModel):
    status: str
    status_code: int
    components: dict
    errors: List[str]
    warnings: List[str]
    timestamp: float
