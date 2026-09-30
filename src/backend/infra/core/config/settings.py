"""Load DataPilot infrastructure settings from the local or repository environment."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from src.backend.logs.log import logger, log_operation


@log_operation
def load_environment(project_root: Path | None = None) -> Path | None:
    root = project_root if project_root is not None else Path(__file__).resolve().parents[5]
    local_env = root / "src/backend/infra/core/config/.env"
    root_env = root / ".env"
    selected = local_env if local_env.is_file() else root_env
    if not selected.is_file():
        logger.info("Nenhum arquivo .env encontrado; usando variáveis do processo")
        return None
    logger.info("Carregando configuração de %s; ambiente do processo tem prioridade", selected)
    load_dotenv(selected, override=False)
    return selected


@log_operation
def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        raise ValueError(f"{name} must be a positive integer") from None
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True)
class Settings:
    db_name: str | None = None
    db_host: str | None = None
    db_user: str | None = None
    db_password: str | None = field(default=None, repr=False)
    database_url: str | None = field(default=None, repr=False)
    db_port: int = 5432
    db_connect_timeout: int = 10
    email_timeout: int = 30
    url_sender: str = "http://api:8000"
    celery_broker_url: str = "redis://redis-celery:6379/0"
    celery_backend_url: str = "redis://redis-celery:6379/0"
    url_email: str | None = None
    secret: str | None = field(default=None, repr=False)
    sing: str | None = field(default=None, repr=False)
    openai_api_key: str | None = field(default=None, repr=False)
    cors_allowed_origins: tuple[str, ...] = ()
    cookie_secure: bool = False

    @classmethod
    @log_operation
    def from_env(cls, project_root: Path | None = None) -> "Settings":
        load_environment(project_root)
        return cls(
            db_name=os.getenv("DB_NAME"),
            db_host=os.getenv("DB_HOST"),
            db_user=os.getenv("DB_USER"),
            db_password=os.getenv("DB_PASSWORD"),
            database_url=os.getenv("DATABASE_URL"),
            db_port=positive_int("DB_PORT", 5432),
            db_connect_timeout=positive_int("DB_CONNECT_TIMEOUT", 10),
            email_timeout=positive_int("EMAIL_TIMEOUT", 30),
            url_sender=os.getenv("URL_SENDER") or "http://api:8000",
            celery_broker_url=os.getenv("CELERY_BROKER_URL") or "redis://redis-celery:6379/0",
            celery_backend_url=os.getenv("CELERY_BACKEND_URL") or "redis://redis-celery:6379/0",
            url_email=os.getenv("URL_EMAIL"),
            secret=os.getenv("SECRET"),
            sing=os.getenv("SING"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            cors_allowed_origins=tuple(
                origin.strip()
                for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
                if origin.strip()
            ),
            cookie_secure=env_bool("COOKIE_SECURE", False),
        )
