"""Cookie-backed access and refresh token sessions."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request, Response, status

from src.backend.domain.module import ExpiredTokenError, InvalidTokenError
from src.backend.infra.manage import settings
from src.backend.service.manage import (
    ACCESS_TOKEN_TTL,
    AUTH2_USER_TTL,
    REFRESH_TOKEN_TTL,
    auth2_jwt,
    jwt,
    redis,
    refresh_jwt,
)


ACCESS_COOKIE = "X-token_user"
REFRESH_COOKIE = "X-refresh_user"
AUTH2_USER_COOKIE = "X-auth2_user"



def create_auth2_user_cookie(
    response: Response,
    email: str,
) -> int:
    now = datetime.now(timezone.utc)
    expires_at = now + AUTH2_USER_TTL

    token = auth2_jwt.write({
        "email": str(email).strip().lower(),
        "token_type": "auth2_user",
    })

    response.set_cookie(
        key=AUTH2_USER_COOKIE,
        value=token,
        max_age=int(AUTH2_USER_TTL.total_seconds()),
        expires=expires_at,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/sender/auth2",
    )

    return int(expires_at.timestamp())


def clear_auth2_user_cookie(response: Response) -> None:
    response.delete_cookie(
        AUTH2_USER_COOKIE,
        path="/sender/auth2",
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )


def read_auth2_user_cookie(request: Request) -> dict[str, Any]:
    token = request.cookies.get(AUTH2_USER_COOKIE)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Two-factor authentication cookie required",
        )

    try:
        claims = auth2_jwt.read(token)
    except ExpiredTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Two-factor authentication cookie expired",
        ) from error
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid two-factor authentication cookie",
        ) from error

    if claims.get("token_type") != "auth2_user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid two-factor authentication token type",
        )

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Two-factor authentication token does not contain an email",
        )

    return claims

def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    data = dict(user)
    data.pop("password", None)
    return data


async def create_session(
    response: Response,
    user: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    access_exp = now + ACCESS_TOKEN_TTL
    refresh_exp = now + REFRESH_TOKEN_TTL
    refresh_jti = str(uuid4())

    base_claims = {
        "user_id": user["user_id"],
        "public_id": str(user["public_id"]),
        "role": user.get("role", "user"),
    }

    access_token = jwt.write({
        **base_claims,
        "token_type": "access",
    })
    refresh_token = refresh_jwt.write({
        **base_claims,
        "token_type": "refresh",
        "jti": refresh_jti,
    })

    refresh_ttl = max(1, int(REFRESH_TOKEN_TTL.total_seconds()))
    await redis.set(
        f"refresh_token:{refresh_jti}",
        str(user["user_id"]),
        ex=refresh_ttl,
    )

    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=int(ACCESS_TOKEN_TTL.total_seconds()),
        expires=access_exp,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=refresh_ttl,
        expires=refresh_exp,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )

    return {
        "authenticated": True,
        "auth2_required": False,
        "access_expires_at": int(access_exp.timestamp()),
        "refresh_expires_at": int(refresh_exp.timestamp()),
        "user": _public_user(user),
    }


async def consume_refresh_token(request: Request) -> dict[str, Any]:
    token = request.cookies.get(REFRESH_COOKIE)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    try:
        claims = refresh_jwt.read(token)
    except ExpiredTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        ) from error
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from error

    if claims.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token type",
        )

    jti = claims.get("jti")
    user_id = claims.get("user_id")

    if not jti or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims",
        )

    stored_user_id = await redis.getdel(f"refresh_token:{jti}")
    if stored_user_id is None or str(stored_user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    return claims


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(
        ACCESS_COOKIE,
        path="/",
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
    response.delete_cookie(
        REFRESH_COOKIE,
        path="/",
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )
