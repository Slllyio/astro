"""H1 Tara-Bala rules (H1.C.35 / H1.C.36) are ACTIVATED, not descriptive.

Raman (HTJAH-I:1142-1146) grades the lagna lord by its Tara from the natal Moon's Janma
nakshatra: a strong lagna lord in the 3rd/5th/7th (vipat/pratyak/naidhana) constellation has its
favourable results *lessened* (#36); a weak one there has its evil *intensified* (#35). These
were inert (condition=None) until the TaraOf + LordHasDignity predicates landed.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets.house_01_lagna import combinations_misc


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def _rule(rid: str):
    return next(r for r in combinations_misc.RULES if r.id == rid)


def test_both_tara_rules_are_evaluable_not_descriptive():
    """Neither Tara rule may regress to an inert descriptive stub."""
    for rid in ("H1.C.35", "H1.C.36"):
        r = _rule(rid)
        assert r.kind == "evaluable", f"{rid} must be evaluable"
        assert r.condition is not None, f"{rid} must carry a condition"


def test_h1_c36_fires_for_strong_lagna_lord_in_naidhana_tara():
    """Aries lagna: Mars (lagna lord) exalted in Capricorn AND in the 7th (naidhana) tara from the
    Moon -> favourable indications lessened (HTJAH-I:1145)."""
    chart = _chart({"Moon": 85.0, "Mars": 285.0})   # Moon nak 7; Mars nak 22 -> tara 7
    assert _rule("H1.C.36").condition.evaluate(C.EvalContext(chart)) is True
    assert _rule("H1.C.35").condition.evaluate(C.EvalContext(chart)) is False


def test_h1_c35_fires_for_uncancelled_weak_lagna_lord_in_vipat_tara():
    """Libra lagna: Venus (lagna lord) debilitated in Virgo, its debilitation UN-cancelled
    (dispositor Mercury absent; Venus not navamsa-exalted), AND in the 3rd (vipat) tara from the
    Moon -> evil indications intensified (HTJAH-I:1142)."""
    chart = _chart({"Venus": 155.0, "Moon": 125.0}, asc_lon=180.0)  # Venus nak12, Moon nak10 -> tara 3
    assert _rule("H1.C.35").condition.evaluate(C.EvalContext(chart)) is True
    assert _rule("H1.C.36").condition.evaluate(C.EvalContext(chart)) is False


def test_h1_c35_does_not_fire_when_debilitation_is_cancelled():
    """Aries lagna: Mars (lagna lord) debilitated in Cancer but its debilitation is cancelled
    (the Moon, Cancer's dispositor, sits in a kendra from itself) -> a Neecha-Bhanga'd lord is not
    truly weak, so the 'evil intensified' branch must stay silent (bphs-reviewer FLAG)."""
    chart = _chart({"Moon": 70.0, "Mars": 100.0})   # Mars debil in Cancer, but neecha-bhanga cancels
    assert C.NeechaBhanga("LORD_OF:1").evaluate(C.EvalContext(chart)) is True
    assert _rule("H1.C.35").condition.evaluate(C.EvalContext(chart)) is False


def test_neither_fires_for_strong_lagna_lord_in_a_benign_tara():
    """Mars exalted but in the 1st (janma) tara -> the Tara qualifier does not apply."""
    chart = _chart({"Moon": 285.0, "Mars": 285.0})   # Mars conjunct Moon -> tara 1 (janma)
    assert _rule("H1.C.35").condition.evaluate(C.EvalContext(chart)) is False
    assert _rule("H1.C.36").condition.evaluate(C.EvalContext(chart)) is False
