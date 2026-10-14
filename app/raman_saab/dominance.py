"""Dominance — which testimony GOVERNS when a house's witnesses disagree.

The engine already discloses both poles when a house is contested (`tension_narrator`, PREC-1
and PREC-3): it names the favourable count, names the adverse count, and stops. That is honest
and it is not what an astrologer does. Raman names the winner and the reason.

His criterion is explicit, and it is strength:

    "But of the planets aspecting this Bhava, the Sun and Mars, the Sun is stronger, being in
     his own sign and in Simhasanamsa... So, the promise of evil concerning this Bhava denoted
     by the weak lord of the Bhava will not only be belied but also be replaced by benefic
     effects."                                                            — HTJAH-I:7152

Two things there, and the second is the one the engine was missing. First, dominance is decided
by **strength** — dignity, and varga standing. Second, the stronger testimony **replaces** the
weaker one's promise; it is not averaged with it, and it does not merely outvote it.

He applies the same test to aspects, deciding by exactness:

    "Although Jupiter aspects the 10th, the aspects of Mars and the Sun are stronger, being to
     the exact degree of the 10th cusp, and determines the nature of work."
                                                                          — HTJAH-II:11673

So for each house this module compares the two planets the engine already names as its factors —
its **lord** and its **karaka** — and where exactly one of them is strong, says that planet
governs. The governing **direction** comes from that planet's functional nature for this
ascendant, not from the contest, which is why a strong functional malefic governing a house
yields an adverse reading rather than a favourable one.

Where the comparison does not decide — both strong, both weak, or the same planet in both roles
— it says nothing. That restraint is the point: dominance is declared only when Raman's own
criterion is actually met, never to manufacture a resolution.

The note further down records an implementation that was measured and rejected for producing a
confident, well-cited, tautological answer. It is worth reading before changing this.

PREC-10 holds: nothing is re-judged. Both poles remain disclosed exactly as before — the
governing sentence is added beside that disclosure, never in place of it.

Usage:
    from app.raman_saab.dominance import house_dominance, dominance_sentences
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.raman_style import weighed

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: Raman decides dominance by strength — "the Sun is stronger, being in his own sign".
STRENGTH_CITE: Final[str] = "HTJAH-I:7152"
#: and among aspects, by exactness to the cusp.
EXACTNESS_CITE: Final[str] = "HTJAH-II:11673"

# A NOTE ON A REJECTED IMPLEMENTATION, kept because it would be easy to write again.
#
# The obvious approach is to read the preponderance ledger's testimony leans and let the side
# holding a `strong` factor govern the side holding a `weak` one. It produces confident,
# well-cited output — and it is tautological. Measured across five charts and every house:
#
#     strong    -> favourable-leaning   91      strong that lean adverse:    0
#     weak      -> adverse-leaning      24      weak that lean favourable:   0
#     afflicted -> adverse-leaning      32
#
# Strength and direction are the SAME axis in that ledger, so "the stronger governs" can only
# ever return "favourable". Shipping it would have told every reader that the good side wins in
# every contested house — an optimistic bias wearing Raman's citation.
#
# What he actually compares is PLANET against PLANET — "of the planets aspecting this Bhava, the
# Sun and Mars, the Sun is stronger" — and the direction comes from the winning planet's own
# nature, not from a pre-assigned lean. So dominance is decided here between the house's LORD
# and its KARAKA, the two factors the ledger names, and the governing direction is that planet's
# functional nature FOR THIS LAGNA. That can, and does, return adverse.

#: functional nature -> the direction a governing planet carries (per-lagna, from the engine).
#: `yogakaraka` — a planet ruling both a kendra and a trikona — is grouped with the functional
#: benefics by the engine's own Laghu Parashari layer (`synthesis_rules.benefic_like`), so it is
#: read the same way here rather than given a direction of our own invention.
DIRECTION: Final[dict[str, str]] = {
    "yogakaraka": "favourable",
    "benefic": "favourable",
    "malefic": "adverse",
    "neutral": "mixed",
}


@dataclass(frozen=True)
class Dominance:
    """One resolved contest: what governs a house, what yields, and on whose authority."""

    house: int
    governing: str          # the PLANET that carries the house
    governing_role: str     # "lord" or "karaka"
    yielding: str           # the planet it overrides
    yielding_role: str
    nature: str             # the governing planet's functional nature for this lagna
    direction: str          # "favourable" | "adverse" | "mixed" — from that nature
    sentence: str
    cites: tuple[str, ...]


def _natures(r: "DetailedReport") -> dict[str, str]:
    return {p: n for p, n in (getattr(getattr(r, "overview", None),
                                      "functional_natures", ()) or ())}


def house_dominance(r: "DetailedReport") -> dict[int, Dominance]:
    """Where a house's lord and karaka disagree in strength, name which planet governs.

    Qualifies only when exactly one of the two is strong — Raman's test is a comparison, so a
    house where both are strong, or neither is, is left alone. The existing both-poles
    disclosure already says everything that can honestly be said about those.
    """
    natures = _natures(r)
    out: dict[int, Dominance] = {}

    for pf in getattr(r, "proformas", ()) or ():
        sigs = getattr(pf, "significations", ()) or ()
        if not sigs:
            continue
        led = getattr(sigs[0], "ledger", None)
        lord, karaka = getattr(led, "lord", None), getattr(led, "karaka", None)
        if led is None or not lord or not karaka or lord == karaka:
            continue
        lord_strong = getattr(led, "lord_strong", None)
        karaka_strong = getattr(led, "karaka_strong", None)
        if lord_strong is None or karaka_strong is None or lord_strong == karaka_strong:
            continue                                   # no comparison to make

        if lord_strong:
            win, win_role, lose, lose_role = lord, "lord", karaka, "karaka"
        else:
            win, win_role, lose, lose_role = karaka, "karaka", lord, "lord"

        nature = natures.get(win, "neutral")
        direction = DIRECTION.get(nature, "mixed")

        # "the promise of evil ... denoted by the weak lord ... will not only be belied but also
        # be REPLACED" — the stronger factor stands in place of the weaker one's indication; it
        # is not averaged with it and it does not merely outvote it.
        sentence = weighed(
            f"the {win_role} {win} strong against the {lose_role} {lose} weak in house "
            f"{pf.house}",
            f"{win} governs this house, and being a functional {nature} for this ascendant the "
            f"reading here follows him rather than averaging the two")

        out[pf.house] = Dominance(
            house=pf.house, governing=win, governing_role=win_role,
            yielding=lose, yielding_role=lose_role, nature=nature, direction=direction,
            sentence=sentence, cites=(STRENGTH_CITE,))
    return out


def dominance_sentences(r: "DetailedReport") -> tuple[str, ...]:
    """The governing sentences, house order — ready for any renderer."""
    return tuple(d.sentence for _h, d in sorted(house_dominance(r).items()))
