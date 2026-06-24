"""In-process memoization for the expensive enrichment layers of /forecast.

The forecast engine is cheap (~1s for 30 days). The expensive layers are:

* RAG citation lookups: ~50ms each, 30 events × 2 citations = ~3s
* LLM daily summaries: 1-3s each, 5-30 distinct days = 5-90s

Both are **deterministic for a fixed input**. A daily summary depends only
on the events of that day; a citation depends only on the event description
+ topic filter. So an in-process dict cache keyed on a stable hash of
those inputs gives huge speed-ups for repeat calls from the same client
(refreshing /forecast/page after a network blip, two browser tabs open,
etc.) AND for the common pattern where /forecast and /almanac both run
for overlapping date windows.

No external dependency (Redis, etc.); the cache lives in process memory.
Reset on app restart. Bounded by a simple LRU eviction so a server that
runs for weeks doesn't grow unbounded.

NB: the cache is NOT thread-safe for writes. FastAPI runs request handlers
on a single event loop; the only concurrency that matters is multiple
``asyncio.to_thread`` calls, and Python's dict mutations are atomic for
single ops — so reads + writes are race-safe enough for this usage. If we
ever move to a multi-worker setup, swap in ``functools.lru_cache`` on
hashable args or a real cache backend.
"""
from __future__ import annotations

import hashlib
import json
import logging
from collections import OrderedDict
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LRUCache:
    """Tiny ordered-dict LRU. Move-to-end on hit, pop-front on overflow.

    Sized for the forecast usage pattern: ~30 distinct days per request,
    ~100 distinct events. A 1000-entry cap covers ~30 sequential 30-day
    horizon requests with no eviction.
    """

    def __init__(self, maxsize: int = 1000) -> None:
        self._maxsize = maxsize
        self._store: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            self.misses += 1
            return None
        self.hits += 1
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.move_to_end(key)
            self._store[key] = value
            return
        self._store[key] = value
        if len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def stats(self) -> dict[str, Any]:
        return {
            "size": self.size, "maxsize": self._maxsize,
            "hits": self.hits, "misses": self.misses,
            "hit_rate": round(self.hit_rate, 4),
        }


# --------------------------------------------------------------------------- #
# Daily-summary key derivation                                                 #
# --------------------------------------------------------------------------- #

def daily_summary_key(
    date: str, events: list[dict[str, Any]], source: str,
) -> str:
    """Stable hash key for a (date, events, llm-or-deterministic) tuple.

    ``source`` differentiates the LLM and deterministic paths so flipping
    OLLAMA_ENABLED never serves stale cross-mode entries. The events list
    is reduced to a stable shape (sorted dicts of the discriminating
    fields) before hashing so dict-key-ordering doesn't fragment the cache.
    """
    reduced = [
        {
            "type": e.get("type"),
            "planet": e.get("planet") or "",
            "planet_a": e.get("planet_a") or "",
            "planet_b": e.get("planet_b") or "",
            "description": e.get("description") or "",
            "severity": e.get("severity"),
            "domains": sorted(e.get("domains") or []),
        }
        for e in events
    ]
    blob = json.dumps(
        {"date": date, "source": source, "events": reduced},
        sort_keys=True,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Process-wide singletons                                                      #
# --------------------------------------------------------------------------- #

_daily_summary_cache = LRUCache(maxsize=2000)


def get_daily_summary_cache() -> LRUCache:
    """Return the process-wide daily-summary cache singleton."""
    return _daily_summary_cache


def reset_daily_summary_cache() -> None:
    """Test helper; drop all cached entries."""
    _daily_summary_cache.clear()


def cached_call(
    cache: LRUCache, key: str, producer: Callable[[], T],
) -> T:
    """Generic cache-or-compute helper.

    Used by the daily-summary and event-text annotators so they don't each
    re-implement the dict-cache pattern.
    """
    hit = cache.get(key)
    if hit is not None:
        return hit
    value = producer()
    cache.put(key, value)
    return value
