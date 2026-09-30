"""Email delivery through the external MCP Sender HTTP API."""

import asyncio

import requests

from src.backend.logs.log import logger, log_operation


class Sender:
    @log_operation
    def __init__(self, url: str) -> None:
        self._url = url.rstrip("/")

    @log_operation
    def _send(self, payload: dict[str, str]) -> None:
        try:
            response = requests.post(
                f"{self._url}/sender/",
                json=payload,
                timeout=30,
            )
        except requests.RequestException as error:
            raise RuntimeError(
                f"Unable to reach sender-v1 at {self._url}: {error}"
            ) from error

        if not response.ok:
            raise RuntimeError(
                "sender-v1 rejected the email request: "
                f"HTTP {response.status_code} - {response.text}"
            )

    @log_operation
    async def send(self, to: str, subject: str, contents: str, *, html: bool = False) -> dict[str, bool]:
        if not self._url:
            raise ValueError("URL_SENDER is required to send email")
        if not to.strip() or not subject.strip() or not contents.strip():
            raise ValueError("Provide recipient, subject and email contents")

        payload = {
            "email": to,
            "subject": subject,
            "body": contents,
        }

        await asyncio.to_thread(self._send, payload)

        logger.info("E-mail encaminhado ao sender server com sucesso")
        return {"sent": True}
