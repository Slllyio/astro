"""The validated 8th-bhāva longevity signal is surfaced in the chart grounding.

Held-out finding (REPORT_longevity.md): only the 8th-BHĀVA fortification tracks Raman's
longevity class (Spearman ρ = +0.52); the 8th-lord/Āyushkāraka do not. These pin that the
production reading exposes exactly that predictor -- graded, with its honest confidence, and
only when the 8th house is actually judged.
"""
import json
from pathlib import Path

from app.medini.doctrine.domains.house_judgment import judge_house_doctrine
from app.medini.doctrine.interpret import build_chart_grounding, longevity_indication
from app.medini.doctrine.validation import reconstruct as R

_CORPUS = Path("docs/raman_doctrine/validation/corpora/unseen_scoreable.json")


def _chart_52():
    rec = next(c for c in json.loads(_CORPUS.read_text())["charts"] if c["chart_no"] == 52)
    return R.chart_from_raman(rec["rasi"], rec["navamsa"],
                              rec["lagna_rasi"], rec["lagna_navamsa"])


def test_longevity_indication_uses_the_validated_8th_bhava_predictor():
    chart = _chart_52()
    js = [judge_house_doctrine(chart, h) for h in range(1, 13)]
    li = longevity_indication(js)
    # exactly the validated field: the 8th-house judgment's bhāva fortification score
    j8 = next(j for j in js if j.house == 8)
    assert li["eighth_bhava_score"] == round(j8.lagna_verdict.score, 2)
    assert li["indication"] in {"above-average life support", "average life support",
                                "below-average life support"}
    # honest framing: directional, not deterministic
    assert "NOT a deterministic" in li["confidence"]


def test_grounding_includes_longevity_only_when_eighth_is_judged():
    chart = _chart_52()
    js = [judge_house_doctrine(chart, h) for h in range(1, 13)]
    assert "longevity" in build_chart_grounding(js)
    assert "longevity" not in build_chart_grounding([j for j in js if j.house != 8])


def test_longevity_indication_is_none_without_eighth():
    chart = _chart_52()
    assert longevity_indication([judge_house_doctrine(chart, 1)]) is None
