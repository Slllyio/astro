"""Firing-coverage audit on the Mainpuri chart (HOUSE_SCHEME_AUDIT increment 21).

The default judgment only makes a rule a candidate if its `domain` tag equals the house's
single `HOUSE_DOMAIN` mapping (or it lives in that house's HTJAH chapter). Two large domains
— `general` and `mind_character` — map to NO house, so hundreds of applicable HPA /
three_hundred sutras (present yogas, avasthas/balas, functional-role, planet-in-sign
character) could never fire. `NATAL_FIRING_WIDEN` closes that gap: every in-natal-scope rule
that references a house becomes a candidate for that house, and chart-global rules (no house
anchor) fire once via `judge_chart_doctrine`.

This test pins, with the flag ON:
  1. COVERAGE — every applicable natal-scope rule surfaces somewhere;
  2. EXCLUSION-BY-DESIGN — the widening adds no out-of-scope rule_type (electional/prasna/
     dasha_timing/transit/definition/method), whose antecedents being true on a birth chart
     is coincidental;
  3. DEDUP — each rule surfaces exactly once (chart_global is disjoint from the house union).
The default path stays byte-identical (the flag defaults OFF); this test flips it via
monkeypatch, so coverage is proven without changing default output.
"""
import pytest

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.domains import house_judgment as HJ
from app.medini.doctrine.domains import natal_scope as NS
from app.medini.doctrine.engine.evaluate import evaluate_rule
from app.medini.doctrine.engine.predicates import EvalContext

# Mainpuri chart (same fixture as test_house_judgment): Scorpio lagna, lord Mars in Virgo/11th.
MAINPURI = dict(
    positions={"Sun": 176.562, "Moon": 319.0817, "Mars": 172.4476,
               "Mercury": 158.7869, "Jupiter": 78.1407, "Venus": 221.6724,
               "Saturn": 255.8022, "Rahu": 300.4694, "Ketu": 120.4694},
    lagna=225.5089, jd=2447811.6888)

_DASHA = {"md": "Mercury", "ad": "Mercury"}

# Out-of-scope rule types — must never be ADDED by the widening (the existing domain path may
# already surface some; the audit only forbids the widening from introducing new ones).
_OUT_OF_SCOPE = {"electional", "prasna", "dasha_timing", "transit", "definition", "method"}


@pytest.fixture(scope="module")
def mainpuri():
    return rc.from_printed_positions(
        MAINPURI["positions"], MAINPURI["lagna"], birth_jd=MAINPURI["jd"])


@pytest.fixture(scope="module")
def rules_by_id():
    return {r["id"]: r for rules in HJ.load_compendium().values() for r in rules}


def _applicable(chart, rules_by_id):
    """Every executable rule whose antecedent is TRUE on the chart (static: no timing gate)."""
    ctx = EvalContext(chart=chart)
    out = {}
    for rid, r in rules_by_id.items():
        if r["antecedent"] is None:
            continue
        if evaluate_rule(r, ctx, mode="static").fired:
            out[rid] = r
    return out


def _surfaced(chart_doctrine):
    house = set().union(*(j.fired_rule_ids for j in chart_doctrine.houses.values()))
    chart_global = {g.rule_id for g in chart_doctrine.chart_global}
    return house, chart_global


def test_every_applicable_natal_sutra_fires(monkeypatch, mainpuri, rules_by_id):
    applicable = _applicable(mainpuri, rules_by_id)
    # A yoga whose documented bhanga (cancellation) holds is a LEGITIMATE non-firing
    # exception (increment 23: Kemadruma is cancelled here by Venus in a kendra), so it is
    # not part of the "must fire" set.
    natal = {i for i, r in applicable.items()
             if NS.in_natal_scope(r) and not HJ._is_cancelled_yoga(r, mainpuri)}

    monkeypatch.setattr(HJ, "NATAL_FIRING_WIDEN", True)
    house, chart_global = _surfaced(HJ.judge_chart_doctrine(mainpuri, dasha=_DASHA))
    surfaced = house | chart_global

    missing = natal - surfaced
    assert not missing, f"applicable natal sutras that never fire: {sorted(missing)}"
    # A material gap was closed: many more natal rules surface than the OFF domain-slice.
    assert len(natal) >= 100


def test_widening_adds_no_out_of_scope(monkeypatch, mainpuri, rules_by_id):
    # Pre-widening (flag OFF) surfaced set — the existing domain-slice path.
    monkeypatch.setattr(HJ, "NATAL_FIRING_WIDEN", False)
    off = set().union(*(j.fired_rule_ids
                        for j in HJ.judge_chart_doctrine(mainpuri, dasha=_DASHA).houses.values()))
    monkeypatch.setattr(HJ, "NATAL_FIRING_WIDEN", True)
    house, chart_global = _surfaced(HJ.judge_chart_doctrine(mainpuri, dasha=_DASHA))
    added = (house | chart_global) - off
    leaked = [i for i in added if rules_by_id[i]["rule_type"] in _OUT_OF_SCOPE]
    assert not leaked, f"widening introduced out-of-scope rule_types: {sorted(leaked)}"


def test_each_rule_surfaces_once(monkeypatch, mainpuri):
    monkeypatch.setattr(HJ, "NATAL_FIRING_WIDEN", True)
    cd = HJ.judge_chart_doctrine(mainpuri, dasha=_DASHA)
    house, chart_global = _surfaced(cd)
    cg_ids = [g.rule_id for g in cd.chart_global]
    # chart-global rules are unique and disjoint from every house verdict.
    assert len(cg_ids) == len(set(cg_ids)), "duplicate chart-global rule ids"
    assert not (chart_global & house), "a chart-global rule also appears in a house verdict"


def test_no_out_of_scope_rule_fires_on_natal_chart(mainpuri, rules_by_id):
    # Increment 22: horary / electional / past-life rules whose antecedents are only
    # coincidentally true on a natal chart (Prasna Marga speculation & lost-property,
    # Muhurtha election, 'loka' after-death definitions) must NOT surface in a birth-chart
    # judgment. Timing rules (dasha/transit) are exempt — the timing sub-verdict uses them.
    cd = HJ.judge_chart_doctrine(mainpuri, dasha=_DASHA)
    surfaced = set().union(*(j.fired_rule_ids for j in cd.houses.values()))
    surfaced |= {g.rule_id for g in cd.chart_global}
    HARD_OUT = {"electional", "prasna", "definition"}
    leaked = sorted(i for i in surfaced if rules_by_id[i]["rule_type"] in HARD_OUT)
    assert not leaked, f"out-of-scope rules fired on a natal chart: {leaked}"


def test_kemadruma_bhanga_suppresses_the_yoga(mainpuri):
    # Increment 23: on Mainpuri, Venus in the 1st is a kendra from both the Lagna and the
    # Moon, so Kemadruma-bhanga holds and the yoga must not surface (Raman: it 'ceases to
    # exist'). Reading-only suppression; grades are guarded by the drift-guard suite.
    cd = HJ.judge_chart_doctrine(mainpuri, dasha=_DASHA)
    fired = set().union(*(j.fired_rule_ids for j in cd.houses.values()))
    fired |= {g.rule_id for g in cd.chart_global}
    assert not [i for i in fired if "kemadruma" in i], "Kemadruma fired despite its bhanga"


def test_natal_firing_is_on_and_grade_safe():
    # Increment 21 landed with the flag ON: firing coverage is the default. It is grade-safe
    # by construction — the widened candidates surface for READING (buckets/combinations/
    # chart_global) but never feed the numeric grade (only the original domain+chapter
    # `scoring_ids` reach `sutra_fired`). The drift-guard + live-anchor ledger prove the
    # verdicts are byte-identical; this pins the coverage default so it can't silently revert.
    assert HJ.NATAL_FIRING_WIDEN is True
