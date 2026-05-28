"""Tests for ``app.core.yoga_strength`` — the unified strength scorer."""
from __future__ import annotations

import pytest

from app.core.yoga_strength import (
    build_yoga_instance,
    score_yoga_strength,
)


def _chart(positions: dict[str, tuple[int, float]]) -> dict:
    """Chart with planet → (sign, longitude). Optional D9 sign added."""
    return {
        p: {
            "sign": s, "longitude": lon,
            "degree_in_sign": lon % 30.0, "is_retrograde": False,
        }
        for p, (s, lon) in positions.items()
    }


def _full_chart(asc_sign: int = 1) -> dict:
    """A complete 9-planet chart at modest strengths for general testing."""
    return _chart({
        "Sun":     (3,   75.0),
        "Moon":    (4,  105.0),
        "Mars":    (5,  135.0),
        "Mercury": (6,  165.0),
        "Jupiter": (9,  255.0),
        "Venus":   (7,  195.0),
        "Saturn":  (10, 295.0),
        "Rahu":    (3,   75.0),
        "Ketu":    (9,  255.0),
    })


def test_score_yoga_strength_in_unit_range() -> None:
    """Strength is always in [0, 1]."""
    chart = _full_chart()
    for participants in [("Sun",), ("Jupiter", "Moon"), ("Mars", "Saturn", "Mercury")]:
        s = score_yoga_strength(participants, chart, asc_sign=1)
        assert 0.0 <= s <= 1.0, (participants, s)


def test_score_yoga_strength_empty_participants_zero() -> None:
    chart = _full_chart()
    assert score_yoga_strength((), chart, asc_sign=1) == pytest.approx(0.0)


def test_score_yoga_strength_missing_participant_returns_0() -> None:
    """A participant missing from the chart drives geometric mean to 0."""
    chart = _full_chart()
    # Pluto is not in chart → fraction 0 → geometric mean 0
    assert score_yoga_strength(("Sun", "Pluto"), chart, asc_sign=1) == \
        pytest.approx(0.0)


def test_score_yoga_strength_vipareeta_inversion() -> None:
    """Vipareeta inversion: high participant strength → low yoga strength."""
    chart = _full_chart()
    normal = score_yoga_strength(("Sun",), chart, asc_sign=1)
    inverted = score_yoga_strength(
        ("Sun",), chart, asc_sign=1, invert_for_vipareeta=True
    )
    assert inverted == pytest.approx(1.0 - normal, abs=1e-9)


def test_build_yoga_instance_basic() -> None:
    """Round-trip: build a YogaInstance with strength scored from chart."""
    chart = _full_chart()
    inst = build_yoga_instance(
        name="Test Yoga",
        category="raja",
        participants=("Sun", "Moon"),
        houses_activated=(1, 4, 4),  # 4 deduped
        promise_axis="fame",
        lords_involved=("Sun", "Moon"),
        chart=chart,
        asc_sign=1,
    )
    assert inst.name == "Test Yoga"
    assert inst.category == "raja"
    assert inst.participants == ("Sun", "Moon")
    assert inst.houses_activated == (1, 4)  # deduped + sorted
    assert 0.0 <= inst.strength <= 1.0


def test_build_yoga_instance_vipareeta_flag() -> None:
    """Vipareeta flag inverts strength at construction time."""
    chart = _full_chart()
    normal = build_yoga_instance(
        name="N", category="raja", participants=("Sun",),
        houses_activated=(1,), promise_axis="x", lords_involved=("Sun",),
        chart=chart, asc_sign=1, invert_for_vipareeta=False,
    )
    inverted = build_yoga_instance(
        name="V", category="vipareeta_raj", participants=("Sun",),
        houses_activated=(1,), promise_axis="x", lords_involved=("Sun",),
        chart=chart, asc_sign=1, invert_for_vipareeta=True,
    )
    assert inverted.strength == pytest.approx(1.0 - normal.strength, abs=1e-9)


def test_score_yoga_strength_geometric_mean_property() -> None:
    """Geometric mean is bounded by individual fractions: min ≤ mean ≤ max
    (when all fractions are non-zero)."""
    chart = _full_chart()
    # Single-participant strength: just the fraction
    s_jupiter = score_yoga_strength(("Jupiter",), chart, asc_sign=1)
    s_sun = score_yoga_strength(("Sun",), chart, asc_sign=1)
    s_both = score_yoga_strength(("Sun", "Jupiter"), chart, asc_sign=1)
    if s_jupiter > 0 and s_sun > 0:
        lo, hi = sorted((s_jupiter, s_sun))
        assert lo <= s_both <= hi + 1e-9, (lo, s_both, hi)
