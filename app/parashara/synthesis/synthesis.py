"""The synthesis report — every bhava judged, cross-house matters rolled up, the layer's capstone.

`synthesize(reading)` judges the twelve bhavas (the spine) and then builds the named cross-house
views (wealth, moksha) as ROLL-UPS of the per-house judgments: when a matter's component houses
agree, the shared verdict stands; when they disagree, the view says `mixed` and reports each house's
own verdict side by side — parallel, never averaged (the Measured-Truth default). A matter view
never pools evidence: pooling made the confidence thresholds depend on how many houses a matter
spans, and its timing pinned to an arbitrary first house.

Pure and deterministic — a function of the reading, no LLM anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.reading import ParasharaReading
from app.parashara.synthesis.judgment import Judgment, judge_topic
from app.parashara.synthesis.topics import all_topics, ordinal

#: Cross-house named matters — views rolled up from >1 bhava (kept small and classical).
#: Wealth = the 2nd (accumulated, BPHS-11:53) with the 11th (gains, BPHS-11:131-133). The
#: moksha-trikona GROUPING (4/8/12) is a later classificatory convention with no locus in this
#: corpus — kept for its usefulness, labeled as such; 12 = emancipation IS corpus-backed
#: (BPHS-32:521 "The 12th house indicates final emancipation").
CROSS_MATTER: Final[dict[str, tuple[int, ...]]] = {
    "prosperity (wealth & gains)": (2, 11),
    "liberation (moksha)": (4, 8, 12),
}


@dataclass(frozen=True)
class MatterView:
    """A named cross-house view: the component houses' verdicts, rolled up without averaging."""
    name: str
    houses: tuple[int, ...]
    component_verdicts: Mapping[int, str]   # house -> its own judgment's verdict
    verdict: str                            # the shared verdict, or "mixed" when they disagree
    note: str                               # the split, spelled out; '' when the houses agree


@dataclass(frozen=True)
class SynthesisReport:
    """Every bhava's judgment plus the rolled-up named-matter views."""
    houses: Mapping[int, Judgment]          # 1..12 — the spine, each with evidence/audit/windows
    matters: Mapping[str, MatterView]       # named views over the spine (no separate evidence)

    @property
    def all_judgments(self) -> tuple[Judgment, ...]:
        """Every full judgment (the twelve houses, in order). Matter views carry no evidence of
        their own — read their component houses."""
        return tuple(self.houses[h] for h in sorted(self.houses))


def _matter_view(name: str, houses: tuple[int, ...],
                 judged: Mapping[int, Judgment]) -> MatterView:
    verdicts = {h: judged[h].verdict for h in houses}
    distinct = set(verdicts.values())
    if len(distinct) == 1:
        return MatterView(name=name, houses=houses, component_verdicts=verdicts,
                          verdict=next(iter(distinct)), note="")
    split = "; ".join(f"{ordinal(h)}: {verdicts[h]}" for h in houses)
    return MatterView(name=name, houses=houses, component_verdicts=verdicts, verdict="mixed",
                      note=f"{split} — reported side by side, not averaged")


def synthesize(reading: ParasharaReading) -> SynthesisReport:
    """Judge the twelve bhavas, then roll the named matters up from those judgments."""
    houses = {t.houses[0]: judge_topic(reading, t) for t in all_topics()}
    matters = {name: _matter_view(name, hs, houses) for name, hs in CROSS_MATTER.items()}
    return SynthesisReport(houses=houses, matters=matters)
