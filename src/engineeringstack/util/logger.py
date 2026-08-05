"""Centralized logging utility for the Engineering Stack SDK.

Provides a singleton-pattern logger factory that writes to both console
and rotating log files. Thread-safe and duplicate-handler-proof.
"""

import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

_PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_PACKAGE_DIR))
_LOG_DIR: Final[str] = os.path.join(_PROJECT_ROOT, "logs")
_LOG_FILE: Final[str] = os.path.join(_LOG_DIR, "engineering_stack.log")

_LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(module)s.%(funcName)s:%(lineno)d | %(message)s"
)
_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB per log file
_BACKUP_COUNT: Final[int] = 5
_ENCODING: Final[str] = "utf-8"
_DEFAULT_LEVEL: Final[int] = logging.DEBUG

_lock: threading.Lock = threading.Lock()
_initialized_loggers: set[str] = set()


def _ensure_log_directory() -> None:
    """Create the logs/ directory if it does not already exist."""
    Path(_LOG_DIR).mkdir(parents=True, exist_ok=True)


def _create_console_handler() -> logging.StreamHandler:
    """Return a stderr console handler with standard format."""
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    return handler


def _create_file_handler() -> RotatingFileHandler:
    """Return a rotating file handler writing to logs/engineering_stack.log."""
    _ensure_log_directory()
    handler = RotatingFileHandler(
        filename=_LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding=_ENCODING,
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    return handler


def get_logger(name: str) -> logging.Logger:
    """Return a configured logging.Logger for *name*.

    Args:
        name: Logger name — pass __name__ from the calling module.

    Returns:
        A fully configured logging.Logger.
    """
    if name in _initialized_loggers:
        return logging.getLogger(name)

    with _lock:
        if name in _initialized_loggers:
            return logging.getLogger(name)

        logger = logging.getLogger(name)
        logger.setLevel(_DEFAULT_LEVEL)

        logger.propagate = False

        if not logger.handlers:
            logger.addHandler(_create_console_handler())
            try:
                logger.addHandler(_create_file_handler())
            except Exception:
                pass

        _initialized_loggers.add(name)

    return logger
