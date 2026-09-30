"""Run with: python -m src.backend.service.db.migrate make_migrate."""

import asyncio
import sys

from src.backend.infra.manage import database
from src.backend.logs.log import logger, log_operation
from src.backend.repository.manage import Migration


@log_operation
async def make_migrate() -> None:
    try:
        migration = Migration(database.engine)
        logger.info("Executando criação das tabelas pela camada service")
        await migration()
    finally:
        await database.close()


@log_operation
def main() -> None:
    if sys.argv[1:] != ["make_migrate"]:
        raise ValueError(
            "Use: python -m src.backend.service.db.migrate make_migrate"
        )
    asyncio.run(make_migrate())


if __name__ == "__main__":
    main()
