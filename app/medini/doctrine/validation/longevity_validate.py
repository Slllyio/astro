"""Outcome-classification pilot: does the engine's STRENGTH verdict predict Raman's stated
LONGEVITY CLASS? (Balarishta < Alpayu < Madhyayu < Purnayu.)

The 9-grade strength map grades a *strength* phrase; much of Raman's 8th-house prose instead
states an *outcome* -- the longevity class -- which the map (correctly) won't grade. This
harness tests those outcomes directly, as an ordinal-classification problem orthogonal to the
strength deltas: for each labelled 8th-house chart, reconstruct it, score the 8th lord /
Ayushkaraka / 8th bhava with the LIVE engine (`judge_house_doctrine`), and Spearman rank-
correlate each score against the longevity-class ordinal.

Labels: `heldout_longevity_ch12_8th.json` (Raman's explicit class, or death-age-derived).
Grids joined from `heldout_ch12_8th.json` on chart_no. Measurement only -- no engine change.

CLI:
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.longevity_validate
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.medini.doctrine.domains.house_judgment import judge_house_doctrine
from app.medini.doctrine.validation import reconstruct as R

_DIR = Path(__file__).resolve().parents[4] / "docs/raman_doctrine/validation/corpora"
_LABELS = _DIR / "heldout_longevity_ch12_8th.json"
_GRIDS = _DIR / "heldout_ch12_8th.json"
_FACTORS = ("lord", "karaka", "bhava", "concl")


def _spearman(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Spearman rho + two-sided p (t-approx). Kept dependency-free so the harness has no
    scipy requirement; ties are average-ranked."""
    import math

    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    vy = math.sqrt(sum((b - my) ** 2 for b in ry))
    rho = cov / (vx * vy) if vx and vy else 0.0
    # two-sided p via t-distribution approximation
    if n > 2 and abs(rho) < 1.0:
        t = rho * math.sqrt((n - 2) / (1 - rho * rho))
        p = _t_sf(abs(t), n - 2) * 2
    else:
        p = 0.0 if abs(rho) == 1.0 else 1.0
    return rho, p


def _t_sf(t: float, df: int) -> float:
    """Survival function of Student-t (one-sided) via the regularised incomplete beta."""
    import math
    x = df / (df + t * t)
    return 0.5 * _betai(df / 2.0, 0.5, x)


def _betai(a: float, b: float, x: float) -> float:
    import math
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b + lbeta) / a
    # Lentz continued fraction
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 200):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1.0 / d
        c = 1.0 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= d * c
        if abs(1.0 - d * c) < 1e-8:
            break
    return front * (f - 1.0)


def run(labels_path: Path = _LABELS, grids_path: Path = _GRIDS) -> dict[str, Any]:
    labels = json.loads(Path(labels_path).read_text())["labels"]
    grids = {c["chart_no"]: c for c in json.loads(Path(grids_path).read_text())["charts"]}
    rows, skipped = [], []
    for lab in labels:
        cn = lab["chart_no"]
        rec = grids.get(cn)
        if not rec or "navamsa" not in rec or R.consistency_errors(rec["rasi"], rec["navamsa"]):
            skipped.append({"chart": cn, "why": "no_grid_or_gate"})
            continue
        try:
            chart = R.chart_from_raman(rec["rasi"], rec["navamsa"],
                                       rec["lagna_rasi"], rec["lagna_navamsa"])
        except (ValueError, KeyError) as e:
            skipped.append({"chart": cn, "why": str(e)})
            continue
        j = judge_house_doctrine(chart, 8)
        rows.append({"chart": cn, "class": lab["class"], "ord": lab["class_ord"],
                     "lord": round(j.lord_verdict.score, 2),
                     "karaka": round(j.karaka_verdict.score, 2),
                     "bhava": round(j.lagna_verdict.score, 2),
                     "concl": round(j.conclusion.score, 2)})
    rows.sort(key=lambda r: r["ord"])
    ords = [r["ord"] for r in rows]
    corr = {}
    for f in _FACTORS:
        rho, p = _spearman([r[f] for r in rows], ords)
        corr[f] = {"rho": round(rho, 3), "p": round(p, 3)}
    return {"n": len(rows), "rows": rows, "spearman": corr,
            "n_skipped": len(skipped), "skipped": skipped}


def _print(s: dict) -> None:
    print(f"labelled & scored: {s['n']}")
    print(f"{'ch':>4} {'class':<11} {'ord':>3} {'lord':>7} {'karaka':>7} {'bhava':>6} {'concl':>6}")
    for r in s["rows"]:
        print(f"{r['chart']:>4} {r['class']:<11} {r['ord']:>3} {r['lord']:>7} "
              f"{r['karaka']:>7} {r['bhava']:>6} {r['concl']:>6}")
    print("\nSpearman (engine score vs longevity-class ordinal):")
    for f, v in s["spearman"].items():
        flag = "  <-- predicts" if v["p"] < 0.1 and v["rho"] > 0 else ""
        print(f"  {f:<7} rho={v['rho']:+.3f}  p={v['p']:.3f}{flag}")
    if s["skipped"]:
        print("skipped:", s["skipped"])


def main() -> None:
    _print(run())
    if "--json" in sys.argv:
        print(json.dumps(run(), indent=1))


if __name__ == "__main__":
    main()
