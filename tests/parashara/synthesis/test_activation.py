"""Activation engine — the four-tier fructification, house-influence, and node-safe association.

Pins the timing logic that mirrors the locked "When Do Indications Fructify" method in pure BPHS.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.parashara.synthesis.activation import bhukti_tier, influences, lords_associated


def _chart(asc_sign: int, signs: dict[str, int]) -> SimpleNamespace:
    """A minimal duck-typed chart: the activation functions read only asc_sign + longitudes."""
    return SimpleNamespace(asc_sign=asc_sign,
                           longitudes={p: (s - 1) * 30 + 5.0 for p, s in signs.items()})


class TestBhuktiTier:
    def test_both_influence_and_associated_is_par_excellence(self):
        """Both period-lords time the house and are associated -> par excellence."""
        assert bhukti_tier(True, True, True) == "par excellence"

    def test_both_influence_not_associated_is_ordinary(self):
        """Both time the house but are not associated -> ordinary."""
        assert bhukti_tier(True, True, False) == "ordinary"

    def test_only_bhukti_lord_is_limited(self):
        """Only the antardasa lord times the house -> limited."""
        assert bhukti_tier(False, True, False) == "limited"

    def test_only_maha_lord_is_feeble(self):
        """Only the mahadasa lord times the house -> feeble."""
        assert bhukti_tier(True, False, False) == "feeble"

    def test_neither_is_no_window(self):
        """Neither period-lord times the house -> not a window."""
        assert bhukti_tier(False, False, False) is None


class TestInfluences:
    def test_owner_influences_its_house(self):
        """A graha lording a house influences it (Aries lagna: Mars lords the 1st)."""
        signs = {"Mars": 8}
        assert influences(_chart(1, signs), "Mars", 1, signs=signs)

    def test_occupant_influences_its_house(self):
        """A graha occupying a house influences it."""
        signs = {"Jupiter": 5}                                  # sign 5 = the 5th from Aries
        assert influences(_chart(1, signs), "Jupiter", 5, signs=signs)

    def test_seventh_aspect_influences(self):
        """Every graha aspects the 7th from itself, so it influences that house."""
        signs = {"Venus": 1}                                    # in Aries; aspects sign 7 (the 7th)
        assert influences(_chart(1, signs), "Venus", 7, signs=signs)

    def test_node_casts_no_aspect_influence(self):
        """A node casts no drishti: Rahu in the 1st does not aspect-influence the 7th."""
        signs = {"Rahu": 1}                                     # owns/occupies neither the 7th nor its lord
        assert not influences(_chart(1, signs), "Rahu", 7, signs=signs)


class TestLordsAssociated:
    def test_conjunction_associates(self):
        """Two grahas in the same rasi are associated."""
        signs = {"Sun": 5, "Mercury": 5}
        assert lords_associated(_chart(1, signs), "Sun", "Mercury", signs=signs)

    def test_mutual_aspect_associates(self):
        """Opposition (the 7th) is a mutual full aspect, so the pair is associated."""
        signs = {"Sun": 1, "Saturn": 7}
        assert lords_associated(_chart(1, signs), "Sun", "Saturn", signs=signs)

    def test_node_associates_by_being_aspected(self):
        """A graha can aspect a node: Sun opposite Rahu associates them (Sun casts, Rahu receives)."""
        signs = {"Rahu": 1, "Sun": 7}
        assert lords_associated(_chart(1, signs), "Rahu", "Sun", signs=signs)

    def test_two_nodes_opposed_do_not_associate(self):
        """Neither node casts drishti, so an opposition of the two nodes is not association."""
        signs = {"Rahu": 1, "Ketu": 7}
        assert not lords_associated(_chart(1, signs), "Rahu", "Ketu", signs=signs)
