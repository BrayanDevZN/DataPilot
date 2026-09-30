"""Read versioned agent prompts stored as Markdown files."""

from pathlib import Path

from src.backend.logs.log import logger, log_operation


class PromptFiles:
    NAMES = (
        "interpreter_dashboard_plan",
        "interpreter_chat",
        "interpreter_analysis",
        "generator_chat",
        "generator_analysis",
        "generator_analysis_multi",
        "generator_dashboard_general",
        "generator_dashboard_specific",
        "generator_dashboard_multi_general",
        "generator_dashboard_multi_specific",
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

    def __getattr__(self, name: str) -> str:
        if name in self.NAMES:
            return self.read(name)
        raise AttributeError(name)
