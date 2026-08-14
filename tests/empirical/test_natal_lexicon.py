"""Lexicon coverage and provenance: the vocabulary is total, typed and bannered.

The epistemic point: the decoder's invariant "every facet is non-empty for any
chart" rests entirely on the lexicon's accessor functions being *total* over
their domains. These tests prove that by iteration, not by trust — all 120
planet-sign pairs, all 120 planet-house pairs, every bespoke key — and pin the
provenance banner to the measured null it must keep disclosing.
"""

from __future__ import annotations

import itertools

from app.empirical.natal import lexicon
from app.empirical.natal.lexicon import (
    ASPECT_BESPOKE,
    ASPECT_TONES,
    ELEMENT_TEMPERAMENT,
    FACETS,
    HOUSE_DOMAINS,
    MODALITY_TEMPERAMENT,
    PLANET_ROLES,
    PLANET_SIGN_BESPOKE,
    SIGN_PROFILES,
    SIGN_RULERS,
    SIGNS,
    TRADITION_BANNER,
    aspect_meaning,
    planet_in_house,
    planet_in_sign,
)


class TestTables:
    """The base tables are complete and internally consistent."""

    def test_twelve_sign_profiles_matching_zodiacal_arithmetic(self):
        """Each profile's element/modality equals the index % 4 / % 3 rule."""
        assert set(SIGN_PROFILES) == set(SIGNS)
        elements = ("fire", "earth", "air", "water")
        modalities = ("cardinal", "fixed", "mutable")
        for i, sign in enumerate(SIGNS):
            profile = SIGN_PROFILES[sign]
            assert profile.element == elements[i % 4]
            assert profile.modality == modalities[i % 3]
            assert profile.keywords and profile.attitude and profile.aptitude and profile.work

    def test_ten_planet_roles_with_valid_facets(self):
        """All ten trait planets present; every declared facet is a real facet."""
        assert len(PLANET_ROLES) == 10
        assert "TrueNode" not in PLANET_ROLES
        for role in PLANET_ROLES.values():
            assert role.facets and set(role.facets) <= set(FACETS)

    def test_twelve_house_domains_with_work_keywords_only_on_working_houses(self):
        """Houses 1..12 present; vocational keywords confined to 2, 6 and 10."""
        assert set(HOUSE_DOMAINS) == set(range(1, 13))
        for num, dom in HOUSE_DOMAINS.items():
            assert dom.facets and set(dom.facets) <= set(FACETS)
            assert bool(dom.work_keywords) == (num in (2, 6, 10))

    def test_sign_rulers_total_and_planet_valued(self):
        """Every sign has exactly one modern ruler drawn from the trait planets."""
        assert set(SIGN_RULERS) == set(SIGNS)
        assert set(SIGN_RULERS.values()) <= set(PLANET_ROLES)

    def test_temperament_lines_cover_all_elements_and_modalities(self):
        """Four element lines, three modality lines, none blank."""
        assert set(ELEMENT_TEMPERAMENT) == {"fire", "earth", "air", "water"}
        assert set(MODALITY_TEMPERAMENT) == {"cardinal", "fixed", "mutable"}
        assert all(ELEMENT_TEMPERAMENT.values()) and all(MODALITY_TEMPERAMENT.values())

    def test_aspect_tones_cover_the_five_ptolemaic_aspects(self):
        """conjunction/sextile/square/trine/opposition all have tone templates."""
        assert set(ASPECT_TONES) == {"conjunction", "sextile", "square", "trine", "opposition"}


class TestCoverage:
    """The accessor functions are total — the decoder's non-empty invariant."""

    def test_planet_in_sign_total_over_all_120_pairs(self):
        """Every planet x sign returns at least one facet with phrases."""
        for planet, sign in itertools.product(PLANET_ROLES, SIGNS):
            meanings = planet_in_sign(planet, sign)
            assert meanings, (planet, sign)
            assert all(phrases for phrases in meanings.values()), (planet, sign)
            assert set(meanings) <= set(FACETS), (planet, sign)

    def test_planet_in_house_total_over_all_120_pairs(self):
        """Every planet x house returns at least one facet with phrases."""
        for planet, house in itertools.product(PLANET_ROLES, range(1, 13)):
            meanings = planet_in_house(planet, house)
            assert meanings, (planet, house)
            assert all(phrases for phrases in meanings.values()), (planet, house)
            assert set(meanings) <= set(FACETS), (planet, house)

    def test_aspect_meaning_total_and_order_insensitive(self):
        """Any trait-planet pair and Ptolemaic aspect resolves, either order."""
        planets = list(PLANET_ROLES)
        for a, b in itertools.combinations(planets, 2):
            for aspect in ASPECT_TONES:
                forward = aspect_meaning(a, b, aspect)
                backward = aspect_meaning(b, a, aspect)
                assert forward == backward
                assert forward and set(forward) <= set(FACETS)

    def test_bespoke_sign_keys_are_valid_and_bespoke_adds_to_composed(self):
        """Bespoke keys reference real planets/signs/facets; the bespoke phrase
        appears in the accessor's output on top of the composed base."""
        for (planet, sign), entry in PLANET_SIGN_BESPOKE.items():
            assert planet in PLANET_ROLES and sign in SIGNS
            merged = planet_in_sign(planet, sign)
            for facet, phrases in entry.items():
                assert facet in FACETS
                for phrase in phrases:
                    assert phrase in merged[facet]

    def test_bespoke_aspect_keys_are_valid_and_canonically_ordered(self):
        """Aspect bespoke keys use real bodies in DEFAULT_BODIES order."""
        order = list(PLANET_ROLES)
        for (a, b, aspect), entry in ASPECT_BESPOKE.items():
            assert a in PLANET_ROLES and b in PLANET_ROLES
            assert order.index(a) < order.index(b), (a, b)
            assert aspect in ASPECT_TONES
            assert entry and all(set(e) <= set(FACETS) for e in [entry])

    def test_sun_moon_mercury_bespoke_complete_across_the_zodiac(self):
        """The three bespoke planets each carry all twelve sign entries."""
        for planet in ("Sun", "Moon", "Mercury"):
            covered = {sign for (p, sign) in PLANET_SIGN_BESPOKE if p == planet}
            assert covered == set(SIGNS), planet


class TestProvenance:
    """The banner travels with the vocabulary and keeps disclosing the null."""

    def test_banner_names_the_tag_and_the_measured_null(self):
        """The banner carries the provenance tag, denies predictive advantage,
        and points at the measurement record."""
        assert TRADITION_BANNER.startswith("WESTERN_TRADITION")
        assert "no predictive advantage" in TRADITION_BANNER
        assert "TIME_BASIS_CONFOUND.md" in TRADITION_BANNER

    def test_facets_are_the_seven_requested_in_fixed_order(self):
        """The facet tuple is exactly the user's seven asks, order pinned."""
        assert FACETS == (
            "personality", "characteristics", "attitude", "aptitude",
            "intelligence", "work_style", "work_area",
        )

    def test_module_exports_everything_it_declares(self):
        """__all__ is honest — every named symbol exists."""
        for name in lexicon.__all__:
            assert hasattr(lexicon, name), name
