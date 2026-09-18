"""
Structured JSON Logging Module.

Provides uniform JSON-formatted log output for cloud-native observability.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured application logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
            "process_id": record.process,
        }

        # Include custom context attributes if injected
        for key in (
            "request_id",
            "path",
            "method",
            "status_code",
            "duration_ms",
            "client_ip",
            "model_version",
            "prediction",
        ):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure root and standard loggers with structured formatting."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
            )
        )

    root_logger.addHandler(handler)

    # Reconfigure uvicorn loggers to harmonize output
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(uvicorn_logger_name)
        u_logger.handlers = [handler]
        u_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Obtain named logger instance."""
    return logging.getLogger(name)
