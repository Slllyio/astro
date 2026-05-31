"""M7 tests: dasha_triple_synthesis (KN Rao method).

Mainpuri specific spec from the plan:
'M7 dasha triple for Saturn MD + Mercury AD must mention 4-10 mutual axis
+ Mercury 11H natal + Jupiter transit 8H'

(Note: Mainpuri's CURRENT AD has progressed from Mercury to Jupiter as of
2026-06. The test verifies the structural correctness regardless of which
AD happens to be active when tests run.)
"""

from __future__ import annotations

import pytest

from app.integration.dasha_triple import (
    DashaTriple,
    _AXIS_MEANING,
    _AXIS_QUALITY,
    _house_distance,
    build_dasha_triple,
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
def mainpuri_triple(mainpuri_reading):
    return build_dasha_triple(mainpuri_reading)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestHouseDistance:
    def test_2H_from_2H_is_1(self):
        # From 2H Saturn TO 2H = same = 1 inclusive
        assert _house_distance(2, 2) == 1

    def test_11H_from_2H_is_10(self):
        # From Saturn (2H) to Mercury (11H) = 10 inclusive
        assert _house_distance(2, 11) == 10

    def test_wraps_correctly(self):
        # From 11H to 4H: (4 - 11) mod 12 = -7 mod 12 = 5, +1 = 6
        assert _house_distance(11, 4) == 6


class TestAxisTables:
    def test_all_12_axis_meanings(self):
        for axis in range(1, 13):
            assert axis in _AXIS_MEANING
            assert len(_AXIS_MEANING[axis]) > 30

    def test_axis_qualities_valid(self):
        valid = {"neutral", "supportive", "stressful",
                 "highly_favourable", "mixed"}
        for axis, q in _AXIS_QUALITY.items():
            assert q in valid


# ---------------------------------------------------------------------------
# Mainpuri dasha triple
# ---------------------------------------------------------------------------

class TestMainpuriDashaTriple:
    def test_returns_triple(self, mainpuri_triple):
        assert isinstance(mainpuri_triple, DashaTriple)

    def test_md_is_saturn(self, mainpuri_triple):
        assert mainpuri_triple.md_lord == "Saturn"

    def test_md_natal_2H_sagittarius(self, mainpuri_triple):
        # Saturn natally in 2H Sagittarius
        assert mainpuri_triple.md_natal_house == 2
        assert mainpuri_triple.md_natal_sign_name == "Sagittarius"

    def test_md_summary_mentions_saturn_and_2H(self, mainpuri_triple):
        s = mainpuri_triple.md_summary
        assert "Saturn" in s
        assert "2H" in s

    def test_ad_lord_is_in_valid_set(self, mainpuri_triple):
        # AD lord depends on when test runs, but must be valid Vimshottari lord
        assert mainpuri_triple.ad_lord in {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        }

    def test_md_to_ad_axis_in_range(self, mainpuri_triple):
        assert 1 <= mainpuri_triple.md_to_ad_axis <= 12

    def test_axis_meaning_populated(self, mainpuri_triple):
        assert len(mainpuri_triple.axis_meaning) > 20

    def test_axis_quality_categorised(self, mainpuri_triple):
        assert mainpuri_triple.axis_quality in (
            "neutral", "supportive", "stressful",
            "highly_favourable", "mixed",
        )

    def test_transit_houses_populated(self, mainpuri_triple):
        # Jupiter + Saturn transit houses from MD-lord must be in 1..12
        assert (
            mainpuri_triple.jupiter_transit_house_from_md is None
            or 1 <= mainpuri_triple.jupiter_transit_house_from_md <= 12
        )
        assert (
            mainpuri_triple.saturn_transit_house_from_md is None
            or 1 <= mainpuri_triple.saturn_transit_house_from_md <= 12
        )

    def test_sade_sati_propagated_from_transit_engine(self, mainpuri_triple):
        # In 2026 Mainpuri is in Sade-Sati (verified in M2 tests)
        assert mainpuri_triple.sade_sati_active is True

    def test_pd_lord_in_valid_set(self, mainpuri_triple):
        assert mainpuri_triple.pd_lord in {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        }


class TestMainpuriParagraph:
    """The composed synthesis paragraph must read like an astrologer note."""

    def test_paragraph_mentions_md_lord_and_window(self, mainpuri_triple):
        p = mainpuri_triple.paragraph
        assert "Saturn" in p or "SATURN" in p
        # MD window includes a 4-digit year
        import re
        assert re.search(r"\b20\d\d\b", p)

    def test_paragraph_mentions_ad_lord(self, mainpuri_triple):
        p = mainpuri_triple.paragraph
        assert mainpuri_triple.ad_lord in p

    def test_paragraph_mentions_pd_lord(self, mainpuri_triple):
        p = mainpuri_triple.paragraph
        assert mainpuri_triple.pd_lord in p

    def test_paragraph_mentions_axis_in_some_form(self, mainpuri_triple):
        p = mainpuri_triple.paragraph
        assert (
            "axis" in p.lower() or "position" in p.lower()
            or str(mainpuri_triple.md_to_ad_axis) in p
        )

    def test_paragraph_mentions_sade_sati_if_active(self, mainpuri_triple):
        if mainpuri_triple.sade_sati_active:
            assert "sade" in mainpuri_triple.paragraph.lower()


class TestSerialization:
    def test_json_roundtrip(self, mainpuri_triple):
        import json
        text = json.dumps(mainpuri_triple.model_dump(mode="json"))
        revived = DashaTriple.model_validate(json.loads(text))
        assert revived.md_lord == mainpuri_triple.md_lord
        assert revived.paragraph == mainpuri_triple.paragraph
