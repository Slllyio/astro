"""Tests for the Phase-3C ETL ``app.medini.etl.add_yoga_features``.

The ETL is the bridge between the Phase-3B yoga catalog and the wedge
eval. We exercise it on a tiny synthetic parquet that mirrors the
relevant parts of the screening-cohort and event-corpus schemas, to
verify:

* Column-set shape (16 natal + 16 dasha-gated when active_*_lord present;
  16 natal only otherwise).
* Dasha gating uses md=1.0 / ad=0.5 / pd=0.25 weights and zeroes out
  when no lord matches the yoga's participants/lords.
* Missing-longitude rows zero-fill cleanly rather than raising.
* Existing columns are passed through untouched.
* The summary dict reports per-yoga prevalence and pos-vs-neg means.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from app.medini.etl.add_yoga_features import (
    _YOGA_SPECS,
    inject_yoga_features,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

_PLANET_COLUMNS = (
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
)


def _mid_lon(sign: int) -> float:
    """Mid-sign tropical longitude in degrees (sign 1..12)."""
    return (sign - 1) * 30.0 + 15.0


def _vipareeta_harsha_row(*, is_event: int = 0) -> dict:
    """Row that produces Vipareeta Harsha: Aries lagna → 6L = Mercury → place in 6 (Virgo).

    Aries lagna means 6th house from lagna is Virgo; Virgo's lord is
    Mercury. Mercury sitting in Virgo (= 6 from lagna) is the textbook
    Harsha. We park all other planets in benign signs that won't trigger
    side-yogas in the 16-catalog (notably no Jupiter-Moon mutual kendra,
    no Sun-Mercury conjunction, no PMP own/exalted placement).
    """
    row: dict[str, float | int | str] = {
        "lagna_sign": 1,            # Aries
        "lon_sun": _mid_lon(5),     # Leo (sun's own sign — would fire PMP via Surya... but Sun is not PMP planet)
        "lon_moon": _mid_lon(2),    # Taurus (Moon's exaltation? exalt sign = Taurus)
        "lon_mars": _mid_lon(11),   # Aquarius — neither own nor exalted, not kendra-by-itself
        "lon_mercury": _mid_lon(6), # Virgo — 6L of Aries lagna in 6th — HARSHA fires
        "lon_jupiter": _mid_lon(8), # Scorpio
        "lon_venus": _mid_lon(11),  # Aquarius
        "lon_saturn": _mid_lon(3),  # Gemini
        "lon_rahu": _mid_lon(12),
        "lon_ketu": _mid_lon(6),
        "is_event_X": is_event,
    }
    return row


def _empty_row() -> dict:
    """Row with NaN longitudes — exercises the 'zero-fill cleanly' path."""
    row: dict[str, float | int | str] = {
        "lagna_sign": 1,
        "is_event_X": 0,
    }
    for p in _PLANET_COLUMNS:
        row[f"lon_{p}"] = math.nan
    return row


def _make_parquet(rows: list[dict], path: Path) -> Path:
    df = pd.DataFrame(rows)
    df.to_parquet(path, index=False)
    return path


# --------------------------------------------------------------------------- #
# Schema tests                                                                #
# --------------------------------------------------------------------------- #

def test_screening_schema_emits_16_natal_columns_no_dasha(tmp_path: Path) -> None:
    """A screening-cohort parquet (no active_*_lord) gets 16 natal columns only."""
    in_path = _make_parquet([_vipareeta_harsha_row()], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"

    summary = inject_yoga_features(in_path, out_path)

    assert summary["has_dasha_columns"] is False
    # 16 natal columns, no dasha-gated columns.
    assert summary["n_new_columns"] == 16

    out = pd.read_parquet(out_path)
    natal_cols = {f"{spec.slug}_natal_strength" for spec in _YOGA_SPECS}
    dasha_cols = {f"{spec.slug}_dasha_gated_strength" for spec in _YOGA_SPECS}
    assert natal_cols.issubset(set(out.columns))
    assert dasha_cols.isdisjoint(set(out.columns))


def test_event_corpus_schema_emits_32_columns_with_dasha(tmp_path: Path) -> None:
    """An event-corpus parquet (with active_*_lord) gets 16 natal + 16 dasha cols."""
    row = _vipareeta_harsha_row()
    row["active_md_lord"] = "Mercury"   # matches the Harsha participant
    row["active_ad_lord"] = "Mars"
    row["active_pd_lord"] = "Venus"
    in_path = _make_parquet([row], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"

    summary = inject_yoga_features(in_path, out_path)

    assert summary["has_dasha_columns"] is True
    assert summary["n_new_columns"] == 32

    out = pd.read_parquet(out_path)
    for spec in _YOGA_SPECS:
        assert f"{spec.slug}_natal_strength" in out.columns
        assert f"{spec.slug}_dasha_gated_strength" in out.columns


def test_existing_columns_pass_through(tmp_path: Path) -> None:
    """No upstream column should be silently dropped or renamed."""
    row = _vipareeta_harsha_row()
    row["birth_decade"] = 1980
    row["name_norm"] = "subject_a"
    in_path = _make_parquet([row], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"

    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    for c in ("lagna_sign", "lon_mercury", "is_event_X", "birth_decade", "name_norm"):
        assert c in out.columns
    # And values preserved
    assert out["birth_decade"].iloc[0] == 1980
    assert out["name_norm"].iloc[0] == "subject_a"


# --------------------------------------------------------------------------- #
# Detector wiring                                                             #
# --------------------------------------------------------------------------- #

def test_vipareeta_harsha_fires_on_aries_lagna_mercury_in_6th(tmp_path: Path) -> None:
    """The textbook Harsha chart yields strength > 0 in the harsha column."""
    in_path = _make_parquet([_vipareeta_harsha_row()], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"
    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    assert out["vipareeta_harsha_natal_strength"].iloc[0] > 0.0


def test_missing_longitudes_zero_fill(tmp_path: Path) -> None:
    """Rows where any lon_<planet> is NaN should get 0.0 across all 16 yogas."""
    in_path = _make_parquet([_empty_row()], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"
    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    for spec in _YOGA_SPECS:
        col = f"{spec.slug}_natal_strength"
        assert out[col].iloc[0] == 0.0, f"{col} should be 0.0 when chart is missing"


def test_invalid_lagna_zero_fills(tmp_path: Path) -> None:
    row = _vipareeta_harsha_row()
    row["lagna_sign"] = 0  # invalid; valid range is 1..12
    in_path = _make_parquet([row], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"
    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    assert out["vipareeta_harsha_natal_strength"].iloc[0] == 0.0


# --------------------------------------------------------------------------- #
# Dasha gating semantics                                                      #
# --------------------------------------------------------------------------- #

def test_dasha_gating_md_match_weight_1(tmp_path: Path) -> None:
    """md-lord matches yoga participant → gated = natal × 1.0."""
    row = _vipareeta_harsha_row()
    row["active_md_lord"] = "Mercury"  # Harsha lord
    row["active_ad_lord"] = "Mars"
    row["active_pd_lord"] = "Venus"
    in_path = _make_parquet([row], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"
    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    natal = out["vipareeta_harsha_natal_strength"].iloc[0]
    gated = out["vipareeta_harsha_dasha_gated_strength"].iloc[0]
    assert natal > 0.0
    assert gated == pytest.approx(natal * 1.0, abs=1e-9)


def test_dasha_gating_ad_only_weight_0_5(tmp_path: Path) -> None:
    """When the participant lord appears only in ad slot, weight is 0.5."""
    row = _vipareeta_harsha_row()
    row["active_md_lord"] = "Mars"
    row["active_ad_lord"] = "Mercury"
    row["active_pd_lord"] = "Venus"
    in_path = _make_parquet([row], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"
    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    natal = out["vipareeta_harsha_natal_strength"].iloc[0]
    gated = out["vipareeta_harsha_dasha_gated_strength"].iloc[0]
    assert gated == pytest.approx(natal * 0.5, abs=1e-9)


def test_dasha_gating_pd_only_weight_0_25(tmp_path: Path) -> None:
    row = _vipareeta_harsha_row()
    row["active_md_lord"] = "Mars"
    row["active_ad_lord"] = "Venus"
    row["active_pd_lord"] = "Mercury"
    in_path = _make_parquet([row], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"
    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    natal = out["vipareeta_harsha_natal_strength"].iloc[0]
    gated = out["vipareeta_harsha_dasha_gated_strength"].iloc[0]
    assert gated == pytest.approx(natal * 0.25, abs=1e-9)


def test_dasha_gating_no_match_zero(tmp_path: Path) -> None:
    """Yoga fires natally but no dasha lord matches → gated = 0.0."""
    row = _vipareeta_harsha_row()
    row["active_md_lord"] = "Mars"
    row["active_ad_lord"] = "Venus"
    row["active_pd_lord"] = "Saturn"
    in_path = _make_parquet([row], tmp_path / "in.parquet")
    out_path = tmp_path / "out.parquet"
    inject_yoga_features(in_path, out_path)
    out = pd.read_parquet(out_path)

    assert out["vipareeta_harsha_natal_strength"].iloc[0] > 0.0
    assert out["vipareeta_harsha_dasha_gated_strength"].iloc[0] == 0.0


# --------------------------------------------------------------------------- #
# Summary dict                                                                #
# --------------------------------------------------------------------------- #

def test_summary_per_yoga_includes_pos_neg_when_target_present(tmp_path: Path) -> None:
    """When ``is_event_X`` is in the parquet, summary["per_yoga"] gets pos/neg means."""
    rows = [
        _vipareeta_harsha_row(is_event=1),
        _vipareeta_harsha_row(is_event=0),
        _empty_row(),
    ]
    in_path = _make_parquet(rows, tmp_path / "in.parquet")
    summary = inject_yoga_features(in_path, tmp_path / "out.parquet")

    h = summary["per_yoga"]["vipareeta_harsha"]
    for key in (
        "n_with_yoga", "prevalence_pct", "mean_strength_all",
        "pos_mean_strength", "neg_mean_strength",
        "pos_yoga_rate_pct", "neg_yoga_rate_pct",
    ):
        assert key in h, f"missing key {key}"

    assert h["n_with_yoga"] >= 1
    assert h["prevalence_pct"] >= 1.0
