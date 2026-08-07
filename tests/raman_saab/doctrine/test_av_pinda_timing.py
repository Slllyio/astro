"""Shodhya Pinda timing, and the two rules whose blockers had already been removed.

`SYN_N9` said "(Kakshya positions not computed.)" and `SYN_N10` said "(Shodhyapinda not
computed; on record only.)" Both notes were STALE. `kakshya_timing` had been populating
`gochara[].kakshya_lord` / `.kakshya_favourable` for some time, and `ashtakavarga_pinda` has
computed the Sodya Pinda since the ASP corpus correction. The rules were waiting on primitives
that already existed — nobody had gone back to check.

That is the finding these tests exist to prevent recurring: a rule's own note is a claim about
the codebase, and claims about the codebase go stale silently.

**One limb of SYN_N10 stays deliberately unencoded** and is asserted here so it cannot be added
casually: Ashtakavarga LONGEVITY. Raman's caveat is aimed exactly and only at it — the method
"does not seem to be quite reliable" (HTJAH-II:4453-4456). The timing marker is precise and is
computed; the lifespan is not.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.av_pinda_timing import _NAK, PINDA_PLANETS, pinda_nakshatras

_CHARTS = [
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("akash", BirthData("Akash", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("canonical", BirthData("Canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("southern", BirthData("Southern", 1975, 3, 3, 4, 30, 5.5, -33.87, 151.21)),
]


@pytest.fixture(scope="module")
def charts():
    return {n: cast_chart(bd) for n, bd in _CHARTS}


class TestPindaNakshatras:
    def test_every_visible_graha_gets_a_marker(self, charts):
        for name, c in charts.items():
            rows = pinda_nakshatras(c)
            assert {r.planet for r in rows} == set(PINDA_PLANETS), name

    def test_the_nodes_are_excluded(self, charts):
        """Rahu and Ketu contribute no Ashtakavarga of their own, so they have no Pinda. The
        strict 7-graha frame, the same discipline as the Chara Karaka lock."""
        for name, c in charts.items():
            assert not {r.planet for r in pinda_nakshatras(c)} & {"Rahu", "Ketu"}, name

    def test_the_marker_is_a_real_nakshatra(self, charts):
        for name, c in charts.items():
            for r in pinda_nakshatras(c):
                assert 0 <= r.index < 27 and r.nakshatra == _NAK[r.index], name

    def test_saturn_flag_can_be_both_true_and_false(self, charts):
        """THE guard. The flag first shipped comparing a NAME to `PlanetPos.nakshatra`, which is
        a 1-based INDEX — so it was silently False on every chart. A flag that cannot be true is
        indistinguishable from one that is merely rarely true, and only this assertion separates
        them."""
        seen = {r.saturn_is_there for c in charts.values() for r in pinda_nakshatras(c)}
        assert seen == {True, False}, (
            f"saturn_is_there took only {seen} across four charts — if it can never be True the "
            f"comparison is broken, as it once was")

    def test_the_flag_agrees_with_saturns_own_nakshatra(self, charts):
        """Independent recomputation, not a re-read of the same expression."""
        for name, c in charts.items():
            sat_idx = int(c.planets["Saturn"].nakshatra) - 1
            for r in pinda_nakshatras(c):
                assert r.saturn_is_there == (sat_idx == r.index), f"{name}/{r.planet}"


class TestBothRulesAreNowEvaluable:
    @pytest.mark.parametrize("rule_id", ["SYN_N9_KAKSHYA_TRANSIT", "SYN_N10_AV_LONGEVITY"])
    def test_no_longer_descriptive(self, rule_id):
        from app.raman_saab.doctrine.synthesis_rules import descriptive_rules
        assert rule_id not in {r.id for r in descriptive_rules()}

    @pytest.mark.parametrize("rule_id", ["SYN_N9_KAKSHYA_TRANSIT", "SYN_N10_AV_LONGEVITY"])
    def test_stays_in_the_av_band(self, rule_id):
        """Raman rates Ashtakavarga corroborative, not decisive. The band encodes that
        precedence and neither rule may leave it."""
        from app.raman_saab.doctrine.synthesis_rules import SYNTHESIS_RULES
        r = next(x for x in SYNTHESIS_RULES if x.id == rule_id)
        assert r.band == "av"

    def test_only_three_rules_remain_on_record(self):
        """And each of the three is closed by DECISION, not by a missing primitive: N5 would
        double-count Raman's own GBB rule, N12 conflicts with the locked Vimshottari
        proportions, N14 is modern practice. If this count drops, something was encoded that
        a lock forbids; if it rises, a rule regressed."""
        from app.raman_saab.doctrine.synthesis_rules import descriptive_rules
        assert {r.id for r in descriptive_rules()} == {
            "SYN_N5_BPHS_ISHTA_ROOT", "SYN_N12_SUBPERIOD_ALLOCATION", "SYN_N14_MODERN_PROTOCOL"}


class TestTheLongevityLimbStaysUnencoded:
    def test_the_detail_never_states_a_lifespan(self):
        """Raman's caveat is aimed precisely at Ashtakavarga longevity. The rule reports the
        timing marker and says outright that the lifespan is not computed."""
        from app.raman_saab.detailed_report import build_detailed_report
        r = build_detailed_report(_CHARTS[0][1])
        fired = [i for i in r.insights if i.rule.id == "SYN_N10_AV_LONGEVITY"]
        assert fired, "the rule should fire — every chart has a Pinda"
        detail = fired[0].detail
        assert "NOT computed" in detail
        assert "does not seem to be quite reliable" in detail

    def test_the_x7_over_27_application_is_still_absent(self):
        """A one-line change would turn the Pinda into a lifespan. This makes adding it a
        deliberate act rather than an easy one."""
        import pathlib
        src = pathlib.Path("app/raman_saab/doctrine/av_pinda_timing.py").read_text(
            encoding="utf-8")
        code = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))
        assert "* 7" not in code and "/ 27" not in code, (
            "an Ayurdaya application appeared in the timing module — that is the limb Raman "
            "distrusts; if it is genuinely wanted, it needs its own doctrine review")
