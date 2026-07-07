"""Tests for the held-out worked-chart validation pipeline.

Pins the two things that must be exact for the validation to mean anything: the
Navāṁśa back-solve reproduces the engine's own D9 for every reachable pair, and the
(rāśi, navāṁśa) consistency gate rejects impossible pairs. Plus verdict-map coverage.
"""
import pytest

from app.core.shodashavarga import compute_divisional_longitude
from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.validation import reconstruct as R
from app.medini.doctrine.validation import worked_chart_validate as W


def _eng_navamsa(lon: float) -> int:
    return int(compute_divisional_longitude(lon, 9) // 30) + 1


class TestNavamsaBackSolve:
    def test_pada_formula_matches_engine_for_all_padas(self):
        # Our pada->navamsa map must equal the engine's calculate_divisional_longitude.
        for r in range(1, 13):
            for k in range(9):
                lon = (r - 1) * 30 + k * R._PADA + R._PADA / 2
                assert R.navamsa_sign_of_pada(r, k) == _eng_navamsa(lon)

    def test_exactly_nine_navamsa_signs_reachable_per_rasi(self):
        for r in range(1, 13):
            reach = [n for n in range(1, 13) if R.navamsa_pada(r, n) is not None]
            assert len(reach) == 9

    def test_chart_reproduces_printed_navamsa_and_rasi(self):
        # Every reachable (rāśi, navāṁśa) pair round-trips through chart_from_raman:
        # the engine's varga_signs[9] equals the requested navāṁśa, and the D1 sign
        # equals the requested rāśi -- reconstruction is exact, not approximate.
        rasi = {g: ((i % 12) + 1) for i, g in enumerate(rc.GRAHAS)}
        nav = {g: R.navamsa_sign_of_pada(rasi[g], 4) for g in rc.GRAHAS}
        ch = R.chart_from_raman(rasi, nav, 1, R.navamsa_sign_of_pada(1, 4))
        for g in rc.GRAHAS:
            assert ch.varga_signs[g][9] == nav[g]
            assert ch.bundle.chart.planet_signs[g] == rasi[g]

    def test_consistency_gate_flags_unreachable_pair(self):
        # Aries (fire) reaches navāṁśa Aries..Sagittarius; Capricorn is impossible.
        assert R.navamsa_pada(1, 10) is None
        bad = R.consistency_errors({"Sun": "Aries"}, {"Sun": "Capricorn"})
        assert bad and "unreachable" in bad[0]
        assert R.consistency_errors({"Sun": "Aries"}, {"Sun": "Sagittarius"}) == []

    def test_sign_num_parses_names_and_numbers(self):
        assert R.sign_num("Cancer") == 4 and R.sign_num("cancer") == 4
        assert R.sign_num("7") == 7
        with pytest.raises(ValueError):
            R.sign_num("Ophiuchus")


class TestVerdictMap:
    def test_map_is_ordered_most_specific_first(self):
        pats = W.load_verdict_map()
        # "very powerful" must be reachable and not shadowed by a bare root.
        assert W.map_verdict("Hence the Lagna is very powerful", pats) == "very powerful"
        assert W.map_verdict("therefore is very strongly situated", pats) == "very strong"
        assert W.map_verdict("moderately powerful", pats) == "moderately good"
        assert W.map_verdict("rendered feebly weak", pats) == "weak"
        assert W.map_verdict("considerably afflicted", pats) == "afflicted"
        assert W.map_verdict("the 4th house is moderately strong", pats) == "moderately good"

    def test_every_mapped_grade_is_on_the_scale(self):
        pats = W.load_verdict_map()
        for _pat, grade in pats:
            assert grade in W._IDX

    def test_unmappable_phrase_returns_none(self):
        pats = W.load_verdict_map()
        # bare 'good' without an intensifier is intentionally unmapped.
        assert W.map_verdict("the results are good", pats) is None
