"""Transport connection to the separate DataPilot AI service."""

from .http import HTTPConnection


class AIConnection(HTTPConnection):
    def __init__(self, base_url: str, *, timeout: int = 180, health_path: str = "/docs") -> None:
        super().__init__(base_url, timeout=timeout)
        self.health_path = health_path

    def test_connection(self, path: str | None = None) -> bool:
        return super().test_connection(self.health_path if path is None else path)
