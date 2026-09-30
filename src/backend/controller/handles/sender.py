"""Public routes for DataPilot transactional emails."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_session
from src.backend.controller.schema.sender import (
    Auth2EmailRequest,
    ChangePasswordEmailRequest,
    CreateAccountEmailRequest,
    SenderResponse,
)
from src.backend.service.manage import control_db, sender, verification_codes


router = APIRouter(prefix="/sender", tags=["sender"])

CODE_TTL_SECONDS = 60


async def _issue_and_send(
    email_type: str,
    email: str,
    send,
) -> None:
    code = await verification_codes.issue(
        email_type,
        email,
        expire=None,
    )

    try:
        await send(email, code)
    except Exception:
        await verification_codes.delete(email_type, email)
        raise


@router.post(
    "/create-account",
    response_model=SenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_create_account_email(
    data: CreateAccountEmailRequest,
    session: AsyncSession = Depends(get_session),
):
    email = str(data.email).strip().lower()

    if await control_db.users.get(session, "email", email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    await _issue_and_send(
        "create_account",
        email,
        sender.create_account,
    )

    return {
        "sent": True,
        "type": "create_account",
        "email": email,
        "expires_in": CODE_TTL_SECONDS,
    }


@router.post(
    "/change-password",
    response_model=SenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_change_password_email(
    data: ChangePasswordEmailRequest,
    session: AsyncSession = Depends(get_session),
):
    email = str(data.email).strip().lower()
    user = await control_db.users.get(session, "email", email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await _issue_and_send(
        "change_password",
        email,
        sender.change_password,
    )

    return {
        "sent": True,
        "type": "change_password",
        "email": email,
        "expires_in": CODE_TTL_SECONDS,
    }


@router.post(
    "/auth2",
    response_model=SenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_auth2_email(
    data: Auth2EmailRequest,
    session: AsyncSession = Depends(get_session),
):
    email = str(data.email).strip().lower()
    user = await control_db.users.get(session, "email", email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.get("auth2", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled for this user",
        )

    await _issue_and_send(
        "auth2",
        email,
        sender.auth2,
    )

    return {
        "sent": True,
        "type": "auth2",
        "email": email,
        "expires_in": CODE_TTL_SECONDS,
    }
