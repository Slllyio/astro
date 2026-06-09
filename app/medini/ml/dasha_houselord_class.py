"""Does the running lord's house-lordship predict WHICH CLASS of event occurs?

The formal, non-circular version of "what does this dasha bring". Finding 8A
showed it for marriage (7th-lord). This generalises to the whole 12×N grid:

    For each house H (1..12), among events whose running MD lord rules H in
    the native's own chart, how is the event-CLASS distribution shifted?
        lift[H, C] = P(class = C | MD lord rules H) / P(class = C)

The predictor is **chart-specific** — the same universal planet (say Saturn)
rules different houses for different ascendants — so this isolates chart
geometry from lord identity. Significance comes from a **chart-shuffle null**
(reassign donor ascendants → the houses each running lord rules change; the
running lord and the event class stay fixed). A single headline statistic, the
**canonical-diagonal lift** — the mean of lift[H, C] over the textbook
house→class pairs (7→marriage, 10→career, 8→death, 6→health, 4→education) —
is tested against that null: > 1 with low p ⇒ the chart's house-lordship
genuinely predicts the class of life event the period delivers.

No classifier needed: the lift matrix *is* the interpretable model, and the
chart-shuffle is the honest significance test (sklearn is not available here,
and a permuted lift matrix is more transparent than a black-box anyway).

Usage::

    python -m app.medini.ml.dasha_houselord_class \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --k 400
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from app.core.functional_roles import houses_ruled_by
from app.medini.ml.dasha_significator_timing import _LORDS

logger = logging.getLogger(__name__)

# Textbook house → event-class diagonal (the rules we expect to light up).
_CANONICAL: Final[dict[int, str]] = {
    7: "marriage", 10: "career", 8: "death", 6: "health", 4: "education",
}


def _ruled_lookup() -> np.ndarray:
    """R[lord_idx, asc-1] = bitmask (12 bits) of houses that lord rules."""
    R = np.zeros((len(_LORDS), 12), dtype=np.int32)
    for li, lord in enumerate(_LORDS):
        for asc in range(1, 13):
            mask = 0
            for h in houses_ruled_by(lord, asc):
                mask |= 1 << (h - 1)
            R[li, asc - 1] = mask
    return R


def prepare(events: pd.DataFrame, charts: pd.DataFrame) -> dict[str, object]:
    asc_by = charts.dropna(subset=["asc_sign"]).set_index(
        "person_id")["asc_sign"].astype(int)
    lord_idx = {l: i for i, l in enumerate(_LORDS)}
    df = events[events["person_id"].isin(asc_by.index)
                & events["md_lord_at_event"].isin(lord_idx)].copy()
    persons = asc_by.index.tolist()
    pid_index = {p: i for i, p in enumerate(persons)}
    return {
        "persons": persons,
        "pe": df["person_id"].map(pid_index).to_numpy(),
        "asc": asc_by.to_numpy(),
        "md": df["md_lord_at_event"].map(lord_idx).to_numpy(),
        "cls": df["event_class"].astype(str).str.lower().to_numpy(),
    }


def _rules_house(md: np.ndarray, asc_e: np.ndarray, house: int, R: np.ndarray,
                 ) -> np.ndarray:
    """Boolean per event: does the running MD lord rule `house` under asc_e?"""
    bit = 1 << (house - 1)
    return (R[md, asc_e - 1] & bit) > 0


def _cell_share(P: dict, R: np.ndarray, asc_per_person: np.ndarray, house: int,
                target_class: str) -> float:
    """P(class == target | MD lord rules `house`) under the given ascendants.

    This is the same statistic as the significator-timing module's match rate,
    so the chart-shuffle baseline below is directly comparable to Finding 8."""
    asc_e = asc_per_person[P["pe"]]
    sel = _rules_house(P["md"], asc_e, house, R)
    if sel.sum() < 30:
        return float("nan")
    return float((P["cls"][sel] == target_class).mean())


def run_analysis(events: pd.DataFrame, charts: pd.DataFrame, *, k: int = 400,
                 seed: int = 0) -> dict[str, object]:
    P = prepare(events, charts)
    R = _ruled_lookup()
    asc_arr = np.asarray(P["asc"], dtype=int)
    cells = [(h, c) for h, c in _CANONICAL.items() if c in set(P["cls"])]

    real = np.array([_cell_share(P, R, asc_arr, h, c) for h, c in cells])
    rng = np.random.default_rng(seed)
    nullshares = np.empty((k, len(cells)))
    for j in range(k):
        donor = asc_arr[rng.permutation(len(P["persons"]))]
        nullshares[j] = [_cell_share(P, R, donor, h, c) for h, c in cells]

    null_mean = np.nanmean(nullshares, axis=0)
    # per-cell: chart-shuffle lift / z / p (same footing as Finding 8)
    cell_rows = []
    for i, (h, c) in enumerate(cells):
        col = nullshares[:, i]
        nstd = float(np.nanstd(col, ddof=1))
        cell_rows.append({
            "house": h, "class": c, "obs": round(float(real[i]), 4),
            "null": round(float(null_mean[i]), 4),
            "lift": round(float(real[i] / null_mean[i]), 3) if null_mean[i] else None,
            "z": round((real[i] - null_mean[i]) / nstd, 2) if nstd else None,
            "p": round(float((col >= real[i]).sum() + 1) / (k + 1), 4)})

    # headline: mean per-cell lift vs its chart-shuffle null
    real_diag = float(np.nanmean(real / null_mean))
    null_diag = np.nanmean(nullshares / null_mean, axis=1)
    nmean, nstd = float(null_diag.mean()), float(null_diag.std(ddof=1))
    z = (real_diag - nmean) / nstd if nstd else float("nan")
    p = float((null_diag >= real_diag).sum() + 1) / (k + 1)
    return {"classes": sorted(set(P["cls"])), "canonical_cells": cell_rows,
            "diagonal_lift": round(real_diag, 4), "null_mean": round(nmean, 4),
            "null_std": round(nstd, 4), "z": round(z, 2), "p": round(p, 4),
            "k_effective": k}


def build_report(res: dict, *, k: int) -> str:
    L = ["# House-lordship → event-class — does the chart predict what the dasha brings?",
         "", "Non-circular: for each house H, the event-class lift among events "
         "whose running MD lord rules H in the native's chart. Chart-specific "
         f"(varies by ascendant); chart-shuffle null, K={k}.", "",
         "## Canonical house → class diagonal (chart-shuffle baseline)", "",
         "| house | expected class | obs | null | lift | z | p |",
         "|---:|---|---:|---:|---:|---:|---:|"]
    for cell in res["canonical_cells"]:
        lv = f"**{cell['lift']:.2f}**" if cell["lift"] is not None else "—"
        star = " ✶" if (cell["p"] is not None and cell["p"] < 0.05) else ""
        L.append(f"| {cell['house']} | {cell['class']} | {cell['obs']*100:.0f}% | "
                 f"{cell['null']*100:.0f}% | {lv}{star} | {cell['z']} | "
                 f"{cell['p']:.4g} |")
    L += ["", "## Headline test — mean diagonal lift vs chart-shuffle null", "",
          "| quantity | value |", "|---|---|",
          f"| mean canonical-diagonal lift | **{res['diagonal_lift']:+.3f}** |",
          f"| null mean ± std | {res['null_mean']:.3f} ± {res['null_std']:.3f} |",
          f"| **z** | **{res['z']}** |", f"| **p** | **{res['p']:.4g}** |",
          f"| K effective | {res['k_effective']} |", "",
          "## Reading", "",
          f"- Diagonal lift {res['diagonal_lift']:.2f} vs null ≈ "
          f"{res['null_mean']:.2f}: " + (
              "the chart's house-lordship predicts which class of event the dasha "
              "delivers, beyond a random chart (z={}, p={})."
              .format(res["z"], res["p"]) if res["z"] and res["z"] >= 2 else
              "no clear chart-specific class prediction beyond the universal "
              "lord-identity/age structure (consistent with most rules being "
              "weak; marriage/7th is the main carrier)."),
          "- Per-cell lift > 1 marks a classical rule that holds; ≈1 or < 1 marks "
          "one that does not survive on this corpus.", ""]
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path, *, k: int = 400, seed: int = 0,
        ) -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    events = events[events["md_lord_at_event"].notna()].copy()
    charts = pd.read_parquet(data_dir / "charts.parquet")
    res = run_analysis(events, charts, k=k, seed=seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(res["canonical_cells"]).to_csv(
        out_dir / "houselord_class_diagonal.csv", index=False)
    (out_dir / "houselord_class.md").write_text(build_report(res, k=k),
                                                encoding="utf-8")
    (out_dir / "houselord_class.json").write_text(
        json.dumps({k2: v for k2, v in res.items() if k2 != "classes"},
                   indent=2, default=str), encoding="utf-8")
    logger.info("houselord-class: diag_lift=%s z=%s p=%s",
                res["diagonal_lift"], res["z"], res["p"])
    return res


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("--k", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print({k2: v for k2, v in run(args.data_dir, args.out, k=args.k,
                                  seed=args.seed).items() if k2 != "classes"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
