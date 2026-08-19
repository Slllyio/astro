"""Run-5 fidelity harness — calibration/held-out evaluation on the registry.

Per case: build the bundle from Raman's printed positions
(``golden_registry``), the Vimshottari MD/AD windows over the lived span from
the printed Moon, and score each window's fatal potency with
``PotencyModelV2``. Metrics per half:

- per-case death-window percentile (0 = most potent lived window),
- median percentile + fraction below 0.50 (the HG1/HG2 statistics),
- killer hit-rate: fraction of Raman-named killers inside the encoder's
  top-4 maraka scores (HG3),
- band hit-rate on cases with an explicit longevity statement.

Transit terms are applied at window midpoints from the Raman-frame Saturn
ingress table when ``use_transits`` is on (the calibration-half inclusion
rule decides whether the frozen weights carry them).

The held-out half must NOT be evaluated before the RUN5 freeze — the CLI
refuses ``--half held_out`` unless ``--allow-heldout`` is passed (set by the
post-freeze step F).
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import swisseph as swe

from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab.golden_registry import (
    GoldenCaseV2, bundle_for, split, validate_all,
)
from app.medini.ml.raman_saab.raman_method_v2 import (
    LORD_IDX, RAMAN_WEIGHTS_V2, AyuBand, PotencyModelV2, load_weights,
    maraka_scores_v2, transit_multiplier_v2,
)
from app.medini.ml.raman_saab.transit_table import get_table

logger = logging.getLogger(__name__)

_TOP_KILLER_K = 4


@dataclass
class CaseEval:
    key: str
    pctile: float | None = None
    death_window: str = ""
    n_windows: int = 0
    killers_named: int = 0
    killers_hit: int = 0
    band_pred: str | None = None
    band_stated: str | None = None
    ad_anchor_ok: bool | None = None
    notes: list = field(default_factory=list)


def _windows(bundle, death_jd: float):
    birth_jd = bundle.kundali.birth_jd
    rows = []
    death_row = None
    for md in D.md_intervals(bundle.kundali.moon_longitude, birth_jd):
        for ad in D.ad_intervals_in_md(md):
            if ad.end_jd <= birth_jd or ad.start_jd > death_jd:
                continue
            mid = (max(ad.start_jd, birth_jd) + min(ad.end_jd, death_jd)) / 2
            frac = (mid - md.start_jd) / (md.end_jd - md.start_jd)
            row = (md.lord, ad.lord,
                   (mid - birth_jd) / D.DAYS_PER_VEDIC_YEAR, frac, mid)
            rows.append(row)
            if ad.start_jd <= death_jd < ad.end_jd:
                death_row = row
    return rows, death_row


def evaluate_case(case: GoldenCaseV2, w: dict, *,
                  use_transits: bool = False) -> CaseEval:
    ev = CaseEval(key=case.key, ad_anchor_ok=case.ad_anchor_ok)
    bundle = bundle_for(case)
    pm = PotencyModelV2.from_bundle(bundle, w)
    ev.band_pred = pm.band.name
    ev.band_stated = case.stated_band

    wins, dw = _windows(bundle, case.death_jd)
    if dw is not None and len(wins) >= 10:
        md_idx = np.array([LORD_IDX[r[0]] for r in wins])
        ad_idx = np.array([LORD_IDX[r[1]] for r in wins])
        ages = np.array([r[2] for r in wins])
        fracs = np.array([r[3] for r in wins])
        tmult = None
        if use_transits:
            mids = np.array([r[4] for r in wins])
            sat = get_table("Saturn", sid_mode=swe.SIDM_RAMAN)
            tmult = transit_multiplier_v2(pm, bundle.kundali.birth_jd,
                                          mids, sat, w)
        pots = pm.potency(md_idx, ad_idx, ages, md_frac=fracs,
                          transit_mult=tmult, w=w)
        i = wins.index(dw)
        ev.pctile = float((pots > pots[i]).sum()) / len(wins)
        ev.death_window = f"{dw[0]}/{dw[1]}@{dw[2]:.0f}"
        ev.n_windows = len(wins)
    else:
        ev.notes.append("no death window resolvable")

    if case.named_killers:
        mk = maraka_scores_v2(bundle, w)
        top = set(sorted(mk, key=mk.get, reverse=True)[:_TOP_KILLER_K])
        ev.killers_named = len(case.named_killers)
        ev.killers_hit = sum(1 for g in case.named_killers if g in top)
    return ev


def evaluate_half(cases: list[GoldenCaseV2], w: dict, *,
                  use_transits: bool = False) -> dict:
    evs = [evaluate_case(c, w, use_transits=use_transits) for c in cases]
    pcts = [e.pctile for e in evs if e.pctile is not None]
    named = sum(e.killers_named for e in evs)
    hit = sum(e.killers_hit for e in evs)
    band_cases = [e for e in evs if e.band_stated]
    return {
        "n_cases": len(cases),
        "n_timed": len(pcts),
        "median_pctile": statistics.median(pcts) if pcts else None,
        "mean_pctile": statistics.fmean(pcts) if pcts else None,
        "frac_below_50": (sum(p < 0.5 for p in pcts) / len(pcts)) if pcts else None,
        "killer_hit_rate": (hit / named) if named else None,
        "band_hit_rate": (sum(e.band_pred == e.band_stated for e in band_cases)
                          / len(band_cases)) if band_cases else None,
        "use_transits": use_transits,
        "cases": [{
            "key": e.key, "pctile": e.pctile, "death_window": e.death_window,
            "n_windows": e.n_windows,
            "killers": f"{e.killers_hit}/{e.killers_named}",
            "band": f"{e.band_pred} vs {e.band_stated or '—'}",
            "ad_anchor_ok": e.ad_anchor_ok, "notes": e.notes,
        } for e in evs],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--half", choices=["calibration", "held_out"],
                   default="calibration")
    p.add_argument("--weights", type=Path, default=None,
                   help="calibrated run5_weights.json (default: v2 defaults)")
    p.add_argument("--transits", action="store_true")
    p.add_argument("--allow-heldout", action="store_true",
                   help="required to score the held-out half (post-freeze F)")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.half == "held_out" and not args.allow_heldout:
        raise SystemExit("REFUSED: held-out half is scored only after the "
                         "RUN5 freeze (pass --allow-heldout in step F).")

    calib, held = split(validate_all())
    cases = calib if args.half == "calibration" else held
    w = load_weights(args.weights)
    res = evaluate_half(cases, w, use_transits=args.transits)
    res["half"] = args.half
    res["weights_file"] = str(args.weights) if args.weights else "defaults"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "cases"}, indent=1))
    for c in res["cases"]:
        pct = "—" if c["pctile"] is None else f"{c['pctile']:.2f}"
        print(f"  {c['key']:<20} pct={pct:<6} win={c['death_window']:<22} "
              f"killers={c['killers']} band={c['band']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
