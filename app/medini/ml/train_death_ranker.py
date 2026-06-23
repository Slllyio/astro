"""Learned per-window death ranker — the ML lever vs the hand-built composite ceiling.

Every person in the death corpus died in exactly one of their 81 Vimśottarī MD×AD
windows. This frames a learning-to-rank problem: per person (group), rank the 81
windows so the true death window ranks high. An XGBoost ranker can learn non-linear
interactions among the features the hand-built composite combines linearly
(duration, age, lord identity, the death significators incl. the doctrine-mined
Karakāṁśa/Sun marakas) — the one structurally-different lever we hadn't tried.

Evaluated on the SAME held-out person split as `death_backtest` (`_in_test`), so the
**capture@10%** number is directly comparable to the composite baseline (~0.22). If it
doesn't beat that, it's recorded as the honest final negative.

Run: python -m app.medini.ml.train_death_ranker
"""
from __future__ import annotations

import logging
import math

import numpy as np
import pandas as pd

from app.core.shodashavarga import compute_divisional_longitude
from app.core.yogas import SIGN_RULERS
from app.medini.analysis import death_backtest as bt
from app.medini.analysis.doctrine_validator import (
    DASHA_LORDS, _MARAKA_GRAHAS, _div_sign_lord, _house_lord, _maraka_set, open_catalog,
)

logger = logging.getLogger(__name__)
_DPY = 365.2425
_LORDS = [l for l, _ in DASHA_LORDS]
_LORD_IDX = {l: i for i, l in enumerate(_LORDS)}


def _per_lord_flags(asc, asc_lon, gh, ak_sign):
    """For each of the 9 dāśā lords, its death-significator memberships in this chart."""
    sun_sign = ((asc - 1) + (gh.get("Sun", 1) - 1)) % 12 + 1
    maraka_full = _maraka_set(asc, gh, "full")
    maraka_sun = {_house_lord(sun_sign, 2), _house_lord(sun_sign, 7), "Saturn"}
    third = {_house_lord(asc, 3)}
    nav64 = {_div_sign_lord(asc_lon + 210.0, 9)}
    km = ({_house_lord(ak_sign, 2), _house_lord(ak_sign, 7), "Saturn"}
          if ak_sign else set())
    rows = []
    for lord in _LORDS:
        f_full = lord in maraka_full
        f_sun = lord in maraka_sun
        f_third = lord in third
        f_nav = lord in nav64
        f_km = lord in km
        rows.append((lord, int(f_full), int(f_sun), int(f_third), int(f_nav), int(f_km),
                     int(f_full) + int(f_third) + int(f_nav)))   # md composite score
    return rows


def build_training_frame(con) -> pd.DataFrame:
    # true death window per person
    deaths = con.execute(
        """SELECT person_id, md_seq, ad_seq FROM events_with_dasha
           WHERE event_class='death_cause_unspecified'
             AND md_seq IS NOT NULL AND ad_seq IS NOT NULL"""
    ).df()
    deaths["is_death"] = 1

    hc = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    lc = ", ".join(f"c.{g.lower()}_lon AS {g.lower()}_lon" for g in _MARAKA_GRAHAS)
    chart_rows = con.execute(
        f"""SELECT c.person_id, c.asc_sign, c.asc_lon, {hc}, {lc}, k.planet AS ak
            FROM charts c
            JOIN (SELECT DISTINCT person_id FROM events_with_dasha
                  WHERE event_class='death_cause_unspecified') d USING(person_id)
            LEFT JOIN jaimini_karakas k ON k.person_id=c.person_id
                                       AND k.karaka='AK_Atmakaraka'
            WHERE c.asc_sign IS NOT NULL AND c.asc_lon IS NOT NULL"""
    ).fetchall()
    nc = len(_MARAKA_GRAHAS)
    flag_rows = []
    for r in chart_rows:
        pid, asc, asc_lon = r[0], int(r[1]), float(r[2])
        houses = r[3:3 + nc]; lons = r[3 + nc:3 + 2 * nc]; ak = r[-1]
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        lo = {g: l for g, l in zip(_MARAKA_GRAHAS, lons)}
        ak_sign = (int(compute_divisional_longitude(lo[ak] % 360.0, 9) // 30) + 1
                   if ak and lo.get(ak) is not None else None)
        for (lord, ff, fs, ft, fn, fk, sc) in _per_lord_flags(asc, asc_lon, gh, ak_sign):
            flag_rows.append((pid, lord, ff, fs, ft, fn, fk, sc))
    flags = pd.DataFrame(flag_rows, columns=[
        "person_id", "lord", "f_full", "f_sun", "f_third", "f_nav", "f_km", "score"])

    windows = con.execute(
        """SELECT w.person_id, w.md_seq, w.ad_seq, w.md_lord, w.ad_lord,
                  w.duration_days, w.start_jd, w.end_jd, c.birth_jd_used AS bjd
           FROM dasha_windows w JOIN charts c USING(person_id)
           JOIN (SELECT DISTINCT person_id FROM events_with_dasha
                 WHERE event_class='death_cause_unspecified') d USING(person_id)"""
    ).df()
    windows["mid_age"] = ((windows["start_jd"] + windows["end_jd"]) / 2 - windows["bjd"]) / _DPY

    # merge md-lord flags
    df = windows.merge(flags, left_on=["person_id", "md_lord"],
                       right_on=["person_id", "lord"], how="left").drop(columns=["lord"])
    # ad composite score
    ad_sc = flags[["person_id", "lord", "score"]].rename(
        columns={"lord": "ad_lord", "score": "ad_score"})
    df = df.merge(ad_sc, on=["person_id", "ad_lord"], how="left")
    # label
    df = df.merge(deaths, on=["person_id", "md_seq", "ad_seq"], how="left")
    df["is_death"] = df["is_death"].fillna(0).astype(int)
    df["md_idx"] = df["md_lord"].map(_LORD_IDX).fillna(-1).astype(int)
    df["ad_idx"] = df["ad_lord"].map(_LORD_IDX).fillna(-1).astype(int)
    df["in_test"] = df["person_id"].map(lambda p: bt._in_test(p, 0.25))
    return df


_FEATURES = ["duration_days", "mid_age", "md_seq", "ad_seq", "md_idx", "ad_idx",
             "score", "ad_score", "f_full", "f_sun", "f_third", "f_nav", "f_km"]


def _capture_at_10(df: pd.DataFrame, score_col: str) -> float:
    hit = n = 0
    for _, g in df.groupby("person_id", sort=False):
        if g["is_death"].sum() != 1:
            continue
        k = max(1, int(round(0.10 * len(g))))
        topk = g.nlargest(k, score_col)
        hit += int(topk["is_death"].sum() >= 1)
        n += 1
    return hit / n if n else 0.0


def main() -> int:
    import xgboost as xgb
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    con = open_catalog()
    try:
        df = build_training_frame(con)
    finally:
        con.close()
    logger.info("rows=%d persons=%d (windows/person≈%.0f)",
                len(df), df["person_id"].nunique(), len(df) / df["person_id"].nunique())

    tr = df[~df["in_test"]].sort_values("person_id")
    te = df[df["in_test"]].sort_values("person_id")
    grp_tr = tr.groupby("person_id", sort=False).size().to_numpy()

    ranker = xgb.XGBRanker(
        objective="rank:pairwise", n_estimators=300, max_depth=5,
        learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        min_child_weight=5, tree_method="hist",
    )
    ranker.fit(tr[_FEATURES], tr["is_death"], group=grp_tr)
    te = te.copy()
    te["pred"] = ranker.predict(te[_FEATURES])

    # Baseline: the hand-built composite weight  dur × bracket × (1+0.05·score)
    from app.medini.analysis import death_window_predictor as dwp
    br = te["mid_age"].map(lambda a: dwp.DEFAULT_BRACKET_FACTOR.get(
        dwp._bracket_for_age(a, dwp.DEFAULT_BRACKETS), 1.0))
    te["composite_w"] = te["duration_days"] * br * (1 + 0.05 * te["score"])

    cap_model = _capture_at_10(te, "pred")
    cap_base = _capture_at_10(te, "composite_w")
    cap_dur = _capture_at_10(te, "duration_days")

    fi = sorted(zip(_FEATURES, ranker.feature_importances_), key=lambda x: -x[1])[:6]
    print("\n=== Learned per-window death ranker (held-out) ===")
    print(f"test persons: {te['person_id'].nunique()}")
    print(f"  capture@10%  duration-only        : {cap_dur:.4f}")
    print(f"  capture@10%  hand composite (M2-ish): {cap_base:.4f}")
    print(f"  capture@10%  XGBoost ranker         : {cap_model:.4f}   "
          f"(Δ vs composite {cap_model - cap_base:+.4f})")
    print("  top features:", ", ".join(f"{f}={i:.2f}" for f, i in fi))
    n = te["person_id"].nunique()
    se = math.sqrt(0.22 * 0.78 / n) if n else 0.0
    print(f"  (±1 SE on capture ≈ {se:.4f}; a real win must clear ~2 SE)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
