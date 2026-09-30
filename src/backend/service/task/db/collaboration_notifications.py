import asyncio

from src.backend.infra.manage import database
from src.backend.service.db.repository import control_repository
from src.backend.service.task import task_app


@task_app.task(queue="database", name="database.collaboration_notifications.create")
def create_notification(data: dict) -> dict:
    async def execute() -> dict:
        async with database.session_factory() as session:
            return await control_repository(session).collaboration_notifications.insert(data)
    return asyncio.run(execute())
