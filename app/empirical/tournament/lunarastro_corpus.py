"""Adapts the LunarAstro canonical corpus to the existing feature-bank builder.

``build_feature_banks.build_banks`` is corpus-agnostic — it only needs
``ChartRow`` objects (person_id, date, ut_hour, lat/lon, a label string,
time_tier, data_quality). The Gauquelin reader fills ``label`` with a single
profession code; this corpus instead carries a variable-length set of category
tags per person. Rather than force a single-label shape onto multi-label data,
``label`` here is the semicolon-joined, sorted set of that person's tags —
:mod:`run_screening_lunarastro` is the multi-label-aware consumer that knows to
split it back apart. ``build_banks`` itself never inspects ``label``'s
contents, so it needs no change at all.

Usage:
    from app.empirical.tournament.lunarastro_corpus import read_lunarastro_corpus
    rows = read_lunarastro_corpus("data/empirical/lunarastro.csv")
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.empirical.tournament.build_feature_banks import ChartRow

__all__ = ["read_lunarastro_corpus"]


def read_lunarastro_corpus(path: str | Path) -> list[ChartRow]:
    """Read the canonical LunarAstro CSV into ``ChartRow`` objects."""
    rows: list[ChartRow] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            categories = tuple(
                c.strip() for c in (raw.get("categories") or "").split(";") if c.strip()
            )
            rows.append(
                ChartRow(
                    person_id=raw["source_id"],
                    year=int(raw["birth_year"]),
                    month=int(raw["birth_month"]),
                    day=int(raw["birth_day"]),
                    ut_hour=float(raw["birth_ut_hour"]),
                    latitude=float(raw["latitude"]),
                    longitude=float(raw["longitude"]),
                    label=";".join(sorted(categories)),
                    time_tier=raw["time_tier"],
                    data_quality=raw["data_quality"],
                )
            )
    return rows
