"""Production-hardening utilities for the integration layer.

- ``ReadingCache`` — in-memory LRU cache keyed on a deterministic hash
  of the chart input. Readings are pure functions of input → safe to cache.
- ``StructuredLogger`` — JSON-line logger with consistent fields for
  trace correlation.
- Telemetry timer decorator for measuring adapter call latency.
"""

from __future__ import annotations

from app.integration.production.cache import (
    CacheKey,
    CacheStats,
    ReadingCache,
    default_cache,
    make_cache_key,
)
from app.integration.production.logging_util import (
    StructuredLogger,
    get_logger,
)
from app.integration.production.timing import (
    TimingContext,
    measure,
    timed,
)

__all__ = [
    "CacheKey",
    "CacheStats",
    "ReadingCache",
    "default_cache",
    "make_cache_key",
    "StructuredLogger",
    "get_logger",
    "TimingContext",
    "measure",
    "timed",
]
