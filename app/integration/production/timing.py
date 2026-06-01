"""Telemetry timing helpers.

- ``measure()`` context manager that records elapsed ms.
- ``timed`` decorator that wraps a sync or async function and emits a
  structured-log line on completion.
"""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable

from app.integration.production.logging_util import get_logger


class TimingContext:
    """Records elapsed time within a ``with`` block."""

    def __init__(self, label: str = "") -> None:
        self.label = label
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "TimingContext":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *exc_info) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000


def measure(label: str = "") -> TimingContext:
    """Factory for a TimingContext — pure sugar."""
    return TimingContext(label)


def timed(label: str | None = None) -> Callable:
    """Decorator that emits a structured-log line with elapsed_ms.

    Works on both sync and async functions. ``label`` defaults to the
    function's qualified name."""

    def _decorator(fn: Callable) -> Callable:
        event_name = label or fn.__qualname__
        logger = get_logger("app.integration.timing")

        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
                t0 = time.perf_counter()
                try:
                    result = await fn(*args, **kwargs)
                except Exception as exc:
                    logger.error(
                        "timed.error",
                        function=event_name,
                        error_type=type(exc).__name__,
                        elapsed_ms=int((time.perf_counter() - t0) * 1000),
                    )
                    raise
                logger.info(
                    "timed.complete",
                    function=event_name,
                    elapsed_ms=int((time.perf_counter() - t0) * 1000),
                )
                return result

            return _async_wrapper

        @functools.wraps(fn)
        def _sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                logger.error(
                    "timed.error",
                    function=event_name,
                    error_type=type(exc).__name__,
                    elapsed_ms=int((time.perf_counter() - t0) * 1000),
                )
                raise
            logger.info(
                "timed.complete",
                function=event_name,
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )
            return result

        return _sync_wrapper

    return _decorator
