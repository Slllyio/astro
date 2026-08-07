"""The Uttara Kalamrita tripod — the verse's own five conditions, after the review that
failed the first version.

The first implementation was reviewed by the bphs-doctrine-reviewer (2026-08-07) and FAILED:
the navamsa condition had been transplanted to the wrong subject (the leg planet's own
dispositor, where the verse afflicts THE MALEFICS in 4/5/8/9/12 from each support), the
no-benefic-contact clause was missing entirely, "ruined only when" inverted a sufficient
condition into a necessary one, and a "7 rupas" bhava threshold had been invented. These tests
pin the corrected shape so none of those four errors can quietly return.

The other property pinned here survived the review unchanged: the mechanism must be SHOWN able
to fire (on a constructed all-true leg), because every observation on real charts is "does not
fire" and that is indistinguishable from "cannot fire" without it.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.uk_tripod import _CONDITIONS, Leg, Tripod, tripod

_CHARTS = [
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("akash", BirthData("Akash", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("canonical", BirthData("Canonical", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("southern", BirthData("Southern", 1975, 3, 3, 4, 30, 5.5, -33.87, 151.21)),
]


def _leg(**kw) -> Leg:
    base = dict(what="lord", who="Mars", hemmed=True, with_malefic_and_weak=True,
                no_benefic_contact=True, malefics_in_dusthanas_from=True,
                their_navamsa_lords_afflicted=True)
    base.update(kw)
    return Leg(**base)


@pytest.fixture(scope="module")
def charts():
    return {n: cast_chart(bd) for n, bd in _CHARTS}


class TestTheVerseIsTheConditionSet:
    """The review's corrections, pinned structurally."""

    def test_all_five_conditions_apply_to_every_support(self, charts):
        """The bhava leg is NOT exempt from clause 2 — malefics can sit in dusthanas from an
        empty house, and the verse counts 'from the concerned Bhava' explicitly."""
        for name, c in charts.items():
            for h in (1, 7, 10):
                for leg in tripod(c, h).legs:
                    assert leg.conditions_applied == _CONDITIONS, f"{name}/{leg.what}"

    def test_the_benefic_clause_exists(self, charts):
        """Clause 1(iii) was dropped in the first version. It must be present AND able to take
        both values on real charts."""
        seen = {leg.no_benefic_contact
                for c in charts.values() for h in range(1, 13)
                for leg in tripod(c, h).legs}
        assert True in seen and False in seen

    def test_clause2_afflicts_the_malefics_not_the_leg(self, charts):
        """The navamsa condition can be True only when malefics actually sit in the dusthanas
        counted from the support — it is a statement about THOSE planets' navamsa lords."""
        for name, c in charts.items():
            for h in range(1, 13):
                for leg in tripod(c, h).legs:
                    if leg.their_navamsa_lords_afflicted is True:
                        assert leg.malefics_in_dusthanas_from is True, (
                            f"{name}/H{h}/{leg.what}: navamsa affliction without afflictors")

    def test_absence_of_afflictors_is_not_affliction(self, charts):
        """No malefic in the dusthanas -> the navamsa condition is None (unanswerable), never
        True. Absence must not condemn."""
        for name, c in charts.items():
            for h in range(1, 13):
                for leg in tripod(c, h).legs:
                    if leg.malefics_in_dusthanas_from is False:
                        assert leg.their_navamsa_lords_afflicted is None, (
                            f"{name}/H{h}/{leg.what}")


class TestTheMechanismCanProduceEitherAnswer:
    """THE guard: 'never fires' must be distinguishable from 'cannot fire'."""

    def test_an_all_true_leg_fails(self):
        assert _leg().failed is True

    def test_one_false_condition_spares_the_leg(self):
        assert _leg(no_benefic_contact=False).failed is False

    def test_one_unknown_condition_spares_the_leg(self):
        leg = _leg(with_malefic_and_weak=None)
        assert leg.failed is False
        assert leg.unknown == ("with_malefic_and_weak",)

    def test_a_full_tripod_completes(self):
        t = Tripod(8, (_leg(what="bhava", who="House 8"), _leg(what="lord", who="Mercury"),
                       _leg(what="karaka", who="Saturn")))
        assert t.complete is True
        assert t.failing == ("bhava", "lord", "karaka")


class TestSufficientNotNecessary:
    def test_the_docstring_does_not_say_only_when(self):
        """'Ruined only when' was the implementer's inversion; UK ch003:1569-1576 destroys a
        bhava on the lord alone. The module must present the tripod as one sufficient path."""
        import app.raman_saab.doctrine.uk_tripod as m
        assert "only when" not in (m.__doc__ or "").lower().replace("'only\n", "")
        assert "sufficient" in (m.__doc__ or "").lower()


class TestNoInventedThreshold:
    def test_the_bhava_weakness_uses_the_documented_knob(self):
        """The '7 rupas / 420 virupas convention' existed nowhere in the corpus. Only the
        engine's one documented (golden-tuned) threshold may decide bhava weakness here."""
        import pathlib
        src = pathlib.Path("app/raman_saab/doctrine/uk_tripod.py").read_text(encoding="utf-8")
        assert "BHAVA_BALA_MIN_SH" in src
        assert "7 rupas" not in src and "_WEAK_BHAVA_RUPAS" not in src

    def test_a_bhava_without_bhava_bala_cannot_complete(self, charts):
        for name, c in charts.items():
            for h in range(1, 13):
                bhava = tripod(c, h).legs[0]
                assert bhava.failed is False or bhava.with_malefic_and_weak is not None, name


class TestPressureIsWhatVaries:
    def test_pressure_varies_and_is_bounded(self, charts):
        seen = set()
        for name, c in charts.items():
            for h in range(1, 13):
                t = tripod(c, h)
                assert 0 <= t.pressure <= t.applicable, name
                assert t.applicable == 15
                seen.add(t.pressure)
        assert len(seen) >= 4, f"pressure took only {seen} — it cannot inform if it is flat"

    def test_met_names_agree_with_the_count(self, charts):
        for c in charts.values():
            for h in (3, 8):
                t = tripod(c, h)
                assert len(t.met) == t.pressure


class TestTheRuleIsWiredAndCorroborativeOnly:
    def test_evaluable_in_the_classical_band(self):
        from app.raman_saab.doctrine.synthesis_rules import SYNTHESIS_RULES, descriptive_rules
        assert "SYN_N6_UK_TRIPOD" not in {r.id for r in descriptive_rules()}
        r = next(x for x in SYNTHESIS_RULES if x.id == "SYN_N6_UK_TRIPOD")
        assert r.band == "classical" and r.provenance == "CLASSICAL_NONCITABLE"

    def test_the_rule_text_carries_the_verbatim_verse_and_the_review(self):
        """The first version's paraphrase-presented-as-quote became the spec the code wrongly
        implemented. The rule text must now quote the verse and record the failed review."""
        from app.raman_saab.doctrine.synthesis_rules import SYNTHESIS_RULES
        r = next(x for x in SYNTHESIS_RULES if x.id == "SYN_N6_UK_TRIPOD")
        assert "have no aspect from or conjunction with benefics" in r.doctrine
        assert "FAILED doctrine review" in r.doctrine
        assert "SUFFICIENT" in r.doctrine
