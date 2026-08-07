"""The Uttara Kalamrita tripod — a house is ruined only when all three of its supports fail.

    "a house is ruined only when the bhava, its lord AND its karaka are all hemmed by
     malefics, conjoined with malefics and weak, with hostile navamsa dispositors"
     — Uttara Kalamrita ch003:1594-1599

This is a **restraint** rule, and that is why it earns a place. Everything else in the classical
band adds a reason to condemn a house; this one names how much has to go wrong before condemning
is warranted — three legs (bhava, lord, karaka), each failing several conditions at once. On most
charts it does not fire, and that is the finding: the engine's own verdict for a house is rarely
corroborated by the full classical test.

It was carried as `kind="descriptive"` (on record, never evaluated) because the primitive it
needed did not exist. It does now — `doctrine.hemming` covers both the planet leg (lord, karaka)
and the house leg (a bhava, which may be empty) and its docstring names this rule as the reason
it was built. This module is that rule made evaluable.

**Band discipline.** CLASSICAL_NONCITABLE. It corroborates, it never overrides: where this and
Raman disagree, Raman wins, and nothing here touches a verdict. Report-layer only (PREC-10).

**Conservative on missing data, always.** A condition the chart cannot answer is NOT counted as
failing, so a leg never completes on absence and the tripod never condemns from ignorance. The
engine's standing preference for saying less over guessing.

**One interpretive choice, named rather than buried.** "hostile navamsa dispositors" is stated
for the supports as a group; it is applied here to the LORD and KARAKA, which are planets and
have navamsa dispositors in the ordinary sense. A bhava is not a planet, so its leg is judged on
the three conditions that plainly apply to a house — hemmed, occupied by a malefic, weak by
Bhava Bala. Deliberate, and flagged in `Leg.conditions_applied` so a reader can see which test
each leg actually faced.

Usage:
    from app.raman_saab.doctrine.uk_tripod import tripod
    t = tripod(chart, house=7, bhava_balas=balas)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.hemming import hemmed_house, hemmed_planet
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA

#: Natural malefics, per the project's locked Avastha convention (CLAUDE.md).
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})

#: Bhava Bala at or below this (in rupas) counts as a weak bhava. Raman gives no numeric Bhava
#: Bala cutoff — the report says so explicitly among its honoured absence findings — so this is
#: the classical average (Bhava Bala is conventionally referenced against 7 rupas / 420 virupas)
#: and is used ONLY inside this classical-band test, never against a Raman verdict.
_WEAK_BHAVA_RUPAS: Final[float] = 7.0


@dataclass(frozen=True)
class Leg:
    """One support of the house, and how it fared against the conditions that apply to it."""

    what: str                      # "bhava" | "lord" | "karaka"
    who: str                       # "House 7", or a planet name
    hemmed: Optional[bool]
    with_malefic: Optional[bool]
    weak: Optional[bool]
    hostile_navamsa: Optional[bool]
    conditions_applied: tuple[str, ...]

    @property
    def failed(self) -> bool:
        """Every condition that applies to this leg is TRUE. Unknown never counts as failure."""
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
        """The classical condemnation: all three supports fail together."""
        return len(self.legs) == 3 and all(leg.failed for leg in self.legs)

    @property
    def failing(self) -> tuple[str, ...]:
        return tuple(leg.what for leg in self.legs if leg.failed)

    @property
    def pressure(self) -> int:
        """How many of the applicable failure-conditions are met, across all three supports.

        MEASURED, and it is why this is the reported quantity rather than `complete`. Across
        1,260 house-tests on 105 charts the literal test completed **0 times**, and not one
        planet leg failed all four of its conditions (0 of 2,520) — the conditions are
        negatively correlated, so a planet hemmed by malefics tends not to ALSO be weak, with a
        malefic, and in a hostile navamsa. The mechanism is not broken (a constructed all-true
        leg does fire); Uttara Kalamrita's threshold is simply near-unsatisfiable, which is its
        whole point — ruin requires everything to fail at once.

        `pressure` is what varies: 0-7 observed of 11 applicable, centred on 2-3. It says how
        FAR a house sits from the classical ruin, which is informative on every chart, where
        `complete` is silent on all of them.
        """
        return sum(1 for leg in self.legs
                   for cond in leg.conditions_applied if getattr(leg, cond) is True)

    @property
    def applicable(self) -> int:
        return sum(len(leg.conditions_applied) for leg in self.legs)

    @property
    def met(self) -> tuple[str, ...]:
        """The conditions actually met, named — so a reader can check the count."""
        return tuple(f"{leg.what} {cond.replace('_', ' ')}"
                     for leg in self.legs
                     for cond in leg.conditions_applied if getattr(leg, cond) is True)


def _occupants(chart: RamanChart, *, sign: Optional[int] = None,
               bhava: Optional[int] = None, exclude: str = "") -> list[str]:
    out = []
    for name, p in chart.planets.items():
        if name == exclude:
            continue
        if sign is not None and getattr(p, "sign", None) == sign:
            out.append(name)
        elif bhava is not None and getattr(p, "bhava", None) == bhava:
            out.append(name)
    return out


def _planet_leg(chart: RamanChart, what: str, planet: str) -> Leg:
    from app.raman_saab.primitives.relationships import naisargika
    from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED

    p = chart.planets.get(planet)
    if p is None:
        return Leg(what, planet, None, None, None, None,
                   ("hemmed", "with_malefic", "weak", "hostile_navamsa"))

    with_malefic = any(x in _MALEFICS
                       for x in _occupants(chart, sign=p.sign, exclude=planet))

    weak: Optional[bool] = None
    sb, req = getattr(p, "shadbala_rupas", None), MIN_REQUIRED.get(planet)
    if sb is not None and req is not None:
        weak = (sb.total / 60.0) < req

    # The dispositor of the sign the planet occupies IN THE NAVAMSA — hostile when the two are
    # naisargika enemies. Nodes own no sign, so they cannot be a dispositor; the leg stays
    # unknown rather than being scored as friendly.
    hostile: Optional[bool] = None
    nav = getattr(p, "navamsa_sign", None)
    if nav:
        from app.raman_saab.chart.constants import SIGN_LORDS
        lord = SIGN_LORDS.get(nav)
        if lord and lord != planet:
            hostile = naisargika(planet, lord) == "enemy"
        elif lord == planet:
            hostile = False                       # in its own navamsa: not hostile

    return Leg(what, planet, hemmed_planet(chart, planet), with_malefic, weak, hostile,
               ("hemmed", "with_malefic", "weak", "hostile_navamsa"))


def _bhava_leg(chart: RamanChart, house: int,
               bhava_balas: Optional[dict[int, float]]) -> Leg:
    with_malefic = any(x in _MALEFICS for x in _occupants(chart, bhava=house))
    weak: Optional[bool] = None
    if bhava_balas:
        bb = bhava_balas.get(house)
        if bb is not None:
            # accept rupas or virupas — the engine has carried both
            weak = (bb / 60.0 if bb > 60 else bb) <= _WEAK_BHAVA_RUPAS
    return Leg("bhava", f"House {house}", hemmed_house(chart, house), with_malefic, weak, None,
               ("hemmed", "with_malefic", "weak"))


def tripod(chart: RamanChart, house: int,
           bhava_balas: Optional[dict[int, float]] = None) -> Tripod:
    """The three-legged test for one house. Never re-judges — a pure read (PREC-10)."""
    from app.raman_saab.doctrine.conditions import _lord_of

    legs = [_bhava_leg(chart, house, bhava_balas)]
    try:
        lord = _lord_of(house, chart)
    except Exception:                                                  # noqa: BLE001
        lord = None
    if lord:
        legs.append(_planet_leg(chart, "lord", lord))
    karaka = BHAVA_KARAKA.get(house)
    if karaka:
        legs.append(_planet_leg(chart, "karaka", karaka))
    return Tripod(house=house, legs=tuple(legs))
