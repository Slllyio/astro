"""Tests for the production-hardening utilities."""

from __future__ import annotations

import asyncio
import json
import logging

import pytest

from app.integration.production import (
    CacheKey,
    CacheStats,
    ReadingCache,
    StructuredLogger,
    TimingContext,
    default_cache,
    get_logger,
    make_cache_key,
    measure,
    timed,
)


# ---------------------------------------------------------------------------
# Cache key
# ---------------------------------------------------------------------------

class TestCacheKey:
    def test_same_inputs_yield_same_fingerprint(self):
        k1 = make_cache_key(dob="1990-07-15", time="12:00", tz="+05:30",
                            lat=12.97, lon=77.59)
        k2 = make_cache_key(dob="1990-07-15", time="12:00", tz="+05:30",
                            lat=12.97, lon=77.59)
        assert k1.fingerprint() == k2.fingerprint()

    def test_different_inputs_yield_different_fingerprints(self):
        k1 = make_cache_key(dob="1990-07-15", time="12:00", tz="+05:30",
                            lat=12.97, lon=77.59)
        k2 = make_cache_key(dob="1990-07-16", time="12:00", tz="+05:30",
                            lat=12.97, lon=77.59)
        assert k1.fingerprint() != k2.fingerprint()

    def test_enrich_flag_affects_fingerprint(self):
        k1 = make_cache_key(dob="1990-07-15", time="12:00", tz="+05:30",
                            lat=12.97, lon=77.59, enrich=True)
        k2 = make_cache_key(dob="1990-07-15", time="12:00", tz="+05:30",
                            lat=12.97, lon=77.59, enrich=False)
        assert k1.fingerprint() != k2.fingerprint()


# ---------------------------------------------------------------------------
# Cache mechanics
# ---------------------------------------------------------------------------

class TestReadingCacheBasics:
    def test_put_and_get(self):
        cache = ReadingCache(capacity=4)
        key = make_cache_key(dob="2000-01-01", time="12:00", tz="+00:00",
                             lat=0.0, lon=0.0)
        cache.put(key, {"hello": "world"})
        assert cache.get(key) == {"hello": "world"}

    def test_miss_returns_none(self):
        cache = ReadingCache(capacity=4)
        key = make_cache_key(dob="1900-01-01", time="00:00", tz="+00:00",
                             lat=0.0, lon=0.0)
        assert cache.get(key) is None

    def test_lru_eviction(self):
        cache = ReadingCache(capacity=2)
        k1 = make_cache_key(dob="1990-01-01", time="00:00", tz="+00:00", lat=1.0, lon=1.0)
        k2 = make_cache_key(dob="1990-01-02", time="00:00", tz="+00:00", lat=1.0, lon=1.0)
        k3 = make_cache_key(dob="1990-01-03", time="00:00", tz="+00:00", lat=1.0, lon=1.0)
        cache.put(k1, {"v": 1})
        cache.put(k2, {"v": 2})
        cache.put(k3, {"v": 3})  # evicts k1
        assert cache.get(k1) is None
        assert cache.get(k2) == {"v": 2}
        assert cache.get(k3) == {"v": 3}

    def test_capacity_zero_or_negative_raises(self):
        with pytest.raises(ValueError):
            ReadingCache(capacity=0)
        with pytest.raises(ValueError):
            ReadingCache(capacity=-1)

    def test_get_or_compute_misses_first_then_hits(self):
        cache = ReadingCache(capacity=4)
        key = make_cache_key(dob="2010-01-01", time="00:00", tz="+00:00", lat=0.0, lon=0.0)
        compute_calls = 0

        def _compute():
            nonlocal compute_calls
            compute_calls += 1
            return {"computed": True}

        v1, was_hit1 = cache.get_or_compute(key, _compute)
        v2, was_hit2 = cache.get_or_compute(key, _compute)
        assert v1 == v2 == {"computed": True}
        assert was_hit1 is False
        assert was_hit2 is True
        assert compute_calls == 1

    def test_get_or_compute_rejects_nondict(self):
        cache = ReadingCache(capacity=4)
        key = make_cache_key(dob="2010-01-01", time="00:00", tz="+00:00", lat=0.0, lon=0.0)
        with pytest.raises(TypeError):
            cache.get_or_compute(key, lambda: "not a dict")


class TestCacheStats:
    def test_stats_reflect_activity(self):
        cache = ReadingCache(capacity=4)
        k1 = make_cache_key(dob="1990-01-01", time="00:00", tz="+00:00", lat=1.0, lon=1.0)
        cache.put(k1, {"v": 1})
        cache.get(k1)  # hit
        cache.get(k1)  # hit
        k2 = make_cache_key(dob="1900-01-01", time="00:00", tz="+00:00", lat=0.0, lon=0.0)
        cache.get(k2)  # miss
        stats = cache.stats()
        assert isinstance(stats, CacheStats)
        assert stats.hits == 2
        assert stats.misses == 1
        assert abs(stats.hit_rate - 2/3) < 1e-9

    def test_clear_resets_stats(self):
        cache = ReadingCache(capacity=4)
        k1 = make_cache_key(dob="1990-01-01", time="00:00", tz="+00:00", lat=1.0, lon=1.0)
        cache.put(k1, {"v": 1})
        cache.get(k1)
        cache.clear()
        stats = cache.stats()
        assert stats.size == 0
        assert stats.hits == 0
        assert stats.misses == 0


class TestDefaultCache:
    def test_default_cache_is_singleton(self):
        a = default_cache()
        b = default_cache()
        assert a is b


# ---------------------------------------------------------------------------
# Structured logger
# ---------------------------------------------------------------------------

class TestStructuredLogger:
    def test_info_emits_one_json_line(self, caplog):
        logger = StructuredLogger("test.logger")
        with caplog.at_level(logging.INFO, logger="test.logger"):
            logger.info("test_event", foo="bar", count=42)
        # Last record's message is JSON.
        record = next(r for r in caplog.records if r.name == "test.logger")
        payload = json.loads(record.message)
        assert payload["event"] == "test_event"
        assert payload["foo"] == "bar"
        assert payload["count"] == 42
        assert payload["level"] == "info"

    def test_get_logger_returns_singleton(self):
        a = get_logger("integration.module")
        b = get_logger("integration.module")
        assert a is b


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

class TestTimingContext:
    def test_measure_records_elapsed_ms(self):
        with measure("test") as ctx:
            pass
        assert ctx.elapsed_ms >= 0.0
        assert ctx.label == "test"


class TestTimedDecorator:
    def test_timed_sync_function(self):
        @timed("sync_fn")
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_timed_sync_function_re_raises_on_error(self):
        @timed("sync_err")
        def fail():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            fail()

    def test_timed_async_function(self):
        @timed("async_fn")
        async def aadd(a, b):
            await asyncio.sleep(0)
            return a + b

        result = asyncio.run(aadd(4, 5))
        assert result == 9

    def test_timed_async_re_raises_on_error(self):
        @timed("async_err")
        async def afail():
            raise RuntimeError("nope")

        with pytest.raises(RuntimeError):
            asyncio.run(afail())
