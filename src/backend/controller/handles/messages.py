"""HTTP routes for conversation messages."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.messages import MessageCreate, MessageUpdate
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db


router = APIRouter(prefix="/messages", tags=["messages"])


async def _owned_message(
    session: AsyncSession,
    message_id: int,
    user_id: int,
) -> dict[str, Any]:
    repository = control_repository(session)
    result = await repository.messages.db.get(message_id)

    if not result["found"]:
        raise HTTPException(status_code=404, detail="Message not found")

    conversation = await repository.conversations.db.get_owned(
        result["item"]["conversation_id"],
        user_id,
    )
    if not conversation["found"]:
        raise HTTPException(status_code=404, detail="Message not found")

    return result["item"]


@router.get("/")
async def list_messages(
    conversation_id: int = Query(..., ge=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await control_repository(
        session,
    ).messages.db.list_by_conversation(
        conversation_id,
        current_user["user_id"],
        limit=limit,
        offset=offset,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_message(
    data: MessageCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    conversation_id = data.conversation_id
    role = data.role
    content = data.content

    try:
        result = await control_repository(
            session,
        ).messages.db.append(
            conversation_id,
            current_user["user_id"],
            role,
            content,
        )
    except (LookupError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return result["item"]


@router.get("/{message_id}")
async def get_message(
    message_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _owned_message(
        session,
        message_id,
        current_user["user_id"],
    )


@router.patch("/")
async def update_message(
    message_id: int = Query(..., gt=0),
    data: MessageUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_message(session, message_id, current_user["user_id"])

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No editable fields provided")

    result = await control_db.messages.update(session, message_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return result


@router.delete("/")
async def delete_message(
    message_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_message(session, message_id, current_user["user_id"])
    return await control_db.messages.delete(session, message_id)
