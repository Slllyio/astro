"""Phase-3C ETL: inject the full 16-yoga catalog into a screening or event parquet.

Replaces ``add_harsha_feature.py`` (single-yoga wedge). For each row this
script reconstructs the minimal natal chart from existing parquet columns
(``lon_<planet>`` + ``lagna_sign``), runs all 16 Phase-3B detectors, and
appends:

* ``<yoga>_natal_strength`` — the YogaInstance.strength in ``[0, 1]`` (0.0
  if the yoga is absent).
* ``<yoga>_dasha_gated_strength`` — natal × dasha-activation, where
  activation = 1.0 if a participant/lord matches the maha-dasha lord, 0.5
  for the antar-dasha lord, 0.25 for the pratyantar-dasha lord, else 0.0.
  This column is only emitted when the input parquet carries
  ``active_md_lord`` / ``active_ad_lord`` / ``active_pd_lord`` (i.e.
  event-corpus rows). On the screening cohort the column is omitted, not
  zero-filled, so the wedge eval on each substrate sees the substrate's
  natural feature dimensionality.

Why this is Phase 3C (not Phase 0):
    The Round-9 plan's falsifiable gate. Phase-0 used one yoga to size
    the wedge; Phase 3C uses all 16 to measure whether the classical
    catalog as a whole carries signal above noise on either substrate.
    The companion ``wedge_eval_v2.py`` then does multi-seed + bootstrap
    CI + replication on the augmented parquet.

Usage:
    python -m app.medini.etl.add_yoga_features \\
        --input  app/medini/data/screening_career.parquet \\
        --output app/medini/data/screening_career_yogas.parquet

The 16 yogas (matching SESSION_SUMMARY_R9.md Phase 3B catalog):
    Vipareeta Harsha, Vipareeta Sarala, Vipareeta Vimala,
    Sunapha, Anapha, Durudhura, Kemadruma,
    Ruchaka, Bhadra, Hamsa, Malavya, Sasa,
    Gajakesari, Budha-Aditya, Raja Yoga, Dhana Yoga.
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.yoga_types import YogaInstance
from app.core.yogas import (
    detect_anapha,
    detect_budha_aditya_instance,
    detect_dhana_yoga,
    detect_durudhura,
    detect_gajakesari_instance,
    detect_kemadruma,
    detect_pancha_mahapurusha,
    detect_raja_yoga,
    detect_sunapha,
    detect_vipareeta_harsha,
    detect_vipareeta_sarala,
    detect_vipareeta_vimala,
)

logger = logging.getLogger(__name__)

_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


def _detect_ruchaka(chart: dict, asc: dict) -> YogaInstance | None:
    for inst in detect_pancha_mahapurusha(chart, asc):
        if inst.name == "Ruchaka":
            return inst
    return None


def _detect_bhadra(chart: dict, asc: dict) -> YogaInstance | None:
    for inst in detect_pancha_mahapurusha(chart, asc):
        if inst.name == "Bhadra":
            return inst
    return None


def _detect_hamsa(chart: dict, asc: dict) -> YogaInstance | None:
    for inst in detect_pancha_mahapurusha(chart, asc):
        if inst.name == "Hamsa":
            return inst
    return None


def _detect_malavya(chart: dict, asc: dict) -> YogaInstance | None:
    for inst in detect_pancha_mahapurusha(chart, asc):
        if inst.name == "Malavya":
            return inst
    return None


def _detect_sasa(chart: dict, asc: dict) -> YogaInstance | None:
    for inst in detect_pancha_mahapurusha(chart, asc):
        if inst.name == "Sasa":
            return inst
    return None


@dataclass(frozen=True, slots=True)
class _YogaSpec:
    slug: str
    detector: Callable[[dict, dict], YogaInstance | None]


# Column order is locked here so the ML harness sees a deterministic
# schema regardless of dict iteration ordering on older Pythons.
_YOGA_SPECS: tuple[_YogaSpec, ...] = (
    _YogaSpec("vipareeta_harsha", detect_vipareeta_harsha),
    _YogaSpec("vipareeta_sarala", detect_vipareeta_sarala),
    _YogaSpec("vipareeta_vimala", detect_vipareeta_vimala),
    _YogaSpec("sunapha",          detect_sunapha),
    _YogaSpec("anapha",           detect_anapha),
    _YogaSpec("durudhura",        detect_durudhura),
    _YogaSpec("kemadruma",        detect_kemadruma),
    _YogaSpec("ruchaka",          _detect_ruchaka),
    _YogaSpec("bhadra",           _detect_bhadra),
    _YogaSpec("hamsa",            _detect_hamsa),
    _YogaSpec("malavya",          _detect_malavya),
    _YogaSpec("sasa",             _detect_sasa),
    _YogaSpec("gajakesari",       detect_gajakesari_instance),
    _YogaSpec("budha_aditya",     detect_budha_aditya_instance),
    _YogaSpec("raja_yoga",        detect_raja_yoga),
    _YogaSpec("dhana_yoga",       detect_dhana_yoga),
)


# Dasha-activation weights — md is strongest, pd weakest. Matches the
# classical idea that maha-dasha sets the headline theme and sub-dashas
# modulate it.
_DASHA_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("active_md_lord", 1.0),
    ("active_ad_lord", 0.5),
    ("active_pd_lord", 0.25),
)


def _row_to_chart(row: pd.Series) -> tuple[dict, dict] | None:
    """Build (chart, ascendant) from a parquet row.

    Returns ``None`` when any required column is missing or non-finite —
    those rows get 0.0 across the whole 16-yoga vector.
    """
    asc_sign = row.get("lagna_sign")
    if not isinstance(asc_sign, (int, float)) or pd.isna(asc_sign):
        return None
    asc_sign = int(asc_sign)
    if not (1 <= asc_sign <= 12):
        return None

    chart: dict[str, dict] = {}
    for p in _PLANETS:
        lon = row.get(f"lon_{p.lower()}")
        if not isinstance(lon, (int, float)) or pd.isna(lon):
            return None
        lon = float(lon) % 360.0
        sign = int(lon // 30) + 1
        chart[p] = {
            "sign": sign,
            "longitude": lon,
            "degree_in_sign": lon % 30.0,
            # Retrograde isn't authoritative in either parquet; strength
            # scoring does not consume it for the Phase-3B catalog.
            "is_retrograde": False,
        }
    return chart, {"sign": asc_sign}


def _dasha_activation(instance: YogaInstance, row: pd.Series) -> float:
    """Compute the dasha-gating coefficient in ``[0, 1]`` for a yoga.

    The yoga's strength is multiplied by this coefficient to give the
    timing-gated column. A yoga whose participants/lords don't appear in
    any of the active md/ad/pd lords yields 0.0 (yoga is latent but
    not currently firing).
    """
    yoga_planets: set[str] = set(instance.participants) | set(instance.lords_involved)
    activation = 0.0
    for column, weight in _DASHA_WEIGHTS:
        lord = row.get(column)
        if not isinstance(lord, str):
            continue
        if lord in yoga_planets:
            activation = max(activation, weight)
    return activation


def _compute_row_features(
    row: pd.Series, has_dasha: bool
) -> dict[str, float]:
    """Run all 16 detectors and return the column dict for this row."""
    out: dict[str, float] = {}
    for spec in _YOGA_SPECS:
        out[f"{spec.slug}_natal_strength"] = 0.0
        if has_dasha:
            out[f"{spec.slug}_dasha_gated_strength"] = 0.0

    parsed = _row_to_chart(row)
    if parsed is None:
        return out
    chart, asc = parsed

    for spec in _YOGA_SPECS:
        instance = spec.detector(chart, asc)
        if instance is None:
            continue
        out[f"{spec.slug}_natal_strength"] = float(instance.strength)
        if has_dasha:
            activation = _dasha_activation(instance, row)
            out[f"{spec.slug}_dasha_gated_strength"] = (
                float(instance.strength) * activation
            )
    return out


def inject_yoga_features(input_path: Path, output_path: Path) -> dict[str, Any]:
    """Apply all 16 detectors row-wise and write the augmented parquet.

    Returns a summary dict suitable for sanity-checking before launching
    the wedge eval. Includes per-yoga prevalence and (when ``is_event_X``
    is present) pos-vs-neg mean-strength gaps.
    """
    df = pd.read_parquet(input_path)
    has_dasha = all(col in df.columns for col, _ in _DASHA_WEIGHTS)
    logger.info(
        "loaded %s shape=%s has_target=%s has_dasha=%s",
        input_path, df.shape,
        "is_event_X" in df.columns, has_dasha,
    )

    features_df = pd.DataFrame(
        [_compute_row_features(row, has_dasha) for _, row in df.iterrows()],
        index=df.index,
    )
    out_df = pd.concat([df, features_df], axis=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(output_path, index=False)
    logger.info("wrote %s shape=%s", output_path, out_df.shape)

    summary: dict[str, Any] = {
        "input": str(input_path),
        "output": str(output_path),
        "n_total": int(len(out_df)),
        "n_new_columns": int(features_df.shape[1]),
        "has_dasha_columns": bool(has_dasha),
        "per_yoga": {},
    }

    has_target = "is_event_X" in out_df.columns
    for spec in _YOGA_SPECS:
        col = f"{spec.slug}_natal_strength"
        series = out_df[col]
        present = int((series > 0).sum())
        per_yoga: dict[str, Any] = {
            "n_with_yoga": present,
            "prevalence_pct": round(100.0 * present / max(len(series), 1), 2),
            "mean_strength_all": round(float(series.mean()), 4),
        }
        if has_target:
            pos = out_df[out_df["is_event_X"] == 1][col]
            neg = out_df[out_df["is_event_X"] == 0][col]
            per_yoga["pos_mean_strength"] = round(float(pos.mean()), 4) if len(pos) else 0.0
            per_yoga["neg_mean_strength"] = round(float(neg.mean()), 4) if len(neg) else 0.0
            per_yoga["pos_yoga_rate_pct"] = round(
                100.0 * (pos > 0).sum() / max(len(pos), 1), 2
            )
            per_yoga["neg_yoga_rate_pct"] = round(
                100.0 * (neg > 0).sum() / max(len(neg), 1), 2
            )
        summary["per_yoga"][spec.slug] = per_yoga

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inject the 16-yoga catalog into a screening or event-corpus parquet."
    )
    parser.add_argument(
        "--input", required=True, type=Path,
        help="Path to input parquet (screening or event-corpus)",
    )
    parser.add_argument(
        "--output", required=True, type=Path,
        help="Path to write the augmented parquet",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not args.input.exists():
        logger.error("input not found: %s", args.input)
        return 2

    summary = inject_yoga_features(args.input, args.output)
    print(f"input:  {summary['input']}")
    print(f"output: {summary['output']}")
    print(f"n_total: {summary['n_total']}  new_cols: {summary['n_new_columns']}  "
          f"has_dasha: {summary['has_dasha_columns']}")
    print()
    print(f"{'yoga':<22} {'prev%':>7} {'mean':>8} {'pos_mean':>10} {'neg_mean':>10} {'gap':>8}")
    for slug, stats in summary["per_yoga"].items():
        pos = stats.get("pos_mean_strength", 0.0)
        neg = stats.get("neg_mean_strength", 0.0)
        gap = pos - neg
        print(
            f"{slug:<22} {stats['prevalence_pct']:>7.2f} "
            f"{stats['mean_strength_all']:>8.4f} {pos:>10.4f} {neg:>10.4f} {gap:>+8.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
