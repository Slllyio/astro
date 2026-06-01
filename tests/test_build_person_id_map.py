"""Tests for app/medini/etl/build_person_id_map.py.

Pins the canonical name_norm ↔ person_id mapping invariants:
- Same person across 3 corpora resolves to consistent birth_jd
- ADB rows always match a Silver person (100% bridge rate)
- WD rows always match a Silver person (100% bridge rate)
- LA rows get synthetic person_ids (no Silver match)
- Round-9 corpora identified by lowercase Q-id correctly map to WD:Q...
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.medini.etl.build_person_id_map import build_mapping


@pytest.fixture
def tiny_data_dir(tmp_path: Path) -> Path:
    """Fixture with the minimum files needed to exercise build_mapping.

    Three persons:
      - Agatha Christie (in ADB+WD+LA, same birth_jd)
      - Einstein (in ADB+WD only, same birth_jd)
      - Test Person (in LA only, synthetic id expected)
    """
    # ADB dasha: per-MD rows for two persons
    pd.DataFrame({
        "name_norm": ["agatha christie", "agatha christie",
                       "albert einstein", "albert einstein"],
        "birth_jd": [2411626.0931, 2411626.0931,
                      2407422.9424, 2407422.9424],
    }).to_parquet(tmp_path / "dasha_event_corpus.parquet", index=False)

    # WD dasha
    pd.DataFrame({
        "name_norm": ["agatha christie", "albert einstein", "q12842639"],
        "birth_jd": [2411626.0931, 2407422.9424, 2419465.6458],
    }).to_parquet(tmp_path / "wikidata_dasha_corpus.parquet", index=False)

    # LA dasha: includes a person not in other corpora
    pd.DataFrame({
        "name_norm": ["agatha christie", "test person la only"],
        "birth_jd": [2411626.0931, 2440000.5],
    }).to_parquet(tmp_path / "lunarastro_dasha_corpus.parquet", index=False)

    # The WD source events file — the bridge for the WD name_norm to Q-id
    pd.DataFrame({
        "person_id": ["Q35064", "Q937", "Q12842639"],
        "person_name": ["Agatha Christie", "Albert Einstein", "Q12842639"],
    }).to_parquet(tmp_path / "wikidata_dated_events.parquet", index=False)

    # persons.parquet — only ADB and WD persons; the LA test person is absent.
    pd.DataFrame({
        "person_id": ["ADB:2411626.0931", "ADB:2407422.9424",
                       "WD:Q35064", "WD:Q937", "WD:Q12842639"],
        "name": ["agatha christie", "albert einstein",
                 "Agatha Christie", "Albert Einstein", "Q12842639"],
        "birth_date": ["1890-09-15", "1879-03-14",
                        "1890-09-15", "1879-03-14", "1912-03-04"],
        "birth_jd": [2411626.0931, 2407422.9424, None, None, None],
        "source": ["astro_databank", "astro_databank",
                    "wikidata", "wikidata", "wikidata"],
    }).to_parquet(tmp_path / "persons.parquet", index=False)
    return tmp_path


class TestBridgeQuality:
    """ADB and WD persons resolve 100% to Silver; LA gets synthetic ids."""

    def test_adb_resolution_is_complete(self, tiny_data_dir: Path):
        """Every ADB row matches an entry in persons.parquet via birth_jd."""
        mapping = build_mapping(tiny_data_dir)
        adb = mapping[mapping["corpus_tag"] == "ADB"]
        assert len(adb) == 2  # Christie + Einstein
        assert adb["is_silver_resident"].all()

    def test_wd_resolution_via_dated_events_bridge(self, tiny_data_dir: Path):
        """WD name_norm bridges through wikidata_dated_events.parquet to Q-id."""
        mapping = build_mapping(tiny_data_dir)
        wd = mapping[mapping["corpus_tag"] == "WD"]
        assert len(wd) == 3
        assert wd["is_silver_resident"].all()
        wd_pids = set(wd["person_id"])
        assert wd_pids == {"WD:Q35064", "WD:Q937", "WD:Q12842639"}

    def test_la_persons_get_synthetic_ids(self, tiny_data_dir: Path):
        """LA persons get ``LA:`` + name_norm ids regardless of Silver presence."""
        mapping = build_mapping(tiny_data_dir)
        la = mapping[mapping["corpus_tag"] == "LA"]
        assert len(la) == 2
        # Synthetic id format: "LA:" + name_norm
        for _, row in la.iterrows():
            assert row["person_id"] == f"LA:{row['name_norm']}"

    def test_la_marked_resident_when_in_persons(self, tmp_path: Path):
        """When LA persons live in persons.parquet, is_silver_resident=True.

        Pins the LA-promotion behavior added in this session: after
        build_person_event_tables.load_la_persons() runs, LA persons
        become first-class Silver residents and the bridge picks them up.
        """
        # Minimal LA dasha corpus (one person).
        pd.DataFrame({
            "name_norm": ["albert einstein"],
            "birth_jd": [2407422.9424],
        }).to_parquet(tmp_path / "lunarastro_dasha_corpus.parquet", index=False)
        # Other corpora empty.
        pd.DataFrame({"name_norm": [], "birth_jd": []}).to_parquet(
            tmp_path / "dasha_event_corpus.parquet", index=False,
        )
        pd.DataFrame({"name_norm": [], "birth_jd": []}).to_parquet(
            tmp_path / "wikidata_dasha_corpus.parquet", index=False,
        )
        # persons.parquet with the LA person promoted.
        pd.DataFrame({
            "person_id": ["LA:albert einstein"],
            "name": ["albert einstein"],
            "birth_date": ["1879-03-14"],
            "birth_jd": [2407422.9424],
            "source": ["lunarastro"],
        }).to_parquet(tmp_path / "persons.parquet", index=False)
        mapping = build_mapping(tmp_path)
        la_einstein = mapping[mapping["name_norm"] == "albert einstein"].iloc[0]
        assert la_einstein["is_silver_resident"]
        assert la_einstein["name_in_persons"] == "albert einstein"


class TestCrossCorpusConsistency:
    """The same person across corpora has matching birth_jd."""

    def test_agatha_across_three_corpora(self, tiny_data_dir: Path):
        """Christie's birth_jd matches across ADB, WD, LA."""
        mapping = build_mapping(tiny_data_dir)
        agatha = mapping[mapping["name_norm"] == "agatha christie"]
        assert len(agatha) == 3
        # All three corpora agree on birth_jd to within float precision.
        jd_set = set(round(jd, 4) for jd in agatha["birth_jd"])
        assert len(jd_set) == 1, f"birth_jd inconsistent: {jd_set}"

    def test_adb_person_id_format(self, tiny_data_dir: Path):
        """ADB person_id encodes birth_jd to 4 decimal places."""
        mapping = build_mapping(tiny_data_dir)
        adb = mapping[mapping["corpus_tag"] == "ADB"]
        for _, row in adb.iterrows():
            assert row["person_id"].startswith("ADB:")
            expected = f"ADB:{row['birth_jd']:.4f}"
            assert row["person_id"] == expected


class TestSchemaContract:
    """Output schema must include every documented column."""

    def test_required_columns_present(self, tiny_data_dir: Path):
        """Schema contract for any downstream consumer."""
        mapping = build_mapping(tiny_data_dir)
        required = {
            "corpus_tag", "name_norm", "birth_jd",
            "person_id", "is_silver_resident", "name_in_persons",
        }
        assert required.issubset(set(mapping.columns))

    def test_corpus_tag_values_are_canonical(self, tiny_data_dir: Path):
        """corpus_tag is always one of ADB / WD / LA."""
        mapping = build_mapping(tiny_data_dir)
        assert set(mapping["corpus_tag"].unique()).issubset({"ADB", "WD", "LA"})
