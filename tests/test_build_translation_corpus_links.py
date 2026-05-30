"""Tests for build_translation_corpus_links — Phase E corpus mapper.

The ETL maps each TranslationRecord to up to N corpus passage IDs from
``data/knowledge_library/manifest.parquet`` via source-name + topic-tag
heuristics. These tests use synthetic manifest rows so they're
hermetic — they don't require the actual 918-artefact corpus.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.core.dkp_translation import Domain, TranslationRecord
from app.medini.etl.build_translation_corpus_links import (
    _extract_source_matches,
    _key_terms,
    _score_artefact,
    build_links,
    composite_key,
)


@pytest.fixture
def synthetic_manifest() -> pd.DataFrame:
    """Tiny 5-row manifest covering the major sources + topic types."""
    return pd.DataFrame([
        {
            "id": "bphs-001", "source": "bphs",
            "topics": ["predictive.marriage_timing", "primitives.planets"],
            "title": "Mangal Dosha analysis from BPHS Ch.34",
        },
        {
            "id": "phal-001", "source": "phaladeepika",
            "topics": ["predictive.career_timing"],
            "title": "Saturn in 10H per Phaladeepika 6.30",
        },
        {
            "id": "sar-001", "source": "saravali",
            "topics": ["predictive.death_timing"],
            "title": "Maraka yogas — Saravali Ch.34",
        },
        {
            "id": "yt-001", "source": "lunarastro/youtube",
            "topics": ["primitives.planets"],
            "title": "Random YouTube on gemstones",
        },
        {
            "id": "raman-001", "source": "hindu_predictive_astrology_raman",
            "topics": ["predictive.marriage_timing"],
            "title": "Raman on Mars-Venus combinations",
        },
    ])


@pytest.fixture
def marriage_record() -> TranslationRecord:
    return TranslationRecord(
        key="Mangal Dosha", classification="yoga", domain=Domain.KINSHIP,
        shloka="Mars in 1/2/4/7/8/12 from Lagna or Moon causes kalatra-pida.",
        classical_references=("Mansagari Ch.6.43", "Phaladeepika Ch.6.17", "BPHS Ch.80"),
        ancient_manifestation="...", desh_shift="...", kaal_shift="...",
        paristhiti_shift="...", modern_manifestation="...",
        invariant_mechanism="...",
        modern_references=(),
    )


@pytest.fixture
def career_record() -> TranslationRecord:
    return TranslationRecord(
        key="bhava_10_planet_Saturn", classification="bhava_placement",
        domain=Domain.CAREER_WEALTH,
        shloka="Saturn in 10H gives long career.",
        classical_references=("Phaladeepika Ch.6.30",),
        ancient_manifestation="...", desh_shift="...", kaal_shift="...",
        paristhiti_shift="...", modern_manifestation="...",
        invariant_mechanism="...",
        modern_references=(),
    )


class TestCompositeKey:
    def test_format_is_key_double_colon_domain(self, marriage_record):
        """Composite key disambiguates same-yoga-different-domain records."""
        assert composite_key(marriage_record) == "Mangal Dosha::kinship"


class TestExtractSourceMatches:
    def test_bphs_reference_maps_to_bphs_source(self):
        """'BPHS Ch.34' → manifest source 'bphs'."""
        assert "bphs" in _extract_source_matches(("BPHS Ch.34",))

    def test_phaladeepika_maps_to_both_variants(self):
        """Phaladeepika appears as 'phaladeepika' AND 'phaladeepika_dli'."""
        sources = _extract_source_matches(("Phaladeepika Ch.6.17",))
        assert "phaladeepika" in sources
        assert "phaladeepika_dli" in sources

    def test_unknown_reference_matches_nothing(self):
        """Unrecognised source name returns empty set, no crash."""
        assert _extract_source_matches(("FooBar Ch.1",)) == set()


class TestKeyTerms:
    def test_extracts_yoga_words(self):
        """Mangal Dosha → ('mangal', 'dosha')."""
        terms = _key_terms("Mangal Dosha")
        assert "mangal" in terms
        assert "dosha" in terms

    def test_bhava_planet_key_extracts_planet(self):
        """bhava_8_planet_Saturn → includes 'saturn'."""
        terms = _key_terms("bhava_8_planet_Saturn")
        assert "saturn" in terms

    def test_strips_common_stopwords(self):
        """'career', 'dharma', 'health' suffixes don't pollute matches."""
        terms = _key_terms("Saraswati_career")
        assert "career" not in terms
        assert "saraswati" in terms


class TestScoreArtefact:
    def test_source_match_adds_2_points(self, marriage_record):
        """Artefact source in the record's source-match set scores +2."""
        score = _score_artefact(
            marriage_record, source="bphs", topics=[], title="",
            source_matches={"bphs"}, domain_topics=frozenset(),
            key_terms=(),
        )
        assert score == 2

    def test_topic_match_adds_1_point(self, marriage_record):
        """Topic in domain's tag set adds +1."""
        score = _score_artefact(
            marriage_record, source="other", topics=["predictive.marriage_timing"],
            title="", source_matches=set(),
            domain_topics=frozenset({"predictive.marriage_timing"}),
            key_terms=(),
        )
        assert score == 1

    def test_title_keyword_match_adds_1_point(self, marriage_record):
        """Record key term appearing in title adds +1."""
        score = _score_artefact(
            marriage_record, source="other", topics=[], title="On the Mangal yoga",
            source_matches=set(), domain_topics=frozenset(),
            key_terms=("mangal",),
        )
        assert score == 1


class TestBuildLinks:
    def test_returns_dict_keyed_by_composite_key(
        self, synthetic_manifest, marriage_record, career_record,
    ):
        """Output uses composite_key so same-yoga-different-domain don't collide."""
        links = build_links(
            synthetic_manifest, (marriage_record, career_record), top_n=8,
        )
        assert "Mangal Dosha::kinship" in links
        assert "bhava_10_planet_Saturn::career_wealth" in links

    def test_marriage_record_prefers_bphs_and_marriage_topic(
        self, synthetic_manifest, marriage_record,
    ):
        """The BPHS marriage-topic artefact should rank first."""
        links = build_links(synthetic_manifest, (marriage_record,), top_n=8)
        marriage_ids = links["Mangal Dosha::kinship"]
        assert marriage_ids[0] == "bphs-001"

    def test_caps_to_top_n(self, synthetic_manifest, marriage_record):
        """Specifying top_n=2 returns at most 2 IDs."""
        links = build_links(synthetic_manifest, (marriage_record,), top_n=2)
        assert len(links["Mangal Dosha::kinship"]) <= 2

    def test_yt_artefact_outranked_by_classical(
        self, synthetic_manifest, marriage_record,
    ):
        """YouTube source has lower priority than classical texts."""
        links = build_links(synthetic_manifest, (marriage_record,), top_n=8)
        ids = links["Mangal Dosha::kinship"]
        # YT artefact ranked AFTER any classical match
        yt_pos = ids.index("yt-001") if "yt-001" in ids else 999
        bphs_pos = ids.index("bphs-001") if "bphs-001" in ids else 999
        assert bphs_pos < yt_pos


class TestEnrichmentLoader:
    """The enrichment loader in app/core/dkp_translation.py applies all
    three sidecars to the base _TRANSLATIONS at module init time.
    Verify the result on the production registry.
    """

    def test_all_records_have_corpus_passage_ids(self):
        """Every record should have at least one corpus passage after
        enrichment (the production sidecar matches all 27)."""
        from app.core.dkp_translation import all_translations
        recs = all_translations()
        n_with = sum(1 for r in recs if r.corpus_passage_ids)
        assert n_with == len(recs), (
            f"only {n_with}/{len(recs)} records have corpus_passage_ids "
            "after enrichment — rerun "
            "`python -m app.medini.etl.build_translation_corpus_links`"
        )

    def test_sanskrit_shlokas_load_for_documented_keys(self):
        """Records named in the Sanskrit sidecar should have non-empty
        shlokas after enrichment."""
        from app.core.dkp_translation import all_translations
        recs = all_translations()
        by_key = {f"{r.key}::{r.domain}": r for r in recs}
        # Mangal Dosha is in the Sanskrit sidecar
        if "Mangal Dosha::kinship" in by_key:
            r = by_key["Mangal Dosha::kinship"]
            assert r.sanskrit_shloka, "Mangal Dosha Sanskrit not loaded"
            assert r.transliteration, "Mangal Dosha transliteration missing"

    def test_lagna_notes_merge_inline_and_sidecar(self):
        """Mangal Dosha had inline Lagna notes for 4 Lagnas; sidecar
        adds all 12. After enrichment we should see 12."""
        from app.core.dkp_translation import all_translations
        recs = all_translations()
        mangal = next(
            (r for r in recs if r.key == "Mangal Dosha"
             and r.domain == Domain.KINSHIP), None,
        )
        assert mangal is not None
        # Sidecar covers all 12 Lagnas; inline had 4. Merged → 12.
        assert len(mangal.lagna_specific_notes) == 12
