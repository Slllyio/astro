"""Yoga routes — a fired yoga moves only the house and sub-matter its own text names.

Consideration 4 (HTJAH-I:480-482) ties a yoga to "any particular house or houses". These pin
the 2026-10-21 fix of the kind-only wiring (MERGE_VERDICT_REVIEW_2026-10-21.md).
"""
from __future__ import annotations

from app.raman_saab.doctrine.yoga_routes import YOGA_ROUTES, routes_to
from app.raman_saab.doctrine.yogas import YOGAS


class TestTheRoutesNameRealMatters:
    def test_every_routed_id_is_an_encoded_yoga(self):
        """No route points at a yoga id that does not exist (a typo would silently mute it)."""
        ids = {y.id for y in YOGAS}
        assert set(YOGA_ROUTES) <= ids

    def test_only_modulating_kinds_are_routed(self):
        """A route on a lunar/other-kind yoga would be dead weight: only dhana/raja/arishta move."""
        kinds = {y.id: y.kind for y in YOGAS}
        assert {kinds[i] for i in YOGA_ROUTES} <= {"dhana", "raja", "arishta"}


class TestTheReviewedFixes:
    def test_bhagya_reaches_fortune_not_gains(self):
        """Bhagya is a 9th-house yoga (3HCC:7989-7990); it never reaches the H11 gains floor."""
        assert routes_to("Y.BHAGYA", 9, "fortune")
        assert not routes_to("Y.BHAGYA", 11, "gains")

    def test_progeny_curses_reach_h5_never_h1(self):
        """Sarpasapa / Pitrusapa / Kalanirdesat print the loss of issues — H5, not the self."""
        for yid in ("Y.SARPASAPA", "Y.PITRUSAPA_SUTAKSHAYA", "Y.KALANIRDESAT_PUTRANASA"):
            assert routes_to(yid, 5, "children"), yid
            for key in ("self", "body", "health"):
                assert not routes_to(yid, 1, key), (yid, key)

    def test_wealth_yogas_never_reach_friends_or_speech(self):
        """Wealth reach is H2 wealth and H11 gains/acquisitions only."""
        for yid in ("Y.LAKSHMI", "Y.VISHNU", "Y.DHANA.EXCH", "Y.DHANA.CHAIN"):
            assert routes_to(yid, 11, "gains") and routes_to(yid, 2, "wealth"), yid
            assert not routes_to(yid, 11, "friends"), yid
            assert not routes_to(yid, 11, "elder_siblings"), yid
            assert not routes_to(yid, 2, "speech"), yid

    def test_merged_raja_yogas_modulate_nothing(self):
        """3HCC:8580-8584 conditions a raja yoga on "inherent vitality" and gives no test of it."""
        for y in YOGAS:
            if y.kind == "raja" and y.source.work.startswith("3HC"):
                assert y.id not in YOGA_ROUTES, y.id

    def test_unrouted_yoga_reaches_nothing(self):
        """A yoga absent from the table modulates nothing."""
        assert not routes_to("Y.RAJA_258", 10, "career")
        assert not routes_to("Y.KALATRASHANDA", 1, "self")
