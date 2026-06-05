"""Tests for EvalContext lazy cache (A3) and functional_nature() accessor (A2).

TDD — written BEFORE implementation, expected to fail RED until both features land.
"""
from __future__ import annotations

import pytest
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    """Minimal chart from stated ecliptic longitudes (asc_lon=0 → Aries lagna)."""
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in lons.items()},
        asc_lon=asc_lon,
        ayanamsa="raman",
    )


def _ctx(lons: dict[str, float], asc_lon: float = 0.0) -> C.EvalContext:
    return C.EvalContext(_chart(lons, asc_lon))


# ---------------------------------------------------------------------------
# A3 — get_or_compute lazy cache
# ---------------------------------------------------------------------------

class TestGetOrComputeCache:
    """EvalContext.get_or_compute(key, fn) memoises across calls."""

    def test_get_or_compute_caches(self):
        """compute_fn is called exactly once even when get_or_compute is called twice."""
        ctx = _ctx({"Sun": 5.0})
        call_count = {"n": 0}

        def expensive():
            call_count["n"] += 1
            return 42

        result1 = ctx.get_or_compute("expensive_key", expensive)
        result2 = ctx.get_or_compute("expensive_key", expensive)

        assert result1 == 42
        assert result2 == 42
        assert call_count["n"] == 1, "compute_fn must be called exactly once (cache miss then hit)"

    def test_get_or_compute_different_keys_are_independent(self):
        """Two different keys each run their own compute_fn once."""
        ctx = _ctx({"Sun": 5.0})
        calls = {"a": 0, "b": 0}

        ctx.get_or_compute("key_a", lambda: (calls.__setitem__("a", calls["a"] + 1) or "val_a"))
        ctx.get_or_compute("key_a", lambda: (calls.__setitem__("a", calls["a"] + 1) or "val_a"))
        ctx.get_or_compute("key_b", lambda: (calls.__setitem__("b", calls["b"] + 1) or "val_b"))

        assert calls["a"] == 1
        assert calls["b"] == 1

    def test_get_or_compute_returns_cached_none(self):
        """Cache must store None values correctly (not mistake None for 'not cached')."""
        ctx = _ctx({"Sun": 5.0})
        calls = {"n": 0}

        def returns_none():
            calls["n"] += 1
            return None

        r1 = ctx.get_or_compute("none_key", returns_none)
        r2 = ctx.get_or_compute("none_key", returns_none)

        assert r1 is None
        assert r2 is None
        assert calls["n"] == 1, "None result must be cached, not recomputed"

    def test_construction_still_accepts_chart_only(self):
        """EvalContext(chart) must continue to work — no extra required args."""
        chart = _chart({"Mars": 5.0})
        ctx = C.EvalContext(chart)
        assert ctx.chart is chart


# ---------------------------------------------------------------------------
# A2 — functional_nature() accessor on EvalContext
# ---------------------------------------------------------------------------

class TestFunctionalNatureAccessor:
    """ctx.functional_nature(planet) returns correct per-Lagna nature via the table."""

    # ── Aries lagna (asc_sign=1, asc_lon=0°) ──────────────────────────────
    def test_aries_jupiter_is_benefic(self):
        """Aries lagna: Jupiter (lord 9&12) is benefic per HTJAH-I:525-527."""
        ctx = _ctx({"Jupiter": 5.0}, asc_lon=0.0)
        assert ctx.functional_nature("Jupiter") == "benefic"

    def test_aries_mercury_is_malefic(self):
        """Aries lagna: Mercury (lord 3&6) is malefic per HTJAH-I:525-527."""
        ctx = _ctx({"Mercury": 5.0}, asc_lon=0.0)
        assert ctx.functional_nature("Mercury") == "malefic"

    def test_aries_mars_is_benefic(self):
        """Aries lagna: Mars (lord 1&8) is benefic (lagna lord, 8th taint overridden by lagna lordship)."""
        ctx = _ctx({"Mars": 5.0}, asc_lon=0.0)
        assert ctx.functional_nature("Mars") == "benefic"

    # ── Cancer lagna (asc_sign=4, asc_lon=90°) ────────────────────────────
    def test_cancer_mars_is_yogakaraka(self):
        """Cancer lagna: Mars owns 5th (trikona) AND 10th (kendra) → yogakaraka per HTJAH-I:540."""
        ctx = _ctx({"Mars": 5.0}, asc_lon=90.0)
        assert ctx.functional_nature("Mars") == "yogakaraka"

    def test_cancer_venus_is_malefic(self):
        """Cancer lagna: Venus (lord 4&11) is malefic per HTJAH-I:540-541."""
        ctx = _ctx({"Venus": 5.0}, asc_lon=90.0)
        assert ctx.functional_nature("Venus") == "malefic"

    # ── Capricorn lagna (asc_sign=10, asc_lon=270°) ───────────────────────
    def test_capricorn_venus_is_benefic(self):
        """Capricorn lagna: Venus (lord 5&10) — owns trikona and kendra → yogakaraka
        per the generating rule; HTJAH-I:558 also lists Venus as the most powerful benefic."""
        ctx = _ctx({"Venus": 5.0}, asc_lon=270.0)
        # Venus owns 5th (trikona) and 10th (kendra) for Capricorn → yogakaraka
        assert ctx.functional_nature("Venus") in ("yogakaraka", "benefic")

    def test_capricorn_mars_is_malefic(self):
        """Capricorn lagna: Mars (lord 4&11) is malefic per HTJAH-I:558-560."""
        ctx = _ctx({"Mars": 5.0}, asc_lon=270.0)
        assert ctx.functional_nature("Mars") == "malefic"

    # ── Rahu/Ketu ─────────────────────────────────────────────────────────
    def test_rahu_returns_neutral(self):
        """Rahu has no house lordship → always neutral per functional_nature.py contract."""
        ctx = _ctx({"Rahu": 5.0}, asc_lon=0.0)
        assert ctx.functional_nature("Rahu") == "neutral"

    def test_ketu_returns_neutral(self):
        """Ketu has no house lordship → always neutral."""
        ctx = _ctx({"Ketu": 5.0}, asc_lon=0.0)
        assert ctx.functional_nature("Ketu") == "neutral"

    # ── caching ───────────────────────────────────────────────────────────
    def test_functional_nature_is_cached(self):
        """functional_nature() routes through get_or_compute; result is in cache after first call."""
        ctx = _ctx({"Jupiter": 5.0}, asc_lon=0.0)
        r1 = ctx.functional_nature("Jupiter")
        r2 = ctx.functional_nature("Jupiter")
        assert r1 == r2 == "benefic"


# ---------------------------------------------------------------------------
# A0 — regression: existing predicates still evaluate correctly
# ---------------------------------------------------------------------------

class TestExistingConditionsRegression:
    """Prove EvalContext construction and existing leaf predicates are unbroken."""

    def test_in_rashi_house_still_works(self):
        """InRashiHouse evaluates correctly — no construction regression."""
        ctx = _ctx({"Saturn": 185.0, "Sun": 5.0})  # Aries: Saturn 7th, Sun 1st
        assert C.InRashiHouse("Saturn", 7).evaluate(ctx) is True
        assert C.InRashiHouse("Saturn", 8).evaluate(ctx) is False

    def test_functional_nature_condition_still_works(self):
        """FunctionalNature(planet, natures) leaf predicate still fires correctly."""
        ctx = _ctx({"Jupiter": 5.0})  # Aries lagna → Jupiter benefic
        assert C.FunctionalNature("Jupiter", {"benefic"}).evaluate(ctx) is True
        assert C.FunctionalNature("Jupiter", {"malefic"}).evaluate(ctx) is False

    def test_eval_context_chart_attribute_unchanged(self):
        """ctx.chart is the same object passed to the constructor."""
        chart = _chart({"Sun": 10.0})
        ctx = C.EvalContext(chart)
        assert ctx.chart is chart
