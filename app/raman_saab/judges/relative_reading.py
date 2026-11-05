"""Derivative-house relative reading (Bhavat Bhavam) — a REPORT-ONLY surface.

Reads a RELATIVE from the native's OWN chart by rotating the relative's kāraka-house into a lagna
and re-deriving that relative's twelve bhavas from it: the mother's house is the 4th, so her
longevity is the 8th-from-4th (= the 11th), her marriage the 7th-from-4th (= the 10th), and so on.

Raman works this rotation in his own nativities — the spouse's maraka is read from the 7th
("Mars is the 7th lord from the 7th and becomes a maraka … the chart indicates widowhood",
HTJAH-II:17826), the father's death from the 9th and the 8th-from-the-9th (HTJAH-II:7891, 8578).
Generalising it to "read any relative as a lagna" is the standard derivative-house principle
(``RAMAN_GENERAL_PRINCIPLE``); the fully-worked "judge the relative's whole life + longevity"
chain is classical (Jaimini/Rath), so this surface stays DESCRIPTIVE (occupancy + aspect + the
malefic-affliction note), never a verdict.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path — the golden ratchet is
untouched by construction, exactly like ``saptamsa_reading.py`` / ``two_spouse_children.py``.

Usage:
    from app.raman_saab.judges.relative_reading import build_family_derivative_reading
    fr = build_family_derivative_reading(chart)
    fr.relatives[0].matters   # the mother's derived constitution / longevity / marriage / ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.judges.saptamsa_reading import Tagged
from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS
from app.raman_saab.ordinals import ordinal

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

# role -> (the relative's kāraka-house in the native's chart, the naisargika kāraka).
_RELATIVES: Final[dict[str, tuple[int, str]]] = {
    "mother": (4, "Moon"),
    "father": (9, "Sun"),
    "spouse": (7, "Venus"),
    "sibling": (3, "Mars"),
    "child": (5, "Jupiter"),
}

# (derived matter, offset-from-the-relative's-lagna). 1 = the relative's own body/constitution.
_MATTERS: Final[tuple[tuple[str, int], ...]] = (
    ("constitution / body", 1),
    ("longevity", 8),
    ("marriage / partner", 7),
    ("children", 5),
    ("fortune", 9),
)

# Raman-explicit rotations that anchor the general principle, cited per relative in the notes.
_RAMAN_ANCHOR: Final[dict[str, str]] = {
    "spouse": "the spouse's maraka read from the 7th (HTJAH-II:17826)",
    "father": "the father's death read from the 9th and the 8th-from-9th (HTJAH-II:7891, 8578)",
}


@dataclass(frozen=True)
class DerivedMatter:
    """One matter of the relative, in the house derived from their kāraka-house-as-lagna."""
    matter: str
    offset: int                       # houses from the relative's lagna (1 = itself)
    native_house: int                 # the resulting house in the NATIVE's chart (1..12)
    sign: int
    lord: str
    occupants: tuple[str, ...]
    aspecting: tuple[str, ...]
    affliction: Optional[Tagged]      # malefic on/aspecting the derived house -> a tagged note


@dataclass(frozen=True)
class RelativeReading:
    """One relative, read by rotating their kāraka-house into a lagna (Bhavat Bhavam)."""
    role: str
    karaka: str
    base_house: int                   # the relative's lagna = their kāraka-house in this chart
    base_sign: int
    matters: tuple[DerivedMatter, ...]
    notes: tuple[Tagged, ...]


@dataclass(frozen=True)
class FamilyDerivativeReading:
    """Every relative read from the native's own chart — REPORT-ONLY, nets no verdict."""
    relatives: tuple[RelativeReading, ...]
    notes: tuple[Tagged, ...]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _house_of_sign(from_sign: int, offset: int) -> int:
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _occupants(chart: RamanChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                if n in chart.planets and chart.planets[n].rasi_house == house)


def _malefic_affliction(occ: tuple[str, ...], asp: tuple[str, ...], matter: str) -> Optional[Tagged]:
    mal = [n for n in _PLANET_ORDER
           if n in NATURAL_MALEFICS and (n in occ or n in asp)]
    if not mal:
        return None
    where = "on" if any(n in occ for n in mal) else "aspecting"
    return Tagged(f"{', '.join(mal)} {where} the derived {matter} house — an affliction to it",
                  "RAMAN_GENERAL_PRINCIPLE")


def _derived_matter(chart: RamanChart, base_house: int, matter: str, offset: int) -> DerivedMatter:
    native_house = _house_of_sign(base_house, offset)
    sign = _house_of_sign(chart.asc_sign, native_house)
    occ = _occupants(chart, native_house)
    asp = tuple(drishti.aspecting_house(native_house, chart))
    return DerivedMatter(matter=matter, offset=offset, native_house=native_house, sign=sign,
                         lord=SIGN_LORDS[sign], occupants=occ, aspecting=asp,
                         affliction=_malefic_affliction(occ, asp, matter))


def build_relative_reading(chart: RamanChart, role: str) -> RelativeReading:
    """Read one relative (``role`` in ``_RELATIVES``) as a lagna from the native's chart."""
    if role not in _RELATIVES:
        raise ValueError(f"unknown relative role {role!r}; use one of {sorted(_RELATIVES)}")
    base_house, karaka = _RELATIVES[role]
    matters = tuple(_derived_matter(chart, base_house, m, off) for m, off in _MATTERS)
    notes = [Tagged(
        f"the {role} is read as a lagna from their kāraka-house (the {ordinal(base_house)}) — the "
        "derivative-house (Bhavat Bhavam) rotation", "RAMAN_GENERAL_PRINCIPLE")]
    if role in _RAMAN_ANCHOR:
        notes.append(Tagged(f"Raman applies this rotation directly: {_RAMAN_ANCHOR[role]}",
                            "RAMAN_EXPLICIT"))
    notes.append(Tagged(
        f"corroborate from the kāraka-as-lagna frame too ({karaka} as the {role}'s lagna)",
        "RAMAN_GENERAL_PRINCIPLE"))
    return RelativeReading(role=role, karaka=karaka, base_house=base_house,
                           base_sign=_house_of_sign(chart.asc_sign, base_house),
                           matters=matters, notes=tuple(notes))


def build_family_derivative_reading(chart: RamanChart) -> FamilyDerivativeReading:
    """Read every relative (mother/father/spouse/sibling/child) from the native's own chart."""
    relatives = tuple(build_relative_reading(chart, role) for role in _RELATIVES)
    notes = (
        Tagged("REPORT-ONLY: imported by nothing in the D1 verdict path; the golden ratchet is "
               "untouched by construction.", "RAMAN_GENERAL_PRINCIPLE"),
        Tagged("Derivative-house reading is descriptive (occupancy + aspect), not a verdict on the "
               "relative — the fully-worked 'judge the relative's whole life' chain is classical "
               "(Jaimini/Rath), not read here.", "CLASSICAL_NONCITABLE"),
    )
    return FamilyDerivativeReading(relatives=relatives, notes=notes)
