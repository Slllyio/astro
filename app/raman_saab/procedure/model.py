"""Record types for the procedure reader (all frozen dataclasses, JSON-safe via ``to_dict``).

The reader is a SEPARATE INSTRUMENT: these records are never read by ``house_template``, the
scored judge, the golden ratchet or the report sections. ``ProcedureReading.to_dict`` follows
the engine's convention (``dataclasses.asdict`` on frozen records, plain JSON leaves; see
``app/raman_saab/report_json.py``).

Every step record carries ``cite`` (an ``HTJAH:<line>`` string, verified by test) and ``basis``:
``"doctrine"`` where the step is Raman's printed rule or practice, ``"convention"`` where he gives
no mechanical rule and the reader adopts the simplest documented one (named in ``note``).

Usage:
    from app.raman_saab.procedure.model import ProcedureReading
    reading.to_dict()     # JSON-serialisable dict
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

Basis = Literal["doctrine", "convention"]

#: Raman's ordinal grade words, weakest first (HTJAH:1801-1815, 4485-4486, 5819; spec 3.4).
GRADES: tuple[str, ...] = ("afflicted", "blemished", "moderate", "fairly strong", "strong")

#: The template steps, in the order Raman prints them (spec 3.1).
TEMPLATE_ORDER: tuple[str, ...] = ("house", "lord", "karaka", "moon", "conclusion")


@dataclass(frozen=True)
class Item:
    """One contributing testimony inside a factor: what it is, its weight (+1 good, -1 bad, 0
    named but not counted), the sub-step it belongs to and its citation."""
    substep: str            # "position" | "dignity" | "associates" | "aspecters" | "kartari" | ...
    text: str
    weight: int
    cite: str
    basis: Basis = "doctrine"


@dataclass(frozen=True)
class Factor:
    """A graded factor of the template (house, lord, karaka or the view from the Moon)."""
    step: str               # one of TEMPLATE_ORDER[:4]
    subject: str            # "the 4th house (Aquarius)", "the 4th lord Venus", ...
    items: tuple[Item, ...]
    rasi_grade: str         # grade from the Rasi items alone
    navamsa_shift: int      # -1, 0 or +1 (one step at most, HTJAH:4688-4689)
    navamsa_note: str
    grade: str              # final grade after the Navamsa step
    redeeming: bool         # a benefic testimony is present (the floor of spec 4.4)
    merged_with: Optional[str] = None   # "lord" when the karaka is the lord itself
    note: str = ""

    @property
    def vote(self) -> str:
        """good / neutral / bad, the unit the two-of-three tally counts."""
        i = GRADES.index(self.grade)
        return "good" if i >= 3 else ("bad" if i <= 1 else "neutral")


@dataclass(frozen=True)
class Conclusion:
    """The conclusion step: tally, tie-break, verdict, outcome and Raman-style sentence."""
    votes: tuple[tuple[str, str], ...]     # ((factor step, vote), ...)
    tally: str                             # verdict from the plain two-of-three count
    rule: str                              # which decision rule settled the verdict
    rule_cite: str
    rule_basis: Basis
    verdict: str                           # favourable | mixed | afflicted
    outcome: str                           # e.g. "denial", "comes but suffers", "comes and lasts"
    sub_answers: tuple[tuple[str, str], ...] = ()   # e.g. education: knowledge / schooling
    sentence: str = ""


@dataclass(frozen=True)
class Candidate:
    """One proposed period: Mahadasha and Bhukti lords with dates and the reason each lord
    qualifies; the MD-AD relation where rank or survival is at stake; the transit note (last,
    an accelerator only); and the engine's own fructification tier as a separate field."""
    maha: str
    antar: str
    start: str              # YYYY-MM
    end: str
    start_age: float
    maha_reason: str
    antar_reason: str
    relation: str = ""
    transit: str = ""
    engine_tier: str = ""   # labelled separately: Raman never applies these words (spec 7.1)
    strength: int = 0       # death rules only: maraka weight of MD + AD lords (convention)


@dataclass(frozen=True)
class TimingRule:
    """One timing rule applied to one matter: who qualifies and why, what was pruned, and the
    candidate periods (both lords qualify, the bhukti lord carrying the event)."""
    event: str              # e.g. "death of the mother"
    kind: str               # good_event | rank | relative_death | marriage | native_death
    cite: str
    qualifiers: tuple[tuple[str, str], ...]   # ((planet, reason), ...)
    pruned: tuple[str, ...]
    window: str             # the age window searched
    candidates: tuple[Candidate, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class MatterReading:
    """House -> Lord -> Karaka -> From the Moon -> Conclusion -> timing, for one matter."""
    house: int
    matter: str
    label: str
    karaka: Optional[str]
    karaka_note: str
    factors: tuple[Factor, ...]
    conclusion: Conclusion
    timing: tuple[TimingRule, ...] = ()

    @property
    def steps(self) -> tuple[str, ...]:
        """The template steps in the order this reading holds them."""
        return tuple(f.step for f in self.factors) + ("conclusion",)


@dataclass(frozen=True)
class StageZero:
    """Done once per chart before any house (spec 2)."""
    lagna: str
    functional: tuple[tuple[str, str], ...]     # ((planet, nature), ...)
    yogakarakas: tuple[str, ...]
    stronger_reference: str                     # "lagna" | "moon"
    stronger_note: str
    span_years: Optional[float]
    span_class: Optional[str]
    span_method: Optional[str]
    balarishta: Optional[str]
    dasas: tuple[tuple[str, str, str, str], ...]  # ((lord, start, end, "within span" | ...), ...)
    cites: tuple[str, ...]
    special_features: tuple[str, ...] = ()      # Raman's opening paragraph (features.py)


@dataclass(frozen=True)
class ProcedureReading:
    """The whole reading: Stage 0, then the houses in Raman's order (1st to 12th)."""
    name: str
    ayanamsa: str
    stage_zero: StageZero
    matters: tuple[MatterReading, ...]
    conventions: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable form (``dataclasses.asdict``)."""
        return asdict(self)
