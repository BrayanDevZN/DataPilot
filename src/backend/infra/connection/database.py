"""Reusable SQL engines for the application and external SQL sources."""

from functools import cached_property

from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Connection, Engine, make_url


class SQLConnection:
    def __init__(self, url: str | URL, connect_args: dict | None = None) -> None:
        self._url = make_url(url) if isinstance(url, str) else url
        self._connect_args = dict(connect_args or {})

    @cached_property
    def engine(self) -> Engine:
        return create_engine(
            self._url, pool_pre_ping=True, connect_args=self._connect_args,
            hide_parameters=True,
        )

    def connect(self) -> Connection:
        """Caller must close the connection, preferably with a context manager."""
        return self.engine.connect()

    def test_connection(self) -> bool:
        """Run a connectivity probe; failures propagate to the caller."""
        with self.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1

    def close(self) -> None:
        if "engine" in self.__dict__:
            self.engine.dispose()


class PostgreSQLConnection(SQLConnection):
    def __init__(
        self, *, database: str | None = None, host: str | None = None,
        port: int = 5432, username: str | None = None, password: str | None = None,
        database_url: str | None = None, connect_timeout: int = 10,
    ) -> None:
        # Validate credentials only when the engine is requested, keeping imports offline.
        self._parameters = dict(database=database, host=host, port=port,
                                username=username, password=password)
        self._database_url = database_url
        self._timeout = connect_timeout

    @cached_property
    def engine(self) -> Engine:
        if self._database_url:
            url = make_url(self._database_url)
            if url.get_backend_name() not in ("postgres", "postgresql"):
                raise ValueError("DATABASE_URL must use PostgreSQL")
            url = url.set(drivername="postgresql+psycopg")
        else:
            missing = [name for name in ("database", "host", "username", "password")
                       if not self._parameters[name]]
            if missing:
                raise ValueError("Missing PostgreSQL settings: " + ", ".join(missing))
            url = URL.create("postgresql+psycopg", **self._parameters)
        return create_engine(
            url, pool_pre_ping=True, hide_parameters=True,
            connect_args={"connect_timeout": self._timeout},
        )
