"""Item 4 (2026-10-13): one sentence promoted, three parked by research with the reason recorded.

Two engine-blind reviews per term; a term ships only when both agree on what Raman meant.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}


def _ctx(planets: dict[str, float], asc_lon: float = 5.0) -> C.EvalContext:
    return C.EvalContext(RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=asc_lon, ayanamsa="raman"))


class TestInFeminineSign:
    def test_even_signs_are_feminine(self) -> None:
        """HPA-5:37-38 'all even signs are mild and feminine': Taurus yes, Aries no."""
        assert C.InFeminineSign("Venus").evaluate(_ctx({"Venus": 40.0})) is True
        assert C.InFeminineSign("Venus").evaluate(_ctx({"Venus": 10.0})) is False

    def test_reads_the_navamsa_sign_in_d9(self) -> None:
        """Aries 0-3 deg 20' is the Aries navamsa (odd); 3 deg 20'-6 deg 40' is Taurus (even)."""
        assert C.InFeminineSign("Mars", "D9").evaluate(_ctx({"Mars": 1.0})) is False
        assert C.InFeminineSign("Mars", "D9").evaluate(_ctx({"Mars": 5.0})) is True

    def test_absent_planet_is_false(self) -> None:
        assert C.InFeminineSign("Saturn").evaluate(_ctx({"Venus": 40.0})) is False


class TestH2L7bIsLive:
    def test_live_neutral_and_omits_the_ungendered_constellation_branch(self) -> None:
        """HTJAH-I:2385 names Rashi, Navamsha OR constellation; no natal Raman book genders the
        nakshatras, so that branch is omitted (under-fires, never wrongly)."""
        r = _R["H2.L.7b"]
        assert r.kind == "evaluable" and r.polarity == "neutral"
        assert "TODO(" not in r.general and "Muhurtha" in r.general

    def test_fires_on_a_2nd_lord_in_the_7th_in_a_feminine_sign(self) -> None:
        """Aries rising: Venus owns the 2nd (Taurus); at Libra 5 deg (7th, odd) she is in the
        second navamsa of a movable sign -- Scorpio (even) -- so the Navamsha half holds."""
        assert _R["H2.L.7b"].condition.evaluate(_ctx({"Venus": 185.0})) is True


class TestParkedByResearch:
    @pytest.mark.parametrize("rid,slot", [("H10.L.3b", "general"), ("H11.L.8a", "general"),
                                          ("H6.L.7b", "afflicted")])
    def test_still_descriptive_with_the_research_recorded(self, rid: str, slot: str) -> None:
        r = _R[rid]
        assert r.kind == "descriptive" and r.condition is None, rid
        assert "PARKED by research 2026-10-13" in getattr(r, slot), rid

    def test_unfriendly_constellation_is_recorded_as_not_planetary_friendship(self) -> None:
        """Both reviews refuted natural friendship on Raman's only worked use (HTJAH-II:14087)."""
        assert "NOT planetary friendship" in _R["H10.L.3b"].general

    def test_hermaphrodite_signs_must_not_be_invented(self) -> None:
        assert "Do NOT build" in _R["H6.L.7b"].afflicted
