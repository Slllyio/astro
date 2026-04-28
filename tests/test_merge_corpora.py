"""Tests for app.medini.etl.merge_corpora.

Pin the dedup tiebreak rules + category union behaviour. The merge is
the single point that decides which duplicate row's data the trainer
sees, so any regression here corrupts the corpus silently.
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.medini.etl.merge_corpora import (
    REQUIRED_COLUMNS,
    _completeness,
    _dedup_key,
    _merge_categories,
    _pick_row,
    merge_csvs,
)


# ---------- _dedup_key ----------

def test_dedup_key_normalizes_case_and_whitespace() -> None:
    row = {"name": "  Albert Einstein  ", "date_of_birth": "1879-03-14"}
    assert _dedup_key(row) == ("albert einstein", "1879-03-14")


def test_dedup_key_returns_none_when_missing_fields() -> None:
    """Rows without a name or DOB can't be safely deduped — pass-through."""
    assert _dedup_key({"name": "", "date_of_birth": "1879-03-14"}) is None
    assert _dedup_key({"name": "Einstein", "date_of_birth": ""}) is None


# ---------- _merge_categories ----------

def test_merge_categories_union_preserves_order() -> None:
    """First file's categories come first; new ones from the second
    append in their own order; duplicates are dropped."""
    out = _merge_categories(
        "marriage : dissolution; Vocation : Politics : Politician",
        "Vocation : Sports : Boxer; marriage : dissolution",
    )
    assert out == (
        "marriage : dissolution;Vocation : Politics : Politician;"
        "Vocation : Sports : Boxer"
    )


def test_merge_categories_handles_blanks() -> None:
    assert _merge_categories("", "Vocation : X") == "Vocation : X"
    assert _merge_categories("A", "") == "A"
    assert _merge_categories("", "") == ""


# ---------- _completeness scoring ----------

def test_completeness_scores_richer_rows_higher() -> None:
    sparse = {
        "name": "x", "date_of_birth": "2000-01-01",
        "time_of_birth": "", "latitude": "", "longitude": "",
        "tz_offset": "", "rodden_rating": "B", "categories": "",
    }
    rich = {
        "name": "x", "date_of_birth": "2000-01-01",
        "time_of_birth": "12:00:00", "latitude": "40", "longitude": "-74",
        "tz_offset": "-5.0", "rodden_rating": "AA",
        "categories": "Vocation : Politics : Politician;Sports : Boxing",
    }
    assert _completeness(rich, 0).as_tuple() > _completeness(sparse, 0).as_tuple()


def test_completeness_aa_beats_a() -> None:
    """AA Rodden wins over A even when other fields tie."""
    aa = {"name": "x", "date_of_birth": "2000-01-01",
          "time_of_birth": "12:00:00", "latitude": "0", "longitude": "0",
          "tz_offset": "0", "rodden_rating": "AA", "categories": ""}
    a = dict(aa, rodden_rating="A")
    assert _completeness(aa, 0).as_tuple() > _completeness(a, 0).as_tuple()


# ---------- _pick_row ----------

def test_pick_row_chooses_richer_data_and_unions_categories() -> None:
    existing = {
        "name": "Einstein",
        "date_of_birth": "1879-03-14",
        "time_of_birth": "",  # missing
        "latitude": "", "longitude": "", "tz_offset": "",
        "rodden_rating": "A",
        "categories": "marriage : happiness",
        "source_url": "url1",
    }
    new = {
        "name": "Einstein",
        "date_of_birth": "1879-03-14",
        "time_of_birth": "11:30:00",
        "latitude": "48.4", "longitude": "10.0", "tz_offset": "1.0",
        "rodden_rating": "AA",
        "categories": "Vocation : Science : Physicist",
        "source_url": "url2",
    }
    picked = _pick_row(existing, new, existing_priority=0, new_priority=1)
    # The new row is more complete → its scalar fields win.
    assert picked["time_of_birth"] == "11:30:00"
    assert picked["rodden_rating"] == "AA"
    assert picked["source_url"] == "url2"
    # Categories are union-merged regardless of which row was chosen.
    assert "marriage : happiness" in picked["categories"]
    assert "Vocation : Science : Physicist" in picked["categories"]


def test_pick_row_keeps_existing_on_tie_breaks_to_priority() -> None:
    """Two equally-rich rows from different sources: earlier CLI source wins."""
    a = {
        "name": "x", "date_of_birth": "2000-01-01",
        "time_of_birth": "12:00:00", "latitude": "1", "longitude": "1",
        "tz_offset": "0", "rodden_rating": "AA",
        "categories": "X",
        "source_url": "first",
    }
    b = dict(a, source_url="second")
    # priority 0 = first, priority 1 = second
    picked = _pick_row(a, b, existing_priority=0, new_priority=1)
    assert picked["source_url"] == "first"


# ---------- merge_csvs end-to-end ----------

def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(REQUIRED_COLUMNS))
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in REQUIRED_COLUMNS})


def test_merge_csvs_collapses_duplicates_across_files(tmp_path: Path) -> None:
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    out = tmp_path / "merged.csv"
    _write_csv(a, [
        {"name": "Einstein", "date_of_birth": "1879-03-14",
         "rodden_rating": "AA", "categories": "Marriage : Happiness",
         "source_url": "vedastro"},
        {"name": "Other", "date_of_birth": "1900-01-01",
         "rodden_rating": "B", "categories": "X"},
    ])
    _write_csv(b, [
        {"name": "Einstein", "date_of_birth": "1879-03-14",
         "time_of_birth": "11:30:00", "latitude": "48.4", "longitude": "10.0",
         "tz_offset": "1.0", "rodden_rating": "AA",
         "categories": "Vocation : Science : Physicist",
         "source_url": "wayback"},
    ])
    stats = merge_csvs([a, b], out)
    assert stats["duplicates_collapsed"] == 1
    assert stats["rows_written"] == 2  # Einstein collapsed + Other

    with out.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by_name = {r["name"]: r for r in rows}
    e = by_name["Einstein"]
    # Wayback row was richer (had time/coords/tz) so its source_url wins.
    assert e["source_url"] == "wayback"
    # Categories from BOTH sources merged, so the trainer can pick either
    # `--target marriage` or `--target physicist`.
    assert "Marriage : Happiness" in e["categories"]
    assert "Vocation : Science : Physicist" in e["categories"]


def test_merge_csvs_passes_through_unmergeable_rows(tmp_path: Path) -> None:
    """Rows missing name or DOB can't be deduped — they should still pass
    through to the output (downstream Stage 2 will filter them)."""
    a = tmp_path / "a.csv"
    out = tmp_path / "merged.csv"
    _write_csv(a, [
        {"name": "", "date_of_birth": "1900-01-01"},   # missing name
        {"name": "OK", "date_of_birth": "1900-01-01"},
    ])
    stats = merge_csvs([a], out)
    assert stats["rows_unmergeable"] == 1
    assert stats["rows_written"] == 2


def test_merge_csvs_skips_missing_input_files(tmp_path: Path) -> None:
    """A missing input shouldn't crash the merge — log + skip."""
    real = tmp_path / "real.csv"
    fake = tmp_path / "does_not_exist.csv"
    out = tmp_path / "out.csv"
    _write_csv(real, [{"name": "X", "date_of_birth": "2000-01-01"}])
    stats = merge_csvs([real, fake], out)
    assert stats["rows_written"] == 1
