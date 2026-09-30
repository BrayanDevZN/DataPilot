from src.backend.infra.manage import database, redis
from src.backend.repository.manage import ControlDb

control_db = ControlDb(redis.client, database.session_factory())
