"""Celery connection backed by the dedicated Redis service."""

from celery import Celery

from src.backend.logs.log import logger, log_operation


class CeleryConnection:
    @log_operation
    def __init__(self, broker: str, backend: str) -> None:
        self._broker = broker
        self._backend = backend
        self._app: Celery | None = None

    @log_operation
    def create_client(self) -> Celery:
        if self._app is None:
            self._app = Celery(
                "datapilot",
                broker=self._broker,
                backend=self._backend,
            )
        logger.info("Cliente Celery disponível")
        return self._app

    @property
    @log_operation
    def client(self) -> Celery:
        return self.create_client()

    @log_operation
    def __call__(self) -> Celery:
        return self.create_client()
