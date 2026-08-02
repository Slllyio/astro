"""Effective strength — `primitives/effective_strength.py` (DOCTRINE_BACKLOG B1).

The point of the measure is that raw Shadbala can disagree with Raman's own reading: at
HTJAH-I:3788 a lord whose Shadbala is strong is called "powerless" because it is combust.
These tests pin that a hard placement fact outvotes the number, and — just as important —
that the measure stays a MEASURE: it reports dusthana placement without penalising it, and
never decides a verdict.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives.effective_strength import (
    MARGINAL_BAND,
    effective_strength,
)
from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED

_CANONICAL = BirthData("canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def chart():
    return cast_chart(_CANONICAL, ayanamsa="raman")


class TestBands:
    def test_band_follows_the_gbb_bar(self, chart):
        """strong/marginal/weak are read off Raman's own MIN_REQUIRED bars (GBB-8:303-312)."""
        for planet, bar in MIN_REQUIRED.items():
            es = effective_strength(planet, chart)
            if es.rupas is None:
                continue
            expected = ("strong" if es.rupas >= bar
                        else "marginal" if es.rupas >= bar - MARGINAL_BAND else "weak")
            assert es.band == expected, f"{planet} {es.rupas:.2f} vs bar {bar} -> {es.band}"

    def test_nodes_have_no_shadbala_band(self, chart):
        """Shadbala is the 7 visible grahas only (GBB-3) — the nodes must read 'unknown',
        never a fabricated zero that would make them look decisively weak."""
        for node in ("Rahu", "Ketu"):
            es = effective_strength(node, chart)
            assert es.band == "unknown"
            assert es.rupas is None

    def test_absent_planet_is_reported_not_crashed(self, chart):
        es = effective_strength("Pluto", chart)
        assert es.band == "unknown" and es.reasons


class TestHardOverrides:
    def test_combustion_makes_a_factor_decisively_weak_whatever_the_number(self, chart):
        """HTJAH-I:3788 — chart_59's lord is combust and Raman reads it powerless while its
        Shadbala reads strong. A measure that lets the number win contradicts Raman."""
        import dataclasses

        es = effective_strength("Jupiter", chart)
        combust = dataclasses.replace(es, band="strong", combust=0.5)
        assert combust.decisively_weak
        assert not dataclasses.replace(es, band="strong", combust=0.0,
                                       debilitated_uncancelled=False).decisively_weak

    def test_uncancelled_debilitation_is_hard_but_cancelled_is_not(self, chart):
        import dataclasses

        es = effective_strength("Venus", chart)
        base = dataclasses.replace(es, band="strong", combust=0.0)
        assert dataclasses.replace(base, debilitated_uncancelled=True).decisively_weak
        assert not dataclasses.replace(base, debilitated_uncancelled=False).decisively_weak

    def test_dusthana_alone_does_not_condemn_a_factor(self, chart):
        """Reported, never penalised: Raman's dusthana readings are matter-specific — a STRONG
        dusthana lord feeds an affliction rather than curing it — so folding placement in here
        would double-count against the judge layer's own clause-1.5."""
        import dataclasses

        es = effective_strength("Saturn", chart)
        strong_in_dusthana = dataclasses.replace(
            es, band="strong", combust=0.0, debilitated_uncancelled=False, in_dusthana=True)
        assert not strong_in_dusthana.decisively_weak


class TestMeasureNotPolicy:
    def test_every_finding_carries_a_reason(self, chart):
        """Nothing is asserted without a citable why — the reasons are what a report renders."""
        for planet in (*MIN_REQUIRED, "Rahu", "Ketu"):
            es = effective_strength(planet, chart)
            if es.band in ("marginal", "weak") or es.combust > 0 or es.debilitated_uncancelled:
                assert es.reasons, f"{planet} flagged with no stated reason"

    def test_raw_shadbala_is_never_mutated(self, chart):
        """The measure ADJUSTS nothing — it reports the number beside the facts, so the
        golden ratchet's Shadbala inputs stay byte-identical."""
        for planet in MIN_REQUIRED:
            p = chart.planets.get(planet)
            if p is None or p.shadbala_rupas is None:
                continue
            assert effective_strength(planet, chart).rupas == p.shadbala_rupas.total / 60.0

    def test_runs_on_every_planet_of_a_real_chart(self, chart):
        for planet in chart.planets:
            es = effective_strength(planet, chart)
            assert es.band in ("strong", "marginal", "weak", "unknown")
            assert 0.0 <= es.combust <= 1.0
