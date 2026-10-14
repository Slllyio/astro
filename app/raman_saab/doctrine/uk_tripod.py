"""The Uttara Kalamrita tripod — bhava, lord and karaka, tested by the verse's own clauses.

The text, verbatim (UK ch003:1594-1606, spelling as printed):

    "(1) When a bhava, its lord, and its significator (karaka) (i) are al[l] hemmed between
     malefics, (ii) are in conjunction with malefics and are weak, and (iii) have no aspect
     from or conjunction with benefics.
     (2) (i) When malefics are in houses 4, 5, 8, 9 and 12 counted from the concerned Bhava,
     its lord and its Karaka, (ii) and when the lords of the navamsas having these malefics
     are inimical, combust, or defeated in Graha Yuddha.
     Then one has to affirm that Bhava is destroyed (literally harmed)."

**This module was reviewed and its first version FAILED (bphs-doctrine-reviewer, 2026-08-07).**
The failures are recorded because each one is a way this class of code goes wrong:

* The navamsa condition had been transplanted to the wrong subject — tested on the lord/karaka's
  OWN dispositor, when the verse attaches it to THE MALEFICS sitting 4/5/8/9/12 from each
  support ("the lords of the navamsas having these malefics"). The bhava leg is NOT exempt:
  malefics can sit in dusthanas from an empty house.
* Clause 1(iii) — no benefic aspect or conjunction — had been dropped entirely.
* The verse gives a SUFFICIENT condition for destruction, not a necessary one ("ruined only
  when" was the implementer's inversion): the preceding verse (ch003:1569-1576) destroys a
  bhava on the lord alone. This is one classical path to ruin among several.
* A seven-rupa bhava-weakness threshold had been invented; no such convention exists in the
  corpus. The engine's one documented knob (`BHAVA_BALA_MIN_SH`, golden-tuned, its own comment
  stating Raman gives no numeric cutoff) is used instead.

Interpretive choices that REMAIN, each named so review can find them:

1. **Raman's karakas inside UK's structure** (`BHAVA_KARAKA`, sourced HTJAH-I:983) — UK ch.4
   has its own significator lists; "Raman wins" applies.
2. **"Inimical" is read as naisargika enmity toward the support's planet** (the leg planet, or
   the bhava's lord for the bhava leg). UK's own notes (ch003:1625-1632) want natural and
   temporary relations fused; naisargika-only is the engine's available primitive and errs
   toward not-condemning.
3. **"Defeated in Graha Yuddha" is left undetermined** — the war test needs the full Shadbala
   pipeline. Because clause 2(ii) is a disjunction (inimical OR combust OR defeated), treating
   the war leg as unsatisfied can only under-condemn, which is the module's standing direction
   of error. Documented, not silent.

**Band discipline** unchanged: CLASSICAL_NONCITABLE, corroborative, report-layer only, no
verdict feed (PREC-10). **Conservative on missing data**: an unanswerable condition is None
and a leg never completes on absence.

Usage:
    from app.raman_saab.doctrine.uk_tripod import tripod
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.hemming import hemmed_house, hemmed_planet
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA

#: Locked sets (CLAUDE.md, Avastha convention).
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})

#: The dusthana offsets of clause 2(i): houses 4, 5, 8, 9, 12 counted from the support.
_CLAUSE2_OFFSETS: Final[frozenset[int]] = frozenset({4, 5, 8, 9, 12})

#: The five conditions, applied UNIFORMLY to all three supports — the review's central
#: correction: the verse exempts nobody.
_CONDITIONS: Final[tuple[str, ...]] = (
    "hemmed", "with_malefic_and_weak", "no_benefic_contact",
    "malefics_in_dusthanas_from", "their_navamsa_lords_afflicted",
)


@dataclass(frozen=True)
class Leg:
    """One support, tested by the verse's five conditions. None = the chart cannot answer."""

    what: str                                     # "bhava" | "lord" | "karaka"
    who: str
    hemmed: Optional[bool]
    with_malefic_and_weak: Optional[bool]         # clause 1(ii) couples them
    no_benefic_contact: Optional[bool]            # clause 1(iii)
    malefics_in_dusthanas_from: Optional[bool]    # clause 2(i)
    their_navamsa_lords_afflicted: Optional[bool] # clause 2(ii)
    conditions_applied: tuple[str, ...] = _CONDITIONS

    @property
    def failed(self) -> bool:
        vals = [getattr(self, c) for c in self.conditions_applied]
        return bool(vals) and all(v is True for v in vals)

    @property
    def unknown(self) -> tuple[str, ...]:
        return tuple(c for c in self.conditions_applied if getattr(self, c) is None)


@dataclass(frozen=True)
class Tripod:
    house: int
    legs: tuple[Leg, ...]

    @property
    def complete(self) -> bool:
        """The verse's sufficient condition: all three supports fail every clause."""
        return len(self.legs) == 3 and all(leg.failed for leg in self.legs)

    @property
    def failing(self) -> tuple[str, ...]:
        return tuple(leg.what for leg in self.legs if leg.failed)

    @property
    def pressure(self) -> int:
        """Conditions met of those applicable — the reported quantity, because the full test
        is nearly unsatisfiable by construction (measured 0 completes pre-review; the verse
        wants everything to fail at once). Says how far a house sits from the classical ruin."""
        return sum(1 for leg in self.legs
                   for c in leg.conditions_applied if getattr(leg, c) is True)

    @property
    def applicable(self) -> int:
        return sum(len(leg.conditions_applied) for leg in self.legs)

    @property
    def met(self) -> tuple[str, ...]:
        return tuple(f"{leg.what} {c.replace('_', ' ')}"
                     for leg in self.legs
                     for c in leg.conditions_applied if getattr(leg, c) is True)


# ─── shared condition machinery ─────────────────────────────────────────────────────────────

def _occupants_of_house(chart: RamanChart, house: int) -> list[str]:
    return [n for n, p in chart.planets.items() if getattr(p, "rasi_house", None) == house]


def _same_sign(chart: RamanChart, planet: str) -> list[str]:
    ps = chart.planets[planet].sign
    return [n for n, p in chart.planets.items() if n != planet and p.sign == ps]


def _no_benefic_contact_planet(chart: RamanChart, planet: str) -> bool:
    """Clause 1(iii) for a planet: no benefic conjoined (same sign) and none aspecting it."""
    from app.raman_saab.doctrine.drishti import aspects_planet
    if any(b in _BENEFICS for b in _same_sign(chart, planet)):
        return False
    return not any(aspects_planet(b, planet, chart) for b in _BENEFICS
                   if b in chart.planets)


def _no_benefic_contact_house(chart: RamanChart, house: int) -> bool:
    """Clause 1(iii) for a bhava: no benefic occupant and none aspecting the house."""
    from app.raman_saab.doctrine.drishti import aspects_house
    if any(b in _BENEFICS for b in _occupants_of_house(chart, house)):
        return False
    return not any(aspects_house(b, house, chart) for b in _BENEFICS
                   if b in chart.planets)


def _clause2(chart: RamanChart, seat_house: int, support_planet: Optional[str]
             ) -> tuple[bool, Optional[bool]]:
    """Clause 2 counted FROM the support's house seat.

    Returns (malefics_present_in_dusthanas, their_navamsa_lords_afflicted). The second is the
    verse's compound: the navamsa lords OF THOSE MALEFICS are inimical (to the support's
    planet — interpretive choice 2), combust, or defeated in war (undetermined — choice 3).
    When no malefic sits in the dusthanas, the second condition is vacuously unanswerable and
    returns None rather than True: absence of afflictors must not read as affliction.
    """
    from app.raman_saab.chart.constants import SIGN_LORDS
    from app.raman_saab.primitives.relationships import naisargika

    afflictors = [n for n, p in chart.planets.items()
                  if n in _MALEFICS
                  and ((getattr(p, "rasi_house", 0) - seat_house) % 12) + 1 in _CLAUSE2_OFFSETS]
    if not afflictors:
        return False, None

    judge = support_planet  # whom "inimical" is toward (interpretive choice 2)
    afflicted = []
    for m in afflictors:
        nav = getattr(chart.planets[m], "navamsa_sign", None)
        lord = SIGN_LORDS.get(nav) if nav else None
        if lord is None or lord not in chart.planets:
            afflicted.append(None)
            continue
        inimical = (judge is not None and naisargika(lord, judge) == "enemy")
        combust = float(getattr(chart.planets[lord], "combust_fraction", 0.0) or 0.0) > 0.0
        # defeated-in-yuddha: undetermined (interpretive choice 3) — never satisfies the OR
        afflicted.append(inimical or combust)
    if any(a is True for a in afflicted):
        return True, True
    if all(a is None for a in afflicted):
        return True, None
    return True, False


def _planet_weak(chart: RamanChart, planet: str) -> Optional[bool]:
    from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED
    p = chart.planets.get(planet)
    sb, req = getattr(p, "shadbala_rupas", None), MIN_REQUIRED.get(planet)
    if sb is None or req is None:
        return None
    return (sb.total / 60.0) < req


def _planet_leg(chart: RamanChart, what: str, planet: str) -> Leg:
    p = chart.planets.get(planet)
    if p is None:
        return Leg(what, planet, None, None, None, None, None)
    with_mal = any(x in _MALEFICS for x in _same_sign(chart, planet))
    weak = _planet_weak(chart, planet)
    both = None if (with_mal and weak is None) else (with_mal and bool(weak))
    seat = getattr(p, "rasi_house", None)
    if seat:
        c2_present, c2_afflicted = _clause2(chart, seat, planet)
    else:
        c2_present, c2_afflicted = None, None
    return Leg(what, planet,
               hemmed=hemmed_planet(chart, planet),
               with_malefic_and_weak=both,
               no_benefic_contact=_no_benefic_contact_planet(chart, planet),
               malefics_in_dusthanas_from=c2_present,
               their_navamsa_lords_afflicted=c2_afflicted)


def _bhava_leg(chart: RamanChart, house: int, lord: Optional[str],
               bhava_balas: Optional[dict[int, float]]) -> Leg:
    with_mal = any(x in _MALEFICS for x in _occupants_of_house(chart, house))
    weak: Optional[bool] = None
    if bhava_balas:
        bb = bhava_balas.get(house)
        if bb is not None:
            # the engine's ONE documented threshold (shashtiamsas; golden-tuned, its own
            # comment records that Raman states no numeric cutoff) — never an invented figure
            from app.raman_saab.primitives.shadbala.total import BHAVA_BALA_MIN_SH
            sh = bb if bb > 60 else bb * 60.0
            weak = sh < BHAVA_BALA_MIN_SH
    both = None if (with_mal and weak is None) else (with_mal and bool(weak))
    c2_present, c2_afflicted = _clause2(chart, house, lord)
    return Leg("bhava", f"House {house}",
               hemmed=hemmed_house(chart, house),
               with_malefic_and_weak=both,
               no_benefic_contact=_no_benefic_contact_house(chart, house),
               malefics_in_dusthanas_from=c2_present,
               their_navamsa_lords_afflicted=c2_afflicted)


def tripod(chart: RamanChart, house: int,
           bhava_balas: Optional[dict[int, float]] = None) -> Tripod:
    """The verse's test for one house. Pure read; never re-judges (PREC-10)."""
    from app.raman_saab.doctrine.conditions import _lord_of

    try:
        lord = _lord_of(house, chart)
    except Exception:                                              # noqa: BLE001
        lord = None
    legs = [_bhava_leg(chart, house, lord, bhava_balas)]
    if lord:
        legs.append(_planet_leg(chart, "lord", lord))
    karaka = BHAVA_KARAKA.get(house)
    if karaka:
        legs.append(_planet_leg(chart, "karaka", karaka))
    return Tripod(house=house, legs=tuple(legs))
