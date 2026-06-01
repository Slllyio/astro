"""One-shot: filter dasha_stage_d_features.parquet to the 2000-person subsample.

Reads the full materialized features (6.17M rows) and writes a new parquet
containing only rows whose name_norm is in dasha_subsample_2000_persons.parquet.
Expected ~1.2M rows on disk (~20 MB), ~2 GB in-memory.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

DATA = Path("app/medini/data")
FULL = DATA / "dasha_stage_d_features.parquet"
SAMPLE = DATA / "dasha_subsample_2000_persons.parquet"
OUT = DATA / "dasha_stage_d_features_subsample.parquet"


def main() -> None:
    t0 = time.time()
    print(f"Reading sample list: {SAMPLE}")
    sample = pd.read_parquet(SAMPLE)
    sample_set = set(sample["name_norm"])
    print(f"  {len(sample_set)} persons in sample")

    print(f"Reading full features: {FULL}")
    df = pd.read_parquet(FULL)
    print(f"  full: {len(df):,} rows x {df.shape[1]} cols")

    sub = df[df["name_norm"].isin(sample_set)].reset_index(drop=True)
    print(f"  filtered: {len(sub):,} rows ({len(sub)/len(df)*100:.1f}%)")
    n_persons = sub["name_norm"].nunique()
    print(f"  persons retained: {n_persons}")

    print(f"Writing: {OUT}")
    sub.to_parquet(OUT, index=False)
    sz = OUT.stat().st_size / (1024 * 1024)
    print(f"  wrote {sz:.1f} MB in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
