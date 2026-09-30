import asyncio

from src.backend.infra.manage import database, redis
from src.backend.repository.manage import ControlDb
from src.backend.service.task import task_app


@task_app.task(queue="database", name="database.collaboration_notifications.create")
def create_notification(data: dict) -> dict:
    async def execute() -> dict:
        async with database.session_factory() as session:
            control_db = ControlDb(redis.client, session)
            return await control_db.collaboration_notifications.insert(data)
    return asyncio.run(execute())
