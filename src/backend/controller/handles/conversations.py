"""HTTP routes for user conversations."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.conversations import ConversationCreate, ConversationUpdate
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db


router = APIRouter(prefix="/conversations", tags=["conversations"])


async def _owned(
    session: AsyncSession,
    conversation_id: int,
    user_id: int,
) -> dict[str, Any]:
    result = await control_repository(
        session,
    ).conversations.db.get_owned(conversation_id, user_id)

    if not result["found"]:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return result["item"]


@router.get("/")
async def list_conversations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await control_repository(
        session,
    ).conversations.db.list_by_user(
        current_user["user_id"],
        limit=limit,
        offset=offset,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = {
        "user_id": current_user["user_id"],
        "title": data.title,
    }

    return await control_db.conversations.create(session, payload)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _owned(
        session,
        conversation_id,
        current_user["user_id"],
    )


@router.patch("/")
async def update_conversation(
    data: ConversationUpdate,
    conversation_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned(session, conversation_id, current_user["user_id"])

    payload = data.model_dump()

    result = await control_db.conversations.update(
        session,
        conversation_id,
        payload,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_conversation(
    conversation_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned(session, conversation_id, current_user["user_id"])
    return await control_db.conversations.delete(
        session,
        conversation_id,
    )
