"""Bhangas: cancellation and exchange primitives for the Raman Saab engine.

Covers neecha-bhanga (cancellation of debilitation), effective_dignity,
parivartana (exchange), and kemadruma (Moon isolation yoga) + cancellation.

Usage:
    python -m app.raman_saab.primitives.bhangas  # (no CLI; import only)

Citation note
-------------
The on-disk corpus files referenced in the plan
(``data/knowledge_library/sources/hindu_predictive_astrology_raman/`` and
``how_to_judge_a_horoscope_raman/``) are not present on disk.  The nearest
available Raman on-disk reference is the methodology overview which cites the
8 Considerations at HTJAH-I:474-493 (consideration 5: exaltation/debilitation
of lords) and the longevity section HPA-14.  The neecha-bhanga 4-condition
list (dispositor/planet-exalted-here in kendra from lagna/moon; conjunction
with dispositor; navamsa exaltation/vargottama) is the **standard
Parashari/Phaladeepika doctrine** that Raman's HPA accepts verbatim — it is
not independently enumerated in the available on-disk Raman corpus.  Per the
project citation-discipline policy, the comment below cites the nearest
available Raman line (HTJAH-I:475 — consideration 5) and documents that the
4-condition set is standard doctrine accepted by the project.  The same
applies to kemadruma (Moon isolation), which Raman discusses in HPA but whose
chapter file is absent from the corpus.

Phase-2 deferral: conditions that classically use *aspect* (dispositor
aspecting the debilitated planet; benefic aspecting the Moon for kemadruma
cancellation) are deferred to Phase 2 (drishti engine) and marked below.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import relationships as r
from app.raman_saab.primitives.dignity import dignity

_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})

# Planet exalted in each sign (inverse of relationships.EXALTATION), for neecha-bhanga cond 2.
_EXALTED_IN_SIGN: Final[dict[int, str]] = {sign: p for p, (sign, _deg) in r.EXALTATION.items()}


def _in_kendra_from(planet: str, ref_house: int, chart: RamanChart) -> bool:
    """Is `planet` in a kendra (1/4/7/10) counted from rasi-house `ref_house`?"""
    if planet not in chart.planets:
        return False
    dist = ((chart.planets[planet].rasi_house - ref_house) % 12) + 1
    return dist in _KENDRA


def exchange(a: str, b_: str, chart: RamanChart) -> bool:
    """Parivartana between two planets: each occupies a sign owned by the other."""
    if a not in chart.planets or b_ not in chart.planets:
        return False
    return (SIGN_LORDS[chart.planets[a].sign] == b_ and
            SIGN_LORDS[chart.planets[b_].sign] == a)


def parivartana(h1: int, h2: int, chart: RamanChart) -> bool:
    """Exchange between the LORDS of houses h1 and h2 (rasi-house lords from the Lagna)."""
    lord1 = SIGN_LORDS[((chart.asc_sign - 1) + (h1 - 1)) % 12 + 1]
    lord2 = SIGN_LORDS[((chart.asc_sign - 1) + (h2 - 1)) % 12 + 1]
    if lord1 == lord2 or lord1 not in chart.planets or lord2 not in chart.planets:
        return False
    return (chart.planets[lord1].rasi_house == h2 and
            chart.planets[lord2].rasi_house == h1)


def neecha_bhanga(planet: str, chart: RamanChart) -> bool:
    """Cancellation of debilitation (neecha-bhanga raja yoga).

    Nearest Raman on-disk citation: HTJAH-I:475 (consideration 5 —
    exaltation/debilitation of the lords).  The 4-condition set below is the
    standard Parashari/Phaladeepika cancellation-of-debilitation doctrine that
    B.V. Raman's Hindu Predictive Astrology accepts; the HPA corpus file is
    absent from disk so an exact HPA line cannot be supplied (see module
    docstring).

    Computable conditions implemented here (Phase 1b):
      (1) dispositor of the debilitation sign is in a kendra from Lagna or Moon
      (2) the planet exalted in that sign is in a kendra from Lagna or Moon
      (3) conjunct its dispositor (same rasi-house)
      (4) exalted in navamsa, or vargottama

    Deferred to Phase 2 (drishti engine):
      aspect-by-dispositor on the debilitated planet.
    """
    if planet in ("Rahu", "Ketu") or planet not in chart.planets:
        return False
    if dignity(planet, chart) != "debil":
        return False
    p = chart.planets[planet]
    lagna_h = 1
    moon_h = chart.planets["Moon"].rasi_house if "Moon" in chart.planets else 1
    dispositor = SIGN_LORDS[p.sign]                      # lord of the debilitation sign
    exalted_here = _EXALTED_IN_SIGN.get(p.sign)          # planet exalted in that sign
    # (1) dispositor in a kendra from Lagna or Moon
    if _in_kendra_from(dispositor, lagna_h, chart) or _in_kendra_from(dispositor, moon_h, chart):
        return True
    # (2) the planet exalted in this sign is in a kendra from Lagna or Moon
    if exalted_here and (_in_kendra_from(exalted_here, lagna_h, chart)
                         or _in_kendra_from(exalted_here, moon_h, chart)):
        return True
    # (3) conjunct its dispositor (same rasi-house)  [aspect variant -> Phase 2]
    if dispositor in chart.planets and chart.planets[dispositor].rasi_house == p.rasi_house:
        return True
    # (4) exalted in navamsa, or vargottama
    if p.vargottama or p.navamsa_sign == r.EXALTATION[planet][0]:
        return True
    return False


def effective_dignity(planet: str, chart: RamanChart) -> str:
    """Dignity with neecha-bhanga applied: a cancelled debilitation reports
    'neecha_bhanga' rather than 'debil'."""
    d = dignity(planet, chart)
    if d == "debil" and neecha_bhanga(planet, chart):
        return "neecha_bhanga"
    return d


def kemadruma(chart: RamanChart) -> bool:
    """Kemadruma yoga: the Moon has no planet (excluding Sun and nodes) in the
    2nd or 12th from it and none conjunct it.

    Nearest Raman on-disk citation: HTJAH-I:475 (consideration 5 — yoga
    alters the influence).  The kemadruma definition is from B.V. Raman's
    Hindu Predictive Astrology; the HPA corpus file is absent from disk (see
    module docstring).  This implements the standard doctrine: Moon isolated
    from all planets except Sun/Rahu/Ketu in the adjacent houses and in
    conjunction.

    NOTE: The aspect-based cancellation condition (benefic aspecting the Moon)
    is deferred to Phase 2 (drishti engine).
    """
    if "Moon" not in chart.planets:
        return False
    mh = chart.planets["Moon"].rasi_house
    neighbours = {(mh % 12) + 1, ((mh - 2) % 12) + 1, mh}   # 2nd, 12th, conjunct
    for name, pl in chart.planets.items():
        if name in ("Moon", "Sun", "Rahu", "Ketu"):
            continue
        if pl.rasi_house in neighbours:
            return False
    return True


def kemadruma_bhanga(chart: RamanChart) -> bool:
    """Kemadruma cancellation (computable subset): a planet other than the Moon
    in a kendra from the Lagna, or the Moon itself in a kendra from the Lagna.

    Nearest Raman on-disk citation: HTJAH-I:475 (yoga alters the influence).
    Full cancellation list (including aspect-based) from HPA — deferred to
    Phase 2 (drishti engine).
    """
    if "Moon" not in chart.planets:
        return False
    if chart.planets["Moon"].rasi_house in _KENDRA:
        return True
    for name, pl in chart.planets.items():
        if name in ("Moon", "Rahu", "Ketu"):
            continue
        if pl.rasi_house in _KENDRA:
            return True
    return False
