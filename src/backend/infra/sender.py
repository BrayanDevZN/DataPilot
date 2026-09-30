"""Async email delivery through the external MCP Sender HTTP API."""

import httpx

from src.backend.logs.log import logger, log_operation


class Sender:
    @log_operation
    def __init__(self, url: str, *, timeout: int = 30) -> None:
        self._url = url.rstrip("/")
        self._timeout = timeout

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

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._url}/sender/", json=payload)
            response.raise_for_status()

        logger.info("E-mail encaminhado ao sender server com sucesso")
        return {"sent": True}
