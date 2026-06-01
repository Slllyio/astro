"""M4 tests: three_pillar_bhava_synthesis.

Pins the plan spec: M4 three-pillar for 10H Leo (Mainpuri) must mention
Ketu occupant + Sun in 11H lord+karaka.
"""

from __future__ import annotations

import pytest

from app.integration.three_pillar import (
    ThreePillarBhava,
    ThreePillarReading,
    _bhava_sign,
    _BHAVA_KARAKAS,
    build_three_pillar_reading,
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
def mainpuri_reading_pillars(mainpuri_reading):
    return build_three_pillar_reading(mainpuri_reading)


@pytest.fixture(scope="module")
def bangalore_reading():
    return track_a_compute(
        ChartInput(dob="1990-07-15", time="12:00", tz="+05:30",
                   lat=12.97, lon=77.59),
        enrich=False,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestBhavaSign:
    def test_first_house_equals_lagna(self):
        assert _bhava_sign(8, 1) == 8  # Scorpio lagna -> 1H = Scorpio

    def test_tenth_house_for_scorpio_is_leo(self):
        # Scorpio (8) + 9 = 17 mod 12 = 5 = Leo
        assert _bhava_sign(8, 10) == 5

    def test_wraps_correctly(self):
        # 12H from Aquarius (11) = Capricorn (10): 11+11 mod 12 = 10
        assert _bhava_sign(11, 12) == 10


class TestKarakaTable:
    def test_all_12_houses_have_karaka(self):
        for h in range(1, 13):
            assert h in _BHAVA_KARAKAS
            assert _BHAVA_KARAKAS[h] in {
                "Sun", "Moon", "Mars", "Mercury", "Jupiter",
                "Venus", "Saturn",
            }

    def test_4H_karaka_is_moon(self):
        assert _BHAVA_KARAKAS[4] == "Moon"

    def test_10H_karaka_is_sun(self):
        assert _BHAVA_KARAKAS[10] == "Sun"

    def test_7H_karaka_is_venus(self):
        assert _BHAVA_KARAKAS[7] == "Venus"


# ---------------------------------------------------------------------------
# Mainpuri three-pillar reading
# ---------------------------------------------------------------------------

class TestMainpuriThreePillarStructure:
    def test_returns_reading_with_12_bhavas(self, mainpuri_reading_pillars):
        assert isinstance(mainpuri_reading_pillars, ThreePillarReading)
        assert set(mainpuri_reading_pillars.per_bhava.keys()) == set(range(1, 13))

    def test_lagna_is_scorpio(self, mainpuri_reading_pillars):
        assert mainpuri_reading_pillars.lagna_sign == 8
        assert mainpuri_reading_pillars.lagna_sign_name == "Scorpio"


class TestMainpuri10HSpec:
    """Plan spec: 10H Leo, Ketu occupant, Sun in 11H lord+karaka."""

    @pytest.fixture(scope="class")
    def h10(self, mainpuri_reading):
        r = build_three_pillar_reading(mainpuri_reading)
        return r.per_bhava[10]

    def test_10H_is_leo(self, h10):
        assert h10.bhava_sign == 5
        assert h10.bhava_sign_name == "Leo"

    def test_10H_occupant_includes_ketu(self, h10):
        assert "Ketu" in h10.occupants

    def test_10H_lord_is_sun(self, h10):
        # Leo is ruled by Sun
        assert h10.lord_planet == "Sun"

    def test_10H_lord_sun_in_11H(self, h10):
        # Sun is natally in 11H Virgo for Mainpuri
        assert h10.lord_house == 11

    def test_10H_karaka_is_sun_same_as_lord(self, h10):
        assert h10.karaka_planet == "Sun"
        # Same planet rules + karakas 10H — should be noted in synthesis
        assert any("same planet" in line.lower() for line in h10.synthesis_lines)

    def test_10H_synthesis_lines_have_three_pillars(self, h10):
        assert len(h10.synthesis_lines) == 3
        # Lines should mention Ketu (occupant pillar), Sun (lord), Sun (karaka)
        joined = " ".join(h10.synthesis_lines).lower()
        assert "ketu" in joined
        assert "sun" in joined


class TestMainpuri7HSpec:
    """Sanity: 7H Taurus has Venus as lord but Mars rules from natal Scorpio lagna."""

    def test_7H_lord_is_venus(self, mainpuri_reading_pillars):
        h7 = mainpuri_reading_pillars.per_bhava[7]
        assert h7.lord_planet == "Venus"

    def test_7H_karaka_is_venus(self, mainpuri_reading_pillars):
        h7 = mainpuri_reading_pillars.per_bhava[7]
        assert h7.karaka_planet == "Venus"


class TestMainpuri11HStellium:
    """11H Virgo has 3 occupants for Mainpuri: Sun + Mars + Mercury."""

    def test_11H_has_three_occupants(self, mainpuri_reading_pillars):
        h11 = mainpuri_reading_pillars.per_bhava[11]
        assert set(h11.occupants) == {"Sun", "Mars", "Mercury"}

    def test_11H_synthesis_mentions_stellium_planets(self, mainpuri_reading_pillars):
        h11 = mainpuri_reading_pillars.per_bhava[11]
        text = " ".join(h11.synthesis_lines).lower()
        assert "sun" in text
        assert "mars" in text
        assert "mercury" in text


class TestCompositeLabels:
    def test_each_bhava_has_valid_label(self, mainpuri_reading_pillars):
        labels = {"very_strong", "strong", "mixed", "weak", "afflicted"}
        for h in mainpuri_reading_pillars.per_bhava.values():
            assert h.composite_label in labels

    def test_score_in_clamp_range(self, mainpuri_reading_pillars):
        for h in mainpuri_reading_pillars.per_bhava.values():
            assert -6.0 <= h.composite_score <= 6.0


# ---------------------------------------------------------------------------
# Bangalore control + serialisation
# ---------------------------------------------------------------------------

class TestBangaloreControl:
    def test_bangalore_lagna_virgo(self, bangalore_reading):
        r = build_three_pillar_reading(bangalore_reading)
        assert r.lagna_sign == 6
        assert r.lagna_sign_name == "Virgo"


class TestSerialization:
    def test_json_roundtrip(self, mainpuri_reading_pillars):
        import json
        as_json = json.dumps(mainpuri_reading_pillars.model_dump(mode="json"))
        revived = ThreePillarReading.model_validate(json.loads(as_json))
        assert set(revived.per_bhava.keys()) == set(range(1, 13))
        assert revived.per_bhava[10].lord_planet == "Sun"
