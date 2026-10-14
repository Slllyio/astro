"""Topics — the units the synthesis reasons about: the twelve bhavas.

The bhava (1..12) is the engine's native verdict unit and the synthesis judges exactly those twelve;
named cross-house matters (wealth, moksha) are ROLLED UP from the per-house judgments in
`synthesis.py` — they are views, never a separate evidence pool (pooling made confidence thresholds
house-count-dependent and pinned timing to an arbitrary first house; replaced 2026-08-29).

House -> matter and house -> karaka are fixed BPHS tables (ch.11-23 significations, ch.32 karakas),
so a Topic is chart-invariant scaffolding; only the evidence gathered onto it is per-nativity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.parashara.doctrine.bhava_karaka import karaka_of


@dataclass(frozen=True)
class Topic:
    """A subject of judgment: a human name, the bhava it reads from, and its significator."""
    name: str
    houses: tuple[int, ...]      # exactly one bhava (the tuple shape kept for the audit surface)
    karakas: tuple[str, ...]     # the natural significator graha (BPHS ch.32)


#: bhava -> its human name (the ch.11-23 significations, in brief). The twelve-topic spine.
#: The 6th is named by ch.11's own content — enemies, ulcers/disease, obstacles (BPHS-11:79-81);
#: "health" would state the house by its opposite, and ch.11 places debts at the 10TH (BPHS-11:106-109).
HOUSE_MATTER: Final[dict[int, str]] = {
    1: "body, self & vitality",
    2: "wealth & family",
    3: "siblings, courage & effort",
    4: "home, mother & contentment",
    5: "children & intellect",
    6: "enemies, disease & obstacles",
    7: "marriage & partnership",
    8: "longevity & upheaval",
    9: "fortune, father & dharma",
    10: "career & status",
    11: "gains & fulfilment",
    12: "loss, expense & liberation",
}


def house_topic(house: int) -> Topic:
    """The single-bhava topic for `house` (1..12)."""
    if not 1 <= house <= 12:
        raise ValueError("house must be 1..12")
    return Topic(name=f"{ordinal(house)} house — {HOUSE_MATTER[house]}",
                 houses=(house,), karakas=(karaka_of(house),))


def all_topics() -> tuple[Topic, ...]:
    """The twelve bhava topics — the whole judgment spine (cross-matters roll up in synthesis)."""
    return tuple(house_topic(h) for h in range(1, 13))


_ORDINALS: Final[dict[int, str]] = {
    1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
    7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th"}


def ordinal(house: int) -> str:
    """The English ordinal for a house number (shared by the synthesis renderers)."""
    return _ORDINALS[house]
