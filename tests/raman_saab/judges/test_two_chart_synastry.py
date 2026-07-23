"""Two-chart synastry — `judges/two_chart_synastry.py`.

Pins Raman's matching contacts on Track-B synthetic charts (no swisseph): Kuja-doṣa detection +
mutual cancellation, the mitigation flag, benefic overlay into the other's houses, and the
Moon-sign = other's-Lagna cross-point. Each test states the matching fact it checks.
"""
from __future__ import annotations

from pathlib import Path

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.two_chart_synastry import (
    _kuja_profile, build_two_chart_synastry)


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    """Track-B chart; asc_lon 5.0 -> Aries ascendant (sign 1)."""
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


def _has(tags: tuple, needle: str) -> bool:
    return any(needle in t.text for t in tags)


class TestKujaProfile:
    def test_mars_in_7th_is_kuja_dosha(self) -> None:
        """Mars in Libra (the 7th from an Aries Lagna) carries Kuja doṣa."""
        k = _kuja_profile("x", _chart({"Mars": 185.0}))   # Libra
        assert k.strength >= 1 and k.house_from_lagna == 7

    def test_mars_in_own_8th_is_mitigated(self) -> None:
        """Mars in Scorpio (its own sign, the 8th from Aries) is a Kuja house but mitigated."""
        k = _kuja_profile("x", _chart({"Mars": 215.0}))   # Scorpio
        assert k.house_from_lagna == 8 and k.mitigated is True

    def test_mars_in_3rd_is_not_kuja(self) -> None:
        """Mars in Gemini (the 3rd, not a Kuja house) → no doṣa."""
        k = _kuja_profile("x", _chart({"Mars": 65.0}))    # Gemini
        assert k.strength == 0 and k.house_from_lagna == 0


class TestSynastry:
    def test_both_dosha_cancel(self) -> None:
        """Both charts with Mars in the 7th → the classical mutual cancellation."""
        a = _chart({"Mars": 185.0})
        b = _chart({"Mars": 185.0})
        s = build_two_chart_synastry(a, "husband", b, "wife")
        assert _has(s.kuja_comparison, "cancel each other")

    def test_one_sided_dosha_is_an_imbalance(self) -> None:
        """One chart with Kuja doṣa and the other without → an imbalance is reported."""
        a = _chart({"Mars": 185.0})   # Libra 7th -> dosha
        b = _chart({"Mars": 65.0})    # Gemini 3rd -> no dosha
        s = build_two_chart_synastry(a, "husband", b, "wife")
        assert _has(s.kuja_comparison, "imbalance")

    def test_benefic_overlay_into_a_trine_harmonises(self) -> None:
        """The husband's Jupiter falling in the wife's 5th (a trine) is a harmonising contact."""
        a = _chart({"Jupiter": 125.0})   # Leo
        b = _chart({}, asc_lon=5.0)      # Aries Lagna -> Leo is the wife's 5th
        s = build_two_chart_synastry(a, "husband", b, "wife")
        assert _has(s.overlays, "harmonising contact")

    def test_moon_sign_equals_other_lagna_is_a_bond(self) -> None:
        """The husband's Moon-sign being the wife's Lagna is a stabilising bond."""
        a = _chart({"Moon": 5.0})        # Aries Moon
        b = _chart({}, asc_lon=5.0)      # Aries Lagna
        s = build_two_chart_synastry(a, "husband", b, "wife")
        assert _has(s.cross_points, "stabilising bond")

    def test_nets_no_verdict(self) -> None:
        """No compatible/incompatible verdict field exists — the report weighs, it does not rule."""
        s = build_two_chart_synastry(_chart({"Mars": 185.0}), "a", _chart({"Mars": 65.0}), "b")
        assert not hasattr(s, "verdict")
        assert not hasattr(s, "compatible")


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_synastry_surface(self) -> None:
        """The D1 verdict path imports nothing from this surface — ratchet untouched."""
        import app.raman_saab.judges.house_template as ht
        assert "two_chart_synastry" not in Path(ht.__file__).read_text(encoding="utf-8")
