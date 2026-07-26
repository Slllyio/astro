"""Kartari (hemming) — Raman Saab doctrine.

Papakartari ("malefic scissors") and its benefic counterpart Subhakartari: a house or
planet is HEMMED when the 2nd and the 12th from it — the signs/houses immediately following
and preceding — are BOTH occupied by planets of one class. Raman's glossary: Papakartari =
"being hemmed in between two malefics" (HTJAH-I:7534-7538); Subhakartari = "being hemmed in
between two benefics" (HTJAH-II:18736-18737). The geometry is pinned to the 2nd/12th:
"hemmed in between Rahu and Saturn in the 2nd and 12th respectively" (HTJAH-I:1181-1184).

Two forms, both attested and both needed:
  - PLANET form — malefics in the signs on either side of the planet's own sign
    ("The Moon being hemmed in between Mars and Saturn", HTJAH-I:1915). This is the form the
    DSL leaf ``conditions.HemmedBy`` already covered.
  - HOUSE form — malefics in the 2nd and 12th houses from a bhava, which may be EMPTY
    ("the Ascendant is hemmed in between malefics", BPHS-83-ii:144; "the second is hemmed in
    between two malefic the Sun and Saturn", HTJAH-I:2720-2721). This is the capability the
    planet-only leaf lacked, and what the BPHS Ch.83 house-hemming verses and the SYN_N6
    tripod (bhava leg, Uttara Kalamrita ch003:1594-1599) require.

Flankers are the NATURAL malefics/benefics (``functional_nature`` sets) — the nodes count and
are in fact Raman's paradigmatic flankers ("preferably Saturn and Rahu", HTJAH-I:1127); they
flank by the sign they occupy though they own none. Whole-sign only (CLAUDE.md lock); the rare
degree-wise hemming within a single sign (HTJAH-I:4994-4996) is deliberately NOT modelled.

CANCELLATION is NOT applied here — it is a separate doctrine layer, left to callers. Raman
counteracts a papakartari by a benefic aspect/association on the hemmed body ("Jupiter's aspect
or association will however counteract the evil indication", HTJAH-I:2532-2533) or by the
hemmed significator's own strength (HTJAH-II:1729-1732); the pure uncancelled form is what
does damage ("without any benefic influence", HTJAH-II:975-977). A caller that needs the
cancelled reading composes ``hemmed_* and not <benefic-relief>`` itself, so this primitive
stays a pure geometry predicate (the ``drishti`` module's shape).

Usage:
    from app.raman_saab.doctrine import hemming
    hemming.hemmed_house(chart, 1)              # is the Lagna papakartari? (house form)
    hemming.hemmed_planet(chart, "Sun")         # is the Sun papakartari? (planet form)
    hemming.hemmed_house(chart, 7, "benefic")   # subhakartari on the 7th
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS, NATURAL_MALEFICS


def _house_from(from_house: int, offset: int) -> int:
    """The house `offset` positions from `from_house` (1-indexed, whole-sign, circular)."""
    return ((from_house - 1) + (offset - 1)) % 12 + 1


def _occupied_by(chart: RamanChart, house: int, group: frozenset[str]) -> bool:
    return any(p.rasi_house == house and name in group
               for name, p in chart.planets.items())


def hemmed_house(chart: RamanChart, house: int, klass: str = "malefic") -> bool:
    """Kartari on a HOUSE: a `klass` planet occupies BOTH the 2nd and the 12th from `house`.

    Works on an EMPTY house (the Lagna, an untenanted bhava) — the capability the planet-only
    ``conditions.HemmedBy`` lacks. `klass` is "malefic" (papakartari) or "benefic"
    (subhakartari)."""
    group = NATURAL_MALEFICS if klass == "malefic" else NATURAL_BENEFICS
    return (_occupied_by(chart, _house_from(house, 2), group)
            and _occupied_by(chart, _house_from(house, 12), group))


def hemmed_planet(chart: RamanChart, planet: str, klass: str = "malefic") -> bool:
    """Kartari on a PLANET: `klass` planets flank the sign the planet occupies (the 2nd and
    12th houses from where it sits). The planet itself sits in the middle house and so can
    never be its own flanker. Returns False for an absent planet (Track-B sparse charts)."""
    p = chart.planets.get(planet)
    if p is None:
        return False
    return hemmed_house(chart, p.rasi_house, klass)
