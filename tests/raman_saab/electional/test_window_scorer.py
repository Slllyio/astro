"""Window scorer — the MUHURTHA-10:226-228 essentials, hard-fail + rank behaviour."""
from __future__ import annotations

from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.electional.negative_windows import Window, rahu_kalam
from app.raman_saab.electional.window_scorer import evaluate_moment

_SUNRISE = 2460000.0
_SUNSET = _SUNRISE + 0.5

_CLEAN = dict(janma_nakshatra=1, janma_rasi=1, tithi_in_paksha=2, weekday=3,
              day_nakshatra=22, yoga=2, karana=1, election_moon_rasi=2, lagna_sign=1)


class TestEvaluateMoment:
    def test_a_clean_moment_scores_full_and_passes(self):
        """All five limbs suitable + Kshema tarabala + Chandrabala + favourable panchaka
        (2+4+22+1 = 29 ... wait: 2+4+22+1 = 29 -> 2 agni; pick lagna 2 -> 30 -> 3 good)."""
        ev = evaluate_moment(jd=_SUNRISE + 0.2, **{**_CLEAN, "lagna_sign": 2})
        assert ev.ok and not ev.hard_failures
        assert ev.tarabala.name == "Kshema"
        assert ev.score == 8

    def test_inside_rahu_kalam_hard_fails_with_the_label(self):
        rk = rahu_kalam(3, _SUNRISE, _SUNSET)          # Wednesday midday eighth
        mid = (rk.start_jd + rk.end_jd) / 2
        ev = evaluate_moment(jd=mid, **{**_CLEAN, "lagna_sign": 2},
                             negative_windows=(rk,))
        assert not ev.ok and "Rahu Kalam" in ev.hard_failures

    def test_failed_chandrabala_is_a_hard_failure(self):
        """MUHURTHA-3:66-71 — Moon 12th from Janma Rasi."""
        ev = evaluate_moment(jd=_SUNRISE + 0.2,
                             **{**_CLEAN, "lagna_sign": 2, "election_moon_rasi": 12})
        assert not ev.ok and any("Chandrabala" in f for f in ev.hard_failures)

    def test_unfavourable_panchaka_hard_fails_without_an_act_exception(self):
        """lagna 1 keeps the total at 29 -> agni; no act given -> hard failure; the
        marriage exception (MUHURTHA-3:157-168) lifts it."""
        bad = evaluate_moment(jd=_SUNRISE + 0.2, **_CLEAN)
        assert not bad.ok and any("Panchaka" in f for f in bad.hard_failures)
        ok = evaluate_moment(jd=_SUNRISE + 0.2, act="marriage", **_CLEAN)
        assert ok.ok

    def test_windows_carry_citations(self):
        w = Window(0.0, 1.0, "x", Citation("MUHURTHA-18", 767))
        assert w.source.work == "MUHURTHA-18"
