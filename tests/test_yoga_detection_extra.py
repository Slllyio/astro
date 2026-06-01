"""Tests for app.core.yoga_detection_extra — all 5 extra detectors.

Canonical fixture: Mainpuri 1989 — Scorpio Lagna (asc_sign=8).

Pre-computed chart facts used in assertions:

SARALA DIGNIFIED (detect_sarala_dignified):
  8H of Scorpio = _step_signs(8,8) = 3 (Gemini), 8L = Mercury.
  Mercury at sign=6 (Virgo), lon=157.34°.
  is_exalted("Mercury", 6) → True (EXALTATION["Mercury"]=6=Virgo).
  → active=True, dignity="exalted".

CHANDRA-MANGALA EXTENDED (detect_chandra_mangala_extended):
  Moon sign=11 (Aquarius), Mars sign=6 (Virgo).
  Conjunction: 11 ≠ 6 → False.
  Opposition: _house_from(11, 6) = ((6-11)%12)+1 = 8 ≠ 7 → False.
  → active=False, mode="".

ADHI YOGA STRICT (detect_adhi_yoga_strict):
  Moon sign=11 (Aquarius).
  6th from Moon → sign 4 (Cancer), 7th → 5 (Leo), 8th → 6 (Virgo).
  Mercury sign=6 → 8th from Moon ✓.
  Jupiter sign=3 → _house_from(11,3) = 5 ≠ {6,7,8} ✗.
  Venus sign=8 → _house_from(11,8) = 10 ≠ {6,7,8} ✗.
  ALL THREE required → active=False.

SARASWATI EXTENDED (detect_saraswati_yoga_extended):
  From Lagna (sign 8): Mercury house=11 ∉ {1,2,4,5,7,9,10} → fails.
  From Moon (sign 11): Mercury sign 6 → house_from_moon=8 ∉ good → fails.
  → active=False.

PUSHKARA NAVAMSA (detect_pushkara_navamsa):
  Jupiter lon=76.69°: D1 sign=Gemini (dual), pada=int(16.69/3.333)=5 ∈ {3,5} ✓.
  Venus  lon=220.23°: D1 sign=Scorpio (fixed), pada=int(10.23/3.333)=3 ∈ {3,7} ✓.
  Moon   lon=317.64°: D1 sign=Aquarius (fixed), pada=int(17.64/3.333)=5 ∉ {3,7} ✗.
  → planets_in_pushkara = {"Jupiter", "Venus"}.
"""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.yoga_detection_extra import (
    AdhiYogaResult,
    ChandraMangalaResult,
    PushkaraResult,
    SaralaDignifiedResult,
    SaraswatiResult,
    detect_adhi_yoga_strict,
    detect_chandra_mangala_extended,
    detect_pushkara_navamsa,
    detect_sarala_dignified,
    detect_saraswati_yoga_extended,
)


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mainpuri_chart() -> Chart:
    """Mainpuri 1989 — Scorpio Lagna, canonical test fixture."""
    return Chart(
        asc_sign=8,
        asc_lon=224.06,
        planet_signs={
            "Sun": 6, "Moon": 11, "Mars": 6, "Mercury": 6,
            "Jupiter": 3, "Venus": 8, "Saturn": 9,
            "Rahu": 11, "Ketu": 5,
        },
        planet_houses={
            "Sun": 11, "Moon": 4, "Mars": 11, "Mercury": 11,
            "Jupiter": 8, "Venus": 1, "Saturn": 2,
            "Rahu": 4, "Ketu": 10,
        },
        planet_lons={
            "Sun": 175.12, "Moon": 317.64, "Mars": 171.00,
            "Mercury": 157.34, "Jupiter": 76.69, "Venus": 220.23,
            "Saturn": 254.36, "Rahu": 300.74, "Ketu": 120.74,
        },
    )


# ---------------------------------------------------------------------------
# 1. SaralaDignified
# ---------------------------------------------------------------------------


class TestSaralaDignifiedMainpuri:
    """Scorpio Lagna: 8L = Mercury; Mercury in Virgo = exalted."""

    def test_returns_sarala_dignified_result(self, mainpuri_chart: Chart) -> None:
        """Return is a SaralaDignifiedResult frozen dataclass."""
        result = detect_sarala_dignified(mainpuri_chart)
        assert isinstance(result, SaralaDignifiedResult)

    def test_active_for_mainpuri(self, mainpuri_chart: Chart) -> None:
        """Mercury (8L of Scorpio) in Virgo is exalted → active=True."""
        result = detect_sarala_dignified(mainpuri_chart)
        assert result.active is True

    def test_eighth_lord_is_mercury(self, mainpuri_chart: Chart) -> None:
        """8th house from Scorpio = Gemini; Gemini lord = Mercury."""
        result = detect_sarala_dignified(mainpuri_chart)
        assert result.eighth_lord == "Mercury"

    def test_eighth_lord_sign_is_virgo(self, mainpuri_chart: Chart) -> None:
        """Mercury is in Virgo (sign 6) in Mainpuri chart."""
        result = detect_sarala_dignified(mainpuri_chart)
        assert result.eighth_lord_sign == 6

    def test_dignity_is_exalted(self, mainpuri_chart: Chart) -> None:
        """Mercury in Virgo (exaltation sign) → dignity='exalted'."""
        result = detect_sarala_dignified(mainpuri_chart)
        assert result.dignity == "exalted"

    def test_inactive_when_eighth_lord_in_neutral_sign(self) -> None:
        """Sarala inactive when 8L is in a non-dignified placement.

        Aries Lagna (asc_sign=1): 8H = Scorpio, 8L = Mars.
        Mars placed in Libra (sign 7): not own {1,8}, not exalted {10},
        Libra lon 195° not in MT range {0-12}. → active=False.
        """
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 2,
                "Jupiter": 1, "Venus": 2, "Saturn": 10,
                "Rahu": 9, "Ketu": 3,
            },
            planet_houses={
                "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 2,
                "Jupiter": 1, "Venus": 2, "Saturn": 10,
                "Rahu": 9, "Ketu": 3,
            },
            planet_lons={
                "Sun": 5.0, "Moon": 95.0, "Mars": 195.0, "Mercury": 40.0,
                "Jupiter": 10.0, "Venus": 45.0, "Saturn": 275.0,
                "Rahu": 260.0, "Ketu": 80.0,
            },
        )
        result = detect_sarala_dignified(chart)
        assert result.active is False
        assert result.dignity == ""

    def test_active_when_eighth_lord_in_own_sign(self) -> None:
        """Sarala active when 8L is in own sign (not exalted).

        Aquarius Lagna (asc_sign=11): 8H = Virgo, 8L = Mercury.
        Mercury placed in Gemini (sign 3) = own sign of Mercury.
        Gemini lon = 65°. is_own_sign("Mercury", 3) → True.
        is_exalted("Mercury", 3) → False (exalt=6).
        is_moolatrikona("Mercury", 65°) → False (range 166-170°).
        → dignity="own", active=True.
        """
        chart = Chart(
            asc_sign=11,
            asc_lon=300.0,
            planet_signs={
                "Sun": 5, "Moon": 8, "Mars": 1, "Mercury": 3,
                "Jupiter": 12, "Venus": 2, "Saturn": 11,
                "Rahu": 6, "Ketu": 12,
            },
            planet_houses={
                "Sun": 7, "Moon": 10, "Mars": 3, "Mercury": 5,
                "Jupiter": 2, "Venus": 4, "Saturn": 1,
                "Rahu": 8, "Ketu": 2,
            },
            planet_lons={
                "Sun": 120.0, "Moon": 215.0, "Mars": 10.0, "Mercury": 65.0,
                "Jupiter": 335.0, "Venus": 45.0, "Saturn": 305.0,
                "Rahu": 155.0, "Ketu": 335.0,
            },
        )
        result = detect_sarala_dignified(chart)
        assert result.active is True
        assert result.dignity == "own"


# ---------------------------------------------------------------------------
# 2. ChandraMangalaExtended
# ---------------------------------------------------------------------------


class TestChandraMangalaMainpuri:
    """Mainpuri: Moon=Aquarius(11), Mars=Virgo(6) — neither conjoined nor opposing."""

    def test_returns_chandra_mangala_result(self, mainpuri_chart: Chart) -> None:
        """Return is a ChandraMangalaResult frozen dataclass."""
        result = detect_chandra_mangala_extended(mainpuri_chart)
        assert isinstance(result, ChandraMangalaResult)

    def test_inactive_for_mainpuri(self, mainpuri_chart: Chart) -> None:
        """Moon(11) and Mars(6): distance=8 (not 7, not same). active=False."""
        result = detect_chandra_mangala_extended(mainpuri_chart)
        assert result.active is False

    def test_mode_empty_for_mainpuri(self, mainpuri_chart: Chart) -> None:
        """No yoga → mode is empty string."""
        result = detect_chandra_mangala_extended(mainpuri_chart)
        assert result.mode == ""

    def test_moon_sign_preserved(self, mainpuri_chart: Chart) -> None:
        """moon_sign field must match chart."""
        result = detect_chandra_mangala_extended(mainpuri_chart)
        assert result.moon_sign == 11

    def test_mars_sign_preserved(self, mainpuri_chart: Chart) -> None:
        """mars_sign field must match chart."""
        result = detect_chandra_mangala_extended(mainpuri_chart)
        assert result.mars_sign == 6


class TestChandraMangalaConjunction:
    """Verify conjunction mode triggers when Moon and Mars are in same sign."""

    def test_conjunction_mode_active(self) -> None:
        """Moon and Mars both in Cancer (sign 4) → conjunction."""
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 4, "Mars": 4, "Mercury": 2,
                "Jupiter": 9, "Venus": 3, "Saturn": 10,
                "Rahu": 7, "Ketu": 1,
            },
            planet_houses={
                "Sun": 1, "Moon": 4, "Mars": 4, "Mercury": 2,
                "Jupiter": 9, "Venus": 3, "Saturn": 10,
                "Rahu": 7, "Ketu": 1,
            },
            planet_lons={
                "Sun": 5.0, "Moon": 95.0, "Mars": 100.0, "Mercury": 40.0,
                "Jupiter": 260.0, "Venus": 70.0, "Saturn": 275.0,
                "Rahu": 185.0, "Ketu": 5.0,
            },
        )
        result = detect_chandra_mangala_extended(chart)
        assert result.active is True
        assert result.mode == "conjunction"


class TestChandraMangalaOpposition:
    """Verify opposition mode triggers when Moon and Mars are in 7th from each other."""

    def test_opposition_mode_active(self) -> None:
        """Moon in Aries (sign 1), Mars in Libra (sign 7): distance=7 → opposition."""
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 1, "Mars": 7, "Mercury": 2,
                "Jupiter": 9, "Venus": 3, "Saturn": 10,
                "Rahu": 5, "Ketu": 11,
            },
            planet_houses={
                "Sun": 1, "Moon": 1, "Mars": 7, "Mercury": 2,
                "Jupiter": 9, "Venus": 3, "Saturn": 10,
                "Rahu": 5, "Ketu": 11,
            },
            planet_lons={
                "Sun": 5.0, "Moon": 15.0, "Mars": 185.0, "Mercury": 40.0,
                "Jupiter": 260.0, "Venus": 70.0, "Saturn": 275.0,
                "Rahu": 125.0, "Ketu": 305.0,
            },
        )
        result = detect_chandra_mangala_extended(chart)
        assert result.active is True
        assert result.mode == "opposition"


# ---------------------------------------------------------------------------
# 3. AdhiYogaStrict
# ---------------------------------------------------------------------------


class TestAdhiYogaMainpuri:
    """Mainpuri: Jupiter(3rd) and Venus(10th) from Moon fail the 6/7/8 condition."""

    def test_returns_adhi_yoga_result(self, mainpuri_chart: Chart) -> None:
        """Return is an AdhiYogaResult frozen dataclass."""
        result = detect_adhi_yoga_strict(mainpuri_chart)
        assert isinstance(result, AdhiYogaResult)

    def test_inactive_for_mainpuri(self, mainpuri_chart: Chart) -> None:
        """Jupiter at 5th, Venus at 10th from Moon — both outside {6,7,8}. active=False."""
        result = detect_adhi_yoga_strict(mainpuri_chart)
        assert result.active is False

    def test_mercury_house_from_moon_is_eighth(self, mainpuri_chart: Chart) -> None:
        """Mercury(sign 6) from Moon(sign 11): ((6-11)%12)+1=8."""
        result = detect_adhi_yoga_strict(mainpuri_chart)
        assert result.mercury_house_from_moon == 8

    def test_jupiter_house_from_moon_is_fifth(self, mainpuri_chart: Chart) -> None:
        """Jupiter(sign 3) from Moon(sign 11): ((3-11)%12)+1=5."""
        result = detect_adhi_yoga_strict(mainpuri_chart)
        assert result.jupiter_house_from_moon == 5

    def test_venus_house_from_moon_is_tenth(self, mainpuri_chart: Chart) -> None:
        """Venus(sign 8) from Moon(sign 11): ((8-11)%12)+1=10."""
        result = detect_adhi_yoga_strict(mainpuri_chart)
        assert result.venus_house_from_moon == 10


class TestAdhiYogaActive:
    """Verify all-three rule fires when Mercury, Jupiter, Venus all in 6/7/8 from Moon."""

    def test_active_when_all_three_in_target(self) -> None:
        """Aries Lagna, Moon in Aries (sign 1).
        6th from Moon = Virgo (6), 7th = Libra (7), 8th = Scorpio (8).
        Mercury in 6 (Virgo), Jupiter in 7 (Libra), Venus in 8 (Scorpio). → active.
        """
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 1, "Mars": 2, "Mercury": 6,
                "Jupiter": 7, "Venus": 8, "Saturn": 3,
                "Rahu": 10, "Ketu": 4,
            },
            planet_houses={
                "Sun": 1, "Moon": 1, "Mars": 2, "Mercury": 6,
                "Jupiter": 7, "Venus": 8, "Saturn": 3,
                "Rahu": 10, "Ketu": 4,
            },
            planet_lons={
                "Sun": 5.0, "Moon": 10.0, "Mars": 35.0, "Mercury": 160.0,
                "Jupiter": 190.0, "Venus": 215.0, "Saturn": 65.0,
                "Rahu": 275.0, "Ketu": 95.0,
            },
        )
        result = detect_adhi_yoga_strict(chart)
        assert result.active is True

    def test_inactive_when_only_two_in_target(self) -> None:
        """Two benefics in 6/7/8 from Moon, one outside → must be inactive."""
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 1, "Mars": 2, "Mercury": 6,
                "Jupiter": 7, "Venus": 3,  # Venus at 3rd from Moon (Gemini)
                "Saturn": 5,
                "Rahu": 10, "Ketu": 4,
            },
            planet_houses={
                "Sun": 1, "Moon": 1, "Mars": 2, "Mercury": 6,
                "Jupiter": 7, "Venus": 3, "Saturn": 5,
                "Rahu": 10, "Ketu": 4,
            },
            planet_lons={
                "Sun": 5.0, "Moon": 10.0, "Mars": 35.0, "Mercury": 160.0,
                "Jupiter": 190.0, "Venus": 65.0, "Saturn": 125.0,
                "Rahu": 275.0, "Ketu": 95.0,
            },
        )
        result = detect_adhi_yoga_strict(chart)
        assert result.active is False


# ---------------------------------------------------------------------------
# 4. SaraswatiExtended
# ---------------------------------------------------------------------------


class TestSaraswatiMainpuri:
    """Mainpuri: Mercury house=11 fails from Lagna; Mercury 8th from Moon fails."""

    def test_returns_saraswati_result(self, mainpuri_chart: Chart) -> None:
        """Return is a SaraswatiResult frozen dataclass."""
        result = detect_saraswati_yoga_extended(mainpuri_chart)
        assert isinstance(result, SaraswatiResult)

    def test_inactive_for_mainpuri(self, mainpuri_chart: Chart) -> None:
        """Mercury in 11H (Lagna axis) and 8th from Moon — neither axis qualifies."""
        result = detect_saraswati_yoga_extended(mainpuri_chart)
        assert result.active is False

    def test_axis_empty_for_mainpuri(self, mainpuri_chart: Chart) -> None:
        """axis must be '' when inactive."""
        result = detect_saraswati_yoga_extended(mainpuri_chart)
        assert result.axis == ""

    def test_jupiter_dignity_empty_when_inactive(self, mainpuri_chart: Chart) -> None:
        """jupiter_dignity must be '' when yoga is inactive."""
        result = detect_saraswati_yoga_extended(mainpuri_chart)
        assert result.jupiter_dignity == ""


class TestSaraswatiFromLagnaActive:
    """Verify Saraswati fires from Lagna axis with dignified Jupiter."""

    def test_active_from_lagna_axis(self) -> None:
        """Cancer Lagna (sign 4): kendra/trikona/2H = {1,2,4,5,7,9,10}.
        Mercury in 2H (Leo=5), Jupiter in 5H (Scorpio=8) — but we need Jupiter
        in good house. Let's use a chart where all three are in 1/2/4/5/7/9/10
        AND Jupiter is in exaltation (Cancer=4).

        Cancer Lagna (4): 1H=Cancer(4), 2H=Leo(5), 4H=Libra(7), 5H=Scorpio(8),
        7H=Capricorn(10), 9H=Pisces(12), 10H=Aries(1).
        Place Mercury in Leo(5)=2H, Jupiter in Cancer(4)=1H (exalted), Venus in Scorpio(8)=5H.
        """
        chart = Chart(
            asc_sign=4,
            asc_lon=90.0,
            planet_signs={
                "Sun": 4, "Moon": 4, "Mars": 10, "Mercury": 5,
                "Jupiter": 4, "Venus": 8, "Saturn": 1,
                "Rahu": 11, "Ketu": 5,
            },
            planet_houses={
                "Sun": 1, "Moon": 1, "Mars": 7, "Mercury": 2,
                "Jupiter": 1, "Venus": 5, "Saturn": 10,
                "Rahu": 8, "Ketu": 2,
            },
            planet_lons={
                "Sun": 92.0, "Moon": 95.0, "Mars": 272.0, "Mercury": 125.0,
                "Jupiter": 98.0, "Venus": 215.0, "Saturn": 5.0,
                "Rahu": 305.0, "Ketu": 125.0,
            },
        )
        result = detect_saraswati_yoga_extended(chart)
        assert result.active is True
        assert result.axis == "lagna"
        assert result.jupiter_dignity == "exalted"


class TestSaraswatiFromMoonActive:
    """Verify Saraswati fires from Moon axis when Lagna axis fails."""

    def test_active_from_moon_axis(self) -> None:
        """Scorpio Lagna (8) with Moon in Aries (1) — Lagna axis fails, Moon axis fires.

        Moon and Lagna must occupy different signs for the two reference
        frames to differ; otherwise the axes are mathematically identical.

        From Moon(1): good house signs = {1, 2, 4, 5, 7, 9, 10}.
          Mercury at Libra(7):       _house_from(1,7)  = 7  ∈ good ✓
          Jupiter at Sagittarius(9): _house_from(1,9)  = 9  ∈ good ✓
          Venus   at Capricorn(10):  _house_from(1,10) = 10 ∈ good ✓

        From Lagna(8): good house signs = {8, 9, 11, 12, 2, 4, 5}.
          Mercury(7): _house_from(8,7)  = 12 ∉ good → Lagna axis fails.

        Jupiter in Sagittarius at 260° (degree 20°) — past the 0–10° MT
        range and not exalted → dignity='own'.
        """
        chart = Chart(
            asc_sign=8,
            asc_lon=210.0,
            planet_signs={
                "Sun": 1, "Moon": 1, "Mars": 1, "Mercury": 7,
                "Jupiter": 9, "Venus": 10, "Saturn": 3,
                "Rahu": 6, "Ketu": 12,
            },
            planet_houses={
                "Sun": 6, "Moon": 6, "Mars": 6, "Mercury": 12,
                "Jupiter": 2, "Venus": 3, "Saturn": 8,
                "Rahu": 11, "Ketu": 5,
            },
            planet_lons={
                "Sun": 5.0, "Moon": 15.0, "Mars": 10.0, "Mercury": 190.0,
                "Jupiter": 260.0, "Venus": 280.0, "Saturn": 65.0,
                "Rahu": 155.0, "Ketu": 335.0,
            },
        )
        result = detect_saraswati_yoga_extended(chart)
        assert result.active is True
        assert result.axis == "moon"
        assert result.jupiter_dignity == "own"


# ---------------------------------------------------------------------------
# 5. PushkaraNavamsa
# ---------------------------------------------------------------------------


class TestPushkaraNavamsaMainpuri:
    """Mainpuri Pushkara padas — Jupiter and Venus verified in auspicious padas."""

    def test_returns_pushkara_result(self, mainpuri_chart: Chart) -> None:
        """Return is a PushkaraResult frozen dataclass."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        assert isinstance(result, PushkaraResult)

    def test_planets_in_pushkara_is_tuple_of_strings(
        self, mainpuri_chart: Chart
    ) -> None:
        """planets_in_pushkara must be a tuple of planet name strings."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        assert isinstance(result.planets_in_pushkara, tuple)
        assert all(isinstance(p, str) for p in result.planets_in_pushkara)

    def test_details_count_matches_planets(self, mainpuri_chart: Chart) -> None:
        """len(details) must equal len(planets_in_pushkara)."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        assert len(result.details) == len(result.planets_in_pushkara)

    def test_details_are_three_tuples(self, mainpuri_chart: Chart) -> None:
        """Each detail entry is a (str, int, int) tuple."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        for entry in result.details:
            assert len(entry) == 3
            planet, d9_sign, pada = entry
            assert isinstance(planet, str)
            assert isinstance(d9_sign, int) and 1 <= d9_sign <= 12
            assert isinstance(pada, int) and 0 <= pada <= 8

    def test_jupiter_is_in_pushkara(self, mainpuri_chart: Chart) -> None:
        """Jupiter at 76.69° (Gemini, dual): pada=int(16.69/3.333)=5 ∈ {3,5} → Pushkara."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        assert "Jupiter" in result.planets_in_pushkara

    def test_venus_is_in_pushkara(self, mainpuri_chart: Chart) -> None:
        """Venus at 220.23° (Scorpio, fixed): pada=int(10.23/3.333)=3 ∈ {3,7} → Pushkara."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        assert "Venus" in result.planets_in_pushkara

    def test_moon_not_in_pushkara(self, mainpuri_chart: Chart) -> None:
        """Moon at 317.64° (Aquarius, fixed): pada=int(17.64/3.333)=5 ∉ {3,7} → NOT Pushkara."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        assert "Moon" not in result.planets_in_pushkara

    def test_exactly_two_pushkara_planets(self, mainpuri_chart: Chart) -> None:
        """For Mainpuri, exactly Jupiter and Venus are in Pushkara padas."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        assert set(result.planets_in_pushkara) == {"Jupiter", "Venus"}

    def test_jupiter_pada_index_is_five(self, mainpuri_chart: Chart) -> None:
        """Jupiter D1 pada = int(16.69 / (30/9)) = 5."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        jup_detail = next(d for d in result.details if d[0] == "Jupiter")
        assert jup_detail[2] == 5  # pada index

    def test_venus_pada_index_is_three(self, mainpuri_chart: Chart) -> None:
        """Venus D1 pada = int(10.23 / (30/9)) = 3."""
        result = detect_pushkara_navamsa(mainpuri_chart)
        ven_detail = next(d for d in result.details if d[0] == "Venus")
        assert ven_detail[2] == 3  # pada index


class TestPushkaraNavamsaEdgeCases:
    """Pushkara with zero planets and with movable-sign planet."""

    def test_no_pushkara_planets_gives_empty_tuple(self) -> None:
        """Chart where every planet is in pada 0 (none in {1,3,5,7}) → empty result."""
        # All planets at longitude X.0° (each sign start) — pada=0 for all.
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                "Jupiter": 5, "Venus": 6, "Saturn": 7,
                "Rahu": 8, "Ketu": 9,
            },
            planet_houses={
                "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                "Jupiter": 5, "Venus": 6, "Saturn": 7,
                "Rahu": 8, "Ketu": 9,
            },
            planet_lons={
                "Sun": 0.5,   "Moon": 30.5,  "Mars": 60.5,
                "Mercury": 90.5, "Jupiter": 120.5, "Venus": 150.5,
                "Saturn": 180.5, "Rahu": 210.5, "Ketu": 240.5,
            },
        )
        result = detect_pushkara_navamsa(chart)
        assert result.planets_in_pushkara == ()
        assert result.details == ()

    def test_movable_sign_pada_1_is_pushkara(self) -> None:
        """Movable sign (Aries=1): pushkara padas are 1 & 5 (0-indexed).
        Place Sun at 4.0° Aries: pada = int(4.0 / (30/9)) = int(1.2) = 1 ∈ {1,5}.
        """
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 2,
                "Jupiter": 3, "Venus": 5, "Saturn": 8,
                "Rahu": 11, "Ketu": 5,
            },
            planet_houses={
                "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 2,
                "Jupiter": 3, "Venus": 5, "Saturn": 8,
                "Rahu": 11, "Ketu": 5,
            },
            planet_lons={
                "Sun": 4.0, "Moon": 90.5, "Mars": 181.0, "Mercury": 31.0,
                "Jupiter": 61.0, "Venus": 121.0, "Saturn": 211.0,
                "Rahu": 301.0, "Ketu": 121.0,
            },
        )
        result = detect_pushkara_navamsa(chart)
        assert "Sun" in result.planets_in_pushkara
