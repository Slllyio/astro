"""Activation — WHEN a promise fructifies: the dasha windows that light up a topic.

This is the timing engine, and the single biggest net-new piece: the parashara engine already
computes the Vimshottari timeline (`nakshatra_dasha`), but nothing grades a period against a house.
The grading here mirrors the platform's locked "When Do Indications Fructify" method (documented in
CLAUDE.md), re-expressed in pure BPHS and cited to BPHS's own dasha-effect chapter (BPHS-47:48 —
"the effects of the Dasas of the planets are in accordance with [their placement/lordship]", and
:108, the effect of a period-lord *associated with the lord* of a house).

Two doctrines drive it:

  * **A period-lord influences a house** if it owns, occupies, or aspects the house OR its lord —
    the broad significator set (BPHS's own house-lord / occupant / aspecter / lord-conjunct /
    lord-aspecter factors). Nodes influence only by ownership-they-lack, occupancy, and conjunction —
    they cast no graha-drishti in this BPHS-root engine. (The subtle sixth factor, the lord counted
    from the Moon, is omitted here; note it if a chart ever needs it.)
  * **The four-tier grade** for a (mahadasha, bhukti) pair, uniform across all twelve houses:
        both period-lords influence + bhukti lord ASSOCIATED with the maha lord -> "par excellence"
        both influence + bhukti lord NOT associated                            -> "ordinary"
        only the bhukti lord influences                                        -> "limited"
        only the maha lord influences                                          -> "feeble"
        neither                                                                -> not a window
    "Associated" = conjoined (same rasi) or in mutual graha-drishti.

Windows are dated as **age** (years after birth): the chart carries no birth year, and the classical
indication idiom — "the matter is activated during the Jupiter dasha, around the 33rd year" — needs
none. Timing is never a decree; it is when a promise the birth chart ALREADY made comes due.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable, Optional

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import SIGN_LORDS
from app.parashara.reading import ParasharaReading
from app.parashara.chart.cast import ParasharaChart
from app.parashara.synthesis.chart_facts import ASPECTING_GRAHAS, house_sign, planet_signs
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier

ACTIVATION_SOURCE: Final[Citation] = Citation("BPHS-47", 48)     # "the effects of the Dasas ... are in accordance"
ASSOCIATION_SOURCE: Final[Citation] = Citation("BPHS-47", 108)   # effect when associated with a house's lord

#: The four fructification tiers, best first — for sorting and display.
TIER_RANK: Final[dict[str, int]] = {
    "par excellence": 0, "ordinary": 1, "limited": 2, "feeble": 3}


@dataclass(frozen=True)
class ActiveWindow:
    """A (mahadasha, bhukti) period that activates the topic, graded by the four-tier scheme."""
    maha_lord: str
    antar_lord: str
    tier: str                 # par excellence | ordinary | limited | feeble
    start_age: float          # years after birth (clipped at 0)
    end_age: float
    maha_influences: bool
    antar_influences: bool
    associated: bool

    @property
    def label(self) -> str:
        lo, hi = round(self.start_age), round(self.end_age)
        age = f"age {lo}" if lo == hi else f"age {lo}-{hi}"
        return (f"{self.maha_lord} dasha / {self.antar_lord} bhukti ({age}): {self.tier}")


def lords_associated(chart: ParasharaChart, a: str, b: str, *, signs=None) -> bool:
    """Two grahas 'associated' — conjoined (same rasi) OR in mutual graha-drishti (nodes: conjunction
    only cast, but a node CAN be aspected by a graha)."""
    signs = signs or planet_signs(chart)
    sa, sb = signs.get(a), signs.get(b)
    if sa is None or sb is None:
        return False
    if sa == sb:
        return True
    a_asp = a in ASPECTING_GRAHAS and aspects_sign(a, sa, sb)
    b_asp = b in ASPECTING_GRAHAS and aspects_sign(b, sb, sa)
    return a_asp or b_asp


def influences(chart: ParasharaChart, planet: str, house: int, *, signs=None) -> bool:
    """Does `planet` influence `house` — own / occupy / aspect the house OR its lord (BPHS-47:48)?"""
    signs = signs or planet_signs(chart)
    sign = signs.get(planet)
    if sign is None:
        return False
    hsign = house_sign(chart.asc_sign, house)
    lord = SIGN_LORDS[hsign]
    lord_sign = signs.get(lord)
    can_aspect = planet in ASPECTING_GRAHAS
    if planet == lord:                                           # owns the house
        return True
    if sign == hsign:                                           # occupies the house
        return True
    if can_aspect and aspects_sign(planet, sign, hsign):        # aspects the house
        return True
    if lord_sign is not None and sign == lord_sign:            # conjoins the lord
        return True
    if lord_sign is not None and can_aspect and aspects_sign(planet, sign, lord_sign):  # aspects lord
        return True
    return False


def influences_any(chart: ParasharaChart, planet: str, houses: Iterable[int], *, signs=None) -> bool:
    signs = signs or planet_signs(chart)
    return any(influences(chart, planet, h, signs=signs) for h in houses)


def bhukti_tier(maha_influences: bool, antar_influences: bool, associated: bool) -> Optional[str]:
    """The four-tier fructification grade for one (maha, bhukti) pair (see module docstring)."""
    if maha_influences and antar_influences:
        return "par excellence" if associated else "ordinary"
    if antar_influences:
        return "limited"
    if maha_influences:
        return "feeble"
    return None


def active_windows(reading: ParasharaReading, houses: Iterable[int]) -> tuple[ActiveWindow, ...]:
    """Every Vimshottari (maha, bhukti) window (age >= 0) that activates any of `houses`, best-graded
    first then chronological."""
    houses = tuple(houses)
    chart = reading.chart
    signs = planet_signs(chart)
    vim = next((d for d in reading.dashas if d.system == "vimshottari"), None)
    if vim is None:
        return ()

    out: list[ActiveWindow] = []
    for maha_lord, bhuktis in vim.bhuktis:
        maha_infl = influences_any(chart, maha_lord, houses, signs=signs)
        for b in bhuktis:
            if b.end_year <= 0:                                 # entirely before birth
                continue
            antar_infl = influences_any(chart, b.lord, houses, signs=signs)
            tier = bhukti_tier(maha_infl, antar_infl,
                               lords_associated(chart, maha_lord, b.lord, signs=signs))
            if tier is None:
                continue
            out.append(ActiveWindow(
                maha_lord=maha_lord, antar_lord=b.lord, tier=tier,
                start_age=max(0.0, b.start_year), end_age=b.end_year,
                maha_influences=maha_infl, antar_influences=antar_infl,
                associated=lords_associated(chart, maha_lord, b.lord, signs=signs)))
    out.sort(key=lambda w: (TIER_RANK[w.tier], w.start_age))
    return tuple(out)


def activation_evidence(reading: ParasharaReading, houses: Iterable[int],
                        windows: tuple[ActiveWindow, ...]) -> list[Evidence]:
    """One ACTIVATION-tier audit note summarising the strongest timing window (weight 0 — activation
    times a promise, it never votes on whether the promise exists)."""
    houses = tuple(houses)
    if not windows:
        return []
    best = windows[0]                                           # already best-graded first
    return [Evidence(
        topic=houses[0], tier=Tier.ACTIVATION, category="activation", polarity=Polarity.NEUTRAL,
        rule=f"the matter is activated {best.tier} in the {best.maha_lord} dasha",
        condition="dasha_activation",
        observed=best.label,
        source=ASSOCIATION_SOURCE if best.associated else ACTIVATION_SOURCE)]
