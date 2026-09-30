import asyncio

from src.backend.infra.manage import database
from src.backend.service.db.repository import control_repository
from src.backend.service.task import task_app


@task_app.task(queue="database", name="database.dashboards.delete")
def delete_dashboard(dashboard_id: int) -> dict:
    async def execute() -> dict:
        async with database.session_factory() as session:
            return await control_repository(session).dashboards.delete("id", dashboard_id)
    return asyncio.run(execute())
