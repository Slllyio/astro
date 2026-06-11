"""H8 — 22nd-drekkana decanate -> cause-of-death grid (the MANDATORY fallback).

Raman (HTJAH-II:3727-3731): "When these particular yogas are absent in a
horoscope, classical works refer to the lord of the 22nd drekkana to find out
the cause of death. It may also be determined from the decanate occupied by the
planet in the 8th house." The 36-cell grid below (HTJAH-II:3736-3845) keys the
bodily cause to the SIGN in which the 22nd drekkana (or the 8th-occupant's
decanate) falls plus the decanate index 1-3 within it. The printed decanate
lords follow the classical drekkana scheme (lords of the 1st/5th/9th signs
therefrom) and are carried verbatim.

This is pure doctrine data returned as judge metadata — no scoring logic.

Data source: docs/raman_saab/methodology/house_08_ayur.md (decanate table),
verified against the corpus HTJAH-II:3736-3845.

Usage:
    from app.raman_saab.doctrine.lookups.decanate_cause import cause_of_death_fallback
    rec = cause_of_death_fallback("Capricorn", 2)   # -> Venus, "snake-bite"
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from app.raman_saab.doctrine.sources import Citation


@dataclass(frozen=True)
class DecanateCause:
    """One cell of the 22nd-drekkana cause-of-death grid.

    Fields
    ------
    sign : str
        Sign the 22nd drekkana (or the 8th-occupant's decanate) falls in.
    decanate_index : int
        Decanate within the sign, 1-3.
    decanate_lord : str
        Printed decanate lord (classical 1st/5th/9th drekkana scheme).
    cause : str
        Cause / manner of death as printed.
    sources : tuple[Citation, ...]
        Corpus line(s) carrying this cell.
    """
    sign: str
    decanate_index: int
    decanate_lord: str
    cause: str
    sources: tuple[Citation, ...]


def _c(line: int) -> Citation:
    return Citation("HTJAH-II", line)


def _cell(sign: str, idx: int, lord: str, cause: str,
          *lines: int) -> tuple[tuple[str, int], DecanateCause]:
    rec = DecanateCause(sign=sign, decanate_index=idx, decanate_lord=lord,
                        cause=cause, sources=tuple(_c(ln) for ln in lines))
    return (sign, idx), rec


# 36-cell grid, HTJAH-II:3736-3845 — one row per (sign, decanate).
DECANATE_CAUSES: Final[Mapping[tuple[str, int], DecanateCause]] = MappingProxyType(dict((
    _cell("Aries", 1, "Mars", "spleen and bilious complaints or poisoning", 3738, 3739),
    _cell("Aries", 2, "Sun", "watery diseases", 3741),
    _cell("Aries", 3, "Jupiter", "drowning in water", 3742),
    _cell("Taurus", 1, "Venus", "asses, horses, mules", 3745),
    _cell("Taurus", 2, "Mercury", "bilious complaints, fire or murder", 3747, 3748),
    _cell("Taurus", 3, "Saturn", "fall from a horse or building", 3750),
    _cell("Gemini", 1, "Mercury", "cough, lung infections, bronchitis", 3754, 3755),
    _cell("Gemini", 2, "Venus", "typhoid", 3759),
    _cell("Gemini", 3, "Saturn", "fall from a conveyance or height", 3761, 3762),
    _cell("Cancer", 1, "Moon", "drinks, thorns", 3766),
    _cell("Cancer", 2, "Mars", "poison", 3768),
    _cell("Cancer", 3, "Jupiter", "tumour, hallucinations, syncope", 3770, 3771),
    _cell("Leo", 1, "Sun", "drinking contaminated water", 3775),
    _cell("Leo", 2, "Jupiter", "water in the lungs, dropsy", 3777, 3779),
    _cell("Leo", 3, "Mars", "travel-sickness, surgery", 3781),
    _cell("Virgo", 1, "Mercury", "headache, wind disease", 3785),
    _cell("Virgo", 2, "Saturn", "fall from a height", 3787),
    _cell("Virgo", 3, "Venus", "explosion, glass, drowning", 3789),
    _cell("Libra", 1, "Venus", "woman, fall, animal", 3793),
    _cell("Libra", 2, "Saturn", "indigestion, gastritis", 3795),
    _cell("Libra", 3, "Mercury", "water, snakes", 3797),
    _cell("Scorpio", 1, "Mars", "poison, weapons", 3801),
    _cell("Scorpio", 2, "Jupiter",
          "prostate trouble, carrying heavy weights, complaints in hip", 3803, 3805),
    _cell("Scorpio", 3, "Moon", "earth (mines), stones", 3805, 3807),
    _cell("Sagittarius", 1, "Jupiter", "anal and colon complaints", 3811),
    _cell("Sagittarius", 2, "Mars", "poison, arrows, sharp instruments", 3813, 3815),
    _cell("Sagittarius", 3, "Sun",
          "abdominal complaints, water, or aquatic animals", 3815, 3816),
    _cell("Capricorn", 1, "Saturn",
          "mauling by lion or wild animal, scorpion sting", 3822, 3823),
    _cell("Capricorn", 2, "Venus", "snake-bite", 3825),
    _cell("Capricorn", 3, "Mercury", "thieves, gun shot, fever", 3827),
    _cell("Aquarius", 1, "Saturn",
          "woman, pelvic disorder, venereal complaints", 3831, 3832),
    _cell("Aquarius", 2, "Mercury",
          "disease in internal organs of generative system", 3834, 3835),
    _cell("Aquarius", 3, "Venus", "infection", 3837),
    _cell("Pisces", 1, "Jupiter", "dysentery, ascites, oesophagitis", 3840, 3841),
    _cell("Pisces", 2, "Moon", "dropsy, oesophagitis", 3843),
    _cell("Pisces", 3, "Mars", "distension of the stomach", 3844),
)))

_VALID_SIGNS: Final[frozenset[str]] = frozenset(sign for sign, _ in DECANATE_CAUSES)


def cause_of_death_fallback(drekkana_sign: str, decanate_index: int) -> DecanateCause:
    """Grid cell for the 22nd-drekkana sign + decanate index (1-3).

    This is the mandatory fallback when no killer combination fires
    (HTJAH-II:3727-3731). Raises ValueError on an unknown sign or index.
    """
    if drekkana_sign not in _VALID_SIGNS:
        raise ValueError(f"unknown sign for decanate lookup: {drekkana_sign!r}")
    if decanate_index not in (1, 2, 3):
        raise ValueError(f"decanate_index must be 1-3, got {decanate_index!r}")
    return DECANATE_CAUSES[(drekkana_sign, decanate_index)]
