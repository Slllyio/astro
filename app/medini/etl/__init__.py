"""Phase 5 ETL pipeline: Astro-Databank scraper -> feature engineering -> parquet.

Three sub-modules:
  - scraper.py: pulls biographical entries from Astro-Databank wiki (CLI).
  - databank_etl.py: filters AA-rated rows and computes Vedic features (CLI).
  - feature_engineering.py: pure functions for angular distances, etc.
  - lahiri_worker.py: per-process pyswisseph initializer for multiprocessing.

All four are import-safe (loading them does NOT trigger heavy work). Heavy
work happens in CLI entrypoints, which are run via `python -m`.
"""
