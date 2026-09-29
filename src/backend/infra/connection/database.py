"""Async SQLAlchemy connections; persistence belongs in repositories."""

from sqlalchemy import URL, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)


class SQLConnection:
    def __init__(self, url: str | URL, connect_args: dict | None = None) -> None:
        self._url = url
        self._connect_args = dict(connect_args or {})
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def base_url(self) -> URL:
        url = make_url(self._url) if isinstance(self._url, str) else self._url
        if url.get_backend_name() in ("postgres", "postgresql"):
            url = url.set(drivername="postgresql+psycopg")
        return url

    def create_engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(
                self.base_url(), pool_pre_ping=True, hide_parameters=True,
                connect_args=self._connect_args,
            )
        return self._engine

    def create_session(self) -> async_sessionmaker[AsyncSession]:
        """Return a factory, so each operation gets its own AsyncSession."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.create_engine(), class_=AsyncSession, expire_on_commit=False,
            )
        return self._session_factory

    @property
    def engine(self) -> AsyncEngine:
        return self.create_engine()

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self.create_session()

    def connect(self) -> AsyncConnection:
        return self.create_engine().connect()

    async def test(self) -> bool:
        """Test this connection with SELECT 1; failures propagate."""
        async with self.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1

    async def test_connection(self) -> bool:
        return await self.test()

    async def __call__(self) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
        """Build the URL, engine and session factory, test, then return both."""
        engine = self.create_engine()
        sessions = self.create_session()
        try:
            if not await self.test():
                raise ConnectionError("Database connection test failed")
        except Exception:
            await self.close()
            raise
        return engine, sessions

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()


class PostgreSQLConnection(SQLConnection):
    def __init__(
        self, *, database: str | None = None, host: str | None = None,
        port: int = 5432, username: str | None = None, password: str | None = None,
        database_url: str | None = None, connect_timeout: int = 10,
    ) -> None:
        super().__init__(database_url or "", {"connect_timeout": connect_timeout})
        self._parameters = dict(database=database, host=host, port=port,
                                username=username, password=password)
        self._database_url = database_url

    def base_url(self) -> URL:
        if self._database_url:
            url = make_url(self._database_url)
            if url.get_backend_name() not in ("postgres", "postgresql"):
                raise ValueError("DATABASE_URL must use PostgreSQL")
            return url.set(drivername="postgresql+psycopg")
        missing = [name for name in ("database", "host", "username", "password")
                   if not self._parameters[name]]
        if missing:
            raise ValueError("Missing PostgreSQL settings: " + ", ".join(missing))
        return URL.create("postgresql+psycopg", **self._parameters)
