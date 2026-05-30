"""Tests for ``app.reading.computations.remedies.yantras``.

Doctrine source: Practitioner field-wisdom (foresightbypriyanka, dkscore,
traditional almanacs). Yantras are geometric diagrams installed at home
to pacify a planet. Each graha has a canonical Sanskrit-named yantra and
a traditional installation direction/placement (e.g. north wall, copper
plate, weekly washing with milk).

Canonical table:

  Sun     - Surya Yantra      / east wall   / copper plate
  Moon    - Chandra Yantra    / north-west  / silver plate
  Mars    - Mangal Yantra     / south       / copper plate
  Mercury - Budha Yantra      / north       / brass plate
  Jupiter - Guru Yantra       / north-east  / gold/yellow plate
  Venus   - Shukra Yantra     / south-east  / silver plate
  Saturn  - Shani Yantra      / west        / iron plate
  Rahu    - Rahu Yantra       / south-west  / mixed-metal plate
  Ketu    - Ketu Yantra       / south       / mixed-metal plate

ID grammar: ``practitioner.remedies.yantra.<planet>`` (planet lowercased).
classification: ``"primitive"``.
direction: ``"positive"``.
"""
from __future__ import annotations

import pytest


_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


_EXPECTED_YANTRA_NAMES = {
    "Sun":     "Surya Yantra",
    "Moon":    "Chandra Yantra",
    "Mars":    "Mangal Yantra",
    "Mercury": "Budha Yantra",
    "Jupiter": "Guru Yantra",
    "Venus":   "Shukra Yantra",
    "Saturn":  "Shani Yantra",
    "Rahu":    "Rahu Yantra",
    "Ketu":    "Ketu Yantra",
}


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestRecommendYantrasShape:

    def test_empty_input_returns_empty(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        assert recommend_yantras([]) == []

    def test_returns_finding_list(self):
        from app.reading.computations.remedies.yantras import recommend_yantras
        from app.reading.schema import Finding

        r = recommend_yantras(["Saturn"])
        assert isinstance(r, list)
        assert len(r) == 1
        assert isinstance(r[0], Finding)

    def test_id_grammar(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras(["Saturn"])
        assert r[0].id == "practitioner.remedies.yantra.saturn"

    def test_classification_primitive(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        for p in _PLANETS:
            r = recommend_yantras([p])
            assert r[0].classification == "primitive"

    def test_direction_positive(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        for p in _PLANETS:
            r = recommend_yantras([p])
            assert r[0].direction == "positive"

    def test_verdict_max_140(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        for p in _PLANETS:
            r = recommend_yantras([p])
            assert len(r[0].verdict) <= 140

    def test_rule_field(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras(["Saturn"])
        assert r[0].rule == "yantra_remedy"

    def test_unknown_planet_raises(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        with pytest.raises(ValueError):
            recommend_yantras(["Pluto"])
        with pytest.raises(ValueError):
            recommend_yantras(["saturn"])


# ---------------------------------------------------------------------------
# Canonical names
# ---------------------------------------------------------------------------


class TestCanonicalNames:

    @pytest.mark.parametrize(
        "planet,yantra_name", list(_EXPECTED_YANTRA_NAMES.items())
    )
    def test_yantra_name_in_verdict(self, planet, yantra_name):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras([planet])
        assert yantra_name in r[0].verdict, (
            f"{planet}: expected {yantra_name!r} in verdict, "
            f"got {r[0].verdict!r}"
        )

    @pytest.mark.parametrize(
        "planet,yantra_name", list(_EXPECTED_YANTRA_NAMES.items())
    )
    def test_yantra_name_in_evidence(self, planet, yantra_name):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras([planet])
        yantra_evidence = next(
            (e for e in r[0].evidence if e.startswith("yantra=")),
            None,
        )
        assert yantra_evidence == f"yantra={yantra_name}"

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_direction_in_evidence(self, planet):
        """The traditional installation direction is in evidence."""
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras([planet])
        placement_evidence = next(
            (e for e in r[0].evidence if e.startswith("placement=")),
            None,
        )
        assert placement_evidence is not None, (
            f"{planet} missing placement= evidence"
        )

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_doctrine_sentinel(self, planet):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras([planet])
        doctrine = next(
            (e for e in r[0].evidence if e.startswith("doctrine=")),
            None,
        )
        assert doctrine is not None
        assert "practitioner" in doctrine.lower()


# ---------------------------------------------------------------------------
# Yantra table
# ---------------------------------------------------------------------------


class TestYantraTable:

    def test_table_exists_and_has_9_planets(self):
        from app.reading.computations.remedies.yantras import YANTRA_TABLE

        assert set(YANTRA_TABLE.keys()) == set(_PLANETS)

    @pytest.mark.parametrize(
        "planet,name", list(_EXPECTED_YANTRA_NAMES.items())
    )
    def test_table_cell_name(self, planet, name):
        from app.reading.computations.remedies.yantras import YANTRA_TABLE

        assert YANTRA_TABLE[planet]["name"] == name

    @pytest.mark.parametrize("planet", _PLANETS)
    def test_table_cell_has_placement(self, planet):
        from app.reading.computations.remedies.yantras import YANTRA_TABLE

        assert "placement" in YANTRA_TABLE[planet]
        assert YANTRA_TABLE[planet]["placement"]


# ---------------------------------------------------------------------------
# Multi-planet & ordering
# ---------------------------------------------------------------------------


class TestMultiPlanetAndOrdering:

    def test_order_preserved(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras(["Saturn", "Jupiter"])
        ids = [f.id for f in r]
        assert ids == [
            "practitioner.remedies.yantra.saturn",
            "practitioner.remedies.yantra.jupiter",
        ]

    def test_duplicates_deduplicated(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras(["Saturn", "Saturn", "Mars"])
        assert [f.id for f in r] == [
            "practitioner.remedies.yantra.saturn",
            "practitioner.remedies.yantra.mars",
        ]

    def test_all_9_planets(self):
        from app.reading.computations.remedies.yantras import recommend_yantras

        r = recommend_yantras(list(_PLANETS))
        assert len(r) == 9
