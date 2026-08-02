"""Real-outcome validation harness — score the engine against CONFIRMED real lives.

Grows the real-outcome generalization track beyond the single committed field_case_01. Reads
a PRIVATE (git-ignored) case file (`data/private/real_outcomes.json`) holding confirmed
nativities, and scores each on the SAME two axes as `tests/raman_saab/test_field_case_01.py`:

  * STATIC  — each confirmed per-signification verdict, engine within 1 ordinal step (afflicted
              < mixed < favourable) of the real life.
  * TIMING  — each dated life event's house (or an aux house) is ACTIVE in the daśā running at
              its date.

The tool is generic and PII-free; the data lives only in the git-ignored private file. When
that file is absent (CI / a fresh clone) the tool reports "nothing to validate" and exits 0.

Usage:
    py -3.12 -m tools.raman_saab.real_outcome_validate
    py -3.12 -m tools.raman_saab.real_outcome_validate --file data/private/real_outcomes.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import house_template as ht
from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification.events import LifeEvent

_DEFAULT = Path("data/private/real_outcomes.json")
_POS = {"afflicted": 0, "mixed": 1, "favourable": 2}


def _ordinal_distance(got: str | None, truth: str) -> int:
    if got == truth:
        return 0
    if got in _POS and truth in _POS:
        return abs(_POS[got] - _POS[truth])
    return 2


def _chart(case: dict):
    b = case["birth"]
    return cast_chart(BirthData(name=case.get("id", "case"), year=b["year"], month=b["month"],
                                day=b["day"], hour=b["hour"], minute=b["minute"],
                                tz_offset=b["tz_offset"], latitude=b["latitude"],
                                longitude=b["longitude"]), ayanamsa=case.get("ayanamsa", "raman"))


def _static(chart, case) -> tuple[int, int, list[str]]:
    within1 = total = 0
    misses: list[str] = []
    for hstr, sigs in case.get("confirmed_verdicts", {}).items():
        engine = {sv.signification: sv.verdict for sv in ht.judge_house(chart, int(hstr)).significations}
        for key, truth in sigs.items():
            got = engine.get(key)
            total += 1
            if _ordinal_distance(got, truth) <= 1:
                within1 += 1
            else:
                misses.append(f"H{hstr}.{key}: engine={got} truth={truth}")
    return within1, total, misses


def _timing(chart, case) -> tuple[int, int, list[str]]:
    hits = total = 0
    misses: list[str] = []
    for e in case.get("events", []):
        ev = LifeEvent(e["event_type"], e["year"], e["month"], e.get("day"))
        houses = (ev.spec.house, *ev.spec.aux_houses)
        acts = {a.house for a in vim.active_houses(chart, ev.jd_point())}
        total += 1
        if any(h in acts for h in houses):
            hits += 1
        else:
            misses.append(f"{e['event_type']} {e['year']}-{e['month']:02d} houses{houses}")
    return hits, total, misses


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Validate the engine against confirmed real lives.")
    ap.add_argument("--file", type=Path, default=_DEFAULT)
    args = ap.parse_args(argv)

    if not args.file.is_file():
        print(f"[real-outcome] no private case file at {args.file} — nothing to validate.")
        return 0

    cases = json.loads(args.file.read_text(encoding="utf-8")).get("cases", [])
    print(f"[real-outcome] validating {len(cases)} confirmed real live(s) from {args.file}\n")
    ok = True
    for case in cases:
        chart = _chart(case)
        sw, st, sm = _static(chart, case)
        th, tt, tm = _timing(chart, case)
        base = case.get("baseline", {})
        s_floor = base.get("static_within1", 0)
        t_floor = base.get("timing_hits", 0)
        s_pass = sw >= s_floor
        t_pass = th >= t_floor
        ok = ok and s_pass and t_pass
        print(f"== {case.get('name', case.get('id'))} ==")
        print(f"  STATIC within-1: {sw}/{st}  (floor {s_floor})  {'PASS' if s_pass else 'FAIL'}")
        for m in sm:
            print(f"       miss: {m}")
        print(f"  TIMING hits    : {th}/{tt}  (floor {t_floor})  {'PASS' if t_pass else 'FAIL'}")
        for m in tm:
            print(f"       dormant: {m}")
        print()
    print(f"[real-outcome] OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
