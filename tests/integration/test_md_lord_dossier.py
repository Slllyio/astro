"""M3 tests: md_lord_natal_dossier.

Pins Saturn-natal-for-Mainpuri behaviour exactly as specified in the plan:
Saturn in 2H Sagittarius, rules 3+4, aspects 4H/8H/11H (Saturn's special
3rd + 10th + universal 7th = houses 4, 8, 11 from 2H position).
"""

from __future__ import annotations

import pytest

from app.integration.md_lord_dossier import (
    MDLordDossier,
    _dignity_for,
    _houses_aspected,
    build_md_lord_dossier,
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
def bangalore_reading():
    return track_a_compute(
        ChartInput(dob="1990-07-15", time="12:00", tz="+05:30",
                   lat=12.97, lon=77.59),
        enrich=False,
    )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

class TestDignity:
    def test_sun_in_aries_is_exalted(self):
        assert _dignity_for("Sun", 1) == "exalted"

    def test_sun_in_libra_is_debilitated(self):
        assert _dignity_for("Sun", 7) == "debilitated"

    def test_mars_in_aries_is_own(self):
        assert _dignity_for("Mars", 1) == "own"

    def test_mars_in_scorpio_is_own(self):
        assert _dignity_for("Mars", 8) == "own"

    def test_jupiter_in_sagittarius_is_own(self):
        assert _dignity_for("Jupiter", 9) == "own"


class TestHousesAspected:
    def test_saturn_aspects_3rd_7th_10th(self):
        """Saturn in 2H aspects 4H (3rd) + 8H (7th) + 11H (10th)."""
        aspected = _houses_aspected("Saturn", 2)
        assert set(aspected) == {4, 8, 11}

    def test_jupiter_aspects_5th_7th_9th(self):
        """Jupiter in 8H aspects 12H (5th) + 2H (7th) + 4H (9th)."""
        aspected = _houses_aspected("Jupiter", 8)
        assert set(aspected) == {12, 2, 4}

    def test_mars_aspects_4th_7th_8th(self):
        """Mars in 1H aspects 4H + 7H + 8H."""
        aspected = _houses_aspected("Mars", 1)
        assert set(aspected) == {4, 7, 8}


# ---------------------------------------------------------------------------
# Mainpuri Saturn dossier — the plan's pinned-output spec
# ---------------------------------------------------------------------------

class TestMainpuriSaturnDossier:
    @pytest.fixture(scope="class")
    def saturn_dossier(self, mainpuri_reading):
        return build_md_lord_dossier(mainpuri_reading)  # Saturn MD active now

    def test_returns_dossier(self, saturn_dossier):
        assert isinstance(saturn_dossier, MDLordDossier)

    def test_planet_is_saturn(self, saturn_dossier):
        assert saturn_dossier.planet == "Saturn"

    def test_saturn_in_2H_sagittarius(self, saturn_dossier):
        # Plan spec: Saturn natal house=2, sign=Sagittarius
        assert saturn_dossier.house == 2
        assert saturn_dossier.sign == 9
        assert saturn_dossier.sign_name == "Sagittarius"

    def test_saturn_aspects_4H_8H_11H(self, saturn_dossier):
        # Plan spec: aspects_4H + aspects_8H + aspects_11H
        assert set(saturn_dossier.houses_aspected) == {4, 8, 11}

    def test_saturn_rules_3_and_4_for_scorpio(self, saturn_dossier):
        # Scorpio lagna: 3H = Capricorn (Saturn rules), 4H = Aquarius (Saturn rules)
        assert set(saturn_dossier.houses_ruled_from_lagna) == {3, 4}

    def test_saturn_avastha_populated(self, saturn_dossier):
        # Saturn at ~14° in Sagittarius (mid-sign) -> baladi=Yuva
        assert saturn_dossier.baladi_stage == "Yuva"

    def test_saturn_not_atmakaraka(self, saturn_dossier):
        # AK is Sun (highest degree 25°), not Saturn
        assert saturn_dossier.is_atmakaraka is False

    def test_md_dates_for_saturn_match_md_at_now(self, saturn_dossier):
        # Saturn MD runs 2008-12-20 to 2027-12-21
        assert "2008" in saturn_dossier.md_start_date
        assert "2027" in saturn_dossier.md_end_date

    def test_summary_line_mentions_saturn_and_2H(self, saturn_dossier):
        s = saturn_dossier.summary
        assert "Saturn" in s
        assert "2H" in s
        assert "Sagittarius" in s


# ---------------------------------------------------------------------------
# Explicit md_lord param
# ---------------------------------------------------------------------------

class TestExplicitMDLord:
    def test_can_request_other_planet(self, mainpuri_reading):
        """Pass md_lord='Jupiter' to inspect Jupiter's natal even though
        the current MD is Saturn."""
        d = build_md_lord_dossier(mainpuri_reading, md_lord="Jupiter")
        assert d.planet == "Jupiter"
        # Jupiter is in 8H Gemini for Mainpuri
        assert d.house == 8
        assert d.sign == 3
        assert d.sign_name == "Gemini"

    def test_unknown_planet_raises(self, mainpuri_reading):
        with pytest.raises(ValueError, match="not found"):
            build_md_lord_dossier(mainpuri_reading, md_lord="Pluto")


# ---------------------------------------------------------------------------
# Bangalore control
# ---------------------------------------------------------------------------

class TestBangaloreControl:
    def test_bangalore_current_md_dossier_runs(self, bangalore_reading):
        d = build_md_lord_dossier(bangalore_reading)
        assert isinstance(d, MDLordDossier)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_json_roundtrip(self, mainpuri_reading):
        import json
        d = build_md_lord_dossier(mainpuri_reading)
        as_json = json.dumps(d.model_dump(mode="json"))
        revived = MDLordDossier.model_validate(json.loads(as_json))
        assert revived.planet == d.planet
        assert revived.houses_aspected == d.houses_aspected
