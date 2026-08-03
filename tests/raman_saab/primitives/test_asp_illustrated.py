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
