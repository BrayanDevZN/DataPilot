"""Authenticated Resend connection; message composition belongs elsewhere."""

from src.backend.logs.log import logger, log_operation

from urllib.parse import urlsplit

import requests


class ResendConnection:
    @log_operation
    def __init__(self, api_key: str | None, *, base_url: str = "https://api.resend.com", timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._api_key = api_key

    @log_operation
    def request(self, method: str, path: str = "", **kwargs) -> requests.Response:
        if not self._api_key:
            raise ValueError("KEY_EMAIL is required for Resend")
        url = f"{self.base_url}/{path.lstrip('/')}"
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("An absolute HTTP(S) URL is required for Resend")
        headers = {**kwargs.pop("headers", {}), "Authorization": f"Bearer {self._api_key}"}
        kwargs.setdefault("timeout", self.timeout)
        with requests.Session() as session:
            response = session.request(method, url, headers=headers, **kwargs)
            logger.info("Resend respondeu com status HTTP %s", response.status_code)
            response.raise_for_status()
            return response

    @log_operation
    def test(self, path: str = "/domains") -> bool:
        """Read-only authentication probe; requires permission to list domains."""
        self.request("GET", path)
        return True

    @log_operation
    def test_connection(self, path: str = "/domains") -> bool:
        return self.test(path)

    @log_operation
    def __call__(self, path: str = "/domains") -> "ResendConnection":
        self.test(path)
        return self
