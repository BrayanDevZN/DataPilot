"""Authenticated Resend transport; message composition belongs in an adapter."""

from .http import HTTPConnection


class ResendConnection(HTTPConnection):
    def __init__(self, api_key: str | None, *, base_url: str = "https://api.resend.com", timeout: int = 30) -> None:
        super().__init__(base_url, timeout=timeout,
                         headers={"Authorization": f"Bearer {api_key}"} if api_key else {})
        self._api_key = api_key

    def request(self, method: str, path: str = "", **kwargs):
        if not self._api_key:
            raise ValueError("KEY_EMAIL is required for Resend")
        return super().request(method, path, **kwargs)

    def test_connection(self, path: str = "/domains") -> bool:
        """Read-only authentication probe; requires a key allowed to list domains."""
        return super().test_connection(path)

    def test(self, path: str = "/domains") -> bool:
        return self.test_connection(path)

    def __call__(self, path: str = "/domains") -> "ResendConnection":
        self.test(path)
        return self
