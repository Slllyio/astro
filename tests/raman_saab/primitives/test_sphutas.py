"""Tests for the sphuta numeric sub-engines (chart-level gates, doctrinal
promotion #6): Beeja/Kshetra (H5 fertility), Special Dhana Lagna (H2 "A New
Method"), and the H9 Sahams (Paradesha / Jalapathana).

Every formula is pinned either to a synthetic hand-computable chart or to a
worked example Raman prints (Charts 49-51, 90, 109, 110), and every citation
carried by the returned records must resolve against the on-disk corpus.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.sources import verify
from app.raman_saab.primitives import sphutas


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


_DEG = 1.0 / 60.0  # arc-minute in degrees


def test_kala_root_numbers_are_immutable():
    """KALA_ROOT_NUMBERS is a read-only mapping proxy (doctrine data is frozen)."""
    with pytest.raises(TypeError):
        sphutas.KALA_ROOT_NUMBERS["Sun"] = 0  # type: ignore[index]


class TestBeejaSphuta:
    def test_beeja_simple_sum_sixty_gemini(self):
        """Beeja = Sun 10 + Venus 20 + Jupiter 30 = 60 deg = Gemini (HTJAH-I:5517)."""
        c = _chart({"Sun": 10.0, "Venus": 20.0, "Jupiter": 30.0,
                    "Mars": 0.0, "Moon": 0.0})
        assert sphutas.beeja_sphuta(c) == pytest.approx(60.0)
        bk = sphutas.beeja_kshetra(c)
        assert bk is not None and bk.beeja_sign == 3

    def test_beeja_expunges_multiples_of_360(self):
        """Sun 350 + Venus 300 + Jupiter 80 = 730 -> 10 deg Aries (HTJAH-I:5517-5518)."""
        c = _chart({"Sun": 350.0, "Venus": 300.0, "Jupiter": 80.0,
                    "Mars": 0.0, "Moon": 0.0})
        assert sphutas.beeja_sphuta(c) == pytest.approx(10.0)

    def test_beeja_strong_odd_sign_odd_navamsa(self):
        """Beeja 60 deg: Gemini (odd) with Libra navamsa (odd) -> strong (HTJAH-I:5521)."""
        bk = sphutas.beeja_kshetra(_chart({"Sun": 10.0, "Venus": 20.0, "Jupiter": 30.0,
                                           "Mars": 0.0, "Moon": 0.0}))
        assert bk is not None
        assert bk.beeja_sign == 3 and bk.beeja_navamsa_sign == 7
        assert bk.beeja_strong is True

    def test_beeja_odd_sign_even_navamsa_not_strong(self):
        """Beeja 71 deg: Gemini (odd) but Capricorn navamsa (even) -> NOT strong."""
        bk = sphutas.beeja_kshetra(_chart({"Sun": 21.0, "Venus": 20.0, "Jupiter": 30.0,
                                           "Mars": 0.0, "Moon": 0.0}))
        assert bk is not None
        assert bk.beeja_sign == 3 and bk.beeja_navamsa_sign == 10
        assert bk.beeja_strong is False

    def test_beeja_chart_90_even_sign_sterility(self):
        """Raman Chart 90: Sun 53 + Jupiter 192 + Venus 26 = 271 = Capricorn 1 deg,
        even in both Rashi and Amsa -> not strong (HTJAH-I:5600-5602)."""
        bk = sphutas.beeja_kshetra(_chart({"Sun": 53.0, "Jupiter": 192.0, "Venus": 26.0,
                                           "Mars": 0.0, "Moon": 0.0}))
        assert bk is not None
        assert bk.beeja_lon == pytest.approx(271.0)
        assert bk.beeja_sign == 10            # Capricorn (even)
        assert bk.beeja_navamsa_sign == 10    # "even ... both in Rashi and Amsa"
        assert bk.beeja_strong is False

    def test_beeja_zero_boundary_aries_strong(self):
        """All three at 0 deg -> Beeja 0.0 Aries (odd), Aries navamsa (odd) -> strong."""
        bk = sphutas.beeja_kshetra(_chart({"Sun": 0.0, "Venus": 0.0, "Jupiter": 0.0,
                                           "Mars": 0.0, "Moon": 0.0}))
        assert bk is not None
        assert bk.beeja_sign == 1 and bk.beeja_navamsa_sign == 1
        assert bk.beeja_strong is True


class TestKshetraSphuta:
    def test_kshetra_simple_sum_thirty_taurus(self):
        """Kshetra = Mars 10 + Moon 10 + Jupiter 10 = 30 deg = Taurus exactly:
        floor semantics put a 30.0 cusp in Taurus, not Aries (HTJAH-I:5519-5520)."""
        c = _chart({"Mars": 10.0, "Moon": 10.0, "Jupiter": 10.0,
                    "Sun": 0.0, "Venus": 0.0})
        assert sphutas.kshetra_sphuta(c) == pytest.approx(30.0)
        bk = sphutas.beeja_kshetra(c)
        assert bk is not None and bk.kshetra_sign == 2

    def test_kshetra_strong_even_sign_even_navamsa(self):
        """Kshetra 30 deg: Taurus (even) with Capricorn navamsa (even) -> fertile
        per Raman's EVEN/EVEN requirement for Kshetra (HTJAH-I:5523-5524)."""
        bk = sphutas.beeja_kshetra(_chart({"Mars": 10.0, "Moon": 10.0, "Jupiter": 10.0,
                                           "Sun": 0.0, "Venus": 0.0}))
        assert bk is not None
        assert bk.kshetra_sign == 2 and bk.kshetra_navamsa_sign == 10
        assert bk.kshetra_strong is True

    def test_kshetra_odd_sign_not_strong_even_with_odd_navamsa(self):
        """Kshetra 60 deg: Gemini (odd) -> NOT strong; Raman demands an EVEN sign
        for the female bed, the mirror of the Beeja rule (HTJAH-I:5523)."""
        bk = sphutas.beeja_kshetra(_chart({"Mars": 20.0, "Moon": 10.0, "Jupiter": 30.0,
                                           "Sun": 0.0, "Venus": 0.0}))
        assert bk is not None
        assert bk.kshetra_sign == 3
        assert bk.kshetra_strong is False

    def test_kshetra_even_sign_odd_navamsa_not_strong(self):
        """Kshetra 33.4 deg: Taurus (even) but Aquarius navamsa (odd) -> NOT strong."""
        bk = sphutas.beeja_kshetra(_chart({"Mars": 13.4, "Moon": 10.0, "Jupiter": 10.0,
                                           "Sun": 0.0, "Venus": 0.0}))
        assert bk is not None
        assert bk.kshetra_sign == 2 and bk.kshetra_navamsa_sign == 11
        assert bk.kshetra_strong is False


class TestBeejaKshetraGuards:
    def test_returns_none_when_required_planet_missing(self):
        """Sparse Track-B chart without Venus -> safe None, never KeyError."""
        c = _chart({"Sun": 10.0, "Jupiter": 30.0, "Mars": 0.0, "Moon": 0.0})
        assert sphutas.beeja_sphuta(c) is None
        assert sphutas.beeja_kshetra(c) is None

    def test_kshetra_none_when_mars_missing(self):
        """No Mars -> kshetra_sphuta None (female-bed formula needs Mars)."""
        c = _chart({"Sun": 10.0, "Venus": 20.0, "Jupiter": 30.0, "Moon": 0.0})
        assert sphutas.kshetra_sphuta(c) is None

    def test_record_is_frozen(self):
        """BeejaKshetra is immutable per project convention."""
        bk = sphutas.beeja_kshetra(_chart({"Sun": 10.0, "Venus": 20.0, "Jupiter": 30.0,
                                           "Mars": 0.0, "Moon": 0.0}))
        assert bk is not None
        with pytest.raises(Exception):
            bk.beeja_strong = False  # type: ignore[misc]

    def test_citations_resolve_on_disk(self):
        """Every citation carried by the gate resolves against the real corpus."""
        bk = sphutas.beeja_kshetra(_chart({"Sun": 10.0, "Venus": 20.0, "Jupiter": 30.0,
                                           "Mars": 0.0, "Moon": 0.0}))
        assert bk is not None and bk.citations
        assert all(verify(c) for c in bk.citations)


class TestSpecialDhanaLagna:
    def test_chart_49_remainder_one_is_moon_sign_itself(self):
        """Raman Chart 49: Venus(12) + Saturn(1) = 13, remainder 1 counted from
        Taurus Moon -> Taurus itself is the Dhana Lagna (HTJAH-I:3274-3277)."""
        # Virgo lagna -> 9th = Taurus -> Venus; Moon in Taurus -> 9th = Capricorn -> Saturn.
        dl = sphutas.special_dhana_lagna(_chart({"Moon": 40.0}, asc_lon=160.0))
        assert dl is not None
        assert dl.lord_ninth_from_lagna == "Venus"
        assert dl.lord_ninth_from_moon == "Saturn"
        assert dl.root_total == 13 and dl.remainder == 1
        assert dl.sign == 2  # Taurus

    def test_chart_50_remainder_four_from_cancer_is_libra(self):
        """Raman Chart 50: Mars(6) + Jupiter(10) = 16, remainder 4 counted from
        Cancer Moon -> Libra (HTJAH-I:3295-3299)."""
        # Leo lagna -> 9th = Aries -> Mars; Moon in Cancer -> 9th = Pisces -> Jupiter.
        dl = sphutas.special_dhana_lagna(_chart({"Moon": 100.0}, asc_lon=130.0))
        assert dl is not None
        assert dl.lord_ninth_from_lagna == "Mars"
        assert dl.lord_ninth_from_moon == "Jupiter"
        assert dl.root_total == 16 and dl.remainder == 4
        assert dl.sign == 7  # Libra

    def test_chart_51_remainder_ten_from_pisces_is_sagittarius(self):
        """Raman Chart 51: Moon(16) + Mars(6) = 22, remainder 10 counted from
        Pisces Moon -> Sagittarius (HTJAH-I:3307-3309)."""
        # Scorpio lagna -> 9th = Cancer -> Moon; Moon in Pisces -> 9th = Scorpio -> Mars.
        dl = sphutas.special_dhana_lagna(_chart({"Moon": 340.0}, asc_lon=220.0))
        assert dl is not None
        assert dl.lord_ninth_from_lagna == "Moon"
        assert dl.lord_ninth_from_moon == "Mars"
        assert dl.root_total == 22 and dl.remainder == 10
        assert dl.sign == 9  # Sagittarius

    def test_remainder_zero_counts_as_twelfth_from_moon(self):
        """Sun(30) + Mars(6) = 36 divides exactly: remainder 0 is treated as 12
        (12th sign from the Moon). Raman prints no zero-remainder case; this
        encodes the inclusive-count convention his worked remainders imply."""
        # Sagittarius lagna -> 9th = Leo -> Sun; Moon in Pisces -> 9th = Scorpio -> Mars.
        dl = sphutas.special_dhana_lagna(_chart({"Moon": 340.0}, asc_lon=250.0))
        assert dl is not None
        assert dl.root_total == 36 and dl.remainder == 12
        assert dl.sign == 11  # Aquarius, the 12th from Pisces

    def test_none_when_moon_absent(self):
        """The remainder is counted from Chandra Lagna: no Moon -> None."""
        assert sphutas.special_dhana_lagna(_chart({"Sun": 10.0}, asc_lon=160.0)) is None

    def test_citations_resolve_on_disk(self):
        dl = sphutas.special_dhana_lagna(_chart({"Moon": 40.0}, asc_lon=160.0))
        assert dl is not None and dl.citations
        assert all(verify(c) for c in dl.citations)


# Raman Chart 109 (HTJAH-II:9180-9200): Sagittarius lagna 265d52'.
_C109 = {"Sun": 16.0 + 25 * _DEG,        # 9th lord (Leo)
         "Jupiter": 146.0 + 16 * _DEG,   # lagna lord
         "Saturn": 74.0 + 34 * _DEG}
_C109_ASC = 265.0 + 52 * _DEG

# Raman Chart 110 (HTJAH-II:9230-9251): Cancer lagna 112d58'.
_C110 = {"Moon": 275.0 + 5 * _DEG,       # lagna lord
         "Jupiter": 136.0,               # 9th lord (Pisces)
         "Saturn": 76.0 + 39 * _DEG}
_C110_ASC = 112.0 + 58 * _DEG


class TestSahams:
    def test_returns_exactly_the_two_cited_sahams(self):
        """Raman names exactly two sahams for the 9th house (HTJAH-II:8664-8666)."""
        out = sphutas.sahams(_chart(_C109, asc_lon=_C109_ASC))
        assert set(out) == {"Paradesha", "Jalapathana"}

    def test_chart_109_paradesha_adds_30_to_aquarius(self):
        """Chart 109: 9th house 145d52' - Sun 16d25' + Jupiter 146d16' = 275d43';
        +30 (Lagna not between) = Aquarius 5d43' (HTJAH-II:9181-9189)."""
        s = sphutas.sahams(_chart(_C109, asc_lon=_C109_ASC))["Paradesha"]
        assert s.lon == pytest.approx(305.0 + 43 * _DEG, abs=0.02)
        assert s.sign == 11 and s.sign_lord == "Saturn"
        assert s.added_30 is True

    def test_chart_109_jalapathana_adds_30_to_aquarius(self):
        """Chart 109: Cancer 15 - Saturn 74d34' + Lagna 265d52' = 296d18';
        +30 = Aquarius 26d18' (HTJAH-II:9193-9200)."""
        s = sphutas.sahams(_chart(_C109, asc_lon=_C109_ASC))["Jalapathana"]
        assert s.lon == pytest.approx(326.0 + 18 * _DEG, abs=0.02)
        assert s.sign == 11 and s.sign_lord == "Saturn"
        assert s.added_30 is True

    def test_chart_110_paradesha_no_30_needed_leo(self):
        """Chart 110: 9th house 352d58' - Jupiter 136 + Moon 275d5' = Leo 12d3';
        NO +30 because the Lagna lies between 9th house and 9th lord
        (HTJAH-II:9231-9238) - pins the shorter-arc between test across 0 Aries."""
        s = sphutas.sahams(_chart(_C110, asc_lon=_C110_ASC))["Paradesha"]
        assert s.lon == pytest.approx(132.0 + 3 * _DEG, abs=0.02)
        assert s.sign == 5 and s.sign_lord == "Sun"
        assert s.added_30 is False

    def test_chart_110_jalapathana_adds_30_to_virgo(self):
        """Chart 110: Cancer 15 - Saturn 76d39' + Lagna 112d58' = 141d19';
        +30 = Virgo 21d19' ruled by Mercury (HTJAH-II:9245-9251)."""
        s = sphutas.sahams(_chart(_C110, asc_lon=_C110_ASC))["Jalapathana"]
        assert s.lon == pytest.approx(171.0 + 19 * _DEG, abs=0.02)
        assert s.sign == 6 and s.sign_lord == "Mercury"
        assert s.added_30 is True

    def test_rasi_house_counted_from_lagna(self):
        """Chart 109 Paradesha in Aquarius from a Sagittarius lagna = 3rd house."""
        s = sphutas.sahams(_chart(_C109, asc_lon=_C109_ASC))["Paradesha"]
        assert s.rasi_house == 3

    def test_jalapathana_skipped_when_saturn_missing(self):
        """No Saturn on a sparse chart -> Jalapathana omitted, no KeyError."""
        lons = {k: v for k, v in _C109.items() if k != "Saturn"}
        out = sphutas.sahams(_chart(lons, asc_lon=_C109_ASC))
        assert "Jalapathana" not in out and "Paradesha" in out

    def test_paradesha_skipped_when_lagna_lord_missing(self):
        """No Jupiter (Sagittarius lagna lord) -> Paradesha omitted safely."""
        lons = {k: v for k, v in _C109.items() if k != "Jupiter"}
        out = sphutas.sahams(_chart(lons, asc_lon=_C109_ASC))
        assert "Paradesha" not in out and "Jalapathana" in out

    def test_citations_resolve_on_disk(self):
        out = sphutas.sahams(_chart(_C109, asc_lon=_C109_ASC))
        for s in out.values():
            assert s.citations and all(verify(c) for c in s.citations)
