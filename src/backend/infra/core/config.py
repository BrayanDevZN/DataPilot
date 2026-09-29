"""Load the local infrastructure .env, or the repository root .env."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def load_environment(project_root: Path | None = None) -> Path | None:
    root = project_root if project_root is not None else Path(__file__).resolve().parents[4]
    local_env = root / "src/backend/infra/core/.env"
    root_env = root / ".env"
    selected = local_env if local_env.is_file() else root_env
    if not selected.is_file():
        return None
    load_dotenv(selected, override=False)
    return selected


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
    http_timeout: int = 30
    ai_timeout: int = 180
    ai_url: str = "https://web-production-40ead.up.railway.app"
    ai_health_path: str = "/docs"
    resend_url: str = "https://api.resend.com"
    key_email: str | None = field(default=None, repr=False)
    email_user: str = "DataPilot <no-reply@datapilotplataform.com>"
    url_email: str | None = None
    secret: str | None = field(default=None, repr=False)
    cors_allowed_origins: tuple[str, ...] = ()

    @classmethod
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
            http_timeout=positive_int("HTTP_TIMEOUT", 30),
            ai_timeout=positive_int("AI_TIMEOUT", 180),
            ai_url=os.getenv("AI_URL", cls.ai_url),
            ai_health_path=os.getenv("AI_HEALTH_PATH", cls.ai_health_path),
            resend_url=os.getenv("RESEND_URL", cls.resend_url),
            key_email=os.getenv("KEY_EMAIL"),
            email_user=os.getenv("EMAIL_USER", cls.email_user),
            url_email=os.getenv("URL_EMAIL"),
            secret=os.getenv("SECRET"),
            cors_allowed_origins=tuple(
                origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
                if origin.strip()
            ),
        )
