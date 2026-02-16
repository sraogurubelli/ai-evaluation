"""
File logging utilities for AI Evolution Platform.

Provides custom JsonFormatter for file output with enhanced metadata.
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for file logging.

    Features:
    - ISO timestamps with milliseconds
    - ANSI escape sequence removal
    - Full exception info
    - Module/function/line number tracking
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json

        # Remove ANSI escape sequences
        message = record.getMessage()
        message = re.sub(r"\x1b\[[0-9;]*m", "", message)

        # Build log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            log_entry["exception_type"] = (
                record.exc_info[0].__name__ if record.exc_info[0] else None
            )

        # Add extra fields from record
        if hasattr(record, "extra"):
            log_entry.update(record.extra)

        # Add any additional attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                if not key.startswith("_"):
                    log_entry[key] = value

        return json.dumps(log_entry, default=str)


def configure_file_logging(log_dir: str = "logs", log_file: str = "ai-evolution.log") -> None:
    """
    Configure file logging with custom JSON formatter.

    Args:
        log_dir: Directory for log files
        log_file: Log filename
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Full path to log file
    log_file_path = log_path / log_file

    # Create file handler
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Capture all levels in file

    # Set custom formatter
    formatter = JsonFormatter()
    file_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Also configure structlog file handler
    structlog_file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    structlog_file_handler.setLevel(logging.DEBUG)
    structlog_file_handler.setFormatter(formatter)

    # Add to structlog logger
    structlog_logger = logging.getLogger("structlog")
    structlog_logger.addHandler(structlog_file_handler)

    # Log file location (use standard logging since structlog may not be configured yet)
    import logging as std_logging

    std_logger = std_logging.getLogger(__name__)
    std_logger.info(
        f"File logging configured: {log_file_path}",
        extra={"log_file": str(log_file_path), "log_dir": log_dir},
    )
