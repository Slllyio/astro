"""Fidelity gate 1 — the compendium's encoded antecedents must reproduce
Raman's stated mechanisms on golden charts built from his prose."""
import json
from pathlib import Path

import pytest

from app.medini.doctrine.compendium import load_compendium
from app.medini.doctrine.engine.evaluate import compile_rule, evaluate_rule
from app.medini.doctrine.engine.predicates import EvalContext
from app.medini.doctrine.fidelity import golden_registry as gr
from app.medini.doctrine.fidelity.score import (
    mechanism_jaccard,
    polarity_agreement,
    score_mechanism,
)


@pytest.fixture(scope="module")
def rules_by_id():
    books = load_compendium()
    return {r["id"]: r for rules in books.values() for r in rules}


class TestConstructedFidelity:
    def test_every_targeted_rule_exists_and_compiles(self, rules_by_id):
        for case in gr.CONSTRUCTED:
            assert case.rule_id in rules_by_id, f"unknown rule {case.rule_id}"
            compile_rule(rules_by_id[case.rule_id])

    def test_mechanism_precision_recall_perfect(self, rules_by_id):
        """Each golden chart is built from the rule's prose; the encoded
        antecedent must fire exactly when the prose is satisfied."""
        outcomes = []
        polarity_pairs = []
        misfires = []
        for case in gr.CONSTRUCTED:
            rule = rules_by_id[case.rule_id]
            ctx = EvalContext(chart=case.chart())
            outcome = evaluate_rule(rule, ctx)
            assert outcome.evaluable, f"{case.label}: not evaluable ({outcome.missing})"
            outcomes.append((case.expected_fire, outcome.fired))
            if outcome.fired != case.expected_fire:
                misfires.append(f"{case.rule_id} [{case.label}]: "
                                f"expected {case.expected_fire}, got {outcome.fired}")
            if outcome.fired and case.verdict_polarity:
                polarity_pairs.append(
                    (rule["consequent"]["polarity"], case.verdict_polarity))

        pr = score_mechanism(outcomes)
        assert not misfires, "mechanism divergences:\n" + "\n".join(misfires)
        assert pr.precision == 1.0 and pr.recall == 1.0
        # polarity of a firing rule must agree with Raman's verdict for the chart
        assert polarity_agreement(polarity_pairs) == 1.0

    def test_golden_cases_json_matches_registry(self, tmp_path):
        # round-trip: the committed JSON must reproduce the in-code registry
        gr.save_constructed(list(gr.CONSTRUCTED), tmp_path / "g.json")
        reloaded = gr.load_constructed(tmp_path / "g.json")
        assert reloaded == list(gr.CONSTRUCTED)
        committed = gr.load_constructed()
        assert committed == list(gr.CONSTRUCTED)


class TestScoreMetrics:
    def test_precision_recall_arithmetic(self):
        pr = score_mechanism([(True, True), (True, False), (False, True),
                              (False, False)])
        assert (pr.tp, pr.fn, pr.fp, pr.tn) == (1, 1, 1, 1)
        assert pr.precision == 0.5 and pr.recall == 0.5 and pr.accuracy == 0.5

    def test_polarity_neutral_is_compatible(self):
        assert polarity_agreement([("neutral", "favorable"),
                                   ("mixed", "unfavorable"),
                                   ("favorable", "favorable")]) == 1.0
        assert polarity_agreement([("favorable", "unfavorable")]) == 0.0

    def test_jaccard(self):
        assert mechanism_jaccard(set(), set()) == 1.0
        assert mechanism_jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)
        assert mechanism_jaccard({"a"}, {"a"}) == 1.0


class TestPrintedChartSmoke:
    """Raman's own printed horoscopes must evaluate cleanly through the whole
    compendium (no interpreter errors), and some rules must fire."""

    def test_printed_charts_evaluate_without_error(self):
        from app.medini.ml.raman_saab.fidelity import GOLDEN_CASES

        books = load_compendium()
        rules = [r for rs in books.values() for r in rs
                 if r["antecedent"] is not None]
        cases = [c for c in GOLDEN_CASES if c.positions and c.lagna_lon]
        assert cases, "expected at least one printed chart with positions"
        for case in cases[:5]:
            lons = dict(case.positions)
            ctx = EvalContext(chart=gr.from_positions(
                lons, case.lagna_lon, birth_jd=2451545.0, ayanamsa="raman"))
            fired = 0
            for rule in rules:
                out = evaluate_rule(rule, ctx)  # must not raise
                fired += bool(out.fired)
            assert fired > 0, f"{case.name}: no compendium rule fired"
