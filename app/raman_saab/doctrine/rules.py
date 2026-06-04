"""The ``RuleRecord`` — the data form of every corpus combination (spec §5.2).

An *evaluable* rule carries a ``Condition`` tree that fires/doesn't against a chart.
A *descriptive* rule is a narrative outcome surfaced with its citation when a
placement holds (the placement layer lands with the encoder; ``condition`` is None).
Every record cites a real on-disk corpus line (``source``); a test enforces it.

Usage:
    r = RuleRecord(id="H7.B.1", house=7, signification="spouse", group="combination",
                   kind="evaluable",
                   condition=And(InRashiHouse("Saturn", 7), Aspects("Mars", "Saturn")),
                   fortified="...", afflicted="...", frame="LAGNA", varga="D1",
                   polarity="malefic", source=Citation("HTJAH-II", 235))
    r.fires(chart)   # -> bool
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.conditions import Condition, EvalContext
from app.raman_saab.doctrine.sources import Citation

Kind = Literal["evaluable", "descriptive"]
Polarity = Literal["benefic", "malefic", "neutral", "maraka"]


@dataclass(frozen=True)
class RuleRecord:
    id: str                              # e.g. "H7.B.23a"
    house: int                           # 1..12
    signification: str                   # which matter of the house (spec §6.1)
    group: str                           # "combination" | "lord_in_house" | "planet_in_house" | ...
    kind: Kind
    condition: Optional[Condition]       # predicate tree (evaluable); None for descriptive
    fortified: str                       # result text when the house/lord/karaka is strong
    afflicted: Optional[str]             # result text when afflicted
    frame: str                           # LAGNA | MOON | KARAKA | FROM(...) | STRONGEST_OF([...])
    varga: str                           # D1 | D9 | ...
    polarity: Polarity
    source: Citation

    def fires(self, chart: RamanChart) -> bool:
        """Evaluable rules: does the condition hold for this chart? Descriptive: always False
        (they are surfaced by placement, not boolean-scored)."""
        if self.kind != "evaluable" or self.condition is None:
            return False
        return self.condition.evaluate(EvalContext(chart))
