"""Tests for the unified ``detect_yogas`` entry point in
``app.reading.computations.yogas_extended``.

The orchestrator runs all 9 yoga detectors and returns a flattened list
of Finding objects. Domains/* consume this for their yoga sections.

Detectors aggregated:
    detect_adhi, detect_lakshmi, detect_saraswati, detect_daridra,
    detect_chamara, detect_vipareeta, detect_parivartana,
    detect_kala_sarpa, detect_neech_bhanga.
"""
from __future__ import annotations

import pytest


def _planet_dict(sign: int, longitude: float | None = None) -> dict:
    lon = longitude if longitude is not None else (sign - 1) * 30.0 + 15.0
    return {"sign": sign, "longitude": float(lon)}


def _empty_chart(asc_sign: int = 1, moon_sign: int = 1) -> dict:
    """Construct a benign 9-planet chart (Moon at moon_sign, all others
    at asc_sign). Should fire NO yogas, but exercise every detector."""
    chart: dict[str, dict] = {"Moon": _planet_dict(moon_sign)}
    for planet in (
        "Sun", "Mars", "Mercury", "Jupiter", "Venus",
        "Saturn", "Rahu", "Ketu",
    ):
        chart[planet] = _planet_dict(asc_sign)
    return chart


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class TestPublicApi:

    def test_detect_yogas_importable(self):
        from app.reading.computations.yogas_extended import detect_yogas

        assert callable(detect_yogas)

    def test_individual_detectors_re_exported(self):
        from app.reading.computations import yogas_extended as ye

        for name in (
            "detect_adhi", "detect_lakshmi", "detect_saraswati",
            "detect_daridra", "detect_chamara", "detect_vipareeta",
            "detect_parivartana", "detect_kala_sarpa", "detect_neech_bhanga",
            "detect_yogas",
        ):
            assert hasattr(ye, name), f"missing re-export: {name}"

    def test_all_includes_orchestrator(self):
        from app.reading.computations import yogas_extended as ye

        assert "detect_yogas" in ye.__all__


# ---------------------------------------------------------------------------
# Shape / behaviour
# ---------------------------------------------------------------------------


class TestDetectYogasShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended import detect_yogas

        chart = _empty_chart()
        result = detect_yogas(chart, asc_sign=1, moon_sign=1)
        assert isinstance(result, list)

    def test_returns_flat_finding_list(self):
        from app.reading.computations.yogas_extended import detect_yogas
        from app.reading.schema import Finding

        chart = _empty_chart()
        result = detect_yogas(chart, asc_sign=1, moon_sign=1)
        for item in result:
            assert isinstance(item, Finding)

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended import detect_yogas

        chart = _empty_chart()
        with pytest.raises(ValueError):
            detect_yogas(chart, asc_sign=0, moon_sign=1)
        with pytest.raises(ValueError):
            detect_yogas(chart, asc_sign=13, moon_sign=1)


# ---------------------------------------------------------------------------
# Bangalore baseline: smoke-test all detectors against a representative
# Virgo-lagna canonical input (Bangalore 1990-07-15 12:00 IST).
# ---------------------------------------------------------------------------


class TestBangaloreBaseline:
    """The Bangalore canonical chart (see CLAUDE.md) has Virgo Lagna
    (~173.99° → sign 6), Moon at Revati pada 3 (Pisces ~16.something).
    We don't pin specific yoga outputs here — this is a smoke test that
    the unified entry point runs end-to-end on a realistic chart and
    returns valid Findings."""

    def test_runs_without_error_on_virgo_lagna_chart(self):
        from app.reading.computations.yogas_extended import detect_yogas
        from app.reading.schema import Finding

        # Approximate Bangalore-baseline d1 chart (signs only, longitudes
        # approximated to mid-sign for stability — yoga detection is
        # sign-based for everything except kala_sarpa).
        # Virgo Lagna → asc_sign=6. Moon in Pisces → moon_sign=12.
        chart = {
            "Sun":     _planet_dict(sign=4,  longitude=98.5),   # Cancer
            "Moon":    _planet_dict(sign=12, longitude=346.7),  # Pisces (Revati)
            "Mars":    _planet_dict(sign=6,  longitude=160.2),  # Virgo
            "Mercury": _planet_dict(sign=3,  longitude=75.4),   # Gemini
            "Jupiter": _planet_dict(sign=4,  longitude=105.1),  # Cancer
            "Venus":   _planet_dict(sign=5,  longitude=130.8),  # Leo
            "Saturn":  _planet_dict(sign=10, longitude=275.2),  # Capricorn
            "Rahu":    _planet_dict(sign=11, longitude=320.0),  # Aquarius
            "Ketu":    _planet_dict(sign=5,  longitude=140.0),  # Leo
        }
        result = detect_yogas(chart, asc_sign=6, moon_sign=12)
        # The orchestrator must succeed end-to-end and every emitted item
        # must be a valid Finding instance.
        assert isinstance(result, list)
        for f in result:
            assert isinstance(f, Finding)
            # ID prefix must match the practitioner.yogas_extended namespace.
            assert f.id.startswith("practitioner.yogas_extended.")
