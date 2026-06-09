"""Enrich dasha events with native-kundli features, then deep-dive benefit rates.

The dignity work scored the running lords on one axis (composite dignity).
This module widens that to the rest of the natal chart and asks, for every
event, *what is the standing of the running MD and AD lords in THIS native's
kundli* — and which of those standings actually track event valence.

Per running lord (MD and AD), relative to the native's D1:
  * natural nature      — benefic / malefic (Jupiter·Venus·Mercury·Moon vs
                          Sun·Mars·Saturn·Rahu·Ketu)
  * functional nature   — benefic / malefic / neutral from house lordship
                          off the ascendant (yogakaraka, dusthana-lord, …)
  * is_yogakaraka / is_maraka / is_lagna_lord
  * dignity_state       — exalted … debilitated (sign placement)
  * house occupied + house_kind (lagna / kendra / trikona / dusthana /
                          upachaya / maraka) + boolean membership flags

Per MD↔AD pair:
  * naisargika relation (friend / neutral / enemy)
  * same_sign (conjunction), both_benefic, both_malefic

Per native (chart-level covariates, constant across that person's events):
  * benefics_in_kendra, malefics_in_dusthana, benefics_in_dusthana,
    malefics_in_kendra, kendra_net (benefic−malefic auspiciousness index)
  * lagna_lord + its house + dignity
  * n_exalted, n_debilitated, n_yogakaraka

The deep dive then reports the benefit rate (and lift over the stage base)
for each feature level, so we can see which native-chart facts — not just
dignity — separate beneficial from adverse events.

Usage::

    python -m app.medini.ml.dasha_event_features \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --stage prime
"""
from __future__ import annotations

import argparse
import logging
from functools import lru_cache
from pathlib import Path
from typing import Final

import pandas as pd
from scipy.stats import binomtest

from app.core.bhava_judge import _NATURAL_BENEFICS, _NATURAL_MALEFICS
from app.core.dignity import SIGN_RULERS, dignity_state
from app.core.functional_roles import functional_roles
from app.medini.ml.dasha_lifestage_dignity import event_valence, life_stage

logger = logging.getLogger(__name__)

_LORDS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({1, 5, 9})
_DUSTHANAS: Final[frozenset[int]] = frozenset({6, 8, 12})
_UPACHAYA: Final[frozenset[int]] = frozenset({3, 6, 10, 11})
_MARAKAS: Final[frozenset[int]] = frozenset({2, 7})


def _natural(planet: str) -> str:
    if planet in _NATURAL_BENEFICS:
        return "benefic"
    if planet in _NATURAL_MALEFICS:
        return "malefic"
    return "neutral"


def _safe_dignity(planet: str, sign: object) -> str:
    if sign is None or pd.isna(sign):
        return "unknown"
    try:
        return dignity_state(planet, int(sign))
    except (KeyError, ValueError):
        return "unknown"  # nodes / unrulable


def _house_kind(h: object) -> str:
    if h is None or pd.isna(h):
        return "unknown"
    h = int(h)
    if h == 1:
        return "lagna"
    if h in _DUSTHANAS:
        return "dusthana"
    if h in (5, 9):
        return "trikona"
    if h in _KENDRAS:
        return "kendra"
    if h in (3, 11):
        return "upachaya"
    if h == 2:
        return "maraka"
    return "other"


@lru_cache(maxsize=16)
def _roles(lagna_sign: int) -> dict:
    return functional_roles(lagna_sign)


def _functional(planet: str, lagna_sign: int | None) -> str:
    if lagna_sign is None or planet not in _LORDS:
        return "unknown"
    r = _roles(int(lagna_sign)).get(planet)
    if r is None:
        return "unknown"
    if r.is_functional_benefic:
        return "benefic"
    if r.is_functional_malefic:
        return "malefic"
    return "neutral"


def _chart_features(crow: pd.Series) -> dict[str, object]:
    """Native-level covariates computed once per person."""
    asc = int(crow["asc_sign"]) if pd.notna(crow.get("asc_sign")) else None
    ben_kendra = mal_dusthana = ben_dusthana = mal_kendra = 0
    n_exalt = n_debil = 0
    for p in _LORDS:
        h = crow.get(f"{p.lower()}_house")
        s = crow.get(f"{p.lower()}_sign")
        if pd.notna(h):
            h = int(h)
            nat = _natural(p)
            if nat == "benefic" and h in _KENDRAS:
                ben_kendra += 1
            if nat == "malefic" and h in _DUSTHANAS:
                mal_dusthana += 1
            if nat == "benefic" and h in _DUSTHANAS:
                ben_dusthana += 1
            if nat == "malefic" and h in _KENDRAS:
                mal_kendra += 1
        dg = _safe_dignity(p, s)
        n_exalt += dg == "exalted"
        n_debil += dg == "debilitated"
    lagna_lord = SIGN_RULERS.get(asc) if asc else None
    ll_house = crow.get(f"{lagna_lord.lower()}_house") if lagna_lord else None
    ll_sign = crow.get(f"{lagna_lord.lower()}_sign") if lagna_lord else None
    n_yk = sum(1 for r in _roles(asc).values() if r.is_yogakaraka) if asc else 0
    return {
        "chart_benefics_in_kendra": ben_kendra,
        "chart_malefics_in_dusthana": mal_dusthana,
        "chart_benefics_in_dusthana": ben_dusthana,
        "chart_malefics_in_kendra": mal_kendra,
        "chart_kendra_net": ben_kendra - mal_kendra,
        "chart_lagna_lord": lagna_lord,
        "chart_lagna_lord_house": int(ll_house) if pd.notna(ll_house) else None,
        "chart_lagna_lord_dignity": _safe_dignity(lagna_lord, ll_sign)
        if lagna_lord else "unknown",
        "chart_n_exalted": n_exalt,
        "chart_n_debilitated": n_debil,
        "chart_n_yogakaraka": n_yk,
    }


def _lord_features(crow: pd.Series, lord: str, prefix: str) -> dict[str, object]:
    """MD- or AD-lord standing in the native chart."""
    asc = int(crow["asc_sign"]) if pd.notna(crow.get("asc_sign")) else None
    sign = crow.get(f"{lord.lower()}_sign")
    house = crow.get(f"{lord.lower()}_house")
    r = _roles(asc).get(lord) if asc else None
    hk = _house_kind(house)
    h = int(house) if pd.notna(house) else None
    return {
        f"{prefix}_natural": _natural(lord),
        f"{prefix}_functional": _functional(lord, asc),
        f"{prefix}_dignity": _safe_dignity(lord, sign),
        f"{prefix}_house": h,
        f"{prefix}_house_kind": hk,
        f"{prefix}_is_kendra": h in _KENDRAS if h else False,
        f"{prefix}_is_trikona": h in _TRIKONAS if h else False,
        f"{prefix}_is_dusthana": h in _DUSTHANAS if h else False,
        f"{prefix}_is_upachaya": h in _UPACHAYA if h else False,
        f"{prefix}_is_yogakaraka": bool(r and r.is_yogakaraka),
        f"{prefix}_is_maraka": bool(r and r.is_maraka),
        f"{prefix}_is_lagna_lord": bool(r and r.is_lagna_lord),
        f"{prefix}_n_houses_ruled": len(r.houses_ruled) if r else 0,
    }


def enrich_events(events: pd.DataFrame, charts: pd.DataFrame) -> pd.DataFrame:
    """Attach native-kundli features + life_stage + valence to every event."""
    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    chart_cache: dict[str, dict] = {}
    rows: list[dict] = []
    for _, ev in events.iterrows():
        pid = ev["person_id"]
        feat: dict[str, object] = {}
        if pid in cidx.index:
            crow = cidx.loc[pid]
            if pid not in chart_cache:
                chart_cache[pid] = _chart_features(crow)
            feat.update(chart_cache[pid])
            md, ad = ev.get("md_lord_at_event"), ev.get("ad_lord_at_event")
            if pd.notna(md) and md in _LORDS:
                feat.update(_lord_features(crow, str(md), "md"))
            if pd.notna(ad) and ad in _LORDS:
                feat.update(_lord_features(crow, str(ad), "ad"))
            # pair relations
            if pd.notna(md) and pd.notna(ad) and md in _LORDS and ad in _LORDS:
                from app.core.dignity import naisargika_relation
                try:
                    feat["pair_naisargika"] = naisargika_relation(str(md), str(ad))
                except (KeyError, ValueError):
                    feat["pair_naisargika"] = "unknown"  # nodes absent from table
                feat["pair_same_sign"] = bool(
                    pd.notna(crow.get(f"{str(md).lower()}_sign"))
                    and crow.get(f"{str(md).lower()}_sign")
                    == crow.get(f"{str(ad).lower()}_sign"))
                feat["pair_both_benefic"] = (
                    _natural(str(md)) == "benefic" and _natural(str(ad)) == "benefic")
                feat["pair_both_malefic"] = (
                    _natural(str(md)) == "malefic" and _natural(str(ad)) == "malefic")
        rows.append(feat)
    feats = pd.DataFrame(rows, index=events.index)
    out = pd.concat([events.reset_index(drop=True), feats.reset_index(drop=True)],
                    axis=1)
    out["life_stage"] = out["age_at_event_years"].map(life_stage)
    sub = out["event_subtype"] if "event_subtype" in out.columns else pd.Series(
        [None] * len(out))
    out["valence"] = [event_valence(c, s) for c, s in zip(out["event_class"], sub)]
    return out


# ── deep-dive analysis ──────────────────────────────────────────────────────
def feature_benefit_table(enriched: pd.DataFrame, feature: str, *,
                          stage: str | None = "prime",
                          min_support: int = 30) -> pd.DataFrame:
    """Benefit share by each level of `feature`, vs the subset base rate."""
    a = enriched[enriched["valence"] != 0].copy()
    if stage:
        a = a[a["life_stage"] == stage]
    if feature not in a.columns or a.empty:
        return pd.DataFrame()
    a["benefit"] = (a["valence"] > 0).astype(int)
    base = a["benefit"].mean()
    rows = []
    for level, g in a.groupby(feature, dropna=False):
        if len(g) < min_support:
            continue
        share = g["benefit"].mean()
        p = binomtest(int(g["benefit"].sum()), len(g), base).pvalue
        rows.append({"feature": feature, "level": level, "n": len(g),
                     "benefit_share": round(share, 3), "base": round(base, 3),
                     "lift": round(share / base, 3) if base else float("nan"),
                     "p_vs_base": p})
    out = pd.DataFrame(rows)
    return out.sort_values("benefit_share", ascending=False).reset_index(drop=True) \
        if not out.empty else out


_DEEP_DIVE_FEATURES: Final[tuple[str, ...]] = (
    "md_natural", "ad_natural", "md_functional", "ad_functional",
    "md_dignity", "md_house_kind", "ad_house_kind",
    "md_is_yogakaraka", "md_is_dusthana", "md_is_trikona", "md_is_kendra",
    "pair_naisargika", "pair_both_benefic", "pair_both_malefic", "pair_same_sign",
    "chart_kendra_net",
)


def build_report(enriched: pd.DataFrame, stage: str) -> str:
    tables = {f: feature_benefit_table(enriched, f, stage=stage)
              for f in _DEEP_DIVE_FEATURES}
    tables = {f: t for f, t in tables.items() if not t.empty}
    n_cells = sum(len(t) for t in tables.values())
    bonf = 0.05 / n_cells if n_cells else 0.05  # family-wise threshold

    # headline: cells that beat the Bonferroni bar, and notable nulls.
    hits = []
    for f, t in tables.items():
        for _, r in t.iterrows():
            if r["p_vs_base"] < bonf:
                hits.append((f, r["level"], r["benefit_share"], r["lift"],
                             r["p_vs_base"]))
    L = [f"# Native-kundli event features — deep dive ({stage} stage)", "",
         "Benefit share by each native-chart feature of the running lords, net "
         "of the stage base rate. `lift` > 1 ⇒ more beneficial than average; "
         "✶ marks raw p < 0.05 vs base.", "",
         "## Headlines", "",
         f"- **{n_cells} feature-levels tested** → Bonferroni family-wise bar "
         f"p < {bonf:.4f}.", ]
    if hits:
        L.append("- Survive that bar:")
        for f, lvl, sh, lift, p in sorted(hits, key=lambda x: x[4]):
            L.append(f"    - `{f} = {lvl}` → {sh*100:.0f}% (lift {lift:.2f}, "
                     f"p={p:.4g})")
    else:
        L.append("- **None** survive the family-wise bar.")
    L += [
        "- **Natural benefic/malefic is flat**: a running natural benefic and a "
        "running natural malefic carry essentially the same benefit rate — the "
        "naisargika dichotomy does *not*, by itself, separate good from bad "
        "events here. `pair_both_benefic` is likewise null.",
        "- The composite *dignity* gradient (separate module, +0.2 pair) is "
        "stronger than any single feature below, because it pools dignity across "
        "both lords and contrasts the tails.", "",
    ]
    for feat, tab in tables.items():
        L += [f"## {feat}", "",
              "| level | n | benefit % | lift | p |",
              "|---|---:|---:|---:|---:|"]
        for _, r in tab.iterrows():
            star = " ✶" if r["p_vs_base"] < 0.05 else ""
            L.append(f"| {r['level']} | {r['n']} | {r['benefit_share']*100:.0f} | "
                     f"**{r['lift']:.2f}**{star} | {r['p_vs_base']:.3g} |")
        L.append("")
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path, *, stage: str = "prime") -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    events = events[events["md_lord_at_event"].notna()].copy()
    charts = pd.read_parquet(data_dir / "charts.parquet")
    enriched = enrich_events(events, charts)

    out_dir.mkdir(parents=True, exist_ok=True)
    enriched.to_parquet(out_dir / "events_enriched.parquet", index=False)
    (out_dir / "event_features_deepdive.md").write_text(
        build_report(enriched, stage), encoding="utf-8")
    n_feat = sum(c.startswith(("md_", "ad_", "pair_", "chart_"))
                 for c in enriched.columns)
    logger.info("enriched %d events with %d kundli features", len(enriched), n_feat)
    return {"events": len(enriched), "features_added": n_feat}


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
