"""Tests for Kala Bala sub-components and assembly (GBB-5 §3).

Track-B: the fixture injects Raman's stated intermediates so the 9 formulae
are pinned without ephemeris.

Fixture: Raman's Standard Horoscope — birth 2:14 pm IST.
  Nirayana positions (degrees):
    Sun 179°08' · Moon 311°40' · Mars 229°49' · Mercury 180°33'
    Jupiter 83°35' · Venus 170°04' · Saturn 124°51'
  Context (Raman's stated): bd=146.5 (day birth), 3rd day-third, Saturn=year,
    Mercury=month+weekday, Moon=hora, ayanamsa 21°16'.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.shadbala import kala

# ── Shared fixture chart ───────────────────────────────────────────────────────

_NIR = {
    "Sun": 179 + 8 / 60,
    "Moon": 311 + 40 / 60,
    "Mars": 229 + 49 / 60,
    "Mercury": 180 + 33 / 60,
    "Jupiter": 83 + 35 / 60,
    "Venus": 170 + 4 / 60,
    "Saturn": 124 + 51 / 60,
}
_CHART = RamanChart.from_stated_positions(
    {p: {"lon": l, "bhava": 1} for p, l in _NIR.items()},
    asc_lon=185.0,
    ayanamsa="raman",
)

# ══════════════════════════════════════════════════════════════════════════════
# Task 1 tests: 4 longitude/time sub-components
# ══════════════════════════════════════════════════════════════════════════════


def test_nathonnatha():
    """bd=146.5 -> Diva=146.5/3≈48.83, Ratri=(180-146.5)/3≈11.17, Mercury always 60."""
    assert abs(kala.nathonnatha_bala("Sun", 146.5) - 48.83) < 0.1
    assert abs(kala.nathonnatha_bala("Moon", 146.5) - 11.17) < 0.1
    assert kala.nathonnatha_bala("Mercury", 146.5) == 60.0


def test_paksha_moon_doubled():
    """Paksha: Moon 88.34, Sun 15.83 (malefic), Jupiter 44.17 (benefic)."""
    assert abs(kala.paksha_bala("Moon", _CHART) - 88.34) < 0.2
    assert abs(kala.paksha_bala("Sun", _CHART) - 15.83) < 0.2
    assert abs(kala.paksha_bala("Jupiter", _CHART) - 44.17) < 0.2


def test_ayana_clean_cells():
    """Ayana reproduces 3 clean cells: Sun 39.82 (doubled), Jupiter 58.92, Saturn 13.75."""
    assert abs(kala.ayana_bala("Sun", _CHART, 21 + 16 / 60) - 39.82) < 0.2
    assert abs(kala.ayana_bala("Jupiter", _CHART, 21 + 16 / 60) - 58.92) < 0.2
    assert abs(kala.ayana_bala("Saturn", _CHART, 21 + 16 / 60) - 13.75) < 0.2


def test_yuddha_zero_when_no_war():
    """No planets within 1° in the standard horoscope -> Yuddha = 0 for all."""
    assert kala.yuddha_bala("Mars", _CHART, {}) == 0.0
    assert kala.yuddha_bala("Jupiter", _CHART, {}) == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Task 2 tests: 5 lord/third sub-components
# ══════════════════════════════════════════════════════════════════════════════


def test_tribhaga():
    """3rd day-third (index 2) -> Saturn 60; Jupiter always 60; Sun gets 0."""
    assert kala.tribhaga_bala("Saturn", is_day=True, day_third=2) == 60.0
    assert kala.tribhaga_bala("Jupiter", is_day=True, day_third=2) == 60.0
    assert kala.tribhaga_bala("Sun", is_day=True, day_third=2) == 0.0


def test_abda_masa_vara_hora():
    """Each lord-based sub-component awards the correct fixed Shashtiamsa amount."""
    assert kala.abda_bala("Saturn", "Saturn") == 15.0
    assert kala.masa_bala("Mercury", "Mercury") == 30.0
    assert kala.vara_bala("Mercury", "Mercury") == 45.0
    assert kala.hora_bala("Moon", "Moon") == 60.0
    assert kala.abda_bala("Sun", "Saturn") == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Task 3 tests: kala_bala assembly + fixture pin
# ══════════════════════════════════════════════════════════════════════════════

# GBB Standard Horoscope context (Raman's stated intermediates).
_CTX = kala.KalaContext(
    birth_degrees=146.5,
    is_day=True,
    day_third=2,
    year_lord="Saturn",
    month_lord="Mercury",
    weekday_lord="Mercury",
    hora_lord="Moon",
    ayanamsa=21 + 16 / 60,
)

# 5 clean Kala-column cells (Sun/Moon/Mercury/Jupiter/Saturn) — ±1 Sh tolerance.
# Mars & Venus carry the Ayana book self-inconsistency and are pinned via xfail below.
_KALA_TOTAL = {
    "Sun": 104.49,
    "Moon": 202.75,
    "Mercury": 219.92,
    "Jupiter": 211.93,
    "Saturn": 115.69,
}


def test_kala_column_clean_cells():
    """5 clean Kala cells reconcile to Raman's printed GBB table (±1 Sh)."""
    for planet, expected in _KALA_TOTAL.items():
        got = kala.kala_bala(planet, _CHART, _CTX)
        assert abs(got - expected) < 1.0, f"{planet}: got {got}, expected {expected}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Ayana book self-inconsistency: formula gives Mars 1.90 / Venus 24.30, "
        "but Raman's printed totals use 1.40 / 23.80 (off ~0.5 Sh). Engine follows "
        "the stated (24 + signed_decl)/48 formula; Mars/Venus xfail carried to 1c-3."
    ),
)
def test_kala_mars_venus_match_book_totals():
    """Mars 28.39 & Venus 116.81 require Raman's lower (inconsistent) Ayana 1.40/23.80.
    Formula gives 1.90/24.30 -> totals are ~0.5 Sh off book, exposed at 0.3 Sh tolerance."""
    assert abs(kala.kala_bala("Mars", _CHART, _CTX) - 28.39) < 0.3
    assert abs(kala.kala_bala("Venus", _CHART, _CTX) - 116.81) < 0.3
