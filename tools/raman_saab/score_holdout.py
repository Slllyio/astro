"""Score a sealed hold-out fixture ONCE (docs/raman_saab/FIDELITY_FIXES_PREREG.md).

Variants R1/R3b/R4 are applied through tools.raman_saab.fidelity_variants; patch-based variants
(R2, R5) must be applied to the working tree before running and reverted after.

Usage:
    python -m tools.raman_saab.score_holdout FIXTURE.jsonl LABEL [R4] [--out result.json]
"""
from __future__ import annotations

import hashlib
import json
import sys


def main(fixture: str, label: str, variants: set[str], out: str | None) -> None:
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    from tools.raman_saab import fidelity_variants as fv
    recs = [json.loads(l) for l in open(fixture, encoding="utf-8") if l.strip() and not l.startswith("#")]
    fv.apply(variants)
    rows = []
    try:
        for r in recs:
            ch = tg.build_chart(r)
            for h, e in r["expected_verdicts"].items():
                g = tg._signification_verdict(ch, int(h[1:]), e["signification"])
                rows.append((f"{r['id']} {h}/{e['signification']}", r["book"], e["verdict"], g,
                             tg._ordinal_distance(g, e["verdict"])))
    finally:
        fv.apply(set())
    verdicts = {k: g for k, _, _, g, _ in rows}
    sha = hashlib.sha256(json.dumps(verdicts, sort_keys=True).encode()).hexdigest()
    n = len(rows)
    ex = sum(d == 0 for *_, d in rows); w1 = sum(d <= 1 for *_, d in rows); re_ = sum(d >= 2 for *_, d in rows)
    print(f"{label}: exact {ex}/{n}  within-1 {w1}/{n}  real {re_}  sha {sha}")
    if out:
        json.dump({"label": label, "exact": ex, "within1": w1, "real": re_, "n": n, "sha": sha,
                   "rows": rows}, open(out, "w"), indent=1)


if __name__ == "__main__":
    a = sys.argv[1:]
    out = a[a.index("--out") + 1] if "--out" in a else None
    a = [x for x in a if x not in ("--out", out)]
    main(a[0], a[1], set(a[2:]), out)
