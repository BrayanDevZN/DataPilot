"""Composition root for connection objects. Importing performs no network I/O."""

from src.backend.logs.log import logger, log_operation

from .connection.celery import CeleryConnection
from .connection.database import SQLConnection
from .connection.redis import RedisConnection
from .sender import Sender
from .openai import OpenAIClient
from .core.config.settings import Settings
from .core.sender.file import EmailFiles
from .core.prompts.prompt import PromptFiles
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class Infrastructure:
    @log_operation
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.email_files = EmailFiles()
        self.prompts = PromptFiles()
        self.redis = RedisConnection(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
        )
        self.celery_connection = CeleryConnection(
            broker=settings.celery_broker_url,
            backend=settings.celery_backend_url,
        )
        self.celery = self.celery_connection()
        database_connect_args = (
            {"timeout": settings.db_connect_timeout}
            if settings.database_url.startswith("postgresql+asyncpg://")
            else {}
        )
        self.database = SQLConnection(
            settings.database_url,
            connect_args=database_connect_args,
        )
        self.sender = Sender(settings.url_sender)
        self.openai = OpenAIClient(settings.openai_api_key)
        logger.info("Infraestrutura pronta: SQL, Redis, Celery e Sender")

    @log_operation
    def external_database(self, url: str, *, connect_args: dict | None = None) -> SQLConnection:
        """Each external source owns its engine; callers must close it after use."""
        return SQLConnection(url, connect_args=connect_args)

    @log_operation
    async def close(self) -> None:
        try:
            await self.database.close()
        finally:
            await self.redis.close()


settings = Settings.from_env()
infra = Infrastructure(settings)
database = infra.database
redis = infra.redis
celery_connection = infra.celery_connection
celery = infra.celery
sender = infra.sender
openai = infra.openai
email_files = infra.email_files
prompts = infra.prompts


@log_operation
async def connect_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initialize and test the shared database at application startup."""
    return await database()
