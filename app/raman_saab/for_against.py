"""For and against, matter by matter — Raman's cited reasons laid out, with a plain count.

Built after the 2026-10-30/31 measurements (docs/raman_saab/CEILING_CHECK_RESULTS_2026-10-30.md,
WEIGHTED_JUDGE_PREREG, REASON_CODING_RESULTS_2026-10-31.md, TALLY_JUDGE_PREREG):

- On 198 of Raman's own conclusions the engine had not been tuned on, a plain count of the
  benefic against the malefic rules that fire for a matter matched him 131 times; the clause
  judge matched 87. No weighted or re-signed variant beat the plain count.
- Raman himself reaches a verdict by adding up the reasons he states (his coded reasons recover
  84% of his verdicts), so a count of cited reasons is also the closest form to his method.
- His verdicts on famous charts also lean on what is known of the life, and no rule-based
  verdict has predicted real outcomes (the 47k-chart validation), so this is presented as his
  reasons, not as a forecast.

For each matter: every rule that speaks for it and against it, with Raman's reading and line,
and the count's lean. The clause judge's verdict is shown beside it where they differ.

PREC-10: a pure re-read of the judged ledgers. No verdict is re-judged and nothing feeds back.

Usage:
    from app.raman_saab.for_against import for_against, NOTICE
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: The fixed honesty notice; every figure is a measured one (see the module docstring).
NOTICE: Final[str] = (
    "Each matter below lists the rules from Raman's books that speak for it and against it, "
    "with his reading and the line it comes from, and then simply counts them. On 198 of "
    "Raman's own worked conclusions that the engine was not tuned on, this count agreed with "
    "him 131 times (66%), more often than the engine's older clause judge (87 times). Raman's "
    "verdicts also draw on what was known of each life, and in tests on real lives no "
    "rule-based verdict has predicted outcomes better than chance. Read these as Raman's "
    "reasons, weighed as he weighed them, not as a forecast.")

LEAN_FOR: Final[str] = "leans favourable"
LEAN_AGAINST: Final[str] = "leans afflicted"
LEAN_EVEN: Final[str] = "evenly balanced"
LEAN_SILENT: Final[str] = "no rule speaks"


@dataclass(frozen=True)
class Reason:
    rule_id: str
    reading: str
    cite: str


@dataclass(frozen=True)
class MatterTally:
    house: int
    matter: str
    reasons_for: tuple[Reason, ...]
    reasons_against: tuple[Reason, ...]
    lean: str
    judge_verdict: str

    @property
    def count_line(self) -> str:
        return f"{len(self.reasons_for)} for, {len(self.reasons_against)} against: {self.lean}"


@dataclass(frozen=True)
class ForAgainst:
    matters: tuple[MatterTally, ...]
    notice: str = NOTICE


def lean_of(n_for: int, n_against: int) -> str:
    if n_for > n_against:
        return LEAN_FOR
    if n_against > n_for:
        return LEAN_AGAINST
    return LEAN_EVEN if n_for else LEAN_SILENT


def _reasons(fired) -> tuple[Reason, ...]:
    out: dict[str, Reason] = {}
    for fr in fired:
        src = fr.rule.source
        out.setdefault(fr.rule.id, Reason(rule_id=fr.rule.id, reading=(fr.text or "").strip(),
                                          cite=f"{src.work}:{src.line}"))
    return tuple(out.values())


def for_against(r: "DetailedReport") -> ForAgainst:
    """Lay out, per matter, the cited rules for and against and their count. Pure re-read."""
    matters = []
    for pf in sorted(getattr(r, "proformas", ()) or (), key=lambda p: p.house):
        for sv in getattr(pf, "significations", ()) or ():
            led = getattr(sv, "ledger", None)
            if led is None:
                continue
            pro, con = _reasons(led.fired_benefic), _reasons(led.fired_malefic)
            matters.append(MatterTally(house=pf.house, matter=sv.signification.replace("_", " "),
                                       reasons_for=pro, reasons_against=con,
                                       lean=lean_of(len(pro), len(con)),
                                       judge_verdict=str(sv.verdict)))
    return ForAgainst(matters=tuple(matters))
