"""Tests for the run-3 Triple-Lock corpus builder (fixture CSVs, no network)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.medini.ml.raman_saab.build_run3_corpus import (
    _is_own_death_root, build_corpus,
)


def _wikitext(events: list[tuple[str, str]]) -> str:
    """Minimal astro_people raw_wikitext with ASTRODATABANK_evn templates."""
    blocks = []
    for i, (sevcode, sevdate) in enumerate(events):
        blocks.append(
            "{{ASTRODATABANK_evn\n"
            f"|CodeID = {i}\n"
            f"|sevcode = {sevcode}\n"
            f"|sevdate = {sevdate}\n"
            "}}"
        )
    return "\n".join(blocks)


@pytest.fixture
def sources(tmp_path: Path) -> tuple[Path, Path, Path]:
    holos = pd.DataFrame({
        "name": ["Alpha, Ann", "Beta, Bob", "Gamma, Guy", "Gamma, Guy",
                 "Delta, Dee", "Polar, Pat", "Echo, Ed"],
        "birth_year": [1900, 1910, 1920, 1921, 1930, 1935, 1940],
        "birth_month": [1, 2, 3, 3, 4, 5, 6],
        "birth_day": [1, 2, 3, 3, 4, 5, 6],
        "birth_hour": [6, 12, 18, 18, 3, 9, 23],
        "birth_min": [30, 0, 15, 15, 45, 0, 59],
        "birth_sec": [0, 0, 0, 0, 0, 0, 0],
        "utc_offset": [-5.0, 1.0, 5.5, 5.5, 0.0, 2.0, -8.0],
        "utc_dst_corrected": [-5.0, 2.0, 5.5, 5.5, None, 2.0, -8.0],
        "latitude": [40.0, 48.0, 13.0, 13.0, 51.0, 70.0, 34.0],
        "longitude": [-74.0, 2.0, 77.5, 77.5, 0.0, 25.0, -118.0],
        "rodden_rating": ["AA", "A", "AA", "AA", "AA", "AA", "C"],
        "is_julian": [0, 0, 0, 0, 0, 0, 0],
    })
    ap = pd.DataFrame({
        "name": ["Alpha, Ann", "Beta, Bob", "Delta, Dee", "Polar, Pat",
                 "Foxtrot, Fay"],
        "raw_wikitext": [
            _wikitext([("Death by Disease", "1980/06/15")]),
            # own death + a family death (the latter must be ignored)
            _wikitext([("Death, Cause unspecified", "1995/01/20"),
                       ("Death of Mate", "1990/03/03")]),
            # conflicting own-death dates -> person dropped
            _wikitext([("Death", "2000/01/01"), ("Death", "2001/01/01")]),
            _wikitext([("Death, Cause unspecified", "2005/07/07")]),
            # year-only date -> excluded by full-date filter
            _wikitext([("Death, Cause unspecified", "1999/00/00")]),
        ],
        "page_id": range(5),
    })
    hp, app_, out = (tmp_path / "holos.csv", tmp_path / "ap.csv",
                     tmp_path / "out" / "corpus.parquet")
    holos.to_csv(hp, index=False)
    ap.to_csv(app_, index=False)
    return hp, app_, out


class TestOwnDeathFilter:
    def test_death_of_family_excluded(self):
        roots = pd.Series(["Death", "Death by Disease",
                           "Death, Cause unspecified", "Death of Mate",
                           "Death of Child", "Work"])
        got = _is_own_death_root(roots).tolist()
        assert got == [True, True, True, False, False, False]


class TestBuildCorpus:
    def test_join_exclusions_and_accounting(self, sources):
        hp, ap, out = sources
        acc = build_corpus(hp, ap, out)
        df = pd.read_parquet(out)
        names = set(df["name"])
        # Alpha joins cleanly (dies 1980, born 1900 -> age ~80).
        assert "Alpha, Ann" in names
        # Beta joins; its family-death event was ignored.
        assert "Beta, Bob" in names
        # Gamma is a duplicated name in holos -> dropped entirely.
        assert not any(n.startswith("Gamma") for n in names)
        assert acc["dropped_dup_names_holos"] == 2
        # Delta has conflicting death dates -> dropped.
        assert "Delta, Dee" not in names
        assert acc["dropped_conflicting_death_dates"] == 1
        # Polar is |lat| > 60 -> dropped, counted.
        assert "Polar, Pat" not in names
        assert acc["dropped_circumpolar_lat"] == 1
        # Echo is Rodden C -> filtered before join.
        assert "Echo, Ed" not in names
        # Foxtrot's year-only death never qualifies.
        assert acc["final_n"] == len(df) == 2
        # accounting file exists
        assert json.loads((out.parent / "exclusions.json").read_text())

    def test_effective_tz_uses_dst_corrected_with_fallback(self, sources):
        hp, ap, out = sources
        build_corpus(hp, ap, out)
        df = pd.read_parquet(out).set_index("name")
        # Beta: utc_dst_corrected=2.0 differs from utc_offset=1.0 -> use 2.0
        assert df.loc["Beta, Bob", "tz_offset"] == 2.0

    def test_age_computed(self, sources):
        hp, ap, out = sources
        build_corpus(hp, ap, out)
        df = pd.read_parquet(out).set_index("name")
        assert df.loc["Alpha, Ann", "age_years"] == pytest.approx(80.45, abs=0.1)
