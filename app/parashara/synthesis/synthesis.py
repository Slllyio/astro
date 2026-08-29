"""The synthesis report — every topic judged, the capstone of the reasoning layer.

`synthesize(reading)` runs the whole pipeline over every topic: the twelve bhavas (the spine) and the
cross-house named-matter views (wealth, moksha). Each becomes a `Judgment` carrying its verdict, its
doctrinal-convergence confidence, its full cited evidence (the audit trail), and its activation
windows (the timing). It is a pure, deterministic function of the reading — the reasoning the engine
does BETWEEN its rules, assembled in one place.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.parashara.reading import ParasharaReading
from app.parashara.synthesis.judgment import Judgment, judge_topic
from app.parashara.synthesis.topics import all_topics


@dataclass(frozen=True)
class SynthesisReport:
    """Every topic's synthesised judgment: the twelve bhavas + the cross-house named-matter views."""
    houses: Mapping[int, Judgment]        # 1..12 — the bhava spine
    matters: Mapping[str, Judgment]       # named cross-house views (e.g. "prosperity (wealth & gains)")

    @property
    def all_judgments(self) -> tuple[Judgment, ...]:
        """Every judgment, houses in order then the named matters."""
        return tuple(self.houses[h] for h in sorted(self.houses)) + tuple(self.matters.values())


def synthesize(reading: ParasharaReading) -> SynthesisReport:
    """Judge every topic (12 bhavas + named-matter views) for a reading."""
    houses: dict[int, Judgment] = {}
    matters: dict[str, Judgment] = {}
    for topic in all_topics():
        judgment = judge_topic(reading, topic)
        if topic.is_house:
            houses[topic.houses[0]] = judgment
        else:
            matters[topic.name] = judgment
    return SynthesisReport(houses=houses, matters=matters)
