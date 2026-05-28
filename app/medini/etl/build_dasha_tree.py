"""Phase 5 - Build the BPHS-faithful dasha tree (MD<->AD mutual relations).

The bphs-doctrine-reviewer agent flagged that the bare ``(person, MD, AD,
PD)`` Cartesian rows in ``dasha_windows.parquet`` store the *labels* but
NOT the *mutual relations* that BPHS Ch.46-47 says drive antardasha
effects. Specifically the doctrine claims:

  AD effect = f(MD-lord's placement, AD-lord's placement,
                MD <-> AD mutual relation: house-distance, mutual
                drishti, mutual reception / dispositor match)

This module materialises those mutual relations as columns on each
(person, MD, AD) row. Downstream Graph-NN / Cox / DeepHit can consume
the resulting parquet directly.

Output schema (dasha_tree.parquet):
  window_id                TEXT  FK -> dasha_windows
  person_id                TEXT  FK -> persons
  md_lord                  TEXT
  ad_lord                  TEXT
  md_seq, ad_seq           INT
  md_lord_house            INT   1..12 — house occupied by MD lord
  md_lord_sign             INT   1..12 — sign occupied by MD lord
  ad_lord_house            INT
  ad_lord_sign             INT
  mutual_house_distance    INT   1..12 — whole-sign distance MD-sign -> AD-sign
  mutual_aspect_md_to_ad   INT   0 or aspect-distance if MD lord casts drishti on AD lord
  mutual_aspect_ad_to_md   INT   0 or aspect-distance if AD lord casts drishti on MD lord
  md_dispositor            TEXT  the planet that rules MD lord's sign
  ad_dispositor            TEXT
  dispositor_md_is_ad      BOOL  AD lord is MD lord's dispositor (mutual reception clue)
  dispositor_ad_is_md      BOOL  MD lord is AD lord's dispositor

Usage:
    python -m app.medini.etl.build_dasha_tree
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

from app.core.avastha import _DRISHTI_HOUSES
from app.medini.etl.build_chart_heterograph import GRAHAS, _SIGN_RULERSHIP

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
DASHA_WINDOWS_FILE: Final = "dasha_windows.parquet"
CHARTS_FILE: Final = "charts.parquet"
OUTPUT_FILE: Final = "dasha_tree.parquet"

# Vimshottari lord names (canonical "Title" form) and lowercase column form.
_LORD_COL: Final[dict[str, str]] = {g: g.lower() for g in GRAHAS}


def _lookup_lord_placement(
    df: pd.DataFrame, lord_col: str, charts: pd.DataFrame, suffix: str,
) -> pd.DataFrame:
    """Add ``{suffix}_house`` and ``{suffix}_sign`` for the lord named in ``lord_col``.

    df must already be merged with charts (so each row has all 9 planet
    columns available). The lookup picks the right column per row based
    on the lord name in ``lord_col``.
    """
    # Vectorised lookup: for each Graha G, where lord_col == G,
    # copy charts."{g}_house" -> df."{suffix}_house".
    df[f"{suffix}_house"] = pd.Series(index=df.index, dtype="Int64")
    df[f"{suffix}_sign"] = pd.Series(index=df.index, dtype="Int64")
    for graha, col_prefix in _LORD_COL.items():
        mask = df[lord_col] == graha
        df.loc[mask, f"{suffix}_house"] = df.loc[mask, f"{col_prefix}_house"].astype("Int64")
        df.loc[mask, f"{suffix}_sign"] = df.loc[mask, f"{col_prefix}_sign"].astype("Int64")
    return df


def _mutual_aspect_column(
    df: pd.DataFrame, src_lord_col: str, distance_col: str,
) -> pd.Series:
    """For each row, return the drishti aspect-distance if src lord aspects target.

    Returns 0 if the distance is not in src lord's drishti house set,
    else returns the matching aspect-distance integer (3, 5, 7, 9, etc.)
    so downstream code can distinguish aspect TYPES.
    """
    out = pd.Series(0, index=df.index, dtype="int64")
    for graha, houses in _DRISHTI_HOUSES.items():
        mask = (df[src_lord_col] == graha) & df[distance_col].isin(houses)
        # Where the mask hits, store the actual distance (a member of houses).
        out.loc[mask] = df.loc[mask, distance_col].astype("int64")
    return out


def build_dasha_tree(
    dasha_windows: pd.DataFrame, charts: pd.DataFrame,
) -> pd.DataFrame:
    """Compute the mutual-relation features for every (person, MD, AD) row."""
    # Select only the chart columns we need to limit memory.
    chart_cols = ["person_id"]
    for g in _LORD_COL.values():
        chart_cols.extend([f"{g}_house", f"{g}_sign"])
    merged = dasha_windows.merge(charts[chart_cols], on="person_id", how="left")

    # Look up MD lord and AD lord placements.
    merged = _lookup_lord_placement(merged, "md_lord", charts, "md_lord")
    merged = _lookup_lord_placement(merged, "ad_lord", charts, "ad_lord")

    # Whole-sign distance from MD lord's sign to AD lord's sign. 1..12,
    # where 1 = conjunction (same sign), 7 = opposition.
    merged["mutual_house_distance"] = (
        ((merged["ad_lord_sign"] - merged["md_lord_sign"]) % 12) + 1
    ).astype("Int64")

    # Mutual aspects: does MD-lord cast drishti on AD-lord and vice versa?
    merged["mutual_aspect_md_to_ad"] = _mutual_aspect_column(
        merged, "md_lord", "mutual_house_distance",
    )
    # For AD -> MD, the distance is reversed.
    merged["distance_ad_to_md"] = (
        ((merged["md_lord_sign"] - merged["ad_lord_sign"]) % 12) + 1
    ).astype("Int64")
    merged["mutual_aspect_ad_to_md"] = _mutual_aspect_column(
        merged, "ad_lord", "distance_ad_to_md",
    )

    # Dispositor matching (BPHS reception logic).
    # md_dispositor = ruler of the sign MD lord is in.
    sign_ruler_lookup = {(s + 1): r for s, r in _SIGN_RULERSHIP.items()}  # 1-indexed
    merged["md_dispositor"] = merged["md_lord_sign"].map(sign_ruler_lookup)
    merged["ad_dispositor"] = merged["ad_lord_sign"].map(sign_ruler_lookup)
    merged["dispositor_md_is_ad"] = (merged["md_dispositor"] == merged["ad_lord"])
    merged["dispositor_ad_is_md"] = (merged["ad_dispositor"] == merged["md_lord"])

    # Drop the wide planet columns; keep only what the tree needs.
    keep = [
        "window_id", "person_id", "md_lord", "ad_lord", "md_seq", "ad_seq",
        "md_lord_house", "md_lord_sign", "ad_lord_house", "ad_lord_sign",
        "mutual_house_distance",
        "mutual_aspect_md_to_ad", "mutual_aspect_ad_to_md",
        "md_dispositor", "ad_dispositor",
        "dispositor_md_is_ad", "dispositor_ad_is_md",
    ]
    return merged[keep]


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    dasha_windows = pd.read_parquet(args.data_dir / DASHA_WINDOWS_FILE)
    charts = pd.read_parquet(args.data_dir / CHARTS_FILE)
    logger.info("Loaded %d dasha_windows, %d charts", len(dasha_windows), len(charts))

    tree = build_dasha_tree(dasha_windows, charts)
    out_path = args.data_dir / OUTPUT_FILE
    tree.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows to %s", len(tree), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
