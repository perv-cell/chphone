from repositories.number_repo import NumberRepository
from service.number import NumberService

# Синглтон-репозиторий (можно заменить на настоящую БД)
_repo_instance = None

def get_number_repository() -> NumberRepository:
    """Провайдер репозитория"""
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = NumberRepository()
    return _repo_instance

def get_number_service(
    repo: NumberRepository = get_number_repository()
) -> NumberService:
    """Провайдер сервиса (внедряет репозиторий)"""
    return NumberService(repo)