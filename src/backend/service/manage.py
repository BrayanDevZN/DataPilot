"""Shared service imports for the rest of the application."""

from src.backend.infra.manage import redis as redis_connection
from src.backend.repository.cache import Cache

from .auth import ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL, hash, jwt, refresh_jwt
from .db.migrate import make_migrate
from .db.control import control_db
from .sender import Sender

redis = redis_connection.client
cache = Cache(redis)
sender = Sender()

__all__ = [
    "control_db",
    "hash",
    "jwt",
    "refresh_jwt",
    "ACCESS_TOKEN_TTL",
    "REFRESH_TOKEN_TTL",
    "sender",
    "redis",
    "cache",
    "make_migrate",
]
