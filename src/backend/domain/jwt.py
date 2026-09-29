"""Sign and validate JWTs with an explicitly supplied signing secret."""

from src.backend.logs.log import logger, log_operation

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt as pyjwt


class InvalidTokenError(ValueError):
    """The token cannot be trusted."""


class ExpiredTokenError(InvalidTokenError):
    """The token has expired."""


class JWT:
    @log_operation
    def __init__(self, sign: str, expires_in: timedelta = timedelta(hours=12)) -> None:
        if not isinstance(sign, str) or len(sign.encode("utf-8")) < 32:
            raise ValueError("JWT signing secret must contain at least 32 bytes")
        if not isinstance(expires_in, timedelta) or expires_in.total_seconds() <= 0:
            raise ValueError("JWT expiration must be a positive timedelta")
        self._sign = sign
        self._expires_in = expires_in

    @log_operation
    def write(self, payload: dict[str, Any]) -> str:
        """Return a signed token; iat and exp are controlled by this class."""
        if not isinstance(payload, dict):
            raise TypeError("JWT payload must be a dictionary")
        now = datetime.now(timezone.utc)
        claims = {**payload, "iat": now, "exp": now + self._expires_in}
        return pyjwt.encode(claims, self._sign, algorithm="HS256")

    @log_operation
    def read(self, token: str) -> dict[str, Any]:
        """Verify signature and expiration before returning any claims."""
        if not isinstance(token, str) or not token.strip():
            raise InvalidTokenError("Invalid JWT")
        try:
            return pyjwt.decode(
                token, self._sign, algorithms=["HS256"],
                options={"require": ["exp", "iat"]},
            )
        except pyjwt.ExpiredSignatureError:
            logger.warning("JWT rejeitado: expirado")
            raise ExpiredTokenError("JWT has expired") from None
        except pyjwt.InvalidTokenError:
            logger.warning("JWT rejeitado: validação inválida")
            raise InvalidTokenError("Invalid JWT") from None
