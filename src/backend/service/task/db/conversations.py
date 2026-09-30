import asyncio

from src.backend.infra.manage import database, redis
from src.backend.repository.manage import ControlDb
from src.backend.service.task import task_app


@task_app.task(queue="database", name="database.conversations.delete")
def delete_conversation(conversation_id: int) -> dict:
    async def execute() -> dict:
        async with database.session_factory() as session:
            control_db = ControlDb(redis.client, session)
            return await control_db.conversations.delete("id", conversation_id)
    return asyncio.run(execute())
