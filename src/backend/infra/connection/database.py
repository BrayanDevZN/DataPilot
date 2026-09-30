"""Async SQLAlchemy connections; persistence belongs in repositories."""

from sqlalchemy import URL, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.backend.logs.log import logger, log_operation


class SQLConnection:
    @log_operation
    def __init__(
        self,
        url: str | URL,
        connect_args: dict | None = None,
    ) -> None:
        self._url = url
        self._connect_args = dict(connect_args or {})
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @log_operation
    def base_url(self) -> URL:
        url = make_url(self._url) if isinstance(self._url, str) else self._url

        if url.get_backend_name() in {"postgres", "postgresql"}:
            if url.drivername != "postgresql+asyncpg":
                raise ValueError(
                    "PostgreSQL URL must explicitly use postgresql+asyncpg://"
                )
        elif url.get_backend_name() == "sqlite":
            if url.drivername != "sqlite+aiosqlite":
                raise ValueError(
                    "SQLite URL must explicitly use sqlite+aiosqlite://"
                )
        else:
            raise ValueError("Unsupported database backend")

        return url

    @log_operation
    def create_engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(
                self.base_url(),
                pool_pre_ping=True,
                hide_parameters=True,
                connect_args=self._connect_args,
            )
        logger.info("AsyncEngine disponível")
        return self._engine

    @log_operation
    def create_session(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.create_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        logger.info("Fábrica de AsyncSession disponível")
        return self._session_factory

    @property
    @log_operation
    def engine(self) -> AsyncEngine:
        return self.create_engine()

    @property
    @log_operation
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self.create_session()

    @log_operation
    def connect(self) -> AsyncConnection:
        return self.create_engine().connect()

    @log_operation
    async def test(self) -> bool:
        async with self.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1

    @log_operation
    async def test_connection(self) -> bool:
        return await self.test()

    @log_operation
    async def __call__(
        self,
    ) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
        engine = self.create_engine()
        sessions = self.create_session()

        try:
            if not await self.test():
                raise ConnectionError("Database connection test failed")
        except Exception:
            await self.close()
            raise

        return engine, sessions

    @log_operation
    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
