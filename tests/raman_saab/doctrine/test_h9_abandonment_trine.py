"""H9.A.18, the abandonment trine (HTJAH-II:7452-7453), read as printed.

"If the Sun and Moon be in trine to Mars and Saturn, the child will be abandoned by both
parents." Repaired 2026-10-30: the rule used to fire when the luminaries were in trine to
Mars OR Saturn. All charts are Aries rising; the Sun in Aries and the Moon in Leo are each in
trine to Sagittarius.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_RULE = {r.id: r for r in ALL_RULES}["H9.A.18"]


def _chart(planets: dict[str, float]) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=5.0, ayanamsa="raman")


class TestAbandonmentTrine:
    def test_both_malefics_in_trine_fires(self) -> None:
        """Mars and Saturn both in Sagittarius, trine to the Sun (Aries) and the Moon (Leo)."""
        chart = _chart({"Sun": 5.0, "Moon": 125.0, "Mars": 245.0, "Saturn": 250.0})
        assert _RULE.condition.evaluate(C.EvalContext(chart))

    def test_mars_alone_in_trine_does_not_fire(self) -> None:
        """Mars in Sagittarius is in trine to both luminaries, Saturn in Gemini to neither:
        the printed "Mars and Saturn" is not met."""
        chart = _chart({"Sun": 5.0, "Moon": 125.0, "Mars": 245.0, "Saturn": 65.0})
        assert not _RULE.condition.evaluate(C.EvalContext(chart))

    def test_saturn_alone_in_trine_does_not_fire(self) -> None:
        """The mirror case: Saturn in trine to both luminaries, Mars in Gemini."""
        chart = _chart({"Sun": 5.0, "Moon": 125.0, "Mars": 65.0, "Saturn": 245.0})
        assert not _RULE.condition.evaluate(C.EvalContext(chart))

    def test_only_the_sun_in_trine_does_not_fire(self) -> None:
        """The Moon in Gemini is in trine to neither malefic in Sagittarius."""
        chart = _chart({"Sun": 5.0, "Moon": 65.0, "Mars": 245.0, "Saturn": 250.0})
        assert not _RULE.condition.evaluate(C.EvalContext(chart))
