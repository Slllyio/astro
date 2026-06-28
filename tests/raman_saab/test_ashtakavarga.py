"""Ashtakavarga — the canonical-total checksum. Each planet's Bhinnashtakavarga total is fixed,
and the Sarvashtakavarga total across all 12 signs is ALWAYS 337, regardless of the chart. These
invariants catch any benefic-places table error that would otherwise be silent.
"""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import ashtakavarga as av

_BLR = BirthData(name="BLR", year=1990, month=7, day=15, hour=12, minute=0,
                 tz_offset=5.5, latitude=12.97, longitude=77.59)
_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_each_bav_total_is_canonical():
    """Every planet's Bhinnashtakavarga sums to its fixed canonical total."""
    ch = cast_chart(_BLR, ayanamsa="raman")
    for planet, total in av.BAV_TOTALS.items():
        assert sum(av.bhinnashtakavarga(ch, planet).values()) == total, planet


def test_sav_total_is_337():
    """Sarvashtakavarga across the 12 signs is always 337 (sum of 48+49+39+54+56+52+39)."""
    for bd in (_BLR, _MAINPURI):
        ch = cast_chart(bd, ayanamsa="lahiri")
        assert sum(av.sarvashtakavarga(ch).values()) == 337
        assert sum(av.BAV_TOTALS.values()) == 337


def test_benefic_table_house_values_in_range():
    """Sanity: every benefic-place house is 1..12 and every planet has all 8 references."""
    for planet, refs in av._BENEFIC.items():
        assert set(refs) == set(av._REFS), planet
        for houses in refs.values():
            assert all(1 <= h <= 12 for h in houses)


def test_bindus_in_house_matches_sav():
    ch = cast_chart(_MAINPURI, ayanamsa="lahiri")
    sav = av.sarvashtakavarga(ch)
    for h in range(1, 13):
        sign = ((ch.asc_sign - 1) + (h - 1)) % 12 + 1
        assert av.bindus_in_house(ch, h) == sav[sign]


# Per-reference benefic-places table, transcribed from Raman's Hindu Predictive Astrology ch.26
# (the engine's namesake source). Pins the DISTRIBUTION, not just the totals — a wrong house with
# the right count (e.g. Moon-from-Jupiter 2 vs 12) preserves the 49/337 checksums and would otherwise
# pass silently. Sun-from-Ascendant uses the canonical 6-house form (Raman's printed '9th' is an OCR
# typo: his row sums to 49, but he declares the Sun total 48).
_RAMAN_BENEFIC = {
    "Sun": {"Sun": (1, 2, 4, 7, 8, 9, 10, 11), "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
            "Saturn": (1, 2, 4, 7, 8, 9, 10, 11), "Jupiter": (5, 6, 9, 11), "Moon": (3, 6, 10, 11),
            "Mercury": (3, 5, 6, 9, 10, 11, 12), "Lagna": (3, 4, 6, 10, 11, 12), "Venus": (6, 7, 12)},
    "Moon": {"Lagna": (3, 6, 10, 11), "Mars": (2, 3, 5, 6, 9, 10, 11), "Moon": (1, 3, 6, 7, 10, 11),
             "Sun": (3, 6, 7, 8, 10, 11), "Saturn": (3, 5, 6, 11), "Mercury": (1, 3, 4, 5, 7, 8, 10, 11),
             "Jupiter": (1, 4, 7, 8, 10, 11, 12), "Venus": (3, 4, 5, 7, 9, 10, 11)},
    "Mars": {"Sun": (3, 5, 6, 10, 11), "Lagna": (1, 3, 6, 10, 11), "Moon": (3, 6, 11),
             "Mars": (1, 2, 4, 7, 8, 10, 11), "Saturn": (1, 4, 7, 8, 9, 10, 11), "Mercury": (3, 5, 6, 11),
             "Venus": (6, 8, 11, 12), "Jupiter": (6, 10, 11, 12)},
    "Mercury": {"Venus": (1, 2, 3, 4, 5, 8, 9, 11), "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
                "Saturn": (1, 2, 4, 7, 8, 9, 10, 11), "Jupiter": (6, 8, 11, 12), "Sun": (5, 6, 9, 11, 12),
                "Mercury": (1, 3, 5, 6, 9, 10, 11, 12), "Moon": (2, 4, 6, 8, 10, 11),
                "Lagna": (1, 2, 4, 6, 8, 10, 11)},
    "Jupiter": {"Mars": (1, 2, 4, 7, 8, 10, 11), "Jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
                "Sun": (1, 2, 3, 4, 7, 8, 9, 10, 11), "Venus": (2, 5, 6, 9, 10, 11),
                "Moon": (2, 5, 7, 9, 11), "Saturn": (3, 5, 6, 12), "Mercury": (1, 2, 4, 5, 6, 9, 10, 11),
                "Lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11)},
    "Venus": {"Lagna": (1, 2, 3, 4, 5, 8, 9, 11), "Moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
              "Venus": (1, 2, 3, 4, 5, 8, 9, 10, 11), "Saturn": (3, 4, 5, 8, 9, 10, 11),
              "Sun": (8, 11, 12), "Jupiter": (5, 8, 9, 10, 11), "Mercury": (3, 5, 6, 9, 11),
              "Mars": (3, 5, 6, 9, 11, 12)},
    "Saturn": {"Saturn": (3, 5, 6, 11), "Mars": (3, 5, 6, 10, 11, 12), "Sun": (1, 2, 4, 7, 8, 10, 11),
               "Lagna": (1, 3, 4, 6, 10, 11), "Mercury": (6, 8, 9, 10, 11, 12), "Moon": (3, 6, 11),
               "Venus": (6, 11, 12), "Jupiter": (5, 6, 11, 12)},
}


def test_benefic_distribution_matches_raman_text():
    """The per-reference DISTRIBUTION matches Raman HPA ch.26 exactly — not just the totals."""
    for planet, refs in _RAMAN_BENEFIC.items():
        for ref, houses in refs.items():
            assert set(av._BENEFIC[planet][ref]) == set(houses), f"{planet} from {ref}"
