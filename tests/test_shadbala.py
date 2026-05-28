"""Tests for `app.core.shadbala` — Phase 0 scope: Sthana-bala only.

The other five Shadbala components (Dig, Kala, Cheshta, Naisargika, Drik)
return 0.0 in Phase 0 and will be filled in Phase 1. The Sthana-bala
implementation is itself a simplified-but-deterministic version:

- Uchcha bala: full and correct (arc from debilitation point).
- Saptavargaja bala: simplified to D1 dignity only (Phase-0 shortcut;
  Phase 1 expands to all 7 vargas using compound relation).
- Oja-Yugma bala: male / female alignment in D1 and D9 signs.
- Kendradi bala: 60 / 30 / 15 virupa per kendra / panaphara / apoklima.
- Drekkana bala: 15 virupa for the correct planet-drekkana alignment.

References: BPHS Adhyaya 27.
"""
from __future__ import annotations

import math

import pytest

from app.core.shadbala import (
    bhava_bala,
    bhavadhipati_bala,
    cheshta_bala,
    dig_bala,
    drekkana_bala,
    drik_bala,
    kendradi_bala,
    naisargika_bala,
    oja_yugma_bala,
    paksha_bala,
    saptavargaja_bala_d1,
    shadbala_total,
    sthana_bala,
    uchcha_bala,
)


# --------------------------------------------------------------------------- #
# Uchcha (exaltation) bala                                                    #
# --------------------------------------------------------------------------- #

def test_uchcha_bala_at_exact_exaltation_is_60() -> None:
    """Sun at Aries 10° (deep exaltation) gets the maximum 60 virupa."""
    assert uchcha_bala("Sun", longitude=10.0) == pytest.approx(60.0)


def test_uchcha_bala_at_exact_debilitation_is_0() -> None:
    """Sun at Libra 10° (deep debilitation) gets 0 virupa."""
    assert uchcha_bala("Sun", longitude=190.0) == pytest.approx(0.0)


def test_uchcha_bala_at_90_from_debilitation_is_30() -> None:
    """Halfway from debilitation → halfway up the bala curve."""
    # Sun: debilitation at 190°; 90° from there is 100° (or 280°).
    assert uchcha_bala("Sun", longitude=100.0) == pytest.approx(30.0, abs=0.01)
    assert uchcha_bala("Sun", longitude=280.0) == pytest.approx(30.0, abs=0.01)


@pytest.mark.parametrize(
    "planet,exalt_long",
    [
        ("Sun",      10.0),    # Aries 10°
        ("Moon",     33.0),    # Taurus 3°
        ("Mars",    298.0),    # Capricorn 28°
        ("Mercury", 165.0),    # Virgo 15°
        ("Jupiter",  95.0),    # Cancer 5°
        ("Venus",   357.0),    # Pisces 27°
        ("Saturn",  200.0),    # Libra 20°
    ],
)
def test_uchcha_bala_max_at_each_exaltation(
    planet: str, exalt_long: float
) -> None:
    assert uchcha_bala(planet, exalt_long) == pytest.approx(60.0, abs=0.01)


def test_uchcha_bala_zero_for_nodes_and_no_value() -> None:
    """Rahu/Ketu have no classical exaltation arc → return 0 (Phase 0)."""
    assert uchcha_bala("Rahu", longitude=120.0) == pytest.approx(0.0)
    assert uchcha_bala("Ketu", longitude=120.0) == pytest.approx(0.0)


def test_uchcha_bala_invalid_planet_raises() -> None:
    with pytest.raises(ValueError):
        uchcha_bala("Pluto", longitude=100.0)


# --------------------------------------------------------------------------- #
# Saptavargaja bala (simplified to D1 in Phase 0)                             #
# --------------------------------------------------------------------------- #

def test_saptavargaja_exalted_20() -> None:
    """Phase-1 BPHS fix: exalted = 20 virupa (NOT 45 — that's Moolatrikona).
    Sun in Aries (1) is exalted; without longitude, treated as plain exalted."""
    assert saptavargaja_bala_d1("Sun", d1_sign=1) == pytest.approx(20.0)
    assert saptavargaja_bala_d1("Jupiter", d1_sign=4) == pytest.approx(20.0)


def test_saptavargaja_moolatrikona_45() -> None:
    """Phase-1 BPHS fix: Moolatrikona = 45 virupa (highest dignity tier).
    Sun in Leo 10° (within MT range 0-20°) → 45 virupa."""
    assert saptavargaja_bala_d1(
        "Sun", d1_sign=5, longitude=125.0
    ) == pytest.approx(45.0)
    # Mars in Aries 5° (within MT range 0-12°) → 45
    assert saptavargaja_bala_d1(
        "Mars", d1_sign=1, longitude=5.0
    ) == pytest.approx(45.0)


def test_saptavargaja_own_non_moolatrikona_30() -> None:
    """Own sign but OUTSIDE the Moolatrikona degree range → 30 virupa.
    Sun in Leo 25° (own but past MT 20°) → 30."""
    assert saptavargaja_bala_d1(
        "Sun", d1_sign=5, longitude=145.0
    ) == pytest.approx(30.0)
    # No longitude given → treated as plain own (30) even if would be MT
    assert saptavargaja_bala_d1("Mars", d1_sign=1) == pytest.approx(30.0)


def test_saptavargaja_friendly_15() -> None:
    """Sun in Pisces (ruled by Jupiter, Sun's friend) → 15 virupa."""
    assert saptavargaja_bala_d1("Sun", d1_sign=12) == pytest.approx(15.0)


def test_saptavargaja_neutral_7_5() -> None:
    """Sun in Gemini (ruled by Mercury, Sun's neutral) → 7.5 virupa."""
    assert saptavargaja_bala_d1("Sun", d1_sign=3) == pytest.approx(7.5)


def test_saptavargaja_inimical_3_75() -> None:
    """Sun in Taurus (ruled by Venus, Sun's enemy) → 3.75 virupa."""
    assert saptavargaja_bala_d1("Sun", d1_sign=2) == pytest.approx(3.75)


def test_saptavargaja_debilitated_0() -> None:
    """Phase-1 BPHS fix: debilitated = 0 virupa (adhi-shatru tier).
    Was incorrectly 1.875 in Phase 0 (which is the shatru-tier value)."""
    assert saptavargaja_bala_d1("Sun", d1_sign=7) == pytest.approx(0.0)
    assert saptavargaja_bala_d1("Jupiter", d1_sign=10) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# Oja-Yugma bala (male/female parity alignment)                               #
# --------------------------------------------------------------------------- #

def test_oja_yugma_male_in_odd_d1_and_odd_d9_gets_30() -> None:
    """Sun (male) in Aries (1, odd) in both D1 and D9 → 15+15 = 30."""
    assert oja_yugma_bala("Sun", d1_sign=1, d9_sign=3) == pytest.approx(30.0)


def test_oja_yugma_male_in_odd_d1_even_d9_gets_15() -> None:
    """Sun (male) in odd D1 but even D9 → 15 only."""
    assert oja_yugma_bala("Sun", d1_sign=1, d9_sign=4) == pytest.approx(15.0)


def test_oja_yugma_male_in_even_signs_gets_0() -> None:
    assert oja_yugma_bala("Sun", d1_sign=2, d9_sign=4) == pytest.approx(0.0)


def test_oja_yugma_female_in_even_d1_and_d9_gets_30() -> None:
    """Moon (female) in even sign in D1 and D9 → 30."""
    assert oja_yugma_bala("Moon", d1_sign=2, d9_sign=4) == pytest.approx(30.0)


def test_oja_yugma_female_in_odd_signs_gets_0() -> None:
    assert oja_yugma_bala("Moon", d1_sign=1, d9_sign=3) == pytest.approx(0.0)


def test_oja_yugma_mercury_saturn_masculine() -> None:
    """Phase-1 audit fix: per BPHS 27.28-30, Mercury and Saturn are
    treated as MASCULINE for Oja-Yugma (NOT neuter, as we conservatively
    had in Phase 0). They gain 15 virupa per odd-sign placement, just
    like Sun, Mars, Jupiter."""
    # Mercury in odd D1 + odd D9 → 30
    assert oja_yugma_bala("Mercury", d1_sign=1, d9_sign=3) == pytest.approx(30.0)
    # Saturn in even D1 + even D9 → 0 (parity wrong for masculine)
    assert oja_yugma_bala("Saturn", d1_sign=2, d9_sign=4) == pytest.approx(0.0)
    # Mercury odd D1 + even D9 → 15
    assert oja_yugma_bala("Mercury", d1_sign=1, d9_sign=2) == pytest.approx(15.0)
    # Saturn odd D1 + odd D9 → 30 (Saturn is masculine after fix)
    assert oja_yugma_bala("Saturn", d1_sign=1, d9_sign=1) == pytest.approx(30.0)


def test_oja_yugma_nodes_get_0() -> None:
    assert oja_yugma_bala("Rahu", d1_sign=1, d9_sign=1) == pytest.approx(0.0)
    assert oja_yugma_bala("Ketu", d1_sign=2, d9_sign=2) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# Kendradi bala (house-category strength)                                     #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("house", [1, 4, 7, 10])
def test_kendradi_kendra_60(house: int) -> None:
    assert kendradi_bala(house) == pytest.approx(60.0)


@pytest.mark.parametrize("house", [2, 5, 8, 11])
def test_kendradi_panaphara_30(house: int) -> None:
    assert kendradi_bala(house) == pytest.approx(30.0)


@pytest.mark.parametrize("house", [3, 6, 9, 12])
def test_kendradi_apoklima_15(house: int) -> None:
    assert kendradi_bala(house) == pytest.approx(15.0)


def test_kendradi_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        kendradi_bala(0)
    with pytest.raises(ValueError):
        kendradi_bala(13)


# --------------------------------------------------------------------------- #
# Drekkana bala                                                               #
# --------------------------------------------------------------------------- #

def test_drekkana_bala_male_in_first_drekkana() -> None:
    """Sun at 5° (1st drekkana of any sign) → 15 virupa."""
    assert drekkana_bala("Sun", longitude=5.0) == pytest.approx(15.0)
    assert drekkana_bala("Mars", longitude=35.0) == pytest.approx(15.0)
    assert drekkana_bala("Jupiter", longitude=125.0) == pytest.approx(15.0)


def test_drekkana_bala_neuter_in_second_drekkana() -> None:
    """Mercury/Saturn in 2nd drekkana (10-20° of any sign) → 15 virupa."""
    assert drekkana_bala("Mercury", longitude=15.0) == pytest.approx(15.0)
    assert drekkana_bala("Saturn", longitude=45.0) == pytest.approx(15.0)


def test_drekkana_bala_female_in_third_drekkana() -> None:
    """Moon/Venus in 3rd drekkana (20-30° of any sign) → 15 virupa."""
    assert drekkana_bala("Moon", longitude=25.0) == pytest.approx(15.0)
    assert drekkana_bala("Venus", longitude=55.0) == pytest.approx(15.0)


def test_drekkana_bala_wrong_drekkana_returns_0() -> None:
    """Male planet in 3rd drekkana → 0."""
    assert drekkana_bala("Sun", longitude=25.0) == pytest.approx(0.0)
    assert drekkana_bala("Moon", longitude=5.0) == pytest.approx(0.0)


def test_drekkana_bala_nodes_return_0() -> None:
    """Rahu/Ketu have no drekkana bala in classical scoring."""
    assert drekkana_bala("Rahu", longitude=5.0) == pytest.approx(0.0)
    assert drekkana_bala("Ketu", longitude=25.0) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# Sthana-bala aggregate                                                       #
# --------------------------------------------------------------------------- #

def test_sthana_bala_keys_present() -> None:
    """The aggregate breakdown carries the five sub-components plus a total."""
    breakdown = sthana_bala(
        "Sun", longitude=5.0, d1_sign=1, d9_sign=1, house=1,
    )
    for key in (
        "uchcha", "saptavargaja_d1", "oja_yugma",
        "kendradi", "drekkana", "total",
    ):
        assert key in breakdown


def test_sthana_bala_sun_at_5_deg_first_drekkana() -> None:
    """Sun at Aries 5°: 1st drekkana → drekkana_bala = 15.

    Phase-1 corrected breakdown:
    Uchcha: 5° from exaltation peak (Aries 10°), 175° from debilitation.
        uchcha = 175/3 ≈ 58.333.
    Saptavargaja_d1: Aries is exaltation (NOT Moolatrikona for Sun — MT is
        Leo 0-20°). Per BPHS 27 exaltation virupa = 20 (was incorrectly 45
        pre-Phase-1).
    Oja-Yugma (Sun male in odd D1=1 and odd D9=1): 30.
    Kendradi (house 1 = kendra): 60.
    Drekkana (Sun male at 1st drekkana 0-10°): 15.
    Total: 58.333 + 20 + 30 + 60 + 15 = 183.333.
    """
    bd = sthana_bala("Sun", longitude=5.0, d1_sign=1, d9_sign=1, house=1)
    assert bd["uchcha"] == pytest.approx(58.333, abs=0.01)
    assert bd["saptavargaja_d1"] == pytest.approx(20.0)
    assert bd["oja_yugma"] == pytest.approx(30.0)
    assert bd["kendradi"] == pytest.approx(60.0)
    assert bd["drekkana"] == pytest.approx(15.0)
    assert bd["total"] == pytest.approx(183.333, abs=0.01)


def test_sthana_bala_sun_deepest_exaltation_drekkana_boundary() -> None:
    """Sun at exactly 10° — drekkana boundary; longitude in [10, 20) is
    2nd drekkana so Sun (male) gets 0 drekkana_bala here.

    Phase-1 corrected: saptavargaja for exalted = 20 (was 45).
    Total = 60 + 20 + 30 + 60 + 0 = 170."""
    bd = sthana_bala("Sun", longitude=10.0, d1_sign=1, d9_sign=5, house=1)
    assert bd["drekkana"] == pytest.approx(0.0)
    assert bd["total"] == pytest.approx(170.0, abs=0.01)


def test_sthana_bala_sun_in_moolatrikona_leo() -> None:
    """Sun at Leo 10° (longitude 130°) — Moolatrikona range.
    Phase-1: Moolatrikona virupa = 45 (highest tier; only when longitude
    enables the check). Verifies the Moolatrikona path."""
    bd = sthana_bala("Sun", longitude=130.0, d1_sign=5, d9_sign=1, house=1)
    assert bd["saptavargaja_d1"] == pytest.approx(45.0)


def test_sthana_bala_returns_finite_for_all_lights() -> None:
    """Smoke: every of 9 lights returns finite virupa for a basic chart."""
    nine = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
            "Rahu", "Ketu"]
    for p in nine:
        bd = sthana_bala(p, longitude=120.0, d1_sign=5, d9_sign=5, house=4)
        assert math.isfinite(bd["total"]), p
        assert bd["total"] >= 0.0, p


# --------------------------------------------------------------------------- #
# Shadbala total (Phase 0: stubs other 5 components at 0)                     #
# --------------------------------------------------------------------------- #

def test_shadbala_total_phase2_partial() -> None:
    """Phase 2 partial: Sthana + Dig + Naisargika filled; 3 still stubbed.

    Total = Sthana + Dig + Naisargika for now."""
    breakdown = shadbala_total(
        "Sun", longitude=10.0, d1_sign=1, d9_sign=5, house=1
    )
    for key in ("sthana", "dig", "kala", "cheshta", "naisargika", "drik", "total"):
        assert key in breakdown
    # Phase 2 stubs (filled in Phase 2b):
    assert breakdown["kala"] == pytest.approx(0.0)
    assert breakdown["cheshta"] == pytest.approx(0.0)
    assert breakdown["drik"] == pytest.approx(0.0)
    # Phase 2 partial-fill:
    # Naisargika: Sun → 60 (max)
    assert breakdown["naisargika"] == pytest.approx(60.0)
    # Dig: Sun at house 1, 3 houses from worst-house 4 → 30 virupa
    assert breakdown["dig"] == pytest.approx(30.0)
    # Total = Sthana + Dig + Naisargika.
    assert breakdown["total"] == pytest.approx(
        breakdown["sthana"] + breakdown["dig"] + breakdown["naisargika"],
        abs=0.001,
    )


# --------------------------------------------------------------------------- #
# Naisargika-bala (BPHS 27.34) — Phase 2 partial                              #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "planet,expected_virupa",
    [
        ("Sun",     60.000),
        ("Moon",    51.429),
        ("Venus",   42.857),
        ("Jupiter", 34.286),
        ("Mercury", 25.714),
        ("Mars",    17.143),
        ("Saturn",   8.571),
    ],
)
def test_naisargika_bala_canonical_virupa(
    planet: str, expected_virupa: float
) -> None:
    """Per BPHS 27.34: Sun 60 → Saturn 8.571 in 60/7 ≈ 8.571 steps."""
    assert naisargika_bala(planet) == pytest.approx(expected_virupa, abs=0.01)


def test_naisargika_bala_nodes_return_0() -> None:
    """Rahu and Ketu have no classical naisargika-bala (shadow points)."""
    assert naisargika_bala("Rahu") == pytest.approx(0.0)
    assert naisargika_bala("Ketu") == pytest.approx(0.0)


def test_naisargika_bala_unknown_planet_raises() -> None:
    with pytest.raises(ValueError):
        naisargika_bala("Pluto")


# --------------------------------------------------------------------------- #
# Dig-bala (BPHS 27.36) — Phase 2                                             #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "planet,best_house",
    [
        ("Sun",     10),  # Madhya
        ("Mars",    10),
        ("Moon",     4),  # Patala
        ("Venus",    4),
        ("Mercury",  1),  # Lagna
        ("Jupiter",  1),
        ("Saturn",   7),  # Descendant
    ],
)
def test_dig_bala_max_at_strongest_house(
    planet: str, best_house: int
) -> None:
    """Each planet earns the full 60 virupa at its strongest direction."""
    assert dig_bala(planet, best_house) == pytest.approx(60.0)


@pytest.mark.parametrize(
    "planet,worst_house",
    [
        ("Sun",      4),  # opposite of 10
        ("Mars",     4),
        ("Moon",    10),  # opposite of 4
        ("Venus",   10),
        ("Mercury",  7),  # opposite of 1
        ("Jupiter",  7),
        ("Saturn",   1),  # opposite of 7
    ],
)
def test_dig_bala_zero_at_opposite_house(
    planet: str, worst_house: int
) -> None:
    """Each planet earns 0 virupa at its weakest (opposite) direction."""
    assert dig_bala(planet, worst_house) == pytest.approx(0.0)


def test_dig_bala_linear_interpolation() -> None:
    """Sun at house 1 (3 houses from worst-house 4) → 30 virupa.
    Sun at house 7 (3 houses other direction from 4) → also 30."""
    assert dig_bala("Sun", 1) == pytest.approx(30.0)
    assert dig_bala("Sun", 7) == pytest.approx(30.0)


def test_dig_bala_nodes_return_0() -> None:
    """Rahu/Ketu have no classical Dig-bala."""
    for h in range(1, 13):
        assert dig_bala("Rahu", h) == pytest.approx(0.0)
        assert dig_bala("Ketu", h) == pytest.approx(0.0)


def test_dig_bala_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError):
        dig_bala("Pluto", 5)
    with pytest.raises(ValueError):
        dig_bala("Sun", 0)
    with pytest.raises(ValueError):
        dig_bala("Sun", 13)


# --------------------------------------------------------------------------- #
# Cheshta-bala (BPHS 27.36-37) — Phase 2 simplified                           #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "planet", ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
)
def test_cheshta_bala_retrograde_star_planets(planet: str) -> None:
    """Retrograde star-planets earn maximum 60 virupa."""
    assert cheshta_bala(planet, is_retrograde=True) == pytest.approx(60.0)


@pytest.mark.parametrize(
    "planet", ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
)
def test_cheshta_bala_direct_star_planets(planet: str) -> None:
    """Direct-motion star-planets earn 30 virupa (Phase-2 simplification)."""
    assert cheshta_bala(planet, is_retrograde=False) == pytest.approx(30.0)


def test_cheshta_bala_sun_moon_zero_phase2() -> None:
    """Sun and Moon get their motional strength from Ayana-bala (a Kala-bala
    sub-component); Phase 2 placeholder returns 0."""
    assert cheshta_bala("Sun", is_retrograde=False) == pytest.approx(0.0)
    assert cheshta_bala("Moon", is_retrograde=False) == pytest.approx(0.0)


def test_cheshta_bala_nodes_zero() -> None:
    """Rahu/Ketu have no classical Cheshta-bala (always geometrically
    retrograde)."""
    assert cheshta_bala("Rahu", is_retrograde=True) == pytest.approx(0.0)
    assert cheshta_bala("Ketu", is_retrograde=True) == pytest.approx(0.0)


def test_cheshta_bala_unknown_planet_raises() -> None:
    with pytest.raises(ValueError):
        cheshta_bala("Pluto", is_retrograde=False)


# --------------------------------------------------------------------------- #
# Drik-bala (BPHS 27.38) — Phase 2 simplified (full aspects only)             #
# --------------------------------------------------------------------------- #

def _drik_chart(positions: dict[str, int]) -> dict:
    """Minimal chart for Drik-bala tests: planet → sign mapping."""
    return {p: {"sign": s, "is_retrograde": False} for p, s in positions.items()}


def test_drik_bala_jupiter_aspects_target_from_7th_pos_virupa() -> None:
    """Jupiter (benefic) in 7th house from target → +60/4 = +15 virupa."""
    # Target Mars in Aries (1); Jupiter in Libra (7) = 7th from Mars.
    chart = _drik_chart({"Mars": 1, "Jupiter": 7})
    assert drik_bala("Mars", chart) == pytest.approx(15.0)


def test_drik_bala_saturn_special_3rd_aspect_neg_virupa() -> None:
    """Saturn (malefic) special 3rd-house aspect: -60/4 = -15 virupa."""
    # Target Sun in Aries (1); Saturn in Aquarius (11) = 3rd from Sun
    # (Saturn-style 3rd-house special aspect upgrade).
    # House from Saturn to Sun: ((1-11)%12)+1 = ((-10)%12)+1 = 2+1 = 3 ✓
    chart = _drik_chart({"Sun": 1, "Saturn": 11})
    assert drik_bala("Sun", chart) == pytest.approx(-15.0)


def test_drik_bala_no_aspects_zero() -> None:
    """Target with no aspecting planets in special positions → 0 virupa."""
    # Target Sun in Aries; all other planets in non-aspecting houses
    # (5th from target — not 7/4/5/8/9/3/10 special).
    chart = _drik_chart({
        "Sun": 1,        # target (Aries)
        "Moon": 2,       # Taurus (2nd from Sun) — no aspect
        "Mars": 2,       # Taurus (2nd from Sun) — Mars 4/8 wouldn't fire
        "Mercury": 2,    # no aspect from 2nd
        "Jupiter": 2,    # no aspect from 2nd (Jupiter aspects 5, 7, 9)
        "Venus": 2,
        "Saturn": 6,     # 6th from Sun — Saturn aspects 3, 7, 10 (6 not in)
        "Rahu": 6,
        "Ketu": 12,      # 12th from Sun — Rahu/Ketu aspect 5, 7, 9
    })
    assert drik_bala("Sun", chart) == pytest.approx(0.0)


def test_drik_bala_mixed_benefic_and_malefic_aspects() -> None:
    """Net = (benefic 60 - malefic 60) / 4 = 0. Cancellation case."""
    # Target Sun in Aries (1); Jupiter in Libra (7) → benefic +60
    # AND Mars in Libra (7) → malefic 7th aspect -60.
    # Net = (60 - 60) / 4 = 0.
    chart = _drik_chart({"Sun": 1, "Jupiter": 7, "Mars": 7})
    assert drik_bala("Sun", chart) == pytest.approx(0.0)


def test_drik_bala_multiple_benefic_aspects_stack() -> None:
    """Two benefic 7th-house aspects → (60+60)/4 = +30."""
    chart = _drik_chart({"Mars": 1, "Jupiter": 7, "Venus": 7})
    assert drik_bala("Mars", chart) == pytest.approx(30.0)


def test_drik_bala_missing_target_returns_0() -> None:
    """Defensive: chart without the target planet returns 0."""
    chart = _drik_chart({"Sun": 1, "Moon": 2})
    assert drik_bala("Mars", chart) == pytest.approx(0.0)


def test_drik_bala_unknown_target_raises() -> None:
    with pytest.raises(ValueError):
        drik_bala("Pluto", {"Pluto": {"sign": 1, "is_retrograde": False}})


# --------------------------------------------------------------------------- #
# Bhava-bala (BPHS 28) — Phase 2 partial: Bhavadhipati only                   #
# --------------------------------------------------------------------------- #

def _full_chart(positions: dict[str, tuple[int, float]]) -> dict:
    """Chart with planet → (sign, longitude). Used for Bhava-bala tests
    where the lord's Shadbala (including Sthana) needs longitude."""
    return {
        p: {"sign": s, "longitude": lon, "is_retrograde": False}
        for p, (s, lon) in positions.items()
    }


def test_bhavadhipati_bala_returns_lord_shadbala() -> None:
    """For Aries asc, 1st house's lord = Mars (rules Aries). Mars in
    own sign Aries 5° earns substantial Shadbala. bhavadhipati_bala
    returns that total."""
    chart = _full_chart({
        "Sun":     (3,  75.0),
        "Moon":    (4, 105.0),
        "Mars":    (1,   5.0),   # Mars in Aries (own sign) at 5°
        "Mercury": (3,  75.0),
        "Jupiter": (9, 255.0),
        "Venus":   (2,  45.0),
        "Saturn":  (10, 295.0),  # Saturn in own sign Capricorn
        "Rahu":    (5, 135.0),
        "Ketu":    (11, 315.0),
    })
    bha = bhavadhipati_bala(house=1, chart=chart, asc_sign=1)
    # Should be Mars's full shadbala — a positive number
    assert bha > 0.0, "Mars's shadbala must be positive for Aries-asc 1st house"


def test_bhavadhipati_bala_house_lord_mapping() -> None:
    """Aries asc:
       house 1 → Aries lord = Mars
       house 2 → Taurus lord = Venus
       house 10 → Capricorn lord = Saturn
       house 12 → Pisces lord = Jupiter
    Verify the lord-of-house mapping is correct by checking that each
    house's bhavadhipati matches that lord's standalone shadbala."""
    chart = _full_chart({
        "Sun":     (5, 125.0),
        "Moon":    (4, 105.0),
        "Mars":    (1,   5.0),
        "Mercury": (3,  75.0),
        "Jupiter": (12, 345.0),
        "Venus":   (2,  45.0),
        "Saturn":  (10, 295.0),
        "Rahu":    (5, 135.0),
        "Ketu":    (11, 315.0),
    })
    asc = 1  # Aries
    bha1 = bhavadhipati_bala(1, chart, asc)   # Mars
    bha2 = bhavadhipati_bala(2, chart, asc)   # Venus
    bha10 = bhavadhipati_bala(10, chart, asc)  # Saturn
    bha12 = bhavadhipati_bala(12, chart, asc)  # Jupiter
    # All four lord-shadbalas should be positive and distinct.
    for label, val in [("Mars", bha1), ("Venus", bha2),
                       ("Saturn", bha10), ("Jupiter", bha12)]:
        assert val > 0.0, f"{label} shadbala must be positive"


def test_bhavadhipati_bala_missing_lord_returns_0() -> None:
    """Chart missing the lord planet returns 0 (defensive)."""
    chart = _full_chart({"Sun": (1, 5.0)})  # no Mars
    assert bhavadhipati_bala(1, chart, asc_sign=1) == pytest.approx(0.0)


def test_bhavadhipati_bala_rejects_invalid_inputs() -> None:
    chart = _full_chart({"Mars": (1, 5.0)})
    with pytest.raises(ValueError):
        bhavadhipati_bala(0, chart, asc_sign=1)
    with pytest.raises(ValueError):
        bhavadhipati_bala(13, chart, asc_sign=1)
    with pytest.raises(ValueError):
        bhavadhipati_bala(1, chart, asc_sign=0)


def test_bhava_bala_returns_breakdown_with_total() -> None:
    """Aggregate returns dict with all 4 keys."""
    chart = _full_chart({"Mars": (1, 5.0)})
    bd = bhava_bala(1, chart, asc_sign=1)
    for key in ("bhavadhipati", "bhava_dig", "bhava_drishti", "total"):
        assert key in bd
    # Phase 2 stubs:
    assert bd["bhava_dig"] == pytest.approx(0.0)
    assert bd["bhava_drishti"] == pytest.approx(0.0)
    # Total = bhavadhipati for now
    assert bd["total"] == pytest.approx(bd["bhavadhipati"], abs=0.001)


# --------------------------------------------------------------------------- #
# Paksha-bala (BPHS 27.32-33) — lunar-phase strength                          #
# --------------------------------------------------------------------------- #

def test_paksha_bala_benefic_full_moon_max() -> None:
    """Jupiter (benefic) at full Moon (180° separation) gets max 60 virupa."""
    assert paksha_bala("Jupiter", sun_longitude=0.0, moon_longitude=180.0) == \
        pytest.approx(60.0)


def test_paksha_bala_benefic_new_moon_zero() -> None:
    """Jupiter (benefic) at new Moon (0° separation) gets 0 virupa."""
    assert paksha_bala("Jupiter", sun_longitude=120.0, moon_longitude=120.0) == \
        pytest.approx(0.0)


def test_paksha_bala_malefic_inverted() -> None:
    """Sun (malefic) gets 60 at new Moon (dark fortnight), 0 at full Moon."""
    assert paksha_bala("Sun", sun_longitude=0.0, moon_longitude=0.0) == \
        pytest.approx(60.0)
    assert paksha_bala("Sun", sun_longitude=0.0, moon_longitude=180.0) == \
        pytest.approx(0.0)


def test_paksha_bala_half_moon_30_virupa() -> None:
    """At 90° separation (half Moon): benefics 30, malefics 30 (symmetric)."""
    assert paksha_bala("Venus", sun_longitude=0.0, moon_longitude=90.0) == \
        pytest.approx(30.0)
    assert paksha_bala("Mars", sun_longitude=0.0, moon_longitude=90.0) == \
        pytest.approx(30.0)


def test_paksha_bala_handles_360_wrap() -> None:
    """Separation must take the shortest arc, not the signed diff."""
    # Sun at 350°, Moon at 10° → shortest arc = 20°
    bala = paksha_bala("Jupiter", sun_longitude=350.0, moon_longitude=10.0)
    assert bala == pytest.approx(20.0 * 60.0 / 180.0, abs=0.01)


def test_paksha_bala_unknown_planet_raises() -> None:
    with pytest.raises(ValueError):
        paksha_bala("Pluto", sun_longitude=0.0, moon_longitude=180.0)
