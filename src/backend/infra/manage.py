"""Composition root for connection objects. Importing performs no network I/O."""

from .connection.ai import AIConnection
from .connection.database import PostgreSQLConnection, SQLConnection
from .connection.email import ResendConnection
from .connection.http import HTTPConnection
from .core.config import Settings


class Infrastructure:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database = PostgreSQLConnection(
            database=settings.db_name, host=settings.db_host, port=settings.db_port,
            username=settings.db_user, password=settings.db_password,
            database_url=settings.database_url, connect_timeout=settings.db_connect_timeout,
        )
        self.http = HTTPConnection(timeout=settings.http_timeout)
        self.ai = AIConnection(settings.ai_url, timeout=settings.ai_timeout,
                               health_path=settings.ai_health_path)
        self.email = ResendConnection(settings.key_email, base_url=settings.resend_url,
                                      timeout=settings.http_timeout)

    def external_database(self, url: str, *, connect_args: dict | None = None) -> SQLConnection:
        """Each external source owns its engine; callers must close it after use."""
        return SQLConnection(url, connect_args=connect_args)

    def close(self) -> None:
        self.database.close()


settings = Settings.from_env()
infra = Infrastructure(settings)
database = infra.database
