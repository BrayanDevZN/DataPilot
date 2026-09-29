"""HTTP transport for external APIs, without data parsing or business operations."""

from urllib.parse import urlsplit

import requests


class HTTPConnection:
    def __init__(
        self, base_url: str | None = None, *, timeout: int = 30,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self._headers = dict(headers or {})

    def _resolve_url(self, path: str) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("An absolute HTTP(S) URL is required")
        return url

    def request(self, method: str, path: str = "", **kwargs) -> requests.Response:
        headers = {**self._headers, **kwargs.pop("headers", {})}
        kwargs.setdefault("timeout", self.timeout)
        # Sessions are scoped to each call; the shared connector has no mutable session.
        with requests.Session() as session:
            response = session.request(method, self._resolve_url(path), headers=headers, **kwargs)
            response.raise_for_status()
            return response

    def test_connection(self, path: str = "") -> bool:
        """A successful GET checks reachability of the chosen endpoint."""
        self.request("GET", path)
        return True

    def test(self, path: str = "") -> bool:
        return self.test_connection(path)

    def __call__(self, path: str = "") -> "HTTPConnection":
        self.test(path)
        return self
