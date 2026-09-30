"""Create the mapped tables; this is not a versioned schema migration system."""

from importlib import import_module

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
        logger.info("Criação das tabelas concluída")

    @log_operation
    async def __call__(self) -> None:
        """Coordinate model registration and table creation."""
        await self.create_tables()
