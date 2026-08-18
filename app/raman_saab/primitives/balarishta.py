"""Balarishta gate — infant-mortality yoga detector + antidote checker.

Implements a faithful cited subset of Raman's HPA Chapter 14 combinations
(yogas at HPA-14:90-115; antidotes at HPA-14:232-266).

Phase 2: yoga 3's "without being aspected by benefics" now uses the drishti
engine (benefic conjunct OR aspecting the Moon). Antidote 9's "Full Moon aspects
lagna" remains a conjunction proxy (needs a Full-Moon test) — flagged below.

Usage:
    python -m app.raman_saab.primitives.balarishta   # (no CLI; pure library)
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import BalarishtaState, RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS, NATURAL_MALEFICS
from app.raman_saab.primitives.shadbala import total as shadbala_total

_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})

# Raman's Moon-affliction balarishta house set is the 7th/8th/12th (HPA-14:96-98).
# The text reads: "The Moon in the 7th, 8th and the 12th houses from the ascendant
# with malefics and without being aspected by benefics."  NOT 6/8/12.
_BALA_MOON_HOUSES: Final[frozenset[int]] = frozenset({7, 8, 12})


def _conjunct_malefic(house: int, chart: RamanChart) -> bool:
    """True if any natural malefic occupies `house` (same rasi-house)."""
    return any(
        n in NATURAL_MALEFICS and p.rasi_house == house
        for n, p in chart.planets.items()
    )


def _has_benefic_with_moon(chart: RamanChart) -> bool:
    """True if a natural benefic (other than the Moon) is **with or aspecting** the
    Moon — Raman's "without being aspected by benefics" protection (HPA-14:96).
    Conjunction OR drishti aspect (Phase 2)."""
    mh = chart.planets["Moon"].rasi_house
    for n, p in chart.planets.items():
        if n not in NATURAL_BENEFICS or n == "Moon":
            continue
        if p.rasi_house == mh or drishti.aspects_planet(n, "Moon", chart):
            return True
    return False


def _lagna_lord_powerful(lagna_lord: str, chart: RamanChart) -> bool:
    """True if the lagna lord is 'powerfully situated' (HPA-14:235).

    Prefers the real Shadbala test (total/60 >= MIN_REQUIRED[lagna_lord]) when the
    chart carries Shadbala for the lagna lord; falls back to the Track-B dignity/kendra
    proxy (lagna lord in a kendra/trikona, or dignity in {exalt, own, moolatrikona})
    when Shadbala is absent.
    """
    ll = chart.planets[lagna_lord]
    if ll.shadbala_rupas is not None:
        req = shadbala_total.MIN_REQUIRED.get(lagna_lord)
        return req is not None and (ll.shadbala_rupas.total / 60.0) >= req
    # Track-B proxy.
    in_good_house = ll.rasi_house in (_KENDRA | _TRIKONA)
    strong_dignity = dignity(lagna_lord, chart) in ("exalt", "own", "moolatrikona")
    return in_good_house or strong_dignity


def balarishta(chart: RamanChart) -> BalarishtaState:
    """Infant-mortality gate.

    Evaluates the computable subset of Raman's HPA-14 yogas and antidotes,
    returning a BalarishtaState(applies, cancelled, reasons) that the Phase-4
    longevity judge uses to gate the houses.

    Yogas implemented (conjunction-based v1):
      (2) Moon in a kendra with malefics.                              HPA-14:93
      (3) Moon in 7th/8th/12th with malefics, no benefic conjunct.    HPA-14:96-98
      (7) Moon in lagna, Mars in 8th, Sun in 9th, Saturn in 12th.     HPA-14:111-112

    Antidotes implemented:
      (1) Jupiter powerfully posited in the ascendant.                HPA-14:232
      (2) Lord of the lagna powerfully situated.                      HPA-14:235
          Real check (Phase 1c-3): total Shadbala/60 >= MIN_REQUIRED[lagna_lord]
          when the chart carries Shadbala; otherwise the Track-B proxy (lagna lord
          in a kendra/trikona OR in exalt/own/moolatrikona).
      (9) Full Moon aspects lagna with Jupiter in quadrants.          HPA-14:263
          v1 proxy: any natural benefic (excl. Moon) in a kendra.
          Aspect refinement deferred to Phase 2.
    """
    if "Moon" not in chart.planets:
        return BalarishtaState(applies=False, cancelled=False, reasons=())

    moon = chart.planets["Moon"]
    reasons: list[str] = []

    # ------------------------------------------------------------------ yogas
    # (2) Moon in a kendra (quadrant) with malefics.               HPA-14:93
    if moon.rasi_house in _KENDRA and _conjunct_malefic(moon.rasi_house, chart):
        reasons.append("moon_kendra_malefic")

    # (3) Moon in the 7th/8th/12th with malefics, no benefic conjunct.
    #     HPA-14:96-98  ("without being aspected by benefics" -> Phase 2 refines
    #     to full aspect; v1 uses conjunction proxy only.)
    if (
        moon.rasi_house in _BALA_MOON_HOUSES
        and _conjunct_malefic(moon.rasi_house, chart)
        and not _has_benefic_with_moon(chart)
    ):
        reasons.append("moon_7_8_12_malefic")

    # (7) Precise 4-planet yoga.                                    HPA-14:111-112
    if (
        moon.rasi_house == 1
        and any(n == "Mars" and p.rasi_house == 8 for n, p in chart.planets.items())
        and any(n == "Sun" and p.rasi_house == 9 for n, p in chart.planets.items())
        and any(n == "Saturn" and p.rasi_house == 12 for n, p in chart.planets.items())
    ):
        reasons.append("moon_lagna_mars8_sun9_sat12")

    applies = bool(reasons)

    # --------------------------------------------------------------- antidotes
    cancel_reasons: list[str] = []
    if applies:
        # (1) Jupiter powerfully posited in the ascendant.          HPA-14:232
        if (
            "Jupiter" in chart.planets
            and chart.planets["Jupiter"].rasi_house == 1
        ):
            cancel_reasons.append("jupiter_in_lagna")

        # (2) Lord of the lagna powerfully situated.                HPA-14:235
        #     Real Shadbala when present; Track-B dignity/kendra proxy otherwise.
        lagna_lord = SIGN_LORDS[chart.asc_sign]
        if lagna_lord in chart.planets and _lagna_lord_powerful(lagna_lord, chart):
            cancel_reasons.append("strong_lagna_lord")

        # (9) Full Moon aspects lagna with Jupiter in quadrants.    HPA-14:263
        #     v1 proxy: any natural benefic (excl. Moon) in a kendra.
        #     Full-aspect + Full-Moon condition -> Phase 2.
        if any(
            n in NATURAL_BENEFICS and n != "Moon" and p.rasi_house in _KENDRA
            for n, p in chart.planets.items()
        ):
            cancel_reasons.append("benefic_in_kendra")

    return BalarishtaState(
        applies=applies,
        cancelled=bool(cancel_reasons),
        reasons=tuple(reasons + cancel_reasons),
    )


# ── append-only disclosure (2026-08-18, REPORT_CRITIQUE Wave-2 item 5a) ────────
# The clear case ("does not apply") previously disclosed NOTHING about what was
# screened, so a reader could not see the method worked. These are the exact
# yogas `balarishta()` checks above, as (label, cite) pairs for report surfaces
# to render as "screened: ... — none present". Keep in lockstep with the checks.
SCREENED_CONDITIONS: Final[tuple[tuple[str, str], ...]] = (
    ("the Moon in a kendra with malefics", "HPA-14:93"),
    ("the Moon in the 7th/8th/12th with malefics, unrelieved by a benefic "
     "with or aspecting it", "HPA-14:96-98"),
    ("the Moon in the lagna with Mars in the 8th, the Sun in the 9th and "
     "Saturn in the 12th", "HPA-14:111-112"),
)


def screened_conditions() -> tuple[tuple[str, str], ...]:
    """The balarishta yogas this screen checks (label, cite) — read-only, for the
    clear-case disclosure line on report surfaces."""
    return SCREENED_CONDITIONS
