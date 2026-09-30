import asyncio

from src.backend.infra.manage import database
from src.backend.service.db.repository import control_repository
from src.backend.service.task import task_app


@task_app.task(queue="database", name="database.users.delete")
def delete_user(user_id: int) -> dict:
    async def execute() -> dict:
        async with database.session_factory() as session:
            return await control_repository(session).users.delete("user_id", user_id)
    return asyncio.run(execute())
