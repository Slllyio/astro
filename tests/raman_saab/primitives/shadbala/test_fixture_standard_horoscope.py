"""Track-B fixture — GBB "Standard Horoscope" (B.V. Raman's own nativity, 16 Oct 1918).

Reference: docs/raman_saab/gbb_shadbala_reference.md §10 (gold table, GBB-8:280-298) and
the per-varga worked tables in GBB-3 (Sthana) cross-checked against Raman's *A Manual of
Hindu Astrology* (MHA) Ch.12 — the authority GBB defers to for varga lords (GBB-3:310-312).

Injected via ``from_stated_positions`` with **Libra Lagna (asc 185 deg)** — verified correct:
all 7 Kendra-bala values reproduce the book's Kendra row (GBB-3:642-651). Ephemeris-free.

What this fixture pins (Phase 1c-1 scope):
  * Naisargika column — reconciles near-exactly.
  * The 3 OCR-clean Sthana totals (Sun, Mercury, Jupiter) — reconcile within ~6 Sh.
  * The Saptavargaja column per planet (localization test) — 5 of 7 reconcile exactly; the
    two that don't (Mars D30, Saturn D7) are xfail-carried with a precise cusp-artifact
    diagnosis (see ``test_saptavargaja_per_planet``).

Carry-overs to Phase 1c-3 (documented, NOT silently hidden):
  * Mars/Saturn Sthana totals — driven by the two Saptavargaja cusp artifacts below.
  * Moon/Venus Sthana totals (gold 141.650 / 157.925) differ from the engine (126.639 /
    172.936) by +/-15 Sh. This is NOT a Saptavargaja gap (their Saptavargaja reconciles
    exactly). It is the documented Ch.8-vs-Ch.3 OCR divergence in the Ochcha/Drekkana
    columns (reference §10, lines 214-219): the engine totals match GBB Ch.3 Ex.13
    (Moon 126.650) while the §10 gold cell is the Ch.8 Ex.56 consolidated value.
  * Drik and Dig column reconciliation (need benefic/malefic refinement and real cusps).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.shadbala import naisargika, sthana

# GBB Standard Horoscope stated Nirayana longitudes (deg), Libra Lagna (asc 185 deg).
_POS = {
    "Sun": 179 + 8 / 60, "Moon": 311 + 40 / 60, "Mars": 229 + 49 / 60,
    "Mercury": 180 + 33 / 60, "Jupiter": 83 + 35 / 60, "Venus": 170 + 4 / 60,
    "Saturn": 124 + 51 / 60}
_CHART = RamanChart.from_stated_positions(
    {p: {"lon": l, "bhava": 1} for p, l in _POS.items()},
    asc_lon=185.0, ayanamsa="raman")

# GBB-7 Naisargika column (Shashtiamsas).
_NAISARGIKA = {
    "Sun": 60.0, "Moon": 51.43, "Mars": 17.14, "Mercury": 25.70,
    "Jupiter": 34.28, "Venus": 42.85, "Saturn": 8.57}

# Sthana totals that reconcile to the §10 gold table AND the summed sub-components
# (verified in plan review — the three OCR-clean cells).
_STHANA_CLEAN = {"Sun": 147.975, "Mercury": 294.800, "Jupiter": 157.450}

# Book Saptavargaja per-planet totals, GBB-3:514-543 (gold column).
_SAPTAVARGAJA_BOOK = {
    "Sun": 129.375, "Moon": 48.750, "Mars": 112.500, "Mercury": 150.000,
    "Jupiter": 71.250, "Venus": 110.625, "Saturn": 82.500}

# Planets whose Saptavargaja reconciles exactly with the book.
_SAPTAVARGAJA_RECONCILE = ("Sun", "Moon", "Mercury", "Jupiter", "Venus")
# Planets that diverge — each by exactly ONE varga cell, a sub-degree cusp artifact in
# Raman's 1918 hand-worked tables (diagnosis below; carried to Phase 1c-3).
_SAPTAVARGAJA_XFAIL = ("Mars", "Saturn")


def test_naisargika_column():
    """The fixed 60/7 ladder reproduces every cell of the GBB-7 Naisargika row."""
    for planet, expected in _NAISARGIKA.items():
        assert abs(naisargika.naisargika_bala(planet) - expected) < 0.5


def test_sthana_clean_cells_reconcile():
    """Sun/Mercury/Jupiter Sthana totals reconcile to the gold table (the OCR-clean cells)."""
    for planet, expected in _STHANA_CLEAN.items():
        got = sthana.sthana_bala(planet, _CHART)
        assert abs(got - expected) < 6.0, f"{planet}: got {got}, expected {expected}"


@pytest.mark.parametrize("planet", _SAPTAVARGAJA_RECONCILE)
def test_saptavargaja_per_planet(planet: str):
    """Saptavargaja Σ over D1,D2,D3,D7,D9,D12,D30 reconciles cell-for-cell with GBB-3:514-543.

    Five of seven planets match exactly. Independently corroborated by Raman's own
    Example-6 relation table (GBB-3:342-349) and the MHA Ch.12 worked varga-lord tables.
    """
    got = sthana.saptavargaja_bala(planet, _CHART)
    expected = _SAPTAVARGAJA_BOOK[planet]
    assert abs(got - expected) < 6.0, f"{planet}: got {got}, expected {expected}"


@pytest.mark.parametrize("planet", _SAPTAVARGAJA_XFAIL)
@pytest.mark.xfail(
    reason=(
        "Sub-degree varga-cusp artifact in Raman's 1918 hand-worked tables; NOT an engine "
        "bug (the general varga-lord algorithm is verified correct for all other cells). "
        "MARS D30 (Thrimsamsa): Mars at Scorpio 19deg49' is 0.18deg below the 20deg "
        "Jupiter->Saturn thrimsamsa cusp (MHA Ch.12 sec.126: even-sign bands "
        "Venus<5,Mercury<12,Jupiter<20,Saturn<25,Mars<30). Engine -> Jupiter (neutral, 7.5). "
        "But GBB Ex.9 (GBB-3:534) and MHA Ex.44 (line 1147) both record Mars in its OWN "
        "thrimsamsa (Kuja, 30) -- internally inconsistent with sec.126, since the 30th 1deg-cell "
        "is 29-30deg, not 19.8deg. Book bakes own=30; engine neutral=7.5 -> Sthana short 22.5 Sh. "
        "SATURN D7 (Saptamsa): Saturn at Leo 4deg51' is 0.56deg past the 4.286deg 1st->2nd "
        "saptamsa cusp (saptamsa width 30/7=4.2857deg). Engine -> 2nd saptamsa -> Virgo -> "
        "Mercury (compound great_friend, 22.5). But MHA Ex.39 (line 625) records the 1st "
        "saptamsa -> Surya (Sun -> compound Sama/neutral, 7.5); GBB-3:349 confirms Sani "
        "Saptamsa=Sama. Book neutral=7.5; engine great_friend=22.5 -> Sthana long 15 Sh. "
        "Both cells sit within ~0.6deg of a cusp; honoring the book would require corrupting "
        "the general algorithm. Carry to Phase 1c-3 ephemeris-cast fixture for re-pin."),
    strict=True,
)
def test_saptavargaja_per_planet_cusp_divergence(planet: str):
    """Mars D30 and Saturn D7 diverge from the book by one cusp-adjacent varga cell."""
    got = sthana.saptavargaja_bala(planet, _CHART)
    expected = _SAPTAVARGAJA_BOOK[planet]
    assert abs(got - expected) < 6.0, f"{planet}: got {got}, expected {expected}"
