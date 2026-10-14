"""Convergence — turn a list of Evidence into a doctrinal-convergence confidence.

This is the "convergence score" and "contradiction resolution" of the architecture, and it is the
confidence surface the user chose: a **tally beside its reasons** plus a **tier label**, never an
opaque number and never a probability of the event.

## How it combines (precedence, not averaging)

Each counting testimony votes with its tier's weight (PROMISE 3, STRENGTH 2, CORROBORATION 1;
ACTIVATION times, it does not vote). The signed sum is the `net` — positive leans favourable, negative
afflicted. Because the weights ARE the precedence, a birth-chart promise already outweighs a divisional
that disagrees: the hierarchy is enforced arithmetically, not by discarding the minority. The minority
is never discarded — genuine disagreement is surfaced in `contradictions` and reported side by side,
per the Measured-Truth default ("parallel, never averaged").

## The tier label

`par-excellence / strong / moderate / weak` measures how *decisively and how convergently* the cited
rules agree — it is a transparent reading of the weighted margin and whether the lenses (promise,
strength, corroboration) point the same way, in the spirit of `richer_bhava._degree`: it surfaces the
margin the verdict discards, it is not a separate doctrinal claim. `insufficient` is stated honestly
when there is no decisive testimony, and a `caveat` flags thin coverage so a lone testimony is never
dressed up as settled.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.parashara.synthesis.evidence import Evidence, Polarity, Tier


@dataclass(frozen=True)
class Convergence:
    """The doctrinal-convergence confidence in a verdict: a tally, a margin, and a tier label.

    It is *verdict-oriented*: `supporting` counts the testimonies that AGREE with the verdict the
    judgment reached, `contradicting` those that point the other way. So a denied verdict shows the
    affliction testimonies as the concurring ones, and the tally can never read against its verdict.
    """
    supporting: int                      # counting testimonies that concur with the verdict
    contradicting: int                   # counting testimonies that point the other way
    cancelled: int                       # antidoted negatives — disclosed, not counted
    weighted_concur: int
    weighted_against: int
    net: int                             # weighted_concur - weighted_against (the confidence margin)
    tier: str                            # par-excellence | strong | moderate | weak | divided | insufficient
    contradictions: tuple[str, ...]      # genuine conflicts, reported (never averaged away)
    caveat: str                          # coverage caveat, '' when evidence is adequate
    split_note: str = ""                 # majority-vs-headline disclosure, '' when they agree

    @property
    def tally(self) -> str:
        """The confidence, in words, beside its reasons — the surface the reader sees."""
        total = self.supporting + self.contradicting
        if total == 0:
            return "no decisive cited testimony"
        out = f"{self.supporting} of {total} cited testimonies concur"
        if self.contradicting:
            out += f", {self.contradicting} contradict"
        if self.cancelled:
            out += f" ({self.cancelled} cancelled by antidote)"
        return out


def tier_net(evidence: Sequence[Evidence], tier: Tier) -> int:
    """Signed count within one tier: counting SUPPORTS (+1) minus counting CONTRADICTS (-1).
    Used by the verdict logic to read each precedence tier's lean."""
    return sum(int(e.polarity) for e in evidence if e.tier is tier and e.counts)


def converge(evidence: Sequence[Evidence], *, toward: int = 1) -> Convergence:
    """Combine evidence into a verdict-oriented `Convergence` (no averaging; precedence by weight).

    `toward` is the verdict's direction: +1 a favourable verdict (granted/delayed/difficult), -1 an
    adverse one (denied), 0 a divided/absent one (mixed/indeterminate). Testimonies that point the
    verdict's way concur; the rest contradict — so the confidence measures agreement WITH the verdict.
    """
    counting = [e for e in evidence if e.counts]
    favour = [e for e in counting if e.polarity is Polarity.SUPPORTS]
    adverse = [e for e in counting if e.polarity is Polarity.CONTRADICTS]
    concur, against = (adverse, favour) if toward < 0 else (favour, adverse)

    supporting, contradicting = len(concur), len(against)
    cancelled = sum(1 for e in evidence
                    if e.antidoted and e.polarity is Polarity.CONTRADICTS)
    wc = sum(e.weight for e in concur)
    wa = sum(e.weight for e in against)
    net = wc - wa

    promise_net = tier_net(evidence, Tier.PROMISE)
    strength_net = tier_net(evidence, Tier.STRENGTH)
    corrob_net = tier_net(evidence, Tier.CORROBORATION)
    promise_mixed = (any(e.tier is Tier.PROMISE and e.counts and e.polarity is Polarity.SUPPORTS
                         for e in evidence)
                     and any(e.tier is Tier.PROMISE and e.counts and e.polarity is Polarity.CONTRADICTS
                             for e in evidence))
    # Does the corroboration tier agree with the verdict direction?
    corrob_agrees = (toward >= 0 and corrob_net > 0) or (toward < 0 and corrob_net < 0)

    contradictions = _contradictions(promise_mixed, promise_net, strength_net, corrob_net)
    if toward == 0:
        # A divided/absent verdict has no direction to concur with: the tally discloses both sides
        # verbatim, and the tier states the division honestly instead of grading a margin.
        tier = "divided" if counting else "insufficient"
    else:
        tier = _tier_label(supporting + contradicting, net, wc + wa, promise_mixed, corrob_agrees)
    caveat = _caveat(supporting + contradicting)
    split_note = _split_note(toward, len(favour), len(adverse))
    return Convergence(supporting=supporting, contradicting=contradicting, cancelled=cancelled,
                       weighted_concur=wc, weighted_against=wa, net=net, tier=tier,
                       contradictions=contradictions, caveat=caveat, split_note=split_note)


def _tier_label(total: int, net: int, denom: int, promise_mixed: bool, corrob_agrees: bool) -> str:
    """The convergence tier: the margin toward the verdict, NORMALIZED by the total weight in play.

    A negative-or-zero net means the verdict was reached over the weight of the evidence (birth-chart
    precedence overruling the rest) — genuinely low confidence, never above 'weak'. The top tiers
    require both an absolute margin AND a high agreement fraction (net/denom), so a topic cannot
    grade par-excellence merely by accumulating a large but contested evidence volume.
    """
    if total == 0:
        return "insufficient"
    if net <= 0:
        return "weak"
    fraction = net / denom if denom else 0.0
    if net >= 5 and fraction >= 0.75 and corrob_agrees and not promise_mixed:
        return "par-excellence"
    if net >= 4 and fraction >= 0.5:
        return "strong"
    if net >= 2:
        return "moderate"
    return "weak"


def _split_note(toward: int, n_favour: int, n_adverse: int) -> str:
    """The majority-vs-headline disclosure: when the RAW testimony count leans against the verdict's
    direction (which the precedence-driven verdict is allowed to do), say so beside the confidence —
    the counterweight that keeps a verdict-oriented tally honest."""
    if toward > 0 and n_adverse > n_favour:
        return (f"note: the raw testimony majority leans the other way ({n_adverse} adverse vs "
                f"{n_favour} favourable); the verdict follows the deciding tier, not the count")
    if toward < 0 and n_favour > n_adverse:
        return (f"note: the raw testimony majority leans the other way ({n_favour} favourable vs "
                f"{n_adverse} adverse); the verdict follows the deciding tier, not the count")
    return ""


def _contradictions(promise_mixed: bool, promise_net: int, strength_net: int, corrob_net: int
                    ) -> tuple[str, ...]:
    """The genuine conflicts to report side by side (contradiction resolution: precedence, not average)."""
    out: list[str] = []
    if promise_mixed:
        out.append("the birth chart is itself divided on this matter — prosperity and affliction "
                   "testimony both fire at the deciding tier")
    if promise_net != 0 and corrob_net != 0 and (promise_net > 0) != (corrob_net > 0):
        out.append(f"the divisional/ashtakavarga corroboration leans "
                   f"{'afflicted' if corrob_net < 0 else 'favourable'} against the birth chart's "
                   f"{'favourable' if promise_net > 0 else 'afflicted'} promise — reported side by "
                   f"side, not averaged (the birth chart decides)")
    if promise_net > 0 and strength_net < 0:
        out.append("the matter is promised but its significators are weak — a promise whose "
                   "delivery is strained")
    return tuple(out)


def _caveat(total: int) -> str:
    """A coverage caveat so thin evidence is never presented as settled."""
    if total == 0:
        return "no decisive testimony bears on this matter for this chart"
    if total < 3:
        return f"thin evidence — only {total} decisive testimon{'y' if total == 1 else 'ies'}; " \
               "read as indicative, not settled"
    return ""
