"""Shared SQLAlchemy declarative base with safe model logging."""

from sqlalchemy.orm import DeclarativeBase, registry

from src.backend.logs.log import logger, log_operation


@log_operation
def _model_constructor(self, **kwargs):
    logger.info("Criando objeto ORM: %s", type(self).__name__)
    for key, value in kwargs.items():
        if not hasattr(type(self), key):
            raise TypeError(f"Invalid mapped attribute: {key}")
        setattr(self, key, value)


class Base(DeclarativeBase):
    registry = registry(constructor=_model_constructor)

    @classmethod
    @log_operation
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        logger.info("Model ORM registrado: %s", cls.__tablename__)
