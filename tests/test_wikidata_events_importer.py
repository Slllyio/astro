"""Tests for the Wikidata dated-events puller (network mocked)."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl import wikidata_events_importer as wei


def test_iso_year_and_date() -> None:
    assert wei._iso_year("1879-03-14T00:00:00Z") == 1879
    assert wei._iso_year("-0044-03-15T00:00:00Z") is None     # 44 BC, out of range
    assert wei._iso_year("2025-01-01T00:00:00Z") == 2025
    assert wei._iso_year(None) is None
    assert wei._iso_date("1879-03-14T00:00:00Z") == "1879-03-14"
    assert wei._iso_date("1879-00-00T00:00:00Z") == ""        # year precision only
    assert wei._iso_date("") == ""


def _binding(qid, label, birth, date):
    b = {"person": {"value": f"http://www.wikidata.org/entity/{qid}"},
         "birth": {"value": birth}, "date": {"value": date}}
    if label is not None:
        b["personLabel"] = {"value": label}
    return b


def _result(*bindings):
    return {"results": {"bindings": list(bindings)}}


def test_parse_bindings_basic() -> None:
    res = _result(
        _binding("Q937", "Albert Einstein", "1879-03-14T00:00:00Z",
                 "1903-01-06T00:00:00Z"))
    rows = wei.parse_bindings(res, "marriage")
    assert len(rows) == 1
    r = rows[0]
    assert r["name"] == "Albert Einstein" and r["event_year"] == 1903
    assert r["birth_year"] == 1879 and r["event_class"] == "marriage"
    assert r["name_norm"] == "alberteinstein"
    assert r["event_date"] == "1903-01-06"
    assert r["source_url"].endswith("/Q937")


def test_parse_bindings_skips_unlabelled_and_bad_dates() -> None:
    res = _result(
        _binding("Q1", "Q1", "1900-01-01T00:00:00Z", "1925-01-01T00:00:00Z"),  # label==qid
        _binding("Q2", "No Birth", None, "1925-01-01T00:00:00Z"),               # no birth val→skip
        _binding("Q3", "Out Of Range", "1879-01-01T00:00:00Z", "3500-01-01T00:00:00Z"),
        _binding("Q4", "Good Person", "1950-01-01T00:00:00Z", "1980-06-01T00:00:00Z"),
    )
    # Q2 has no birth value key → birth_year None → skip; manually drop birth.
    res["results"]["bindings"][1].pop("birth")
    rows = wei.parse_bindings(res, "death")
    assert [r["name"] for r in rows] == ["Good Person"]


def test_pull_class_paginates_until_short_page() -> None:
    pages = [
        _result(*[_binding(f"Q{i}", f"P{i}", "1900-01-01T00:00:00Z",
                           "1930-01-01T00:00:00Z") for i in range(3)]),
        _result(_binding("Q9", "Last", "1901-01-01T00:00:00Z",
                         "1931-01-01T00:00:00Z")),   # short page → stop
    ]
    calls = {"n": 0}

    def fake_sparql(q):
        out = pages[calls["n"]]
        calls["n"] += 1
        return out

    rows = wei.pull_class("marriage", page_size=3, max_pages=10,
                          sparql=fake_sparql, pause=0.0)
    assert len(rows) == 4 and calls["n"] == 2


def test_pull_class_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        wei.pull_class("lottery", page_size=10, max_pages=1, sparql=lambda q: {})


def test_build_dedups_and_writes(tmp_path) -> None:
    page = _result(
        _binding("Q937", "Albert Einstein", "1879-03-14T00:00:00Z",
                 "1903-01-06T00:00:00Z"),
        _binding("Q937", "Albert Einstein", "1879-03-14T00:00:00Z",
                 "1903-01-06T00:00:00Z"),     # exact dup → collapsed
    )
    out = tmp_path / "wd.parquet"
    stats = wei.build(["marriage"], out, page_size=5000, max_pages=1,
                      sparql=lambda q: page)
    assert stats["total_events"] == 1 and stats["marriage"] == 1
    df = pd.read_parquet(out)
    assert list(df["event_class"]) == ["marriage"]
