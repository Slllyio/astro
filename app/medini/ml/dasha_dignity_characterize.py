"""Characterize the dignity → benefit gradient — turn the scalar into doctrine.

The permutation control established that a chart-strong MD+AD pair skews
prime-life events beneficial (+0.21, p=0.002). This module dissects *how*:

  1. **Dignity ladder** — benefit rate by the MD lord's raw dignity state
     (exalted → own → friendly → neutral → inimical → debilitated). Is the
     relationship monotonic, and is it the strong side lifting or the weak
     side dragging?

  2. **Within-lord contrast** — the cleanest control. For a *fixed* planet
     (Jupiter is Jupiter), do its dasha events skew more beneficial when it
     is well-dignified vs ill-dignified in the native's chart? This removes
     the lord-identity confound entirely: any gradient here is dignity, not
     "which planet is running". Shows which planets carry the effect.

  3. **Strong/weak side decomposition** — how much of the composite
     gradient is strong>base vs base>weak.

  4. **MD vs AD vs pair** — which sub-period level drives it.

All within the prime life stage by default (where the permutation signal
lives) and net of that stage's base benefit rate. Descriptive — the
permutation module is what licenses causal-ish language; this is the
anatomy.

Usage::

    python -m app.medini.ml.dasha_dignity_characterize \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --stage prime
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd
from scipy.stats import binomtest, fisher_exact

from app.core.dignity import dignity_state
from app.medini.ml.dasha_lifestage_dignity import event_valence, life_stage

logger = logging.getLogger(__name__)

_LORDS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
# dignity_state ladder, best → worst.
_DIGNITY_ORDER: Final[tuple[str, ...]] = (
    "exalted", "own", "friendly", "neutral", "inimical", "debilitated",
)
_WELL: Final[frozenset[str]] = frozenset({"exalted", "own", "friendly"})
_ILL: Final[frozenset[str]] = frozenset({"inimical", "debilitated"})


def _safe_dignity(lord: str, sign: object) -> str:
    """dignity_state, tolerant of nodes/missing signs → 'unknown'."""
    if sign is None or pd.isna(sign):
        return "unknown"
    try:
        return dignity_state(lord, int(sign))
    except (KeyError, ValueError):
        return "unknown"  # Rahu/Ketu have no rulership-based dignity here


def annotate(events: pd.DataFrame, charts: pd.DataFrame) -> pd.DataFrame:
    """Attach md_dignity / ad_dignity states, life_stage, valence, benefit."""
    df = events.copy()
    cidx = charts.set_index("person_id")
    md_dig, ad_dig = [], []
    for pid, ml, al in zip(df["person_id"], df["md_lord_at_event"],
                           df.get("ad_lord_at_event", pd.Series([None] * len(df)))):
        if pid not in cidx.index:
            md_dig.append("unknown"); ad_dig.append("unknown"); continue
        crow = cidx.loc[pid]
        if isinstance(crow, pd.DataFrame):
            crow = crow.iloc[0]
        md_dig.append(_safe_dignity(str(ml), crow.get(f"{str(ml).lower()}_sign"))
                      if pd.notna(ml) else "unknown")
        ad_dig.append(_safe_dignity(str(al), crow.get(f"{str(al).lower()}_sign"))
                      if pd.notna(al) else "unknown")
    df["md_dignity"] = md_dig
    df["ad_dignity"] = ad_dig
    df["life_stage"] = df["age_at_event_years"].map(life_stage)
    sub = df["event_subtype"] if "event_subtype" in df.columns else pd.Series(
        [None] * len(df), index=df.index)
    df["valence"] = [event_valence(c, s) for c, s in zip(df["event_class"], sub)]
    return df


def _subset(annotated: pd.DataFrame, stage: str | None) -> pd.DataFrame:
    a = annotated[annotated["valence"] != 0].copy()
    if stage:
        a = a[a["life_stage"] == stage]
    a["benefit"] = (a["valence"] > 0).astype(int)
    return a


def dignity_ladder(annotated: pd.DataFrame, *, stage: str | None = "prime",
                   min_support: int = 25) -> pd.DataFrame:
    """Benefit rate by MD-lord dignity state, vs the subset base rate."""
    a = _subset(annotated, stage)
    if a.empty:
        return pd.DataFrame()
    base = a["benefit"].mean()
    rows = []
    for state in _DIGNITY_ORDER:
        g = a[a["md_dignity"] == state]
        if len(g) < min_support:
            continue
        share = g["benefit"].mean()
        p = binomtest(int(g["benefit"].sum()), len(g), base).pvalue
        rows.append({"md_dignity": state, "n": len(g),
                     "benefit_share": round(share, 3), "base_share": round(base, 3),
                     "lift": round(share / base, 3) if base else float("nan"),
                     "p_vs_base": p})
    return pd.DataFrame(rows)


def within_lord_contrast(annotated: pd.DataFrame, *, stage: str | None = "prime",
                         min_support: int = 20) -> pd.DataFrame:
    """Per planet: benefit share when WELL vs ILL dignified (events under
    that planet's MD only). The lord-identity-controlled gradient."""
    a = _subset(annotated, stage)
    if a.empty:
        return pd.DataFrame()
    rows = []
    for lord in _LORDS:
        g = a[a["md_lord_at_event"] == lord]
        well = g[g["md_dignity"].isin(_WELL)]
        ill = g[g["md_dignity"].isin(_ILL)]
        if len(well) < min_support or len(ill) < min_support:
            continue
        ws, is_ = well["benefit"].mean(), ill["benefit"].mean()
        # Exact 2x2 test (well/ill × beneficial/adverse) — two-sided.
        wb, wa = int(well["benefit"].sum()), len(well) - int(well["benefit"].sum())
        ib, ia = int(ill["benefit"].sum()), len(ill) - int(ill["benefit"].sum())
        p = fisher_exact([[wb, wa], [ib, ia]])[1]
        rows.append({"lord": lord, "n_well": len(well), "n_ill": len(ill),
                     "benefit_well": round(ws, 3), "benefit_ill": round(is_, 3),
                     "contrast": round(ws - is_, 3), "p": p})
    out = pd.DataFrame(rows)
    return out.sort_values("contrast", ascending=False).reset_index(drop=True) \
        if not out.empty else out


def side_decomposition(annotated: pd.DataFrame, *, stage: str | None = "prime",
                       min_support: int = 25) -> dict[str, float]:
    """Split the gradient into strong-side lift and weak-side drag, using
    the well/ill dignity grouping on the MD lord."""
    a = _subset(annotated, stage)
    if a.empty:
        return {}
    base = a["benefit"].mean()
    well = a[a["md_dignity"].isin(_WELL)]["benefit"]
    ill = a[a["md_dignity"].isin(_ILL)]["benefit"]
    if len(well) < min_support or len(ill) < min_support:
        return {"base": round(base, 3)}
    return {
        "base": round(base, 3),
        "well_share": round(well.mean(), 3),
        "ill_share": round(ill.mean(), 3),
        "strong_side_lift": round(well.mean() - base, 3),   # how much strong beats base
        "weak_side_drag": round(base - ill.mean(), 3),      # how much base beats weak
        "total_contrast": round(well.mean() - ill.mean(), 3),
    }


def build_report(ladder: pd.DataFrame, within: pd.DataFrame,
                 sides: dict[str, float], stage: str) -> str:
    L = [f"# Anatomy of the dignity → benefit gradient ({stage} stage)", "",
         "Descriptive dissection of the permutation-validated effect. "
         "All benefit rates net of the stage base rate.", ""]

    L += ["## 1. Dignity ladder (MD lord)", ""]
    if ladder.empty:
        L.append("_insufficient support._\n")
    else:
        L += ["| MD dignity | n | benefit % | base % | lift | p vs base |",
              "|---|---:|---:|---:|---:|---:|"]
        for _, r in ladder.iterrows():
            star = " ✶" if r["p_vs_base"] < 0.05 else ""
            L.append(f"| {r['md_dignity']} | {r['n']} | {r['benefit_share']*100:.0f} | "
                     f"{r['base_share']*100:.0f} | **{r['lift']:.2f}**{star} | "
                     f"{r['p_vs_base']:.3g} |")
        L.append("")

    if sides:
        L += ["## 2. Strong-side vs weak-side", "",
              "| component | value |", "|---|---:|"]
        for k, v in sides.items():
            L.append(f"| {k} | {v:+.3f} |" if k not in ("base", "well_share", "ill_share")
                     else f"| {k} | {v:.3f} |")
        L.append("")

    L += ["## 3. Within-lord contrast (lord-identity controlled)", "",
          "Benefit share when the *same planet* is well- vs ill-dignified in "
          "the native's chart — events under that planet's MD only.", ""]
    if within.empty:
        L.append("_no planet has enough well- AND ill-dignified events._\n")
    else:
        L += ["| MD lord | n well | n ill | benefit well % | benefit ill % | contrast | p |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for _, r in within.iterrows():
            star = " ✶" if r["p"] < 0.05 else ""
            L.append(f"| {r['lord']} | {r['n_well']} | {r['n_ill']} | "
                     f"{r['benefit_well']*100:.0f} | {r['benefit_ill']*100:.0f} | "
                     f"**{r['contrast']:+.2f}**{star} | {r['p']:.3g} |")
        L.append("")
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path, *, stage: str = "prime") -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    events = events[events["md_lord_at_event"].notna()].copy()
    charts = pd.read_parquet(data_dir / "charts.parquet")
    ann = annotate(events, charts)

    ladder = dignity_ladder(ann, stage=stage)
    within = within_lord_contrast(ann, stage=stage)
    sides = side_decomposition(ann, stage=stage)

    out_dir.mkdir(parents=True, exist_ok=True)
    ladder.to_csv(out_dir / "dignity_ladder.csv", index=False)
    within.to_csv(out_dir / "within_lord_contrast.csv", index=False)
    (out_dir / "dignity_anatomy.md").write_text(
        build_report(ladder, within, sides, stage), encoding="utf-8")
    logger.info("ladder rows=%d within-lord rows=%d sides=%s",
                len(ladder), len(within), sides)
    return {"ladder": len(ladder), "within_lord": len(within), "sides": sides}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("--stage", type=str, default="prime")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.data_dir, args.out, stage=args.stage))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
