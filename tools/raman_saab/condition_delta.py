"""Condition-delta harness — what a proposed predicate change would actually do.

Playbook rule 3 says measure BEFORE doctrine review and review BEFORE ship. For a TEXT change
that is easy: text cannot move a verdict. For a CONDITION change it is the whole game, because
the rule starts or stops firing and the golden ratchet moves. This is the instrument for that,
generalised out of the H8 lord-in-house narrowing (2026-09-01), where it was improvised.

It answers three questions about a proposed condition, in the order they should be asked:

  1. COVERAGE  — how many golden charts does the rule fire on now, and how many under the
     proposal? A narrowing that removes most firings is a strong signal the encoded predicate
     was not Raman's; a widening that fires on most charts is a strong signal the proposal is
     not his either.
  2. EXPOSURE  — of the charts whose firing changes, how many carry a SCORED expectation for
     that rule's house? A change touching no scored row cannot move the ratchet, and its
     safety is then a coverage question, not an accuracy one.
  3. IMPACT    — which scored rows actually change verdict, and in which direction. This is
     the number that decides whether a faithful change is also a measurable improvement, and
     it is reported per row so a re-base can be argued from the specific charts.

WHY IT REPORTS DIRECTION, NOT JUST A COUNT. The H8 narrowing cost one exact match and turned
it into an inversion — but the diagnosis (the engine had been reaching Raman's verdict through
a rule he would not have applied to that chart) is what justified shipping it anyway. A bare
delta would have argued for reverting. Always read the per-row lines, not the totals.

REPORT-ONLY / read-only: it evaluates conditions and re-judges houses in memory. It writes
nothing and changes no engine state.

Usage:
    # the H8-style check: does this rule's house-lord conjunction narrow it?
    py -3.12 -m tools.raman_saab.condition_delta --lord-conjunction H8.L.4
    py -3.12 -m tools.raman_saab.condition_delta --lord-conjunction-scan 8
    py -3.12 -m tools.raman_saab.condition_delta --lord-conjunction-scan 1,2,3

    # in a script, for an arbitrary proposal:
    from tools.raman_saab.condition_delta import measure
    print(measure("H4.L.7", C.And(C.LordIn(4, 7), C.Aspects("Jupiter", "Moon"))))
"""
from __future__ import annotations

import argparse
import importlib.util as _ilu
from dataclasses import dataclass, field
from pathlib import Path as _Path

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.conditions import Condition, EvalContext
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_HARNESS = _Path(__file__).resolve().parents[2] / "tests" / "raman_saab" / "test_goldens.py"
_spec = _ilu.spec_from_file_location("_raman_golden_harness_delta", _HARNESS)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load golden harness from {_HARNESS}")
_h = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_h)

_RULES = {r.id: r for r in ALL_RULES}


@dataclass(frozen=True)
class Delta:
    """What a proposed condition would do to one rule."""
    rule_id: str
    house: int
    fires_now: int
    fires_proposed: int
    charts_total: int
    #: charts whose firing changes AND which carry a scored expectation for this house
    exposed: tuple[str, ...] = ()
    #: (chart, signification, golden, verdict_now, verdict_proposed) for rows that MOVE
    moved: tuple[tuple[str, str, str, str, str], ...] = ()
    notes: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        pct = (100.0 * (self.fires_now - self.fires_proposed) / self.fires_now
               if self.fires_now else 0.0)
        out = [f"{self.rule_id} (H{self.house})",
               f"  coverage : {self.fires_now} -> {self.fires_proposed} of "
               f"{self.charts_total} goldens  ({pct:.0f}% of firings removed)",
               f"  exposure : {len(self.exposed)} changed chart(s) carry a scored H"
               f"{self.house} expectation"]
        if self.moved:
            out.append(f"  IMPACT   : {len(self.moved)} scored row(s) change verdict")
            for cid, sig, gold, now, prop in self.moved:
                flag = "FIXES" if prop == gold else ("BREAKS" if now == gold else "shifts")
                out.append(f"     [{flag}] {cid} H{self.house}/{sig}: "
                           f"golden={gold} | now={now} -> proposed={prop}")
        else:
            out.append("  IMPACT   : no scored row changes verdict "
                       "(coverage-only change; cannot move the ratchet)")
        for n in self.notes:
            out.append(f"  note     : {n}")
        return "\n".join(out)


def _golden_charts() -> list[tuple[str, dict, RamanChart]]:
    out: list[tuple[str, dict, RamanChart]] = []
    for rec in _h.load_goldens():
        try:
            out.append((_h._id(rec), rec, _h.build_chart(rec)))
        except Exception:
            continue          # a record that will not cast is test_goldens' business
    return out


def _scored(rec: dict, house: int) -> list[tuple[str, str]]:
    """[(signification, golden verdict)] for scored expectations on `house`."""
    return [(e["signification"], e["verdict"])
            for h, e in _h.confirmed_verdicts(rec) if h == house]


def measure(rule_id: str, proposed: Condition,
            charts: list | None = None) -> Delta:
    """Coverage, exposure and per-row verdict impact of swapping one rule's condition.

    The verdict arm re-judges the house with the rule's condition temporarily swapped. The
    swap is restored in a `finally`, so an exception mid-measurement cannot leave the corpus
    mutated — this runs against the live rule objects, and a leaked swap would silently
    corrupt every later measurement in the same process."""
    rule = _RULES[rule_id]
    charts = charts if charts is not None else _golden_charts()
    original = rule.condition

    fires_now = fires_new = 0
    changed: list[tuple[str, dict, RamanChart]] = []
    for cid, rec, ch in charts:
        ctx = EvalContext(ch)
        a = bool(original and original.evaluate(ctx))
        b = bool(proposed.evaluate(ctx))
        fires_now += a
        fires_new += b
        if a != b:
            changed.append((cid, rec, ch))

    exposed = tuple(cid for cid, rec, _ch in changed if _scored(rec, rule.house))
    moved: list[tuple[str, str, str, str, str]] = []
    notes: list[str] = []
    try:
        for cid, rec, ch in changed:
            scored = _scored(rec, rule.house)
            if not scored:
                continue
            before = {sig: _h._signification_verdict(ch, rule.house, sig)
                      for sig, _g in scored}
            object.__setattr__(rule, "condition", proposed)
            after = {sig: _h._signification_verdict(ch, rule.house, sig)
                     for sig, _g in scored}
            object.__setattr__(rule, "condition", original)
            for sig, gold in scored:
                if before[sig] != after[sig]:
                    moved.append((cid, sig, gold, str(before[sig]), str(after[sig])))
    finally:
        object.__setattr__(rule, "condition", original)

    if fires_now and fires_new == 0:
        notes.append("proposal fires on NO golden — it becomes an unmeasured blind spot "
                     "(rule-liveness floor will move)")
    if fires_now and (fires_now - fires_new) / fires_now > 0.75:
        notes.append("removes >75% of firings — either the encoded predicate was badly "
                     "over-broad, or the proposal is too narrow; check the source sentence")
    return Delta(rule_id, rule.house, fires_now, fires_new, len(charts),
                 exposed, tuple(moved), notes)


def lord_conjunction(rule_id: str) -> Condition:
    """The H8-shaped proposal: require the house lord to be WITH the target house's own lord.

    Raman writes this as "the lord of the 8th house in conjunction with the 2nd lord in the
    2nd house" (HTJAH-II:2916). `LordsConjunct` is identity-false, so a rule whose own house
    IS the target house (HN.L.N) can never satisfy it — those are excluded by the scan."""
    rule = _RULES[rule_id]
    target = int(rule_id.rsplit(".", 1)[-1])
    return C.And(C.LordIn(rule.house, target),
                 C.LordsConjunct(rule.house, target))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--lord-conjunction", metavar="RULE_ID",
                   help="measure the house-lord-conjunction narrowing on one lord_in_house rule")
    g.add_argument("--lord-conjunction-scan", metavar="HOUSES",
                   help="comma-separated house numbers; scan all 12 lord_in_house rules of each")
    args = ap.parse_args()

    charts = _golden_charts()
    print(f"[condition-delta] {len(charts)} golden charts cast\n")

    targets: list[str] = []
    if args.lord_conjunction:
        targets = [args.lord_conjunction]
    else:
        for h in (int(x) for x in args.lord_conjunction_scan.split(",")):
            targets += [f"H{h}.L.{k}" for k in range(1, 13)
                        if k != h and f"H{h}.L.{k}" in _RULES]   # HN.L.N is identity-false

    for rid in targets:
        if rid not in _RULES:
            print(f"{rid}: not in the corpus\n")
            continue
        print(measure(rid, lord_conjunction(rid), charts))
        print()


if __name__ == "__main__":
    main()
