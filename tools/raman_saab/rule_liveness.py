"""Rule-liveness / coverage harness — which doctrine rules the goldens actually exercise.

The golden ratchet proves the engine's VERDICTS match Raman on 192 worked charts. It does NOT
tell you how much of the 845-rule doctrine surface those charts fire. A rule that never fires on
any golden is an unmeasured blind spot: it could be broken (condition never True), mis-cited, or
simply beyond the corpus — and nothing would catch a regression in it.

This tool casts every golden chart and tallies, per rule, how many charts it fires on. It reports:
  * evaluable rules (kind="evaluable", condition present) that fire on >=1 golden vs NEVER;
  * the same for the 72 named yogas.
Descriptive rules (condition is None) are excluded by construction — they never fire.

REPORT-ONLY / read-only: casts charts + evaluates conditions; changes no engine state.

Usage:
    py -3.12 -m tools.raman_saab.rule_liveness
    py -3.12 -m tools.raman_saab.rule_liveness --list-never   # print every never-firing rule id
"""
from __future__ import annotations

import argparse
import importlib.util as _ilu
import sys
from dataclasses import dataclass
from pathlib import Path as _Path

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.conditions import EvalContext
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.doctrine.yogas import YOGAS

# Load the golden harness by file path (tests/ is deliberately not an importable package).
_HARNESS_PATH = _Path(__file__).resolve().parents[2] / "tests" / "raman_saab" / "test_goldens.py"
_spec = _ilu.spec_from_file_location("_raman_golden_harness_liveness", _HARNESS_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load golden harness from {_HARNESS_PATH}")
_harness = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_harness)
load_goldens = _harness.load_goldens
build_chart = _harness.build_chart


def golden_charts() -> list[tuple[str, RamanChart]]:
    """Every golden record cast to a chart (id, chart). Records that fail to build are skipped
    (they are exercised by test_goldens' own schema guards, not here)."""
    out: list[tuple[str, RamanChart]] = []
    for rec in load_goldens():
        try:
            out.append((str(rec.get("id", "?")), build_chart(rec)))
        except Exception:  # noqa: BLE001 - a build failure is not a liveness signal
            continue
    return out


def _evaluable_rules() -> list:
    return [r for r in ALL_RULES if r.kind == "evaluable" and r.condition is not None]


def _fires(cond, chart: RamanChart) -> bool:
    try:
        return bool(cond.evaluate(EvalContext(chart)))
    except Exception:  # noqa: BLE001 - a rule that errors on a chart did not fire on it
        return False


def rule_fire_counts(charts: list[tuple[str, RamanChart]]) -> dict[str, int]:
    """rule id -> number of golden charts it fires on (evaluable rules only)."""
    counts: dict[str, int] = {}
    for r in _evaluable_rules():
        counts[r.id] = sum(1 for _, ch in charts if _fires(r.condition, ch))
    return counts


def yoga_fire_counts(charts: list[tuple[str, RamanChart]]) -> dict[str, int]:
    """yoga id -> number of golden charts it fires on."""
    counts: dict[str, int] = {}
    for y in YOGAS:
        counts[y.id] = sum(1 for _, ch in charts if _fires(y.condition, ch))
    return counts


@dataclass(frozen=True)
class LivenessSummary:
    evaluable_total: int
    evaluable_fired: int
    never_fired: tuple[str, ...]        # evaluable rule ids that fire on 0 goldens
    yogas_total: int
    yogas_fired: int
    yogas_never: tuple[str, ...]

    def as_baseline(self) -> dict[str, int]:
        """The compact ratchet baseline (counts only — the id lists are informational)."""
        return {
            "evaluable_total": self.evaluable_total,
            "evaluable_fired": self.evaluable_fired,
            "never_fired": len(self.never_fired),
            "yogas_total": self.yogas_total,
            "yogas_fired": self.yogas_fired,
            "yogas_never": len(self.yogas_never),
        }


def liveness_summary(charts: list[tuple[str, RamanChart]] | None = None) -> LivenessSummary:
    charts = charts if charts is not None else golden_charts()
    rc = rule_fire_counts(charts)
    yc = yoga_fire_counts(charts)
    never = tuple(sorted(rid for rid, n in rc.items() if n == 0))
    yn = tuple(sorted(yid for yid, n in yc.items() if n == 0))
    return LivenessSummary(
        evaluable_total=len(rc), evaluable_fired=sum(1 for n in rc.values() if n > 0),
        never_fired=never, yogas_total=len(yc), yogas_fired=sum(1 for n in yc.values() if n > 0),
        yogas_never=yn)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Measure rule/yoga liveness over the golden corpus.")
    ap.add_argument("--list-never", action="store_true",
                    help="print every never-firing evaluable rule id + yoga id")
    args = ap.parse_args(argv)

    charts = golden_charts()
    s = liveness_summary(charts)
    print(f"[rule-liveness] golden charts cast: {len(charts)}")
    print(f"[rule-liveness] evaluable rules: {s.evaluable_fired}/{s.evaluable_total} fire on >=1 "
          f"golden  ({len(s.never_fired)} never fire)")
    print(f"[rule-liveness] yogas: {s.yogas_fired}/{s.yogas_total} fire on >=1 golden  "
          f"({len(s.yogas_never)} never fire)")
    print(f"[rule-liveness] descriptive rules (condition=None) excluded: "
          f"{sum(1 for r in ALL_RULES if r.condition is None)}")
    if args.list_never:
        print("\n-- evaluable rules that never fire on any golden --")
        for rid in s.never_fired:
            print(f"  {rid}")
        print("\n-- yogas that never fire on any golden --")
        for yid in s.yogas_never:
            print(f"  {yid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
