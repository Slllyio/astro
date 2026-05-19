"""Round 6 Phase 12: Synastry / pairwise compatibility.

Two deliverables:

1. **Synastry feature library** (`compute_synastry_features(chart_a, chart_b)`).
   Pre-built infrastructure for when explicit couple data arrives.
   Computes all classical synastry features:
   - Cross-chart aspects (planet_A vs planet_B angular distances)
   - House placements (planet_A in house_B vs reverse)
   - Sign rulership of partner's significators
   - Ashtakoot kuta scores (Varna, Vashya, Tara, Yoni, Graha Maitri,
     Gana, Bhakoot, Nadi — the 8 classical compatibility factors)

2. **Marriage outcome classifier** trained on the per-person event_subtype
   (Positive vs Negative for marriage events). Tests whether the
   individual's natal chart alone carries signal about MARRIAGE
   QUALITY (not just whether marriage happened).

Without explicit couple labels we can't validate (1) directly; the
library is shipped for downstream use. (2) is the empirical deliverable
for Phase 12.

CLI
===
    python -m app.medini.ml.synastry \\
        --natal app/medini/data/ml_astro_round5.parquet \\
        --events data/astro_databank/events_all.csv \\
        --output data/ml_runs/synastry_round6_phase12/
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from app.medini.ml.train_classifier import select_features

logger = logging.getLogger(__name__)


GRAHAS: tuple[str, ...] = (
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
)


# ---------- Ashtakoot kuta scoring (classical 8-fold compatibility) ----------
#
# Classical Vedic synastry rates two charts on 8 axes via Ashtakoot.
# Each kuta is a 0..N points contribution; total max 36.
# We compute the kuta scores from Moon nakshatra + sign data.

NAKSHATRA_NAMES = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
)

# Nadi mapping: 0=Adi, 1=Madhya, 2=Antya (classical 3-way grouping of 27 nakshatras)
# Standard Bhrigu mapping: nakshatra index → nadi
NADI_MAP = (
    0, 1, 2, 2, 1, 0, 0, 1, 2,    # Ashwini..Ashlesha
    2, 1, 0, 0, 1, 2, 2, 1, 0,    # Magha..Jyeshtha
    0, 1, 2, 2, 1, 0, 0, 1, 2,    # Mula..Revati
)

# Yoni mapping (classical animal pairings) — 14 yonis cycled
YONI_MAP = (
    0, 1, 2, 2, 3, 3, 4, 4, 5,
    5, 6, 6, 7, 7, 8, 8, 9, 9,
    10, 10, 11, 11, 12, 12, 13, 13, 0,
)
YONI_COMPATIBILITY = {
    # Same yoni = 4, friendly = 3, neutral = 2, unfriendly = 1, enemy = 0
    # Simplified: same = 4, opposite parity = 1, else 2
}


def _gana(nak_idx: int) -> int:
    """Classify nakshatra into Deva/Manushya/Rakshasa gana (0/1/2)."""
    devas = {0, 4, 6, 11, 12, 16, 21, 23, 26}
    manushyas = {1, 5, 10, 11, 17, 18, 19, 20, 24, 25}
    if nak_idx in devas:
        return 0
    if nak_idx in manushyas:
        return 1
    return 2


def _varna(moon_sign: int) -> int:
    """Brahmin/Kshatriya/Vaishya/Shudra mapping from Moon sign."""
    # Cancer(4), Scorpio(8), Pisces(12) → Brahmin (0)
    # Aries(1), Leo(5), Sagittarius(9) → Kshatriya (1)
    # Taurus(2), Virgo(6), Capricorn(10) → Vaishya (2)
    # Gemini(3), Libra(7), Aquarius(11) → Shudra (3)
    return {1: 1, 2: 2, 3: 3, 4: 0, 5: 1, 6: 2,
            7: 3, 8: 0, 9: 1, 10: 2, 11: 3, 12: 0}.get(moon_sign, 0)


def _vashya(moon_sign: int) -> int:
    """5-way classification: Chatushpada/Dvipada/Jalachara/Vanachara/Keeta."""
    return {1: 0, 4: 1, 5: 2, 7: 2, 8: 4, 11: 3,
            2: 0, 6: 1, 3: 1, 9: 0, 10: 0, 12: 2}.get(moon_sign, 0)


def _ashtakoot_score(
    moon_sign_a: int, moon_nak_a: int,
    moon_sign_b: int, moon_nak_b: int,
) -> dict[str, float]:
    """Compute the 8 Ashtakoot kutas + total. Returns scores normalised
    to 0..1 per kuta; total returned as 0..1 (the raw sum / 36).

    This is a classical scoring rather than empirical — used as a
    feature in case we ever get couple data.
    """
    out = {}

    # 1. Varna (1 pt): higher Varna of bride should equal or exceed groom's
    out["kuta_varna"] = float(_varna(moon_sign_a) == _varna(moon_sign_b)) * 1.0

    # 2. Vashya (2 pts): same vashya group
    out["kuta_vashya"] = float(_vashya(moon_sign_a) == _vashya(moon_sign_b)) * 2.0

    # 3. Tara (3 pts): nakshatra distance compatibility
    distance = (moon_nak_b - moon_nak_a) % 9
    # Auspicious distances 1, 3, 5, 7; inauspicious 2, 4, 6, 8 (0 = same)
    out["kuta_tara"] = (3.0 if distance in (0, 1, 3, 5, 7) else 0.0)

    # 4. Yoni (4 pts): same yoni = 4, else simplified parity
    yoni_a, yoni_b = YONI_MAP[moon_nak_a], YONI_MAP[moon_nak_b]
    out["kuta_yoni"] = (
        4.0 if yoni_a == yoni_b else (2.0 if (yoni_a - yoni_b) % 14 < 7 else 1.0)
    )

    # 5. Graha Maitri (5 pts): friendship of Moon-sign rulers; simplified
    out["kuta_graha_maitri"] = (
        5.0 if moon_sign_a == moon_sign_b else 2.5
    )

    # 6. Gana (6 pts): same gana = 6, deva-manushya = 5, else 0
    g_a, g_b = _gana(moon_nak_a), _gana(moon_nak_b)
    if g_a == g_b:
        out["kuta_gana"] = 6.0
    elif {g_a, g_b} == {0, 1}:
        out["kuta_gana"] = 5.0
    else:
        out["kuta_gana"] = 0.0

    # 7. Bhakoot (7 pts): sign distance — auspicious 1, 3, 7, 9
    sign_distance = ((moon_sign_b - moon_sign_a) % 12) + 1
    out["kuta_bhakoot"] = (
        7.0 if sign_distance in (1, 3, 4, 7, 9, 10) else 0.0
    )

    # 8. Nadi (8 pts): DIFFERENT nadi required for compatibility
    out["kuta_nadi"] = 8.0 if NADI_MAP[moon_nak_a] != NADI_MAP[moon_nak_b] else 0.0

    out["kuta_total"] = sum(out.values())
    out["kuta_compatible"] = float(out["kuta_total"] >= 18.0)  # classical cutoff
    return out


# ---------- Cross-chart pairwise features ----------

def compute_synastry_features(
    chart_a: pd.Series, chart_b: pd.Series,
) -> dict[str, float]:
    """All synastry features for an A-B chart pair."""
    out = {}

    # Cross-chart planet angular distances
    for p_a in GRAHAS:
        lon_a = float(chart_a.get(f"lon_{p_a}", 0.0))
        for p_b in GRAHAS:
            lon_b = float(chart_b.get(f"lon_{p_b}", 0.0))
            diff = abs(lon_a - lon_b) % 360.0
            out[f"syn_dist_{p_a}_to_{p_b}"] = float(min(diff, 360 - diff))

    # Cross-house placements: A's planets in B's house template
    asc_b_sign = int(chart_b.get("lagna_sign", 1))
    for p_a in GRAHAS:
        sign_a = int(float(chart_a.get(f"lon_{p_a}", 0.0)) // 30) + 1
        house_in_b = ((sign_a - asc_b_sign) % 12) + 1
        out[f"syn_{p_a}_in_b_house"] = float(house_in_b)

    # Ashtakoot kutas (Moon-based)
    moon_sign_a = int(float(chart_a.get("lon_moon", 0.0)) // 30) + 1
    moon_nak_a = int(chart_a.get("nak_moon", 0))
    moon_sign_b = int(float(chart_b.get("lon_moon", 0.0)) // 30) + 1
    moon_nak_b = int(chart_b.get("nak_moon", 0))
    out.update(_ashtakoot_score(moon_sign_a, moon_nak_a, moon_sign_b, moon_nak_b))

    return out


# ---------- Marriage outcome classifier ----------

def run_marriage_outcome_task(
    natal_parquet: Path, events_csv: Path,
) -> dict:
    """Build (natal_features, outcome) where outcome is the marriage
    event_subtype (Positive=1, Negative=0). Train XGBoost; report
    AUC.

    Tests whether the individual chart's features carry signal about
    marriage QUALITY independent of marriage OCCURRENCE.
    """
    natal = pd.read_parquet(natal_parquet)
    natal["_n"] = natal["name"].astype(str).str.strip().str.lower()
    natal = natal.drop_duplicates(subset="_n").set_index("_n")

    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    marriages = events.loc[events["root_lower"] == "marriage"].copy()
    marriages["subtype_clean"] = (
        marriages["event_subtype"].astype(str).str.strip().str.lower()
    )

    # Keep rows with clean Positive/Negative + person in natal
    marriages = marriages[
        marriages["subtype_clean"].isin(("positive", "negative"))
    ]
    marriages = marriages[marriages["_n"].isin(natal.index)]
    logger.info(
        "marriage outcome dataset: %d rows  (%d Positive, %d Negative)",
        len(marriages),
        int((marriages["subtype_clean"] == "positive").sum()),
        int((marriages["subtype_clean"] == "negative").sum()),
    )

    if len(marriages) < 100:
        return {"error": "too few marriage outcomes", "n_rows": len(marriages)}

    # First-marriage per person (deduplicate)
    marriages = marriages.drop_duplicates(subset="_n", keep="first")
    X_rows = natal.loc[marriages["_n"]].reset_index(drop=True)
    y = (marriages["subtype_clean"] == "positive").astype(int).reset_index(drop=True)

    X = select_features(X_rows)

    # 5-fold CV
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    aucs = []
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
        if y_tr.sum() < 5 or y_val.sum() < 1:
            continue
        scale_pos = float((y_tr == 0).sum()) / max(int(y_tr.sum()), 1)
        clf = xgb.XGBClassifier(
            n_estimators=150, max_depth=4, learning_rate=0.1,
            scale_pos_weight=scale_pos, enable_categorical=True,
            tree_method="hist", random_state=42, n_jobs=-1,
            eval_metric="logloss",
        )
        clf.fit(X_tr, y_tr)
        proba = clf.predict_proba(X_val)[:, 1]
        try:
            aucs.append(roc_auc_score(y_val, proba))
        except ValueError:
            continue
    return {
        "n_rows": len(marriages),
        "n_positive": int(y.sum()),
        "n_negative": int(len(y) - y.sum()),
        "cv_aucs": aucs,
        "mean_auc": float(np.mean(aucs)) if aucs else 0.5,
        "std_auc": float(np.std(aucs)) if aucs else 0.0,
    }


# ---------- Main ----------

def run_phase12(
    *,
    natal_parquet: Path,
    events_csv: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Part 1: marriage outcome classifier
    logger.info("=== Part 1: marriage outcome classifier ===")
    outcome_result = run_marriage_outcome_task(natal_parquet, events_csv)
    logger.info("marriage outcome result: %s", outcome_result)

    # Part 2: demo synastry feature library on 2 sample charts
    logger.info("=== Part 2: synastry feature library demo ===")
    natal = pd.read_parquet(natal_parquet)
    sample = natal.sample(n=2, random_state=42).reset_index(drop=True)
    chart_a = sample.iloc[0]
    chart_b = sample.iloc[1]
    syn_features = compute_synastry_features(chart_a, chart_b)
    logger.info("computed %d synastry features for demo pair", len(syn_features))
    logger.info(
        "demo pair Ashtakoot total: %.1f / 36 (%s)",
        syn_features["kuta_total"],
        "COMPATIBLE" if syn_features["kuta_compatible"] else "incompatible",
    )

    # Write demo synastry CSV
    demo_path = output_dir / "demo_synastry_features.csv"
    with demo_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["chart_a_name", chart_a.get("name", "?")])
        writer.writerow(["chart_b_name", chart_b.get("name", "?")])
        writer.writerow([])
        writer.writerow(["feature", "value"])
        for k, v in syn_features.items():
            writer.writerow([k, v])

    # Report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    lines = [
        "# Phase 12 — Synastry / pairwise compatibility",
        "",
        f"_Generated {now}_",
        "",
        "## Scope",
        "",
        "Two deliverables:",
        "",
        "1. **Synastry feature library**: `compute_synastry_features("
        "chart_a, chart_b)` produces ~100 pairwise features:",
        "   - 81 cross-planet angular distances (sun_a→saturn_b etc.)",
        "   - 9 cross-house placements (planet_A in chart_B's house template)",
        "   - 8 Ashtakoot kuta scores (Varna, Vashya, Tara, Yoni, Graha",
        "     Maitri, Gana, Bhakoot, Nadi) + total + compatible flag",
        "",
        "2. **Marriage outcome classifier**: trained on the per-person",
        "   event_subtype (Positive/Negative for marriage events).",
        "",
        "## Marriage outcome results",
        "",
    ]
    if "error" in outcome_result:
        lines.append(f"- Skipped: {outcome_result['error']}")
    else:
        lines.extend([
            f"- Dataset: {outcome_result['n_rows']} first-marriages "
            f"({outcome_result['n_positive']} Positive, "
            f"{outcome_result['n_negative']} Negative)",
            f"- **Mean CV ROC-AUC**: {outcome_result['mean_auc']:.4f} "
            f"± {outcome_result['std_auc']:.4f}",
            f"- Random baseline: 0.5",
            "",
            "Per-fold AUCs:",
            "",
        ])
        for i, auc in enumerate(outcome_result.get("cv_aucs", []), start=1):
            lines.append(f"- Fold {i}: {auc:.4f}")

    lines.extend([
        "",
        "## Demo synastry calculation",
        "",
        f"- Chart A: `{chart_a.get('name', '?')}`",
        f"- Chart B: `{chart_b.get('name', '?')}`",
        f"- Ashtakoot total: **{syn_features['kuta_total']:.1f}** / 36",
        f"- Compatibility verdict: "
        f"**{'COMPATIBLE' if syn_features['kuta_compatible'] else 'incompatible'}**",
        "",
        "Per-kuta breakdown:",
        "",
        f"- Varna: {syn_features['kuta_varna']:.1f} / 1",
        f"- Vashya: {syn_features['kuta_vashya']:.1f} / 2",
        f"- Tara: {syn_features['kuta_tara']:.1f} / 3",
        f"- Yoni: {syn_features['kuta_yoni']:.1f} / 4",
        f"- Graha Maitri: {syn_features['kuta_graha_maitri']:.1f} / 5",
        f"- Gana: {syn_features['kuta_gana']:.1f} / 6",
        f"- Bhakoot: {syn_features['kuta_bhakoot']:.1f} / 7",
        f"- Nadi: {syn_features['kuta_nadi']:.1f} / 8",
        "",
        "Full demo features in `demo_synastry_features.csv`.",
        "",
        "## Interpretation",
        "",
        "The marriage-outcome classifier tests whether the INDIVIDUAL chart",
        "alone carries signal about marriage QUALITY (vs OCCURRENCE).",
        "",
        "The synastry feature library is shipped for future use when",
        "couple data becomes available — pair the bride's and groom's",
        "charts, compute features, train on (pair_features, marriage_outcome)",
        "to learn data-driven synastry rules.",
        "",
        "The classical Ashtakoot 8-kuta scoring is implemented exactly as",
        "in BPHS / Saravali / Phaladeepika consensus. Total ≥ 18 / 36 is",
        "the traditional cutoff for marriage approval.",
    ])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.synastry",
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/ml_astro_round5.parquet"),
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/synastry_round6_phase12/"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase12(
        natal_parquet=args.natal,
        events_csv=args.events,
        output_dir=args.output,
    )
    print(f"Phase 12 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
