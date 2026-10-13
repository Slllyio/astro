"""Phase 4.2: pooled rule effect + dose-response for Raman's rules (docs/validation/PHASE4_2_RULES_PREREG.md).

Usage:
    py -3.12 -m tools.validation.rules_pooling --derived E:/astro/data/astro_databank/derived --out docs/validation/PHASE4_2_RESULTS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from tools.raman_saab.astrobank.rule_enrichment import OUTCOMES, _rule_index
from tools.validation.result import Result, emit
from tools.validation.stats import random_effects, tost

PREREG = "PHASE4_2_RULES_PREREG@0c3d2f66"
SESOI = math.log(1.20)


def pooled_rules(enr: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    e = enr.copy()
    k = e.k_case.where(e.k_case > 0, 0.5)
    e["log_rr"] = np.log(np.maximum(k, 0.5) / e.n_fired / e.base)
    e["se"] = np.sqrt((1 - e.rate.clip(upper=0.999)) / k)
    re_ = random_effects(e.log_rr, e.se)
    re_["p_tost"] = tost(re_["effect"], re_["se"], SESOI)
    re_["share_rr_gt_1"] = float((e.log_rr > 0).mean())
    from scipy.stats import binomtest
    re_["sign_p"] = float(binomtest(int((e.log_rr > 0).sum()), len(e), 0.5).pvalue)
    return re_, e


def dose_response(derived: Path) -> list[dict]:
    R = derived / "raman"
    labels = pd.read_parquet(R / "labels.parquet")
    fires = pd.read_parquet(R / "rule_fires.parquet")
    pop = pd.read_parquet(R / "store_population.parquet")
    master = pd.read_parquet(R / "person_master.parquet").set_index("person_id")
    tier_ok = set(master[master.quality_tier.isin(["A", "B"])].index) & set(pop.person_id)
    by_map = {m: set(g.person_id) & tier_ok for m, g in labels.groupby("map_id")}
    control = set(pop[pop.is_control].person_id) & tier_ok
    meta = {rid: (sig, pol) for rid, sig, pol in _rule_index()}
    fires = fires[fires.rule_id.isin(meta)]
    fires["sig"] = fires.rule_id.map(lambda r: meta[r][0])
    fires["pol"] = fires.rule_id.map(lambda r: meta[r][1])
    out = []
    for outcome, (case_map, contrast_map, want_pol, sig) in OUTCOMES.items():
        case = by_map.get(case_map, set())
        universe = case | (by_map.get(contrast_map, set()) if contrast_map else control)
        if len(case) < 20:
            continue
        cnt = fires[(fires.sig == sig) & (fires.pol == want_pol)].groupby("person_id").size()
        df = pd.DataFrame({"person_id": sorted(universe)})
        df["y"] = df.person_id.isin(case).astype(float)
        df["count"] = df.person_id.map(cnt).fillna(0.0)
        df["decade"] = (master.loc[df.person_id, "birth_date"].str[:4].astype(int) // 10 * 10).to_numpy()
        if df["count"].std() == 0:
            continue
        # decade adjustment by conditional logistic regression (decade = stratum): strata with only
        # cases or only contrasts drop out instead of causing separation (deviation note in results)
        from statsmodels.discrete.conditional_models import ConditionalLogit
        try:
            fit = ConditionalLogit(df.y.to_numpy(), df[["count"]].to_numpy(), groups=df.decade.to_numpy()).fit(disp=0)
            out.append({"outcome": outcome, "n": len(df), "n_case": int(df.y.sum()),
                        "mean_count": float(df["count"].mean()), "slope": float(fit.params[0]),
                        "se": float(fit.bse[0])})
        except Exception:  # noqa: BLE001 - separation etc.: reported as skipped
            out.append({"outcome": outcome, "n": len(df), "skipped": True})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sink", type=Path, default=None)
    a = ap.parse_args(argv)
    enr = pd.read_parquet(a.derived / "raman" / "rule_enrichment.parquet")
    q1, rows = pooled_rules(enr)
    dr = dose_response(a.derived)
    ok = [d for d in dr if not d.get("skipped")]
    q2 = random_effects([d["slope"] for d in ok], [d["se"] for d in ok])
    q2["p_tost"] = tost(q2["effect"], q2["se"], SESOI)
    recs = {}
    for tag, q, k in (("Q1_pooled_rule_logRR", q1, q1["k"]), ("Q2_dose_slope", q2, sum(d["n_case"] for d in ok))):
        res = Result(test_id=f"phase4_2:{tag}", prereg_id=PREREG, engine="raman", statistic="logRR",
                     unit="rule" if tag.startswith("Q1") else "person", effect=q["effect"], se=q["se"],
                     se0=q["se"], sesoi=SESOI, n_cases=int(k), n_clusters=int(k),
                     sham_ok=True, config={"tau2": q["tau2"], "i2": q["i2"], "note": "no sham at this level"})
        recs[tag] = res
        if a.sink:
            emit(res, a.sink)
    L = ["# Phase 4.2 results: Raman rule-level effects", "",
         f"Per `docs/validation/PHASE4_2_RULES_PREREG.md` ({PREREG}). SESOI log 1.20 (RR 1.20).", "",
         "## Q1: pooled effect of the 91 published rule × outcome tests", "",
         "| k | pooled RR | 95% CI | 90% CI | τ² | I² | p_TOST | RR>1 share (sign p) | verdict |",
         "|---|---|---|---|---|---|---|---|---|"]
    e, s = q1["effect"], q1["se"]
    L.append(f"| {q1['k']} | {math.exp(e):.3f} | {math.exp(e-1.96*s):.3f}–{math.exp(e+1.96*s):.3f} "
             f"| {math.exp(e-1.645*s):.3f}–{math.exp(e+1.645*s):.3f} | {q1['tau2']:.4f} | {q1['i2']:.2f} "
             f"| {q1['p_tost']:.4f} | {q1['share_rr_gt_1']:.2f} ({q1['sign_p']:.3f}) | **{recs['Q1_pooled_rule_logRR'].verdict}** |")
    L += ["", "## Q2: dose-response (number of registered-polarity rules fired → outcome)", "",
          "| outcome | n | cases | mean rules fired | slope (log-odds per extra rule) | 95% CI |", "|---|---|---|---|---|---|"]
    for d in dr:
        if d.get("skipped"):
            L.append(f"| {d['outcome']} | {d['n']} | – | – | skipped (fit failed) | |")
        else:
            L.append(f"| {d['outcome']} | {d['n']} | {d['n_case']} | {d['mean_count']:.2f} | {d['slope']:+.3f} "
                     f"| {d['slope']-1.96*d['se']:+.3f}..{d['slope']+1.96*d['se']:+.3f} |")
    e, s = q2["effect"], q2["se"]
    L += ["", f"**Pooled slope:** {e:+.4f} log-odds per extra rule (OR {math.exp(e):.3f} per rule; 95% CI "
          f"{math.exp(e-1.96*s):.3f}–{math.exp(e+1.96*s):.3f}), τ² {q2['tau2']:.4f}, p_TOST {q2['p_tost']:.4f} → "
          f"**{recs['Q2_dose_slope'].verdict}**", "",
          "Deviation (implementation, recorded): the first run used decade dummies in an ordinary logit; 5 of 9 fits "
          "failed by separation (decades with only cases or only contrasts). Decade adjustment is now done by "
          "conditional logistic regression with decade strata, which is the same adjustment without the failure. "
          "The 4 slopes visible in the failed run were childless −0.097, widowed −0.040, bankrupt −0.222, suicide +0.037.", ""]
    a.out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
