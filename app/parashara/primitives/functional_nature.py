"""Natural benefics and malefics (BPHS ch.3, sloka 11).

    "The Sun, Saturn, Mars, decreasing Moon, Rahu and Ketu are malefics while the rest are
     benefics. Mercury, however, is a malefic if he joins a malefic." (BPHS-3:187)
    "Should the Moon be conjunct a benefic or aspected by a benefic, she turns a benefic, even
     if in a waning state." (BPHS-3:208)

Two grahas are CONDITIONAL, and Parashara says so explicitly — encoding them as fixed would be
unfaithful:
  * the Moon's nature depends on paksha (waxing = benefic, waning = malefic), and a waning Moon in
    benefic company turns benefic;
  * Mercury takes the nature of what he joins — malefic only if conjunct a malefic.

`natural_benefic` therefore needs the Moon's paksha and Mercury's companions to answer for those
two; the five fixed grahas answer without context.
"""
from __future__ import annotations

from typing import Final, Iterable, Optional

from app.parashara.doctrine.sources import Citation

#: Unconditional malefics (BPHS-3:187). Sun, Saturn, Mars + the two nodes.
FIXED_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Saturn", "Mars", "Rahu", "Ketu"})
#: Unconditional benefics — Jupiter and Venus. (Moon and Mercury are conditional; see below.)
FIXED_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus"})

SOURCE: Final[Citation] = Citation("BPHS-3", 187)
MOON_BENEFIC_COMPANY_SOURCE: Final[Citation] = Citation("BPHS-3", 208)


def natural_benefic(planet: str, *,
                    moon_waxing: Optional[bool] = None,
                    companions: Iterable[str] = (),
                    companions_are_benefic: Optional[bool] = None,
                    aspected_by_benefic: bool = False) -> bool:
    """Is `planet` a natural benefic per BPHS ch.3 sl.11?

    Args:
        planet: the graha.
        moon_waxing: required for the Moon — True in Sukla Paksha (bright half). A waxing Moon is a
            benefic; a waning Moon is a malefic UNLESS in benefic company (below).
        companions: grahas conjunct `planet` (same sign). Used for Mercury (malefic only if joined
            by a malefic) and for the waning-Moon-turns-benefic clause.
        companions_are_benefic: optional pre-computed "is any companion a benefic" — supply when the
            caller already knows, to avoid recursion. If omitted it is derived from `companions`
            using the unconditional sets (a safe, non-recursive approximation: the fixed sets settle
            it for every graha except a Moon/Mercury companion, which is the rare ambiguous case).

    Raises:
        ValueError: the Moon without `moon_waxing` — its nature is undefined without paksha, and
            guessing would silently mislabel half of all charts.
    """
    if planet in FIXED_MALEFICS:
        return False
    if planet in FIXED_BENEFICS:
        return True

    if planet == "Mercury":
        # "a malefic if he joins a malefic" — otherwise benefic.
        return not _any_companion_malefic(companions, companions_are_benefic)

    if planet == "Moon":
        if moon_waxing is None:
            raise ValueError("the Moon's nature needs paksha (moon_waxing=True/False)")
        if moon_waxing:
            return True
        # waning Moon: malefic, UNLESS conjunct OR aspected by a benefic (BPHS-3:208 —
        # "conjunct a benefic or aspected by a benefic ... turns a benefic").
        if aspected_by_benefic:
            return True
        if companions_are_benefic is True:
            return True
        return _any_companion_benefic(companions)

    raise ValueError(f"unknown graha {planet!r}")


def _any_companion_malefic(companions: Iterable[str],
                           companions_are_benefic: Optional[bool]) -> bool:
    if companions_are_benefic is not None:
        return not companions_are_benefic
    # Non-recursive: a companion is malefic if it is a fixed malefic, or a waning Moon we cannot
    # see the paksha of here (treated conservatively as NOT malefic to avoid inventing a paksha).
    return any(c in FIXED_MALEFICS for c in companions)


def _any_companion_benefic(companions: Iterable[str]) -> bool:
    return any(c in FIXED_BENEFICS for c in companions)


def natural_malefic(planet: str, **kwargs) -> bool:
    """Convenience inverse of `natural_benefic` (same keyword args)."""
    return not natural_benefic(planet, **kwargs)
