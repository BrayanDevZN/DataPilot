"""Read versioned agent prompts stored as Markdown files."""

from pathlib import Path

from src.backend.logs.log import logger, log_operation


class PromptFiles:
    NAMES = (
        "dashboard_planner",
        "chart_interpreter",
        "chat_agent",
        "dashboard_analysis",
        "dashboard_multi_analysis",
    )

    @log_operation
    def __init__(self) -> None:
        self._directory = Path(__file__).resolve().parent

    @log_operation
    def read(self, name: str) -> str:
        if name not in self.NAMES:
            raise ValueError(f"Prompt desconhecido: {name}")
        content = (self._directory / f"{name}.md").read_text(encoding="utf-8")
        logger.info("Prompt carregado: %s", name)
        return content

    @log_operation
    def read_all(self) -> dict[str, str]:
        return {name: self.read(name) for name in self.NAMES}

    @property
    def dashboard_planner(self) -> str:
        return self.read("dashboard_planner")

    @property
    def chart_interpreter(self) -> str:
        return self.read("chart_interpreter")

    @property
    def chat_agent(self) -> str:
        return self.read("chat_agent")

    @property
    def dashboard_analysis(self) -> str:
        return self.read("dashboard_analysis")

    @property
    def dashboard_multi_analysis(self) -> str:
        return self.read("dashboard_multi_analysis")
