import asyncio

from src.backend.infra.manage import database
from src.backend.service.db.repository import control_repository
from src.backend.service.task import task_app


@task_app.task(queue="database", name="database.data_sources.delete")
def delete_data_source(data_source_id: int) -> dict:
    async def execute() -> dict:
        async with database.session_factory() as session:
            return await control_repository(session).data_sources.delete("id", data_source_id)
    return asyncio.run(execute())
