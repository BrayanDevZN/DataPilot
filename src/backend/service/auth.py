from datetime import timedelta

from src.backend.domain.module import JWT, PasswordHash
from src.backend.infra.manage import settings


ACCESS_TOKEN_TTL = timedelta(hours=12)
REFRESH_TOKEN_TTL = timedelta(days=30)

hash = PasswordHash()
jwt = JWT(settings.sing, expires_in=ACCESS_TOKEN_TTL)
refresh_jwt = JWT(settings.sing, expires_in=REFRESH_TOKEN_TTL)
