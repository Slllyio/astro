"""Judgment — the final deterministic synthesis for one topic, on the classical axis.

`judge_topic` gathers every tier of evidence for a topic's bhava(s), converges it, and states a
verdict on the axis Parashara's readings actually use — not a bare good/bad, but **granted / delayed /
difficult / denied** (with `mixed` when the chart is genuinely divided, `indeterminate` when nothing
decisive bears on it). The distinction is the whole point of reasoning between the rules:

  * **granted** — promised, the significators deliver, the divisions corroborate.
  * **delayed** — promised, but a substantive affliction was CANCELLED by a BPHS antidote. Parashara's
    antidotes soften adversity into postponement, they do not erase it: the matter comes, but late —
    look to the activated windows for when.
  * **difficult** — promised, but the significators are weak or a division weakens it: it comes with
    struggle.
  * **denied** — the birth chart's own affliction (its non-cancelled annihilation) outweighs the
    promise. The birth chart decides; strength or a division cannot manufacture a promise it withheld.

The verdict reads the tiers by precedence: the PROMISE tier settles denied-vs-granted; cancellation
(the antidote) and the STRENGTH/CORROBORATION tiers separate delay and difficulty from a clean grant.
Every judgment carries its `Convergence` (the tally + tier confidence) and its full `evidence` list —
which, rendered line by line, IS the audit trail (sloka -> rule -> condition -> evidence).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

from app.parashara.reading import ParasharaReading
from app.parashara.synthesis.activation import ActiveWindow, activation_evidence, active_windows
from app.parashara.synthesis.convergence import Convergence, converge, tier_net
from app.parashara.synthesis.corroboration import gather_corroboration
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier
from app.parashara.synthesis.evidence_engine import (
    gather_affliction, gather_promise, gather_strength)
from app.parashara.synthesis.topics import Topic, house_topic

#: verdict -> its direction for the verdict-oriented convergence (+1 favourable, -1 adverse, 0 split).
_DIRECTION: Final[dict[str, int]] = {
    "granted": 1, "delayed": 1, "difficult": 1, "denied": -1, "mixed": 0, "indeterminate": 0}

#: verdict -> its one-line meaning (for rendering; the verdict itself is the machine-readable value).
VERDICT_MEANING: Final[dict[str, str]] = {
    "granted": "promised, its significators deliver, and the divisions corroborate",
    "delayed": "promised, but a substantive affliction was cancelled by an antidote — it comes, but "
               "late; see the activated windows",
    "difficult": "promised, but its significators are weak or the divisions weaken it — it comes "
                 "with struggle",
    "denied": "the birth chart's own affliction outweighs the promise (the birth chart decides)",
    "mixed": "the birth chart is genuinely divided — reported side by side, not averaged",
    "indeterminate": "no decisive testimony bears on this matter for this chart",
}


@dataclass(frozen=True)
class Judgment:
    """The synthesised judgment for one topic — verdict, convergence confidence, evidence, timing."""
    topic: str
    houses: tuple[int, ...]
    verdict: str                     # granted | delayed | difficult | denied | mixed | indeterminate
    meaning: str
    convergence: Convergence
    evidence: tuple[Evidence, ...]
    windows: tuple[ActiveWindow, ...]

    @property
    def headline(self) -> str:
        return (f"{self.topic}: {self.verdict} — {self.convergence.tally} "
                f"[{self.convergence.tier}]")

    @property
    def audit(self) -> tuple[str, ...]:
        """The audit trail: one `sloka -> rule -> condition -> evidence` line per testimony."""
        return tuple(e.audit_line for e in self.evidence)


def judge_topic(reading: ParasharaReading, topic: Topic) -> Judgment:
    """Gather -> converge -> decide the verdict for one topic (a bhava or a named-matter view)."""
    evidence: list[Evidence] = []
    for house in topic.houses:
        evidence += gather_promise(reading, house)
        evidence += gather_affliction(reading, house)
        evidence += gather_strength(reading, house)
        evidence += gather_corroboration(reading, house)
    windows = active_windows(reading, topic.houses)
    evidence += activation_evidence(reading, topic.houses, windows)

    verdict = _verdict(evidence)
    convergence = converge(evidence, toward=_DIRECTION[verdict])
    return Judgment(topic=topic.name, houses=topic.houses, verdict=verdict,
                    meaning=VERDICT_MEANING[verdict], convergence=convergence,
                    evidence=tuple(evidence), windows=windows)


def judge_house(reading: ParasharaReading, house: int) -> Judgment:
    """Convenience: judge a single bhava (1..12) as a topic."""
    return judge_topic(reading, house_topic(house))


def _verdict(evidence: Sequence[Evidence]) -> str:
    """The granted/delayed/difficult/denied axis, read by precedence (see module docstring).

    The PROMISE tier (ch.11) settles denied-vs-granted; the overall weighted balance separates a
    genuine denial (affliction dominates throughout) from a *difficult* outcome (an afflicted promise
    that strength/corroboration drag back into a struggling manifestation); cancellation and the
    STRENGTH/CORROBORATION tiers separate delay and difficulty from a clean grant.
    """
    counting = [e for e in evidence if e.counts]
    if not counting:
        return "indeterminate"

    promise_net = tier_net(evidence, Tier.PROMISE)
    strength_net = tier_net(evidence, Tier.STRENGTH)
    corrob_net = tier_net(evidence, Tier.CORROBORATION)
    overall = sum(int(e.polarity) * e.weight for e in counting)  # favourable-oriented weighted net
    # A substantive antidote: a promise-tier affliction that was cancelled — excluding ch.11's
    # always-mild "unaspected_by_lord", which is antidoted by definition and is not an obstruction.
    cancelled = any(e.tier is Tier.PROMISE and e.antidoted
                    and e.polarity is Polarity.CONTRADICTS
                    and e.condition != "unaspected_by_lord"
                    for e in evidence)

    if promise_net < 0:
        return "denied" if overall < 0 else "difficult"
    if promise_net == 0:
        if cancelled:
            return "delayed"
        return "difficult" if overall < 0 else "mixed"   # neutral promise, but obstructed -> difficult
    if cancelled:
        return "delayed"
    if strength_net < 0 or corrob_net < 0 or overall < 0:
        return "difficult"
    return "granted"
