"""Layer A + B timing metrics — the surviving strength effect in practitioner terms.

The deep-research synthesis (`evaluation_methodology.md`) showed our `lift` is an
unbranded self-controlled rate ratio and that two upgrades are nearly free while
being far more interpretable and aligned with how astrologers actually predict:

  LAYER A — effect size as a SELF-CONTROLLED INCIDENCE-RATE RATIO (+ 95% CI).
  Fit the single-exposure Self-Controlled Case Series / conditional-Poisson model
  (Farrington 1995; Whitaker 2006). For each native (a case, with one first event)
  the event falls in the rule's *exposed* person-time with probability
  p = e·e^β / (e·e^β + u), where e,u = exposed/unexposed in-band duration. The
  conditional MLE of β gives IRR = e^β — the multiplicative change in event rate
  during the rule's periods, each native its own control — with a proper CI from
  the observed information. This replaces "lift ~1.1 (p=…)" with
  "rate ratio 1.x (95% CI …)", the estimand epidemiology uses for exactly this
  question, and the number a practitioner reads as "events 1.x× more frequent."

  LAYER B — DISCRIMINATION: does the rule rank the true period high?
  Score every in-band period by a graded 0–4 weight-of-evidence for the strength
  rule (benefic AD · well-dignified · kendra/trikona from Lagna · benefic from the
  dasha lord). Report the within-person, duration-weighted C-index / AUC
  (= P(true period scored above a random non-event period); 0.5 = no skill), and
  top-1 / top-3 hit-rate ("is the true period the astrologer's #1 / top-3 pick?").
  Baselines come from the same within-person permutation null (event ∝ duration),
  so a long period cannot win by mere length.

Both keep the self-controlled design; Layer B's graded score is also the bridge to
a full forecast-skill (calibration) layer.

Usage::

    python -m app.medini.ml.dasha_timing_metrics --data-dir /tmp/la_run \\
        --out data/ml_runs/lunarastro_dignity --k 5000
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

from app.medini.ml.dasha_strength_confirm import (
    _facts, _pos_benefic, _KENDRA_TRIKONA, _first_events, _half,
)
from app.medini.ml.dasha_verse_timing import DOMAINS, _BENEFICS

logger = logging.getLogger(__name__)


def _graded(md: str, ad: str, f: dict) -> int:
    """0–4 weight-of-evidence for the benefic-AD strength rule (the graded form
    of the frozen Finding-15 spec S4)."""
    return (int(ad in _BENEFICS) + int(ad in f["good"])
            + int(f["houses"].get(ad) in _KENDRA_TRIKONA)
            + int(_pos_benefic(md, ad, f)))


def collect(windows, charts, d9, events, domain: str, *, half: str | None):
    """Per native with a first event of `domain` in its age band: duration,
    graded 0–4 score and binary-strength flag for every in-band window, and the
    index of the event's own window."""
    auspicious, (lo, hi) = DOMAINS[domain]
    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    d9idx = d9.drop_duplicates("person_id").set_index("person_id") if d9 is not None else None
    birth = cidx["birth_jd_used"]
    win_by = {pid: g for pid, g in windows.groupby("person_id")}
    evf = _first_events(events, domain)
    recs = []
    for pid in evf.index:
        if half is not None and _half(pid) != half:
            continue
        if pid not in cidx.index or pid not in win_by or pd.isna(birth.get(pid)):
            continue
        wg = win_by[pid]
        b = float(birth[pid])
        mid = (((wg["start_jd"] + wg["end_jd"]) / 2) - b) / 365.25
        band = wg[(mid >= lo) & (mid <= hi)].reset_index(drop=True)
        if band.empty or band["duration_days"].sum() <= 0:
            continue
        es = (int(evf.loc[pid, "md_seq"]), int(evf.loc[pid, "ad_seq"]))
        ix = band.index[(band["md_seq"] == es[0]) & (band["ad_seq"] == es[1])]
        if len(ix) == 0:
            continue
        f = _facts(cidx.loc[pid],
                   d9idx.loc[pid] if (d9idx is not None and pid in d9idx.index) else None,
                   domain)
        md = band["md_lord"].astype(str).to_numpy()
        ad = band["ad_lord"].astype(str).to_numpy()
        graded = np.array([_graded(md[i], ad[i], f) for i in range(len(md))])
        recs.append({"dur": band["duration_days"].to_numpy(float),
                     "graded": graded, "binary": graded == 4,
                     "ev_idx": int(ix[0])})
    return recs


# ── Layer A: SCCS / conditional-Poisson incidence-rate ratio ────────────────
def sccs_irr(recs) -> dict:
    """Single-exposure SCCS conditional-Poisson MLE (one event per native)."""
    x = np.array([r["binary"][r["ev_idx"]] for r in recs], float)
    e = np.array([r["dur"][r["binary"]].sum() for r in recs], float)
    u = np.array([r["dur"][~r["binary"]].sum() for r in recs], float)
    m = (e > 0) & (u > 0)                       # informative natives only
    x, e, u = x[m], e[m], u[m]
    n = len(x)
    if n == 0:
        return {}
    lift = float(x.sum() / (e / (e + u)).sum())  # our old statistic, same set
    Sx = x.sum()
    if Sx == 0 or Sx == n:                       # boundary: IRR 0 or ∞
        return {"n_informative": n, "n_exposed_events": int(Sx),
                "irr": 0.0 if Sx == 0 else float("inf"),
                "ci_lo": None, "ci_hi": None, "z": None, "p": None, "lift": round(lift, 3)}
    r = e / u

    def p(beta):
        ex = r * np.exp(beta)
        return ex / (ex + 1.0)

    beta = brentq(lambda b: Sx - p(b).sum(), -15.0, 15.0)
    pe = p(beta)
    info = float((pe * (1 - pe)).sum())
    se = 1.0 / np.sqrt(info)
    z = beta / se
    return {"n_informative": n, "n_exposed_events": int(Sx),
            "irr": round(float(np.exp(beta)), 3),
            "ci_lo": round(float(np.exp(beta - 1.96 * se)), 3),
            "ci_hi": round(float(np.exp(beta + 1.96 * se)), 3),
            "z": round(float(z), 2), "p": round(float(2 * norm.sf(abs(z))), 4),
            "lift": round(lift, 3)}


# ── Layer B: within-person discrimination on the graded score ───────────────
def _auc_i(dur, graded, ev) -> float | None:
    s_ev = graded[ev]
    mask = np.ones(len(dur), bool)
    mask[ev] = False
    d, g = dur[mask], graded[mask]
    tot = d.sum()
    if tot <= 0:
        return None
    conc = d[g < s_ev].sum()
    tie = d[g == s_ev].sum()
    return float((conc + 0.5 * tie) / tot)


def _hit_at_k(graded, ev, k) -> bool:
    return int((graded > graded[ev]).sum()) < k      # optimistic ties


def discrimination(recs, *, k=5000, seed=0) -> dict:
    aucs = [(_auc_i(r["dur"], r["graded"], r["ev_idx"])) for r in recs]
    aucs = [a for a in aucs if a is not None]
    h1 = [int(_hit_at_k(r["graded"], r["ev_idx"], 1)) for r in recs]
    h3 = [int(_hit_at_k(r["graded"], r["ev_idx"], 3)) for r in recs]
    if not aucs:
        return {}
    # Precompute, per native, the AUC / hit@k value for *every* candidate window
    # position, plus the duration-weights. The permutation then just draws K
    # positions ∝ duration and reads precomputed values — no inner recompute.
    rng = np.random.default_rng(seed)
    null_c = np.zeros(k)
    null_h1 = np.zeros(k)
    null_h3 = np.zeros(k)
    cn = np.zeros(k)
    for r in recs:
        n = len(r["dur"])
        w = r["dur"] / r["dur"].sum()
        auc_pos = np.array([_auc_i(r["dur"], r["graded"], p) for p in range(n)],
                           dtype=float)            # may contain None→nan for n==1
        h1_pos = np.array([_hit_at_k(r["graded"], p, 1) for p in range(n)], float)
        h3_pos = np.array([_hit_at_k(r["graded"], p, 3) for p in range(n)], float)
        picks = rng.choice(n, size=k, p=w)
        a = auc_pos[picks]
        valid = ~np.isnan(a)
        null_c += np.where(valid, np.nan_to_num(a), 0.0)
        cn += valid
        null_h1 += h1_pos[picks]
        null_h3 += h3_pos[picks]
    null_c = null_c / np.where(cn > 0, cn, 1)
    null_h1 /= len(recs)
    null_h3 /= len(recs)
    c = float(np.mean(aucs))
    o1, o3 = float(np.mean(h1)), float(np.mean(h3))
    return {"n": len(recs),
            "c_index": round(c, 4),
            "c_index_null": round(float(null_c.mean()), 4),
            "c_index_p": round(float((np.abs(null_c - 0.5) >= abs(c - 0.5)).sum() + 1) / (k + 1), 4),
            "hit_at_1": round(o1, 4), "hit_at_1_expected": round(float(null_h1.mean()), 4),
            "hit_at_1_p": round(float((null_h1 >= o1).sum() + 1) / (k + 1), 4),
            "hit_at_3": round(o3, 4), "hit_at_3_expected": round(float(null_h3.mean()), 4),
            "hit_at_3_p": round(float((null_h3 >= o3).sum() + 1) / (k + 1), 4)}


def run(data_dir: Path, out_dir: Path, *, k: int = 5000, seed: int = 0) -> dict:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    windows = pd.read_parquet(data_dir / "dasha_windows.parquet")
    d9 = pd.read_parquet(data_dir / "charts_d9.parquet") \
        if (data_dir / "charts_d9.parquet").exists() else None

    per_domain, pooled_aus = {}, []
    for dom in DOMAINS:
        recs = collect(windows, charts, d9, events, dom, half=None)
        per_domain[dom] = {"irr": sccs_irr(recs),
                           "discrimination": discrimination(recs, k=k, seed=seed)}
        if DOMAINS[dom][0]:
            pooled_aus += recs
        logger.info("%s: IRR=%s discrim C=%s", dom,
                    per_domain[dom]["irr"].get("irr"),
                    per_domain[dom]["discrimination"].get("c_index"))
    pooled = {"irr": sccs_irr(pooled_aus),
              "discrimination": discrimination(pooled_aus, k=k, seed=seed)}
    results = {"frozen_rule": "benefic-AD strength (graded 0–4; binary = all four)",
               "pooled_auspicious": pooled, "per_domain": per_domain, "k_perm": k}

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "timing_metrics.json").write_text(json.dumps(results, indent=2),
                                                 encoding="utf-8")
    (out_dir / "timing_metrics.md").write_text(_report(results), encoding="utf-8")
    return results


def _report(r: dict) -> str:
    def irr_str(d):
        if not d or d.get("irr") is None:
            return "—"
        if d.get("ci_lo") is None:
            return f"{d['irr']}"
        return f"{d['irr']} (95% CI {d['ci_lo']}–{d['ci_hi']}, p={d['p']:.3g})"

    L = ["# Timing metrics — the benefic-AD strength effect in practitioner terms",
         "",
         "The surviving signal (Finding 15) reported as a **self-controlled "
         "incidence-rate ratio** (Layer A, SCCS / conditional-Poisson) and as "
         "**within-person discrimination** on a graded 0–4 weight-of-evidence "
         "(Layer B: C-index/AUC and top-k). Each native is its own control; "
         f"permutation K={r['k_perm']}.", "",
         "## Layer A — incidence-rate ratio (SCCS), vs the old lift", "",
         "| group | n (informative) | exposed events | **IRR (95% CI)** | old lift |",
         "|---|---:|---:|---|---:|"]
    pa = r["pooled_auspicious"]["irr"]
    L.append(f"| **auspicious pooled** | {pa.get('n_informative')} | "
             f"{pa.get('n_exposed_events')} | **{irr_str(pa)}** | {pa.get('lift')} |")
    for dom, d in r["per_domain"].items():
        di = d["irr"]
        L.append(f"| {dom} | {di.get('n_informative')} | {di.get('n_exposed_events')} "
                 f"| {irr_str(di)} | {di.get('lift')} |")
    L += ["", "## Layer B — discrimination (graded 0–4 strength score)", "",
          "| group | n | **C-index** (null 0.5) | p | hit@1 (exp) | hit@3 (exp) |",
          "|---|---:|---:|---:|---:|---:|"]
    pd_ = r["pooled_auspicious"]["discrimination"]
    L.append(f"| **auspicious pooled** | {pd_.get('n')} | **{pd_.get('c_index')}** | "
             f"{pd_.get('c_index_p'):.3g} | {pd_.get('hit_at_1')} ({pd_.get('hit_at_1_expected')}) "
             f"| {pd_.get('hit_at_3')} ({pd_.get('hit_at_3_expected')}) |")
    for dom, d in r["per_domain"].items():
        dd = d["discrimination"]
        if not dd:
            continue
        L.append(f"| {dom} | {dd.get('n')} | {dd.get('c_index')} | {dd.get('c_index_p'):.3g} "
                 f"| {dd.get('hit_at_1')} ({dd.get('hit_at_1_expected')}) "
                 f"| {dd.get('hit_at_3')} ({dd.get('hit_at_3_expected')}) |")
    L += ["", "## Reading", "",
          "- **Layer A** restates the effect as a rate ratio with a confidence "
          "interval — the estimand epidemiology uses for self-controlled timing "
          "(SCCS). A CI that includes 1.0 means the effect is not resolved; the "
          "point estimate is the practitioner-legible 'events N× more frequent'.",
          "- **Layer B** asks the astrologer's question directly: does the rule "
          "**rank** the true period high? C-index 0.5 = no discrimination; "
          "hit@k vs its duration-aware expectation says whether the true period "
          "lands in the rule's top-k more than chance.", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=Path("/tmp/la_run"))
    ap.add_argument("--out", type=Path, default=Path("data/ml_runs/lunarastro_dignity"))
    ap.add_argument("--k", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")
    res = run(args.data_dir, args.out, k=args.k, seed=args.seed)
    pa = res["pooled_auspicious"]
    print("pooled auspicious:", pa["irr"], pa["discrimination"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
