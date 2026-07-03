"""
Structured logging configuration.

Foundation setup only (Milestone 0): a JSON log formatter and log-level
wiring per docs/System_Architecture.md Section 10. Per-action audit event
logging (result approval, payment recording, etc.) is added alongside the
business modules that generate those events, not here.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "extra_fields", {}).items():
            payload[key] = value
        return json.dumps(payload)


def configure_logging(log_level: str = "INFO") -> None:
    """Idempotent: safe to call once at application startup."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers at DEBUG; keep our own app logger verbose.
    logging.getLogger("uvicorn.access").setLevel("WARNING")
