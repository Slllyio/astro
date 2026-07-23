"""D-7 (Sapthamsa) children-varga status — `house_template._saptamsa_status`.

The Sapthamsa is Raman's child-specific varga ("Saptamsa for children", HPA-11:198). This
pins the confirm/weaken read of the two children pillars (the 5th lord + Putrakaraka Jupiter)
inside the cast D-7 chart — the exact D-7 mirror of the proven `_navamsa_status`. Each test
states the divisional-astronomy fact it verifies. Longitudes are chosen (and cross-checked in
the module scratch run) so no accidental vargottama confounds the intended pillar state.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.house_template import (
    _d7_hollow_redeemed_occupants, _d7_seat_occupancy, _saptamsa_status)


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    """Track-B chart from explicit sidereal longitudes (only asc_lon + per-planet lon
    are needed to cast the D-7). asc_lon 5.0 (Aries 5) -> D-7 lagna = Taurus (sign 2)."""
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


class TestSaptamsaStatus:
    def test_karaka_exalted_in_d7_confirms(self) -> None:
        """Jupiter at Aries 15 falls in Cancer in the D-7 — its exaltation -> confirms."""
        c = _chart({"Sun": 15.0, "Jupiter": 15.0})
        assert _saptamsa_status("Sun", "Jupiter", c) == "confirms"

    def test_karaka_debilitated_in_d7_weakens(self) -> None:
        """Jupiter at Capricorn 27 stays in Capricorn in the D-7 — its debilitation -> weakens."""
        c = _chart({"Sun": 15.0, "Jupiter": 297.0})
        assert _saptamsa_status("Sun", "Jupiter", c) == "weakens"

    def test_karaka_in_d7_dusthana_weakens(self) -> None:
        """Jupiter at Libra 27 -> D-7 Aries = the 12th from the Taurus D-7 lagna -> weakens."""
        c = _chart({"Sun": 15.0, "Jupiter": 207.0})
        assert _saptamsa_status("Sun", "Jupiter", c) == "weakens"

    def test_one_confirm_one_weaken_is_neutral(self) -> None:
        """Sun exalted in the D-7 (Aries) confirms while Jupiter debilitated (Capricorn)
        weakens — a split testimony reads neutral, never a one-sided verdict."""
        c = _chart({"Sun": 2.0, "Jupiter": 297.0})
        assert _saptamsa_status("Sun", "Jupiter", c) == "neutral"

    def test_no_pillar_resolvable_is_unknown(self) -> None:
        """Neither the 5th lord nor the karaka present in the chart -> unknown (safe no-op)."""
        c = _chart({"Sun": 15.0})
        assert _saptamsa_status("Mars", "Jupiter", c) == "unknown"

    def test_karaka_in_own_d7_sign_confirms(self) -> None:
        """Jupiter at Taurus 17.2 falls in Pisces in the D-7 — its own sign -> confirms."""
        c = _chart({"Sun": 15.0, "Jupiter": 47.2})
        assert _saptamsa_status("Sun", "Jupiter", c) == "confirms"

    def test_vargottama_alone_does_not_confirm(self) -> None:
        """Doctrine decision (P-review): the D1==D9 vargottama flag is a NAVAMSA fact already
        weighed by the D9 layer, so it is NOT counted as a D-7 confirm. Sun at Taurus 13.4 is
        vargottama yet only neutral-by-dignity in the D-7 (Aquarius) -> the D-7 read stays
        neutral, not confirms (the child-varga speaks only in its own evidence)."""
        c = _chart({"Sun": 43.4})
        assert _saptamsa_status("Sun", "Jupiter", c) == "neutral"


class TestSaptamsaOccupants:
    """D7-4: a 5th-house occupant whose rashi<->D-7 dignity flips modulates the status, the
    exact D-7 mirror of the D9-4/D9-6 hollow/redeemed occupant."""

    def test_hollow_occupant_via_extra_weakens(self) -> None:
        """Sun at Aries 27 is EXALTED in the rashi (Aries) but its D-7 falls in Libra - its
        DEBILITATION. Passed as an occupant, this hollow planet routes through weakens."""
        c = _chart({"Sun": 27.0})
        assert _saptamsa_status("Mars", "Jupiter", c, extra=("Sun",)) == "weakens"

    def test_redeemed_occupant_via_extra_confirms(self) -> None:
        """Sun at Libra 27 is DEBILITATED in the rashi (Libra) but its D-7 falls in Aries - its
        EXALTATION. asc_lon 2.0 -> D-7 lagna Aries, so the exalted Sun sits in the 1st (NOT a
        D-7 dusthana that would cancel it). This redeemed occupant routes through confirms."""
        c = _chart({"Sun": 207.0}, asc_lon=2.0)
        assert _saptamsa_status("Mars", "Jupiter", c, extra=("Sun",)) == "confirms"

    def test_extra_defaults_empty_leaves_status_unchanged(self) -> None:
        """The occupant channel is opt-in: with no `extra`, an absent lord/karaka -> unknown
        (the pre-D7-4 behaviour is preserved for every existing 2-arg caller)."""
        c = _chart({"Sun": 27.0})
        assert _saptamsa_status("Mars", "Jupiter", c) == "unknown"

    def test_selector_picks_hollow_5th_occupant_excludes_plain(self) -> None:
        """The selector returns the hollow 5th occupant (Sun: exalt-rashi/debil-D7) and excludes
        a plain 5th occupant (Mercury own-D7, no dignity flip). asc in Sagittarius (245) puts
        Aries in the 5th house."""
        c = _chart({"Sun": 27.0, "Mercury": 10.0}, asc_lon=245.0)
        assert _d7_hollow_redeemed_occupants(c, "Saturn", "Jupiter") == ("Sun",)

    def test_selector_excludes_lord_and_karaka(self) -> None:
        """A hollow 5th occupant that happens to BE the lord or karaka is not double-counted as
        an extra (it is already a pillar)."""
        c = _chart({"Sun": 27.0}, asc_lon=245.0)
        assert _d7_hollow_redeemed_occupants(c, "Sun", "Jupiter") == ()


class TestSaptamsaSeatOccupancy:
    """D7-4 Item 2: the net benefic/malefic occupancy of the two D-7 child-seats (the D-7 lagna
    and the 5th-from-D-7-lagna) modulates the status, but ONLY when include_seats=True. asc_lon
    5.0 -> D-7 lagna = Taurus (house 1); Virgo is the 5th-from-lagna (house 5)."""

    def test_malefic_on_d7_lagna_seat_weakens(self) -> None:
        """Saturn at Aries 6 falls in Taurus in the D-7 = the D-7 lagna (eldest-child seat). A
        malefic on the child-seat nets to weakens."""
        c = _chart({"Saturn": 6.0})
        assert _saptamsa_status("Mars", "Jupiter", c, include_seats=True) == "weakens"

    def test_benefic_on_seat_does_not_lift(self) -> None:
        """WEAKEN-ONLY (doctrine-reviewer ruling): a benefic on the D-7 lagna does NOT confirm/
        lift - Raman's progeny apparatus denies but never affirms. Venus alone on the seat, no
        malefic and no pillar -> the seat is silent -> status unknown."""
        c = _chart({"Venus": 6.0})
        assert _saptamsa_status("Mars", "Jupiter", c, include_seats=True) == "unknown"

    def test_malefic_on_fifth_from_d7_lagna_weakens(self) -> None:
        """Mars at Aries 23 falls in Virgo in the D-7 = the 5th-from-D-7-lagna (continuity
        seat). A malefic there weakens."""
        c = _chart({"Mars": 23.0})
        assert _saptamsa_status("Saturn", "Jupiter", c, include_seats=True) == "weakens"

    def test_benefic_offsets_a_malefic_on_the_same_seat(self) -> None:
        """WITHIN-seat offset is allowed: Saturn + Venus both in Taurus D-7 (same seat, house 1)
        -> malefics do not outnumber benefics -> the seat is silent -> status unknown."""
        c = _chart({"Saturn": 6.0, "Venus": 6.0})
        assert _saptamsa_status("Mars", "Jupiter", c, include_seats=True) == "unknown"

    def test_house5_benefic_cannot_cancel_house1_malefic(self) -> None:
        """PER-SEAT (doctrine-reviewer Q3): a benefic on the continuity seat (house 5, Venus in
        Virgo) must NOT cancel a malefic on the primary eldest seat (house 1, Saturn in Taurus).
        Per-seat, house 1 is net-malefic -> weakens (a pooled net would wrongly read neutral)."""
        c = _chart({"Saturn": 6.0, "Venus": 23.0})
        assert _saptamsa_status("Mars", "Jupiter", c, include_seats=True) == "weakens"

    def test_seats_are_opt_in_off_by_default(self) -> None:
        """Without include_seats the child-seat occupancy is ignored: a malefic on the D-7 lagna
        with no resolvable pillar stays unknown (every existing caller keeps pillars-only)."""
        c = _chart({"Saturn": 6.0})
        assert _saptamsa_status("Mars", "Jupiter", c) == "unknown"

    def test_seat_helper_direct_reads_house_1_and_5(self) -> None:
        """The helper reads occupancy directly from the cast D-7: a malefic on house 1 -> weakens."""
        from app.raman_saab.chart.varga_chart import cast_varga_chart
        c = _chart({"Saturn": 6.0})
        assert _d7_seat_occupancy(cast_varga_chart(c, 7)) == "weakens"
