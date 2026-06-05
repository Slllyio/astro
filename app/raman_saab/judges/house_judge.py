"""House judge — synthesise an ordinal verdict for a house from its fired rules and
the strength of its three pillars (House / Lord / Karaka). Spec §6.3.

Verdict is an explicit ordinal, never a false-precision score:
    favourable | mixed | afflicted | insufficient-evidence

This is the house-level v1: one verdict per house. The per-signification routing
(each signification judged through its own karaka — spec §6.1) is the next refinement;
the fired-rule evidence + citations it needs are already produced here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA
from app.raman_saab.judges import rule_firing as rf
from app.raman_saab.primitives.shadbala import total as shadbala_total

Verdict = Literal["favourable", "mixed", "afflicted", "insufficient-evidence"]


@dataclass(frozen=True)
class HouseVerdict:
    house: int
    verdict: Verdict
    lord: str
    karaka: str
    lord_strong: Optional[bool]      # None when Shadbala isn't computed (Track-B chart)
    karaka_strong: Optional[bool]
    benefic: tuple[rf.FiredRule, ...]   # fired rules, by polarity — the cited evidence
    malefic: tuple[rf.FiredRule, ...]
    neutral: tuple[rf.FiredRule, ...]


def _lord_of(house: int, chart: RamanChart) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _strong(planet: str, chart: RamanChart) -> Optional[bool]:
    p = chart.planets.get(planet)
    if p is None or p.shadbala_rupas is None:
        return None
    return shadbala_total.is_powerful(planet, p.shadbala_rupas.total / 60.0)


def _synthesise(benefic, malefic, neutral, lord_strong, karaka_strong) -> Verdict:
    """The §6.3 decision rule, house-level. When strength is unknown (Track-B), decide on
    rule polarity alone."""
    if benefic and malefic:
        return "mixed"                                   # contradiction shown, never hidden
    if lord_strong is None or karaka_strong is None:     # no Shadbala -> polarity only
        if malefic:
            return "afflicted"
        if benefic:
            return "favourable"
        return "insufficient-evidence"
    both_strong = lord_strong and karaka_strong
    if malefic and not both_strong:
        return "afflicted"
    if benefic and both_strong:
        return "favourable"
    if both_strong and not malefic:
        return "favourable"
    if not lord_strong and not karaka_strong:
        return "afflicted"
    if not benefic and not malefic and not neutral:
        return "insufficient-evidence"
    return "mixed"                                        # borderline: strength split / mixed evidence


def judge_house(chart: RamanChart, house: int) -> HouseVerdict:
    lord = _lord_of(house, chart)
    karaka = BHAVA_KARAKA[house]
    fired = rf.fire_house(chart, house)
    benefic = tuple(f for f in fired if f.rule.polarity == "benefic")
    malefic = tuple(f for f in fired if f.rule.polarity == "maraka" or f.rule.polarity == "malefic")
    neutral = tuple(f for f in fired if f.rule.polarity == "neutral")
    lord_strong, karaka_strong = _strong(lord, chart), _strong(karaka, chart)
    verdict = _synthesise(benefic, malefic, neutral, lord_strong, karaka_strong)
    return HouseVerdict(house=house, verdict=verdict, lord=lord, karaka=karaka,
                        lord_strong=lord_strong, karaka_strong=karaka_strong,
                        benefic=benefic, malefic=malefic, neutral=neutral)


def judge_all_houses(chart: RamanChart) -> list[HouseVerdict]:
    return [judge_house(chart, h) for h in range(1, 13)]
