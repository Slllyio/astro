"""Houses 10-12 strength-slot sweep (2026-10-13): H10 0/12, H11 1/12, H12 5/12 correctly encoded.

The last batch of the twelve-house sweep. Every re-homed record is neutral; across this batch the
doctrine snapshot recorded 1951 presentation changes and ZERO verdict changes, including the
removal of H10.L.10 (Raman gives no unconditioned reading for the 10th lord in the 10th).
"""
from __future__ import annotations

import re

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}
_NEW = [r.id for r in ALL_RULES
        if r.house in (10, 11, 12) and r.group == "lord_in_house"
        and not re.fullmatch(r"H\d+\.L\.\d+", r.id)]


def _ctx(planets: dict[str, float], asc_lon: float) -> C.EvalContext:
    return C.EvalContext(RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=asc_lon, ayanamsa="raman"))


class TestEveryRehomedClause:
    @pytest.mark.parametrize("rid", _NEW)
    def test_is_cited_and_neutral(self, rid: str) -> None:
        """Re-homed and section-level records show Raman's words without a good/bad vote."""
        r = _R[rid]
        assert r.source.work == "HTJAH-II" and r.source.line > 0
        assert r.polarity == "neutral", rid

    def test_the_batch_is_the_size_the_reviews_produced(self) -> None:
        assert len(_NEW) == 55, len(_NEW)   # H10 29 + H11 14 + H12 12


class TestRemovalsAndParkedText:
    def test_h10_l10_is_gone(self) -> None:
        """9546-9554 has no unconditioned sentence; a fortified-only base record leaked "highly
        successful" to weak and Shadbala-less charts via _branch's fortified default."""
        assert "H10.L.10" not in _R
        assert {"H10.L.10a", "H10.L.10b", "H10.L.10c", "H10.L.10d"} <= set(_R)

    def test_the_comma_splice_is_parked_not_asserted(self) -> None:
        """9572-9573's antecedent cannot be determined; putting it in `general` would assert
        smuggling for every chart on a grammatical technicality."""
        assert _R["H10.L.12d"].kind == "descriptive"
        assert "[sic]" in _R["H10.L.12d"].general

    def test_the_d60_clause_stays_blocked_on_source_attribution(self) -> None:
        assert "BLOCKED on source attribution" in _R["H10.L.4b"].general

    def test_the_benefic_and_in_dignity_clause_is_parked_after_enumeration(self) -> None:
        """A Jupiter/Venus 12th lord in the 2nd can never be exalted, own or moolatrikona."""
        assert _R["H12.L.2a"].kind == "descriptive"


class TestStrengthLadder:
    def test_h11_l1_carries_ramans_three_tiers(self) -> None:
        """14259-14264: "According as the 11th lord in Lagna is strong, middling or weak, the
        native will be born in a very rich, fairly rich or well-to-do family." Outer tiers live in
        the strength slots; the middle one, which a binary branch cannot express, is H11.L.1a."""
        r = _R["H11.L.1"]
        assert "very rich family" in r.fortified and "strong" in r.fortified
        assert "well-to-do family" in r.afflicted and "weak" in r.afflicted
        assert "fairly rich" in _R["H11.L.1a"].general


class TestPlanetIdentityBySign:
    def test_h11_l10_moon_or_mercury_lords_fire_neither_arm(self) -> None:
        """Leo rising: the 11th lord is Mercury, in the 10th = Taurus (sign 2). Raman counts
        Mercury benefic only conditionally, so neither 'fair' nor 'foul' fires."""
        ctx = _ctx({"Mercury": 40.0}, asc_lon=125.0)
        assert C.LordIn(11, 10).evaluate(ctx) is True
        assert _R["H11.L.10a"].condition.evaluate(ctx) is False
        assert _R["H11.L.10b"].condition.evaluate(ctx) is False

    def test_h11_l10_a_malefic_lord_fires_foul_means(self) -> None:
        """Aries rising: Saturn is the 11th lord; in the 10th he sits in Capricorn (sign 10)."""
        ctx = _ctx({"Saturn": 280.0}, asc_lon=5.0)
        assert _R["H11.L.10a"].condition.evaluate(ctx) is True


class TestJoinedBy:
    def test_conjunction_only_and_never_the_subject_itself(self) -> None:
        """Libra rising: Venus is the 1st lord. Venus alone in the Lagna is not 'a benefic
        joining' it; Jupiter beside it is; Jupiter merely aspecting it is not."""
        alone = _ctx({"Venus": 190.0}, asc_lon=185.0)
        joined = _ctx({"Venus": 190.0, "Jupiter": 195.0}, asc_lon=185.0)
        aspect = _ctx({"Venus": 190.0, "Jupiter": 10.0}, asc_lon=185.0)   # Aries, 7th from Libra
        assert C.JoinedBy("LORD_OF:1", C.FIRM_BENEFICS).evaluate(alone) is False
        assert C.JoinedBy("LORD_OF:1", C.FIRM_BENEFICS).evaluate(joined) is True
        assert C.JoinedBy("LORD_OF:1", C.FIRM_BENEFICS).evaluate(aspect) is False


class TestRareRulesCanFire:
    """Two records fire on zero goldens; a rule the ratchet never exercises is proved by chart."""

    def test_h10_l6c_witness(self) -> None:
        """Aries rising: Saturn (10th lord) in Virgo, the 6th, with Rahu."""
        assert _R["H10.L.6c"].condition.evaluate(_ctx({"Saturn": 160.0, "Rahu": 165.0}, 5.0))

    def test_h12_l3b_witness(self) -> None:
        """Taurus rising: Mars (12th lord) and Mercury (2nd lord) in Cancer, the 3rd; Jupiter in
        Pisces aspects Cancer by its 5th-house drishti."""
        ctx = _ctx({"Mars": 100.0, "Mercury": 105.0, "Jupiter": 340.0}, asc_lon=35.0)
        assert _R["H12.L.3b"].condition.evaluate(ctx) is True
