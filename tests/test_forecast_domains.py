"""Unit tests for app.medini.forecast_domains.

Validates classical planet→domain mappings + the event-type dispatch logic
for ingresses, conjunctions, and eclipses.
"""
from __future__ import annotations

from app.medini.forecast_domains import (
    DOMAINS,
    annotate_events,
    describe_domain,
    domains_for_event,
    domains_for_planet,
)


class TestPlanetDomainTable:
    """Pin classical attributions so a future edit can't silently drop them."""

    def test_saturn_owns_labor_and_agriculture(self) -> None:
        d = domains_for_planet("Saturn")
        assert "labor" in d
        assert "agriculture" in d
        assert "politics" in d  # Saturn = the established order

    def test_mars_owns_military(self) -> None:
        d = domains_for_planet("Mars")
        assert d[0] == "military"  # primary domain

    def test_jupiter_owns_religion_finance_politics(self) -> None:
        d = domains_for_planet("Jupiter")
        assert {"religion", "finance", "politics"} <= set(d)

    def test_moon_owns_masses_and_public_sentiment(self) -> None:
        d = domains_for_planet("Moon")
        assert "masses" in d

    def test_rahu_owns_foreign_and_tech_disruption(self) -> None:
        """Rahu = the outer-world / disruption channel."""
        d = domains_for_planet("Rahu")
        assert "foreign" in d
        assert "tech_disruption" in d

    def test_unknown_planet_returns_empty(self) -> None:
        assert domains_for_planet("Pluto") == ()


class TestEventDispatch:
    """domains_for_event must dispatch correctly per event type."""

    def test_ingress_uses_single_planet(self) -> None:
        ev = {"type": "INGRESS", "planet": "Mars"}
        assert "military" in domains_for_event(ev)

    def test_station_uses_single_planet(self) -> None:
        ev = {"type": "STATION", "planet": "Jupiter"}
        assert "religion" in domains_for_event(ev)

    def test_conjunction_unions_both_planets(self) -> None:
        """Mars-Saturn must touch military (Mars) AND labor (Saturn)."""
        ev = {"type": "CONJUNCTION", "planet_a": "Mars", "planet_b": "Saturn"}
        d = set(domains_for_event(ev))
        assert "military" in d
        assert "labor" in d

    def test_conjunction_preserves_order_of_first_planet(self) -> None:
        """Insertion-ordered union — planet_a's domains come first."""
        ev = {"type": "CONJUNCTION", "planet_a": "Mars", "planet_b": "Venus"}
        d = domains_for_event(ev)
        assert d[0] == "military"  # Mars is planet_a, military is its primary

    def test_solar_eclipse_blends_sun_and_rahu(self) -> None:
        """Eclipses carry Rahu/Ketu shadow energy — solar = Sun + Rahu."""
        ev = {"type": "ECLIPSE", "family": "SOLAR", "subtype": "TOTAL"}
        d = set(domains_for_event(ev))
        # Sun domains
        assert "politics" in d
        # Rahu domains
        assert "foreign" in d

    def test_lunar_eclipse_blends_moon_and_rahu(self) -> None:
        ev = {"type": "ECLIPSE", "family": "LUNAR", "subtype": "PARTIAL"}
        d = set(domains_for_event(ev))
        assert "masses" in d   # Moon
        assert "foreign" in d  # Rahu

    def test_new_moon_uses_moon_domains(self) -> None:
        ev = {"type": "NEW_MOON", "planet": "Moon"}
        d = set(domains_for_event(ev))
        assert "masses" in d


class TestAnnotateEvents:
    def test_annotate_adds_domains_field(self) -> None:
        evs = [
            {"type": "INGRESS", "planet": "Saturn"},
            {"type": "CONJUNCTION", "planet_a": "Mars", "planet_b": "Saturn"},
        ]
        out = annotate_events(evs)
        for e in out:
            assert "domains" in e
            assert isinstance(e["domains"], list)

    def test_annotate_returns_new_dicts(self) -> None:
        """Immutability convention — caller's events untouched."""
        orig = {"type": "INGRESS", "planet": "Saturn"}
        annotate_events([orig])
        assert "domains" not in orig


class TestDomainCatalog:
    """The DOMAINS dict is the API contract for the /domains endpoint."""

    def test_every_domain_in_planet_map_exists_in_catalog(self) -> None:
        """No planet maps to a key that isn't in DOMAINS — otherwise the UI
        chips have no tooltip metadata."""
        from app.medini.forecast_domains import _PLANET_DOMAINS
        all_used = set()
        for keys in _PLANET_DOMAINS.values():
            all_used.update(keys)
        missing = all_used - set(DOMAINS.keys())
        assert not missing, f"keys used but not in DOMAINS: {missing}"

    def test_describe_domain_returns_full_metadata(self) -> None:
        d = describe_domain("finance")
        assert d is not None
        assert d["label"]
        assert d["description"]
        assert d["icon"]

    def test_describe_domain_unknown_returns_none(self) -> None:
        assert describe_domain("non-existent-key") is None
