"""Structured JSON-line logger for the integration layer.

Each log entry is a single line of JSON with consistent fields:
- timestamp (ISO 8601)
- level (info/warning/error)
- logger (qualified name)
- event (short event tag)
- ... any extra kwargs

This is helpful for ingesting into Loki / Splunk / DataDog without
having to parse free-form text.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any


class StructuredLogger:
    """Thin wrapper around stdlib logging that emits one JSON line per call."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
        self._name = name

    def _emit(self, level: int, event: str, **fields: Any) -> None:
        record: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "level": logging.getLevelName(level).lower(),
            "logger": self._name,
            "event": event,
        }
        record.update(fields)
        # logger.log() takes the level + a message string. We pass the
        # JSON-serialised record as message so the existing logging
        # handlers don't need to know about our schema.
        self._logger.log(level, json.dumps(record, default=str))

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._emit(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self._emit(logging.ERROR, event, **fields)

    def debug(self, event: str, **fields: Any) -> None:
        self._emit(logging.DEBUG, event, **fields)


_logger_cache: dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Module-level singleton accessor (cheap and re-entrant)."""
    if name not in _logger_cache:
        _logger_cache[name] = StructuredLogger(name)
    return _logger_cache[name]
