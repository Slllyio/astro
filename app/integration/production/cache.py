"""In-memory LRU cache for integrated readings.

Readings are deterministic functions of the chart input — same (dob, time,
tz, lat, lon, enrich) always produces the same output. So we can safely
cache.

This module ships a per-process LRU keyed on a SHA-256 of the canonical
input form. The cache is a singleton via ``default_cache()``; tests
inject a fresh one to avoid cross-test pollution.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections import OrderedDict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


_DEFAULT_CAPACITY = 256


class CacheKey(BaseModel):
    """Canonical key for cache lookup."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dob: str
    time: str
    tz: str
    lat: float
    lon: float
    enrich: bool = False
    extras: str = ""  # opaque tag for layer-combos ("dkp+gap" etc.)

    def fingerprint(self) -> str:
        """Stable SHA-256 hex digest of the canonical form."""
        canonical = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CacheStats(BaseModel):
    """Snapshot of cache stats."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capacity: int
    size: int
    hits: int
    misses: int
    evictions: int
    hit_rate: float = Field(ge=0.0, le=1.0)


def make_cache_key(
    *, dob: str, time: str, tz: str, lat: float, lon: float,
    enrich: bool = False, extras: str = "",
) -> CacheKey:
    """Helper builder so callers don't need to import the class."""
    return CacheKey(
        dob=dob, time=time, tz=tz, lat=float(lat), lon=float(lon),
        enrich=bool(enrich), extras=extras,
    )


class ReadingCache:
    """Thread-safe LRU cache for reading dicts.

    Bounded by ``capacity`` (default 256). Eviction is least-recently-used.
    """

    def __init__(self, capacity: int = _DEFAULT_CAPACITY) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._store: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: CacheKey) -> dict[str, Any] | None:
        fp = key.fingerprint()
        with self._lock:
            value = self._store.get(fp)
            if value is None:
                self._misses += 1
                return None
            # Move to end (most-recently-used).
            self._store.move_to_end(fp)
            self._hits += 1
            return value

    def put(self, key: CacheKey, value: dict[str, Any]) -> None:
        fp = key.fingerprint()
        with self._lock:
            if fp in self._store:
                self._store.move_to_end(fp)
                self._store[fp] = value
                return
            self._store[fp] = value
            while len(self._store) > self._capacity:
                self._store.popitem(last=False)
                self._evictions += 1

    def get_or_compute(
        self, key: CacheKey, compute_fn,
    ) -> tuple[dict[str, Any], bool]:
        """Get cached value or compute + cache. Returns (value, was_hit)."""
        existing = self.get(key)
        if existing is not None:
            return existing, True
        value = compute_fn()
        if not isinstance(value, dict):
            raise TypeError(
                f"compute_fn must return dict, got {type(value).__name__}"
            )
        self.put(key, value)
        return value, False

    def stats(self) -> CacheStats:
        with self._lock:
            denom = self._hits + self._misses
            rate = self._hits / denom if denom > 0 else 0.0
            return CacheStats(
                capacity=self._capacity,
                size=len(self._store),
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                hit_rate=rate,
            )

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0


# Module-level singleton.
_default_cache: ReadingCache | None = None
_default_cache_lock = threading.Lock()


def default_cache() -> ReadingCache:
    """Return the module-level singleton ReadingCache."""
    global _default_cache
    if _default_cache is None:
        with _default_cache_lock:
            if _default_cache is None:
                _default_cache = ReadingCache()
    return _default_cache
