"""Tests for D9 (Navamsa) chart construction from birth JD."""
from __future__ import annotations

import pandas as pd

from app.medini.etl.build_d9_charts import _GRAHAS, build, d9_row, d9_sign


def test_d9_sign_range_and_known_pada() -> None:
    # First navamsa of Aries (0–3.33°, fire sign) starts at Aries → sign 1.
    assert d9_sign(0.0) == 1
    assert d9_sign(1.0) == 1
    # Second navamsa of Aries → Taurus → sign 2.
    assert d9_sign(3.5) == 2
    # all outputs are valid signs
    for lon in (0.0, 45.0, 123.4, 270.0, 359.9):
        assert 1 <= d9_sign(lon) <= 12


def test_d9_row_has_all_grahas() -> None:
    # Use a plausible modern JD; just check structure + ranges, not values.
    row = d9_row(2451545.0)  # J2000
    assert set(row) == {f"{g.lower()}_d9_sign" for g in _GRAHAS}
    assert all(1 <= v <= 12 for v in row.values())


def test_build_skips_missing_jd_and_keeps_person_id() -> None:
    charts = pd.DataFrame([
        {"person_id": "p1", "birth_jd_used": 2451545.0},
        {"person_id": "p2", "birth_jd_used": None},
    ])
    out = build(charts)
    assert list(out["person_id"]) == ["p1"]
    assert "venus_d9_sign" in out.columns
