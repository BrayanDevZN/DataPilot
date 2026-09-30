"""HTTP route for sending DataPilot transactional emails."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.backend.controller.dependencies import get_current_user

from src.backend.controller.schema.sender import SenderRequest, SenderResponse
from src.backend.service.manage import sender


router = APIRouter(prefix="/sender", tags=["sender"])


@router.post(
    "/",
    response_model=SenderResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_email(
    data: SenderRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    if str(data.email).lower() != str(current_user["email"]).lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transactional emails can only be sent to the authenticated user",
        )

    handlers = {
        "create_account": sender.create_account,
        "change_password": sender.change_password,
        "auth2": sender.auth2,
    }

    try:
        await handlers[data.template](str(data.email), data.code)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return {
        "sent": True,
        "template": data.template,
        "email": data.email,
    }
