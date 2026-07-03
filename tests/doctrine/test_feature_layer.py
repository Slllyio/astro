"""varga_points, arishta_yogas, RamanChart: the P2 feature layer."""
import hashlib
import json
from pathlib import Path

import pytest

from app.core.arishta_yogas import (
    evaluate_arishta,
    full_moon_hemmed_by_benefics,
    malefics_in_2_6_8_12,
    malefics_in_last_navamsa,
    moon_afflicted_in_7_8_12,
    moon_in_benefic_drekkana,
    moon_with_malefics_in_kendra,
)
from app.core.varga_points import khara_drekkana, navamsa_64th, occupies_point
from app.medini.doctrine import raman_chart as rc

# Canonical repo baseline: Bangalore 1990-07-15 12:00 IST — but golden
# printed-position tests need no ephemeris, so charts here are synthetic.
LONS = {
    "Sun": 89.0,       # Gemini 29 (last navamsa)
    "Moon": 215.0,     # Scorpio 5
    "Mars": 5.0,       # Aries 5
    "Mercury": 95.0,   # Cancer 5
    "Jupiter": 100.0,  # Cancer 10
    "Venus": 45.0,     # Taurus 15
    "Saturn": 280.0,   # Capricorn 10
    "Rahu": 118.0,     # Cancer 28
    "Ketu": 298.0,     # Capricorn 28
}
LAGNA = 155.0          # Virgo 5


class TestVargaPoints:
    def test_khara_is_210_degrees_on(self):
        kp = khara_drekkana(10.0)  # Aries 10, 2nd drekkana
        assert kp.longitude == pytest.approx(220.0)
        assert kp.sign == 8  # Scorpio — 8th sign, middle drekkana family
        # Scorpio 10 = 2nd drekkana of Scorpio -> Pisces (own-triplicity map)
        assert kp.varga_sign == 12 and kp.lord == "Jupiter"

    def test_chidra_64th_navamsa(self):
        np_ = navamsa_64th(0.0)  # Aries 0, 1st navamsa
        assert np_.longitude == pytest.approx(210.0)
        assert np_.sign == 8

    def test_occupies_point_orb(self):
        kp = khara_drekkana(10.0)
        assert occupies_point(221.0, kp)
        assert not occupies_point(230.0, kp)
        assert occupies_point(216.0, kp, orb=5.0) is True
        assert occupies_point(214.0, kp, orb=0.5) is False


def _houses(lagna_sign, signs):
    return {p: ((s - lagna_sign) % 12) + 1 for p, s in signs.items()}


class TestArishta:
    def test_malefics_in_last_navamsa(self):
        assert malefics_in_last_navamsa({"Sun": 29.0, "Mars": 5.0}) == ["Sun"]
        assert malefics_in_last_navamsa({"Jupiter": 29.0}) == []

    def test_moon_with_malefics_in_kendra(self):
        houses = {"Moon": 4, "Saturn": 4}
        assert moon_with_malefics_in_kendra(houses)
        assert not moon_with_malefics_in_kendra({"Moon": 5, "Saturn": 5})
        assert not moon_with_malefics_in_kendra({"Moon": 4, "Jupiter": 4})

    def test_moon_afflicted_in_8_without_benefic_aspect(self):
        houses = {"Moon": 8, "Mars": 8, "Jupiter": 3}
        # Jupiter in 3 aspects 7, 9, 11 — not 8 -> afflicted
        assert moon_afflicted_in_7_8_12(houses)
        # Jupiter in 4 aspects 8 (5th aspect' — whole-sign 5/7/9) -> saved
        houses_saved = {"Moon": 8, "Mars": 8, "Jupiter": 4}
        assert not moon_afflicted_in_7_8_12(houses_saved)

    def test_malefics_in_dusthana_list(self):
        houses = {"Saturn": 8, "Mars": 6, "Sun": 5, "Rahu": 12}
        assert malefics_in_2_6_8_12(houses) == ["Mars", "Rahu", "Saturn"]

    def test_moon_in_benefic_drekkana(self):
        # Scorpio 5° -> 1st drekkana = Scorpio itself (Mars) -> not benefic
        assert not moon_in_benefic_drekkana(215.0)
        # Scorpio 15° -> 2nd drekkana -> Pisces (Jupiter) -> benefic
        assert moon_in_benefic_drekkana(225.0)

    def test_full_moon_hemmed(self):
        houses = {"Moon": 5, "Venus": 4, "Jupiter": 6}
        assert full_moon_hemmed_by_benefics(houses, True, 180.0)
        assert not full_moon_hemmed_by_benefics(houses, False, 20.0)
        assert not full_moon_hemmed_by_benefics({"Moon": 5, "Venus": 4}, True, 180.0)

    def test_evaluate_arishta_returns_both_lists(self):
        houses = _houses(6, {p: int(v // 30) + 1 for p, v in LONS.items()})
        arishtas, bhangas = evaluate_arishta(
            LONS, houses, "Mercury", {"Jupiter": 0.8, "Mercury": 0.7}, True,
        )
        assert {f.key for f in arishtas} == {
            "balarishta_1", "balarishta_2", "balarishta_3", "balarishta_5"}
        assert all(f.citation.startswith("HPA Ch.XIV") for f in arishtas + bhangas)


@pytest.fixture(scope="module")
def chart():
    return rc.from_printed_positions(LONS, LAGNA, birth_jd=2448088.0)


class TestRamanChart:

    def test_parity_with_bundle(self, chart):
        b = chart.bundle
        for g in LONS:
            assert chart.house_of(g) == b.house_of(g)
            assert chart.varga_sign(g, 9) == b.navamsa_sign[g]
            assert chart.varga_sign(g, 1) == b.chart.planet_signs[g]
        assert chart.lagna_sign() == b.kundali.lagna_sign
        assert chart.lagna_sign("navamsa") == b.navamsa_lagna

    def test_all_16_vargas_present(self, chart):
        assert set(chart.varga_lagna) == set(rc.SHODASHAVARGA_DIVISORS)
        for g in LONS:
            assert set(chart.varga_signs[g]) == set(rc.SHODASHAVARGA_DIVISORS)
            assert all(1 <= s <= 12 for s in chart.varga_signs[g].values())

    def test_frames(self, chart):
        moon_sign = chart.bundle.chart.planet_signs["Moon"]
        for g in LONS:
            expect = ((chart.bundle.chart.planet_signs[g] - moon_sign) % 12) + 1
            assert chart.house_of(g, "moon") == expect
        assert 1 <= chart.house_of("Sun", "arudha") <= 12
        assert 1 <= chart.house_of("Sun", "karakamsa") <= 12
        with pytest.raises(ValueError):
            chart.house_of("Sun", "chalit")

    def test_atmakaraka_is_highest_degree_in_sign(self, chart):
        assert chart.atmakaraka == "Sun"  # 29° in sign beats all others
        assert chart.karakamsa_sign == chart.varga_signs["Sun"][9]

    def test_khara_and_chidra_wired(self, chart):
        assert chart.khara.longitude == pytest.approx((LAGNA + 210.0) % 360.0)
        assert chart.chidra.longitude == pytest.approx((LONS["Moon"] + 210.0) % 360.0)

    def test_printed_positions_are_raman_frame(self, chart):
        assert chart.ayanamsa == "raman"
        assert rc.from_positions(LONS, LAGNA, birth_jd=2448088.0).ayanamsa == "lahiri"
        with pytest.raises(ValueError):
            rc.from_positions(LONS, LAGNA, birth_jd=2448088.0, ayanamsa="krishnamurti")

    def test_lahiri_to_raman_shifts_by_delta(self):
        jd = 2448088.0
        delta = rc.ayanamsa_delta_lahiri_minus_raman(jd)
        assert 0.3 < abs(delta) < 2.0  # Lahiri vs Raman differ by ~0.9 deg
        shifted, lag = rc.lahiri_to_raman({"Sun": 10.0}, 100.0, jd)
        assert shifted["Sun"] == pytest.approx((10.0 + delta) % 360.0)
        assert lag == pytest.approx((100.0 + delta) % 360.0)


class TestFrozenRunFive:
    def test_raman_saab_sources_unchanged(self):
        """app/medini/ml/raman_saab/ is sha-frozen (run-5 artifacts).

        The doctrine layer composes it; nothing may edit it. If this test
        fails, revert the edit and extend via a NEW module instead.
        """
        pins = json.loads(
            Path("tests/doctrine/raman_saab_frozen_hashes.json").read_text()
        )
        base = Path("app/medini/ml/raman_saab")
        current = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(base.glob("*.py"))
        }
        assert current == pins
