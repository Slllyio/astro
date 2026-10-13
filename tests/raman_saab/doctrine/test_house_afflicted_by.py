"""HouseAfflictedBy: Raman's "if the Nth house is afflicted" -- the HOUSE, not its lord, is the
subject. A natural malefic occupies or aspects it; neither the house's own lord (HTJAH-I:2740)
nor the Lagna lord (HTJAH-I:13193, NH:26922) afflicts it, each with Raman's own exception.

All charts are Aries rising, so MARS is the Lagna lord: the generic examples use Saturn, the Sun
and the nodes.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}
PROMOTED = ["H3.L.6b", "H7.L.2b", "H10.L.2a", "H10.L.11a", "H12.L.1c"]


def _ctx(planets: dict[str, float]) -> C.EvalContext:
    """Aries rising (asc 5 deg): house n is the nth sign."""
    return C.EvalContext(RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=5.0, ayanamsa="raman"))


class TestTheHouseIsTheSubject:
    def test_a_malefic_occupying_the_house_afflicts_it(self) -> None:
        """Saturn in Leo is in the 5th for Aries rising."""
        assert C.HouseAfflictedBy(5).evaluate(_ctx({"Saturn": 130.0})) is True

    def test_a_special_aspect_afflicts_the_house(self) -> None:
        """Saturn in the 1st aspects the 3rd (Gemini, Mercury's) by his 3rd-house aspect."""
        assert C.HouseAfflictedBy(3).evaluate(_ctx({"Saturn": 10.0})) is True

    def test_a_benefic_alone_does_not_afflict(self) -> None:
        """Jupiter in the 5th is no affliction of it."""
        assert C.HouseAfflictedBy(5).evaluate(_ctx({"Jupiter": 130.0})) is False

    def test_the_nodes_aspect_the_7th_only(self) -> None:
        """Rahu in the 1st aspects the 7th, never the 5th (Raman: nodes 7th only)."""
        ctx = _ctx({"Rahu": 10.0})
        assert C.HouseAfflictedBy(7).evaluate(ctx) is True
        assert C.HouseAfflictedBy(5).evaluate(ctx) is False


class TestTheOwnLordNeverAfflicts:
    def test_saturn_in_his_own_11th_is_not_an_affliction_of_it(self) -> None:
        """Aquarius is the 11th for Aries rising and Saturn owns it; he still afflicts the 5th he
        aspects (owned by the Sun)."""
        ctx = _ctx({"Saturn": 305.0})
        assert C.HouseAfflictedBy(11).evaluate(ctx) is False
        assert C.HouseAfflictedBy(5).evaluate(ctx) is True

    def test_another_malefic_there_still_afflicts_it(self) -> None:
        """The Sun beside Saturn in Aquarius does afflict the 11th."""
        assert C.HouseAfflictedBy(11).evaluate(_ctx({"Saturn": 305.0, "Sun": 310.0})) is True

    def test_a_debilitated_own_lord_joined_by_a_node_loses_the_shield(self) -> None:
        """HTJAH-II:2139-2161: the 7th is afflicted though its lord aspects it, the lord being
        debilitated without cancellation and afflicted by Ketu. Here Saturn, owner of the 10th,
        is debilitated in Aries and aspects the 10th; with Rahu beside him the shield is gone."""
        assert C.HouseAfflictedBy(10).evaluate(_ctx({"Saturn": 10.0})) is False
        assert C.HouseAfflictedBy(10).evaluate(_ctx({"Saturn": 10.0, "Rahu": 15.0})) is True


class TestTheLagnaLordNeverAfflicts:
    def test_mars_as_lagna_lord_does_not_afflict_the_house_he_aspects(self) -> None:
        """NH:26922 "ruler of Lagna is always the most benefic planet"; HTJAH-I:13193 "does not
        afflict in the strict sense of the term being the Lagna lord". Mars in Leo (5th) casts
        his 8th aspect on Pisces, the 12th."""
        assert C.HouseAfflictedBy(12).evaluate(_ctx({"Mars": 130.0})) is False

    def test_joined_by_a_node_he_afflicts_again(self) -> None:
        """HTJAH-I:17253 "Although Saturn as Lagna lord is a benefice, his association with Ketu
        ... renders him a malefic". Rahu beside Mars in Leo, Ketu in Aquarius: neither node
        touches Pisces, so Mars is the afflicter."""
        ctx = _ctx({"Mars": 130.0, "Rahu": 135.0, "Ketu": 315.0})
        assert C.HouseAfflictedBy(12).evaluate(ctx) is True


class TestDegree:
    def test_min_count_needs_that_many_afflicters(self) -> None:
        """Ketu in the 5th plus Saturn aspecting it (from Aquarius, 7th) make two."""
        one = _ctx({"Ketu": 130.0})
        two = _ctx({"Ketu": 130.0, "Saturn": 305.0})
        assert C.HouseAfflictedBy(5, min_count=2).evaluate(one) is False
        assert C.HouseAfflictedBy(5, min_count=2).evaluate(two) is True

    def test_zero_is_refused(self) -> None:
        with pytest.raises(ValueError):
            C.HouseAfflictedBy(5, min_count=0)


class TestPromotedClauses:
    @pytest.mark.parametrize("rid", PROMOTED)
    def test_is_live_neutral_and_text_in_general(self, rid: str) -> None:
        """Parked on 'affliction of the HOUSE'; now live, showing Raman's words without a vote."""
        r = _R[rid]
        assert r.kind == "evaluable" and r.polarity == "neutral", rid
        assert r.general and not r.fortified and not r.afflicted, rid
        assert "TODO(" not in r.general, rid
        kinds = (C.AfflictedBy,) if rid == "H3.L.6b" else (C.HouseAfflictedBy,)
        assert any(isinstance(c, kinds) for c in r.condition.conds), rid

    def test_h3_l6b_reads_the_two_lords_not_the_houses(self) -> None:
        """HTJAH-I:3374-3377 runs on lords: 'the 6th and the 3rd are both afflicted' is set
        against 'well disposed', a lord's quality (doctrine review 2026-10-13)."""
        conds = _R["H3.L.6b"].condition.conds
        assert [c.planet for c in conds if isinstance(c, C.AfflictedBy)] == ["LORD_OF:3", "LORD_OF:6"]
        assert not any(isinstance(c, C.HouseAfflictedBy) for c in conds)

    def test_h10_l2a_fires_on_its_own_sentence(self) -> None:
        """HTJAH-II:9470: the 10th lord (Saturn, Aries rising) in the 2nd, the Sun in the 10th."""
        ctx = _ctx({"Saturn": 40.0, "Sun": 280.0})
        assert _R["H10.L.2a"].condition.evaluate(ctx) is True
        assert _R["H10.L.2a"].condition.evaluate(_ctx({"Saturn": 40.0})) is False
