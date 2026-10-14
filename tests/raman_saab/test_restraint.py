"""Restraint — how firmly each house stands, and where the engine declines to decide.

The guards here are against the two ways a restraint faculty fails silently: a branch that can
never fire (the first version's `unsettled` was unreachable, so the engine could never restrain
anything and read as pure confidence), and a threshold invented locally instead of taken from
the engine's own contest classification (which flagged a 4-vs-1 majority as undecided).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.restraint import (
    PREMATURE_CITE,
    STANDING_CONCENTRATED,
    STANDING_CONCORDANT,
    STANDING_GOVERNED,
    STANDING_UNSETTLED,
    house_restraint,
    unsettled_houses,
)

_CHARTS = [
    ("canonical", BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("scorpio", BirthData("Scorpio", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
    ("mumbai", BirthData("Mumbai", 1975, 3, 3, 4, 30, 5.5, 19.07, 72.87)),
    ("delhi", BirthData("Delhi", 2001, 11, 9, 21, 15, 5.5, 28.61, 77.20)),
]


@pytest.fixture(scope="module")
def reports():
    return {name: build_detailed_report(bd) for name, bd in _CHARTS}


class TestNoDeadBranches:
    def test_every_standing_actually_occurs(self, reports):
        """THE regression guard. The first implementation decided `unsettled` by lord/karaka
        strength — but dominance already fires on every strength difference, so the branch was
        unreachable and the engine could never decline. A restraint faculty that cannot restrain
        is worse than none: it reads as confidence."""
        seen = {x.standing for r in reports.values() for x in house_restraint(r).values()}
        for standing in (STANDING_GOVERNED, STANDING_CONCORDANT,
                         STANDING_CONCENTRATED, STANDING_UNSETTLED):
            assert standing in seen, f"{standing!r} never occurs — the branch is dead"

    def test_the_engine_declines_on_a_real_share_of_houses(self, reports):
        """Restraint that fires almost never, or almost always, is not calibrated."""
        total = sum(len(house_restraint(r)) for r in reports.values())
        soft = sum(len(unsettled_houses(r)) for r in reports.values())
        assert 0.05 <= soft / total <= 0.50, f"{soft}/{total} houses unsettled — implausible"


class TestUsesTheEnginesOwnJudgment:
    def test_unsettled_matches_the_engine_contested_status(self, reports):
        """`unsettled` must be the engine's own `status == "contested"`, never a ratio invented
        here. House 1 at 4 favourable / 1 adverse reads well-corroborated while house 12 at the
        same 4/1 reads contested — what matters is whether the dissent bears on the headline,
        which the engine already decided."""
        for r in reports.values():
            engine_contested = {h.house for h in r.preponderance.houses
                                if h.status == "contested"}
            soft = set(unsettled_houses(r))
            assert soft <= engine_contested, (
                f"softened houses {sorted(soft - engine_contested)} that the engine does not "
                f"call contested — a locally invented threshold")

    def test_soften_is_set_only_for_unsettled(self, reports):
        """Only genuine indecision may soften the prose. A house that is uniformly strong is a
        FIRM reading, not an uncertain one, and must never be hedged."""
        for r in reports.values():
            for x in house_restraint(r).values():
                assert x.soften == (x.standing == STANDING_UNSETTLED)


class TestContract:
    def test_every_house_is_accounted_for(self, reports):
        """No house may fall through unclassified — silence is what this module exists to end."""
        for name, r in reports.items():
            got = set(house_restraint(r))
            expected = {pf.house for pf in r.proformas if pf.significations}
            assert got == expected, f"{name}: unclassified houses {sorted(expected - got)}"

    def test_every_classification_carries_ramans_citation(self, reports):
        """The injunction is his — no slip-shod interpretation, no premature conclusion."""
        for r in reports.values():
            for x in house_restraint(r).values():
                assert PREMATURE_CITE in x.cites
                assert x.reason and x.sentence

    def test_sentences_pass_the_llm_guard(self, reports):
        from app.llm.report_explainer import _FORBIDDEN_RE
        for r in reports.values():
            for x in house_restraint(r).values():
                m = _FORBIDDEN_RE.search(x.sentence)
                assert m is None, f"restraint sentence trips the guard: {m.group(0)!r}"

    def test_is_a_pure_re_read(self, reports):
        """PREC-10: restraint annotates how firmly a reading stands. It must not change one —
        the house verdicts are identical whether or not restraint is computed."""
        for r in reports.values():
            before = [pf.rollup for pf in r.proformas]
            house_restraint(r)
            assert [pf.rollup for pf in r.proformas] == before
