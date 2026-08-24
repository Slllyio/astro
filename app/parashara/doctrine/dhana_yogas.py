"""Dhana (wealth) yogas — BPHS ch.41, the crisp combinations, each a cited detector.

ch.41 opens with two regular families of chart-computable wealth combinations. Each is encoded as its
own rule citing its own sloka (the maraka/conjunction pattern — a specific stated combination per
rule, never a synthesized general principle):

  Family A (sl.2-8) — a planet in the 5th house in its own sign, with named planets in the 11th.
  Family B (sl.9-15) — a planet in its own sign identical with the ascendant, conjunct or aspected
                       by two (for Mars, three) named planets.

DEFERRED (not faked): the general clause "the 9th and 5th lords bestow wealth" (sl.16) and the
Parijatamsa/varga-graded verses (sl.18+) — the former is a soft general rule, the latter need the
Shadvarga dignity of the lord, a separate layer. Conjunction is same-sign (whole-sign); aspects use
graha drishti.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import SIGN_LORDS

_WORK: Final[str] = "BPHS-41"

#: Family A — (planet in own-sign 5th, planets required in the 11th, sloka line).
_FIFTH_AND_ELEVENTH: Final[tuple[tuple[str, frozenset[str], int], ...]] = (
    ("Venus", frozenset({"Mars"}), 34),
    ("Mercury", frozenset({"Moon", "Mars", "Jupiter"}), 50),
    ("Sun", frozenset({"Saturn", "Moon", "Jupiter"}), 65),
    ("Saturn", frozenset({"Sun", "Moon"}), 78),
    ("Jupiter", frozenset({"Mercury"}), 93),
    ("Mars", frozenset({"Venus"}), 105),
    ("Moon", frozenset({"Saturn"}), 116),
)

#: Family B — (planet in own-sign ascendant, planets conjunct/aspecting it, sloka line).
_OWN_LAGNA_ASPECTED: Final[tuple[tuple[str, frozenset[str], int], ...]] = (
    ("Sun", frozenset({"Mars", "Jupiter"}), 132),
    ("Moon", frozenset({"Mercury", "Jupiter"}), 140),
    ("Mars", frozenset({"Mercury", "Venus", "Saturn"}), 148),
    ("Mercury", frozenset({"Saturn", "Jupiter"}), 154),
    ("Jupiter", frozenset({"Mercury", "Mars"}), 162),
    ("Venus", frozenset({"Saturn", "Mercury"}), 170),
    ("Saturn", frozenset({"Mars", "Jupiter"}), 180),
)

# a representative source line for the chapter (sl.1 header) — for module-level citation checks
SOURCE: Final[Citation] = Citation(_WORK, 27)


@dataclass(frozen=True)
class DhanaYoga:
    name: str
    reason: str
    source: Citation


def _house(asc_sign: int, sign: int) -> int:
    return ((sign - asc_sign) % 12) + 1


def detect(longitudes: Mapping[str, float], *, asc_sign: int) -> tuple[DhanaYoga, ...]:
    """Every crisp ch.41 wealth yoga present in the chart, each cited to its own sloka."""
    signs = {p: int(l % 360.0 // 30) + 1 for p, l in longitudes.items()}
    out: list[DhanaYoga] = []

    for subj, eleventh, line in _FIFTH_AND_ELEVENTH:
        if (subj in signs and _house(asc_sign, signs[subj]) == 5
                and SIGN_LORDS[signs[subj]] == subj
                and all(p in signs and _house(asc_sign, signs[p]) == 11 for p in eleventh)):
            out.append(DhanaYoga(
                f"Dhana ({subj} in own sign in the 5th, {'/'.join(sorted(eleventh))} in the 11th)",
                f"{subj} in its own sign in the 5th with {', '.join(sorted(eleventh))} in the 11th",
                Citation(_WORK, line)))

    for subj, aspecters, line in _OWN_LAGNA_ASPECTED:
        if (subj in signs and _house(asc_sign, signs[subj]) == 1
                and SIGN_LORDS[signs[subj]] == subj
                and all(p in signs and (signs[p] == asc_sign or aspects_sign(p, signs[p], asc_sign))
                        for p in aspecters)):
            out.append(DhanaYoga(
                f"Dhana ({subj} in own-sign lagna, joined/aspected by {'/'.join(sorted(aspecters))})",
                f"{subj} in its own sign as the ascendant, conjunct or aspected by "
                f"{', '.join(sorted(aspecters))}",
                Citation(_WORK, line)))

    return tuple(out)
