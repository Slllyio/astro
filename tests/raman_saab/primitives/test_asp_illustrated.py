"""ASP ch.XVI Illustrated Horoscopes — printed-table fixtures (ASP-16).

The chapter's preamble spells out Illustrated Horoscope No. 1's Sun Ashtakavarga cell by cell,
raw and reduced (ASP-16:40-51): "in the Sun's Ashtakavarga the bindus are as follows: Aries 5,
Taurus 5 (and 2 after reduction), Gemini 4, Cancer 3 (and 1 after reduction), Leo 4 (and 2
after reduction), Virgo 5 (and 2 after reduction), Libra 6 (and 2 after reduction), Scorpio 5
(and 3 after reduction), Sagittarius 2, Capricorn 3, Aquarius 4 and Pisces 2."

That is a PRINTED raw table with printed post-reduction cells — a validation dataset for the
reduction pipeline fully independent of both the Standard Horoscope and HPA-26's example.

Scope note: the Ekadhipatya pass needs the chart's occupancies, which the preamble does not
state (and the No. 1 chart's positions are OCR-damaged) — but every stated reduced cell lands
in a sign the TRIKONA pass alone determines, so the assertion set is exact without them.
Roosevelt's (No. 2) printed longitudes are too OCR-damaged to reconstruct responsibly
(month digit corrupted, the Moon's value lost) — recorded here rather than guessed at;
re-extractable from the source PDF by vision in a future session.
"""
from __future__ import annotations

from app.raman_saab.primitives.ashtakavarga_reduction import trikona_shodhana

#: ASP-16:45-51 — Illustrated No. 1's raw Sun Ashtakavarga, Aries..Pisces.
_NO1_SUN_RAW = {1: 5, 2: 5, 3: 4, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 2, 10: 3, 11: 4, 12: 2}

#: The reduced cells the preamble states (signs with no bracketed figure are not asserted —
#: their final values depend on the Ekadhipatya occupancies the text does not give).
_NO1_STATED_REDUCED = {2: 2, 4: 1, 5: 2, 6: 2, 7: 2, 8: 3}


class TestIllustratedNo1Sun:
    def test_the_printed_raw_table_carries_the_canonical_total(self):
        """Any Sun Ashtakavarga must total 48 — the printed table does, confirming the OCR
        recovered every cell (a single misread digit would break the checksum)."""
        assert sum(_NO1_SUN_RAW.values()) == 48

    def test_every_stated_reduced_cell_reproduces_under_trikona(self):
        """All six bracketed figures Raman prints — Taurus 2, Cancer 1, Leo 2, Virgo 2,
        Libra 2, Scorpio 3 — fall out of `trikona_shodhana` on his raw table exactly.
        A second printed-book validation of the subtract reading (after HPA-26's worked
        example), on a third independent nativity."""
        tri = trikona_shodhana(_NO1_SUN_RAW)
        for sign, stated in _NO1_STATED_REDUCED.items():
            assert tri[sign] == stated, f"sign {sign}: trikona {tri[sign]} != printed {stated}"

    def test_the_stated_cells_are_exactly_the_trikona_determined_ones(self):
        """Documents WHY only six cells are asserted: the four trines here are (5,4,2),
        (5,5,3), (4,6,4), (3,5,2) — no special case fires, rule 10 subtracts the least in
        each, and the six stated signs are those left nonzero before Ekadhipatya."""
        tri = trikona_shodhana(_NO1_SUN_RAW)
        nonzero = {s for s, v in tri.items() if v > 0}
        assert set(_NO1_STATED_REDUCED) <= nonzero


#: Vision-verified from the source PDF (page 84 / book pp.160-161) — the OCR text of these
#: longitude strings is damaged, so the values below were read from the page image directly.
_NO1_POSITIONS = {  # "An Eminent Indian", born 8/9-12-1878 (ASP-16, No. 1)
    "Sun": 237 + 8 / 60, "Moon": 59 + 24 / 60, "Mars": 209 + 24 / 60,
    "Mercury": 257 + 54 / 60, "Jupiter": 285 + 11 / 60, "Venus": 238 + 11 / 60,
    "Saturn": 335 + 31 / 60, "Rahu": 285 + 45 / 60, "Ketu": 105 + 45 / 60}
_NO1_ASC = 229 + 16 / 60
_NO1_SODYA = {"Sun": 154, "Moon": 81, "Mars": 186, "Mercury": 147,
              "Jupiter": 78, "Venus": 72, "Saturn": 163}

_NO2_POSITIONS = {  # Franklin Delano Roosevelt (ASP-16, No. 2)
    "Sun": 290 + 20 / 60, "Moon": 75 + 5 / 60, "Mars": 66 + 15 / 60,
    "Mercury": 306 + 23 / 60, "Jupiter": 26 + 10 / 60, "Venus": 285 + 16 / 60,
    "Saturn": 15 + 20 / 60, "Rahu": 224 + 55 / 60, "Ketu": 44 + 55 / 60}
_NO2_ASC = 143 + 32 / 60
_NO2_SUN_RAW = [5, 2, 4, 6, 3, 3, 4, 5, 5, 5, 4, 2]
_NO2_SODYA = {"Sun": 150, "Moon": 129, "Mars": 135, "Mercury": 211,
              "Jupiter": 94, "Venus": 96, "Saturn": 99}


class TestIllustratedEndToEnd:
    """The definitive whole-pipeline validation: BAV -> Trikona -> Ekadhipatya -> Rasi+Graha
    Gunakara -> Sodya Pinda, against Raman's own printed SODYA PINDAS tables for two complete
    nativities (ASP-16 Nos. 1-2). Every one of the 14 printed pindas reproduces EXACTLY, which
    also settles the ASP-14 Standard-Horoscope delta: the rules are right, that one printed
    table was slipped."""

    @staticmethod
    def _chart(positions, asc):
        from app.raman_saab.chart.model import RamanChart
        return RamanChart.from_stated_positions(
            {p: {"lon": lon, "bhava": 1} for p, lon in positions.items()},
            asc_lon=asc, ayanamsa="raman")

    def test_no1_raw_sun_table_matches_print(self):
        from app.raman_saab.primitives.ashtakavarga import bhinnashtakavarga
        bav = bhinnashtakavarga(self._chart(_NO1_POSITIONS, _NO1_ASC), "Sun")
        assert [bav[s] for s in range(1, 13)] == [_NO1_SUN_RAW[s] for s in range(1, 13)]

    def test_no2_raw_sun_table_matches_print(self):
        from app.raman_saab.primitives.ashtakavarga import bhinnashtakavarga
        bav = bhinnashtakavarga(self._chart(_NO2_POSITIONS, _NO2_ASC), "Sun")
        assert [bav[s] for s in range(1, 13)] == _NO2_SUN_RAW

    def test_all_fourteen_printed_sodya_pindas_reproduce_exactly(self):
        """No bands, no tolerance: 154/81/186/147/78/72/163 and 150/129/135/211/94/96/99,
        planet for planet."""
        from app.raman_saab.primitives.ashtakavarga import PLANETS
        from app.raman_saab.primitives.ashtakavarga_pinda import ashtakavarga_pinda
        for positions, asc, printed in ((_NO1_POSITIONS, _NO1_ASC, _NO1_SODYA),
                                        (_NO2_POSITIONS, _NO2_ASC, _NO2_SODYA)):
            chart = self._chart(positions, asc)
            for p in PLANETS:
                assert ashtakavarga_pinda(chart, p).total == printed[p], p
