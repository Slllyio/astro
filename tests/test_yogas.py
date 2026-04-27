"""Tests for `app.core.yogas.detect_yogas`.

Each test constructs a minimal d1_chart dict supplying only the planets
relevant to the yoga under test (other planets in deliberately-irrelevant
signs). The ascendant dict supplies just the `sign` field — yoga detection
ignores other ascendant attributes.
"""
from __future__ import annotations

import pytest

from app.core.yogas import detect_yogas


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _planet(name: str, sign: int) -> dict:
    """Build a minimal planet entry. Only `name` and `sign` matter for yoga
    detection; other engine fields are filled with placeholder values to
    mirror the real chart shape."""
    return {
        "name": name,
        "sign": sign,
        "longitude": (sign - 1) * 30 + 15.0,
        "sign_name": "",
        "degree_in_sign": 15.0,
        "is_retrograde": False,
    }


def _asc(sign: int) -> dict:
    """Build a minimal ascendant dict carrying just the 1..12 sign."""
    return {
        "sign": sign,
        "longitude": (sign - 1) * 30 + 0.0,
        "sign_name": "",
        "degree_in_sign": 0.0,
    }


def _yoga_names(yogas: list[dict]) -> list[str]:
    return [y["name"] for y in yogas]


# Signs deliberately chosen to never form any v1 yoga. Used as filler for
# planets irrelevant to a particular test.
NEUTRAL_FILLERS: dict[str, int] = {
    "Sun": 2,        # Taurus — not own (5), not exalted (1)
    "Moon": 3,       # Gemini — not own (4), not exalted (2)
    "Mars": 3,       # Gemini — not own (1, 8), not exalted (10)
    "Mercury": 11,   # Aquarius — not own (3, 6), not exalted (6)
    "Jupiter": 11,   # Aquarius — not own (9, 12), not exalted (4)
    "Venus": 11,     # Aquarius — not own (2, 7), not exalted (12)
    "Saturn": 3,     # Gemini — not own (10, 11), not exalted (7)
    "Rahu": 5,
    "Ketu": 11,
}


def _filler_chart(**overrides: int) -> dict:
    """Build a 9-planet d1 chart with neutral fillers, applying the supplied
    `planet=sign` overrides."""
    chart: dict = {}
    signs = {**NEUTRAL_FILLERS, **overrides}
    for planet, sign in signs.items():
        chart[planet] = _planet(planet, sign)
    return chart


# --------------------------------------------------------------------------- #
# Pancha Mahapurusha — Hamsa                                                  #
# --------------------------------------------------------------------------- #

def test_hamsa_positive_jupiter_exalted_in_kendra() -> None:
    """Jupiter in Cancer (exalted, sign=4), Lagna=Capricorn (10).
    Jupiter occupies the 7th house from Lagna (kendra) -> Hamsa forms."""
    chart = _filler_chart(Jupiter=4)
    yogas = detect_yogas(chart, _asc(10))
    assert "Hamsa" in _yoga_names(yogas)
    hamsa = next(y for y in yogas if y["name"] == "Hamsa")
    assert hamsa["type"] == "Pancha Mahapurusha"
    assert hamsa["planets_involved"] == ["Jupiter"]


def test_hamsa_negative_wrong_house() -> None:
    """Jupiter in Cancer (exalted) but Lagna=Sagittarius (9). Jupiter in the
    8th house (NOT kendra) -> no Hamsa."""
    chart = _filler_chart(Jupiter=4)
    yogas = detect_yogas(chart, _asc(9))
    assert "Hamsa" not in _yoga_names(yogas)


# --------------------------------------------------------------------------- #
# Pancha Mahapurusha — Ruchaka                                                #
# --------------------------------------------------------------------------- #

def test_ruchaka_positive_mars_exalted_in_kendra() -> None:
    """Mars in Capricorn (exalted, sign=10), Lagna=Cancer (4).
    Mars in the 7th house from Lagna (kendra) -> Ruchaka forms."""
    chart = _filler_chart(Mars=10)
    yogas = detect_yogas(chart, _asc(4))
    assert "Ruchaka" in _yoga_names(yogas)
    ruchaka = next(y for y in yogas if y["name"] == "Ruchaka")
    assert ruchaka["type"] == "Pancha Mahapurusha"
    assert ruchaka["planets_involved"] == ["Mars"]


# --------------------------------------------------------------------------- #
# Pancha Mahapurusha — Sasa                                                   #
# --------------------------------------------------------------------------- #

def test_sasa_positive_saturn_exalted_in_kendra() -> None:
    """Saturn in Libra (exalted, sign=7), Lagna=Aries (1).
    Saturn in the 7th house from Lagna (kendra) -> Sasa forms."""
    chart = _filler_chart(Saturn=7)
    yogas = detect_yogas(chart, _asc(1))
    assert "Sasa" in _yoga_names(yogas)
    sasa = next(y for y in yogas if y["name"] == "Sasa")
    assert sasa["type"] == "Pancha Mahapurusha"
    assert sasa["planets_involved"] == ["Saturn"]


# --------------------------------------------------------------------------- #
# Pancha Mahapurusha — Bhadra                                                 #
# --------------------------------------------------------------------------- #

def test_bhadra_positive_mercury_in_kendra() -> None:
    """Mercury in Virgo (own + exalted, sign=6), Lagna=Pisces (12).
    Mercury in the 7th house from Lagna (kendra) -> Bhadra forms."""
    chart = _filler_chart(Mercury=6)
    yogas = detect_yogas(chart, _asc(12))
    assert "Bhadra" in _yoga_names(yogas)
    bhadra = next(y for y in yogas if y["name"] == "Bhadra")
    assert bhadra["type"] == "Pancha Mahapurusha"
    assert bhadra["planets_involved"] == ["Mercury"]


def test_bhadra_negative_wrong_house_libra_lagna() -> None:
    """Mercury in Virgo but Lagna=Libra (7). Mercury sits in the 12th house
    (NOT kendra) -> no Bhadra."""
    chart = _filler_chart(Mercury=6)
    yogas = detect_yogas(chart, _asc(7))
    assert "Bhadra" not in _yoga_names(yogas)


# --------------------------------------------------------------------------- #
# Pancha Mahapurusha — Malavya                                                #
# --------------------------------------------------------------------------- #

def test_malavya_positive_venus_exalted_in_kendra() -> None:
    """Venus in Pisces (exalted, sign=12), Lagna=Pisces (12).
    Venus in the 1st house (kendra) -> Malavya forms."""
    chart = _filler_chart(Venus=12)
    yogas = detect_yogas(chart, _asc(12))
    assert "Malavya" in _yoga_names(yogas)
    malavya = next(y for y in yogas if y["name"] == "Malavya")
    assert malavya["type"] == "Pancha Mahapurusha"
    assert malavya["planets_involved"] == ["Venus"]


def test_malavya_negative_wrong_house_cancer_lagna() -> None:
    """Venus in Pisces but Lagna=Cancer (4). Venus sits in the 9th house
    (NOT kendra) -> no Malavya."""
    chart = _filler_chart(Venus=12)
    yogas = detect_yogas(chart, _asc(4))
    assert "Malavya" not in _yoga_names(yogas)


# --------------------------------------------------------------------------- #
# Gajakesari                                                                  #
# --------------------------------------------------------------------------- #

def test_gajakesari_positive_same_sign() -> None:
    """Jupiter sign=4, Moon sign=4. Distance 0 -> mutual 1st -> Gajakesari."""
    chart = _filler_chart(Jupiter=4, Moon=4)
    # Avoid Hamsa side-effect: Jupiter in Cancer is exalted, but with a
    # non-kendra Lagna it won't form Hamsa. Lagna=Sagittarius (9): Jupiter
    # falls in the 8th house, NOT a kendra. Distance Jupiter->Moon stays 0.
    yogas = detect_yogas(chart, _asc(9))
    assert "Gajakesari" in _yoga_names(yogas)
    gk = next(y for y in yogas if y["name"] == "Gajakesari")
    assert gk["type"] == "Lunar"
    assert set(gk["planets_involved"]) == {"Jupiter", "Moon"}


@pytest.mark.parametrize(
    ("jupiter_sign", "moon_sign", "distance"),
    [
        (1, 4, 3),    # Moon 4th from Jupiter
        (1, 7, 6),    # Moon 7th from Jupiter
        (1, 10, 9),   # Moon 10th from Jupiter
    ],
)
def test_gajakesari_positive_other_kendra_distances(
    jupiter_sign: int, moon_sign: int, distance: int
) -> None:
    """Jupiter-Moon distances 3, 6, 9 each form Gajakesari."""
    chart = _filler_chart(Jupiter=jupiter_sign, Moon=moon_sign)
    yogas = detect_yogas(chart, _asc(2))  # Taurus Lagna keeps things quiet
    assert "Gajakesari" in _yoga_names(yogas), (
        f"expected Gajakesari at distance {distance}"
    )


def test_gajakesari_negative_distance_one() -> None:
    """Jupiter sign=1, Moon sign=2. Distance 1 (Moon 2nd from Jupiter) ->
    NOT mutual kendra -> no Gajakesari."""
    chart = _filler_chart(Jupiter=1, Moon=2)
    yogas = detect_yogas(chart, _asc(2))
    assert "Gajakesari" not in _yoga_names(yogas)


# --------------------------------------------------------------------------- #
# Budha-Aditya                                                                #
# --------------------------------------------------------------------------- #

def test_budha_aditya_positive_same_sign() -> None:
    """Sun sign=5, Mercury sign=5 -> Budha-Aditya forms."""
    chart = _filler_chart(Sun=5, Mercury=5)
    yogas = detect_yogas(chart, _asc(1))
    assert "Budha-Aditya" in _yoga_names(yogas)
    ba = next(y for y in yogas if y["name"] == "Budha-Aditya")
    assert ba["type"] == "Solar"
    assert set(ba["planets_involved"]) == {"Sun", "Mercury"}


# --------------------------------------------------------------------------- #
# Empty chart                                                                 #
# --------------------------------------------------------------------------- #

def test_empty_chart_returns_no_yogas() -> None:
    """A chart explicitly arranged to form no v1 yoga returns []."""
    # Lagna=Aries (1) -> kendras are signs {1, 4, 7, 10}.
    # All planets placed in non-kendra signs, none in own/exalted.
    chart = _filler_chart(
        Sun=2,        # not Leo (5), not Aries (1)
        Moon=3,       # not Cancer (4), not Taurus (2)
        Mars=3,       # not Aries/Scorpio (1/8), not Capricorn (10)
        Mercury=11,   # not Gemini/Virgo (3/6)
        Jupiter=11,   # not Sag/Pisces (9/12), not Cancer (4)
        Venus=11,     # not Taurus/Libra (2/7), not Pisces (12)
        Saturn=3,     # not Capricorn/Aquarius (10/11), not Libra (7)
    )
    # Sanity: Jupiter(11)-Moon(3) distance = (3-11) % 12 = 4 -> no Gajakesari.
    # Sun(2) != Mercury(11) -> no Budha-Aditya.
    yogas = detect_yogas(chart, _asc(1))
    assert yogas == []
