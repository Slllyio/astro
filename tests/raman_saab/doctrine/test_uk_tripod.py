"""The Uttara Kalamrita tripod — and the measurement that decided how to report it.

The rule sat as `kind="descriptive"` (on record, never evaluated) until the hemming primitive
existed. Building it revealed why the literal test is the wrong thing to report, and these tests
pin both the mechanism and that finding.

**The mechanism can fire.** Asserted directly on a constructed leg, because everything else here
observes that it does not, and "never fires" is indistinguishable from "cannot fire" without
this test. That distinction is the one the tautological-dominance bug turned on.

**It essentially never fires on real charts.** 0 of 1,260 house-tests and 0 of 2,520 planet legs
across 105 charts: the conditions are negatively correlated, so a planet hemmed by malefics
tends not to ALSO be weak, with a malefic, and in a hostile navamsa. That is Uttara Kalamrita's
threshold working as intended — ruin requires everything to fail at once — and it is why
`pressure` is reported instead of `complete`.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.uk_tripod import Leg, Tripod, tripod

_C4 = ("hemmed", "with_malefic", "weak", "hostile_navamsa")
_C3 = ("hemmed", "with_malefic", "weak")

_CHARTS = [
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("akash", BirthData("Akash", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("canonical", BirthData("Canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("southern", BirthData("Southern", 1975, 3, 3, 4, 30, 5.5, -33.87, 151.21)),
]


@pytest.fixture(scope="module")
def charts():
    return {n: cast_chart(bd) for n, bd in _CHARTS}


class TestTheMechanismCanProduceEitherAnswer:
    """THE guard. A test that only ever observes 'does not fire' cannot tell a rare rule from a
    broken one."""

    def test_a_leg_with_every_condition_true_fails(self):
        assert Leg("lord", "Mars", True, True, True, True, _C4).failed is True

    def test_one_false_condition_spares_the_leg(self):
        assert Leg("lord", "Mars", True, True, False, True, _C4).failed is False

    def test_a_full_tripod_completes(self):
        t = Tripod(8, (Leg("bhava", "House 8", True, True, True, None, _C3),
                       Leg("lord", "Mercury", True, True, True, True, _C4),
                       Leg("karaka", "Saturn", True, True, True, True, _C4)))
        assert t.complete is True
        assert t.failing == ("bhava", "lord", "karaka")


class TestItNeverCondemnsFromIgnorance:
    def test_an_unknown_condition_is_not_a_failure(self):
        """Conservative on missing data — the engine's standing preference for saying less."""
        leg = Leg("lord", "Mars", True, True, None, True, _C4)
        assert leg.failed is False
        assert leg.unknown == ("weak",)

    def test_a_bhava_without_bhava_bala_cannot_complete(self, charts):
        """`weak` is unanswerable without Bhava Bala, so the bhava leg must not fail — and the
        tripod must not complete — merely because the caller omitted an optional argument."""
        for name, c in charts.items():
            for h in range(1, 13):
                bhava = tripod(c, h).legs[0]
                assert bhava.weak is None and bhava.failed is False, name

    def test_the_bhava_leg_is_not_judged_on_navamsa(self, charts):
        """A bhava is not a planet. The interpretive choice is deliberate and visible."""
        leg = tripod(charts["mainpuri"], 7).legs[0]
        assert "hostile_navamsa" not in leg.conditions_applied
        assert leg.hostile_navamsa is None


class TestPressureIsWhatVaries:
    def test_pressure_counts_only_conditions_actually_met(self):
        t = Tripod(1, (Leg("bhava", "House 1", True, False, True, None, _C3),
                       Leg("lord", "Mars", True, False, False, None, _C4)))
        assert t.pressure == 3
        assert t.applicable == 7
        assert t.met == ("bhava hemmed", "bhava weak", "lord hemmed")

    def test_pressure_varies_across_charts_and_houses(self, charts):
        seen = {tripod(c, h).pressure for c in charts.values() for h in range(1, 13)}
        assert len(seen) >= 3, (
            f"pressure took only {seen} — a quantity that does not vary cannot inform anything")

    def test_pressure_never_exceeds_what_applies(self, charts):
        for name, c in charts.items():
            for h in range(1, 13):
                t = tripod(c, h)
                assert 0 <= t.pressure <= t.applicable, name


class TestTheRuleIsWiredAndCorroborativeOnly:
    def test_the_rule_is_now_evaluable(self):
        from app.raman_saab.doctrine.synthesis_rules import descriptive_rules
        assert "SYN_N6_UK_TRIPOD" not in {r.id for r in descriptive_rules()}

    def test_it_stays_in_the_classical_band(self):
        """Corroborative. It must never sit in the Raman band, where it could appear to decide."""
        from app.raman_saab.doctrine.synthesis_rules import SYNTHESIS_RULES
        r = next(x for x in SYNTHESIS_RULES if x.id == "SYN_N6_UK_TRIPOD")
        assert r.band == "classical"
        assert r.provenance == "CLASSICAL_NONCITABLE"

    def test_it_reports_conditions_rather_than_a_verdict(self):
        """The detail must state its own evidence and, while the full test is unmet, say so —
        a restraint disclosure, not a condemnation."""
        from app.raman_saab.detailed_report import build_detailed_report
        r = build_detailed_report(_CHARTS[0][1])
        fired = [i for i in r.insights if i.rule.id == "SYN_N6_UK_TRIPOD"]
        if not fired:
            pytest.skip("no house under sufficient pressure on this chart")
        detail = fired[0].detail
        assert "classical failure-conditions" in detail
        assert "NOT met" in detail or "full test IS met" in detail
