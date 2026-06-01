"""Tests for app.core.drishti_argala — BPHS Ch.26 + Jaimini Ch.4 doctrine.

Locked decision per CLAUDE.md: whole-sign drishti, Rahu/Ketu use
Jupiter-style 5/9 aspects (Sukra Nadi).
"""
from __future__ import annotations

import pytest

from app.core.drishti_argala import (
    ArgalaSource,
    aspects_from_planet,
    aspect_graph,
    argala_for_bhava,
    argala_report,
    planets_aspecting_bhava,
)


# ─── Drishti tests ───────────────────────────────────────────────────


class TestDrishtiBasePlanets:
    """Sun/Moon/Mercury/Venus aspect only the 7th sign."""

    def test_sun_in_1_aspects_only_7(self):
        """Sun has no extra aspects → opposition only."""
        assert aspects_from_planet("Sun", 1) == (7,)

    def test_moon_in_4_aspects_only_10(self):
        """Moon in 4th aspects 10th (opposition)."""
        assert aspects_from_planet("Moon", 4) == (10,)

    def test_venus_in_7_aspects_only_1(self):
        """Venus opposite Lagna aspects 1st house."""
        assert aspects_from_planet("Venus", 7) == (1,)


class TestDrishtiMars:
    """Mars adds 4th + 8th aspects beyond the opposition."""

    def test_mars_in_1_aspects_4_7_8(self):
        """Mars in Lagna aspects 4th, 7th, 8th — the angular-trial set."""
        assert aspects_from_planet("Mars", 1) == (4, 7, 8)

    def test_mars_in_10_aspects_1_4_5(self):
        """Mars in 10th: +4 → 1st, +7 → 4th (opp), +8 → 5th."""
        assert aspects_from_planet("Mars", 10) == (1, 4, 5)


class TestDrishtiJupiterAndNodes:
    """Jupiter + Rahu + Ketu all carry 5 + 9 aspects (Sukra Nadi)."""

    def test_jupiter_in_1_aspects_5_7_9(self):
        """Jupiter in Lagna casts the trinal-benevolent triple."""
        assert aspects_from_planet("Jupiter", 1) == (5, 7, 9)

    def test_rahu_in_1_uses_jupiter_aspects(self):
        """Locked decision: Rahu uses Jupiter-style 5/9 aspects."""
        assert aspects_from_planet("Rahu", 1) == (5, 7, 9)

    def test_ketu_in_1_uses_jupiter_aspects(self):
        """Locked decision: Ketu uses Jupiter-style 5/9 aspects."""
        assert aspects_from_planet("Ketu", 1) == (5, 7, 9)


class TestDrishtiSaturn:
    """Saturn adds 3rd + 10th aspects — the karma-pressure pair."""

    def test_saturn_in_1_aspects_3_7_10(self):
        """Saturn in Lagna aspects 3rd, 7th, 10th — its signature."""
        assert aspects_from_planet("Saturn", 1) == (3, 7, 10)

    def test_saturn_in_12_aspects_2_6_9(self):
        """Saturn in 12: +3 → 2nd, +7 → 6th (opp), +10 → 9th."""
        assert aspects_from_planet("Saturn", 12) == (2, 6, 9)


class TestAspectGraphAndReverseLookup:
    """Graph-level integrity + the reverse "who aspects bhava X" lookup."""

    def test_aspect_graph_excludes_missing_planets(self):
        """Missing planets in the input → absent from output graph."""
        g = aspect_graph({"Sun": 1, "Moon": 4})
        assert set(g) == {"Sun", "Moon"}

    def test_planets_aspecting_bhava_includes_self_opposition(self):
        """A planet in 1H aspects 7H — reverse lookup must catch it."""
        houses = {"Mars": 1, "Jupiter": 5, "Saturn": 10}
        # Bhava 7: Mars (1→7 opp), Jupiter (5→11 not 7), Saturn (10→1,4,5 not 7)
        result = planets_aspecting_bhava(7, houses)
        assert "Mars" in result

    def test_jupiter_in_5_aspects_bhava_9_via_5th_aspect(self):
        """Jupiter's 5th aspect: 5+5 = 9 (1-indexed wrap: 5→9 via dist 5)."""
        result = planets_aspecting_bhava(9, {"Jupiter": 5})
        assert result == ("Jupiter",)


# ─── Argala tests ────────────────────────────────────────────────────


class TestArgalaDistances:
    """Verify the 4 argala distances map to the right houses."""

    def test_argala_on_1h_finds_houses_2_4_11_5(self):
        """From focal 1H: argala houses are 2nd, 4th, 11th (primary), 5th (sec)."""
        houses = {
            "Sun": 2, "Moon": 4, "Mars": 11, "Mercury": 5,  # cause
            "Jupiter": 12, "Venus": 10, "Saturn": 3,        # block
        }
        sources = argala_for_bhava(1, houses)
        argala_house_set = {s.argala_house for s in sources}
        assert argala_house_set == {2, 4, 11, 5}

    def test_argala_distances_are_primary_or_secondary(self):
        """Every argala source has kind ∈ {primary, secondary}."""
        houses = {"Sun": 2, "Mars": 4}
        sources = argala_for_bhava(1, houses)
        for s in sources:
            assert s.kind in ("primary", "secondary")
            if s.distance in (2, 4, 11):
                assert s.kind == "primary"
            elif s.distance == 5:
                assert s.kind == "secondary"


class TestVirodhargalaBlocking:
    """Counter-blocks neutralise argala when count ≥ source count."""

    def test_solo_argala_with_no_blocker_is_active(self):
        """One planet in argala house, none in counter → not blocked."""
        houses = {"Jupiter": 2}  # 2nd-house argala on 1H
        sources = argala_for_bhava(1, houses)
        argala_2 = next(s for s in sources if s.distance == 2)
        assert argala_2.causing_planets == ("Jupiter",)
        assert argala_2.blocking_planets == ()
        assert not argala_2.is_blocked

    def test_argala_blocked_by_equal_count_in_counter_house(self):
        """1 cause + 1 block → blocked (simple count rule, pre-Phase-6)."""
        houses = {"Jupiter": 2, "Saturn": 12}  # 12 is Virodhargala to 2
        sources = argala_for_bhava(1, houses)
        argala_2 = next(s for s in sources if s.distance == 2)
        assert argala_2.causing_planets == ("Jupiter",)
        assert argala_2.blocking_planets == ("Saturn",)
        assert argala_2.is_blocked


class TestArgalaPairing:
    """Counter-house pairings: 2↔12, 4↔10, 11↔3, 5↔9."""

    @pytest.mark.parametrize("focal,distance,expected_argala,expected_counter", [
        (1, 2, 2, 12),
        (1, 4, 4, 10),
        (1, 11, 11, 3),
        (1, 5, 5, 9),
        (5, 4, 8, 2),  # 4th from 5th = 8; 10th from 5th = 2
    ])
    def test_pairings_arithmetic(self, focal, distance, expected_argala, expected_counter):
        """Argala arithmetic with inclusive Jaimini counting."""
        # Force a planet into each candidate house so the source records.
        houses = {"Sun": expected_argala, "Moon": expected_counter}
        sources = argala_for_bhava(focal, houses)
        s = next(s for s in sources if s.distance == distance)
        assert s.argala_house == expected_argala
        assert s.counter_house == expected_counter


class TestArgalaReport:
    """Whole-chart argala report — every bhava that has activity."""

    def test_full_report_covers_all_12_bhavas_by_default(self):
        """Default call returns one entry per bhava 1..12."""
        houses = {"Sun": 5}
        report = argala_report(houses)
        assert set(report.keys()) == set(range(1, 13))

    def test_empty_chart_has_no_argala_sources(self):
        """No planets → every bhava's source list is empty."""
        report = argala_report({})
        for sources in report.values():
            assert sources == ()


class TestArgalaSourceDataclass:
    """Argala records are frozen — defensive invariant."""

    def test_argala_source_is_frozen(self):
        """Immutability prevents downstream mutation surprise."""
        houses = {"Mars": 2}
        sources = argala_for_bhava(1, houses)
        with pytest.raises(Exception):  # FrozenInstanceError
            sources[0].is_blocked = True  # type: ignore[misc]


class TestInvalidInputs:
    """Out-of-range bhavas raise per CLAUDE.md fail-fast convention."""

    def test_aspect_lookup_rejects_invalid_bhava(self):
        """Reverse-aspect lookup validates bhava range."""
        with pytest.raises(ValueError):
            planets_aspecting_bhava(0, {})
        with pytest.raises(ValueError):
            planets_aspecting_bhava(13, {})

    def test_aspects_from_planet_rejects_invalid_house(self):
        """Audit fix: aspects_from_planet validates house range (was
        silently producing phantom aspects via modular arithmetic)."""
        with pytest.raises(ValueError):
            aspects_from_planet("Saturn", 0)
        with pytest.raises(ValueError):
            aspects_from_planet("Saturn", 13)
        with pytest.raises(ValueError):
            aspects_from_planet("Mars", -1)

    def test_argala_rejects_invalid_focal(self):
        """argala_for_bhava validates focal range."""
        with pytest.raises(ValueError):
            argala_for_bhava(0, {})
