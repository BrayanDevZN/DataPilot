"""Composition root for connection objects. Importing performs no network I/O."""

from src.backend.logs.log import logger, log_operation

from .connection.database import PostgreSQLConnection, SQLConnection
from .connection.redis import RedisConnection
from .sender import Sender
from .core.config import Settings
from .core.file import EmailFiles
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class Infrastructure:
    @log_operation
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.email_files = EmailFiles()
        self.redis = RedisConnection()
        self.database = PostgreSQLConnection(
            database=settings.db_name, host=settings.db_host, port=settings.db_port,
            username=settings.db_user, password=settings.db_password,
            database_url=settings.database_url, connect_timeout=settings.db_connect_timeout,
        )
        self.sender = Sender(settings.url_sender)
        logger.info("Infraestrutura pronta: PostgreSQL, Redis e Sender")

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
sender = infra.sender
email_files = infra.email_files


@log_operation
async def connect_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Initialize and test the shared database at application startup."""
    return await database()
