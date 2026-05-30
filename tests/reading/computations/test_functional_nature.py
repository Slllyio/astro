"""Tests for ``app.reading.computations.functional_nature``.

Doctrine lock D-7 (``docs/doctrine-decisions.md``):

    Use the PVR Narasimha Rao / Sanjay Rath synthesis of the full
    12-lagna x 9-planet functional benefic/malefic matrix. Each cell is
    one of {yogakaraka, functional_benefic, functional_neutral,
    functional_malefic}. Rahu and Ketu carry no lordship-based functional
    nature in classical doctrine and are always returned as neutral.

Algorithm summary
=================

For each ascendant (Lagna) 1..12 (Aries..Pisces) the table assigns each
of the 9 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu,
Ketu) one of four labels:

- ``yogakaraka``         -- owns BOTH a kendra (1/4/7/10) AND a kona (5/9)
- ``functional_benefic`` -- owns 1, 5, or 9 (Trikona) or a kendra without
                            kendradhipati conflict
- ``functional_neutral`` -- owns 2 (Maraka) or 4/7 in some mixed cases
- ``functional_malefic`` -- owns 3, 6, 8, 11, or 12 with no compensating
                            Trikona ownership

Direction in the emitted Finding:
- yogakaraka, functional_benefic  -> positive
- functional_neutral              -> neutral
- functional_malefic              -> negative

Canonical pin examples (from spec):
- Aries lagna:  Sun  is functional_benefic   (5L Trikona)
- Aries lagna:  Saturn is functional_malefic (10L kendra + 11L upachaya)
- Aries lagna:  Jupiter is functional_benefic (9L Trikona dominates 12L)
- Cancer lagna: Mars is yogakaraka  (5L + 10L = kona + kendra)
- Cancer lagna: Mercury is functional_malefic (3L + 12L)
- Cancer lagna: Venus is functional_neutral   (4L kendra + 11L upachaya)
- Leo lagna:    Mars is yogakaraka  (4L + 9L = kendra + kona)
- Leo lagna:    Sun  is functional_benefic   (1L Lagna lord)
- Libra lagna:  Saturn is yogakaraka (4L + 5L = kendra + kona)
- Libra lagna:  Mars is functional_malefic   (2L + 7L Maraka)
- Capricorn:    Venus is yogakaraka (5L + 10L = kona + kendra)
- Aquarius:     Venus is yogakaraka (4L + 9L = kendra + kona)
"""
from __future__ import annotations

import pytest


_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


_LAGNA_NAMES = (
    "",  # 0-slot
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


_VALID_NATURES = {
    "yogakaraka",
    "functional_benefic",
    "functional_neutral",
    "functional_malefic",
}


_VALID_DIRECTIONS = {"positive", "negative", "neutral", "mixed"}


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeFunctionalNature:

    def test_returns_dict_keyed_by_planet(self):
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        result = compute_functional_nature(asc_sign=1)  # Aries
        assert isinstance(result, dict)
        assert set(result.keys()) == set(_PLANETS)

    def test_emits_findings(self):
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )
        from app.reading.schema import Finding

        result = compute_functional_nature(asc_sign=4)  # Cancer
        for planet, finding in result.items():
            assert isinstance(finding, Finding), (
                f"{planet} value is not a Finding"
            )

    def test_id_grammar(self):
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        result = compute_functional_nature(asc_sign=5)  # Leo
        for planet, finding in result.items():
            assert finding.id == (
                f"foundation.functional_nature.{planet.lower()}"
            ), f"unexpected id {finding.id!r} for {planet}"

    def test_classification_is_primitive(self):
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        result = compute_functional_nature(asc_sign=7)  # Libra
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self):
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        result = compute_functional_nature(asc_sign=10)  # Capricorn
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        with pytest.raises(ValueError):
            compute_functional_nature(asc_sign=0)
        with pytest.raises(ValueError):
            compute_functional_nature(asc_sign=13)
        with pytest.raises(ValueError):
            compute_functional_nature(asc_sign=-1)

    def test_direction_matches_nature(self):
        """positive for benefic/YK, negative for malefic, neutral for neutral."""
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        for asc in range(1, 13):
            result = compute_functional_nature(asc)
            for planet, finding in result.items():
                # extract nature from evidence
                nature = _parse_nature(finding)
                if nature in ("yogakaraka", "functional_benefic"):
                    assert finding.direction == "positive", (
                        f"asc={asc} {planet} nature={nature} but "
                        f"direction={finding.direction}"
                    )
                elif nature == "functional_malefic":
                    assert finding.direction == "negative", (
                        f"asc={asc} {planet} nature={nature} but "
                        f"direction={finding.direction}"
                    )
                else:
                    assert finding.direction == "neutral", (
                        f"asc={asc} {planet} nature={nature} but "
                        f"direction={finding.direction}"
                    )


# ---------------------------------------------------------------------------
# Canonical per-lagna pin tests (from spec D-7 examples)
# ---------------------------------------------------------------------------


class TestAriesLagnaPins:
    """Aries (1) — Mars=1L+8L benefic; Sun=5L benefic; Saturn=10L+11L mal;
    Jupiter=9L+12L benefic."""

    def test_sun_benefic(self):
        nature = _nature_for(asc=1, planet="Sun")
        assert nature == "functional_benefic"

    def test_mars_benefic_as_lagna_lord(self):
        nature = _nature_for(asc=1, planet="Mars")
        assert nature == "functional_benefic"

    def test_saturn_malefic(self):
        nature = _nature_for(asc=1, planet="Saturn")
        assert nature == "functional_malefic"

    def test_jupiter_benefic_via_9th_lord(self):
        nature = _nature_for(asc=1, planet="Jupiter")
        assert nature == "functional_benefic"

    def test_mercury_malefic_via_3_and_6(self):
        nature = _nature_for(asc=1, planet="Mercury")
        assert nature == "functional_malefic"


class TestCancerLagnaPins:
    """Cancer (4) — Mars YK (5L+10L); Mercury malefic (3L+12L);
    Venus mixed/neutral (4L+11L); Moon=1L benefic."""

    def test_mars_yogakaraka(self):
        nature = _nature_for(asc=4, planet="Mars")
        assert nature == "yogakaraka"

    def test_moon_benefic_as_lagna_lord(self):
        nature = _nature_for(asc=4, planet="Moon")
        assert nature == "functional_benefic"

    def test_mercury_malefic(self):
        nature = _nature_for(asc=4, planet="Mercury")
        assert nature == "functional_malefic"

    def test_venus_neutral_mixed(self):
        nature = _nature_for(asc=4, planet="Venus")
        assert nature == "functional_neutral"


class TestLeoLagnaPins:
    """Leo (5) — Mars YK (4L+9L); Sun=1L benefic."""

    def test_mars_yogakaraka(self):
        nature = _nature_for(asc=5, planet="Mars")
        assert nature == "yogakaraka"

    def test_sun_benefic_as_lagna_lord(self):
        nature = _nature_for(asc=5, planet="Sun")
        assert nature == "functional_benefic"


class TestLibraLagnaPins:
    """Libra (7) — Saturn YK (4L+5L); Mars malefic (2L+7L Marakas);
    Venus=1L benefic."""

    def test_saturn_yogakaraka(self):
        nature = _nature_for(asc=7, planet="Saturn")
        assert nature == "yogakaraka"

    def test_mars_malefic_via_2L_7L(self):
        nature = _nature_for(asc=7, planet="Mars")
        assert nature == "functional_malefic"

    def test_venus_benefic_as_lagna_lord(self):
        nature = _nature_for(asc=7, planet="Venus")
        assert nature == "functional_benefic"


class TestCapricornLagnaPins:
    """Capricorn (10) — Venus YK (5L+10L); Saturn=1L benefic."""

    def test_venus_yogakaraka(self):
        nature = _nature_for(asc=10, planet="Venus")
        assert nature == "yogakaraka"

    def test_saturn_benefic_as_lagna_lord(self):
        nature = _nature_for(asc=10, planet="Saturn")
        assert nature == "functional_benefic"


class TestAquariusLagnaPins:
    """Aquarius (11) — Venus YK (4L+9L); Saturn=1L benefic."""

    def test_venus_yogakaraka(self):
        nature = _nature_for(asc=11, planet="Venus")
        assert nature == "yogakaraka"

    def test_saturn_benefic_as_lagna_lord(self):
        nature = _nature_for(asc=11, planet="Saturn")
        assert nature == "functional_benefic"


# ---------------------------------------------------------------------------
# Critical invariant: Rahu and Ketu are ALWAYS neutral (no lordship)
# ---------------------------------------------------------------------------


class TestNodesAlwaysNeutral:
    """D-7 critical invariant: shadow planets have no lordship-based
    functional nature. Both Rahu and Ketu must be ``functional_neutral``
    for every one of the 12 lagnas."""

    @pytest.mark.parametrize("asc", range(1, 13))
    def test_rahu_always_neutral(self, asc):
        nature = _nature_for(asc=asc, planet="Rahu")
        assert nature == "functional_neutral", (
            f"Rahu must be neutral for lagna {asc} ({_LAGNA_NAMES[asc]}), "
            f"got {nature!r}"
        )

    @pytest.mark.parametrize("asc", range(1, 13))
    def test_ketu_always_neutral(self, asc):
        nature = _nature_for(asc=asc, planet="Ketu")
        assert nature == "functional_neutral", (
            f"Ketu must be neutral for lagna {asc} ({_LAGNA_NAMES[asc]}), "
            f"got {nature!r}"
        )

    @pytest.mark.parametrize("asc", range(1, 13))
    def test_node_directions_are_neutral(self, asc):
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        result = compute_functional_nature(asc)
        assert result["Rahu"].direction == "neutral"
        assert result["Ketu"].direction == "neutral"


# ---------------------------------------------------------------------------
# Yogakaraka coverage — every classical YK pairing across the 12 lagnas
# ---------------------------------------------------------------------------


class TestYogakarakaCoverage:
    """The classical yogakaraka assignments (Laghu Parashari verse)."""

    @pytest.mark.parametrize(
        "asc,planet",
        [
            (2,  "Saturn"),   # Taurus: 9+10
            (4,  "Mars"),     # Cancer: 5+10
            (5,  "Mars"),     # Leo:    4+9
            (7,  "Saturn"),   # Libra:  4+5
            (10, "Venus"),    # Capricorn: 5+10
            (11, "Venus"),    # Aquarius:  4+9
        ],
    )
    def test_classical_yogakaraka(self, asc, planet):
        nature = _nature_for(asc=asc, planet=planet)
        assert nature == "yogakaraka", (
            f"Expected {planet} = yogakaraka for lagna {asc} "
            f"({_LAGNA_NAMES[asc]}), got {nature!r}"
        )


# ---------------------------------------------------------------------------
# Property tests: 108 (lagna, planet) combinations
# ---------------------------------------------------------------------------


class TestPropertyInvariants:
    """Exhaustive enumeration over the full 12 x 9 = 108 cell matrix."""

    def test_full_matrix_has_valid_direction(self):
        """Every (lagna, planet) cell must have a direction in the
        Finding enum {positive, negative, neutral, mixed}."""
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        for asc in range(1, 13):
            result = compute_functional_nature(asc)
            for planet, finding in result.items():
                assert finding.direction in _VALID_DIRECTIONS, (
                    f"asc={asc} planet={planet} direction="
                    f"{finding.direction!r} not in {_VALID_DIRECTIONS!r}"
                )

    def test_full_matrix_has_valid_nature(self):
        """Every cell's evidence must encode one of the 4 valid natures."""
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        for asc in range(1, 13):
            result = compute_functional_nature(asc)
            for planet, finding in result.items():
                nature = _parse_nature(finding)
                assert nature in _VALID_NATURES, (
                    f"asc={asc} planet={planet} nature={nature!r} not "
                    f"in {_VALID_NATURES!r}"
                )

    def test_all_lagna_ids_grammar(self):
        """ID stays ``foundation.functional_nature.<planet>`` for all 12
        lagnas (the ID does NOT vary by lagna — same Finding shape, the
        nature varies)."""
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        for asc in range(1, 13):
            result = compute_functional_nature(asc)
            for planet, finding in result.items():
                assert finding.id == (
                    f"foundation.functional_nature.{planet.lower()}"
                )

    def test_total_cell_count_is_108(self):
        """12 lagnas x 9 planets = 108 distinct cells exercised."""
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        cell_count = 0
        for asc in range(1, 13):
            result = compute_functional_nature(asc)
            cell_count += len(result)
        assert cell_count == 108

    def test_lagna_lord_always_benefic_or_yk(self):
        """The 1L (lagna lord) is always either functional_benefic or
        yogakaraka — it can never be malefic or neutral."""
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )
        from app.core.dignity import SIGN_RULERS

        for asc in range(1, 13):
            lagna_lord = SIGN_RULERS[asc]
            result = compute_functional_nature(asc)
            nature = _parse_nature(result[lagna_lord])
            assert nature in {"functional_benefic", "yogakaraka"}, (
                f"lagna {asc} ({_LAGNA_NAMES[asc]}) lord={lagna_lord} "
                f"has nature={nature!r}; lagna-lord must be benefic/YK"
            )


# ---------------------------------------------------------------------------
# Module-level table sanity
# ---------------------------------------------------------------------------


class TestFunctionalNatureTable:
    """The hardcoded ``FUNCTIONAL_NATURE_TABLE`` constant is a complete
    12 x 9 matrix used by ``compute_functional_nature``."""

    def test_table_has_12_lagnas(self):
        from app.reading.computations.functional_nature import (
            FUNCTIONAL_NATURE_TABLE,
        )

        assert set(FUNCTIONAL_NATURE_TABLE.keys()) == set(range(1, 13))

    def test_each_lagna_has_9_planets(self):
        from app.reading.computations.functional_nature import (
            FUNCTIONAL_NATURE_TABLE,
        )

        for asc, row in FUNCTIONAL_NATURE_TABLE.items():
            assert set(row.keys()) == set(_PLANETS), (
                f"lagna {asc} row keys are {set(row.keys())!r}, "
                f"expected {set(_PLANETS)!r}"
            )

    def test_all_cells_valid_natures(self):
        from app.reading.computations.functional_nature import (
            FUNCTIONAL_NATURE_TABLE,
        )

        for asc, row in FUNCTIONAL_NATURE_TABLE.items():
            for planet, nature in row.items():
                assert nature in _VALID_NATURES, (
                    f"asc={asc} {planet} nature={nature!r} invalid"
                )

    def test_table_is_constant_across_calls(self):
        """The table is a module-level Final constant — calling the
        function twice with the same asc returns the same nature."""
        from app.reading.computations.functional_nature import (
            compute_functional_nature,
        )

        r1 = compute_functional_nature(asc_sign=6)
        r2 = compute_functional_nature(asc_sign=6)
        for planet in _PLANETS:
            assert _parse_nature(r1[planet]) == _parse_nature(r2[planet])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _nature_for(asc: int, planet: str) -> str:
    """Compute functional nature for (asc, planet) via the public API."""
    from app.reading.computations.functional_nature import (
        compute_functional_nature,
    )

    return _parse_nature(compute_functional_nature(asc)[planet])


def _parse_nature(finding) -> str:
    """Extract the ``nature=<value>`` evidence line from a Finding."""
    for line in finding.evidence:
        if line.startswith("nature="):
            return line.split("=", 1)[1]
    raise AssertionError(
        f"finding {finding.id!r} missing 'nature=' evidence line; "
        f"evidence={finding.evidence!r}"
    )
