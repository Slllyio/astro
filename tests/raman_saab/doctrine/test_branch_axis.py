"""Lord-in-house readings are picked on the axis of Raman's own qualifier word.

Two independent engine-blind reviews tagged each slot from HTJAH-I/II (2026-10-13); only slots
both tagged identically are in QUALIFIER_AXIS. All charts are Aries rising with no Shadbala, so
"strong" never holds and "weak" comes only from hard facts (combustion, debility).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.branch_axis import QUALIFIER_AXIS
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.judges import rule_firing as RF

_R = {r.id: r for r in ALL_RULES}


def _chart(planets: dict[str, float]) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=5.0, ayanamsa="raman")


class TestTheTable:
    @pytest.mark.parametrize("rid", sorted(QUALIFIER_AXIS))
    def test_every_tagged_slot_exists(self, rid: str) -> None:
        """A tag on a missing rule or an empty slot would silently do nothing."""
        r = _R[rid]
        assert r.group == "lord_in_house" and r.kind == "evaluable", rid
        for slot, axis in zip(("fortified", "afflicted"), QUALIFIER_AXIS[rid]):
            if axis:
                assert getattr(r, slot), (rid, slot)
                assert axis in ("influence", "strength", "both"), (rid, axis)

    def test_the_contested_slots_are_left_out(self) -> None:
        """Split or unclear between the reviews: H8.L.5, H8.L.8, H6.L.11, H10.L.3, H12.L.4; H8.L.7
        conditions on two lords."""
        assert not {"H8.L.5", "H8.L.8", "H6.L.11", "H10.L.3", "H12.L.4", "H8.L.7"} & set(QUALIFIER_AXIS)


class TestInfluenceSlots:
    """H5.L.3 (HTJAH-I 5th lord in the 3rd): 'Favourably disposed' / 'unfavourably disposed'.
    For Aries the 5th lord is the Sun; in Gemini he is in the 3rd."""

    def test_saturn_joining_shows_the_afflicted_reading(self) -> None:
        assert RF._branch(_R["H5.L.3"], _chart({"Sun": 70.0, "Saturn": 75.0})) == "afflicted"

    def test_jupiter_aspecting_shows_the_fortified_reading(self) -> None:
        assert RF._branch(_R["H5.L.3"], _chart({"Sun": 70.0, "Jupiter": 250.0})) == "fortified"


class TestStrengthSlots:
    """H4.L.1 (HTJAH-I:4150): 'strong ... or weak'. For Aries the 4th lord is the Moon."""

    def test_a_combust_lord_is_weak(self) -> None:
        """The Moon beside the Sun in Aries is combust -- 'powerless' (HTJAH-I:3788)."""
        assert RF._branch(_R["H4.L.1"], _chart({"Moon": 10.0, "Sun": 12.0})) == "afflicted"

    def test_unknown_strength_shows_the_unconditioned_reading(self) -> None:
        """No Shadbala and no hard fact: neither strong nor weak."""
        assert RF._branch(_R["H4.L.1"], _chart({"Moon": 10.0})) == "general"


class TestWeakAndAfflicted:
    """H6.L.4 (HTJAH-I 6th lord in the 4th): 'Well fortified' / 'Weak and afflicted'. For Aries
    the 6th lord is Mercury; Cancer is the 4th."""

    def test_combust_by_the_sun_is_both_weak_and_afflicted(self) -> None:
        assert RF._branch(_R["H6.L.4"], _chart({"Mercury": 100.0, "Sun": 102.0})) == "afflicted"

    def test_afflicted_but_not_weak_never_shows_the_fortified_reading(self) -> None:
        """Saturn joins Mercury far from the Sun: afflicted, not weak. With no unconditioned text
        something must show; the 'weak and afflicted' reading is half true, the fortified one is
        the opposite pole, so the clear disposition picks the former."""
        assert RF._branch(_R["H6.L.4"], _chart({"Mercury": 100.0, "Saturn": 105.0})) == "afflicted"
