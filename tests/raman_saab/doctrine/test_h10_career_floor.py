"""H10.C.61 — the benefic-fortified, malefic-free 10th -> favourable career (subhakartari on Karma).

The placement-based FAVOURABLE-career signal (HTJAH-II:10181-10191) that fires WITHOUT Shadbala, so
it reaches Track-B charts where the strength pillars abstain. The malefic-free guard is load-bearing:
a raja/mahapurusha yoga does NOT lift a malefic-afflicted 10th, so the rule requires the 10th to be
benefic-influenced AND untouched by malefic occupation/aspect.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets.house_10_karma import combinations as comb
from app.raman_saab.judges import house_template as ht


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def _rule():
    return next(r for r in comb.RULES if r.id == "H10.C.61")


def _fires(chart: RamanChart) -> bool:
    return _rule().condition.evaluate(C.EvalContext(chart))


# Aries lagna: the 10th house is Capricorn (270-300 deg). Venus is undebilitated in Capricorn;
# Jupiter is DEBILITATED there (used for the exclude_debil test).
class TestH10C61:
    def test_benefic_in_tenth_no_malefic_fires(self):
        """An undebilitated benefic (Venus) in the 10th with no malefic influence -> the rule fires."""
        assert _fires(_chart({"Venus": 285.0, "Moon": 45.0})) is True

    def test_benefic_aspecting_tenth_fires(self):
        """A benefic that ASPECTS the 10th (Jupiter in the 6th, undebilitated in Virgo, aspects the
        10th by its 5th drishti), with no malefic influence, also fires."""
        assert _fires(_chart({"Jupiter": 165.0})) is True   # Jupiter h6 -> 5th aspect on h10

    def test_debilitated_benefic_does_not_fortify(self):
        """A DEBILITATED benefic (Jupiter in Capricorn = the 10th) does NOT count as a fortifier
        (bphs-reviewer flag: a debilitated significator does not fortify)."""
        assert _fires(_chart({"Jupiter": 285.0})) is False

    def test_malefic_in_tenth_blocks_the_lift(self):
        """A malefic occupying the 10th cancels the fortification (Hitler-style Saturn-in-10th)."""
        assert _fires(_chart({"Venus": 285.0, "Saturn": 280.0})) is False

    def test_malefic_aspecting_tenth_blocks_the_lift(self):
        """A malefic aspecting the 10th (Saturn in the 4th, 7th aspect on the 10th) also cancels it."""
        assert _fires(_chart({"Venus": 285.0, "Saturn": 95.0})) is False

    def test_no_benefic_influence_does_not_fire(self):
        """No benefic on/aspecting the 10th -> nothing to lift."""
        assert _fires(_chart({"Sun": 285.0})) is False

    def test_career_verdict_is_favourable_on_a_benefic_fortified_tenth(self):
        """End to end: a Track-B chart with an undebilitated-benefic-fortified, malefic-free 10th
        judges the career favourable (the abstain is closed)."""
        chart = _chart({"Venus": 285.0, "Moon": 40.0})
        pf = ht.judge_house(chart, 10)
        sv = next((s for s in pf.significations if s.signification == "career"), None)
        assert sv is not None and sv.verdict == "favourable"
