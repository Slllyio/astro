"""Unit pins for the synthesis_v2 gated-override scorer (parallel to the live engine).

Each pin builds a FactorVerdict directly (no chart needed) so the gate/guard behaviour is isolated.
The three-axis held-out numbers are pinned separately by test_synthesis_v2_result.
"""
from __future__ import annotations

from app.medini.doctrine.domains import synthesis_v2 as S2
from app.medini.doctrine.domains.house_judgment import (
    Finding, FactorVerdict, _cap_positive, _verdict_label,
)

_IDX = {lab: i for i, lab in enumerate(S2.VERDICT_SCALE)}


def _fv(findings, *, nav_score=0.0):
    """A FactorVerdict whose scores match the engine's own arithmetic over `findings`
    (Rāśi frame; optional pre-computed Navāṁśa score)."""
    rasi = [f for f in findings if f.frame in ("Rasi", "both")]
    pos = sum(f.delta for f in rasi if f.delta > 0)
    neg = sum(f.delta for f in rasi if f.delta < 0)
    rasi_score = round(_cap_positive(pos) + neg, 3)
    score = round((rasi_score + 0.3 * nav_score) if nav_score else rasi_score, 3)
    return FactorVerdict("Lord", "test", _verdict_label(score), score,
                         tuple(findings), rasi_score=rasi_score, navamsa_score=nav_score)


def _grade(fv):
    return S2.label(S2.grade_factor(fv)[0])


def test_config_is_the_landing_ablation():
    # A + B are the two doctrine gates that break the ceiling; P/C are off (documented negatives).
    assert S2.GATE_A and S2.GATE_B
    assert not S2.GATE_P and not S2.GATE_C


def test_base_reproduces_engine_when_no_gate_fires():
    # a benign factor (mild net-positive, no besiegement, shallow negatives) → v2 == engine label
    fv = _fv([Finding("placed in the 4th (kendra/trikona)", 1.2, "Rasi", "placement"),
              Finding("aspected by Mercury (benefic)", 0.7, "Rasi", "aspect"),
              Finding("conjunct Saturn (malefic)", -0.7, "Rasi", "conjunction")])
    assert _grade(fv) == _verdict_label(fv.score)


def test_gate_A_besiegement_caps_at_weak():
    # papakartari destroys the factor regardless of a strong positional/dignity base
    fv = _fv([Finding("occupant in own sign", 1.2, "Rasi", "dignity"),
              Finding("placed in the 4th (kendra/trikona)", 1.2, "Rasi", "placement"),
              Finding("hemmed between malefics (Papakartari)", -1.0, "Rasi", "kartari")])
    assert _IDX[_verdict_label(fv.score)] > S2.WEAK          # base is above "weak"
    assert _grade(fv) == "weak"                              # …but Gate A caps it


def test_gate_B_deep_affliction_to_afflicted():
    # sum of Rāśi negatives ≤ −2.45 → afflicted, whatever the positive credit
    fv = _fv([Finding("exalted", 1.6, "Rasi", "dignity"),
              Finding("conjunct Sun (malefic)", -0.85, "Rasi", "conjunction"),
              Finding("aspected by Saturn (malefic)", -0.85, "Rasi", "aspect"),
              Finding("aspected by Mars (malefic)", -0.85, "Rasi", "aspect")])
    assert _grade(fv) == "afflicted"


def test_gate_B_moderate_affliction_to_weak():
    # −2.45 < sum_neg ≤ −1.22 → weak (the A2 tree's load-bearing split)
    fv = _fv([Finding("exalted", 1.6, "Rasi", "dignity"),
              Finding("conjunct Saturn (malefic)", -0.7, "Rasi", "conjunction"),
              Finding("aspected by Rahu (malefic)", -0.6, "Rasi", "aspect")])
    assert _IDX[_verdict_label(fv.score)] > S2.WEAK          # base above weak (exaltation credit)
    assert _grade(fv) == "weak"


def test_collinearity_guard_dedups_combustion_and_sun_conjunction():
    # combustion is the tight-orb case of Sun-proximity: counted once, not stacked. Double-counted
    # (−0.9 + −0.9 = −1.8) the negatives trip Gate B → "weak"; de-duped (−0.9) they don't, and the
    # exaltation credit survives → "fairly good". The guarded pair must equal the single-count case.
    exalted = Finding("exalted", 1.6, "Rasi", "dignity")
    combust = Finding("Mars combust (astangata, degree-orb)", -0.9, "Rasi", "combustion")
    sun_conj = Finding("conjunct Sun (malefic)", -0.9, "Rasi", "conjunction")
    both = _fv([exalted, combust, sun_conj])
    only = _fv([exalted, combust])
    assert _grade(both) == _grade(only) == "fairly good"


def test_dignity_floor_is_off_by_default():
    # With C off, an exalted-but-deeply-afflicted factor is NOT rescued by a dignity floor — it stays
    # afflicted. (This is the documented negative: the floor lifts the anchor 1→2 but costs held-out.)
    fv = _fv([Finding("exalted", 1.6, "Rasi", "dignity"),
              Finding("conjunct Sun (malefic)", -0.85, "Rasi", "conjunction"),
              Finding("aspected by Saturn (malefic)", -0.85, "Rasi", "aspect"),
              Finding("aspected by Mars (malefic)", -0.85, "Rasi", "aspect")])
    assert _grade(fv) == "afflicted"                       # C off → no floor rescue
    S2.GATE_C = True
    try:
        assert S2.label(S2.grade_factor(fv)[0]) == "moderately good"   # C on would floor to index 3
    finally:
        S2.GATE_C = False


def test_synthesis_v2_result_beats_live_engine():
    """Ratchet: synthesis_v2 (A+B) must keep beating the live engine on both big held-out axes and
    hold the anchor at parity. Pinned floors below the measured 64.2% / 62.5% / 1-of-8."""
    from app.medini.doctrine.validation import synthesis_v2_validate as V
    held = V.run_heldout()
    nh = V.run_nh()
    anchor = V.run_anchor()
    assert held["within1_pct"] >= 62.0, held["within1_pct"]      # measured 64.2 (live 54.7)
    assert nh["within1_pct"] >= 60.0, nh["within1_pct"]          # measured 62.5 (live 53.1)
    assert anchor["within1"] >= 1, anchor["within1"]             # parity with live 1/8 (no regression)


def test_grow2_corpus_integrity():
    """nh_strength_grow2 pins: 18 rows, every key degree-usable in the registry, every phrase
    mappable by the unchanged pre-registered verdict map, every karaka row on the default karaka."""
    import json
    from pathlib import Path
    from app.medini.doctrine.validation import worked_chart_validate as W
    from app.medini.ml.raman_saab.golden_registry import load_registry
    corp = json.loads((Path(__file__).resolve().parents[2] /
                       "docs/raman_doctrine/validation/corpora/nh_strength_grow2.json").read_text())
    rows = corp["rows"]
    assert len(rows) == 18
    cases = {c.key: c for c in load_registry()}
    patterns = W.load_verdict_map()
    for r in rows:
        assert r["key"] in cases and cases[r["key"]].positions, r["key"]
        assert r["factor"] in ("bhava", "lord", "karaka"), r
        assert 1 <= int(r["house"]) <= 12, r
        assert W.map_verdict(r["phrase"], patterns) is not None, r["phrase"]


def test_synthesis_v2_enlarged_degree_pool():
    """Ratchet on the ENLARGED degree pool (N=50, grow2 included): v2 must stay >= 50% within-one
    and keep a real lead over the live engine measured on the same rows (measured 52.0 vs 44.0)."""
    from app.medini.doctrine.validation import synthesis_v2_validate as V
    s = V.run_nh(V._NH_ALL)
    assert s["n"] == 50, s["n"]
    assert s["within1_pct"] >= 50.0, s["within1_pct"]
    assert s["within1_pct"] - s["live_within1_pct"] >= 4.0, (
        s["within1_pct"], s["live_within1_pct"])
