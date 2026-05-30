"""Tests for ``app.reading.computations.remedies.mantras``.

Doctrine source: classical Vedic remedies tradition + practitioner field
wisdom. The Beej (seed) mantra table assigns each of the 9 planets a
single-syllable seed-mantra string, a recommended completion count, and
a weekday of practice. The recommender returns one Finding per afflicted
planet — recommendations only, never judgments.

Canonical table (verbatim, do NOT vary transliteration):

  +---------+-----------------------------------------------+--------+----------+
  | Planet  | Mantra                                        | Reps   | Weekday  |
  +=========+===============================================+========+==========+
  | Sun     | Om Hraam Hreem Hraum Sah Suryaya Namah        |   7000 | Sunday   |
  | Moon    | Om Shraam Shreem Shraum Sah Chandraya Namah   |  11000 | Monday   |
  | Mars    | Om Kraam Kreem Kraum Sah Bhaumaya Namah       |  10000 | Tuesday  |
  | Mercury | Om Braam Breem Braum Sah Budhaya Namah        |   9000 | Wednesday|
  | Jupiter | Om Graam Greem Graum Sah Gurave Namah         |  19000 | Thursday |
  | Venus   | Om Draam Dreem Draum Sah Shukraya Namah       |  16000 | Friday   |
  | Saturn  | Om Praam Preem Praum Sah Shanaye Namah        |  23000 | Saturday |
  | Rahu    | Om Bhraam Bhreem Bhraum Sah Rahave Namah      |  18000 | Saturday |
  | Ketu    | Om Sraam Sreem Sraum Sah Ketave Namah         |  17000 | Saturday |
  +---------+-----------------------------------------------+--------+----------+

ID grammar: ``practitioner.remedies.mantra.<planet>`` (planet lowercased).
classification: ``"primitive"`` (recommendation, not judgment).
direction: ``"neutral"`` (mantras are remedial neutral by classical doctrine).
"""
from __future__ import annotations

import pytest


_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


_EXPECTED_MANTRAS = {
    "Sun":     ("Om Hraam Hreem Hraum Sah Suryaya Namah",     7000,  "Sunday"),
    "Moon":    ("Om Shraam Shreem Shraum Sah Chandraya Namah", 11000, "Monday"),
    "Mars":    ("Om Kraam Kreem Kraum Sah Bhaumaya Namah",    10000, "Tuesday"),
    "Mercury": ("Om Braam Breem Braum Sah Budhaya Namah",      9000, "Wednesday"),
    "Jupiter": ("Om Graam Greem Graum Sah Gurave Namah",      19000, "Thursday"),
    "Venus":   ("Om Draam Dreem Draum Sah Shukraya Namah",    16000, "Friday"),
    "Saturn":  ("Om Praam Preem Praum Sah Shanaye Namah",     23000, "Saturday"),
    "Rahu":    ("Om Bhraam Bhreem Bhraum Sah Rahave Namah",   18000, "Saturday"),
    "Ketu":    ("Om Sraam Sreem Sraum Sah Ketave Namah",      17000, "Saturday"),
}


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestRecommendMantrasShape:
    """Construction / type / id / classification invariants."""

    def test_empty_afflicted_planets_returns_empty_list(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras([])
        assert result == []

    def test_returns_finding_list(self):
        from app.reading.computations.remedies.mantras import recommend_mantras
        from app.reading.schema import Finding

        result = recommend_mantras(["Saturn"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Finding)

    def test_one_finding_per_afflicted_planet(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras(["Saturn", "Mars", "Rahu"])
        assert len(result) == 3

    def test_id_grammar_lowercased_planet(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras(["Saturn"])
        assert result[0].id == "practitioner.remedies.mantra.saturn"

    def test_classification_is_primitive(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        for planet in _PLANETS:
            result = recommend_mantras([planet])
            assert result[0].classification == "primitive", (
                f"{planet} mantra classification != 'primitive'"
            )

    def test_direction_is_neutral(self):
        """Mantras are recommendations, not benefic/malefic judgments."""
        from app.reading.computations.remedies.mantras import recommend_mantras

        for planet in _PLANETS:
            result = recommend_mantras([planet])
            assert result[0].direction == "neutral"

    def test_verdict_under_140_chars(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        for planet in _PLANETS:
            result = recommend_mantras([planet])
            assert len(result[0].verdict) <= 140, (
                f"{planet} verdict={result[0].verdict!r} too long"
            )

    def test_rule_field(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras(["Jupiter"])
        assert result[0].rule == "mantra_remedy"

    def test_unknown_planet_raises(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        with pytest.raises(ValueError):
            recommend_mantras(["Pluto"])
        with pytest.raises(ValueError):
            recommend_mantras(["sun"])  # exact case required


# ---------------------------------------------------------------------------
# Canonical table verification — every cell pinned literally
# ---------------------------------------------------------------------------


class TestMantraCanonicalTable:
    """Every planet's mantra text, rep count, and weekday must match the
    classical table EXACTLY. Transliteration variants are NOT permitted."""

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_mantra_text_matches_table(self, planet):
        from app.reading.computations.remedies.mantras import recommend_mantras

        expected_text, _, _ = _EXPECTED_MANTRAS[planet]
        result = recommend_mantras([planet])
        assert expected_text in result[0].verdict, (
            f"{planet}: mantra text {expected_text!r} missing from verdict "
            f"{result[0].verdict!r}"
        )

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_rep_count_in_verdict_and_evidence(self, planet):
        from app.reading.computations.remedies.mantras import recommend_mantras

        _, expected_reps, _ = _EXPECTED_MANTRAS[planet]
        result = recommend_mantras([planet])
        assert str(expected_reps) in result[0].verdict, (
            f"{planet}: rep count {expected_reps} not in verdict"
        )
        # And in evidence as canonical machine-readable line
        reps_evidence = next(
            (e for e in result[0].evidence if e.startswith("reps=")),
            None,
        )
        assert reps_evidence == f"reps={expected_reps}", (
            f"{planet}: expected 'reps={expected_reps}' evidence, "
            f"got {reps_evidence!r}"
        )

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_weekday_in_evidence(self, planet):
        from app.reading.computations.remedies.mantras import recommend_mantras

        _, _, expected_weekday = _EXPECTED_MANTRAS[planet]
        result = recommend_mantras([planet])
        weekday_evidence = next(
            (e for e in result[0].evidence if e.startswith("weekday=")),
            None,
        )
        assert weekday_evidence == f"weekday={expected_weekday}", (
            f"{planet}: expected 'weekday={expected_weekday}', "
            f"got {weekday_evidence!r}"
        )

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_doctrine_sentinel_in_evidence(self, planet):
        """All findings must declare doctrine source per project convention."""
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras([planet])
        doctrine_line = next(
            (e for e in result[0].evidence if e.startswith("doctrine=")),
            None,
        )
        assert doctrine_line is not None, (
            f"{planet} missing doctrine= evidence"
        )
        assert "classical" in doctrine_line.lower()


# ---------------------------------------------------------------------------
# Public table re-export
# ---------------------------------------------------------------------------


class TestBeejMantraTable:
    """The ``BEEJ_MANTRA_TABLE`` module constant must be exposed and
    contain exactly the 9 classical planets."""

    def test_table_exists_and_has_9_planets(self):
        from app.reading.computations.remedies.mantras import BEEJ_MANTRA_TABLE

        assert set(BEEJ_MANTRA_TABLE.keys()) == set(_PLANETS)

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_table_cell_matches_expected(self, planet):
        from app.reading.computations.remedies.mantras import BEEJ_MANTRA_TABLE

        cell = BEEJ_MANTRA_TABLE[planet]
        expected_text, expected_reps, expected_weekday = _EXPECTED_MANTRAS[planet]
        assert cell["mantra"] == expected_text
        assert cell["reps"] == expected_reps
        assert cell["weekday"] == expected_weekday


# ---------------------------------------------------------------------------
# Multi-planet & order preservation
# ---------------------------------------------------------------------------


class TestMultiPlanetAndOrdering:
    """The recommender must preserve input order and not deduplicate."""

    def test_order_is_preserved(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras(["Saturn", "Jupiter", "Mars"])
        ids = [f.id for f in result]
        assert ids == [
            "practitioner.remedies.mantra.saturn",
            "practitioner.remedies.mantra.jupiter",
            "practitioner.remedies.mantra.mars",
        ]

    def test_duplicates_deduplicated(self):
        """Repeated planets in the input collapse to one Finding."""
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras(["Saturn", "Saturn", "Mars"])
        ids = [f.id for f in result]
        assert ids == [
            "practitioner.remedies.mantra.saturn",
            "practitioner.remedies.mantra.mars",
        ]

    def test_all_9_planets_at_once(self):
        from app.reading.computations.remedies.mantras import recommend_mantras

        result = recommend_mantras(list(_PLANETS))
        assert len(result) == 9
        ids = {f.id for f in result}
        expected = {f"practitioner.remedies.mantra.{p.lower()}" for p in _PLANETS}
        assert ids == expected
