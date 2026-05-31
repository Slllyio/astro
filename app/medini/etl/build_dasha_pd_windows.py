"""Build the PD (pratyantar) level dasha windows.

Completes the Vimshottari hierarchy from MD/AD (in ``dasha_windows.parquet``)
to MD/AD/PD. Each AD window contains 9 PD sub-periods. Each PD's duration
is proportional to its lord's Vimshottari tenure scaled by the parent AD:

    PD_years = AD_total_years × PD_lord_years / 120

The PD sequence within an AD starts with the AD lord itself, then proceeds
through the canonical Vimshottari order (Ketu → Venus → Sun → Moon → Mars →
Rahu → Jupiter → Saturn → Mercury, wrapping).

## Output schema (dasha_pd_windows.parquet)

  pd_window_id    TEXT  -- "{person_id}::MD::{md}::AD::{ad}::PD::{pd}::{md_seq}::{ad_seq}::{pd_seq}"
  person_id       TEXT  -- FK → persons.parquet
  md_lord, ad_lord, pd_lord  TEXT  -- the three nested lords
  md_seq, ad_seq, pd_seq     INT   -- indices into each level
  start_jd        FLOAT64  -- Julian Day of PD start
  end_jd          FLOAT64  -- Julian Day of PD end
  duration_days   FLOAT64  -- end_jd - start_jd

## Scale

For 75,149 persons × 729 PDs (9 MD × 9 AD × 9 PD) = ~54.8M rows.
Compressed parquet: roughly 800-900 MB.

This is the heaviest table in the Silver layer. Most experiments do NOT
need PD precision; they read ``dasha_windows.parquet`` (6M rows) instead.
PD is useful for:
  - BPHS Ch.55 sub-period doctrine application
  - Per-person deterministic reading systems
  - Sub-AD temporal precision in event timing

Usage:
    python -m app.medini.etl.build_dasha_pd_windows
    python -m app.medini.etl.build_dasha_pd_windows --workers 6
"""
from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Final, Any

import pandas as pd

from app.core.ephemeris_engine import DASHA_LORDS, DAYS_PER_VEDIC_YEAR

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
INPUT_FILE: Final = "dasha_windows.parquet"
OUTPUT_FILE: Final = "dasha_pd_windows.parquet"

_LORD_NAMES: Final[tuple[str, ...]] = tuple(name for name, _ in DASHA_LORDS)
_LORD_YEARS: Final[dict[str, int]] = dict(DASHA_LORDS)
_TOTAL_VIMSHOTTARI_YEARS: Final = 120


def _pratyantars_in_ad(
    ad_lord: str, ad_start_jd: float, ad_duration_years: float,
) -> list[tuple[str, float, float]]:
    """Expand one AD into its 9 PDs.

    Same Vimshottari nesting rule as AD-within-MD: the PD sequence starts
    with the AD lord itself, then proceeds through the canonical order.
    Each PD's length is proportional to its lord's Vimshottari tenure
    scaled by the parent AD's length.

    Returns: list of (pd_lord, pd_start_jd, pd_end_jd) tuples.
    """
    start_idx = _LORD_NAMES.index(ad_lord)
    cursor = ad_start_jd
    out: list[tuple[str, float, float]] = []
    for offset in range(len(_LORD_NAMES)):
        pd_lord = _LORD_NAMES[(start_idx + offset) % len(_LORD_NAMES)]
        pd_years = (
            ad_duration_years
            * _LORD_YEARS[pd_lord]
            / _TOTAL_VIMSHOTTARI_YEARS
        )
        pd_end = cursor + pd_years * DAYS_PER_VEDIC_YEAR
        out.append((pd_lord, cursor, pd_end))
        cursor = pd_end
    return out


def _pds_for_one_ad_row(args: tuple) -> list[dict[str, Any]]:
    """Worker function: expand one AD-window row to 9 PD-window rows.

    Doctrinal note: the natural key of a PD window is
    ``(person_id, md_seq, ad_seq, pd_seq)`` — these four values uniquely
    identify the window without ambiguity. Earlier versions of this
    script also emitted a derived ``pd_window_id`` string column
    (concatenation of all the lord names + seqs); database-optimizer
    audit found it consumed 562 MB / 38.9% of the file's pre-ZSTD size
    while being literally unused outside of one uniqueness test. Drop.
    """
    person_id, md_lord, ad_lord, md_seq, ad_seq, start_jd, end_jd = args
    duration_days = end_jd - start_jd
    ad_duration_years = duration_days / DAYS_PER_VEDIC_YEAR
    rows: list[dict[str, Any]] = []
    for pd_seq, (pd_lord, pd_start, pd_end) in enumerate(
        _pratyantars_in_ad(ad_lord, start_jd, ad_duration_years)
    ):
        rows.append({
            "person_id": person_id,
            "md_lord": md_lord,
            "ad_lord": ad_lord,
            "pd_lord": pd_lord,
            "md_seq": md_seq,
            "ad_seq": ad_seq,
            "pd_seq": pd_seq,
            "start_jd": pd_start,
            "end_jd": pd_end,
            "duration_days": pd_end - pd_start,
        })
    return rows


def build_pd_windows(
    dasha_windows: pd.DataFrame, workers: int = 1,
) -> pd.DataFrame:
    """Expand every (person, MD, AD) row to its 9 PD windows.

    Input: dasha_windows.parquet schema (one row per (person, MD, AD)).
    Output: 9× the row count (one row per (person, MD, AD, PD)).
    """
    inputs = list(zip(
        dasha_windows["person_id"].tolist(),
        dasha_windows["md_lord"].tolist(),
        dasha_windows["ad_lord"].tolist(),
        dasha_windows["md_seq"].tolist(),
        dasha_windows["ad_seq"].tolist(),
        dasha_windows["start_jd"].tolist(),
        dasha_windows["end_jd"].tolist(),
    ))
    if workers > 1:
        with mp.Pool(workers) as pool:
            chunks = list(pool.imap_unordered(
                _pds_for_one_ad_row, inputs, chunksize=2048,
            ))
    else:
        chunks = [_pds_for_one_ad_row(t) for t in inputs]

    flat = [row for chunk in chunks for row in chunk]
    logger.info(
        "Built %d PD windows from %d AD windows (factor of %.2f)",
        len(flat), len(inputs), len(flat) / max(1, len(inputs)),
    )
    return pd.DataFrame(flat)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N AD rows (smoke test).")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--force", action="store_true",
                        help="Rebuild even if output is fresh vs inputs.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    from app.medini.etl._freshness import skip_if_fresh

    in_path = args.data_dir / INPUT_FILE
    out_path = args.data_dir / OUTPUT_FILE
    if args.limit is None and skip_if_fresh(out_path, [in_path], force=args.force):
        return 0

    dw = pd.read_parquet(in_path)
    if args.limit is not None:
        dw = dw.head(args.limit)
    logger.info("Loaded %d AD windows", len(dw))

    pd_df = build_pd_windows(dw, workers=args.workers)
    # Sort by (person_id, start_jd) so DuckDB ZONEMAP can eliminate row
    # groups for "active PD at JD X for person Y" queries. With 128K-row
    # row groups, a per-person query touches ~5 of 430 row groups instead
    # of all 53. Combined with the column drop above + ZSTD, this is the
    # biggest single-query speedup in the project.
    pd_df = pd_df.sort_values(["person_id", "start_jd"], kind="stable").reset_index(drop=True)
    from app.medini.etl._parquet_io import write_parquet_zstd
    import pyarrow as pa
    import pyarrow.parquet as pq
    table = pa.Table.from_pandas(pd_df, preserve_index=False)
    pq.write_table(
        table, out_path,
        compression="zstd", compression_level=3,
        row_group_size=128_000,
    )
    logger.info(
        "Wrote %d rows to %s (sorted by person_id, start_jd; row_group=128K; ZSTD)",
        len(pd_df), out_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
