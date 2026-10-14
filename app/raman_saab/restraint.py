"""Restraint — saying how firmly a house is decided, and where it is not decided at all.

`dominance` names which planet governs a house when its lord and karaka differ in strength. On a
real chart it resolves two houses of twelve and is silent on ten. That silence is the problem
this module fixes: as it stands, a reader cannot tell "the engine examined this and found no
governing factor" from "the engine had nothing to say". The first is a finding; the second is a
gap. They should not look identical.

Raman is explicit that declining is part of the method, not a failure of it:

    "In all these cases, a careful weighing of the pros and cons of the affliction or
     fortification is absolutely necessary. No slip-shod interpretation should be made and a
     premature conclusion arrived at."                                    — HTJAH-I:4299

    "Readers must be very careful ... lest they should come to premature conclusions based on
     insufficient knowledge or want of experience. Any antidotes present must be carefully
     scrutinised before pronouncing judgment."                            — HTJAH-I:6810

Both sit immediately after his gravest indications — insanity, tragedy, violence, disease —
which is precisely where an engine is most tempted to overclaim.

The important distinction, and the one an unqualified "confidence score" would destroy: **silence
is not uncertainty**. A house whose lord and karaka are BOTH strong is not unclear — it is
uniformly well-founded, and dominance stays quiet only because there is no weaker side to
overrule. Likewise a house where one planet is both lord and karaka is not ambiguous; its fate
simply concentrates on a single graha. Only a contested house with no governing factor is
genuinely unsettled, and only that one should soften what the report says.

PREC-10: every input is already computed. No verdict is re-judged and none is suppressed — the
house reading still renders in full. Restraint annotates how firmly it stands.

Usage:
    from app.raman_saab.restraint import house_restraint, unsettled_houses
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from app.raman_saab.raman_style import because, conclusion

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: "No slip-shod interpretation should be made and a premature conclusion arrived at."
PREMATURE_CITE: Final[str] = "HTJAH-I:4299"
#: "Any antidotes present must be carefully scrutinised before pronouncing judgment."
JUDGMENT_CITE: Final[str] = "HTJAH-I:6810"

#: How firmly a house stands. Only `unsettled` should soften the surrounding prose.
STANDING_GOVERNED: Final[str] = "governed"
STANDING_CONCORDANT: Final[str] = "concordant"
STANDING_CONCENTRATED: Final[str] = "concentrated"
STANDING_UNSETTLED: Final[str] = "unsettled"


@dataclass(frozen=True)
class Restraint:
    """How firmly one house is decided, and — when it is not — why not."""

    house: int
    standing: str
    #: True only for `unsettled`. Renderers should soften prose here and nowhere else.
    soften: bool
    reason: str
    sentence: str
    cites: tuple[str, ...]


def house_restraint(r: "DetailedReport") -> dict[int, Restraint]:
    """Classify how firmly each house stands. Pure re-read; nothing is re-judged."""
    from app.raman_saab.dominance import house_dominance

    governed = house_dominance(r)

    # Which houses are genuinely unsettled. Use the engine's OWN `status`, not a ratio invented
    # here: it already distinguishes "well-corroborated" from "contested", and it is not a count
    # — house 1 at 4 favourable / 1 adverse reads well-corroborated while house 12 at the same
    # 4/1 reads contested, because what matters is whether the dissent bears on the headline.
    # An earlier version used "any favourable AND any adverse" and flagged a 4-1 majority as
    # undecided, overstating the doubt.
    contested: dict[int, tuple[int, int]] = {}
    for ht in getattr(getattr(r, "preponderance", None), "houses", ()) or ():
        if getattr(ht, "status", "") == "contested":
            contested[ht.house] = (getattr(ht, "favourable", 0), getattr(ht, "adverse", 0))

    out: dict[int, Restraint] = {}

    for pf in getattr(r, "proformas", ()) or ():
        sigs = getattr(pf, "significations", ()) or ()
        if not sigs:
            continue
        led = getattr(sigs[0], "ledger", None)
        if led is None:
            continue
        house = pf.house
        lord, karaka = getattr(led, "lord", None), getattr(led, "karaka", None)
        lord_strong = getattr(led, "lord_strong", None)
        karaka_strong = getattr(led, "karaka_strong", None)

        if house in governed:
            d = governed[house]
            standing, soften = STANDING_GOVERNED, False
            reason = (f"{d.governing} as {d.governing_role} is strong where "
                      f"{d.yielding} as {d.yielding_role} is not")
            sentence = because(
                f"{d.governing} stands stronger here than {d.yielding}",
                f"this house is decided rather than balanced, and the reading follows "
                f"{d.governing}")

        elif lord and karaka and lord == karaka:
            standing, soften = STANDING_CONCENTRATED, False
            reason = f"{lord} is both lord and karaka of this house"
            sentence = because(
                f"{lord} both rules this house and signifies its matters",
                "its fortunes rest on a single graha rather than being shared between two, "
                f"so how {lord} itself stands is the whole of the matter here")

        elif contested.get(house):
            # The case restraint exists for. Note it is decided by the house's WITNESSES, not by
            # lord/karaka strength: an earlier version tested strength here and the branch was
            # dead code, because dominance already fires on every strength difference. A
            # restraint faculty that can never restrain is worse than none — it reads as
            # confidence.
            fav, adv = contested[house]
            standing, soften = STANDING_UNSETTLED, True
            reason = f"{fav} witnesses lean favourable and {adv} lean adverse, with none governing"
            sentence = conclusion(
                f"this house is not clearly decided — {fav} of its witnesses lean one way and "
                f"{adv} the other, and no factor stands strong enough to govern between them, "
                f"so the reading below is reported as it stands rather than resolved into a "
                f"single verdict")

        elif lord_strong is not None and lord_strong == karaka_strong:
            firm = "strong" if lord_strong else "weak"
            standing, soften = STANDING_CONCORDANT, False
            reason = f"lord {lord} and karaka {karaka} are both {firm}"
            sentence = because(
                f"both {lord} as lord and {karaka} as karaka are {firm} here",
                "the house is uniform rather than divided — there is no contest to settle, "
                "which is itself a firm reading and not an absence of one")

        else:
            standing, soften = STANDING_CONCORDANT, False
            reason = "no contest among its factors"
            sentence = because(
                "this house's factors do not pull against one another",
                "there is no contest to settle here")

        out[house] = Restraint(house=house, standing=standing, soften=soften, reason=reason,
                               sentence=sentence,
                               cites=(PREMATURE_CITE, JUDGMENT_CITE) if soften
                               else (PREMATURE_CITE,))
    return out


def unsettled_houses(r: "DetailedReport") -> tuple[int, ...]:
    """Houses the engine declines to resolve — where a renderer should say less, not more."""
    return tuple(h for h, x in sorted(house_restraint(r).items()) if x.soften)
