"""Shared service imports for the rest of the application."""

from src.backend.infra.manage import redis as redis_connection

from .auth import hash, jwt
from .db.migrate import make_migrate
from .db.tables import control_db
from .sender import Sender

redis = redis_connection.client
sender = Sender()

__all__ = ["control_db", "hash", "jwt", "sender", "redis", "make_migrate"]
