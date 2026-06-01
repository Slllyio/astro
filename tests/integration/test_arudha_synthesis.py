"""M6 tests: arudha_image_synthesis."""

from __future__ import annotations

import pytest

from app.integration.arudha_synthesis import (
    ArudhaSynthesis,
    _ARUDHA_HOUSE_THEMES,
    _UPAPADA_HOUSE_THEMES,
    _house_from_lagna,
    synthesise_arudha,
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
def mainpuri_arudha(mainpuri_reading):
    return synthesise_arudha(mainpuri_reading)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestHouseFromLagna:
    def test_cancer_from_scorpio_is_9H(self):
        # Scorpio (8) -> Cancer (4): 4-8+12 mod 12 = 8, +1 = 9
        assert _house_from_lagna(8, 4) == 9

    def test_same_sign_is_1H(self):
        assert _house_from_lagna(5, 5) == 1

    def test_opposite_is_7H(self):
        assert _house_from_lagna(1, 7) == 7  # Aries lagna, Libra = 7H


class TestThemeTables:
    def test_all_12_arudha_themes(self):
        for h in range(1, 13):
            assert h in _ARUDHA_HOUSE_THEMES
            assert len(_ARUDHA_HOUSE_THEMES[h]) > 20

    def test_all_12_upapada_themes(self):
        for h in range(1, 13):
            assert h in _UPAPADA_HOUSE_THEMES


# ---------------------------------------------------------------------------
# Mainpuri Arudha synthesis
# ---------------------------------------------------------------------------

class TestMainpuriArudha:
    """Mainpuri Scorpio lagna with Mars in 11H Virgo gives Arudha Lagna = Cancer.
    Cancer is 9th house from Scorpio. Upapada = Sagittarius (2H from Scorpio)."""

    def test_returns_synthesis(self, mainpuri_arudha):
        assert isinstance(mainpuri_arudha, ArudhaSynthesis)

    def test_arudha_is_cancer(self, mainpuri_arudha):
        assert mainpuri_arudha.arudha_sign == 4
        assert mainpuri_arudha.arudha_sign_name == "Cancer"

    def test_arudha_house_is_9H(self, mainpuri_arudha):
        # Cancer from Scorpio = 9H
        assert mainpuri_arudha.arudha_house_from_lagna == 9

    def test_arudha_theme_mentions_dharma_or_wise(self, mainpuri_arudha):
        theme = mainpuri_arudha.arudha_house_theme.lower()
        assert "dharma" in theme or "wise" in theme or "fortunate" in theme

    def test_arudha_lord_is_moon(self, mainpuri_arudha):
        # Cancer ruled by Moon
        assert mainpuri_arudha.arudha_lord == "Moon"

    def test_arudha_lord_moon_in_4H(self, mainpuri_arudha):
        # Moon natally in 4H Aquarius for Mainpuri
        assert mainpuri_arudha.arudha_lord_house == 4

    def test_planets_in_arudha_sign(self, mainpuri_arudha):
        # Cancer is empty for Mainpuri
        assert mainpuri_arudha.planets_in_arudha == ()

    def test_image_summary_mentions_9H_and_moon(self, mainpuri_arudha):
        s = mainpuri_arudha.image_summary.lower()
        assert "9h" in s
        assert "moon" in s


class TestMainpuriUpapada:
    def test_upapada_is_sagittarius(self, mainpuri_arudha):
        assert mainpuri_arudha.upapada_sign == 9
        assert mainpuri_arudha.upapada_sign_name == "Sagittarius"

    def test_upapada_house_is_2H(self, mainpuri_arudha):
        # Sagittarius from Scorpio = 2H
        assert mainpuri_arudha.upapada_house_from_lagna == 2

    def test_upapada_theme_mentions_wealth_or_voice(self, mainpuri_arudha):
        # 2H theme mentions wealth + family + voice
        t = mainpuri_arudha.upapada_house_theme.lower()
        assert "wealth" in t or "family" in t or "voice" in t

    def test_upapada_lord_is_jupiter(self, mainpuri_arudha):
        # Sagittarius ruled by Jupiter
        assert mainpuri_arudha.upapada_lord == "Jupiter"

    def test_upapada_lord_jupiter_in_8H(self, mainpuri_arudha):
        # Jupiter natally in 8H Gemini for Mainpuri
        assert mainpuri_arudha.upapada_lord_house == 8

    def test_marriage_summary_mentions_2H_and_jupiter(self, mainpuri_arudha):
        s = mainpuri_arudha.marriage_summary.lower()
        assert "2h" in s
        assert "jupiter" in s


class TestSerialization:
    def test_json_roundtrip(self, mainpuri_arudha):
        import json
        text = json.dumps(mainpuri_arudha.model_dump(mode="json"))
        revived = ArudhaSynthesis.model_validate(json.loads(text))
        assert revived.arudha_sign_name == "Cancer"
        assert revived.upapada_sign_name == "Sagittarius"
