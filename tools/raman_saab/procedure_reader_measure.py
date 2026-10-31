"""Measure the procedure reader against the golden ledger (pre-registered, run once).

Two measurements, both pre-registered in ``docs/raman_saab/PROCEDURE_READER_2026-10-25.md``
section 3 before the first run:

1. **Verdicts.** Every CONFIRMED Track-B worked-example row (the harness's ``_TRACK_B_RATCHET``,
   ``confirmed_verdicts`` and ``build_chart``) is read by ``read_matter`` on the matter that
   ``SIGNIFICATION_MATTER`` names, and scored with the harness's ``_ordinal_distance``: exact,
   within one, real errors (distance 2), confusion matrix.
2. **Timing.** Raman's printed dated events (the table in the doc, encoded in ``EVENTS`` below)
   are checked against the candidate periods of the matching timing rule: hit, whether the printed
   period lies in the rule's window at all, the rule's base rate (share of bhuktis in the window
   that are candidates) and, for death rules, the strength-rank percentile of the printed pair.

The harness is loaded from its file path (``tests/`` is not a package), as
``tools/raman_saab/tune_thresholds.py`` does, so the reader is scored exactly as the judge is.

Usage:
    python -m tools.raman_saab.procedure_reader_measure
    python -m tools.raman_saab.procedure_reader_measure --json out.json
"""
from __future__ import annotations

import argparse
import importlib.util as _ilu
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.raman_saab.procedure import timing as tm
from app.raman_saab.procedure.matters import SIGNIFICATION_MATTER, matter_for
from app.raman_saab.procedure.model import TimingRule
from app.raman_saab.procedure.reader import read_matter, stage_zero

logger = logging.getLogger(__name__)

_HARNESS_PATH = Path(__file__).resolve().parents[2] / "tests" / "raman_saab" / "test_goldens.py"
_spec = _ilu.spec_from_file_location("_raman_golden_harness_proc", _HARNESS_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"cannot load golden harness from {_HARNESS_PATH}")
_harness = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_harness)

#: The engine's current figures (CLAUDE.md, 2026-10-24), shown beside the reader's.
ENGINE = {"exact": 269, "within1": 354, "real": 35, "total": 389}


@dataclass(frozen=True)
class DatedEvent:
    """One printed dated event: the golden id, the matter read, the rule kind, the period."""
    gid: str
    house: int
    matter: str
    kind: str
    maha: Optional[str]
    antar: Optional[str]


def _e(gid: str, house: int, matter: str, kind: str, maha: Optional[str],
       antar: Optional[str] = None) -> DatedEvent:
    return DatedEvent(gid, house, matter, kind, maha, antar)


_ND, _RD, _GE, _RK = "native_death", "relative_death", "good_event", "rank"

#: Pre-registered event table (doc section 3), period lords as Raman prints them.
EVENTS: tuple[DatedEvent, ...] = (
    _e("HTJAH-II.chart_35", 8, "longevity", _ND, "Rahu", "Sun"),
    _e("HTJAH-II.chart_73", 8, "longevity", _ND, "Saturn", "Mercury"),
    _e("HTJAH-II.chart_74", 8, "longevity", _ND, "Jupiter", "Sun"),
    _e("HTJAH-II.chart_75", 8, "longevity", _ND, "Jupiter", "Saturn"),
    _e("HTJAH-II.chart_78", 8, "longevity", _ND, "Rahu", "Moon"),
    _e("HTJAH-I.h6_02", 8, "longevity", _ND, "Rahu", "Saturn"),
    _e("HTJAH-I.h4_01", 4, "mother", _RD, "Mars", "Saturn"),
    _e("HTJAH-I.x67", 4, "mother", _RD, "Rahu", "Jupiter"),
    _e("HTJAH-I.x69", 4, "mother", _RD, "Rahu", "Rahu"),
    _e("HTJAH-I.x71", 4, "mother", _RD, "Mars", "Saturn"),
    _e("HTJAH-I.x72", 4, "mother", _RD, "Venus", "Venus"),
    _e("HTJAH-I.x73", 4, "mother", _RD, "Saturn", "Venus"),
    _e("HTJAH-II.h9_01", 9, "father", _RD, "Saturn", "Ketu"),
    _e("HTJAH-II.h9_03", 9, "father", _RD, "Venus", "Mercury"),
    _e("HTJAH-II.h9_04", 9, "father", _RD, "Saturn", "Jupiter"),
    _e("HTJAH-II.h9_05", 9, "father", _RD, "Mars", "Mercury"),
    _e("HTJAH-II.h9_06", 9, "father", _RD, "Rahu", "Saturn"),
    _e("HTJAH-II.h9_07", 9, "father", _RD, "Jupiter", "Rahu"),
    _e("HTJAH-II.h9_08", 9, "father", _RD, "Jupiter", "Mercury"),
    _e("HTJAH-II.h9_09", 9, "father", _RD, "Jupiter", "Ketu"),
    _e("HTJAH-II.h9_12", 9, "father", _RD, "Mercury", "Rahu"),
    _e("HTJAH-II.h9_13", 9, "father", _RD, "Saturn", "Rahu"),
    _e("HTJAH-II.h7_09", 7, "marriage", _RD, "Rahu", "Venus"),
    _e("HTJAH-II.h7_11", 7, "marriage", _RD, "Rahu", "Ketu"),
    _e("HTJAH-II.h7_12", 7, "marriage", _RD, "Saturn", "Saturn"),
    _e("HTJAH-II.h7_13", 7, "marriage", _RD, "Mars", "Venus"),
    _e("HTJAH-I.chart_38", 2, "wealth", _GE, "Saturn", "Venus"),
    _e("HTJAH-I.chart_40", 2, "wealth", _GE, "Ketu", "Mercury"),
    _e("HTJAH-I.h4_05", 4, "vehicles", _GE, "Jupiter", "Venus"),
    _e("HTJAH-I.h4_06", 4, "property", _GE, "Jupiter", "Mars"),
    _e("HTJAH-I.h5_13", 5, "children", _GE, "Ketu"),
    _e("HTJAH-II.h11_14", 11, "gains", _GE, "Venus", "Rahu"),
    _e("HTJAH-II.h11_15", 11, "gains", _GE, "Jupiter", "Jupiter"),
    _e("HTJAH-II.h11_16", 11, "gains", _GE, "Jupiter", "Sun"),
    _e("HTJAH-II.h11_17", 11, "gains", _GE, "Saturn", "Rahu"),
    _e("HTJAH-II.h11_18", 11, "gains", _GE, "Mercury"),
    _e("HTJAH-II.h9_15", 9, "fortune", _GE, "Ketu", "Rahu"),
    _e("HTJAH-II.h9_17", 9, "fortune", _GE, "Sun", "Jupiter"),
    _e("HTJAH-II.h9_18", 9, "fortune", _GE, "Jupiter", "Jupiter"),
    _e("HTJAH-II.h10_01", 10, "profession", _RK, None, "Rahu"),
    _e("HTJAH-II.h10_05", 10, "profession", _RK, "Rahu", "Mars"),
    # bad events of a house, read with the house's influence set (the good_event rule)
    _e("HTJAH-I.chart_39", 2, "eyes", _GE, "Jupiter", "Rahu"),
    _e("HTJAH-I.chart_44", 2, "wealth", _GE, "Ketu", "Venus"),
    _e("HTJAH-I.chart_12", 1, "self", _GE, "Jupiter"),
    _e("HTJAH-I.h6_11", 6, "disease_enemies", _GE, "Rahu"),
    _e("HTJAH-I.h6_12", 6, "disease_enemies", _GE, "Sun"),
    _e("HTJAH-I.h6_12", 6, "disease_enemies", _GE, "Moon"),
    _e("HTJAH-I.h6_13", 6, "disease_enemies", _GE, "Sun"),
    _e("HTJAH-I.h6_13", 6, "disease_enemies", _GE, "Moon"),
    _e("HTJAH-II.h12_09", 12, "losses", _GE, "Rahu"),
)

_BAD_EVENT_IDS = frozenset({"HTJAH-I.chart_39", "HTJAH-I.chart_44", "HTJAH-I.chart_12",
                            "HTJAH-I.h6_11", "HTJAH-I.h6_12", "HTJAH-I.h6_13",
                            "HTJAH-II.h12_09"})


# -- verdicts ----------------------------------------------------------------------------------

def measure_verdicts() -> dict[str, Any]:
    """Score the reader's verdicts on every CONFIRMED Track-B worked-example row."""
    exact = within1 = total = 0
    matrix: Counter[tuple[str, str]] = Counter()
    by_house: dict[int, list[int]] = {}
    real: list[str] = []
    unmapped: Counter[str] = Counter()
    for rec in _harness._TRACK_B_RATCHET:
        chart = _harness.build_chart(rec)
        for house, entry in _harness.confirmed_verdicts(rec):
            sig = entry["signification"]
            key = SIGNIFICATION_MATTER.get(sig)
            if key is None:
                unmapped[sig] += 1
            matter = matter_for(house, key)
            got = read_matter(chart, house, matter.key, with_timing=False).conclusion.verdict
            want = entry["verdict"]
            d = _harness._ordinal_distance(got, want)
            total += 1
            exact += d == 0
            within1 += d <= 1
            matrix[(want, got)] += 1
            hb = by_house.setdefault(house, [0, 0, 0])
            hb[0] += 1
            hb[1] += d == 0
            hb[2] += d >= 2
            if d >= 2:
                real.append(f"{rec['id']} H{house} {sig} ({matter.key}): expected {want}, "
                            f"reader {got}")
    return {"total": total, "exact": exact, "within1": within1, "real": len(real),
            "matrix": {f"{w}->{g}": n for (w, g), n in sorted(matrix.items())},
            "by_house": {h: {"rows": v[0], "exact": v[1], "real": v[2]}
                         for h, v in sorted(by_house.items())},
            "real_errors": real, "unmapped_significations": dict(unmapped)}


# -- timing ------------------------------------------------------------------------------------

_WIN_RE = re.compile(r"ages (\d+) to (\d+)|birth to about age (\d+)")


def _window(rule: TimingRule) -> tuple[float, float]:
    m = _WIN_RE.search(rule.window)
    if m is None:
        raise ValueError(f"unparsed window {rule.window!r}")
    if m.group(3) is not None:
        return 0.0, float(m.group(3))
    return float(m.group(1)), float(m.group(2))


def _matches(maha: Optional[str], antar: Optional[str], m: str, a: str) -> bool:
    return (maha is None or m == maha) and (antar is None or a == antar)


def measure_timing() -> dict[str, Any]:
    """Check each printed dated event against its timing rule's candidate periods."""
    recs = {r["id"]: r for r in _harness.load_goldens()}
    rows: list[dict[str, Any]] = []
    for ev in EVENTS:
        rec = recs.get(ev.gid)
        if rec is None or _harness._birth_from(rec) is None:
            rows.append({"id": ev.gid, "error": "no record with birth data"})
            continue
        chart = _harness.build_chart(rec)
        s0 = stage_zero(chart)
        mr = read_matter(chart, ev.house, ev.matter, with_timing=True, span=s0.span_years,
                         span_class=s0.span_class)
        rule = next((t for t in mr.timing if t.kind == ev.kind), None)
        if rule is None:
            rows.append({"id": ev.gid, "error": f"no {ev.kind} rule on {ev.matter}"})
            continue
        lo, hi = _window(rule)
        periods = tm._bhuktis(chart, lo, hi)
        in_window = any(_matches(ev.maha, ev.antar, b.maha, b.antar) for b in periods)
        hit = any(_matches(ev.maha, ev.antar, c.maha, c.antar) for c in rule.candidates)
        base = len(rule.candidates) / len(periods) if periods else 0.0
        q = {p for p, _ in rule.qualifiers}
        row: dict[str, Any] = {
            "id": ev.gid, "kind": ev.kind, "matter": ev.matter,
            "printed": f"{ev.maha or '?'}/{ev.antar or '-'}",
            "bad_event": ev.gid in _BAD_EVENT_IDS,
            "hit": hit, "in_window": in_window, "base_rate": round(base, 3),
            "maha_qualifies": ev.maha is None or ev.maha in q,
            "antar_qualifies": ev.antar is None or ev.antar in q,
            "n_candidates": len(rule.candidates), "n_periods": len(periods),
            "span": s0.span_years, "window": rule.window,
        }
        if ev.kind in (_ND, _RD) and hit and rule.candidates:
            st = [c.strength for c in rule.candidates]
            mine = max(c.strength for c in rule.candidates
                       if _matches(ev.maha, ev.antar, c.maha, c.antar))
            above = sum(1 for s in st if s > mine)
            row["strength"] = mine
            row["strength_percentile"] = round(above / len(st), 3)
        rows.append(row)
    summary: dict[str, Any] = {}
    groups = {"native_death": lambda r: r["kind"] == _ND,
              "relative_death": lambda r: r["kind"] == _RD,
              "good_event": lambda r: r["kind"] == _GE and not r["bad_event"],
              "bad_event_of_house": lambda r: r["kind"] == _GE and r["bad_event"],
              "rank": lambda r: r["kind"] == _RK}
    for name, pred in groups.items():
        g = [r for r in rows if "error" not in r and pred(r)]
        if not g:
            continue
        hits = sum(r["hit"] for r in g)
        base = sum(r["base_rate"] for r in g) / len(g)
        s = {"n": len(g), "hits": hits, "in_window": sum(r["in_window"] for r in g),
             "hit_rate": round(hits / len(g), 3), "mean_base_rate": round(base, 3),
             "lift": round((hits / len(g)) / base, 2) if base else None}
        pct = [r["strength_percentile"] for r in g if "strength_percentile" in r]
        if pct:
            s["mean_strength_percentile"] = round(sum(pct) / len(pct), 3)
        summary[name] = s
    return {"events": rows, "summary": summary,
            "errors": [r for r in rows if "error" in r]}


def main(argv: Optional[list[str]] = None) -> int:
    """Run both measurements and print them (optionally write JSON)."""
    ap = argparse.ArgumentParser(prog="tools.raman_saab.procedure_reader_measure")
    ap.add_argument("--json", help="write the full result to this path")
    a = ap.parse_args(argv)
    v = measure_verdicts()
    t = measure_timing()
    print(f"VERDICTS  reader: {v['exact']}/{v['total']} exact, {v['within1']} within one, "
          f"{v['real']} real errors   |   engine: {ENGINE['exact']}/{ENGINE['total']}, "
          f"{ENGINE['within1']}, {ENGINE['real']}")
    print("  matrix (expected->reader):", v["matrix"])
    print("  by house:", v["by_house"])
    print("  unmapped significations:", v["unmapped_significations"])
    print("TIMING")
    for name, s in t["summary"].items():
        print(f"  {name}: {s}")
    for r in t["events"]:
        print("   ", {k: r[k] for k in r if k not in ("window",)})
    if a.json:
        Path(a.json).write_text(json.dumps({"verdicts": v, "timing": t}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
