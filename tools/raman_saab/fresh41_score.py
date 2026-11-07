"""Score the sealed fresh-41 Raman conclusions once (docs/raman_saab/FRESH41_PREREG_2026-11-07.md).

Runs the shipped engine (E), the pre-registered new weighing R1 (a signed tally of the matter's
own fired rules, ties and silence -> favourable), and the two no-fit baselines (B3, always
favourable) on a golden-shaped JSONL. Per-row results go ONLY to --out-dir (kept outside any
repo); stdout carries aggregates, never a verdict or a verdict text.

Usage: python -m tools.raman_saab.fresh41_score --records PATH --out-dir DIR [--seed 20261107]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Optional

CLASSES = ("favourable", "mixed", "afflicted")
_ORD = {"favourable": 0, "mixed": 1, "afflicted": 2}


def dist(got: Optional[str], gold: str) -> int:
    """Ordinal distance; a non-graded answer against a graded gold counts 2 (harness rule)."""
    if got == gold:
        return 0
    if got in _ORD and gold in _ORD:
        return abs(_ORD[got] - _ORD[gold])
    return 2


def tally(nb: int, nm: int) -> str:
    """R1 / B3 decision: more benefic -> favourable, more malefic -> afflicted, else favourable."""
    if nb > nm:
        return "favourable"
    if nm > nb:
        return "afflicted"
    return "favourable"


def score_rows(recs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Judge every graded conclusion; return per-row results and exclusion notes."""
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    import app.raman_saab.judges.house_template as ht
    rows: list[dict[str, Any]] = []
    excluded: list[str] = []
    for r in recs:
        try:
            ch = tg.build_chart(r)
        except Exception as exc:  # pre-registered exclusion: not castable
            excluded.append(f"{r.get('id')}: not castable ({type(exc).__name__})")
            continue
        pfs: dict[int, Any] = {}
        for h, e in r.get("expected_verdicts", {}).items():
            if e.get("verdict") not in CLASSES:
                excluded.append(f"{r.get('id')} {h}: verdict not graded")
                continue
            hn = int(h[1:])
            pf = pfs.setdefault(hn, ht.judge_house(ch, hn))
            sv = next((s for s in pf.significations if s.signification == e["signification"]), None)
            if sv is None:
                excluded.append(f"{r.get('id')} {h}: signification {e['signification']} unknown")
                continue
            L = sv.ledger
            own = e["signification"]
            nb = len(L.fired_benefic)
            nm = len(L.fired_malefic)
            nbo = sum(1 for f in L.fired_benefic if f.rule.signification == own)
            nmo = sum(1 for f in L.fired_malefic if f.rule.signification == own)
            rows.append({"key": f"{r['id']} {h}/{own}", "chart": r["id"],
                         "cast": "birth" if r.get("birth") and (r["birth"] or {}).get("dt") else "stated",
                         "gold": e["verdict"], "E": str(sv.verdict), "R1": tally(nbo, nmo),
                         "B3": tally(nb, nm), "FAV": "favourable"})
    return rows, excluded


def metrics(rows: list[dict[str, Any]], p: str) -> dict[str, Any]:
    """Exact, within-one, real errors and macro recall for predictor `p`."""
    rec = [sum(r[p] == c for r in rows if r["gold"] == c) / n
           for c in CLASSES if (n := sum(r["gold"] == c for r in rows))]
    return {"n": len(rows), "exact": sum(r[p] == r["gold"] for r in rows),
            "within1": sum(dist(r[p], r["gold"]) <= 1 for r in rows),
            "real": sum(dist(r[p], r["gold"]) >= 2 for r in rows),
            "macro_recall": round(sum(rec) / len(rec), 3) if rec else None}


def boot(rows: list[dict[str, Any]], fn: Callable[[list[dict[str, Any]]], int],
         seed: int, n: int = 10000) -> tuple[int, int]:
    """Chart-clustered 95% bootstrap interval of `fn`."""
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[r["chart"]].append(r)
    charts = sorted(by)
    rnd = random.Random(seed)
    vals = sorted(fn([x for c in (rnd.choice(charts) for _ in charts) for x in by[c]])
                  for _ in range(n))
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=20261107)
    a = ap.parse_args()
    recs = [json.loads(l) for l in open(a.records, encoding="utf-8") if l.strip()]
    rows, excluded = score_rows(recs)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "fresh41_rows_SEALED.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    ex = lambda rs, p: sum(r[p] == r["gold"] for r in rs)
    real = lambda rs, p: sum(dist(r[p], r["gold"]) >= 2 for r in rs)
    res: dict[str, Any] = {"excluded": excluded, "metrics": {}, "birth_cast_only": {}}
    for p in ("E", "R1", "B3", "FAV"):
        res["metrics"][p] = metrics(rows, p)
        res["birth_cast_only"][p] = metrics([r for r in rows if r["cast"] == "birth"], p)
    res["D_exact_R1_minus_E"] = ex(rows, "R1") - ex(rows, "E")
    res["D_exact_ci95"] = boot(rows, lambda rs: ex(rs, "R1") - ex(rs, "E"), a.seed)
    res["D_real_R1_minus_E"] = real(rows, "R1") - real(rows, "E")
    res["D_real_ci95"] = boot(rows, lambda rs: real(rs, "R1") - real(rs, "E"), a.seed)
    res["class_split"] = {c: sum(r["gold"] == c for r in rows) for c in CLASSES}
    (out / "fresh41_aggregates.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
