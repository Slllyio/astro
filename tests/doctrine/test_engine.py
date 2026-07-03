"""P3 engine: predicate leaves across frames, combinators, escape hatch,
evaluation semantics, and the committed seed evaluating end to end."""
import json
from pathlib import Path

import pytest

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.compendium import load_book
from app.medini.doctrine.engine import escape_hatch
from app.medini.doctrine.engine.evaluate import (
    compile_rule,
    evaluate_rule,
    evaluate_rules,
)
from app.medini.doctrine.engine.predicates import (
    EvalContext,
    MissingInput,
    UnknownOp,
    evaluate_predicate,
    validate_predicate,
)

# Synthetic chart, hand-checkable. Lagna Virgo (6). Houses from Virgo:
# Sun Gemini29 -> 10th; Moon Scorpio5 -> 3rd; Mars Aries5 -> 8th;
# Mercury/Jupiter Cancer -> 11th; Venus Taurus15 -> 9th;
# Saturn Capricorn10 -> 5th; Rahu Cancer28 -> 11th; Ketu Capricorn28 -> 5th.
LONS = {
    "Sun": 89.0, "Moon": 215.0, "Mars": 5.0, "Mercury": 95.0,
    "Jupiter": 100.0, "Venus": 45.0, "Saturn": 280.0,
    "Rahu": 118.0, "Ketu": 298.0,
}
LAGNA = 155.0


@pytest.fixture(scope="module")
def ctx():
    chart = rc.from_printed_positions(LONS, LAGNA, birth_jd=2448088.0)
    return EvalContext(chart=chart)


def ev(node, ctx):
    validate_predicate(node)
    return evaluate_predicate(node, ctx)


class TestLeaves:
    def test_lagna_sign_is(self, ctx):
        assert ev({"op": "lagna_sign_is", "sign": "virgo"}, ctx)
        assert not ev({"op": "lagna_sign_is", "sign": 1}, ctx)

    def test_planet_in_house_frames(self, ctx):
        assert ev({"op": "planet_in_house", "planet": "Sun", "house": 10}, ctx)
        # from the Moon (Scorpio): Sun in Gemini = 8th from Moon
        assert ev({"op": "planet_in_house", "planet": "Sun", "house": 8,
                   "frame": "moon"}, ctx)
        # group + planet-class specs
        assert ev({"op": "planet_in_house", "planet": "malefic",
                   "house": "dusthana"}, ctx)  # Mars in 8
        assert ev({"op": "planet_in_house", "planet": "Saturn",
                   "house": [4, 5, 6]}, ctx)

    def test_planet_in_sign_and_conjunct(self, ctx):
        assert ev({"op": "planet_in_sign", "planet": "Mars", "sign": "aries"}, ctx)
        assert ev({"op": "planets_conjunct",
                   "planets": ["Mercury", "Jupiter"]}, ctx)
        assert not ev({"op": "planets_conjunct",
                       "planets": ["Mercury", "Venus"]}, ctx)

    def test_lordships(self, ctx):
        # Virgo lagna: lord of 8 (Aries) = Mars, Mars in 8th
        assert ev({"op": "lord_of_house_in_house", "of_house": 8,
                   "in_house": 8}, ctx)
        assert ev({"op": "planet_is_lord_of", "planet": "Mercury",
                   "house": 1}, ctx)

    def test_aspects(self, ctx):
        # Saturn in 5th: 3rd/7th/10th aspects -> 7, 11, 2
        assert ev({"op": "planet_aspects_house", "planet": "Saturn",
                   "house": 11}, ctx)
        # Mercury/Jupiter/Rahu in 11 — Saturn aspects them
        assert ev({"op": "planet_aspects_planet", "planet": "Saturn",
                   "target": "Jupiter"}, ctx)
        assert not ev({"op": "planet_aspects_planet", "planet": "Saturn",
                       "target": "Sun"}, ctx)

    def test_vargas(self, ctx):
        d9 = ctx.chart.varga_signs["Moon"][9]
        assert ev({"op": "varga_sign_is", "planet": "Moon", "divisor": 9,
                   "sign": d9}, ctx)
        assert ev({"op": "varga_lord_is", "planet": "Moon", "divisor": 3,
                   "lord": "Mars"}, ctx)  # Scorpio 5 -> 1st drekkana Scorpio

    def test_dignity(self, ctx):
        assert ev({"op": "exalted", "planet": "Jupiter"}, ctx)  # Cancer
        assert ev({"op": "own_sign", "planet": "Mars"}, ctx)  # Aries
        assert not ev({"op": "debilitated", "planet": "Venus"}, ctx)  # Taurus own
        with pytest.raises(MissingInput):
            ev({"op": "dignity_is", "planet": "Rahu", "state": "own"}, ctx)

    def test_strength_and_states(self, ctx):
        assert isinstance(ev({"op": "strong", "planet": "Venus"}, ctx), bool)
        assert ev({"op": "strength_gte", "planet": "Venus", "value": 0.0}, ctx)
        assert isinstance(ev({"op": "combust", "planet": "Mercury"}, ctx), bool)
        assert ev({"op": "waxing_moon"}, ctx)  # Moon 215 - Sun 89 = 126 < 180
        with pytest.raises(MissingInput):
            ev({"op": "retrograde", "planet": "Saturn"}, ctx)

    def test_ashtakavarga_ops(self, ctx):
        assert ev({"op": "av_bindus_gte", "planet": "Sun", "value": 0}, ctx)
        assert ev({"op": "sav_bindus_gte", "house": 1, "value": 10}, ctx)
        assert ev({"op": "reduced_av_total_cmp", "planet": "Sun",
                   "cmp": "lte", "value": 48}, ctx)

    def test_tara_class(self, ctx):
        assert ev({"op": "tara_class", "planet": "Moon", "tara": 1}, ctx)
        assert isinstance(
            ev({"op": "tara_class", "planet": "Saturn", "tara": [3, 5, 7]}, ctx),
            bool)

    def test_dasha_requires_context(self, ctx):
        node = {"op": "dasha_lord_is", "planet": "Saturn"}
        with pytest.raises(MissingInput):
            ev(node, ctx)
        timed = EvalContext(chart=ctx.chart, dasha={"md": "Saturn"})
        assert evaluate_predicate(node, timed)

    def test_jaimini_and_points(self, ctx):
        assert ev({"op": "karaka_is", "planet": "Sun"}, ctx)  # Sun 29° in sign
        assert isinstance(ev({"op": "occupies_khara", "planet": "Mars"}, ctx), bool)
        assert isinstance(ev({"op": "occupies_chidra", "planet": "Venus"}, ctx), bool)

    def test_yoga_present(self, ctx):
        assert isinstance(ev({"op": "yoga_present", "yoga": "adhi"}, ctx), bool)


class TestCombinators:
    def test_all_any_not_count(self, ctx):
        t = {"op": "lagna_sign_is", "sign": "virgo"}
        f = {"op": "lagna_sign_is", "sign": "aries"}
        assert ev({"op": "all", "args": [t, t]}, ctx)
        assert not ev({"op": "all", "args": [t, f]}, ctx)
        assert ev({"op": "any", "args": [f, t]}, ctx)
        assert ev({"op": "not", "arg": f}, ctx)
        assert ev({"op": "count_gte", "n": 2, "args": [t, f, t]}, ctx)
        assert not ev({"op": "count_gte", "n": 3, "args": [t, f, t]}, ctx)

    def test_unknown_op_fails_at_load(self):
        with pytest.raises(UnknownOp):
            validate_predicate({"op": "planet_feels_lucky", "planet": "Venus"})
        with pytest.raises(UnknownOp):
            validate_predicate({"op": "all", "args": []})
        with pytest.raises(UnknownOp):
            validate_predicate({"op": "all", "args": [{"op": "bogus"}]})

    def test_validate_returns_ops_used(self):
        used = validate_predicate({"op": "all", "args": [
            {"op": "lagna_sign_is", "sign": 1},
            {"op": "not", "arg": {"op": "combust", "planet": "Venus"}},
        ]})
        assert {"all", "not", "lagna_sign_is", "combust"} == used


class TestEscapeHatch:
    def test_resolve_and_run(self, ctx):
        impl = escape_hatch.resolve("impl:python:hpa.balarishta_screen")
        assert "HPA Ch. XIV" in impl.citation
        assert isinstance(impl.fn(ctx), bool)

    def test_unregistered_fails(self):
        with pytest.raises(KeyError):
            escape_hatch.resolve("impl:python:nope.never")

    def test_registry_guardrails(self):
        with pytest.raises(TypeError):
            escape_hatch.register("x.bad_sig", "cite")(lambda chart, extra: True)
        with pytest.raises(ValueError):
            escape_hatch.register("x.no_cite", "  ")(lambda ctx: True)
        with pytest.raises(ValueError):
            escape_hatch.register("hpa.balarishta_screen", "dup")(lambda ctx: True)

    def test_every_registered_impl_has_citation_and_signature(self):
        for impl in escape_hatch.registered().values():
            assert impl.citation.strip()
            import inspect
            assert list(inspect.signature(impl.fn).parameters) == ["ctx"]


def _rule(antecedent, timing=None, rule_id="raman.hpa.xvii.aries_key_planets"):
    return {
        "id": rule_id,
        "antecedent": antecedent,
        "consequent": {"polarity": "neutral", "text": "t", "timing": timing},
    }


class TestEvaluateRule:
    def test_static_fire(self, ctx):
        out = evaluate_rule(_rule({"op": "lagna_sign_is", "sign": "virgo"}), ctx)
        assert out.evaluable and out.fired and out.active

    def test_missing_input_is_not_false(self, ctx):
        out = evaluate_rule(_rule({"op": "dasha_lord_is", "planet": "Saturn"}), ctx)
        assert not out.evaluable and not out.fired and out.missing

    def test_timeline_gates_on_timing(self, ctx):
        rule = _rule({"op": "lagna_sign_is", "sign": "virgo"},
                     timing={"mode": "dasha", "of": "lord_of_8"})
        timed = EvalContext(chart=ctx.chart, dasha={"md": "Mars"})  # 8L Virgo=Mars
        assert evaluate_rule(rule, timed, mode="timeline").fired
        wrong = EvalContext(chart=ctx.chart, dasha={"md": "Venus"})
        assert not evaluate_rule(rule, wrong, mode="timeline").fired
        # static mode reports the structural potential, ignoring timing
        assert evaluate_rule(rule, ctx, mode="static").fired

    def test_shadow_mode_under_profile(self, ctx, tmp_path):
        conflicts = tmp_path / "conflicts.jsonl"
        conflicts.write_text(json.dumps({
            "conflict_id": "c1",
            "rule_ids": ["raman.hpa.xvii.aries_key_planets",
                         "raman.htjah_vol1.i.aries_alt"],
            "dimension": "antecedent_logic",
            "resolution": {"active_rule_id": "raman.htjah_vol1.i.aries_alt",
                           "scope": "raman_default"},
            "precedence_basis": "test",
            "rationale": "test",
        }) + "\n")
        rules = [_rule({"op": "lagna_sign_is", "sign": "virgo"})]
        outs = evaluate_rules(rules, ctx, conflicts_path=conflicts)
        assert outs[0].fired and not outs[0].active and outs[0].shadow_of == "c1"

    def test_compile_rejects_bad_antecedents(self):
        with pytest.raises(UnknownOp):
            compile_rule(_rule({"op": "bogus"}))
        with pytest.raises(KeyError):
            compile_rule(_rule("impl:python:not.registered"))
        compile_rule(_rule(None))  # manual rules compile as no-ops


class TestSeedEndToEnd:
    def test_committed_seed_compiles_and_evaluates(self, ctx):
        rules = load_book(Path("data/raman_doctrine/compendium/hpa.jsonl"))
        for rule in rules:
            compile_rule(rule)
        outs = evaluate_rules(rules, ctx)
        fired = [o.rule_id for o in outs if o.fired]
        # Virgo lagna chart: exactly the virgo key-planet rule fires
        assert fired == ["raman.hpa.xvii.virgo_key_planets"]
        assert all(o.evaluable for o in outs)
