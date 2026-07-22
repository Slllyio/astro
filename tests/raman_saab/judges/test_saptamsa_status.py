"""D-7 (Sapthamsa) children-varga status — `house_template._saptamsa_status`.

The Sapthamsa is Raman's child-specific varga ("Saptamsa for children", HPA-11:198). This
pins the confirm/weaken read of the two children pillars (the 5th lord + Putrakaraka Jupiter)
inside the cast D-7 chart — the exact D-7 mirror of the proven `_navamsa_status`. Each test
states the divisional-astronomy fact it verifies. Longitudes are chosen (and cross-checked in
the module scratch run) so no accidental vargottama confounds the intended pillar state.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.house_template import _saptamsa_status


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
