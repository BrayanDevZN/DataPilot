"""Pydantic schemas for AI agent routes."""

from typing import Any, Literal

from pydantic import Field, model_validator

from .common import StrictSchema


class AgentHistoryMessage(StrictSchema):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)


class AgentTextResponse(StrictSchema):
    output: str


class ChatAgentRequest(StrictSchema):
    question: str = Field(min_length=1, max_length=20_000)
    history: list[AgentHistoryMessage] = Field(default_factory=list, max_length=200)


class ChatIntentAgentRequest(ChatAgentRequest):
    pass


class AnalysisAgentRequest(StrictSchema):
    question: str | None = Field(default=None, min_length=1, max_length=20_000)
    chart: dict[str, Any] | None = None
    interpretation: dict[str, Any] | None = None
    history: list[AgentHistoryMessage] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def require_analysis_input(self):
        if self.question is None and self.chart is None and self.interpretation is None:
            raise ValueError(
                "question, chart or interpretation must be provided"
            )
        return self


class MultiAnalysisAgentRequest(StrictSchema):
    question: str | None = Field(default=None, min_length=1, max_length=20_000)
    charts: list[dict[str, Any]] = Field(min_length=1, max_length=100)
    interpretation: dict[str, Any] | None = None
    history: list[AgentHistoryMessage] = Field(default_factory=list, max_length=200)


class DataAgentRequest(StrictSchema):
    data_source_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=20_000)
    history: list[AgentHistoryMessage] = Field(default_factory=list, max_length=200)


class DashboardPlannerAgentRequest(StrictSchema):
    user_prompt: str | None = Field(default=None, min_length=1, max_length=20_000)
    dataset_schema: dict[str, Any] = Field(alias="schema", min_length=1)


class DashboardGeneralAgentRequest(StrictSchema):
    plan: dict[str, Any]
    dataset_schema: dict[str, Any] = Field(alias="schema", min_length=1)
    metrics: list[dict[str, Any]] = Field(min_length=1, max_length=500)


class DashboardSpecificAgentRequest(DashboardGeneralAgentRequest):
    user_prompt: str = Field(min_length=1, max_length=20_000)


class DashboardMultiGeneralAgentRequest(StrictSchema):
    plan: dict[str, Any]
    dataset_schema: dict[str, Any] = Field(alias="schema", min_length=1)
    charts: list[dict[str, Any]] = Field(min_length=1, max_length=100)


class DashboardMultiSpecificAgentRequest(DashboardMultiGeneralAgentRequest):
    user_prompt: str = Field(min_length=1, max_length=20_000)
