"""HTTP routes for collaboration notifications."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.collaboration_notifications import (
    CollaborationNotificationCreate,
    CollaborationNotificationUpdate,
)
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db


router = APIRouter(
    prefix="/collaboration-notifications",
    tags=["collaboration-notifications"],
)


async def _owned_notification(
    session: AsyncSession,
    notification_id: int,
    user_id: int,
) -> dict[str, Any]:
    result = await control_repository(
        session,
    ).collaboration_notifications.db.get(
        notification_id,
        filters={"user_id": user_id},
    )

    if not result["found"]:
        raise HTTPException(status_code=404, detail="Notification not found")

    return result["item"]


@router.get("/")
async def list_notifications(
    limit: int = Query(30, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await control_repository(
        session,
    ).collaboration_notifications.db.list_by_user(
        current_user["user_id"],
        limit=limit,
        offset=offset,
    )


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_notification(
    data: CollaborationNotificationCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_dump()
    payload["user_id"] = current_user["user_id"]
    payload["is_read"] = False

    try:
        return await control_db.collaboration_notifications.create(
            session,
            payload,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/read-all")
async def mark_all_notifications_read(
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await control_repository(
        session,
    ).collaboration_notifications.db.mark_all_read(
        current_user["user_id"],
    )


@router.get("/{notification_id}")
async def get_notification(
    notification_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _owned_notification(
        session,
        notification_id,
        current_user["user_id"],
    )


@router.patch("/")
async def update_notification(
    notification_id: int = Query(..., gt=0),
    data: CollaborationNotificationUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if data.is_read is not True:
        raise HTTPException(
            status_code=400,
            detail="Only marking a notification as read is supported",
        )

    result = await control_repository(
        session,
    ).collaboration_notifications.db.mark_read(
        notification_id,
        current_user["user_id"],
    )

    if not result["updated"]:
        raise HTTPException(status_code=404, detail="Notification not found")

    return result["item"]


@router.delete("/")
async def delete_notification(
    notification_id: int = Query(..., gt=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await control_repository(
        session,
    ).collaboration_notifications.db.delete(
        notification_id,
        filters={"user_id": current_user["user_id"]},
    )

    if not result["deleted"]:
        raise HTTPException(status_code=404, detail="Notification not found")

    return result
