"""OpenAI function tool for deterministic dataframe analysis."""

from typing import Any

from src.backend.utils.manage import DataToolsManager


ANALYTICS_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "analyze_data",
    "description": (
        "Executa uma operação analítica determinística sobre o dataset atual. "
        "Use esta tool para contagem, agrupamento, série temporal, scatter, KPI, "
        "tabela, filtros e agregações. Use somente colunas existentes no dataset."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "groupby",
                    "count",
                    "time_groupby",
                    "scatter",
                    "kpi",
                    "table",
                ],
                "description": "Operação analítica a executar.",
            },
            "group_by": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Colunas usadas para agrupamento.",
            },
            "metric": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Colunas numéricas usadas como métricas.",
            },
            "aggregation": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "sum",
                        "mean",
                        "avg",
                        "count",
                        "max",
                        "min",
                        "median",
                        "none",
                    ],
                },
                "description": "Agregação aplicada às métricas.",
            },
            "x": {
                "type": ["string", "null"],
                "description": "Coluna do eixo X quando aplicável.",
            },
            "y": {
                "type": ["string", "null"],
                "description": "Coluna do eixo Y quando aplicável.",
            },
            "time_column": {
                "type": ["string", "null"],
                "description": "Coluna temporal usada em time_groupby.",
            },
            "time_freq": {
                "type": "string",
                "enum": ["D", "W", "M", "Q", "Y"],
                "description": "Frequência temporal.",
            },
            "filters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "column": {"type": "string"},
                        "operator": {
                            "type": "string",
                            "enum": ["equals", "not_equals", "contains", "in"],
                        },
                        "value": {},
                    },
                    "required": ["column", "operator", "value"],
                    "additionalProperties": False,
                },
                "description": "Filtros aplicados antes da operação.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 500,
                "description": "Limite máximo de linhas retornadas.",
            },
            "sort": {
                "type": "string",
                "enum": ["asc", "desc", "none"],
                "description": "Ordenação do resultado.",
            },
            "title": {
                "type": "string",
                "description": "Título opcional para identificar o resultado.",
            },
        },
        "required": ["operation"],
        "additionalProperties": False,
    },
}


class AgentDataTools:
    def __init__(
        self,
        data,
        *,
        spark_threshold: int = 100_000,
    ) -> None:
        self.manager = DataToolsManager(
            data,
            spark_threshold=spark_threshold,
        )
        self.tool = self.manager.get_tool()
        self.data = self.manager.get_data()

    @property
    def definition(self) -> dict[str, Any]:
        return ANALYTICS_TOOL

    def execute(self, arguments: dict[str, Any]) -> list[dict]:
        return self.tool.execute(
            self.data,
            arguments,
        )
