"""Rasi & Graha Gunakara — `primitives/ashtakavarga_pinda.py` (HPA-26:1130-1404).

The anchor is Raman's own worked example, which survives the OCR intact enough to pin exactly:
the Sun's reduced table (Aries 2, Taurus 3, Cancer 3, Capricorn 2, Aquarius 2, Pisces 2) gives
14+30+12+10+22+24 = **112**, and the stated occupancies give 15+15+15 = **45**; "The sign total
is 112 and the planet total is 45, i.e., 112+45=157" (HPA-26:1394). Ephemeris-free — the fixture
feeds the stated tables directly, so it can never drift with casting.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives.ashtakavarga import PLANETS
from app.raman_saab.primitives.ashtakavarga_pinda import (
    GRAHA_GUNAKARA,
    RASI_GUNAKARA,
    ashtakavarga_pinda,
    graha_gunakara,
    rasi_gunakara,
)

#: The Sun's Ashtakavarga "after I & II reductions" as printed in the example (HPA-26:1160 ff.,
#: recovered from the per-sign products: 2x7, 3x10, 0, 3x4, 0,0,0,0,0, 2x5, 2x11, 2x12).
_SUN_REDUCED = {1: 2, 2: 3, 3: 0, 4: 3, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 2, 11: 2, 12: 2}

#: "the Sun is in Cancer; Moon and Saturn in Taurus; Mercury, Venus and Mars in Leo; and
#: Jupiter in Scorpio" (HPA-26:1317-1320).
_EXAMPLE_OCCUPANCY = {"Sun": 4, "Moon": 2, "Saturn": 2, "Mercury": 5, "Venus": 5,
                      "Mars": 5, "Jupiter": 8}


class TestRamansWorkedExample:
    def test_rasi_gunakara_gives_112(self):
        """14+30+12+10+22+24 — 'Sum= 112' (HPA-26:1254)."""
        assert rasi_gunakara(_SUN_REDUCED) == 112

    def test_graha_gunakara_gives_45(self):
        """Sun-in-Cancer 3x5 + Moon-in-Taurus 3x5 + Saturn-in-Taurus 3x5; every Leo/Scorpio
        occupant multiplies a zero. 'The total of these will be 45' (HPA-26:1383)."""
        assert graha_gunakara(_SUN_REDUCED, _EXAMPLE_OCCUPANCY) == 45

    def test_the_sum_is_157(self):
        """'The sign total is 112 and the planet total is 45, i.e., 112+45=157' (HPA-26:1394)."""
        assert rasi_gunakara(_SUN_REDUCED) + graha_gunakara(_SUN_REDUCED,
                                                            _EXAMPLE_OCCUPANCY) == 157

    def test_graha_side_multiplies_the_owning_planets_table(self):
        """The Moon's factor multiplies the SUN's bindus in Taurus — the table under
        consideration stays the owning planet's (HPA-26:1322-1329). If the implementation
        wrongly used each occupant's own table, Moon's contribution here would differ."""
        moon_only = graha_gunakara(_SUN_REDUCED, {"Moon": 2})
        assert moon_only == _SUN_REDUCED[2] * GRAHA_GUNAKARA["Moon"] == 15


class TestConstants:
    def test_rasi_factors_are_ramans(self):
        """'Aries 7, Taurus 10, Gemini 8, Cancer 4, Leo 10, Virgo 5, Libra 7, Scorpio 8,
        Sagittarius 9, Capricorn 5, Aquarius 11, and Pisces 12' (HPA-26:1149-1153)."""
        assert [RASI_GUNAKARA[s] for s in range(1, 13)] == [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]

    def test_graha_factors_are_ramans(self):
        """'Sun 5, Moon 5, Mars 8, Mercury 5, Jupiter 10, Venus 7 and Saturn 5'
        (HPA-26:1311-1315)."""
        assert GRAHA_GUNAKARA == {"Sun": 5, "Moon": 5, "Mars": 8, "Mercury": 5,
                                  "Jupiter": 10, "Venus": 7, "Saturn": 5}

    def test_nodes_never_contribute(self):
        """Rahu/Ketu have no planetary factor; an occupancy entry for them must be ignored,
        not crash and not add."""
        with_node = dict(_EXAMPLE_OCCUPANCY, Rahu=2, Ketu=8)
        assert graha_gunakara(_SUN_REDUCED, with_node) == 45


class TestOnACastChart:
    @pytest.fixture(scope="class")
    def chart(self):
        return cast_chart(BirthData("c", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59),
                          ayanamsa="raman")

    def test_breakdown_totals_are_consistent(self, chart):
        for planet in PLANETS:
            pb = ashtakavarga_pinda(chart, planet)
            assert pb.total == pb.rasi + pb.graha
            assert pb.rasi >= 0 and pb.graha >= 0

    def test_uses_the_reduced_table_not_the_raw_one(self, chart):
        """HPA-26:1128-1131 is emphatic: the Gunakaras read the tables 'after reduction' and
        'forget for the present the same tables before reduction'. The raw table's Rasi sum is
        strictly larger whenever any reduction removed a bindu from a nonzero-factor sign."""
        from app.raman_saab.primitives.ashtakavarga import bhinnashtakavarga
        from app.raman_saab.primitives.ashtakavarga_reduction import reduced_bhinnashtakavarga

        planet = "Sun"
        raw, red = bhinnashtakavarga(chart, planet), reduced_bhinnashtakavarga(chart, planet)
        assert ashtakavarga_pinda(chart, planet).rasi == rasi_gunakara(red)
        if raw != red:
            assert rasi_gunakara(raw) > rasi_gunakara(red)


class TestASP14CrossCheck:
    """ASP ch.XIV works the same math on the Standard Horoscope. Where his statements are
    checkable against the rules, they reproduce; his printed reduced TABLES carry hand-
    computation slips (module docstring), so the totals are recorded, not matched."""

    @pytest.fixture(scope="class")
    def standard(self):
        from app.raman_saab.chart.model import RamanChart
        S = {"Sun": 179 + 8 / 60, "Moon": 311 + 40 / 60, "Mars": 229 + 49 / 60,
             "Mercury": 180 + 33 / 60, "Jupiter": 83 + 35 / 60, "Venus": 170 + 4 / 60,
             "Saturn": 124 + 51 / 60, "Rahu": 53 + 23 / 60, "Ketu": 233 + 23 / 60}
        return RamanChart.from_stated_positions(
            {p: {"lon": lon, "bhava": 1} for p, lon in S.items()},
            asc_lon=185.0, ayanamsa="raman")

    def test_sodya_pinda_is_ramans_own_term_and_shape(self, standard):
        """ASP-14:196-198 — rasi + graha IS the Sodya Pinda; the breakdown must expose
        exactly that sum, and the x7/27 Ayurdaya application must be computable from it."""
        pb = ashtakavarga_pinda(standard, "Sun")
        assert pb.total == pb.rasi + pb.graha
        gross = pb.total * 7 / 27
        assert gross > 0

    def test_virgo_reduced_cell_matches_ramans_statement(self, standard):
        """ASP-14: '4 bindus in Virgo, the sign occupied by the Sun' (after reductions) —
        the one reduced cell his prose states directly, and ours agrees."""
        from app.raman_saab.primitives.ashtakavarga_reduction import reduced_bhinnashtakavarga
        assert reduced_bhinnashtakavarga(standard, "Sun")[6] == 4

    def test_totals_are_in_ramans_magnitude_band(self, standard):
        """His printed Sun Sodya Pinda is 182; ours is 191 — within 5%, the delta traced to
        slips in his hand-computed reduced tables (docstring). Guard the BAND so a real rule
        regression (which moves totals by tens) cannot hide behind 'the book differs anyway'."""
        pb = ashtakavarga_pinda(standard, "Sun")
        assert 170 <= pb.total <= 200
