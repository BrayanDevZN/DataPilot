from src.backend.infra.manage import database
from src.backend.repository.manage import ControlDb

control_db = ControlDb(database.session_factory())
