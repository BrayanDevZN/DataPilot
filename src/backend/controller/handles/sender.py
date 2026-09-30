"""Public routes for DataPilot transactional emails."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_session
from src.backend.controller.session import (
    clear_auth2_user_cookie,
    read_auth2_user_cookie,
)
from src.backend.controller.schema.sender import (
    ChangePasswordEmailRequest,
    CreateAccountEmailRequest,
    SenderResponse,
)
from src.backend.infra.manage import settings
from src.backend.service.manage import control_db, sender, verification_codes


router = APIRouter(prefix="/sender", tags=["sender"])

CODE_TTL_SECONDS = 60


async def _issue_and_send(
    email_type: str,
    email: str,
    send,
) -> str:
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

    return code


def _sender_response(
    *,
    email_type: str,
    email: str,
    code: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "sent": True,
        "type": email_type,
        "email": email,
        "expires_in": CODE_TTL_SECONDS,
    }
    if settings.enviroiment == "test":
        payload["code"] = code
    return payload


@router.post(
    "/create-account",
    response_model=SenderResponse,
    response_model_exclude_none=True,
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

    code = await _issue_and_send(
        "create_account",
        email,
        sender.create_account,
    )

    return _sender_response(
        email_type="create_account",
        email=email,
        code=code,
    )


@router.post(
    "/change-password",
    response_model=SenderResponse,
    response_model_exclude_none=True,
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

    code = await _issue_and_send(
        "change_password",
        email,
        sender.change_password,
    )

    return _sender_response(
        email_type="change_password",
        email=email,
        code=code,
    )


@router.post(
    "/auth2",
    response_model=SenderResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_auth2_email(
    request: Request,
    response: Response,
):
    try:
        claims = read_auth2_user_cookie(request)
    except HTTPException:
        clear_auth2_user_cookie(response)
        raise

    email = str(claims["email"]).strip().lower()

    code = await _issue_and_send(
        "auth2",
        email,
        sender.auth2,
    )

    clear_auth2_user_cookie(response)

    return _sender_response(
        email_type="auth2",
        email=email,
        code=code,
    )
