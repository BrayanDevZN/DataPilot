"""Global logger: terminal and rotating logs/app.log, without sensitive arguments."""

import inspect
import logging
import sys
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import RLock


LOG_FILE = Path(__file__).resolve().parent / "app.log"
_configuration_lock = RLock()


def configure_logging() -> logging.Logger:
    """Configure once, including when modules are reloaded."""
    with _configuration_lock:
        configured = logging.getLogger("datapilot.backend")
        configured.setLevel(logging.INFO)
        configured.propagate = False
        if getattr(configured, "_datapilot_configured", False):
            return configured

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        configured.addHandler(file_handler)
        configured.addHandler(console_handler)
        configured._datapilot_configured = True
        return configured


logger = configure_logging()


def log_operation(function):
    """Log starts, successes and failures without arguments, results or secrets."""
    operation = f"{function.__module__}.{function.__qualname__}"

    if inspect.iscoroutinefunction(function):
        @wraps(function)
        async def async_wrapper(*args, **kwargs):
            logger.info("Iniciando %s", operation)
            try:
                result = await function(*args, **kwargs)
            except Exception as error:
                # Exception messages may contain URLs, passwords or authorization headers.
                logger.error("Falha em %s (%s)", operation, type(error).__name__)
                raise
            logger.info("Concluído %s", operation)
            return result
        return async_wrapper

    @wraps(function)
    def wrapper(*args, **kwargs):
        logger.info("Iniciando %s", operation)
        try:
            result = function(*args, **kwargs)
        except Exception as error:
            logger.error("Falha em %s (%s)", operation, type(error).__name__)
            raise
        logger.info("Concluído %s", operation)
        return result
    return wrapper
