"""Does natal chart strength predict the AGE of a life event?

A continuous, fully non-circular target — the opposite end from the valence
work. Two classical claims, each falsifiable on real ADB dates:

  * **Longevity (Ayurdaya).** Does a stronger lagna + 8th house go with a
    later age at death? Target = age at death (n≈2.7k real death records).
  * **Marriage age.** Does a stronger / less-afflicted 7th house go with an
    earlier marriage? Target = age at marriage (n≈1.75k).

Chart strength reuses `bhava_promise` (house-lord + karaka + occupancy +
aspect) from `dasha_event_promise`. Each native contributes one row per target
(first event of that class), so this is a clean cross-person regression of age
on chart strength.

Test: Spearman rank correlation of the chart index vs age, with a
**chart-shuffle permutation** (shuffle the index across people, recompute the
correlation) for significance — plus strong-vs-weak mean-age split. Because the
target is age (independent of `event_class` labelling), a real correlation here
is a real astrological signal and a null is a real null.

Caveats: ADB death records are a notable-person, died-already sample
(survivorship / selection); read longevity within that frame.

Usage::

    python -m app.medini.ml.dasha_event_age \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --k 2000
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from app.medini.ml.dasha_event_promise import _chart_dicts, bhava_promise

logger = logging.getLogger(__name__)

# (target name, event_class, bhavas summed for the chart index, expected sign).
_TARGETS: Final[tuple[tuple[str, str, tuple[int, ...], str], ...]] = (
    ("longevity", "death", (1, 8), "higher strength → later death (ρ>0)"),
    ("marriage_age", "marriage", (7,), "higher 7th strength → earlier marriage (ρ<0)"),
)


def chart_index(crow: pd.Series, bhavas: tuple[int, ...]) -> float | None:
    asc = crow.get("asc_sign")
    if pd.isna(asc):
        return None
    houses, signs = _chart_dicts(crow)
    return float(sum(
        bhava_promise(crow, b, asc=int(asc), houses=houses, signs=signs)["promise_score"]
        for b in bhavas))


def _frame(events: pd.DataFrame, charts: pd.DataFrame, event_class: str,
           bhavas: tuple[int, ...]) -> pd.DataFrame:
    """One row per native: chart index + age at the first such event."""
    ev = events[(events["event_class"].astype(str).str.lower() == event_class)
                & events["age_at_event_years"].notna()].copy()
    order = "event_jd" if "event_jd" in ev.columns else "age_at_event_years"
    ev = ev.sort_values(order).groupby("person_id").head(1)
    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    rows = []
    for _, e in ev.iterrows():
        pid = e["person_id"]
        if pid not in cidx.index:
            continue
        idx = chart_index(cidx.loc[pid], bhavas)
        if idx is None:
            continue
        rows.append({"person_id": pid, "index": idx,
                     "age": float(e["age_at_event_years"])})
    return pd.DataFrame(rows)


def correlate(frame: pd.DataFrame, *, k: int = 2000, seed: int = 0,
              ) -> dict[str, object]:
    if len(frame) < 50:
        return {"n": len(frame), "rho": None}
    idx = frame["index"].to_numpy()
    age = frame["age"].to_numpy()
    rho = float(spearmanr(idx, age).statistic)
    rng = np.random.default_rng(seed)
    null = np.array([spearmanr(rng.permutation(idx), age).statistic
                     for _ in range(k)])
    nstd = float(null.std(ddof=1))
    z = rho / nstd if nstd > 0 else float("nan")
    p_two = float((np.abs(null) >= abs(rho)).sum() + 1) / (k + 1)
    med = np.median(idx)
    strong = frame[frame["index"] >= med]["age"]
    weak = frame[frame["index"] < med]["age"]
    return {
        "n": len(frame), "rho": round(rho, 4),
        "z": round(z, 2), "p_two_sided": round(p_two, 4),
        "mean_age_strong": round(float(strong.mean()), 2),
        "mean_age_weak": round(float(weak.mean()), 2),
        "age_gap": round(float(strong.mean() - weak.mean()), 2),
    }


def build_report(results: dict[str, dict], *, k: int) -> str:
    L = ["# Does chart strength predict the AGE of an event?", "",
         "Continuous, non-circular target. Chart index = summed `bhava_promise` "
         "of the relevant houses. Spearman ρ vs age with a chart-shuffle "
         f"permutation (K={k}); strong/weak split at the index median.", "",
         "| target | class | n | ρ(index,age) | z | p | mean age strong | "
         "mean age weak | gap | expectation |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for name, cls, _, expect in _TARGETS:
        r = results.get(name, {})
        if r.get("rho") is None:
            L.append(f"| {name} | {cls} | {r.get('n', 0)} | — | — | — | — | — | — "
                     f"| {expect} |")
            continue
        star = " ✶" if r["p_two_sided"] < 0.05 else ""
        L.append(f"| {name} | {cls} | {r['n']} | **{r['rho']:+.3f}**{star} | "
                 f"{r['z']} | {r['p_two_sided']:.4g} | {r['mean_age_strong']} | "
                 f"{r['mean_age_weak']} | {r['age_gap']:+.2f} | {expect} |")
    L += ["", "## Reading", "",
          "- ρ significantly ≠ 0 ⇒ the chart's domain strength tracks *when* the "
          "event happens — a real, non-circular astrological signal.",
          "- ρ ≈ 0 (within a tight permutation band) ⇒ a real null: this chart "
          "index does not time the event's age on this corpus.",
          "- Longevity uses a died-already, notable-person sample — interpret "
          "within that selection.", ""]
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path, *, k: int = 2000, seed: int = 0,
        ) -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    results, frames = {}, []
    for name, cls, bhavas, _ in _TARGETS:
        fr = _frame(events, charts, cls, bhavas)
        results[name] = correlate(fr, k=k, seed=seed)
        fr.insert(0, "target", name)
        frames.append(fr)
    out_dir.mkdir(parents=True, exist_ok=True)
    if frames:
        pd.concat(frames, ignore_index=True).to_csv(
            out_dir / "event_age_data.csv", index=False)
    (out_dir / "event_age.md").write_text(
        build_report(results, k=k), encoding="utf-8")
    logger.info("event-age results: %s", results)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("--k", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.data_dir, args.out, k=args.k, seed=args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
