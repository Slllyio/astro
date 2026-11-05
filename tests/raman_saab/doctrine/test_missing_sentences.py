"""Gaps the 2026-10-13 qualifier tagging found in the lord-in-house tables.

Eleven of the twelve "missing" afflicted sentences already existed as child records; these are
the three real fixes.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}


def _ctx(planets: dict[str, float]) -> C.EvalContext:
    """Aries rising."""
    return C.EvalContext(RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=5.0, ayanamsa="raman"))


class TestH7L6aIsLive:
    def test_badly_afflicted_7th_lord_with_ill_disposed_venus_fires(self) -> None:
        """HTJAH-II:283 'If badly afflicted and the karaka Venus is also ill-disposed'. Aries
        rising: Venus is the 7th lord, in Virgo (the 6th) with Saturn and Rahu -- two first-rate
        malefics -- and nothing fortifies her."""
        r = _R["H7.L.6a"]
        assert r.kind == "evaluable" and r.polarity == "neutral"
        assert r.condition.evaluate(_ctx({"Venus": 165.0, "Saturn": 168.0, "Rahu": 170.0})) is True

    def test_one_malefic_is_not_badly_afflicted(self) -> None:
        assert _R["H7.L.6a"].condition.evaluate(_ctx({"Venus": 165.0, "Saturn": 168.0})) is False

    def test_ill_disposed_is_not_merely_afflicted(self) -> None:
        """Raman 'deliberately does not say afflicted' of Venus: Jupiter's aspect from Pisces
        fortifies her, so she is not ill-disposed though two malefics join her."""
        ctx = _ctx({"Venus": 165.0, "Saturn": 168.0, "Rahu": 170.0, "Jupiter": 345.0})
        assert C.IllDisposed("Venus").evaluate(ctx) is False


class TestH8L1HasNoInventedStrengthReading:
    def test_the_fortified_slot_is_empty(self) -> None:
        """HTJAH-II:2902-2904 states the penury unconditionally; only the weak case is qualified.
        'The 8th lord strong - ... undiminished' was the encoding's inference."""
        r = _R["H8.L.1"]
        assert r.fortified is None and "penury" in r.general and "weak" in r.afflicted


class TestH8L11AfflictedSentence:
    def test_ramans_closing_sentence_is_restored(self) -> None:
        """HTJAH-II:3050-3051 'Afflictions will aggravate the malefic results.'"""
        assert "aggravated" in _R["H8.L.11"].afflicted
