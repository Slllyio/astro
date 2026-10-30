"""Phase 1: restate every published real-outcome null as a bound (docs/validation/SESOI_PREREG.md).

Reads the published results JSONs (nothing is re-run), converts each test to a 0 = no-effect scale,
and gives each one a verdict: SIGNAL / BOUNDED_NULL / UNDERPOWERED. Then pools DerSimonian-Laird
within each engine x family (secondary; optimistic because tests share contrast groups).

Usage:
    py -3.12 -m tools.validation.rebound --derived E:/astro/data/astro_databank/derived --out docs/validation/BOUNDS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from app.empirical.tournament.controls import null_auc_se
from tools.validation.result import Result, emit
from tools.validation.stats import mde80, random_effects, tost

SESOI = {"static": 0.03, "timing": 0.03, "rule": math.log(1.20)}
PREREG = "SESOI_PREREG@a52ccb63"
_W = 3.919928  # 95% CI width in SEs


def _row(engine, family, test, effect, se, se0, n, *, sham=False, withheld=False, note=""):
    return dict(engine=engine, family=family, test=test, effect=float(effect), se=float(se),
                se0=float(se0), n=int(n), sham=sham, withheld=withheld, note=note)


def _static(engine: str, d: dict) -> list[dict]:
    out = []
    for k, v in d.items():
        if "auc" not in v:      # e.g. Raman H8_class_match: a bare match rate, no null reference
            continue
        se = v.get("se") or (v["ci_hi"] - v["ci_lo"]) / _W
        out.append(_row(engine, "static", k, v["auc"] - 0.5, se,
                        null_auc_se(v["n_case"], v["n_contrast"]), v["n_case"],
                        sham=k.startswith("SHAM")))
    return out


def _timing(engine: str, d: dict, *, family_note: str = "") -> list[dict]:
    out = []
    for k, v in d.items():
        if not v.get("n_events"):
            continue
        lo, hi = v.get("lift_ci") or (v["ci_lo"], v["ci_hi"])
        se = (hi - lo) / _W
        out.append(_row(engine, "timing", k, v["mean_lift"], se, se, v["n_events"],
                        withheld=bool(v.get("withheld_saturated") or v.get("status") == "WITHHELD"),
                        note=family_note))
    return out


def _confirmatory(d: dict) -> list[dict]:
    out = []
    for k, v in d.items():
        if "auc" in v:
            lo, hi = v["ci"]
            out.append(_row("raman", "static", k, v["auc"] - 0.5, (hi - lo) / _W,
                            null_auc_se(v["n_case"], v["n_contrast"]), v["n_case"],
                            sham="sham" in k.lower(), note="held-out confirmatory"))
        elif "odds_ratio" in v:
            lo, hi = (math.log(x) for x in v["or_ci"])
            out.append(_row("raman", "rule", k, math.log(v["odds_ratio"]), (hi - lo) / _W,
                            (hi - lo) / _W, v["n_case"],
                            note="log OR (prereg names log RR: scale deviation, flagged)"))
    return out


def load(derived: Path) -> list[dict]:
    rd = lambda p: json.loads((derived / p).read_text(encoding="utf-8"))  # noqa: E731
    rows = _static("parashara", rd("parashara/static_results.json"))
    rows += _timing("parashara", rd("parashara/timing_results.json"))
    rows += _timing("parashara", rd("parashara_ext/transit_results_pooled.json"),
                    family_note="dasha+double transit, pooled A+B")
    rows += _static("raman", rd("raman/static_results.json")["results"])
    rows += _timing("raman", rd("raman/timing_results.json"))
    rows += _confirmatory(rd("raman/confirmatory_results.json"))
    return rows


def judge(rows: list[dict]) -> list[dict]:
    """Attach verdicts. A sham row gates its engine's static family."""
    sham_ok = {}
    for r in rows:
        if r["sham"]:
            ok = abs(r["effect"]) <= 1.959964 * r["se"]
            sham_ok[r["engine"]] = sham_ok.get(r["engine"], True) and ok
    for r in rows:
        if r["sham"]:
            r["verdict"] = "SHAM (gate: " + ("pass" if abs(r["effect"]) <= 1.96 * r["se"] else "FAIL") + ")"
            continue
        res = Result(test_id=f"{r['engine']}:{r['test']}", prereg_id=PREREG, engine=r["engine"],
                     statistic={"static": "AUC-0.5", "timing": "hit_diff", "rule": "logOR"}[r["family"]],
                     unit="event" if r["family"] == "timing" else "person",
                     effect=r["effect"], se=r["se"], se0=r["se0"], sesoi=SESOI[r["family"]],
                     n_cases=r["n"], n_clusters=r["n"],
                     sham_ok=sham_ok.get(r["engine"], True) if r["family"] == "static" else True,
                     config={"source": "published results JSON", "note": r["note"]})
        r.update(verdict="WITHHELD (saturated)" if r["withheld"] else res.verdict,
                 p_tost=res.p_tost, mde80=mde80(r["se0"]), ci90=res.ci90, _result=res)
    return rows


def pools(rows: list[dict]) -> list[dict]:
    out = []
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        if not r["sham"] and not r["withheld"]:
            groups.setdefault((r["engine"], r["family"]), []).append(r)
    for (eng, fam), g in sorted(groups.items()):
        if len(g) < 2:
            continue
        re_ = random_effects([r["effect"] for r in g], [r["se"] for r in g])
        z90 = 1.644854 * re_["se"]
        out.append(dict(engine=eng, family=fam, **re_, sesoi=SESOI[fam],
                        ci90=(re_["effect"] - z90, re_["effect"] + z90),
                        p_tost=tost(re_["effect"], re_["se"], SESOI[fam])))
    return out


def _fmt(x: float) -> str:
    return f"{x:+.3f}"


def markdown(rows: list[dict], pooled: list[dict]) -> str:
    L = ["# Bounds: every published real-outcome null, restated (Phase 1)", "",
         f"Generated by `tools/validation/rebound.py` per `docs/validation/SESOI_PREREG.md` ({PREREG}).",
         "Effects are on a 0 = no-effect scale (AUC − 0.5, hit-rate difference, log OR).",
         "**BOUNDED_NULL** = the 90% CI lies inside ±SESOI: an effect that large is excluded.",
         "**UNDERPOWERED** = neither an effect nor its absence is established.", ""]
    from collections import Counter
    c = Counter(r["verdict"].split(" ")[0] for r in rows if not r["sham"])
    L += ["## Tally", "", " · ".join(f"**{k}** {v}" for k, v in sorted(c.items())), ""]
    L += ["## Per test (primary readout)", "",
          "| engine | family | test | n | effect | 90% CI | SESOI | MDE80 | p_TOST | verdict |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["sham"]:
            L.append(f"| {r['engine']} | {r['family']} | {r['test']} | {r['n']} | {_fmt(r['effect'])} "
                     f"| – | – | – | – | {r['verdict']} |")
            continue
        lo, hi = r["ci90"]
        note = f" ({r['note']})" if r["note"] else ""
        L.append(f"| {r['engine']} | {r['family']} | {r['test']}{note} | {r['n']} | {_fmt(r['effect'])} "
                 f"| {_fmt(lo)}..{_fmt(hi)} | ±{SESOI[r['family']]:.3f} | {r['mde80']:.3f} "
                 f"| {r['p_tost']:.3f} | {r['verdict']} |")
    L += ["", "## Within-engine pools (secondary: optimistic, because tests share contrast groups)", "",
          "| engine | family | k | pooled effect | 90% CI | τ² | I² | p_TOST | bounded at SESOI? |",
          "|---|---|---|---|---|---|---|---|---|"]
    for p in pooled:
        lo, hi = p["ci90"]
        L.append(f"| {p['engine']} | {p['family']} | {p['k']} | {_fmt(p['effect'])} | {_fmt(lo)}..{_fmt(hi)} "
                 f"| {p['tau2']:.5f} | {p['i2']:.2f} | {p['p_tost']:.4f} | "
                 f"{'yes' if p['p_tost'] < 0.05 else 'no'} |")
    L += ["", "Not covered here: Raman 91-rule enrichment (per-rule results were never persisted; moves to "
          "Phase 4.2), Raman `H8_class_match` (a bare match rate with no null reference), and withheld "
          "(saturated) timing instruments (listed, never pooled).", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sink", type=Path, default=None, help="append Result records (JSONL)")
    a = ap.parse_args(argv)
    rows = judge(load(a.derived))
    pooled = pools(rows)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(markdown(rows, pooled), encoding="utf-8")
    if a.sink:
        for r in rows:
            if "_result" in r:
                emit(r["_result"], a.sink)
    print(f"[rebound] {len(rows)} tests, {len(pooled)} pools -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
