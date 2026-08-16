"""Centralized logging utility for the Engineering Stack SDK.

By default, the SDK suppresses console logging for end users and attaches a NullHandler
so it integrates cleanly into standard Python applications without unsolicited console noise.

Developers can enable verbose logging by:
1. Setting the environment variable `ENGINEERINGSTACK_DEBUG=1` or `ENGINEERINGSTACK_LOG_LEVEL=DEBUG` / `INFO`
2. Calling `engineeringstack.enable_logging()` or `enable_logging(level=logging.DEBUG, to_console=True)`
3. Passing `EngineeringStack(verbose=True)` or `EngineeringStack(enable_logging=True)`
"""

import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final, Optional

_PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_PACKAGE_DIR))
_DEFAULT_LOG_DIR: Final[str] = os.path.join(_PROJECT_ROOT, "logs")
_DEFAULT_LOG_FILE: Final[str] = os.path.join(_DEFAULT_LOG_DIR, "engineering_stack.log")

_LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(module)s.%(funcName)s:%(lineno)d | %(message)s"
)
_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB per log file
_BACKUP_COUNT: Final[int] = 5
_ENCODING: Final[str] = "utf-8"

_lock: threading.Lock = threading.Lock()
_initialized_loggers: dict[str, logging.Logger] = {}
_logging_enabled: bool = False


def _is_debug_env_set() -> bool:
    """Check if developer debug mode is enabled via environment variables."""
    return os.environ.get("ENGINEERINGSTACK_DEBUG", "").lower() in ("1", "true", "yes", "on") or bool(
        os.environ.get("ENGINEERINGSTACK_LOG_LEVEL", "").strip()
    )


def _get_env_log_level() -> int:
    """Get log level configured in environment variables, defaulting to WARNING if not in debug mode."""
    env_level = os.environ.get("ENGINEERINGSTACK_LOG_LEVEL", "").upper().strip()
    if env_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        return getattr(logging, env_level)
    if os.environ.get("ENGINEERINGSTACK_DEBUG", "").lower() in ("1", "true", "yes", "on"):
        return logging.DEBUG
    return logging.WARNING


def _create_console_handler(level: int = logging.DEBUG) -> logging.StreamHandler:
    """Return a stderr console handler with standard format."""
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    return handler


def _create_file_handler(
    log_file: Optional[str] = None,
    level: int = logging.DEBUG,
) -> Optional[RotatingFileHandler]:
    """Return a rotating file handler writing to log_file or logs/engineering_stack.log."""
    target_file = log_file or _DEFAULT_LOG_FILE
    try:
        Path(os.path.dirname(target_file)).mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            filename=target_file,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding=_ENCODING,
        )
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        return handler
    except Exception:
        return None


def enable_logging(
    level: int = logging.DEBUG,
    to_console: bool = True,
    to_file: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """Enable detailed logging for developers/debugging."""
    global _logging_enabled
    with _lock:
        _logging_enabled = True
        for name, logger in _initialized_loggers.items():
            logger.setLevel(level)
            logger.handlers.clear()
            if to_console:
                logger.addHandler(_create_console_handler(level=level))
            if to_file:
                fh = _create_file_handler(log_file=log_file, level=level)
                if fh:
                    logger.addHandler(fh)


def disable_logging() -> None:
    """Disable/silence detailed logging (returns to NullHandler mode)."""
    global _logging_enabled
    with _lock:
        _logging_enabled = False
        for name, logger in _initialized_loggers.items():
            logger.setLevel(logging.WARNING)
            logger.handlers.clear()
            logger.addHandler(logging.NullHandler())


def get_logger(name: str) -> logging.Logger:
    """Return a configured logging.Logger for *name*.

    By default, attaches a NullHandler to remain silent for library consumers.
    If developer debug mode is active (via environment or enable_logging()),
    configures active console/file handlers.

    Args:
        name: Logger name — pass __name__ from the calling module.

    Returns:
        A fully configured logging.Logger.
    """
    if name in _initialized_loggers:
        return _initialized_loggers[name]

    with _lock:
        if name in _initialized_loggers:
            return _initialized_loggers[name]

        logger = logging.getLogger(name)

        if _logging_enabled or _is_debug_env_set():
            level = _get_env_log_level() if not _logging_enabled else logger.level or logging.DEBUG
            logger.setLevel(level)
            logger.propagate = False
            if not logger.handlers:
                logger.addHandler(_create_console_handler(level=level))
                fh = _create_file_handler(level=level)
                if fh:
                    logger.addHandler(fh)
        else:
            logger.setLevel(logging.WARNING)
            logger.propagate = False
            if not logger.handlers:
                logger.addHandler(logging.NullHandler())

        _initialized_loggers[name] = logger
        return logger
