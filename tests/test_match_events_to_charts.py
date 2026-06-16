"""Tests for the events→charts person_id matcher."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl import match_events_to_charts as m


def test_jd_to_year_known_epochs() -> None:
    assert m.jd_to_year(2451545.0) == 2000          # 2000-01-01 12:00 TT
    assert m.jd_to_year(2415021.0) == 1900          # ~1900-01-01
    assert m.jd_to_year(2440588.0) == 1970          # ~1970-01-01
    assert m.jd_to_year(None) is None


def _persons():
    # birth_jd ≈ 1879 for Einstein, 1950 for John Doe, plus a homonym in 1980.
    return pd.DataFrame({
        "person_id": ["ADB:1", "VED:2", "ADB:3", "ADB:4"],
        "name": ["alberteinstein", "johndoe", "johnsmith", "johnsmith"],
        "birth_jd": [2407794.0, 2433648.0, 2444240.0, 2444240.0],  # 1879,1950,1980,1980
    })


def test_match_unique_and_year_tolerance() -> None:
    events = pd.DataFrame({
        "name_norm": ["alberteinstein", "johndoe"],
        "birth_year": [1879, 1951],                  # 1951 within ±1 of 1950
        "event_class": ["marriage", "marriage"],
        "event_year": [1903, 1972],
    })
    matched, stats = m.attach_person_ids(events, _persons(), year_tolerance=1)
    assert stats["matched"] == 2 and stats["unmatched"] == 0
    assert set(matched["person_id"]) == {"ADB:1", "VED:2"}


def test_ambiguous_homonym_dropped() -> None:
    # two different person_ids share name+year → ambiguous, not guessed.
    events = pd.DataFrame({"name_norm": ["johnsmith"], "birth_year": [1980],
                           "event_class": ["death"], "event_year": [2010]})
    matched, stats = m.attach_person_ids(events, _persons())
    assert stats["ambiguous"] == 1 and matched.empty


def test_unmatched_when_no_person() -> None:
    events = pd.DataFrame({"name_norm": ["nobody"], "birth_year": [1990],
                           "event_class": ["marriage"], "event_year": [2015]})
    matched, stats = m.attach_person_ids(events, _persons())
    assert stats["unmatched"] == 1 and matched.empty


def test_year_out_of_tolerance_unmatched() -> None:
    events = pd.DataFrame({"name_norm": ["johndoe"], "birth_year": [1955],
                           "event_class": ["marriage"], "event_year": [1975]})
    _, stats = m.attach_person_ids(events, _persons(), year_tolerance=1)
    assert stats["unmatched"] == 1            # 1955 vs 1950 > tolerance


def test_persons_with_name_column_gets_normalized() -> None:
    persons = pd.DataFrame({"person_id": ["X:1"], "name": ["Agnès B."],
                            "birth_jd": [2433648.0]})  # 1950
    events = pd.DataFrame({"name": ["Agnes B"], "birth_year": [1950],
                           "event_class": ["career"], "event_year": [1980]})
    matched, stats = m.attach_person_ids(events, persons)
    assert stats["matched"] == 1 and matched["person_id"].iloc[0] == "X:1"


def test_build_writes_output(tmp_path) -> None:
    p = tmp_path / "persons.parquet"
    e = tmp_path / "events.parquet"
    _persons().to_parquet(p)
    pd.DataFrame({"name_norm": ["alberteinstein"], "birth_year": [1879],
                  "event_class": ["marriage"], "event_year": [1903]}).to_parquet(e)
    out = tmp_path / "matched.parquet"
    stats = m.build(e, p, out)
    assert stats["matched"] == 1
    assert pd.read_parquet(out)["person_id"].iloc[0] == "ADB:1"


def test_missing_key_columns_raise() -> None:
    with pytest.raises(KeyError):
        m.attach_person_ids(pd.DataFrame({"event_year": [1903]}), _persons())
