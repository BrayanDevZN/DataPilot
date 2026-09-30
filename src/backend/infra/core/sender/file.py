"""Load HTML email templates relative to the sender core package."""

from pathlib import Path

from src.backend.logs.log import logger, log_operation


class EmailFiles:
    @log_operation
    def __init__(self) -> None:
        self._directory = Path(__file__).resolve().parent

    @log_operation
    def read(self) -> dict[str, str]:
        templates = {
            name: (self._directory / f"{name}.html").read_text(encoding="utf-8")
            for name in ("create_account", "change_password")
        }
        logger.info("Templates HTML de e-mail carregados: %s", len(templates))
        return templates
