"""Provide table controls with a session scoped to each context."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from src.backend.infra.manage import database
from src.backend.logs.log import logger
from src.backend.repository.manage import ControlDb


class Tables:
    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[ControlDb]:
        async with database.session_factory() as session:
            logger.info("Abrindo sessão para os controles de tabelas")
            try:
                yield ControlDb(session)
            except Exception as error:
                logger.error("Falha no contexto dos controles de tabelas (%s)", type(error).__name__)
                raise
            finally:
                logger.info("Encerrando contexto dos controles de tabelas")


tables = Tables()
