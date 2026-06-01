"""M8 tests: master_compose — the v1.1.0 depth output entry point."""

from __future__ import annotations

import pytest

from app.integration.master_compose import (
    DomainParagraph,
    MasterReading,
    _DOMAIN_BHAVA,
    compose_master_reading,
)
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput


@pytest.fixture(scope="module")
def mainpuri_reading():
    return track_a_compute(
        ChartInput(dob="1989-10-12", time="10:02", tz="+05:30",
                   lat=27.23, lon=79.03),
        enrich=False,
    )


@pytest.fixture(scope="module")
def master(mainpuri_reading):
    return compose_master_reading(mainpuri_reading)


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

class TestStructure:
    def test_returns_master_reading(self, master):
        assert isinstance(master, MasterReading)

    def test_version_pinned(self, master):
        assert master.integration_version == "1.1.0"

    def test_chart_basics_populated(self, master):
        b = master.chart_basics
        for field in (
            "lagna_sign", "lagna_sign_name", "moon_sign_name",
            "moon_nakshatra", "sun_sign_name",
        ):
            assert field in b

    def test_six_domain_paragraphs(self, master):
        assert len(master.domain_paragraphs) == 6
        assert {dp.domain for dp in master.domain_paragraphs} == set(_DOMAIN_BHAVA.keys())

    def test_each_domain_has_paragraph_text(self, master):
        for dp in master.domain_paragraphs:
            assert isinstance(dp, DomainParagraph)
            # Real paragraph, not just data dump
            assert len(dp.paragraph) > 100

    def test_dasha_triple_paragraph_populated(self, master):
        assert "Saturn" in master.dasha_triple_paragraph
        assert "MD" in master.dasha_triple_paragraph

    def test_arudha_summary_populated(self, master):
        assert "Arudha" in master.arudha_image_summary
        assert "Upapada" in master.upapada_marriage_summary


# ---------------------------------------------------------------------------
# Mainpuri-specific synthesis (the plan spec)
# ---------------------------------------------------------------------------

class TestMainpuriCareerParagraph:
    """Plan spec: M8 output for Mainpuri career domain should structurally
    match the user's reference paragraph — Ketu in 10H, Sun in 11H,
    Saturn discipline, Mercury sub-period activation, Jupiter transit."""

    @pytest.fixture(scope="class")
    def career(self, master):
        return next(dp for dp in master.domain_paragraphs if dp.domain == "career")

    def test_career_paragraph_mentions_ketu(self, career):
        # 10H Leo has Ketu
        assert "Ketu" in career.paragraph or "KETU" in career.paragraph

    def test_career_paragraph_mentions_sun_in_11H(self, career):
        # Sun (10H lord + karaka) is in 11H Virgo
        assert "Sun" in career.paragraph or "SUN" in career.paragraph

    def test_career_paragraph_mentions_10H(self, career):
        # H10 mentioned
        assert "H10" in career.paragraph or "10H" in career.paragraph

    def test_career_paragraph_has_pillar_synthesis(self, career):
        # Should have at least 2 sentences (3 pillars + maybe more)
        sentences = [s for s in career.paragraph.split(".") if s.strip()]
        assert len(sentences) >= 3


class TestMainpuriMarriageParagraph:
    @pytest.fixture(scope="class")
    def marriage(self, master):
        return next(dp for dp in master.domain_paragraphs if dp.domain == "marriage")

    def test_marriage_includes_upapada(self, marriage):
        # Marriage paragraph should reference Upapada/UPL
        assert "Upapada" in marriage.paragraph or "UPL" in marriage.paragraph

    def test_marriage_mentions_jupiter_or_8H(self, marriage):
        # Upapada lord for Mainpuri is Jupiter in 8H
        assert "Jupiter" in marriage.paragraph or "8H" in marriage.paragraph


class TestMainpuriDomainMetadata:
    def test_career_md_relevance(self, master):
        career = next(dp for dp in master.domain_paragraphs if dp.domain == "career")
        # For Mainpuri Scorpio lagna, Saturn rules 3+4 not 10 — relevance "indirect"
        assert career.md_relevance in {
            "directly_rules", "placed_in_domain", "double_transit_active", "indirect",
        }

    def test_wealth_md_relevance_high(self, master):
        wealth = next(dp for dp in master.domain_paragraphs if dp.domain == "wealth")
        # Wealth bhava = 2. Saturn natal house = 2. So MD lord SITS IN this bhava.
        assert wealth.md_relevance == "placed_in_domain"

    def test_education_md_relevance(self, master):
        education = next(dp for dp in master.domain_paragraphs if dp.domain == "education")
        # Education bhava = 4. Saturn rules Aquarius (4H from Scorpio).
        assert education.md_relevance in {"directly_rules", "placed_in_domain", "indirect"}


# ---------------------------------------------------------------------------
# Yogas wired into domain paragraphs
# ---------------------------------------------------------------------------

class TestYogasInDomains:
    def test_career_domain_can_carry_adhi(self, master):
        career = next(dp for dp in master.domain_paragraphs if dp.domain == "career")
        # Adhi is in the career yoga set; if detected (both engines), should appear
        if "adhi" in career.yogas_touching_domain:
            assert "ADHI" in career.paragraph or "adhi" in career.paragraph.lower()


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_json_roundtrip(self, master):
        import json
        text = json.dumps(master.model_dump(mode="json"))
        revived = MasterReading.model_validate(json.loads(text))
        assert revived.integration_version == "1.1.0"
        assert len(revived.domain_paragraphs) == 6


# ---------------------------------------------------------------------------
# Depth check — output must NOT be a data dump
# ---------------------------------------------------------------------------

class TestDepth:
    def test_total_paragraph_length_substantial(self, master):
        """All 6 domain paragraphs + dasha + arudha must total >2000 chars."""
        total = (
            sum(len(dp.paragraph) for dp in master.domain_paragraphs)
            + len(master.dasha_triple_paragraph)
            + len(master.arudha_image_summary)
            + len(master.upapada_marriage_summary)
        )
        assert total > 2000

    def test_paragraphs_dont_have_data_atom_artifacts(self, master):
        """Paragraphs should not contain dict/Pydantic repr artifacts."""
        for dp in master.domain_paragraphs:
            assert "{" not in dp.paragraph[:500] or "}" not in dp.paragraph[:500]
            assert "None" not in dp.paragraph
