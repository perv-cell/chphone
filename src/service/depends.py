from fastapi import Depends
from route.repositories.database.number import NumberRepository
from route.repositories.database.email import EmailRepository
from route.repositories.database.common import CommonRepository
from service.services.common import CommonService
from service.services.number import NumberService
from service.services.email import EmailService
# Синглтон-репозиторий (можно заменить на настоящую БД)
_repo_instance_number = None
_repo_instance_email = None
_repo_instance_common = None

def get_number_repository() -> NumberRepository:
    """Провайдер репозитория"""
    global _repo_instance_number
    if _repo_instance_number is None:
        _repo_instance_number = NumberRepository()
    return _repo_instance_number

def get_email_repository() -> EmailRepository:
    global _repo_instance_email
    if _repo_instance_email is None:
          _repo_instance_email = EmailRepository()
    return _repo_instance_email


def get_number_service(
    repo: NumberRepository = Depends(get_number_repository),
) -> NumberService:
    """Провайдер сервиса (внедряет репозиторий)"""

    return NumberService(repo)

def get_email_service(
    repo: EmailRepository = Depends(get_email_repository),
) -> EmailService:
    return EmailService(repo)

def get_common_repository()-> CommonRepository:
    global _repo_instance_common
    if _repo_instance_common is None:
        _repo_instance_common = CommonRepository()
    return _repo_instance_common

def get_common_service(
    repo: CommonRepository = Depends(get_common_repository),
) -> CommonService:
    """Провайдер сервиса (внедряет репозиторий)"""
    return CommonService(repo)
