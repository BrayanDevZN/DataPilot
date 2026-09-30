from src.backend.domain.module import JWT, PasswordHash
from src.backend.infra.manage import settings

hash = PasswordHash()
jwt = JWT(settings.sing)
