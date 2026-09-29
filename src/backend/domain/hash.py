"""Password hashing and verification with bcrypt."""

from src.backend.logs.log import logger, log_operation

import bcrypt


class PasswordHash:
    @log_operation
    def __init__(self, rounds: int = 12) -> None:
        if isinstance(rounds, bool) or not isinstance(rounds, int) or not 4 <= rounds <= 31:
            raise ValueError("bcrypt rounds must be an integer between 4 and 31")
        self._rounds = rounds

    @log_operation
    def _encode(self, password: str) -> bytes:
        if not isinstance(password, str) or not password:
            raise ValueError("Password must be a non-empty string")
        encoded = password.encode("utf-8")
        if len(encoded) > 72:
            raise ValueError("bcrypt passwords must not exceed 72 UTF-8 bytes")
        return encoded

    @log_operation
    def generate(self, password: str) -> str:
        """Return a salted hash suitable for storage as text."""
        encoded = self._encode(password)
        return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=self._rounds)).decode("ascii")

    @log_operation
    def compare(self, password: str, password_hash: str) -> bool:
        """Return whether the password matches; malformed stored hashes return False."""
        encoded = self._encode(password)
        if not isinstance(password_hash, str):
            logger.warning("Hash de senha com tipo inválido")
            return False
        try:
            matches = bcrypt.checkpw(encoded, password_hash.encode("ascii"))
            logger.info("Comparação de senha concluída: %s", "corresponde" if matches else "não corresponde")
            return matches
        except (ValueError, UnicodeEncodeError):
            logger.warning("Hash de senha com formato inválido")
            return False
