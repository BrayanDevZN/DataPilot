"""FastAPI dependency for the current authenticated user."""

from typing import Any

from fastapi import Request

from .token_user import TokenUser


_token_user = TokenUser()


async def get_current_user(request: Request) -> dict[str, Any]:
    return await _token_user(request)
