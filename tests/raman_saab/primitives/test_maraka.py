from __future__ import annotations
from app.raman_saab.primitives.maraka import maraka_points
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart

BANGALORE = BirthData("Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


def _c(lons, asc_lon=0.0):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def test_22nd_drekkana_lord_pins_ramans_printed_example():
    # Raman HTJAH-II:3692-3695: Lagna 27° Aquarius -> lagna drekkana = 3rd of Aquarius;
    # the 22nd drekkana from this = 1st drekkana of Libra -> lord Venus.
    c = _c({"Moon": 0.0}, asc_lon=10 * 30 + 27.0)   # 27° Aquarius
    assert maraka_points(c).drekkana22_lord == "Venus"


def test_64th_navamsa_lord_is_reckoned_from_the_moon():
    # HTJAH-II:4544: "the lord of the 64th Navamsa occupied by the Moon" -> from the MOON.
    # Structural: a valid sign-lord; and it MUST change when only the Moon moves.
    c1 = _c({"Moon": 5.0}, asc_lon=0.0)
    c2 = _c({"Moon": 100.0}, asc_lon=0.0)           # same lagna, different Moon
    from app.raman_saab.chart.constants import SIGN_LORDS
    assert maraka_points(c1).navamsa64_lord in SIGN_LORDS.values()
    assert maraka_points(c1).navamsa64_lord != maraka_points(c2).navamsa64_lord


def test_second_and_seventh_lords_are_primary_marakas():
    # Aries lagna: 2nd lord = Venus (Taurus), 7th lord = Venus (Libra) -> Venus primary.
    c = _c({"Venus": 35.0, "Moon": 0.0}, asc_lon=0.0)
    mp = maraka_points(c)
    grahas = {u.graha for u in mp.units if u.tier == "primary"}
    assert "Venus" in grahas


# ── Phase 1c-3 backfills (need real Shadbala) ────────────────────────────────────

def test_strength_rank_is_zero_without_shadbala():
    """Track-B (stated-positions) charts have no Shadbala -> strength_rank stays 0."""
    c = _c({"Venus": 35.0, "Moon": 0.0}, asc_lon=0.0)
    mp = maraka_points(c)
    assert all(u.strength_rank == 0 for u in mp.units)


def test_ephemeris_chart_maraka_units_carry_sane_strength_rank():
    """An ephemeris chart fills strength_rank in 1..7 (rank by total Shadbala, 1=strongest)."""
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    mp = chart.maraka_points
    assert mp is not None and len(mp.units) >= 1
    for u in mp.units:
        assert 1 <= u.strength_rank <= 7, f"{u.graha} rank {u.strength_rank} out of 1..7"


def test_strength_rank_matches_shadbala_ordering():
    """Rank 1 must be the strongest maraka graha by total Shadbala; ranks are consistent."""
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    mp = chart.maraka_points
    # Build the independent ranking of the 7 by total Shadbala (desc).
    totals = {n: chart.planets[n].shadbala_rupas.total
              for n in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")}
    ordered = sorted(totals, key=lambda n: totals[n], reverse=True)
    expected = {n: i + 1 for i, n in enumerate(ordered)}
    for u in mp.units:
        assert u.strength_rank == expected[u.graha]


def test_weakest_planet_tertiary_appears_with_shadbala():
    """The lowest-total-Shadbala planet is added as a tertiary maraka (GBB-8 / §8.2)."""
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    mp = chart.maraka_points
    totals = {n: chart.planets[n].shadbala_rupas.total
              for n in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")}
    weakest = min(totals, key=lambda n: totals[n])
    assert weakest in {u.graha for u in mp.units}
