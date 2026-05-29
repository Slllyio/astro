"""Tests for app.core.reading_composer — Phase 9 final synthesis."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.dkp_modulation import Ashrama, DKPContext
from app.core.reading_composer import (
    Reading,
    ReadingClaim,
    compose_reading,
    format_reading_text,
)


@pytest.fixture
def chart() -> Chart:
    return Chart(
        asc_sign=6, asc_lon=173.99,
        planet_signs={"Sun": 3, "Moon": 12, "Mars": 4, "Mercury": 3,
                      "Jupiter": 4, "Venus": 4, "Saturn": 9,
                      "Rahu": 12, "Ketu": 6},
        planet_houses={"Sun": 10, "Moon": 7, "Mars": 11, "Mercury": 10,
                       "Jupiter": 11, "Venus": 11, "Saturn": 4,
                       "Rahu": 7, "Ketu": 1},
        planet_lons={"Sun": 88.6, "Moon": 351.0, "Mars": 120.5,
                     "Mercury": 95.2, "Jupiter": 101.8, "Venus": 102.0,
                     "Saturn": 268.4, "Rahu": 348.5, "Ketu": 168.5},
        person_id="test-baseline",
    )


@pytest.fixture
def full_dkp() -> DKPContext:
    return DKPContext(
        birth_latitude=12.97, birth_longitude=77.59,
        current_residence_country="IN", climate_mahabhuta="kapha",
        birth_date_iso="1990-07-15", age_years=35.0,
        active_mundane_event="none", active_dasha_lord="Mercury",
        ashrama=Ashrama.GRIHASTHA, marital_status="married",
        profession="engineering", prashna="career direction",
    )


class TestReadingStructure:
    """The Reading object's structural invariants."""

    def test_reading_covers_all_12_bhavas(self, chart):
        """Every bhava 1..12 has a ReadingClaim."""
        r = compose_reading(chart, DKPContext())
        assert set(r.bhava_claims.keys()) == set(range(1, 13))

    def test_each_claim_is_a_reading_claim(self, chart):
        """Type contract: bhava_claims values are ReadingClaim."""
        r = compose_reading(chart, DKPContext())
        for v in r.bhava_claims.values():
            assert isinstance(v, ReadingClaim)

    def test_lagna_identity_populated(self, chart):
        """asc_sign + lagna lord always populated."""
        r = compose_reading(chart, DKPContext())
        assert r.asc_sign == 6
        assert r.asc_lagna_lord == "Mercury"

    def test_badhakesh_resolved(self, chart):
        """Virgo Lagna (dual) → Badhakesh = 7L = Jupiter."""
        r = compose_reading(chart, DKPContext())
        assert r.badhakesh == "Jupiter"

    def test_strongest_weakest_planets_populated(self, chart):
        """Shadbala-derived strongest + weakest set."""
        r = compose_reading(chart, DKPContext())
        assert r.strongest_planet in {"Sun", "Moon", "Mars", "Mercury",
                                       "Jupiter", "Venus", "Saturn"}
        assert r.weakest_planet in {"Sun", "Moon", "Mars", "Mercury",
                                     "Jupiter", "Venus", "Saturn"}


class TestCitationsAlwaysCarry:
    """Every claim with findings carries at least one citation."""

    def test_every_claim_with_findings_cites(self, chart):
        """If there are key_findings, citations must be non-empty."""
        r = compose_reading(chart, DKPContext())
        for b, claim in r.bhava_claims.items():
            if claim.key_findings:
                assert claim.citations, (
                    f"Bhava {b} has findings but no citations — "
                    "Phase 9 contract violated"
                )


class TestDKPIntegration:
    """DKP context flows into reading focus and confidence."""

    def test_grihastha_5h_reads_as_children(self, chart):
        """Householder DKP → bhava 5 focus is children."""
        ctx = DKPContext(ashrama=Ashrama.GRIHASTHA)
        r = compose_reading(chart, ctx)
        assert "children" in r.bhava_claims[5].reading_focus

    def test_full_dkp_yields_no_open_questions(self, chart, full_dkp):
        """Completeness >= 9 → no clarifying questions surface."""
        r = compose_reading(chart, full_dkp)
        assert r.open_questions == ()

    def test_empty_dkp_yields_open_questions(self, chart):
        """Empty DKP → clarifying questions appear."""
        r = compose_reading(chart, DKPContext())
        assert len(r.open_questions) > 0


class TestGocharaOverlay:
    """Transit data overlays per-bhava trigger flags."""

    def test_gochara_skipped_when_no_transits(self, chart):
        """Without transit_signs → all gochara_triggered False."""
        r = compose_reading(chart, DKPContext())
        for claim in r.bhava_claims.values():
            assert claim.gochara_triggered is False

    def test_gochara_triggered_with_transits(self, chart):
        """With transits, at least some bhavas should trigger."""
        # Saturn + Jupiter both in sign 6 (= bhava 1 for Virgo Lagna)
        transits = {"Sun": 1, "Moon": 5, "Mars": 8, "Mercury": 2,
                    "Jupiter": 6, "Venus": 4, "Saturn": 6,
                    "Rahu": 12, "Ketu": 6}
        r = compose_reading(chart, DKPContext(), transit_signs=transits)
        triggered = [b for b, c in r.bhava_claims.items() if c.gochara_triggered]
        assert len(triggered) >= 1


class TestDashaIntegration:
    """Vimshottari and Chara dasha lord lookups."""

    def test_chara_md_skipped_without_birth_jd(self, chart):
        """No birth_jd → Chara MD is None."""
        r = compose_reading(chart, DKPContext())
        assert r.chara_md_at_target is None

    def test_chara_md_resolved_with_jds(self, chart):
        """With birth + target JD → Chara MD sign 1..12."""
        r = compose_reading(
            chart, DKPContext(),
            birth_jd=2448087.5, target_jd=2459580.0,
        )
        assert r.chara_md_at_target is not None
        assert 1 <= r.chara_md_at_target <= 12

    def test_vimshottari_md_passes_through(self, chart):
        """Caller-provided Vimshottari MD lord appears in reading."""
        r = compose_reading(
            chart, DKPContext(), vimshottari_md_lord="Mercury",
        )
        assert r.vimshottari_md_at_target == "Mercury"


class TestFormatReadingText:
    """Plain-text rendering doesn't crash and produces structured output."""

    def test_format_reading_produces_text(self, chart, full_dkp):
        """Smoke test: format_reading_text returns non-empty multi-line str."""
        r = compose_reading(chart, full_dkp)
        text = format_reading_text(r)
        assert "ASTROLOGER-LENS READING" in text
        assert len(text.splitlines()) > 20

    def test_format_includes_per_bhava_section(self, chart, full_dkp):
        """Output should mention every bhava 1..12."""
        r = compose_reading(chart, full_dkp)
        text = format_reading_text(r)
        for b in range(1, 13):
            assert f"Bhava {b:2d}" in text or f"Bhava  {b}" in text
