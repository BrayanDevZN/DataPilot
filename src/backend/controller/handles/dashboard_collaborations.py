"""HTTP routes for dashboard collaborations."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.dashboard_collaborations import (
    DashboardCollaborationCreate,
    DashboardCollaborationRespond,
    DashboardCollaborationUpdate,
)
from src.backend.service.db.repository import control_repository


router = APIRouter(
    prefix="/dashboard-collaborations",
    tags=["dashboard-collaborations"],
)


async def _collaboration(
    session: AsyncSession,
    collaboration_id: int,
) -> dict[str, Any]:
    result = await control_repository(
        session,
    ).dashboard_collaborations.db.get(collaboration_id)

    if not result["found"]:
        raise HTTPException(
            status_code=404,
            detail="Collaboration not found",
        )

    return result["item"]


async def _owned_dashboard(
    session: AsyncSession,
    dashboard_id: int,
    user_id: int,
) -> None:
    result = await control_repository(session).dashboards.db.get(
        dashboard_id,
        filters={"user_id": user_id},
    )
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Dashboard not found")


@router.get("")
async def list_collaborations(
    dashboard_id: int | None = Query(None, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repository = control_repository(session)
    user_id = current_user["user_id"]

    owner_filters: dict[str, Any] = {"owner_user_id": user_id}
    collaborator_filters: dict[str, Any] = {
        "collaborator_user_id": user_id,
    }

    if dashboard_id is not None:
        owner_filters["dashboard_id"] = dashboard_id
        collaborator_filters["dashboard_id"] = dashboard_id

    owned = await repository.dashboard_collaborations.db.list(
        filters=owner_filters,
        limit=limit,
        offset=offset,
    )
    received = await repository.dashboard_collaborations.db.list(
        filters=collaborator_filters,
        limit=limit,
        offset=offset,
    )

    items = {
        item["id"]: item
        for item in [*owned["items"], *received["items"]]
    }

    return {
        "items": list(items.values()),
        "count": len(items),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_collaboration(
    data: DashboardCollaborationCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    dashboard_id = data.dashboard_id
    collaborator_user_id = data.collaborator_user_id
    permission = data.permission

    await _owned_dashboard(
        session,
        dashboard_id,
        current_user["user_id"],
    )

    collaborator = await control_repository(session).users.db.get(
        collaborator_user_id,
    )
    if not collaborator["found"]:
        raise HTTPException(
            status_code=404,
            detail="Collaborator user not found",
        )

    try:
        result = await control_repository(
            session,
        ).dashboard_collaborations.db.invite(
            dashboard_id,
            current_user["user_id"],
            collaborator_user_id,
            permission,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return result["item"]


@router.get("/{collaboration_id}")
async def get_collaboration(
    collaboration_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await _collaboration(session, collaboration_id)
    user_id = current_user["user_id"]

    if user_id not in (
        item["owner_user_id"],
        item["collaborator_user_id"],
    ):
        raise HTTPException(status_code=404, detail="Collaboration not found")

    return item


@router.patch("/{collaboration_id}")
async def update_collaboration(
    collaboration_id: int,
    data: DashboardCollaborationUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    permission = data.permission

    result = await control_repository(
        session,
    ).dashboard_collaborations.db.update(
        collaboration_id,
        {"permission": permission},
        filters={"owner_user_id": current_user["user_id"]},
    )

    if not result["updated"]:
        raise HTTPException(status_code=404, detail="Collaboration not found")

    return result["item"]


@router.post("/{collaboration_id}/respond")
async def respond_collaboration(
    collaboration_id: int,
    data: DashboardCollaborationRespond,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    response = data.response

    try:
        result = await control_repository(
            session,
        ).dashboard_collaborations.db.respond(
            collaboration_id,
            current_user["user_id"],
            response,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not result["updated"]:
        raise HTTPException(
            status_code=404,
            detail="Pending collaboration not found",
        )

    return result["item"]


@router.delete("/{collaboration_id}")
async def delete_collaboration(
    collaboration_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await control_repository(
        session,
    ).dashboard_collaborations.db.delete(
        collaboration_id,
        filters={"owner_user_id": current_user["user_id"]},
    )

    if not result["deleted"]:
        raise HTTPException(status_code=404, detail="Collaboration not found")

    return result
