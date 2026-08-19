"""The 6th-house medical read — Raman's own procedure from HPA-29 §10.

This is the reader for `doctrine/medical_astrology.py`. It answers the question the
health section's own subtitle asks — *which body areas does this chart mark* — which the
report has until now answered with house numbers, because the tables were not encoded.

RAMAN'S PROCEDURE, VERBATIM (HPA-29:433-440), and this module follows it literally:

    "The house of diseases is the sixth from the ascendant. The planets therein, the lord
    of the sixth, the aspects on the 6th and the navamsa the lord of the 6th occupies,
    should all be considered for predicting diseases. The planet in the 6th house affect
    the particular part of the body governed by the sign, and the diseases will be those
    that are indicated by its rulers."

Four testimonies, each named in that sentence, each surfaced separately so a reader can
see which clause produced which line:

  1. the SIGN on the 6th          -> the body regions marked (HPA-29 §6)
  2. the PLANETS in the 6th       -> their diseases (HPA-29 §9), and per the last clause
                                     they act ON the region the 6th sign governs
  3. the LORD of the 6th          -> its diseases, plus the navamsa it occupies, whose
                                     sign contributes its own regions
  4. the planets ASPECTING the 6th -> their diseases

WHAT THIS IS NOT. Not a diagnosis, not a prediction, and not a verdict. It reports a
classical correspondence table indexed by this chart's own 6th-house testimony, and every
surface carries `medical_astrology.CAVEAT`. The nodes contribute NOTHING: Raman's tables
cover the seven visible grahas, and inventing a Rahu or Ketu row would be the
mint-from-memory the PRIME DIRECTIVE forbids — so a node in the 6th is reported as
present-but-unlisted rather than silently skipped.

VERDICT-AUTHORITY INVARIANT: imported by nothing in the D1 verdict path. The golden
ratchet is untouched by construction, and a test enforces it.

Usage:
    from app.raman_saab.judges.medical_reading import build_medical_reading
    mr = build_medical_reading(chart)
    mr.regions_marked        # body areas the 6th sign governs
    mr.testimonies           # one row per clause of HPA-29 §10
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.medical_astrology import (
    APPLICATION, CAVEAT, CITE_APPLICATION, CITE_PLANET_RULERSHIP, CITE_SIGN_ANATOMY,
    CITE_SIGN_DISEASES, PROVENANCE_NOTE, planet_diseases, planet_organs,
    sign_anatomy, sign_diseases)

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
_NODES: Final[frozenset[str]] = frozenset({"Rahu", "Ketu"})

_SIGNS: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces")


@dataclass(frozen=True)
class MedicalTestimony:
    """One clause of HPA-29 §10, with what it contributed."""
    clause: str                    # which of Raman's four testimonies this is
    actor: str                     # the sign or graha speaking
    regions: tuple[str, ...]       # body regions it marks (may be empty)
    complaints: tuple[str, ...]    # complaints it indicates (may be empty)
    why: str                       # the sentence tying actor to chart
    citation: str


@dataclass(frozen=True)
class MedicalReading:
    """The 6th-house medical read — classical correspondence, never a diagnosis."""
    sixth_sign: int
    sixth_sign_name: str
    sixth_lord: str
    sixth_lord_house: int
    sixth_lord_navamsa_sign: int
    occupants: tuple[str, ...]
    aspecting: tuple[str, ...]
    unlisted_bodies: tuple[str, ...]      # nodes present in the testimony, table-less
    regions_marked: tuple[str, ...]       # union, de-duplicated, order-stable
    complaints_indicated: tuple[str, ...]
    testimonies: tuple[MedicalTestimony, ...]
    #: Raman's rule verbatim — carried on the reading so every surface quotes the same
    #: sentence rather than each renderer importing the doctrine module separately.
    application: str
    caveat: str
    provenance: str


def _sign_name(sign: int) -> str:
    return _SIGNS[sign - 1] if 1 <= sign <= 12 else f"sign {sign}"


def _house_of_sign(from_sign: int, offset: int) -> int:
    return ((from_sign - 1) + (offset - 1)) % 12 + 1


def _occupants(chart: RamanChart, house: int) -> tuple[str, ...]:
    return tuple(n for n in _PLANET_ORDER
                 if n in chart.planets and chart.planets[n].rasi_house == house)


def _dedup(items: tuple[str, ...]) -> tuple[str, ...]:
    """Order-stable de-duplication — two testimonies naming 'consumption' say it once."""
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        k = it.casefold()
        if k not in seen:
            seen.add(k)
            out.append(it)
    return tuple(out)


def build_medical_reading(chart: RamanChart) -> Optional[MedicalReading]:
    """Apply HPA-29 §10 to a chart. None when the 6th cannot be resolved (sparse Track-B)."""
    asc = int(getattr(chart, "asc_sign", 0) or 0)
    if not 1 <= asc <= 12:
        return None
    sixth = _house_of_sign(asc, 6)
    lord = SIGN_LORDS[sixth]
    lp = chart.planets.get(lord)

    testimonies: list[MedicalTestimony] = []
    unlisted: list[str] = []

    # ── 1. the sign on the 6th gives the body regions ────────────────────────
    regions = sign_anatomy(sixth)
    testimonies.append(MedicalTestimony(
        clause="the sign on the 6th — the body regions marked",
        actor=_sign_name(sixth),
        regions=regions,
        complaints=sign_diseases(sixth),
        why=(f"the 6th house from {_sign_name(asc)} lagna falls in {_sign_name(sixth)}, "
             f"and Raman reads the house of diseases from the ascendant"),
        citation=f"{CITE_SIGN_ANATOMY.work}:{CITE_SIGN_ANATOMY.line} (regions); "
                 f"{CITE_SIGN_DISEASES.work}:{CITE_SIGN_DISEASES.line} (complaints)"))

    # ── 2. planets IN the 6th — "the diseases will be those indicated by its rulers" ──
    occ = _occupants(chart, sixth)
    for p in occ:
        if p in _NODES:
            unlisted.append(p)
            continue
        testimonies.append(MedicalTestimony(
            clause="a planet in the 6th",
            actor=p,
            regions=planet_organs(p),
            complaints=planet_diseases(p),
            why=(f"{p} stands in the 6th, so by Raman's last clause it affects the part "
                 f"of the body {_sign_name(sixth)} governs, and the complaints are those "
                 f"{p} itself indicates"),
            citation=f"{CITE_PLANET_RULERSHIP.work}:{CITE_PLANET_RULERSHIP.line}"))

    # ── 3. the LORD of the 6th, and the navamsa it occupies ──────────────────
    nav = int(getattr(lp, "navamsa_sign", 0) or 0) if lp is not None else 0
    if lord not in _NODES:
        testimonies.append(MedicalTestimony(
            clause="the lord of the 6th",
            actor=lord,
            regions=planet_organs(lord),
            complaints=planet_diseases(lord),
            why=(f"{lord} owns the 6th"
                 + (f" and sits in house {lp.rasi_house}" if lp is not None else "")),
            citation=f"{CITE_PLANET_RULERSHIP.work}:{CITE_PLANET_RULERSHIP.line}"))
    if 1 <= nav <= 12:
        testimonies.append(MedicalTestimony(
            clause="the navamsa the 6th lord occupies",
            actor=_sign_name(nav),
            regions=sign_anatomy(nav),
            complaints=sign_diseases(nav),
            why=(f"Raman names the navamsa of the 6th lord as one of the four things to "
                 f"consider; {lord} occupies {_sign_name(nav)} there"),
            citation=f"{CITE_APPLICATION.work}:{CITE_APPLICATION.line} (the rule); "
                     f"{CITE_SIGN_ANATOMY.work}:{CITE_SIGN_ANATOMY.line} (regions)"))

    # ── 4. planets ASPECTING the 6th ─────────────────────────────────────────
    try:
        aspecting = tuple(drishti.aspecting_house(sixth, chart))
    except Exception:  # noqa: BLE001 — sparse Track-B chart
        aspecting = ()
    for p in aspecting:
        if p in _NODES:
            if p not in unlisted:
                unlisted.append(p)
            continue
        if p in occ:
            continue                       # already spoken for as an occupant
        testimonies.append(MedicalTestimony(
            clause="a planet aspecting the 6th",
            actor=p,
            regions=(),                    # an aspect is not occupancy; regions come
            complaints=planet_diseases(p),  # from the sign, per Raman's own clause
            why=f"{p} casts drishti on the 6th",
            citation=f"{CITE_PLANET_RULERSHIP.work}:{CITE_PLANET_RULERSHIP.line}"))

    return MedicalReading(
        sixth_sign=sixth,
        sixth_sign_name=_sign_name(sixth),
        sixth_lord=lord,
        sixth_lord_house=int(getattr(lp, "rasi_house", 0) or 0) if lp is not None else 0,
        sixth_lord_navamsa_sign=nav,
        occupants=occ,
        aspecting=aspecting,
        unlisted_bodies=tuple(unlisted),
        regions_marked=_dedup(tuple(x for t in testimonies for x in t.regions)),
        complaints_indicated=_dedup(tuple(x for t in testimonies for x in t.complaints)),
        testimonies=tuple(testimonies),
        application=APPLICATION,
        caveat=CAVEAT,
        provenance=PROVENANCE_NOTE,
    )
