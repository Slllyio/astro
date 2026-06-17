"""Tests for the multi-source event aggregator + funnel."""
from __future__ import annotations

import pandas as pd

from app.medini.etl import aggregate_events as ag


def test_normalize_from_event_root_and_name() -> None:
    df = pd.DataFrame({"name": ["Albert Einstein"], "event_root": ["marriage"],
                       "event_year": ["1903"]})
    out = ag.normalize_events(df, "vedastro")
    assert out["name_norm"].iloc[0] == "alberteinstein"
    assert out["event_class"].iloc[0] == "marriage"
    assert out["event_year"].iloc[0] == 1903
    assert pd.isna(out["birth_year"].iloc[0]) and out["source"].iloc[0] == "vedastro"


def test_normalize_from_class_and_birth_year() -> None:
    df = pd.DataFrame({"name_norm": ["x"], "event_class": ["career"],
                       "event_year": [1980], "birth_year": [1950]})
    out = ag.normalize_events(df, "wikidata")
    assert out["event_class"].iloc[0] == "career" and out["birth_year"].iloc[0] == 1950


def test_enrich_birth_year_from_persons() -> None:
    events = ag.normalize_events(
        pd.DataFrame({"name": ["A B", "C D"], "event_root": ["marriage", "marriage"],
                      "event_year": [1925, 1960]}), "ved")
    persons = pd.DataFrame({"person_id": ["P1", "P2"], "name": ["A B", "C D"],
                            "birth_year": [1879, 1950]})
    out = ag.enrich_birth_year(events, persons)
    assert list(out["birth_year"]) == [1879, 1950]


def test_enrich_birth_year_from_jd_persons() -> None:
    events = ag.normalize_events(
        pd.DataFrame({"name": ["A B"], "event_root": ["marriage"],
                      "event_year": [1925]}), "ved")
    jd = 2407794.0
    out = ag.enrich_birth_year(events, pd.DataFrame(
        {"person_id": ["P1"], "name": ["A B"], "birth_jd": [jd]}))
    assert out["birth_year"].iloc[0] == ag.jd_to_year(jd)   # exact, JD-consistent


def test_aggregate_dedups_cross_source() -> None:
    a = ag.normalize_events(pd.DataFrame(
        {"name_norm": ["x"], "event_class": ["marriage"], "event_year": [1903],
         "birth_year": [1879]}), "wikidata")
    b = ag.normalize_events(pd.DataFrame(
        {"name_norm": ["x"], "event_class": ["marriage"], "event_year": [1903],
         "birth_year": [1879]}), "vedastro")
    assert len(ag.aggregate([a, b])) == 1            # same event, two sources → 1


def test_funnel_counts_auspicious_in_band() -> None:
    df = pd.DataFrame({
        "name_norm": ["a", "b", "c", "d"],
        "birth_year": [1950, 1950, 1950, 1950],
        "event_class": ["marriage", "career", "death", "marriage"],
        "event_year": [1978, 1985, 1958, 1958],      # ages 28, 35, 8, 8
        "source": ["wd"] * 4,
    })
    f = ag.funnel(df, target=10)
    # marriage@28 ✓, career@35 ✓, death excluded (not auspicious),
    # marriage@8 ✗ (below 16) → 2 auspicious in band.
    assert f["auspicious_in_band"] == 2
    assert f["by_class"] == {"marriage": 1, "career": 1}
    assert f["fraction_of_target"] == 0.2


def test_build_writes_and_matches(tmp_path) -> None:
    ev = ag.normalize_events(pd.DataFrame(
        {"name_norm": ["alberteinstein"], "event_class": ["marriage"],
         "event_year": [1903], "birth_year": [1879]}), "wd")
    persons = pd.DataFrame({"person_id": ["ADB:1"], "name": ["alberteinstein"],
                            "birth_jd": [2407794.0]})  # 1879
    out = tmp_path / "u.parquet"
    rep = ag.build([ev], out, persons, target=100)
    assert rep["match"]["matched"] == 1
    assert "person_id" in pd.read_parquet(out).columns
    assert rep["funnel_matched"]["auspicious_first_events"] == 1
