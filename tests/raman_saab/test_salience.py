"""Salience — pinning a MEASURED result so it cannot be edited away by accident.

`app/raman_saab/salience.py` scores which house a reader should meet first, and it drives the
digest — the most-read section of the report. Every chart-specific modulation weight in it is
**zero**, which is not a placeholder and not an oversight: it is the outcome of the salience
programme (`docs/raman_saab/SALIENCE_BASELINE.md`). Eight signals were ablated across two
independent benchmarks at n=14 and n=95, and none beat doctrine alone. Raman's attention is
predicted by doctrine and by nothing else the engine computes.

A zero weight is a fact that looks exactly like a stub. Nothing about the module's shape says
"this was measured"; a later reader sees five weights set to 0.0 and reasonably concludes the
feature is half-built. These tests are the difference between the two readings.

The consequence worth stating plainly: with the weights at zero, `house_salience` returns the
SAME ordering for every chart in existence. That is the correct encoding of the finding, and it
means a single edited constant silently changes what every reader meets first while invalidating
the whole Phase 1-3 record. Nothing else in the tree would fail.

If a signal ever clears the doctrinal prior on holdout — paired, interval excluding zero, the bar
this programme has used throughout — these tests are EXPECTED to change. They exist to make that
change deliberate and measured, not incidental.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.salience import (
    DOCTRINAL_PRIOR,
    W_CENTRALITY,
    W_EXTREMITY,
    W_PRIOR,
    W_SURPRISAL,
    W_YOGA,
    house_salience,
    rank_houses,
)

#: Structurally unlike each other on purpose — different ascendants, eras, and latitudes. If any
#: chart-specific term were live, these would not rank identically.
_CHARTS = [
    ("canonical", BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)),
    ("mainpuri", BirthData("Mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03)),
    ("scorpio", BirthData("Scorpio", 1989, 12, 11, 6, 20, 5.5, 23.20, 77.08)),
]

#: Raman's order of examination, COPIED BY HAND. Deriving this from `DOCTRINAL_PRIOR` would make
#: the test pass silently whenever the prior and the expectation are edited in the same commit —
#: the exact failure mode `_ORDER_V34` is hand-copied to prevent for the reading arc.
_DOCTRINAL_ORDER = (1, 10, 7, 9, 4, 5, 2, 11, 8, 12, 6, 3)


@pytest.fixture(scope="module")
def reports():
    return {name: build_detailed_report(bd) for name, bd in _CHARTS}


class TestTheMeasurementIsLocked:
    def test_the_prior_is_the_whole_score(self):
        """Every modulation weight is zero because each was measured and each lost.

        Ablated on the tune split against Raman's own emphasis (SALIENCE_BASELINE Phase 1b) and
        again on a 7x larger benchmark (Phase 3): surprisal, extremity, graph centrality,
        occupancy, dignity, house-lord shadbala, lord-strength deviation and yoga-by-kind all
        rank WORSE than the doctrinal prior alone. Raising any of these without a fresh holdout
        measurement would silently reorder every reader's digest.
        """
        assert W_PRIOR == 1.0
        assert (W_SURPRISAL, W_EXTREMITY, W_CENTRALITY, W_YOGA) == (0.0, 0.0, 0.0, 0.0), (
            "a modulation weight is live. That may be right — but it must be earned on the "
            "holdout split, paired, with an interval excluding zero, and recorded in "
            "docs/raman_saab/SALIENCE_BASELINE.md before this test is updated"
        )

    def test_doctrinal_order_is_the_reviewed_one(self):
        """The shipped order of examination: Lagna, then kendras and trikonas, then the rest."""
        derived = tuple(h for h, _ in sorted(DOCTRINAL_PRIOR.items(), key=lambda kv: -kv[1]))
        assert derived == _DOCTRINAL_ORDER

    def test_every_house_is_scored(self):
        """All twelve carry an explicit prior — none falls through to the 0.45 default."""
        assert sorted(DOCTRINAL_PRIOR) == list(range(1, 13))
        assert len(set(DOCTRINAL_PRIOR.values())) == 12, "a tie would let house number decide"


class TestRankingIsCurrentlyChartIndependent:
    """THE guard, and the uncomfortable one.

    With every modulation weight at zero the ranking cannot vary by chart. This test asserts that
    state deliberately so it is visible rather than implicit. It is a record of what was measured,
    NOT a design goal: if chart-specific salience is ever demonstrated, this test should fail and
    should be rewritten to assert the opposite.
    """

    def test_unlike_charts_rank_identically(self, reports):
        orders = {name: tuple(rank_houses(r)) for name, r in reports.items()}
        assert len(set(orders.values())) == 1, (
            f"rankings now differ by chart: {orders}. If a weight was raised on measured "
            f"evidence, update test_the_prior_is_the_whole_score too and record the holdout "
            f"numbers; if not, this is an accidental behaviour change"
        )
        assert next(iter(orders.values())) == _DOCTRINAL_ORDER

    def test_scores_are_the_prior_itself(self, reports):
        """Not merely the same ORDER across charts — the same numbers, equal to the prior.

        Ordering could coincide while the arithmetic drifted. Pinning the values catches a
        modulation term that fires but is too small to reorder anything.
        """
        for name, r in reports.items():
            scored = house_salience(r)
            for h in range(1, 13):
                assert scored[h].score == pytest.approx(DOCTRINAL_PRIOR[h]), (
                    f"{name} H{h}: score {scored[h].score} != prior {DOCTRINAL_PRIOR[h]} — a "
                    f"modulation term is contributing"
                )

    def test_all_twelve_houses_come_back(self, reports):
        for name, r in reports.items():
            scored = house_salience(r)
            assert sorted(scored) == list(range(1, 13)), f"{name} lost a house"


class TestWhyStatesOnlyReasonsThatRanked:
    """`why` explains a house's POSITION; `notable` describes the house.

    Conflating them is how a report ends up telling a reader that a house came first because its
    readings are rare, when rarity contributed exactly nothing to its position. The observations
    are worth keeping — they are chart-specific and true — so nothing is removed; they move to a
    field whose name does not claim causation.
    """

    #: phrase -> the weight that would have to be live for it to have moved the score
    _ATTRIBUTABLE = {
        "unusually rare": "W_SURPRISAL",
        "population median": "W_EXTREMITY",
        "chart-specific factors": "W_CENTRALITY",
        "fired yoga": "W_YOGA",
    }

    def test_why_never_credits_a_zero_weighted_term(self, reports):
        live = {"W_SURPRISAL": W_SURPRISAL, "W_EXTREMITY": W_EXTREMITY,
                "W_CENTRALITY": W_CENTRALITY, "W_YOGA": W_YOGA}
        for name, r in reports.items():
            for house, s in house_salience(r).items():
                for line in s.why:
                    for phrase, weight_name in self._ATTRIBUTABLE.items():
                        if phrase in line:
                            assert live[weight_name] != 0.0, (
                                f"{name} H{house}: why says {line!r}, but {weight_name} is 0.0 "
                                f"— that observation did not affect the ranking. It belongs in "
                                f"`notable`, not `why`"
                            )

    def test_the_lagna_says_why_it_leads(self, reports):
        """The prior IS the ranking, so the Lagna's reason is the one honest `why` today."""
        for name, r in reports.items():
            assert any("Lagna" in line for line in house_salience(r)[1].why), name

    def test_observations_are_kept_not_dropped(self, reports):
        """Append-only: the chart-specific observations survive, under an honest name."""
        seen = [line
                for r in reports.values()
                for s in house_salience(r).values()
                for line in s.notable]
        assert seen, ("no chart-specific observations survived anywhere — they were dropped "
                      "rather than moved, which the append-only directive forbids")
