"""Create mapped tables and ensure public UUID columns; not a versioned migration system."""

from importlib import import_module
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.backend.logs.log import logger, log_operation

from .base import Base


class Migration:
    @log_operation
    def __init__(self, engine: AsyncEngine) -> None:
        if not isinstance(engine, AsyncEngine):
            raise TypeError("Migration requires a SQLAlchemy AsyncEngine")
        self._engine = engine

    @log_operation
    def load_models(self) -> None:
        """Register every model in the shared metadata before creating tables."""
        import_module(".models", package=__package__)
        logger.info("Models carregados: %s tabelas", len(Base.metadata.tables))

    @log_operation
    async def create_tables(self) -> None:
        self.load_models()
        logger.info("Criando tabelas ausentes no banco")
        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all, checkfirst=True)
            migration_files = (
                ("public_ids.sql", "Garantindo public_id UUID em users e dashboards"),
                ("users_auth2.sql", "Garantindo coluna auth2 em users"),
            )
            for file_name, message in migration_files:
                statements = (
                    Path(__file__).resolve().parent / file_name
                ).read_text(encoding="utf-8")
                logger.info(message)
                for statement in statements.split(";"):
                    if statement.strip():
                        await connection.execute(text(statement))
        logger.info("Criação das tabelas concluída")

    @log_operation
    async def __call__(self) -> None:
        """Coordinate model registration and table creation."""
        await self.create_tables()
