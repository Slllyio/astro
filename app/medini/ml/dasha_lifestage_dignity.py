"""Life-stage × MD-lord-dignity interaction over dated events.

The flat "Venus MD → marriage" association (``dasha_event_associations``)
hides two interacting modifiers the classics insist on:

  1. **Chart-quality of the MD lord.** An *exalted / benefic / good-house*
     lord delivers its dasha very differently from a *debilitated /
     functional-malefic* one — same planet, opposite outcome.
  2. **Life stage at which the dasha lands.** A strong benefic MD in the
     productive years (≈25–42) has runway to manifest as marriage,
     career, wealth, progeny; the *same* MD at 70+ has less to build and
     meets a different event base-rate (health/death rise, marriage
     falls). The mirror holds: a weak/malefic MD bites harder where the
     native is most exposed.

This module makes that interaction measurable. It joins
``events_with_dasha.parquet`` to ``charts.parquet`` (natal sign of the
active MD lord + ascendant), scores the lord into strong / mixed / weak
by composing the project's canonical classical layers —

  * :func:`app.core.dignity.dignity_state`  (exalted/own/debilitated/…),
  * :func:`app.core.functional_roles.functional_roles`  (functional
    benefic/malefic, yogakaraka, from the ascendant),
  * natural benefic/malefic nature —

buckets ``age_at_event_years`` into life stages, tags each event's
**valence** (beneficial / adverse), and reports:

  * the benefit rate in every (life_stage × md_quality) cell, as a lift
    over that life stage's *own* base rate — so the dignity effect is
    read net of the age shift in base rates;
  * the **dignity gradient** per life stage (strong − weak benefit
    share) — the direct test of "a good lord helps more in the prime
    years than in old age";
  * which MD lords actually run at each life stage.

Valence
-------
Polarity is only recorded explicitly in the lapaas corpus
(``event_subtype`` ∈ Beneficial/Adverse/Neutral). For the ADB events we
fall back to a documented, overridable ``VALENCE_MAP`` over
``event_class``. Explicit polarity, when present, always wins.

Caveat (carried from round11_triple_test_synthesis): a descriptive
interaction, not a deconfounded causal effect. The life-stage
stratification removes the *first-order* age confound only.

Usage::

    python -m app.medini.ml.dasha_lifestage_dignity
    python -m app.medini.ml.dasha_lifestage_dignity \\
        --data-dir app/medini/data \\
        --out data/ml_runs/dasha_lifestage_dignity --min-support 8
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

from app.core.dignity import dignity_state
from app.core.functional_roles import functional_roles

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DEFAULT_OUT_DIR: Final = Path("data/ml_runs/dasha_lifestage_dignity")
EVENTS_FILE: Final = "events_with_dasha.parquet"
CHARTS_FILE: Final = "charts.parquet"

# (label, lo_inclusive, hi_exclusive) — years of age at the event.
LIFE_STAGES: Final[tuple[tuple[str, float, float], ...]] = (
    ("childhood", 0.0, 14.0),
    ("youth", 14.0, 25.0),
    ("prime", 25.0, 42.0),      # establishment / productive years
    ("maturity", 42.0, 60.0),
    ("elder", 60.0, 200.0),
)
_STAGE_ORDER: Final = [s[0] for s in LIFE_STAGES]
_QUALITY_ORDER: Final = ["strong", "mixed", "weak"]

# Natural nature (uncontested classical sets; nodes malefic).
_NATURAL_BENEFICS: Final[frozenset[str]] = frozenset(
    {"Jupiter", "Venus", "Mercury", "Moon"})
_NATURAL_MALEFICS: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"})

# dignity_state → signed strength.
_DIGNITY_SCORE: Final[dict[str, float]] = {
    "exalted": 1.0, "own": 0.7, "friendly": 0.3, "neutral": 0.0,
    "inimical": -0.35, "debilitated": -1.0,
}

# Coarse, documented event_class → valence. +1 beneficial, -1 adverse,
# 0 neutral/excluded from the benefit rate. Overridden by explicit
# polarity subtype when present. Tune freely — reporting-only.
VALENCE_MAP: Final[dict[str, int]] = {
    "marriage": 1, "career": 1, "fame": 1, "education": 1,
    "finance": 1, "work": 1, "progeny": 1, "achievement": 1,
    "death": -1, "death_by_disease": -1, "death_cause_unspecified": -1,
    "health": -1, "legal": -1, "crime": -1, "accident": -1, "divorce": -1,
    # deliberately neutral (mixed valence): relationship(s), personal, family
}
_POLARITY_SUBTYPE: Final[dict[str, int]] = {
    "beneficial": 1, "adverse": -1, "negative": -1, "positive": 1, "neutral": 0,
}


def _bucket(score: float) -> str:
    """Composite-score → strong / mixed / weak (±0.33 thresholds)."""
    return "strong" if score >= 0.33 else "weak" if score <= -0.33 else "mixed"


def md_lord_quality(
    planet: str,
    sign: int | None,
    asc_sign: int | None,
    *,
    w_dignity: float = 0.5,
    w_functional: float = 0.3,
    w_natural: float = 0.2,
) -> dict[str, object]:
    """Composite natal quality of the active MD lord → strong/mixed/weak.

    Blends three canonical layers:
      * dignity_state(planet, sign) — by the lord's natal sign;
      * functional_roles(asc_sign)  — yogakaraka / functional benefic /
        malefic, by the ascendant (nodes carry no rulership → 0);
      * natural benefic/malefic nature.

    Returns a dict of component labels/scores plus a ``quality`` bucket
    (strong ≥ +0.33, weak ≤ −0.33, else mixed). Weights are exposed so
    the contested functional component can be sensitivity-tested.
    """
    dig = dignity_state(planet, int(sign)) if sign and 1 <= int(sign) <= 12 else "neutral"
    dig_s = _DIGNITY_SCORE.get(dig, 0.0)

    func_s = 0.0
    func_label = "neutral"
    yk = False
    if asc_sign and 1 <= int(asc_sign) <= 12:
        roles = functional_roles(int(asc_sign)).get(planet)
        if roles is not None:  # nodes are absent → stay neutral
            yk = roles.is_yogakaraka
            if roles.is_yogakaraka:
                func_s, func_label = 0.6, "yogakaraka"
            elif roles.is_functional_benefic:
                func_s, func_label = 0.4, "benefic"
            elif roles.is_functional_malefic:
                func_s, func_label = -0.5, "malefic"

    if planet in _NATURAL_BENEFICS:
        nat_s = 0.3
    elif planet in _NATURAL_MALEFICS:
        nat_s = -0.3
    else:
        nat_s = 0.0

    score = w_dignity * dig_s + w_functional * func_s + w_natural * nat_s
    score = max(-1.0, min(1.0, score))
    return {
        "planet": planet, "dignity": dig, "functional": func_label,
        "yogakaraka": yk, "quality_score": round(score, 3),
        "quality": _bucket(score),
    }


def life_stage(age_years: float | None) -> str | None:
    """Map an age to its life-stage label, or None if missing/negative."""
    if age_years is None or pd.isna(age_years) or age_years < 0:
        return None
    for label, lo, hi in LIFE_STAGES:
        if lo <= age_years < hi:
            return label
    return None


def event_valence(event_class: str | None, event_subtype: str | None) -> int:
    """Resolve an event's valence (+1/-1/0). Explicit polarity wins."""
    if event_subtype is not None and not pd.isna(event_subtype):
        v = _POLARITY_SUBTYPE.get(str(event_subtype).strip().lower())
        if v is not None:
            return v
    if event_class is None or pd.isna(event_class):
        return 0
    return VALENCE_MAP.get(str(event_class).strip().lower(), 0)


def annotate(events: pd.DataFrame, charts: pd.DataFrame) -> pd.DataFrame:
    """Attach md_quality, md_functional, life_stage and valence per event.

    Requires ``events`` columns: person_id, event_class, md_lord_at_event,
    age_at_event_years (optionally event_subtype). ``charts`` must carry
    person_id, asc_sign and ``<graha>_sign``. Rows whose person has no
    chart (or whose MD lord is missing) get md_quality = "unknown".
    """
    df = events.copy()
    chart_idx = charts.set_index("person_id")
    has_ad = "ad_lord_at_event" in df.columns

    def _q(crow: pd.Series, lord: object) -> dict[str, object]:
        sign = crow.get(f"{str(lord).lower()}_sign")
        asc = crow.get("asc_sign")
        return md_lord_quality(
            str(lord),
            int(sign) if pd.notna(sign) else None,
            int(asc) if pd.notna(asc) else None,
        )

    md_q, md_f, md_s = [], [], []
    ad_q, ad_f, ad_s = [], [], []
    pair_q, pair_lbl = [], []
    ad_lords = df["ad_lord_at_event"] if has_ad else [None] * len(df)
    for person_id, md_lord, ad_lord in zip(
            df["person_id"], df["md_lord_at_event"], ad_lords):
        if md_lord is None or pd.isna(md_lord) or person_id not in chart_idx.index:
            for lst in (md_q, md_f, ad_q, ad_f, pair_q, pair_lbl):
                lst.append("unknown")
            md_s.append(float("nan"))
            ad_s.append(float("nan"))
            continue
        crow = chart_idx.loc[person_id]
        if isinstance(crow, pd.DataFrame):  # duplicate person_id — take first
            crow = crow.iloc[0]
        qm = _q(crow, md_lord)
        md_q.append(qm["quality"]); md_f.append(qm["functional"])
        md_s.append(float(qm["quality_score"]))
        if has_ad and ad_lord is not None and not pd.isna(ad_lord):
            qa = _q(crow, ad_lord)
            ad_q.append(qa["quality"]); ad_f.append(qa["functional"])
            ad_s.append(float(qa["quality_score"]))
            # Pair quality = mean of the two lords' composite scores. The AD
            # modulates the MD: a strong MD soured by a weak AD lands mixed.
            mean_s = (float(qm["quality_score"]) + float(qa["quality_score"])) / 2
            pair_q.append(_bucket(mean_s))
            pair_lbl.append(f"{qm['quality']}/{qa['quality']}")
        else:
            ad_q.append("unknown"); ad_f.append("unknown")
            ad_s.append(float("nan"))
            pair_q.append("unknown"); pair_lbl.append("unknown")

    df["md_quality"], df["md_functional"], df["md_quality_score"] = md_q, md_f, md_s
    df["ad_quality"], df["ad_functional"], df["ad_quality_score"] = ad_q, ad_f, ad_s
    df["pair_quality"], df["pair_label"] = pair_q, pair_lbl
    df["life_stage"] = df["age_at_event_years"].map(life_stage)
    subtype = (df["event_subtype"] if "event_subtype" in df.columns
               else pd.Series([None] * len(df), index=df.index))
    df["valence"] = [
        event_valence(ec, st) for ec, st in zip(df["event_class"], subtype)
    ]
    return df


def stage_quality_table(
    annotated: pd.DataFrame, *, quality_col: str = "md_quality", min_support: int = 8,
) -> pd.DataFrame:
    """Benefit rate per (life_stage × ``quality_col``), as a lift over the
    life stage's own base benefit rate.

    ``quality_col`` selects the lord whose dignity drives the split —
    ``md_quality``, ``ad_quality`` or the combined ``pair_quality``. Only
    valence≠0 events count. ``benefit_lift`` > 1 means that quality
    over-delivers beneficial events *relative to others at the same age*.
    Cells below ``min_support`` non-neutral events drop.
    """
    a = annotated[
        (annotated["valence"] != 0)
        & annotated["life_stage"].notna()
        & annotated[quality_col].isin(_QUALITY_ORDER)
    ].copy()
    if a.empty:
        return pd.DataFrame()
    a["benefit"] = (a["valence"] > 0).astype(int)
    stage_base = a.groupby("life_stage")["benefit"].mean()

    rows: list[dict[str, object]] = []
    for (stage, quality), grp in a.groupby(["life_stage", quality_col]):
        n = len(grp)
        if n < min_support:
            continue
        share = grp["benefit"].mean()
        base = stage_base[stage]
        rows.append({
            "life_stage": stage, "md_quality": quality, "n": int(n),
            "benefit_share": round(share, 3),
            "stage_base_share": round(base, 3),
            "benefit_lift": round(share / base, 3) if base > 0 else float("nan"),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_s"] = out["life_stage"].map(_STAGE_ORDER.index)
    out["_q"] = out["md_quality"].map(_QUALITY_ORDER.index)
    return out.sort_values(["_s", "_q"]).drop(columns=["_s", "_q"]).reset_index(drop=True)


def dignity_gradient(table: pd.DataFrame) -> pd.DataFrame:
    """Per life stage: strong benefit share − weak benefit share.

    The direct test of the claim — a positive gradient largest in the
    prime/maturity stages and compressing in childhood and old age is the
    signature of "a good lord helps more when there's runway to use it".
    """
    if table.empty:
        return pd.DataFrame()
    piv = table.pivot_table(
        index="life_stage", columns="md_quality", values="benefit_share")
    rows = []
    for stage in _STAGE_ORDER:
        if stage not in piv.index:
            continue
        strong = piv.loc[stage].get("strong")
        weak = piv.loc[stage].get("weak")
        if pd.isna(strong) or pd.isna(weak):
            continue
        rows.append({
            "life_stage": stage,
            "strong_benefit_share": round(float(strong), 3),
            "weak_benefit_share": round(float(weak), 3),
            "gradient": round(float(strong) - float(weak), 3),
        })
    return pd.DataFrame(rows)


def pair_cross_table(annotated: pd.DataFrame, *, min_support: int = 8) -> pd.DataFrame:
    """Benefit share for every (MD quality × AD quality) cell, pooled over
    life stages, as a lift over the global base benefit rate.

    This is the MD/AD interaction in one grid: does a strong MD survive a
    weak AD, and does a weak AD drag a strong MD down? Cells below
    ``min_support`` non-neutral events drop.
    """
    a = annotated[
        (annotated["valence"] != 0)
        & annotated["md_quality"].isin(_QUALITY_ORDER)
        & annotated["ad_quality"].isin(_QUALITY_ORDER)
    ].copy()
    if a.empty:
        return pd.DataFrame()
    a["benefit"] = (a["valence"] > 0).astype(int)
    base = a["benefit"].mean()

    rows: list[dict[str, object]] = []
    for (mq, aq), grp in a.groupby(["md_quality", "ad_quality"]):
        n = len(grp)
        if n < min_support:
            continue
        share = grp["benefit"].mean()
        rows.append({
            "md_quality": mq, "ad_quality": aq, "n": int(n),
            "benefit_share": round(share, 3), "base_share": round(base, 3),
            "benefit_lift": round(share / base, 3) if base > 0 else float("nan"),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_m"] = out["md_quality"].map(_QUALITY_ORDER.index)
    out["_a"] = out["ad_quality"].map(_QUALITY_ORDER.index)
    return out.sort_values(["_m", "_a"]).drop(columns=["_m", "_a"]).reset_index(drop=True)


def lord_by_stage(annotated: pd.DataFrame) -> pd.DataFrame:
    """Count of events by (life_stage × MD lord) — the literal 'which md
    runs at which life stage'. A sanity/exposure cross-check."""
    a = annotated[annotated["life_stage"].notna()
                  & annotated["md_lord_at_event"].notna()]
    if a.empty:
        return pd.DataFrame()
    tab = (a.groupby(["life_stage", "md_lord_at_event"]).size()
           .rename("n").reset_index())
    tab["_s"] = tab["life_stage"].map(_STAGE_ORDER.index)
    return tab.sort_values(["_s", "n"], ascending=[True, False]).drop(
        columns="_s").reset_index(drop=True)


def _scope_section(
    title: str, table: pd.DataFrame, gradient: pd.DataFrame, quality_label: str,
) -> list[str]:
    lines = [f"## {title}", "",
             "### Dignity gradient by life stage (strong − weak benefit share)", ""]
    if gradient.empty:
        lines.append("_insufficient support._\n")
    else:
        lines += ["| life stage | strong | weak | gradient |", "|---|---:|---:|---:|"]
        for _, r in gradient.iterrows():
            lines.append(
                f"| {r['life_stage']} | {r['strong_benefit_share']:.2f} | "
                f"{r['weak_benefit_share']:.2f} | **{r['gradient']:+.2f}** |")
        lines.append("")
    lines += [f"### Benefit lift per (life stage × {quality_label})", ""]
    if table.empty:
        lines.append("_insufficient support._\n")
    else:
        lines += [f"| life stage | {quality_label} | n | benefit % | stage base % | lift |",
                  "|---|---|---:|---:|---:|---:|"]
        for _, r in table.iterrows():
            lines.append(
                f"| {r['life_stage']} | {r['md_quality']} | {r['n']} | "
                f"{r['benefit_share']*100:.0f} | {r['stage_base_share']*100:.0f} | "
                f"**{r['benefit_lift']:.2f}** |")
        lines.append("")
    return lines


def build_report(
    scopes: dict[str, tuple[pd.DataFrame, pd.DataFrame]],
    cross: pd.DataFrame,
    lords: pd.DataFrame,
) -> str:
    """Render the multi-scope report. ``scopes`` maps a section title to
    its (stage_quality_table, dignity_gradient) pair; ``cross`` is the
    pooled MD×AD grid."""
    lines: list[str] = [
        "# Life-stage × dasha-lord dignity (descriptive)",
        "",
        "`*_quality` = composite of natal dignity + functional nature "
        "(yogakaraka/FB/FM) + natural nature, for the Mahadasha lord (MD), "
        "Antardasha lord (AD), or both (pair = mean of the two scores). "
        "`benefit_lift` = cell benefit share ÷ that life stage's base "
        "benefit share, so the dignity effect is read net of the age shift "
        "in base rates.",
        "",
        "> Descriptive interaction, not a deconfounded causal effect.",
        "",
    ]
    labels = {"MD lord": "MD quality", "AD lord": "AD quality",
              "MD+AD pair": "pair quality"}
    for title, (table, gradient) in scopes.items():
        lines += _scope_section(title, table, gradient, labels.get(title, "quality"))

    lines += ["## MD × AD interaction grid (pooled, lift over global base)", ""]
    if cross.empty:
        lines.append("_insufficient support._\n")
    else:
        lines += ["| MD quality | AD quality | n | benefit % | base % | lift |",
                  "|---|---|---:|---:|---:|---:|"]
        for _, r in cross.iterrows():
            lines.append(
                f"| {r['md_quality']} | {r['ad_quality']} | {r['n']} | "
                f"{r['benefit_share']*100:.0f} | {r['base_share']*100:.0f} | "
                f"**{r['benefit_lift']:.2f}** |")
        lines.append("")

    lines += ["## Which MD lord runs at each life stage (event counts)", ""]
    if lords.empty:
        lines.append("_no data._")
    else:
        for stage in _STAGE_ORDER:
            sub = lords[lords["life_stage"] == stage]
            if sub.empty:
                continue
            top = ", ".join(f"{r.md_lord_at_event} ({r.n})"
                            for r in sub.head(4).itertuples())
            lines.append(f"- **{stage}**: {top}")
        lines.append("")
    return "\n".join(lines)


def run(data_dir: Path, out_dir: Path, *, min_support: int = 8) -> dict[str, int]:
    events_path = data_dir / EVENTS_FILE
    charts_path = data_dir / CHARTS_FILE
    for p in (events_path, charts_path):
        if not p.exists():
            raise FileNotFoundError(
                f"{p} missing — build events_with_dasha + charts first.")

    events = pd.read_parquet(events_path)
    events = events[events["md_lord_at_event"].notna()].copy()
    charts = pd.read_parquet(charts_path)
    logger.info("events=%d charts=%d", len(events), len(charts))

    annotated = annotate(events, charts)

    scopes: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for title, col in (("MD lord", "md_quality"), ("AD lord", "ad_quality"),
                       ("MD+AD pair", "pair_quality")):
        tbl = stage_quality_table(annotated, quality_col=col, min_support=min_support)
        scopes[title] = (tbl, dignity_gradient(tbl))

    cross = pair_cross_table(annotated, min_support=min_support)
    lords = lord_by_stage(annotated)

    out_dir.mkdir(parents=True, exist_ok=True)
    for title, (tbl, grad) in scopes.items():
        tag = title.split()[0].lower().replace("+", "_")
        tbl.to_csv(out_dir / f"stage_quality_{tag}.csv", index=False)
        grad.to_csv(out_dir / f"dignity_gradient_{tag}.csv", index=False)
    cross.to_csv(out_dir / "md_ad_cross.csv", index=False)
    lords.to_csv(out_dir / "lord_by_stage.csv", index=False)
    (out_dir / "lifestage_dignity.md").write_text(
        build_report(scopes, cross, lords), encoding="utf-8")

    logger.info("wrote report + CSVs to %s", out_dir)
    return {
        "events_annotated": len(annotated),
        "with_chart": int((annotated["md_quality"] != "unknown").sum()),
        "md_cells": len(scopes["MD lord"][0]),
        "ad_cells": len(scopes["AD lord"][0]),
        "pair_cells": len(scopes["MD+AD pair"][0]),
        "cross_cells": len(cross),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--min-support", type=int, default=8)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.data_dir, args.out, min_support=args.min_support))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
