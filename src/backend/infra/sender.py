"""Async email delivery using a separate yagmail client per send."""

import asyncio

import yagmail

from src.backend.logs.log import logger, log_operation


class Sender:
    @log_operation
    def __init__(self, email: str | None, password: str | None, *, timeout: int = 30) -> None:
        self._email = email
        self._password = password
        self._timeout = timeout

    @log_operation
    def _send(self, to: str, subject: str, contents: str, html: bool) -> None:
        with yagmail.SMTP(user=self._email, password=self._password, timeout=self._timeout) as client:
            client.send(to=to, subject=subject, contents=contents if html else yagmail.raw(contents))

    @log_operation
    async def send(self, to: str, subject: str, contents: str, *, html: bool = False) -> dict[str, bool]:
        if not self._email or not self._password:
            raise ValueError("EMAIL_USER and EMAIL_PASSWORD are required to send email")
        if not to.strip() or not subject.strip() or not contents.strip():
            raise ValueError("Provide recipient, subject and email contents")
        await asyncio.to_thread(self._send, to, subject, contents, html)
        logger.info("E-mail enviado com sucesso")
        return {"sent": True}
