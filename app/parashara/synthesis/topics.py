"""Topics — the units the synthesis reasons about: the twelve bhavas, and named life-matters.

The bhava (1..12) is the engine's native verdict unit, so it is the spine: the synthesis judges all
twelve. On top of that spine sit *named-matter views* — the life-matters a reader actually asks about
("marriage", "career", "children") — each mapped to the bhava(s) BPHS reads it from and to that
matter's natural significator(s). A single-house matter is just that house wearing a human name; a
cross-house matter (wealth = the 2nd of accumulated wealth AND the 11th of gains) rolls its houses'
judgments together.

House -> matter and house -> karaka are both fixed BPHS tables (ch.11-23 for the significations,
ch.32 for the karakas), so a Topic is chart-invariant scaffolding; only the evidence gathered onto it
is per-nativity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.parashara.doctrine.bhava_karaka import karaka_of


@dataclass(frozen=True)
class Topic:
    """A subject of judgment: a human name, the bhava(s) it reads from, and its significator(s)."""
    name: str
    houses: tuple[int, ...]      # the bhava(s) this matter is judged from
    karakas: tuple[str, ...]     # the natural significator graha(s) (BPHS ch.32)

    @property
    def is_house(self) -> bool:
        """True for the twelve single-bhava topics (the spine); False for cross-house matter views."""
        return len(self.houses) == 1


#: bhava -> its human name (the ch.11-23 significations, in brief). The twelve-topic spine.
HOUSE_MATTER: Final[dict[int, str]] = {
    1: "body, self & vitality",
    2: "wealth & family",
    3: "siblings, courage & effort",
    4: "home, mother & contentment",
    5: "children & intellect",
    6: "health, debts & enemies",
    7: "marriage & partnership",
    8: "longevity & upheaval",
    9: "fortune, father & dharma",
    10: "career & status",
    11: "gains & fulfilment",
    12: "loss, expense & liberation",
}

#: Cross-house named matters — views that roll >1 bhava together (kept small and classical).
#: Wealth is the 2nd (accumulated) with the 11th (gains); the moksha trikona is the 4th/8th/12th.
CROSS_MATTER: Final[dict[str, tuple[int, ...]]] = {
    "prosperity (wealth & gains)": (2, 11),
    "liberation (moksha)": (4, 8, 12),
}


def _karakas(houses: tuple[int, ...]) -> tuple[str, ...]:
    """The distinct significators of the given houses, in house order (BPHS ch.32)."""
    seen: list[str] = []
    for h in houses:
        k = karaka_of(h)
        if k not in seen:
            seen.append(k)
    return tuple(seen)


def house_topic(house: int) -> Topic:
    """The single-bhava topic for `house` (1..12)."""
    if not 1 <= house <= 12:
        raise ValueError("house must be 1..12")
    return Topic(name=f"{_ordinal(house)} house — {HOUSE_MATTER[house]}",
                 houses=(house,), karakas=_karakas((house,)))


def all_topics() -> tuple[Topic, ...]:
    """The twelve bhava topics (the spine) followed by the cross-house named-matter views."""
    spine = tuple(house_topic(h) for h in range(1, 13))
    cross = tuple(Topic(name=name, houses=houses, karakas=_karakas(houses))
                  for name, houses in CROSS_MATTER.items())
    return spine + cross


_ORDINALS: Final[dict[int, str]] = {
    1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
    7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th"}


def _ordinal(house: int) -> str:
    return _ORDINALS[house]
