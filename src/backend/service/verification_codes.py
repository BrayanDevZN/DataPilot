"""Redis-backed verification code lifecycle."""

from secrets import randbelow

from src.backend.logs.log import log_operation
from src.backend.repository.cache import Cache


class VerificationCodes:
    VALID_TYPES = {"create_account", "change_password", "auth2"}
    DEFAULT_EXPIRE_SECONDS = 60

    @log_operation
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    def _normalize_email(self, email: str) -> str:
        normalized = str(email).strip().lower()
        if not normalized:
            raise ValueError("Email is required")
        return normalized

    def _key(self, email_type: str, email: str) -> str:
        if email_type not in self.VALID_TYPES:
            raise ValueError("Unknown verification email type")
        return f"{email_type}:{self._normalize_email(email)}"

    def _code(self) -> str:
        return f"{randbelow(1_000_000):06d}"

    @log_operation
    async def issue(
        self,
        email_type: str,
        email: str,
        *,
        expire: int | None = None,
    ) -> str:
        code = self._code()
        ttl = self.DEFAULT_EXPIRE_SECONDS if expire is None else expire
        await self.cache.set(
            self._key(email_type, email),
            code,
            expire=ttl,
        )
        return code

    @log_operation
    async def consume(
        self,
        email_type: str,
        email: str,
        code: str,
    ) -> bool:
        result = await self.cache.consume(
            self._key(email_type, email),
            code,
        )
        return result["consumed"]

    @log_operation
    async def delete(
        self,
        email_type: str,
        email: str,
    ) -> None:
        await self.cache.delete(self._key(email_type, email))
