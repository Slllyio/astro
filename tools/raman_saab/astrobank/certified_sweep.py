"""Certified Cohort — full matched-pair sweep across every certified domain (pre-registered).

Runs the matched-discordant-pair engine (certified_matched_pairs.analyze_domain) over every
outcome domain that has a tier-A (birth-certificate + minute) cohort, so we have the complete
matched-pair picture on the certificate-grade slice before any fresh collection begins. Directions,
house mappings, and sham (off-target H10/career) are frozen here BEFORE the sweep runs — this file
IS the pre-registration.

Two design flavours (both are valid discordant-pair case-control designs):
  * LABELLED CONTRAST — case cohort vs a labelled opposite (childless vs prolific, short vs long
    life, widowed vs long-married, divorced vs long-married). Cleanest.
  * POOLED CONTROL — case vs every certified non-case person (prison, suicide, accident): no
    labelled opposite exists, so "without the outcome" = the certified pool. Weaker (leans on the
    off-target sham + specificity), flagged as such.

BH q=0.10 is applied across the interpretable primary tests. Nothing tunes the engine. REPORT-ONLY.

Usage:
    py -3.12 -m tools.raman_saab.astrobank.certified_sweep
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from tools.raman_saab.astrobank._stats import bh_fdr
from tools.raman_saab.astrobank.certified_matched_pairs import _STORE, analyze_domain

logger = logging.getLogger(__name__)

_OUT = _STORE / "certified_sweep_results.json"
_SHAM = (10, "career")   # universal off-target: unrelated to any domain below

# (label, case_map, control_map|None, house, signification, direction, exclude-from-pool)
_DOMAINS: list[tuple] = [
    ("H5_children",  "H5_CHILDLESS", "H5_PROLIFIC",     5, "children",          "afflicted", ()),
    ("H7_divorce",   "H7_DIVORCED",  "H7_LONGMARRIAGE", 7, "marital_happiness", "afflicted", ()),
    ("H7_widow",     "H7_WIDOWED",   "H7_LONGMARRIAGE", 7, "spouse",            "afflicted", ()),
    ("H8_longevity", "H8_SHORTLIFE", "H8_LONGLIFE",     8, "longevity",         "afflicted", ()),
    ("H2_wealth",    "H2_BANKRUPT",  "H2_WEALTHY",      2, "wealth",            "afflicted", ()),
    ("H12_prison",   "H12_PRISON",   None,             12, "incarceration",     "afflicted",
     ("H12_PRISON",)),
    ("H8_suicide",   "H8_SUICIDE",   None,              8, "death",             "afflicted",
     ("H8_SUICIDE", "H8_ACCIDENT")),
    ("H8_accident",  "H8_ACCIDENT",  None,              8, "death",             "afflicted",
     ("H8_SUICIDE", "H8_ACCIDENT")),
]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    master = pd.read_parquet(_STORE / "person_master.parquet").set_index("person_id")
    labels = pd.read_parquet(_STORE / "labels.parquet")
    verdicts = pd.read_parquet(_STORE / "verdicts.parquet")

    rows = []
    for label, case, ctrl, house, sig, direction, excl in _DOMAINS:
        res = analyze_domain(master, labels, verdicts, case, ctrl, house, sig, direction,
                             _SHAM[0], _SHAM[1], exclude=frozenset(excl))
        res["label"] = label
        res["design"] = "labelled_contrast" if ctrl else "pooled_control"
        rows.append(res)
        p = res["primary"]
        logger.info("%-13s pairs=%-4d AUC=%.3f CI%s p=%s sham=%.3f[%s] -> %s",
                    label, p["n_pairs"], p["paired_auc"], p["ci95"], p["signed_rank_p"],
                    res["sham_gate"]["paired_auc"],
                    "gate ok" if res["sham_gate"]["null_gate_open"] else "GATE FAIL",
                    res["verdict"].split(":")[0])

    # BH across the interpretable (sufficient-N) primary tests
    interp = [r for r in rows if not r["insufficient_n"] and r["primary"]["signed_rank_p"] is not None]
    passed = bh_fdr({r["label"]: r["primary"]["signed_rank_p"] for r in interp}, q=0.10)
    for r in interp:
        r["bh_reject_null"] = bool(passed[r["label"]])

    n_signal = sum(r.get("bh_reject_null", False) for r in interp)
    tail = ("the convergent null holds on the certified slice under the matched-pair design."
            if n_signal == 0 else "INVESTIGATE the surviving domain(s).")
    summary = {
        "experiment": "Certified Cohort - full matched-pair sweep (tier-A certified slice)",
        "design_doc": "docs/raman_saab/CERTIFIED_COHORT_DESIGN.md",
        "sham": {"house": _SHAM[0], "signification": _SHAM[1]},
        "n_domains": len(rows), "n_interpretable": len(interp),
        "n_signal_after_bh": n_signal,
        "headline": (f"{n_signal} of {len(interp)} interpretable certified domains show signal "
                     f"after BH q=0.10 - {tail}"),
        "domains": rows,
    }
    _OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("wrote %s", _OUT)

    print(f"\n{'domain':14}{'design':18}{'pairs':>6}{'AUC':>7}{'CI':>18}{'p':>7}{'sham':>7}  verdict")
    for r in rows:
        p = r["primary"]
        ci = f"({p['ci95'][0]:.3f},{p['ci95'][1]:.3f})"
        pv = f"{p['signed_rank_p']}" if p["signed_rank_p"] is not None else "  -"
        print(f"{r['label']:14}{r['design']:18}{p['n_pairs']:>6}{p['paired_auc']:>7.3f}"
              f"{ci:>18}{pv:>7}{r['sham_gate']['paired_auc']:>7.3f}  {r['verdict'].split(':')[0]}")
    print(f"\n{summary['headline']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
