"""End-to-end Shadbala orchestration for a real (ephemeris) chart.

`compute_shadbala` ties the 6 graha-bala components + ishta/kashta together for
the canonical Bangalore baseline; the adapter then attaches the result to every
`PlanetPos`.

Canonical baseline: Bangalore 1990-07-15 12:00 IST, lat 12.97, lon 77.59, tz +5.5.

Usage:
    py -3.12 -m pytest tests/raman_saab/chart/test_shadbala_compute.py -q
"""
from __future__ import annotations

import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.model import BirthData, ShadbalaBreakdown
from app.raman_saab.chart.shadbala_compute import compute_shadbala

_BLR = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _compute() -> dict[str, tuple[ShadbalaBreakdown, float, float]]:
    chart = cast_chart(_BLR, ayanamsa="raman")
    with sidereal_mode("raman"):
        ayan_deg = swe.get_ayanamsa_ut(chart.jd_ut)
    return compute_shadbala(chart, _BLR, ayan_deg)


def test_returns_a_breakdown_for_all_seven_grahas() -> None:
    """compute_shadbala covers exactly the 7 visible planets (no nodes)."""
    out = _compute()
    assert set(out) == set(_SEVEN)
    for p in _SEVEN:
        br, ishta, kashta = out[p]
        assert isinstance(br, ShadbalaBreakdown)


def test_totals_are_in_a_plausible_rupa_band() -> None:
    """Every planet's total Shadbala (Rupas = total/60) is positive and < 12."""
    out = _compute()
    for p in _SEVEN:
        br, _i, _k = out[p]
        rupas = br.total / 60.0
        assert 0.0 < rupas < 12.0, f"{p} total/60 = {rupas} out of band"


def test_ishta_kashta_in_zero_to_sixty() -> None:
    """Ishta and Kashta phala are Shashtiamsa scores bounded [0, 60]."""
    out = _compute()
    for p in _SEVEN:
        _br, ishta, kashta = out[p]
        assert 0.0 <= ishta <= 60.0, f"{p} ishta={ishta}"
        assert 0.0 <= kashta <= 60.0, f"{p} kashta={kashta}"


def test_total_equals_sum_of_six_components() -> None:
    """The assembled total is the (rounded) sum of the six components."""
    out = _compute()
    for p in _SEVEN:
        br, _i, _k = out[p]
        manual = br.sthana + br.dig + br.kala + br.cheshta + br.naisargika + br.drik
        assert abs(br.total - round(manual, 3)) < 1e-6


def test_sun_and_moon_carry_zero_cheshta() -> None:
    """Cheshta Bala is awarded only to the 5 star-planets; Sun/Moon get 0 (GBB-6:23-28)."""
    out = _compute()
    assert out["Sun"][0].cheshta == 0.0
    assert out["Moon"][0].cheshta == 0.0
