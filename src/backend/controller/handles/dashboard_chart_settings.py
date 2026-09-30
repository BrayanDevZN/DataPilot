"""HTTP routes for dashboard chart settings."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.dashboard_chart_settings import (
    DashboardChartSettingsSave,
    DashboardChartSettingsUpdate,
)
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import control_db


router = APIRouter(
    prefix="/dashboard-chart-settings",
    tags=["dashboard-chart-settings"],
)


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


async def _owned_setting(
    session: AsyncSession,
    setting_id: int,
    user_id: int,
) -> dict[str, Any]:
    result = await control_repository(
        session,
    ).dashboard_chart_settings.db.get(setting_id)

    if not result["found"]:
        raise HTTPException(status_code=404, detail="Chart setting not found")

    await _owned_dashboard(
        session,
        result["item"]["dashboard_id"],
        user_id,
    )
    return result["item"]


@router.get("")
async def list_chart_settings(
    dashboard_id: int = Query(..., ge=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_dashboard(
        session,
        dashboard_id,
        current_user["user_id"],
    )
    return await control_repository(
        session,
    ).dashboard_chart_settings.db.list(
        filters={"dashboard_id": dashboard_id},
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def save_chart_settings(
    data: DashboardChartSettingsSave,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    payload = data.model_dump()
    dashboard_id = payload.pop("dashboard_id")
    chart_id = payload.pop("chart_id")

    await _owned_dashboard(
        session,
        dashboard_id,
        current_user["user_id"],
    )

    try:
        result = await control_repository(
            session,
        ).dashboard_chart_settings.db.save(
            dashboard_id,
            payload,
            chart_id=chart_id,
        )
    except (LookupError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return result["item"]


@router.get("/{setting_id}")
async def get_chart_setting(
    setting_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _owned_setting(
        session,
        setting_id,
        current_user["user_id"],
    )


@router.patch("/{setting_id}")
async def update_chart_setting(
    setting_id: int,
    data: DashboardChartSettingsUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_setting(session, setting_id, current_user["user_id"])

    payload = data.model_dump(exclude_unset=True)

    if not payload:
        raise HTTPException(status_code=400, detail="No editable fields provided")

    result = await control_db.dashboard_chart_settings.update(
        session,
        setting_id,
        payload,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Chart setting not found")
    return result


@router.delete("/{setting_id}")
async def delete_chart_setting(
    setting_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await _owned_setting(session, setting_id, current_user["user_id"])
    return await control_db.dashboard_chart_settings.delete(
        session,
        setting_id,
    )
