"""Unit tests for app.medini.forecast_cache + cache integration with
annotate_by_day.
"""
from __future__ import annotations

import pytest

from app.llm.client import StubClient
from app.medini.forecast_cache import (
    LRUCache,
    cached_call,
    daily_summary_key,
    get_daily_summary_cache,
    reset_daily_summary_cache,
)
from app.medini.forecast_daily_summary import annotate_by_day


SAMPLE_EVENTS = [
    {
        "type": "INGRESS", "jd": 2460676.5, "date_utc": "2026-01-01",
        "planet": "Saturn", "from_sign": "Aquarius", "to_sign": "Pisces",
        "description": "Saturn ingresses Pisces (from Aquarius)",
        "severity": 8, "domains": ["labor", "agriculture"],
    },
]


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_daily_summary_cache()
    yield
    reset_daily_summary_cache()


# --------------------------------------------------------------------------- #
# LRUCache                                                                     #
# --------------------------------------------------------------------------- #

class TestLRUCache:
    def test_get_returns_none_on_miss_and_increments_misses(self) -> None:
        c = LRUCache(maxsize=5)
        assert c.get("nope") is None
        assert c.misses == 1
        assert c.hits == 0

    def test_put_then_get_returns_value(self) -> None:
        c = LRUCache(maxsize=5)
        c.put("k", "v")
        assert c.get("k") == "v"
        assert c.hits == 1

    def test_overflow_evicts_oldest(self) -> None:
        """maxsize=2; put 3 keys; oldest evicted."""
        c = LRUCache(maxsize=2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        assert c.get("a") is None  # evicted
        assert c.get("b") == 2
        assert c.get("c") == 3

    def test_get_promotes_to_most_recently_used(self) -> None:
        """Accessing a key moves it to end → next eviction skips it."""
        c = LRUCache(maxsize=2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")           # a is now MRU
        c.put("c", 3)        # evicts b (LRU)
        assert c.get("a") == 1
        assert c.get("b") is None

    def test_stats_envelope(self) -> None:
        c = LRUCache(maxsize=10)
        c.put("k", 1)
        c.get("k")
        c.get("miss")
        s = c.stats()
        assert s == {"size": 1, "maxsize": 10, "hits": 1, "misses": 1, "hit_rate": 0.5}


# --------------------------------------------------------------------------- #
# daily_summary_key                                                            #
# --------------------------------------------------------------------------- #

class TestDailySummaryKey:
    def test_same_inputs_produce_same_key(self) -> None:
        k1 = daily_summary_key("2026-01-01", SAMPLE_EVENTS, "llm")
        k2 = daily_summary_key("2026-01-01", SAMPLE_EVENTS, "llm")
        assert k1 == k2

    def test_different_source_differentiates_key(self) -> None:
        """LLM vs deterministic must NOT share a cache entry."""
        k_llm = daily_summary_key("2026-01-01", SAMPLE_EVENTS, "llm")
        k_det = daily_summary_key("2026-01-01", SAMPLE_EVENTS, "deterministic")
        assert k_llm != k_det

    def test_different_date_differentiates_key(self) -> None:
        k1 = daily_summary_key("2026-01-01", SAMPLE_EVENTS, "llm")
        k2 = daily_summary_key("2026-01-02", SAMPLE_EVENTS, "llm")
        assert k1 != k2

    def test_dict_key_order_does_not_affect_key(self) -> None:
        """Events are reduced to a canonical shape before hashing — Python
        dict iteration order should never flip the cache key."""
        # Build the same event with reversed dict order
        forward = SAMPLE_EVENTS[0]
        reversed_keys = {k: forward[k] for k in reversed(list(forward.keys()))}
        k1 = daily_summary_key("2026-01-01", [forward], "llm")
        k2 = daily_summary_key("2026-01-01", [reversed_keys], "llm")
        assert k1 == k2

    def test_different_event_text_differentiates_key(self) -> None:
        modified = [{**SAMPLE_EVENTS[0], "description": "Different ingress"}]
        k1 = daily_summary_key("2026-01-01", SAMPLE_EVENTS, "llm")
        k2 = daily_summary_key("2026-01-01", modified, "llm")
        assert k1 != k2


# --------------------------------------------------------------------------- #
# cached_call                                                                  #
# --------------------------------------------------------------------------- #

class TestCachedCall:
    def test_first_call_invokes_producer(self) -> None:
        c = LRUCache()
        calls = {"n": 0}
        def producer():
            calls["n"] += 1
            return "computed"
        result = cached_call(c, "k", producer)
        assert result == "computed"
        assert calls["n"] == 1

    def test_second_call_hits_cache(self) -> None:
        c = LRUCache()
        calls = {"n": 0}
        def producer():
            calls["n"] += 1
            return calls["n"]
        cached_call(c, "k", producer)
        result = cached_call(c, "k", producer)
        assert result == 1  # cached value, not re-computed
        assert calls["n"] == 1


# --------------------------------------------------------------------------- #
# Integration with annotate_by_day                                              #
# --------------------------------------------------------------------------- #

class TestCacheIntegration:
    def test_second_annotate_uses_cache(self) -> None:
        """Calling annotate_by_day twice with same data hits the cache the
        second time — verify via the LRU's hits/misses counter."""
        cache = get_daily_summary_cache()
        by_day = {"2026-01-01": SAMPLE_EVENTS}
        annotate_by_day(by_day)
        first_misses = cache.misses
        annotate_by_day(by_day)
        # No new miss on the second call (cache hit)
        assert cache.hits >= 1
        assert cache.misses == first_misses

    def test_cache_disabled_via_kwarg(self) -> None:
        """use_cache=False bypasses the cache entirely (caller can opt out
        for in-process tests that want fresh computation)."""
        cache = get_daily_summary_cache()
        by_day = {"2026-01-01": SAMPLE_EVENTS}
        annotate_by_day(by_day, use_cache=False)
        annotate_by_day(by_day, use_cache=False)
        # No cache touches at all
        assert cache.hits == 0
        assert cache.misses == 0

    def test_llm_and_deterministic_dont_cross_pollute(self) -> None:
        """An entry cached as 'deterministic' must NOT be served when the
        caller asks for 'llm'. Source goes into the key."""
        cache = get_daily_summary_cache()
        by_day = {"2026-01-01": SAMPLE_EVENTS}
        # First call: deterministic (no client)
        det_result = annotate_by_day(by_day)
        # Second call: LLM via stub — must produce a NEW cache miss, not
        # serve the deterministic text by mistake.
        stub = StubClient(canned_response="LLM PROSE HERE")
        llm_result = annotate_by_day(by_day, client=stub)
        assert det_result["2026-01-01"]["summary"] != llm_result["2026-01-01"]["summary"]
        assert llm_result["2026-01-01"]["source"] == "llm"
