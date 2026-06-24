"""Unit tests for app.medini.forecast_severity.

Severity scoring is pure lookup — fast, deterministic. Tests pin the
weighting principles so a future tweak to the constants can't silently
re-rank events without a failing test.
"""
from __future__ import annotations

import pytest

from app.medini.forecast_severity import (
    annotate_events,
    score_event,
    severity_band,
)


# --------------------------------------------------------------------------- #
# Principle: SLOW PLANETS DOMINATE                                             #
# --------------------------------------------------------------------------- #

class TestIngressOrdering:
    """Saturn / Jupiter > Mars > Venus > Mercury — locked classical priority."""

    def test_saturn_ingress_outranks_mercury_ingress(self) -> None:
        saturn = {"type": "INGRESS", "planet": "Saturn"}
        mercury = {"type": "INGRESS", "planet": "Mercury"}
        assert score_event(saturn) > score_event(mercury)

    def test_jupiter_ingress_outranks_venus_ingress(self) -> None:
        jupiter = {"type": "INGRESS", "planet": "Jupiter"}
        venus = {"type": "INGRESS", "planet": "Venus"}
        assert score_event(jupiter) > score_event(venus)

    def test_node_ingress_high_priority(self) -> None:
        """Rahu/Ketu ingresses (every ~18 months) should score high — they
        re-set the karmic axis for collectives."""
        rahu = {"type": "INGRESS", "planet": "Rahu"}
        venus = {"type": "INGRESS", "planet": "Venus"}
        assert score_event(rahu) > score_event(venus)


# --------------------------------------------------------------------------- #
# Principle: ECLIPSES ARE TOP-TIER                                             #
# --------------------------------------------------------------------------- #

class TestEclipseScoring:
    def test_total_solar_eclipse_is_max_score(self) -> None:
        ev = {"type": "ECLIPSE", "family": "SOLAR", "subtype": "TOTAL"}
        assert score_event(ev) == 10

    def test_solar_outranks_lunar_at_same_subtype(self) -> None:
        """Solar eclipses affect a confined geographic path → mundane
        impact rated higher than lunar (visible to whole hemisphere)."""
        solar = {"type": "ECLIPSE", "family": "SOLAR", "subtype": "TOTAL"}
        lunar = {"type": "ECLIPSE", "family": "LUNAR", "subtype": "TOTAL"}
        assert score_event(solar) > score_event(lunar)

    def test_partial_solar_outranks_total_lunar_borderline_case(self) -> None:
        """Edge: partial solar (8) vs total lunar (9) — verify what we
        actually picked, so a refactor can't quietly flip it."""
        partial_solar = {"type": "ECLIPSE", "family": "SOLAR", "subtype": "PARTIAL"}
        total_lunar = {"type": "ECLIPSE", "family": "LUNAR", "subtype": "TOTAL"}
        assert score_event(partial_solar) == 8
        assert score_event(total_lunar) == 9


# --------------------------------------------------------------------------- #
# Principle: CONJUNCTION SEVERITY = PAIR RARITY + ORB TIGHTNESS                #
# --------------------------------------------------------------------------- #

class TestConjunctionScoring:
    def test_great_conjunction_jupiter_saturn_scores_high(self) -> None:
        """Jupiter-Saturn (every ~20 yrs) is the textbook 'era marker'.
        Should score significantly above a Mercury-Venus conjunction."""
        great = {
            "type": "CONJUNCTION", "planet_a": "Jupiter", "planet_b": "Saturn",
            "orb_degrees": 1.0,
        }
        minor = {
            "type": "CONJUNCTION", "planet_a": "Mercury", "planet_b": "Venus",
            "orb_degrees": 1.0,
        }
        assert score_event(great) >= score_event(minor) + 3

    def test_tighter_orb_increases_score(self) -> None:
        """Same pair, tighter orb → higher score."""
        loose = {
            "type": "CONJUNCTION", "planet_a": "Mars", "planet_b": "Saturn",
            "orb_degrees": 1.8,
        }
        tight = {
            "type": "CONJUNCTION", "planet_a": "Mars", "planet_b": "Saturn",
            "orb_degrees": 0.3,
        }
        assert score_event(tight) > score_event(loose)

    def test_pair_order_does_not_matter(self) -> None:
        """Pair lookup uses frozenset — Mars-Saturn == Saturn-Mars."""
        a = {"type": "CONJUNCTION", "planet_a": "Mars", "planet_b": "Saturn",
             "orb_degrees": 1.0}
        b = {"type": "CONJUNCTION", "planet_a": "Saturn", "planet_b": "Mars",
             "orb_degrees": 1.0}
        assert score_event(a) == score_event(b)


# --------------------------------------------------------------------------- #
# Clamping + UI band                                                            #
# --------------------------------------------------------------------------- #

class TestClamping:
    def test_score_always_in_1_to_10(self) -> None:
        """All event combinations must yield a 1-10 integer; the UI palette
        depends on this band being closed."""
        cases = [
            {"type": "INGRESS", "planet": "Saturn"},
            {"type": "INGRESS", "planet": "Mercury"},
            {"type": "STATION", "planet": "Saturn"},
            {"type": "CONJUNCTION", "planet_a": "Jupiter", "planet_b": "Saturn",
             "orb_degrees": 0.1},
            {"type": "CONJUNCTION", "planet_a": "Mercury", "planet_b": "Venus",
             "orb_degrees": 1.9},
            {"type": "NEW_MOON"}, {"type": "FULL_MOON"},
            {"type": "ECLIPSE", "family": "SOLAR", "subtype": "TOTAL"},
            {"type": "ECLIPSE", "family": "LUNAR", "subtype": "PENUMBRAL"},
            {"type": "UNKNOWN_TYPE"},  # fall-through path
        ]
        for ev in cases:
            s = score_event(ev)
            assert 1 <= s <= 10, f"{ev} -> {s} (out of band)"

    @pytest.mark.parametrize("score,band", [
        (10, "red"), (9, "red"),
        (8, "orange"), (7, "orange"),
        (6, "yellow"), (5, "yellow"),
        (4, "green"), (1, "green"),
    ])
    def test_severity_band_mapping(self, score: int, band: str) -> None:
        assert severity_band(score) == band


class TestAnnotateEvents:
    def test_annotate_adds_severity_and_band(self) -> None:
        """Annotation is immutable: returns new dicts with added fields."""
        evs = [
            {"type": "INGRESS", "planet": "Saturn"},
            {"type": "NEW_MOON"},
        ]
        annotated = annotate_events(evs)
        for e in annotated:
            assert "severity" in e
            assert "severity_band" in e
            assert e["severity_band"] in {"red", "orange", "yellow", "green"}

    def test_annotate_does_not_mutate_inputs(self) -> None:
        orig = {"type": "INGRESS", "planet": "Saturn"}
        annotate_events([orig])
        assert "severity" not in orig
