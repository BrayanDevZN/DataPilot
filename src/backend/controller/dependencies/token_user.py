"""Resolve and validate the authenticated user from an HTTP request."""

from typing import Any

from fastapi import HTTPException, Request, status

from src.backend.domain.module import ExpiredTokenError, InvalidTokenError
from src.backend.infra.manage import database
from src.backend.service.manage import control_db, jwt


class TokenUser:
    """Read a JWT from the request and return the corresponding database user."""

    def _token(self, request: Request) -> str:
        authorization = request.headers.get("authorization", "")
        scheme, _, bearer = authorization.partition(" ")

        if scheme.lower() == "bearer" and bearer.strip():
            return bearer.strip()

        cookie_token = (
            request.cookies.get("token")
            or request.cookies.get("access_token")
        )
        if cookie_token:
            return cookie_token.strip()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def _identifier(self, claims: dict[str, Any]) -> tuple[str, Any]:
        public_id = claims.get("public_id")
        if public_id is not None:
            return "public_id", public_id

        user_id = claims.get("user_id")
        if user_id is not None:
            return "user_id", user_id

        subject = claims.get("sub")
        if subject is not None:
            try:
                return "user_id", int(subject)
            except (TypeError, ValueError):
                return "public_id", subject

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not identify a user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def __call__(self, request: Request) -> dict[str, Any]:
        token = self._token(request)

        try:
            claims = jwt.read(token)
        except ExpiredTokenError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except InvalidTokenError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error

        identifier, value = self._identifier(claims)

        async with database.session_factory() as session:
            try:
                user = await control_db.users.get(
                    session,
                    identifier,
                    value,
                )
            except (TypeError, ValueError) as error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user identifier in token",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from error

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user does not exist",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = dict(user)
        user.pop("password", None)
        return user
