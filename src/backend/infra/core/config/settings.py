"""Load and validate DataPilot infrastructure settings."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

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

    logger.info(
        "Carregando configuração de %s; ambiente do processo tem prioridade",
        selected,
    )
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


@log_operation
def cookie_samesite(name: str = "COOKIE_SAMESITE") -> str:
    value = (os.getenv(name) or "lax").strip().lower()
    if value not in {"lax", "strict", "none"}:
        raise ValueError(f"{name} must be lax, strict or none")
    return value


@log_operation
def positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        raise ValueError(f"{name} must be a positive integer") from None

    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


@log_operation
def runtime_environment() -> str:
    value = (os.getenv("ENVIROIMENT") or "test").strip().lower()
    if value not in {"test", "prod"}:
        raise ValueError("ENVIROIMENT must be test or prod")
    return value


@log_operation
def resolve_database_url(environment: str, project_root: Path) -> str:
    configured = (os.getenv("DATABASE_URL") or "").strip()

    if configured:
        url = make_url(configured)
        if url.get_backend_name() in {"postgres", "postgresql"}:
            if url.drivername != "postgresql+asyncpg":
                raise ValueError(
                    "PostgreSQL DATABASE_URL must explicitly use "
                    "postgresql+asyncpg://"
                )
        elif url.drivername != "sqlite+aiosqlite":
            raise ValueError(
                "DATABASE_URL must use postgresql+asyncpg:// or "
                "sqlite+aiosqlite://"
            )
        return configured

    if environment == "prod":
        raise ValueError("DATABASE_URL is required when ENVIROIMENT=prod")

    sqlite_path = (
        project_root
        / "src"
        / "backend"
        / "repository"
        / "db"
        / "data.db"
    ).resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{sqlite_path}"


@dataclass(frozen=True)
class Settings:
    enviroiment: str = "test"
    database_url: str = field(default="", repr=False)
    db_connect_timeout: int = 10
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
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
    cookie_samesite: str = "lax"

    @classmethod
    @log_operation
    def from_env(cls, project_root: Path | None = None) -> "Settings":
        root = (
            project_root.resolve()
            if project_root is not None
            else Path(__file__).resolve().parents[5]
        )
        load_environment(root)

        environment = runtime_environment()
        openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip() or None
        signing_key = (os.getenv("SING") or "").strip() or None

        if environment == "prod":
            missing = [
                name
                for name, value in {
                    "DATABASE_URL": os.getenv("DATABASE_URL"),
                    "OPENAI_API_KEY": openai_api_key,
                    "SING": signing_key,
                }.items()
                if not value
            ]
            if missing:
                raise ValueError(
                    "Missing required production settings: "
                    + ", ".join(missing)
                )
        elif signing_key is None:
            signing_key = "datapilot-local-test-signing-key-32-bytes"

        return cls(
            enviroiment=environment,
            database_url=resolve_database_url(environment, root),
            db_connect_timeout=positive_int("DB_CONNECT_TIMEOUT", 10),
            redis_host=os.getenv("REDIS_HOST") or "localhost",
            redis_port=positive_int("REDIS_PORT", 6379),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            email_timeout=positive_int("EMAIL_TIMEOUT", 30),
            url_sender=os.getenv("URL_SENDER") or "http://api:8000",
            celery_broker_url=(
                os.getenv("CELERY_BROKER_URL")
                or "redis://redis-celery:6379/0"
            ),
            celery_backend_url=(
                os.getenv("CELERY_BACKEND_URL")
                or "redis://redis-celery:6379/0"
            ),
            url_email=os.getenv("URL_EMAIL"),
            secret=os.getenv("SECRET"),
            sing=signing_key,
            openai_api_key=openai_api_key,
            cors_allowed_origins=tuple(
                origin.strip()
                for origin in os.getenv(
                    "CORS_ALLOWED_ORIGINS",
                    "",
                ).split(",")
                if origin.strip()
            ),
            cookie_secure=env_bool("COOKIE_SECURE", False),
            cookie_samesite=cookie_samesite(),
        )
