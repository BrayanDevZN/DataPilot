"""Public routes for DataPilot transactional emails."""

from fastapi import APIRouter, HTTPException, status

from src.backend.controller.schema.sender import (
    Auth2EmailRequest,
    ChangePasswordEmailRequest,
    CreateAccountEmailRequest,
    SenderResponse,
)
from src.backend.service.manage import sender


router = APIRouter(prefix="/sender", tags=["sender"])


@router.post(
    "/create-account",
    response_model=SenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_create_account_email(
    data: CreateAccountEmailRequest,
):
    try:
        await sender.create_account(
            str(data.email),
            data.code,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {
        "sent": True,
        "type": "create_account",
        "email": data.email,
    }


@router.post(
    "/change-password",
    response_model=SenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_change_password_email(
    data: ChangePasswordEmailRequest,
):
    try:
        await sender.change_password(
            str(data.email),
            data.code,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {
        "sent": True,
        "type": "change_password",
        "email": data.email,
    }


@router.post(
    "/auth2",
    response_model=SenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_auth2_email(
    data: Auth2EmailRequest,
):
    try:
        await sender.auth2(
            str(data.email),
            data.code,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {
        "sent": True,
        "type": "auth2",
        "email": data.email,
    }
