"""Chart-level overview — the spec §9 pre-pass surface for the Raman Saab engine.

Gathers, in one frozen record, the chart-level context every house judgment
reads first (methodology overview §9):

* ``stronger_frame`` — LAGNA vs MOON (Chandra Lagna) by the total Shadbala of
  their sign-LORDS; Track-B charts (no Shadbala) default to ``"lagna"``,
  matching the lead-frame rule in :mod:`house_template`.
* ``functional_natures`` — per-graha functional nature for this ascendant
  (HTJAH-I:523-604 + yogakaraka overlay), via the memoised ``EvalContext``.
* ``fired_yogas`` — every encoded yoga active in the chart
  (:func:`app.raman_saab.doctrine.yogas.detect_yogas`, HTJAH-I:480-482).
* specials — the Special Dhana Lagna sign (HTJAH-I:3229-3318) and the H5
  Beeja/Kshetra sphuta strengths (HTJAH-I:5517-5527); all ``None``-safe on
  sparse Track-B charts.

Proforma wiring lands at Phase G — ``proforma.py`` is deliberately untouched.

Usage:
    from app.raman_saab.judges.chart_overview import chart_overview
    ov = chart_overview(chart)
    ov.stronger_frame          # "lagna" | "moon"
    dict(ov.functional_natures)["Saturn"]
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.conditions import EvalContext
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.primitives.sphutas import beeja_kshetra, special_dhana_lagna

#: Canonical graha order — keeps ``functional_natures`` deterministic.
_PLANET_ORDER: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class ChartOverview:
    """The §9 chart-level pre-pass record (frozen; all specials None-safe)."""
    stronger_frame: Literal["lagna", "moon"]
    functional_natures: tuple[tuple[str, str], ...]
    fired_yogas: tuple[FiredYoga, ...]
    dhana_lagna_sign: Optional[int]       # Special Dhana Lagna rasi 1..12, or None
    beeja_strong: Optional[bool]          # H5 Beeja sphuta verdict, or None (sparse)
    kshetra_strong: Optional[bool]        # H5 Kshetra sphuta verdict, or None


def _total_shadbala(planet: str, chart: RamanChart) -> Optional[float]:
    """Total Shadbala (Shashtiamsas) of `planet`, or None on Track-B / absent."""
    p = chart.planets.get(planet)
    if p is None or p.shadbala_rupas is None:
        return None
    return p.shadbala_rupas.total


def _stronger_frame(chart: RamanChart) -> Literal["lagna", "moon"]:
    """LAGNA vs MOON by the Shadbala of their lords; any gap in the data -> lagna."""
    moon = chart.planets.get("Moon")
    if moon is None:
        return "lagna"
    lagna_sb = _total_shadbala(SIGN_LORDS[chart.asc_sign], chart)
    moon_sb = _total_shadbala(SIGN_LORDS[moon.sign], chart)
    if lagna_sb is None or moon_sb is None:
        return "lagna"
    return "moon" if moon_sb > lagna_sb else "lagna"


def chart_overview(chart: RamanChart) -> ChartOverview:
    """Assemble the §9 pre-pass surface for `chart` (pure; None-safe throughout)."""
    ctx = EvalContext(chart)
    natures = tuple(
        (p, ctx.functional_nature(p)) for p in _PLANET_ORDER if p in chart.planets)
    dl = special_dhana_lagna(chart)
    bk = beeja_kshetra(chart)
    return ChartOverview(
        stronger_frame=_stronger_frame(chart),
        functional_natures=natures,
        fired_yogas=detect_yogas(chart),
        dhana_lagna_sign=dl.sign if dl is not None else None,
        beeja_strong=bk.beeja_strong if bk is not None else None,
        kshetra_strong=bk.kshetra_strong if bk is not None else None)
