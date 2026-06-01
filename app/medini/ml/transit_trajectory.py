"""Round 6 Phase 11: Transit trajectory models.

Captures the CONTINUOUS approach pattern of transits leading up to
an event, rather than the snapshot at the moment of the event. The
hypothesis: an event isn't triggered by a single instant; it builds
over weeks/months as a transit configuration APPROACHES exactness.

Approach
========
For each event, sample the transit chart at multiple offsets before
and after the event date:
  - 90 days before
  - 30 days before
  - day of event (existing snapshot in event_corpus)
  - 30 days after
  - 90 days after

We focus on a small set of slow-planet transit features that change
meaningfully over these windows:
  - Saturn longitude (~0.03°/day)
  - Jupiter longitude (~0.08°/day)
  - Rahu/Ketu (~0.05°/day)
  - Saturn-natal-planet cross_lon distance (sade-sati / sade-x phases)
  - Jupiter-natal-planet cross_lon distance

Each event now becomes a TIME SERIES of these features. We train a
small 1D CNN or temporal MLP to predict event-class from the
trajectory.

Comparison baseline: the same model on event-day snapshot alone.
If trajectory beats snapshot, then **temporal approach patterns
carry signal**.

Scope choice for CPU: compute trajectories for a SUBSET of the
corpus (say 3000 events) at 5 offsets × ~15 features = 75 cols per
event. Fast and demonstrative.
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
import swisseph as swe
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from app.medini.etl.lahiri_worker import init_worker
from app.medini.etl.feature_engineering import GRAHAS

logger = logging.getLogger(__name__)


# Offsets (days from event) at which to sample transit positions
OFFSETS_DAYS: tuple[int, ...] = (-90, -30, 0, 30, 90)

# Planets whose slow motion matters for trajectory analysis. Saturn,
# Jupiter, Rahu, Ketu are the obvious slow-mover candidates; Sun and
# Mars at slower speeds also relevant for some events.
TRAJECTORY_PLANETS: tuple[str, ...] = (
    "sun", "mars", "jupiter", "saturn", "rahu", "ketu",
)


# ---------- Transit sampling ----------

PLANET_SWE_IDS: dict[str, int] = {
    "sun": swe.SUN, "moon": swe.MOON, "mars": swe.MARS,
    "mercury": swe.MERCURY, "jupiter": swe.JUPITER,
    "venus": swe.VENUS, "saturn": swe.SATURN, "rahu": swe.MEAN_NODE,
}


def transit_longitude(jd: float, planet: str) -> float:
    """Sidereal longitude of one planet at a JD (Lahiri ayanamsa)."""
    if planet == "ketu":
        rahu = swe.calc_ut(jd, PLANET_SWE_IDS["rahu"],
                           swe.FLG_SIDEREAL)[0][0]
        return (rahu + 180.0) % 360.0
    return swe.calc_ut(jd, PLANET_SWE_IDS[planet], swe.FLG_SIDEREAL)[0][0]


def trajectory_features_for_event(
    natal_row: pd.Series, event_jd: float,
) -> dict[str, float]:
    """Compute trajectory features at OFFSETS_DAYS around event_jd.

    Per planet × per offset:
      - transit_lon at offset
      - cross_lon (transit - natal) at offset

    Plus dynamics:
      - slope of cross_lon over the [-90, +90] window
      - tightest cross_lon during the window (closest approach age)
    """
    out: dict[str, float] = {}
    natal_lons = {p: float(natal_row.get(f"lon_{p}", 0.0)) for p in TRAJECTORY_PLANETS}

    for planet in TRAJECTORY_PLANETS:
        natal_lon = natal_lons[planet]
        cross_series: list[float] = []
        for offset in OFFSETS_DAYS:
            jd = event_jd + offset
            t_lon = transit_longitude(jd, planet)
            diff = abs(t_lon - natal_lon) % 360.0
            cross = min(diff, 360.0 - diff)
            out[f"traj_t_lon_{planet}_d{offset:+d}"] = t_lon
            out[f"traj_cross_{planet}_d{offset:+d}"] = cross
            cross_series.append(cross)
        # Slope (linear fit over the window) — captures approach vs separation
        x = np.array(OFFSETS_DAYS, dtype=float)
        y = np.array(cross_series, dtype=float)
        if y.std() > 1e-6:
            slope = float(np.polyfit(x, y, 1)[0])
        else:
            slope = 0.0
        out[f"traj_slope_{planet}"] = slope
        out[f"traj_min_cross_{planet}"] = float(min(cross_series))
        out[f"traj_at_event_cross_{planet}"] = cross_series[
            OFFSETS_DAYS.index(0)
        ]
    return out


# ---------- Main ----------

def run_phase11(
    *,
    corpus_parquet: Path,
    raw_csv: Path,
    output_dir: Path,
    max_events: int = 3000,
    classes: list[str] | None = None,
    seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    init_worker()

    logger.info("loading event corpus + raw birth data ...")
    df = pd.read_parquet(corpus_parquet)
    df["_label"] = df["event_root"].astype(str).str.lower().str.strip()

    if classes is None:
        counts = df["_label"].value_counts()
        classes = [c for c, n in counts.items() if n >= 300][:6]
    logger.info("classes: %s", classes)

    # Subsample for compute budget
    rng = np.random.default_rng(seed)
    sampled_idx = rng.choice(
        len(df), size=min(max_events, len(df)), replace=False,
    )
    df_sub = df.iloc[sampled_idx].reset_index(drop=True)
    logger.info("subsampled to %d events for trajectory compute", len(df_sub))

    logger.info("computing trajectory features ...")
    trajectory_rows: list[dict[str, float]] = []
    for i, row in df_sub.iterrows():
        event_jd = float(row.get("event_jd", 0.0))
        if event_jd <= 0:
            trajectory_rows.append({})
            continue
        try:
            feats = trajectory_features_for_event(row, event_jd)
            trajectory_rows.append(feats)
        except Exception as exc:
            logger.warning("trajectory failed for row %d: %s", i, exc)
            trajectory_rows.append({})
        if (i + 1) % 500 == 0:
            logger.info("  %d / %d events processed", i + 1, len(df_sub))

    trajectory_df = pd.DataFrame(trajectory_rows).fillna(0.0)
    logger.info("trajectory features shape: %s", trajectory_df.shape)

    # Snapshot baseline = the at-event cross_lon_* cols already in the corpus
    snapshot_cols = [c for c in df_sub.columns if c.startswith("cross_lon_")]
    snapshot_df = df_sub[snapshot_cols].fillna(0.0).copy()

    summary = []
    for class_name in classes:
        y = (df_sub["_label"] == class_name).astype(int)
        n_pos = int(y.sum())
        if n_pos < 30:
            logger.warning("skip %s: only %d positives", class_name, n_pos)
            continue
        logger.info("=== %s (n_pos=%d) ===", class_name, n_pos)

        # Snapshot baseline
        try:
            X_tr, X_val, y_tr, y_val = train_test_split(
                snapshot_df.to_numpy(), y.to_numpy(),
                test_size=0.25, stratify=y, random_state=seed,
            )
            clf = xgb.XGBClassifier(
                n_estimators=100, max_depth=4, learning_rate=0.1,
                scale_pos_weight=float((y_tr == 0).sum()) / max(int(y_tr.sum()), 1),
                tree_method="hist", random_state=seed, n_jobs=-1,
                eval_metric="logloss",
            )
            clf.fit(X_tr, y_tr)
            proba = clf.predict_proba(X_val)[:, 1]
            auc_snapshot = float(roc_auc_score(y_val, proba))
        except Exception as exc:
            logger.warning("snapshot eval failed: %s", exc)
            auc_snapshot = 0.5

        # Trajectory
        try:
            X_tr, X_val, y_tr, y_val = train_test_split(
                trajectory_df.to_numpy(), y.to_numpy(),
                test_size=0.25, stratify=y, random_state=seed,
            )
            clf = xgb.XGBClassifier(
                n_estimators=100, max_depth=4, learning_rate=0.1,
                scale_pos_weight=float((y_tr == 0).sum()) / max(int(y_tr.sum()), 1),
                tree_method="hist", random_state=seed, n_jobs=-1,
                eval_metric="logloss",
            )
            clf.fit(X_tr, y_tr)
            proba = clf.predict_proba(X_val)[:, 1]
            auc_trajectory = float(roc_auc_score(y_val, proba))
        except Exception as exc:
            logger.warning("trajectory eval failed: %s", exc)
            auc_trajectory = 0.5

        logger.info(
            "  snapshot=%.4f  trajectory=%.4f  delta=%+.4f",
            auc_snapshot, auc_trajectory, auc_trajectory - auc_snapshot,
        )
        summary.append({
            "class": class_name,
            "n_pos": n_pos,
            "auc_snapshot": auc_snapshot,
            "auc_trajectory": auc_trajectory,
            "delta": auc_trajectory - auc_snapshot,
        })

    csv_path = output_dir / "trajectory_scorecard.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(summary[0].keys()) if summary else ["class"],
        )
        writer.writeheader()
        for r in summary:
            writer.writerow(r)

    # Report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    lines = [
        "# Phase 11 — Transit trajectory models",
        "",
        f"_Generated {now}_",
        "",
        "## Setup",
        f"- Subsampled events: {len(df_sub):,}",
        f"- Trajectory offsets: {OFFSETS_DAYS} days from event",
        f"- Trajectory planets: {', '.join(TRAJECTORY_PLANETS)}",
        f"- Trajectory feature cols: {trajectory_df.shape[1]}",
        f"- Snapshot baseline cols: {len(snapshot_cols)} "
        "(cross_lon_* from event corpus)",
        "",
        "## Per-class comparison",
        "",
        "| Class | N pos | Snapshot AUC | Trajectory AUC | Δ |",
        "|---|---|---|---|---|",
    ]
    for s in sorted(summary, key=lambda r: -r["delta"]):
        lines.append(
            f"| {s['class']} | {s['n_pos']} | {s['auc_snapshot']:.4f} | "
            f"{s['auc_trajectory']:.4f} | {s['delta']:+.4f} |"
        )

    if summary:
        mean_snap = float(np.mean([s["auc_snapshot"] for s in summary]))
        mean_traj = float(np.mean([s["auc_trajectory"] for s in summary]))
        lines.extend([
            "",
            "## Aggregate",
            "",
            f"- Snapshot mean AUC:   {mean_snap:.4f}",
            f"- Trajectory mean AUC: {mean_traj:.4f}",
            f"- Delta: {mean_traj - mean_snap:+.4f}",
            "",
            "## Verdict",
            "",
        ])
        if mean_traj > mean_snap + 0.01:
            lines.append(
                f"**Trajectory wins** by {mean_traj - mean_snap:+.4f}. The "
                f"approach pattern of transits (90 days before through 90 "
                f"days after) carries information beyond the snapshot at "
                f"the event moment. Events build up over weeks; the "
                f"continuous trajectory captures that build-up."
            )
        elif mean_snap > mean_traj + 0.01:
            lines.append(
                f"Snapshot wins by {mean_snap - mean_traj:+.4f}. The event-"
                f"moment configuration is more informative than the "
                f"surrounding trajectory pattern at this granularity."
            )
        else:
            lines.append(
                "Trajectory and snapshot are within noise. At ±90-day "
                "sampling resolution, the approach pattern doesn't add "
                "much beyond the snapshot."
            )

    lines.extend([
        "",
        "## Caveats",
        "",
        "- Trajectory features focus on slow planets (Sun/Mars/Jupiter/",
        "  Saturn/Rahu/Ketu) — fast planets change too much in 30 days",
        "  for the offsets to be coherent samples of the same",
        "  configuration.",
        "- Finer offsets (e.g. ±7 days) would capture short-cycle",
        "  triggers (Mars transit, lunar phase). Tradeoff: more cols.",
        "- This is a baseline trajectory model. A proper Neural ODE or",
        "  TCN on hourly-resolution transit timelines would be the",
        "  full continuous-time hazard model.",
    ])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.transit_trajectory",
    )
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("app/medini/data/event_corpus_round5_all.parquet"),
    )
    parser.add_argument(
        "--raw", type=Path,
        default=Path("data/astro_databank/merged_with_events.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/trajectory_round6_phase11/"),
    )
    parser.add_argument("--max-events", type=int, default=3000)
    parser.add_argument(
        "--classes", type=str, nargs="*", default=None,
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase11(
        corpus_parquet=args.corpus,
        raw_csv=args.raw,
        output_dir=args.output,
        max_events=args.max_events,
        classes=args.classes,
    )
    print(f"Phase 11 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
