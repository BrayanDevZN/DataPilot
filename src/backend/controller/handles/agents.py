"""Authenticated HTTP routes for DataPilot AI agents."""

import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.controller.dependencies import get_current_user, get_session
from src.backend.controller.schema.agents import (
    AgentTextResponse,
    ChatAgentRequest,
    ChatIntentAgentRequest,
    DashboardAgentResponse,
    DashboardAnalysisRequest,
    DashboardAnalysisResponse,
    DashboardGeneralAgentRequest,
    DashboardMultiGeneralAgentRequest,
    DashboardMultiSpecificAgentRequest,
    DashboardPlannerAgentRequest,
    DashboardSpecificAgentRequest,
    DataAgentRequest,
    MultiAnalysisAgentRequest,
)
from src.backend.service.agents import (
    ChatAgent,
    ChatIntentAgent,
    DashboardGeneralAgent,
    DashboardMultiGeneralAgent,
    DashboardMultiSpecificAgent,
    DashboardPlannerAgent,
    DashboardSpecificAgent,
    DataAgent,
    MultiAnalysisAgent,
)
from src.backend.service.db.repository import control_repository
from src.backend.service.manage import dashboard_pipeline
from src.backend.service.source_ingestion import agent_dataset_loader


router = APIRouter(prefix="/agents", tags=["agents"])

_chat_agent = ChatAgent()
_chat_intent_agent = ChatIntentAgent()
_multi_analysis_agent = MultiAnalysisAgent()
_dashboard_planner_agent = DashboardPlannerAgent()
_dashboard_general_agent = DashboardGeneralAgent()
_dashboard_specific_agent = DashboardSpecificAgent()
_dashboard_multi_general_agent = DashboardMultiGeneralAgent()
_dashboard_multi_specific_agent = DashboardMultiSpecificAgent()


def _history(messages) -> list[dict[str, Any]]:
    return [
        message.model_dump()
        for message in messages
    ]


@router.post("/chat", response_model=AgentTextResponse)
async def run_chat_agent(
    data: ChatAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _chat_agent.run(
        data.question,
        history=_history(data.history),
    )
    return {"output": output}


@router.post("/chat-intent", response_model=AgentTextResponse)
async def run_chat_intent_agent(
    data: ChatIntentAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _chat_intent_agent.run(
        data.question,
        history=_history(data.history),
    )
    return {"output": output}


@router.post(
    "/analysis",
    response_model=DashboardAnalysisResponse,
)
async def run_analysis_agent(
    data: DashboardAnalysisRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await dashboard_pipeline.run_analysis(
        data.analysis_id,
        user_id=current_user["user_id"],
        question=data.question,
        history=_history(data.history),
    )

    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard analysis context not found or expired",
        )

    return {
        "analysis_id": data.analysis_id,
        "output": output,
    }


@router.post("/multi-analysis", response_model=AgentTextResponse)
async def run_multi_analysis_agent(
    data: MultiAnalysisAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _multi_analysis_agent.run(
        question=data.question,
        charts=data.charts,
        interpretation=data.interpretation,
        history=_history(data.history),
    )
    return {"output": output}


@router.post("/data", response_model=AgentTextResponse)
async def run_data_agent(
    data: DataAgentRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    source = await control_repository(session).data_sources.db.get(
        data.data_source_id,
        filters={"user_id": current_user["user_id"]},
    )

    if not source["found"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found",
        )

    file_data = source["item"].get("file_data")
    if not isinstance(file_data, list) or not file_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data source does not contain analyzable data",
        )

    agent = DataAgent(file_data)

    try:
        output = await agent.run(
            data.question,
            history=_history(data.history),
        )
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return {"output": output}


@router.post(
    "/dashboard",
    response_model=DashboardAgentResponse,
)
async def run_dashboard_agent(
    prompt: Annotated[str | None, Form(max_length=20_000)] = None,
    data_source_id: Annotated[int | None, Form(gt=0)] = None,
    file: Annotated[UploadFile | None, File()] = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if (file is None) == (data_source_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one of file or data_source_id",
        )

    if file is not None:
        filename = file.filename or "dataset"

        try:
            content = await file.read()
            dataset, _ = await asyncio.to_thread(
                agent_dataset_loader.load,
                filename,
                content,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        finally:
            await file.close()
    else:
        source = await control_repository(
            session,
        ).data_sources.db.get(
            data_source_id,
            filters={
                "user_id": current_user["user_id"],
            },
        )

        if not source["found"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data source not found",
            )

        dataset = source["item"].get("file_data")

        if not isinstance(dataset, list) or not dataset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data source does not contain analyzable data",
            )

    try:
        return await dashboard_pipeline.generate(
            dataset,
            user_id=current_user["user_id"],
            prompt=prompt,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error


@router.post("/dashboard-planner", response_model=AgentTextResponse)
async def run_dashboard_planner_agent(
    data: DashboardPlannerAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _dashboard_planner_agent.run(
        data.user_prompt,
        data.dataset_schema,
    )
    return {"output": output}


@router.post("/dashboard-general", response_model=AgentTextResponse)
async def run_dashboard_general_agent(
    data: DashboardGeneralAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _dashboard_general_agent.run(
        plan=data.plan,
        schema=data.dataset_schema,
        metrics=data.metrics,
    )
    return {"output": output}


@router.post("/dashboard-specific", response_model=AgentTextResponse)
async def run_dashboard_specific_agent(
    data: DashboardSpecificAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _dashboard_specific_agent.run(
        user_prompt=data.user_prompt,
        plan=data.plan,
        schema=data.dataset_schema,
        metrics=data.metrics,
    )
    return {"output": output}


@router.post("/dashboard-multi-general", response_model=AgentTextResponse)
async def run_dashboard_multi_general_agent(
    data: DashboardMultiGeneralAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _dashboard_multi_general_agent.run(
        plan=data.plan,
        schema=data.dataset_schema,
        charts=data.charts,
    )
    return {"output": output}


@router.post("/dashboard-multi-specific", response_model=AgentTextResponse)
async def run_dashboard_multi_specific_agent(
    data: DashboardMultiSpecificAgentRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    output = await _dashboard_multi_specific_agent.run(
        user_prompt=data.user_prompt,
        plan=data.plan,
        schema=data.dataset_schema,
        charts=data.charts,
    )
    return {"output": output}
