"""Authentication routes for login, token refresh and logout."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_session
from src.backend.controller.schema.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
)
from src.backend.controller.session import (
    clear_session_cookies,
    create_session,
    consume_refresh_token,
)
from src.backend.service.manage import (
    control_db,
    hash,
    sender,
    verification_codes,
)


router = APIRouter(prefix="/auth", tags=["auth"])


async def _find_user(
    session: AsyncSession,
    identifier: str,
) -> dict[str, Any] | None:
    field = "email" if "@" in identifier else "username"
    return await control_db.users.get(
        session,
        field,
        identifier.strip().lower(),
    )


@router.post(
    "/",
    response_model=LoginResponse,
)
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    user = await _find_user(session, data.identifier)

    if user is None or not hash.compare(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.get("auth2", False):
        if data.code is None:
            response.status_code = status.HTTP_202_ACCEPTED
            code = await verification_codes.issue(
                "auth2",
                user["email"],
                expire=None,
            )

            try:
                await sender.auth2(user["email"], code)
            except Exception:
                await verification_codes.delete(
                    "auth2",
                    user["email"],
                )
                raise

            return {
                "authenticated": False,
                "auth2_required": True,
                "access_expires_at": None,
                "refresh_expires_at": None,
                "user": None,
            }

        consumed = await verification_codes.consume(
            "auth2",
            user["email"],
            data.code,
        )

        if not consumed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired two-factor code",
            )
    elif data.code is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled for this user",
        )

    return await create_session(response, user)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    claims = await consume_refresh_token(request)

    user = await control_db.users.get(
        session,
        "user_id",
        claims["user_id"],
    )

    if user is None:
        clear_session_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token user does not exist",
        )

    session_data = await create_session(response, user)

    return {
        "authenticated": True,
        "access_expires_at": session_data["access_expires_at"],
        "refresh_expires_at": session_data["refresh_expires_at"],
    }


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    request: Request,
    response: Response,
):
    try:
        await consume_refresh_token(request)
    except HTTPException:
        pass

    # The refresh token was consumed atomically by consume_refresh_token.
    clear_session_cookies(response)
    return {"logged_out": True}
