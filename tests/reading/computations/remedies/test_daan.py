"""Tests for ``app.reading.computations.remedies.daan``.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs). Daan (charity) is the practitioner-preferred
front-line remedy: free, karmically clean, and to be performed BEFORE
gemstone strengthening. Each planet has a canonical bundle of items,
a weekday of donation, and a target recipient class.

Canonical table (verbatim):

  Sun     - Wheat, jaggery, copper, red items          / Sunday        / brahmins
  Moon    - Rice, milk, silver, white items            / Monday        / mother-figures
  Mars    - Red lentils (masoor), red cloth, copper    / Tuesday       / soldiers/braves
  Mercury - Green moong, green cloth, emerald-like     / Wednesday     / students
  Jupiter - Yellow items, chana dal, gold              / Thursday      / teachers/gurus
  Venus   - White items, sugar, silk, perfume          / Friday        / women/cows
  Saturn  - Black sesame, mustard oil, iron, black     / Saturday      / poor/elderly/disabled
  Rahu    - Black blanket, gomedh stone if affordable  / Saturday eve  / laborers
  Ketu    - Multi-colored cloth, mustard oil           / Tuesday eve   / ascetics

ID grammar: ``practitioner.remedies.daan.<planet>`` (planet lowercased).
classification: ``"primitive"``.
direction: ``"positive"`` (charity is uplifting / pacifies the planet).
"""
from __future__ import annotations

import pytest


_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


_EXPECTED_WEEKDAYS = {
    "Sun":     "Sunday",
    "Moon":    "Monday",
    "Mars":    "Tuesday",
    "Mercury": "Wednesday",
    "Jupiter": "Thursday",
    "Venus":   "Friday",
    "Saturn":  "Saturday",
    "Rahu":    "Saturday evening",
    "Ketu":    "Tuesday evening",
}


_EXPECTED_RECIPIENTS = {
    "Sun":     "brahmins",
    "Moon":    "mother-figures",
    "Mars":    "soldiers",
    "Mercury": "students",
    "Jupiter": "teachers",
    "Venus":   "women",
    "Saturn":  "poor",
    "Rahu":    "laborers",
    "Ketu":    "ascetics",
}


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestRecommendDaanShape:

    def test_empty_input_returns_empty(self):
        from app.reading.computations.remedies.daan import recommend_daan

        assert recommend_daan([]) == []

    def test_returns_finding_list(self):
        from app.reading.computations.remedies.daan import recommend_daan
        from app.reading.schema import Finding

        result = recommend_daan(["Saturn"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Finding)

    def test_id_grammar(self):
        from app.reading.computations.remedies.daan import recommend_daan

        result = recommend_daan(["Saturn"])
        assert result[0].id == "practitioner.remedies.daan.saturn"

    def test_classification_primitive(self):
        from app.reading.computations.remedies.daan import recommend_daan

        for planet in _PLANETS:
            r = recommend_daan([planet])
            assert r[0].classification == "primitive"

    def test_direction_positive(self):
        from app.reading.computations.remedies.daan import recommend_daan

        for planet in _PLANETS:
            r = recommend_daan([planet])
            assert r[0].direction == "positive"

    def test_verdict_max_140(self):
        from app.reading.computations.remedies.daan import recommend_daan

        for planet in _PLANETS:
            r = recommend_daan([planet])
            assert len(r[0].verdict) <= 140, (
                f"{planet}: verdict too long: {r[0].verdict!r}"
            )

    def test_rule_field(self):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan(["Saturn"])
        assert r[0].rule == "daan_remedy"

    def test_unknown_planet_raises(self):
        from app.reading.computations.remedies.daan import recommend_daan

        with pytest.raises(ValueError):
            recommend_daan(["Pluto"])
        with pytest.raises(ValueError):
            recommend_daan(["saturn"])


# ---------------------------------------------------------------------------
# Canonical content
# ---------------------------------------------------------------------------


class TestCanonicalContent:

    @pytest.mark.parametrize("planet,weekday", list(_EXPECTED_WEEKDAYS.items()))
    def test_weekday_in_evidence(self, planet, weekday):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan([planet])
        weekday_evidence = next(
            (e for e in r[0].evidence if e.startswith("weekday=")),
            None,
        )
        assert weekday_evidence == f"weekday={weekday}", (
            f"{planet}: expected weekday={weekday}, got {weekday_evidence!r}"
        )

    @pytest.mark.parametrize(
        "planet,recipient", list(_EXPECTED_RECIPIENTS.items()),
    )
    def test_recipient_in_evidence(self, planet, recipient):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan([planet])
        recipient_evidence = next(
            (e for e in r[0].evidence if e.startswith("recipient=")),
            None,
        )
        assert recipient_evidence is not None, (
            f"{planet} missing recipient= evidence"
        )
        assert recipient.lower() in recipient_evidence.lower(), (
            f"{planet}: expected recipient {recipient!r} in evidence, "
            f"got {recipient_evidence!r}"
        )

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_items_in_evidence(self, planet):
        """Each Finding must list the donation items in an items= line."""
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan([planet])
        items_evidence = next(
            (e for e in r[0].evidence if e.startswith("items=")),
            None,
        )
        assert items_evidence is not None, (
            f"{planet} missing items= evidence"
        )
        # The items line must be non-empty (more than just "items=")
        assert len(items_evidence) > len("items="), (
            f"{planet}: items= evidence is empty"
        )

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_doctrine_sentinel(self, planet):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan([planet])
        doctrine = next(
            (e for e in r[0].evidence if e.startswith("doctrine=")),
            None,
        )
        assert doctrine is not None, f"{planet} missing doctrine sentinel"
        assert "practitioner" in doctrine.lower()


# ---------------------------------------------------------------------------
# Specific high-signal items (verbatim from the table)
# ---------------------------------------------------------------------------


class TestSaturnDaan:
    """Saturn daan: black sesame, mustard oil, iron — to poor/elderly."""

    def test_saturn_verdict_mentions_black_sesame(self):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan(["Saturn"])
        verdict_lower = r[0].verdict.lower()
        items_evidence = next(
            (e for e in r[0].evidence if e.startswith("items=")),
            "",
        )
        haystack = (verdict_lower + " " + items_evidence.lower())
        assert "sesame" in haystack or "til" in haystack

    def test_saturn_recipient_poor(self):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan(["Saturn"])
        recipient_evidence = next(
            (e for e in r[0].evidence if e.startswith("recipient=")),
            "",
        )
        assert "poor" in recipient_evidence.lower()


class TestJupiterDaan:
    """Jupiter daan: yellow items, chana dal, gold / Thursday / teachers."""

    def test_jupiter_evidence_yellow(self):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan(["Jupiter"])
        items_evidence = next(
            (e for e in r[0].evidence if e.startswith("items=")),
            "",
        )
        assert "yellow" in items_evidence.lower()


# ---------------------------------------------------------------------------
# Public table re-export
# ---------------------------------------------------------------------------


class TestDaanTable:

    def test_table_exists_and_has_9_planets(self):
        from app.reading.computations.remedies.daan import DAAN_TABLE

        assert set(DAAN_TABLE.keys()) == set(_PLANETS)

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_table_cell_has_keys(self, planet):
        """Every cell must have items, weekday, and recipient."""
        from app.reading.computations.remedies.daan import DAAN_TABLE

        cell = DAAN_TABLE[planet]
        assert "items" in cell
        assert "weekday" in cell
        assert "recipient" in cell
        assert cell["items"]  # non-empty
        assert cell["weekday"]
        assert cell["recipient"]


# ---------------------------------------------------------------------------
# Multi-planet & ordering
# ---------------------------------------------------------------------------


class TestMultiPlanetAndOrdering:

    def test_order_preserved(self):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan(["Saturn", "Jupiter", "Mars"])
        ids = [f.id for f in r]
        assert ids == [
            "practitioner.remedies.daan.saturn",
            "practitioner.remedies.daan.jupiter",
            "practitioner.remedies.daan.mars",
        ]

    def test_duplicates_deduplicated(self):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan(["Saturn", "Saturn", "Mars"])
        ids = [f.id for f in r]
        assert ids == [
            "practitioner.remedies.daan.saturn",
            "practitioner.remedies.daan.mars",
        ]

    def test_all_9_planets(self):
        from app.reading.computations.remedies.daan import recommend_daan

        r = recommend_daan(list(_PLANETS))
        assert len(r) == 9
