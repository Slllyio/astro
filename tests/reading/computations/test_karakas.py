"""Tests for ``app.reading.computations.karakas``.

Doctrine lock D-1: 8-karaka Jaimini scheme (PVR Narasimha Rao).

The algorithm orders planets by degree-within-sign in *descending* order;
the highest-degree planet becomes the Atmakaraka (AK), the second
becomes Amatya Karaka (AmK), and so on down to Dara Karaka (DK). In the
8-karaka mode, Rahu participates with its longitude inverted
(``30 - degree``), Ketu is excluded entirely, and the eighth slot is
the additional Putra/Stri Karaka.

For RETROGRADE planets (vakri), degree-within-sign is also inverted
(``30 - degree``) before ranking, matching jagannathahora.io's behaviour
when "use reverse longitudes for retrograde" is enabled (the default).

Bangalore baseline (1990-07-15 12:00 IST / 12.97, 77.59) is used as the
canonical fixture; we recompute it at test time so any swisseph upgrade
is caught by these tests.
"""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Bangalore baseline fixture (computed once per session)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    """Canonical Bangalore-baseline chart used across reading-layer tests."""
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def d1_chart(bangalore_chart) -> dict:
    return bangalore_chart["d1"]


# ---------------------------------------------------------------------------
# Construction / shape
# ---------------------------------------------------------------------------


_KARAKA_NAMES_8 = (
    "atmakaraka", "amatyakaraka", "bhratrikaraka", "matrikaraka",
    "pitrikaraka", "gnatikaraka", "darakaraka", "strikaraka",
)
_KARAKA_NAMES_7 = _KARAKA_NAMES_8[:7]


class TestComputeKarakas8:
    """Default 8-karaka mode (D-1 lock)."""

    def test_returns_mapping_with_eight_karakas(self, d1_chart):
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(_KARAKA_NAMES_8)

    def test_emits_findings(self, d1_chart):
        from app.reading.computations.karakas import compute_karakas
        from app.reading.schema import Finding

        result = compute_karakas(d1_chart)
        for karaka, finding in result.items():
            assert isinstance(finding, Finding), f"{karaka} is not a Finding"

    def test_id_grammar(self, d1_chart):
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart)
        for karaka, finding in result.items():
            assert finding.id == f"primitive.karakas.{karaka}"

    def test_classification_is_primitive(self, d1_chart):
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_each_karaka_planet_unique(self, d1_chart):
        """The 8 karakas must be assigned to 8 different planets."""
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart)
        planets_used = []
        for finding in result.values():
            # Verdict embeds the planet name; the evidence carries it
            # explicitly for machine-readable use.
            for line in finding.evidence:
                if line.startswith("planet="):
                    planets_used.append(line.split("=", 1)[1])
                    break
        assert len(planets_used) == 8
        assert len(set(planets_used)) == 8, (
            f"karaka planets must be unique, got {planets_used}"
        )

    def test_ketu_excluded(self, d1_chart):
        """Ketu is never a karaka in the Jaimini scheme."""
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart)
        for finding in result.values():
            for line in finding.evidence:
                if line.startswith("planet="):
                    planet = line.split("=", 1)[1]
                    assert planet != "Ketu", (
                        f"Ketu must not be a karaka, found in {finding.id}"
                    )

    def test_rahu_present_in_8_mode(self, d1_chart):
        """In 8-karaka mode, Rahu IS included (uses ``30 - deg`` ranking)."""
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart, karaka_mode=8)
        planets_used = set()
        for finding in result.values():
            for line in finding.evidence:
                if line.startswith("planet="):
                    planets_used.add(line.split("=", 1)[1])
                    break
        assert "Rahu" in planets_used

    def test_verdict_under_140_chars(self, d1_chart):
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_verdict_mentions_atmakaraka(self, d1_chart):
        """AK verdict should clearly identify it as Atmakaraka."""
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart)
        assert "Atmakaraka" in result["atmakaraka"].verdict


class TestComputeKarakas7:
    """7-karaka mode (classical BPHS — excludes Rahu)."""

    def test_returns_seven_karakas(self, d1_chart):
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart, karaka_mode=7)
        assert set(result.keys()) == set(_KARAKA_NAMES_7)

    def test_rahu_excluded(self, d1_chart):
        """7-karaka mode excludes Rahu (only the 7 natural planets)."""
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1_chart, karaka_mode=7)
        planets_used = set()
        for finding in result.values():
            for line in finding.evidence:
                if line.startswith("planet="):
                    planets_used.add(line.split("=", 1)[1])
                    break
        assert "Rahu" not in planets_used
        assert "Ketu" not in planets_used


class TestRanking:
    """Verify the ranking algorithm itself."""

    def test_ranking_descending_by_effective_degree(self):
        """AK has the highest effective degree among karaka candidates."""
        from app.reading.computations.karakas import compute_karakas

        # Hand-crafted chart: Sun at 29.5 (highest direct), Mars at 28
        # (retrograde -> 2 effective), Moon at 25, etc.
        chart = {
            "Sun":     {"longitude": 29.5, "degree_in_sign": 29.5, "is_retrograde": False},
            "Moon":    {"longitude": 55.0, "degree_in_sign": 25.0, "is_retrograde": False},
            "Mars":    {"longitude": 88.0, "degree_in_sign": 28.0, "is_retrograde": True},  # eff 2
            "Mercury": {"longitude": 120.0, "degree_in_sign": 0.0, "is_retrograde": False},
            "Jupiter": {"longitude": 150.5, "degree_in_sign": 0.5, "is_retrograde": False},
            "Venus":   {"longitude": 175.0, "degree_in_sign": 25.0, "is_retrograde": False},
            "Saturn":  {"longitude": 210.0, "degree_in_sign": 0.0, "is_retrograde": False},
            "Rahu":    {"longitude": 220.0, "degree_in_sign": 10.0, "is_retrograde": False},  # eff 20
            "Ketu":    {"longitude": 40.0, "degree_in_sign": 10.0, "is_retrograde": False},  # excluded
        }
        result = compute_karakas(chart, karaka_mode=8)
        # AK is Sun (effective 29.5)
        ak_planet = None
        for line in result["atmakaraka"].evidence:
            if line.startswith("planet="):
                ak_planet = line.split("=", 1)[1]
        assert ak_planet == "Sun"

    def test_retrograde_uses_inverted_degree(self):
        """A planet at deg 28 retrograde ranks lower than a planet at deg 27 direct."""
        from app.reading.computations.karakas import compute_karakas

        chart = {
            "Sun":     {"longitude": 0.0,  "degree_in_sign": 0.0,  "is_retrograde": False},
            "Moon":    {"longitude": 31.0, "degree_in_sign": 1.0,  "is_retrograde": False},
            "Mars":    {"longitude": 88.0, "degree_in_sign": 28.0, "is_retrograde": True},   # effective 2
            "Mercury": {"longitude": 117.0, "degree_in_sign": 27.0, "is_retrograde": False},  # 27
            "Jupiter": {"longitude": 152.0, "degree_in_sign": 2.0,  "is_retrograde": False},
            "Venus":   {"longitude": 183.0, "degree_in_sign": 3.0,  "is_retrograde": False},
            "Saturn":  {"longitude": 214.0, "degree_in_sign": 4.0,  "is_retrograde": False},
            "Rahu":    {"longitude": 270.0, "degree_in_sign": 0.0,  "is_retrograde": False},   # effective 30
            "Ketu":    {"longitude": 90.0,  "degree_in_sign": 0.0,  "is_retrograde": False},
        }
        result = compute_karakas(chart, karaka_mode=8)
        ak_planet = None
        for line in result["atmakaraka"].evidence:
            if line.startswith("planet="):
                ak_planet = line.split("=", 1)[1]
        # Rahu effective degree = 30 - 0 = 30 -> highest
        assert ak_planet == "Rahu"

        # Mars eff degree = 30 - 28 = 2 (very low); Mercury at 27 outranks Mars.
        # Locate Mars and Mercury in the karaka sequence.
        mars_idx = mercury_idx = None
        for idx, name in enumerate(_KARAKA_NAMES_8):
            for line in result[name].evidence:
                if line.startswith("planet="):
                    planet = line.split("=", 1)[1]
                    if planet == "Mars":
                        mars_idx = idx
                    elif planet == "Mercury":
                        mercury_idx = idx
                    break
        assert mars_idx is not None and mercury_idx is not None
        assert mercury_idx < mars_idx, (
            f"Mercury(27 dir) should outrank Mars(28 retro -> eff 2); "
            f"got mercury_idx={mercury_idx}, mars_idx={mars_idx}"
        )


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


_PLANET_NAMES_FOR_PROP = (
    "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


@st.composite
def _synthetic_d1(draw):
    """Generate a synthetic D1 chart with random longitudes & retrograde flags."""
    out = {}
    for name in _PLANET_NAMES_FOR_PROP:
        # Random sign offset to keep longitudes spread across the zodiac.
        lon = draw(st.floats(min_value=0.0, max_value=359.999))
        retro = draw(st.booleans()) if name not in ("Sun", "Moon") else False
        out[name] = {
            "longitude": lon,
            "degree_in_sign": lon % 30,
            "is_retrograde": retro,
        }
    return out


class TestPropertyInvariants:

    @given(d1=_synthetic_d1())
    def test_eight_karaka_planet_assignment_is_permutation(self, d1):
        """The 8 karaka planet assignments must be a permutation of 8 candidates."""
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1, karaka_mode=8)
        # Candidate set: 7 naturals + Rahu, excluding Ketu.
        candidates = {
            "Sun", "Moon", "Mars", "Mercury",
            "Jupiter", "Venus", "Saturn", "Rahu",
        }
        planets_used = []
        for name in _KARAKA_NAMES_8:
            for line in result[name].evidence:
                if line.startswith("planet="):
                    planets_used.append(line.split("=", 1)[1])
                    break
        assert len(planets_used) == 8
        assert set(planets_used) == candidates, (
            f"karaka set != candidate set: {set(planets_used)} vs {candidates}"
        )
        assert len(set(planets_used)) == 8  # no duplicates

    @given(d1=_synthetic_d1())
    def test_seven_karaka_planet_assignment_is_permutation(self, d1):
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1, karaka_mode=7)
        candidates = {
            "Sun", "Moon", "Mars", "Mercury",
            "Jupiter", "Venus", "Saturn",
        }
        planets_used = []
        for name in _KARAKA_NAMES_7:
            for line in result[name].evidence:
                if line.startswith("planet="):
                    planets_used.append(line.split("=", 1)[1])
                    break
        assert set(planets_used) == candidates
        assert len(set(planets_used)) == 7

    @given(d1=_synthetic_d1())
    def test_ids_unique(self, d1):
        from app.reading.computations.karakas import compute_karakas

        result = compute_karakas(d1, karaka_mode=8)
        ids = [f.id for f in result.values()]
        assert len(ids) == len(set(ids))
