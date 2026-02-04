"""
Logging configuration for AI Evolution Platform.

Initializes structured logging using structlog with support for:
- JSON and console (colored) output formats
- Context variables for request-scoped metadata
- Environment-based configuration
- Optional file logging
"""

import logging
import os
import sys
from typing import Any

import structlog
from structlog.types import Processor


def _get_log_level() -> str:
    """Get log level from environment variable."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def _get_log_format() -> str:
    """Get log format from environment variable."""
    return os.getenv("LOG_FORMAT", "console").lower()


def _should_export_logs() -> bool:
    """Check if file logging should be enabled."""
    return os.getenv("EXPORT_LOGS", "false").lower() == "true"


def _get_log_dir() -> str:
    """Get log directory from environment variable."""
    return os.getenv("LOG_DIR", "logs")


def _get_log_file() -> str:
    """Get log filename from environment variable."""
    return os.getenv("LOG_FILE", "ai-evolution.log")


def _configure_standard_logging() -> None:
    """Configure Python's standard logging module."""
    log_level = _get_log_level()
    
    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level, logging.INFO),
    )
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Set specific logger levels from environment
    autogen_log_level = os.getenv("AUTOGEN_LOG_LEVEL", "WARNING").upper()
    logging.getLogger("autogen").setLevel(getattr(logging, autogen_log_level, logging.WARNING))
    
    # Suppress Anthropic SDK logs
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    
    # Suppress OpenAI SDK logs (if present)
    logging.getLogger("openai").setLevel(logging.WARNING)


def _get_processors() -> list[Processor]:
    """Get structlog processors based on configuration."""
    processors: list[Processor] = [
        # Filter by log level
        structlog.stdlib.filter_by_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add log level
        structlog.stdlib.add_log_level,
        # Merge context variables
        structlog.contextvars.merge_contextvars,
        # Add timestamps
        structlog.processors.TimeStamper(fmt="iso"),
        # Add stack info
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Add dict tracebacks
        structlog.processors.dict_tracebacks,
    ]
    
    # Add renderer based on format
    log_format = _get_log_format()
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Colored console output
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )
    
    return processors


def _configure_file_logging() -> None:
    """Configure file logging if enabled."""
    if not _should_export_logs():
        return
    
    from aieval.logging_utils import configure_file_logging as _configure
    
    log_dir = _get_log_dir()
    log_file = _get_log_file()
    _configure(log_dir, log_file)


def initialize_logging() -> None:
    """
    Initialize logging configuration.
    
    This should be called at application startup.
    """
    # Configure standard logging first
    _configure_standard_logging()
    
    # Configure structlog
    structlog.configure(
        processors=_get_processors(),
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure file logging if enabled
    _configure_file_logging()
    
    # Log initialization
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging initialized",
        log_level=_get_log_level(),
        log_format=_get_log_format(),
        file_logging=_should_export_logs(),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structlog logger instance.
    
    Args:
        name: Logger name (defaults to calling module name)
        
    Returns:
        Configured structlog logger
    """
    if name is None:
        import inspect
        try:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                name = frame.f_back.f_globals.get("__name__", __name__)
            else:
                name = __name__
        except Exception:
            # Fallback if inspection fails
            name = __name__
    
    return structlog.get_logger(name)

