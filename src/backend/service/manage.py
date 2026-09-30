"""Shared service imports for the rest of the application."""

from src.backend.infra.manage import redis as redis_connection
from src.backend.repository.cache import Cache

from .auth import (
    ACCESS_TOKEN_TTL,
    AUTH2_USER_TTL,
    REFRESH_TOKEN_TTL,
    auth2_jwt,
    hash,
    jwt,
    refresh_jwt,
)
from .db.migrate import make_migrate
from .db.control import control_db
from .sender import Sender
from .verification_codes import VerificationCodes

redis = redis_connection.client
cache = Cache(redis)
sender = Sender()
verification_codes = VerificationCodes(cache)

__all__ = [
    "control_db",
    "hash",
    "jwt",
    "refresh_jwt",
    "auth2_jwt",
    "ACCESS_TOKEN_TTL",
    "REFRESH_TOKEN_TTL",
    "AUTH2_USER_TTL",
    "sender",
    "verification_codes",
    "redis",
    "cache",
    "make_migrate",
]
