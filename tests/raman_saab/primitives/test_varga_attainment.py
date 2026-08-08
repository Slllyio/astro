"""Varga attainment — Raman's amsa ladder, and the measurement that bounded what it exposes.

The module exists because four 3HC yogas named amsa titles the engine could not evaluate.
Building it MEASURED the ladder's reachability over the shodasavarga and split the outcome:
Gopuramsa (rung 8) is reachable for every planet under own-sign counting; Vaiseshikamsa
(rung 12) is not, under any basis measured — so the module deliberately exports the first
and refuses the second. These tests pin the ladder verbatim, the counting definition, and
that refusal.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.varga_attainment import (
    RAMAN_AMSA_TITLES,
    SAPTAVARGA,
    SHODASAVARGA,
    amsa_title,
    attains_gopuramsa,
    swavarga_count,
)


def _chart(planet: str, lon: float) -> RamanChart:
    return RamanChart.from_stated_positions(
        {planet: {"lon": lon, "bhava": 1}}, asc_lon=0.0, ayanamsa="raman")


class TestTheLadderIsRamansVerbatim:
    def test_the_eleven_rungs(self):
        """GBB-3:371-395, copied by hand — the same discipline as every hand-copied order in
        this project: a test deriving the table from the module passes when both are edited
        together."""
        assert RAMAN_AMSA_TITLES == {
            2: "Parijatamsa", 3: "Parvathamsa", 4: "Simhasanamsa", 5: "Swargabalamsa",
            6: "Indramsa", 7: "Rajapadmamsa", 8: "Gopuramsam", 9: "Brahmapadamsam",
            10: "Vaishnavamsam", 11: "Saivamsam", 12: "Vaiseshikamsam"}

    def test_below_two_earns_nothing(self):
        assert amsa_title(0) is None and amsa_title(1) is None

    def test_counts_beyond_twelve_cap_at_the_top_rung(self):
        assert amsa_title(14) == "Vaiseshikamsam"


class TestSwavargaCounting:
    def test_mars_at_zero_aries(self):
        """0.0 Aries is Mars's best seat: own sign in 14 of the 16 vargas (measured in the
        module's reachability scan; pinned here as a spot value)."""
        assert swavarga_count(_chart("Mars", 0.0), "Mars") == 14

    def test_a_poorly_seated_moon_counts_low(self):
        assert swavarga_count(_chart("Moon", 200.0), "Moon") <= 2

    def test_nodes_always_count_zero(self):
        """Rahu and Ketu own no sign — no varga can be their Swavarga."""
        assert swavarga_count(_chart("Rahu", 100.0), "Rahu") == 0

    def test_the_saptavarga_subset_is_the_examples_seven(self):
        assert SAPTAVARGA == (1, 2, 3, 7, 9, 12, 30)
        assert set(SAPTAVARGA) <= set(SHODASAVARGA)


class TestGopuramsaIsTheExposedRung:
    def test_mars_attains_it_at_its_best_seat(self):
        assert attains_gopuramsa(_chart("Mars", 0.0), "Mars")

    def test_a_low_count_refuses(self):
        assert not attains_gopuramsa(_chart("Moon", 200.0), "Moon")

    def test_vaiseshikamsa_is_deliberately_not_exported(self):
        """Rung 12 is unreachable for most planets under every counting basis measured —
        a predicate would be dead code or a silent redefinition of Raman's count. If someone
        adds it, they must first answer the measurement in the module docstring."""
        import app.raman_saab.primitives.varga_attainment as m
        assert not hasattr(m, "attains_vaiseshikamsa")
