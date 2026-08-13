from fastapi import Depends
from route.repositories.database.postgres import PostgresRepositories
from route.repositories.database.redis import CommonRepository
from service.services.common import CommonService
from service.services.healthy import HealthCheckerService
from service.services.number import NumberService
from service.services.email import EmailService

_repo_instance_number = None
_repo_instance_email = None
_repo_instance_common = None

def get_postgres_repository() -> PostgresRepositories:
    """Провайдер репозитория"""
    global _repo_instance_number
    if _repo_instance_number is None:
        _repo_instance_number = PostgresRepositories()
    return _repo_instance_number


def get_number_service(
    repo: PostgresRepositories = Depends(get_postgres_repository, use_cache=True),
) -> NumberService:
    """Провайдер сервиса (внедряет репозиторий)"""

    return NumberService(repo)

def get_email_service(
    repo: PostgresRepositories = Depends(get_postgres_repository, use_cache=True),
) -> EmailService:
    return EmailService(repo)

def get_redis_repository()-> CommonRepository:
    global _repo_instance_common
    if _repo_instance_common is None:
        _repo_instance_common = CommonRepository()
    return _repo_instance_common

def get_common_service(
    repo: CommonRepository = Depends(get_redis_repository, use_cache=True),
) -> CommonService:
    """Провайдер сервиса (внедряет репозиторий)"""
    return CommonService(repo)

def get_health_checker_service(
    repoPostgr: PostgresRepositories = Depends(get_postgres_repository, use_cache=True),
    repoRedis: CommonRepository = Depends(get_redis_repository, use_cache=True),
)-> HealthCheckerService:
    return HealthCheckerService(
        repoPostgr=repoPostgr,
        repoRedis=repoRedis
    )
