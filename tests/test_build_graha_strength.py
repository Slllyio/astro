"""Tests for the graha_strength (Shadbala) builder."""
from __future__ import annotations

import pandas as pd

from app.medini.etl.build_graha_strength import _GRAHAS, _person_strength_rows

_ALL = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")


def _chart_row() -> pd.Series:
    # Spread grahas across distinct longitudes/houses so each is computable.
    data = {"person_id": "p1", "asc_sign": 1}
    for i, g in enumerate(_ALL):
        lon = (i * 37.5) % 360.0
        data[f"{g}_lon"] = lon
        data[f"{g}_sign"] = int(lon // 30) + 1
        data[f"{g}_house"] = (int(lon // 30) % 12) + 1
    return pd.Series(data)


def test_seven_grahas_ranked() -> None:
    rows = _person_strength_rows(("p1", _chart_row()))
    assert len(rows) == 7                       # nodes excluded
    assert {r["graha"] for r in rows} == set(_GRAHAS)
    ranks = sorted(r["rank"] for r in rows)
    assert ranks == list(range(1, 8))           # contiguous 1..7
    # rank 1 has the max virupa
    top = next(r for r in rows if r["rank"] == 1)
    assert top["shadbala_virupa"] == max(r["shadbala_virupa"] for r in rows)


def test_rupa_is_virupa_over_60_and_components_present() -> None:
    rows = _person_strength_rows(("p1", _chart_row()))
    r = rows[0]
    assert r["shadbala_rupa"] == round(r["shadbala_virupa"] / 60.0, 4)
    for comp in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik"):
        assert comp in r
