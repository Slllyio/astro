"""Evidence — the atom of the synthesis layer, and the unit of its audit trail.

One `Evidence` is one cited testimony about one topic: a rule that fired, the condition it needed,
what the chart actually shows, its polarity toward the topic's promise, and the sloka it comes from.
Every conclusion the layer reaches is a function of a list of these, so the list IS the audit trail
(sloka -> rule -> condition -> evidence) the reading shows behind each judgment.

## The evidence hierarchy (BPHS's own precedence)

Not all testimony carries equal weight, and Parashara says which decides. The `Tier` encodes that
precedence, and the convergence layer weights by it:

  * **PROMISE** — the birth-chart result of the bhava itself (ch.11's prosperity/annihilation). This
    is what a matter fundamentally IS; it — and it alone — decides denied-vs-granted. A fired ch.11
    annihilation condition is PROMISE-tier evidence of CONTRADICTS polarity: the negative of the very
    thing being judged.
  * **STRENGTH** — what modulates the promise: the significators' Shadbala / Vimsopaka (ch.27, ch.7)
    AND supplementary affliction ch.11 does not enumerate (a malefic occupying/aspecting the house).
    A strong promise is delivered, a weak or afflicted one struggles — strength modulates the
    promise, it never replaces it (which is why ubiquitous malefic drishti lands here, not at
    PROMISE: it makes a matter *difficult*, not *denied*).
  * **CORROBORATION** — the Navamsa/Dasamsa, Ashtakavarga, karaka and Arudha Lagna (ch.7, ch.66,
    ch.32, ch.29). "The Rasi is the tree, the divisions its fruit": a division confirms or weakens a
    promise, it never overturns it.
  * **ACTIVATION** — the dasha windows (ch.46-47). A dasha times WHEN a promise fructifies; it never
    creates a promise the birth chart withheld, so it carries no vote on WHETHER — only on when.

`polarity` is the direction of a testimony toward the promise: it SUPPORTS it, CONTRADICTS it, or is
NEUTRAL. `antidoted` marks a fired negative that a BPHS antidote cancels (ch.11's own mitigation
clauses, neecha-bhanga, a benefic's rescue): such a negative is *shown* — the reading discloses its
working — but it does not count against the promise. A cancelled affliction is the seed of the
delay/difficulty axis (Parashara's antidotes soften a denial into a delay, they do not erase the
adversity), handled in `judgment`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation


class Polarity(IntEnum):
    """A testimony's direction toward the topic's promise."""
    SUPPORTS = 1
    NEUTRAL = 0
    CONTRADICTS = -1


class Tier(IntEnum):
    """The precedence rank of a testimony (higher decides). Values are also the convergence weight."""
    PROMISE = 3        # the bhava's own ch.11 result — decides
    STRENGTH = 2       # significators' strength — modulates the promise
    CORROBORATION = 1  # divisional / ashtakavarga / karaka / Arudha — confirms, never overturns
    ACTIVATION = 0     # dasha timing — WHEN, never WHETHER (carries no vote on the verdict)


#: The categories the user's architecture names as separate "evidence engines" — a display facet,
#: orthogonal to the precedence Tier (an affliction is PROMISE- or STRENGTH-tier, CONTRADICTS).
CATEGORIES: Final[tuple[str, ...]] = (
    "promise", "strength", "affliction", "corroboration", "activation")

_SIGN: Final[Mapping[Polarity, str]] = {
    Polarity.SUPPORTS: "+", Polarity.NEUTRAL: "·", Polarity.CONTRADICTS: "-"}


@dataclass(frozen=True)
class Evidence:
    """One cited testimony about one topic — and one line of the audit trail."""
    topic: int             # the bhava (1..12) this testimony bears on
    tier: Tier             # its precedence rank (and convergence weight)
    category: str          # promise | strength | affliction | corroboration | activation (display)
    polarity: Polarity     # SUPPORTS | NEUTRAL | CONTRADICTS the promise
    rule: str              # the doctrinal rule, e.g. "a benefic aspects the house"
    condition: str         # the condition key it needed, e.g. "benefic_aspect"
    observed: str          # what the chart shows, e.g. "Jupiter aspects the 5th from the Lagna"
    source: Citation       # the sloka it comes from
    antidoted: bool = False  # a fired negative a BPHS antidote cancels (shown, not counted)

    @property
    def counts(self) -> bool:
        """Does this testimony vote in the convergence? A neutral does not, nor an antidoted
        negative (its adversity is disclosed but softened — it feeds delay/difficulty, not denial)."""
        if self.polarity is Polarity.NEUTRAL:
            return False
        if self.antidoted and self.polarity is Polarity.CONTRADICTS:
            return False
        return True

    @property
    def weight(self) -> int:
        """The convergence weight this testimony carries if it counts (its tier rank)."""
        return int(self.tier) if self.counts else 0

    @property
    def audit_line(self) -> str:
        """The audit-trail rendering: `<sign> [WORK:line] rule — observed` (antidotes marked)."""
        tok = f"{self.source.work}:{self.source.line}"
        mark = " (antidoted)" if self.antidoted else ""
        return f"{_SIGN[self.polarity]} [{tok}] {self.rule} — {self.observed}{mark}"
