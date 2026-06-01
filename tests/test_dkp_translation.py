"""Tests for app.core.dkp_translation — Doctrine Translation Engine."""
from __future__ import annotations

import pytest

from app.core.dkp_translation import (
    Domain,
    TranslationRecord,
    all_translations,
    DOMAIN_META_PRINCIPLES,
    format_translation,
    translate_bhava_planet,
    translate_yoga,
    translations_by_domain,
    translations_for_reading,
)


class TestRegistryIntegrity:
    """Module-level invariants on the translation registry."""

    def test_has_at_least_15_records(self):
        """Sanity: registry contains meaningful coverage."""
        assert len(all_translations()) >= 15

    def test_all_4_domains_represented(self):
        """Kinship, career-wealth, dharma, health all populated."""
        for d in (Domain.KINSHIP, Domain.CAREER_WEALTH,
                  Domain.DHARMA, Domain.HEALTH):
            assert len(translations_by_domain(d)) >= 1

    def test_each_domain_has_meta_principle(self):
        """Every domain has a synthesized meta-principle string."""
        for d in (Domain.KINSHIP, Domain.CAREER_WEALTH,
                  Domain.DHARMA, Domain.HEALTH):
            assert d in DOMAIN_META_PRINCIPLES
            assert len(DOMAIN_META_PRINCIPLES[d]) > 100

    def test_records_are_frozen_dataclasses(self):
        """TranslationRecord must be immutable."""
        rec = all_translations()[0]
        with pytest.raises(Exception):
            rec.shloka = "X"  # type: ignore[misc]


class TestRecordContent:
    """Each record carries the 5 translation layers."""

    @pytest.mark.parametrize("record", all_translations())
    def test_every_record_has_shloka_and_references(self, record):
        """Shloka + classical refs are mandatory."""
        assert record.shloka, f"empty shloka on {record.key}"
        assert record.classical_references, (
            f"no classical refs on {record.key}"
        )

    @pytest.mark.parametrize("record", all_translations())
    def test_every_record_has_dkp_shifts(self, record):
        """All 3 shifts (desh, kaal, paristhiti) populated."""
        assert record.desh_shift, f"{record.key} missing desh shift"
        assert record.kaal_shift, f"{record.key} missing kaal shift"
        assert record.paristhiti_shift, f"{record.key} missing paristhiti shift"

    @pytest.mark.parametrize("record", all_translations())
    def test_every_record_has_modern_manifestation(self, record):
        """Modern manifestation text is non-trivial."""
        assert len(record.modern_manifestation) > 100, (
            f"{record.key} modern manifestation too short"
        )

    @pytest.mark.parametrize("record", all_translations())
    def test_every_record_has_invariant_mechanism(self, record):
        """The 'this is what doesn't change' line is mandatory."""
        assert len(record.invariant_mechanism) > 80, (
            f"{record.key} invariant mechanism too short"
        )

    @pytest.mark.parametrize("record", all_translations())
    def test_classification_is_valid(self, record):
        """Classification ∈ {yoga, bhava_placement}."""
        assert record.classification in ("yoga", "bhava_placement")

    @pytest.mark.parametrize("record", all_translations())
    def test_domain_is_known(self, record):
        """Domain is one of the 4 registered tags."""
        assert record.domain in {
            Domain.KINSHIP, Domain.CAREER_WEALTH,
            Domain.DHARMA, Domain.HEALTH,
        }


class TestLookups:
    """Public lookup API behaviour."""

    def test_translate_yoga_finds_mangal_dosha(self):
        """Mangal Dosha is in the registry and resolvable."""
        recs = translate_yoga("Mangal Dosha")
        assert len(recs) >= 1
        assert recs[0].domain == Domain.KINSHIP

    def test_translate_yoga_returns_empty_for_unknown(self):
        """Unknown yoga name → empty tuple, no exception."""
        assert translate_yoga("NotAYoga") == ()

    def test_translate_bhava_planet_saturn_8(self):
        """Saturn in 8H = ayur-karaka health translation exists."""
        recs = translate_bhava_planet(8, "Saturn")
        assert len(recs) >= 1
        assert recs[0].domain == Domain.HEALTH

    def test_translate_bhava_planet_returns_empty_for_unknown(self):
        """No record for arbitrary (bhava, planet) → empty."""
        recs = translate_bhava_planet(3, "Venus")
        assert recs == ()

    def test_translations_for_reading_combines(self):
        """Combined yoga + placement lookup returns deduplicated set."""
        out = translations_for_reading(
            ["Mangal Dosha", "Gajakesari"],
            [(8, "Saturn"), (1, "Rahu")],
        )
        keys = {r.key for r in out}
        assert "Mangal Dosha" in keys
        assert "Gajakesari" in keys
        assert "bhava_8_planet_Saturn" in keys


class TestRendering:
    """format_translation output."""

    def test_format_translation_includes_all_5_layers(self):
        """Output mentions shloka, ancient, DKP shift, modern, invariant."""
        rec = all_translations()[0]
        text = format_translation(rec)
        assert "SHLOKA" in text
        assert "ANCIENT" in text
        assert "DKP" in text
        assert "MODERN" in text
        assert "INVARIANT" in text


class TestDoctrineFidelity:
    """Spot-checks that specific records carry the expected anchors."""

    def test_mangal_dosha_cites_mansagari(self):
        """Mangal Dosha record cites Mansagari Ch.6."""
        recs = translate_yoga("Mangal Dosha")
        refs = " ".join(recs[0].classical_references)
        assert "Mansagari" in refs

    def test_ketu_12h_cites_jaimini(self):
        """Ketu-12H moksha-karaka cites Jaimini Sutra."""
        recs = translate_bhava_planet(12, "Ketu")
        refs = " ".join(recs[0].classical_references)
        assert "Jaimini" in refs

    def test_saturn_8h_cites_bphs_ayur_daya(self):
        """Saturn-8H Ayur-karaka cites BPHS Ayur-Daya."""
        recs = translate_bhava_planet(8, "Saturn")
        refs = " ".join(recs[0].classical_references)
        assert "Ayur" in refs or "BPHS" in refs

    def test_kinship_meta_principle_mentions_kali_yuga(self):
        """Kinship principle names the Kali-Yuga Individuation theme."""
        assert "Kali" in DOMAIN_META_PRINCIPLES[Domain.KINSHIP]

    def test_career_meta_principle_mentions_decentralization(self):
        """Career-wealth principle names the Rajya decentralization."""
        principle = DOMAIN_META_PRINCIPLES[Domain.CAREER_WEALTH]
        assert "decentrali" in principle.lower()

    def test_dharma_meta_principle_mentions_transmission(self):
        """Dharma principle frames the transmission shift."""
        principle = DOMAIN_META_PRINCIPLES[Domain.DHARMA]
        assert "transmission" in principle.lower()

    def test_health_meta_principle_mentions_chronic(self):
        """Health principle frames the chronic-trajectory shift."""
        principle = DOMAIN_META_PRINCIPLES[Domain.HEALTH]
        assert "chronic" in principle.lower()
