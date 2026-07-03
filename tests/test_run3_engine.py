"""Tests for the run-3 Triple-Lock engine modules.

Covers:
- transit_table  — ingress table vs direct swe.calc_ut (property test)
- gochara_death  — vectorized T1/T2/T3 vs the production gochara engine
                   (parity oracle) + hand cases
- ayurdaya       — P3 table exhaustively, HL anchor identities, sunrise
                   golden, tie-break, band_of_age boundaries, and the
                   B. V. Raman end-to-end golden chart
"""
from __future__ import annotations

import numpy as np
import pytest
import swisseph as swe

from app.medini.ml.raman_saab import gochara_death as G
from app.medini.ml.raman_saab.ayurdaya import (
    ALPAYU_MAX, MADHYAYU_MAX, AyuBand, band_of_age, compute_ayurdaya,
    hora_lagna_lon, modality, pair_band, sunrise_before, _sun_sidereal_lon,
)
from app.medini.ml.raman_saab.kundali import cast_kundali
from app.medini.ml.raman_saab.transit_table import (
    _PLANET_IDS, get_table, sidereal_lon,
)

# ── transit_table ────────────────────────────────────────────────────────────


class TestTransitTable:
    def test_table_matches_direct_on_random_dates(self):
        """Property test: table sign == direct ephemeris sign on 300 random
        JDs across the full range (guards missed station-grazing ingresses)."""
        rng = np.random.default_rng(42)
        jd0 = swe.julday(1851, 1, 1, 0.0, swe.GREG_CAL)
        jd1 = swe.julday(2034, 1, 1, 0.0, swe.GREG_CAL)
        jds = rng.uniform(jd0, jd1, size=300)
        for planet in ("Saturn", "Jupiter", "Mars"):
            table = get_table(planet)
            got = table.sign_at(jds)
            want = np.array([int(sidereal_lon(j, _PLANET_IDS[planet]) // 30) + 1
                             for j in jds])
            # Allow the ±0.5-day boundary tolerance: any mismatch must sit
            # within 0.5 day of an ingress.
            mism = got != want
            for j in jds[mism]:
                dist = np.abs(table.ingress_jd - j).min()
                assert dist <= 0.5, f"{planet} sign mismatch {dist:.2f}d from ingress"

    def test_ingress_counts_plausible(self):
        # 185 years: Saturn ~29.5y/cycle -> >=75 ingresses (+ retro re-entries);
        # Jupiter ~11.9y/cycle -> >=185.
        assert len(get_table("Saturn").ingress_jd) >= 75
        assert len(get_table("Jupiter").ingress_jd) >= 185
        # Mars ~1.88y/cycle -> >=1100 ingresses incl. retro re-entries.
        assert len(get_table("Mars").ingress_jd) >= 1100


# ── gochara_death ────────────────────────────────────────────────────────────


class TestGocharaHandCases:
    def test_t1_sade_sati_bands(self):
        # Moon in Aries(1): Saturn in Pisces(12), Aries(1), Taurus(2) = active.
        sat = np.array([12, 1, 2, 3, 7])
        got = G.t1_sade_sati(sat, moon_sign=1)
        assert got.tolist() == [True, True, True, False, False]

    def test_t2_saturn_8h(self):
        # Lagna Aries(1): 8H is Scorpio(8).
        sat = np.array([8, 7, 9])
        assert G.t2_saturn_in_8h(sat, asc_sign=1).tolist() == [True, False, False]

    def test_t3_requires_both(self):
        # Lagna Aries: 8H=Scorpio. Saturn IN 8H + Jupiter aspecting 8H via
        # 5th drishti (Jupiter in 4H Cancer -> 5th from 4H is 8H) -> True.
        sat = np.array([8]); jup = np.array([4])
        assert G.t3_double_transit_8h(sat, jup, asc_sign=1).tolist() == [True]
        # Saturn in 8H but Jupiter nowhere near 8H (Jupiter 1H: drishti 5,7,9) -> False
        jup2 = np.array([1])
        assert G.t3_double_transit_8h(sat, jup2, asc_sign=1).tolist() == [False]

    def test_t4_protective_jupiter(self):
        # Moon Aries: kendras from Moon = signs 1,4,7,10. Jupiter there -> protected.
        jup = np.array([1, 4, 7, 10, 2, 5])
        got = G.t4_no_protective_jupiter(jup, moon_sign=1)
        assert got.tolist() == [False, False, False, False, True, True]


class TestGocharaParityOracle:
    """Randomized parity vs the production gochara engine (T3 semantics)."""

    def test_double_transit_8h_matches_compute_gochara(self):
        from app.core.chart_model import Chart
        from app.core.gochara_engine import compute_gochara
        rng = np.random.default_rng(7)
        grahas = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                  "Saturn", "Rahu", "Ketu")
        n_checked = 0
        for _ in range(200):
            asc = int(rng.integers(1, 13))
            natal_signs = {g: int(rng.integers(1, 13)) for g in grahas}
            chart = Chart(
                asc_sign=asc, asc_lon=(asc - 1) * 30.0 + 15.0,
                planet_signs=natal_signs,
                planet_houses={g: ((s - asc) % 12) + 1
                               for g, s in natal_signs.items()},
                planet_lons={g: (s - 1) * 30.0 + 10.0
                             for g, s in natal_signs.items()},
                planet_retrograde={g: False for g in grahas},
            )
            transit_signs = {g: int(rng.integers(1, 13)) for g in grahas}
            verdict = compute_gochara(chart, transit_signs)
            state = verdict.per_bhava[8]
            oracle = bool(state.is_double_transit_bhava)
            ours = bool(G.t3_double_transit_8h(
                np.array([transit_signs["Saturn"]]),
                np.array([transit_signs["Jupiter"]]),
                asc_sign=asc)[0])
            assert ours == oracle, (
                f"T3 parity broke: asc={asc} "
                f"sat={transit_signs['Saturn']} jup={transit_signs['Jupiter']} "
                f"ours={ours} oracle={oracle}")
            n_checked += 1
        assert n_checked == 200

    def test_sade_sati_matches_engine_semantics(self):
        from app.core.sade_sati import is_in_sade_sati
        for moon in range(1, 13):
            for sat in range(1, 13):
                ours = bool(G.t1_sade_sati(np.array([sat]), moon)[0])
                oracle = is_in_sade_sati(sat, moon) is not None
                assert ours == oracle


# ── ayurdaya ────────────────────────────────────────────────────────────────

# Independently hand-written modality + P3 tables (NOT derived from the code).
_HAND_MODALITY = {1: "chara", 2: "sthira", 3: "dvisvabhava", 4: "chara",
                  5: "sthira", 6: "dvisvabhava", 7: "chara", 8: "sthira",
                  9: "dvisvabhava", 10: "chara", 11: "sthira", 12: "dvisvabhava"}
_HAND_P3 = {
    frozenset(["chara"]): AyuBand.PURNAYU,
    frozenset(["sthira", "dvisvabhava"]): AyuBand.PURNAYU,
    frozenset(["dvisvabhava"]): AyuBand.MADHYAYU,
    frozenset(["chara", "sthira"]): AyuBand.MADHYAYU,
    frozenset(["sthira"]): AyuBand.ALPAYU,
    frozenset(["chara", "dvisvabhava"]): AyuBand.ALPAYU,
}


class TestAyurdayaPrimitives:
    @pytest.mark.parametrize("a", range(1, 13))
    @pytest.mark.parametrize("b", range(1, 13))
    def test_p3_table_exhaustive(self, a, b):
        want = _HAND_P3[frozenset([_HAND_MODALITY[a], _HAND_MODALITY[b]])]
        assert pair_band(a, b) == want

    def test_modality_partition(self):
        assert sorted(s for s in range(1, 13) if modality(s) == "chara") == [1, 4, 7, 10]
        assert sorted(s for s in range(1, 13) if modality(s) == "sthira") == [2, 5, 8, 11]

    def test_band_of_age_boundaries(self):
        assert band_of_age(31.999) == AyuBand.ALPAYU
        assert band_of_age(ALPAYU_MAX) == AyuBand.MADHYAYU
        assert band_of_age(69.999) == AyuBand.MADHYAYU
        assert band_of_age(MADHYAYU_MAX) == AyuBand.PURNAYU
        assert band_of_age(100.0) == AyuBand.PURNAYU


class TestHoraLagna:
    # Bangalore, a mid-latitude tropical site with well-known sunrise times.
    LAT, LON = 12.9716, 77.5946

    def test_sunrise_precedes_birth_and_is_recent(self):
        birth_jd = swe.julday(1912, 8, 8, 19.7 - 5.5, swe.GREG_CAL)  # 19:42 IST
        rise = sunrise_before(birth_jd, self.LAT, self.LON)
        assert 0 < birth_jd - rise < 1.0  # same local day

    def test_hl_anchor_identity_at_sunrise(self):
        birth_jd = swe.julday(1950, 3, 10, 6.0, swe.GREG_CAL)
        rise = sunrise_before(birth_jd, self.LAT, self.LON)
        assert hora_lagna_lon(rise, rise) == pytest.approx(
            _sun_sidereal_lon(rise), abs=1e-9)

    def test_hl_advances_30deg_per_hour(self):
        birth_jd = swe.julday(1950, 3, 10, 6.0, swe.GREG_CAL)
        rise = sunrise_before(birth_jd, self.LAT, self.LON)
        h0 = hora_lagna_lon(rise, rise)
        h2 = hora_lagna_lon(rise + 2.0 / 24.0, rise)
        assert (h2 - h0) % 360.0 == pytest.approx(60.0, abs=1e-6)

    def test_bangalore_sunrise_golden(self):
        # 1912-08-08 Bangalore sunrise ≈ 06:03 IST (almanac; ±3 min).
        birth_jd = swe.julday(1912, 8, 8, 19.7 - 5.5, swe.GREG_CAL)
        rise = sunrise_before(birth_jd, self.LAT, self.LON)
        y, m, d, ut = swe.revjul(rise, swe.GREG_CAL)
        ist = (ut + 5.5) % 24.0
        assert (y, m, d) == (1912, 8, 8)
        assert ist == pytest.approx(6.05, abs=0.05)  # 06:03 ± 3 min


class TestAyurdayaGolden:
    def test_bv_raman_chart_end_to_end(self):
        """B. V. Raman: 1912-08-08 19:42 IST, Bangalore (12.97N 77.59E).

        Hand-computation with the engine's Lahiri positions:
        - Lagna: Aquarius (11, sthira) — matches Raman's published chart.
        - Pair 1 (Lagna & lagna-lord): lord Saturn sits in Taurus (2, sthira)
          -> sthira+sthira -> ALPAYU.
        - Pair 2 (Moon & Saturn): Moon Taurus (2), Saturn Taurus (2)
          -> sthira+sthira -> ALPAYU.
        - Pair 3 (Lagna & Hora Lagna): birth ~13.6h after the ~06:03 IST
          sunrise -> HL advanced ~408° ≈ Sun(Cancer ~113°) + 408° ≈ 161°
          = Virgo (6, dvisvabhava) -> sthira+dvisvabhava -> PURNAYU.
        Majority: ALPAYU (2 of 3), no tie-break.

        He died 1998-12-20 at age 86 — observed PURNAYU. The doctrine's
        miss on its own author is recorded, not patched (prereg P11: no
        exception rules in v1).
        """
        k = cast_kundali(1912, 8, 8, 19, 42, 5.5, 12.9716, 77.5946)
        assert k is not None
        assert k.lagna_sign == 11
        res = compute_ayurdaya(k, 12.9716, 77.5946)
        assert [p.band for p in res.pairs] == [
            AyuBand.ALPAYU, AyuBand.ALPAYU, AyuBand.PURNAYU]
        assert res.band == AyuBand.ALPAYU
        assert res.tie_broken is False
        assert res.hora_lagna_sign == 6
        assert band_of_age(86.4) == AyuBand.PURNAYU

    def test_three_way_tie_uses_lagna_hl_pair(self, monkeypatch):
        """Synthetic 3-way split: verify P7 tie-break wiring."""
        from app.medini.ml.raman_saab import ayurdaya as A

        class FakeK:
            lagna_sign = 1                       # chara
            birth_jd = swe.julday(1950, 6, 1, 6.0, swe.GREG_CAL)
            # lagna lord Mars in house 7 -> sign 7 (chara): pair1 chara+chara
            #   -> PURNAYU
            # Moon h2 -> sign 2 (sthira), Saturn h4 -> sign 4 (chara):
            #   pair2 chara+sthira -> MADHYAYU
            planet_house = {"Mars": 7, "Moon": 2, "Saturn": 4}

        # Force HL sign to Virgo (6, dvisvabhava): pair3 chara+dvisvabhava
        #   -> ALPAYU. Three-way split -> pair 3 prevails -> ALPAYU.
        monkeypatch.setattr(A, "sunrise_before", lambda *a, **k: FakeK.birth_jd - 0.1)
        monkeypatch.setattr(A, "hora_lagna_lon", lambda *a, **k: 165.0)
        res = A.compute_ayurdaya(FakeK, 10.0, 76.0)
        assert res.tie_broken is True
        assert res.tie_rule == "lagna_horalagna_prevails"
        assert res.band == AyuBand.ALPAYU
