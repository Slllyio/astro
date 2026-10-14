"""Saravali's planet-in-house grid (ch.30) — the allied doctrine BPHS itself lacks.

BPHS gives lords-in-houses (ch.24); Saravali gives the 7-graha x 12-house effect grid. These pin
that the grid is complete (84 cells), every cell resolves to a real Saravali line, the block
arithmetic lands each planet's houses in order (proven by effect content, not the OCR-damaged
in-text digits), and the render-time house-phrase repair fixes exactly the corrupted-digit cells
while leaving verbatim text otherwise untouched.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.saravali_grids import (
    all_house_effects,
    normalize_house_phrase,
    planet_in_house,
)
from app.parashara.doctrine.sources import verify

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


class TestGridCoverage:
    def test_full_84_cell_grid(self):
        g = all_house_effects()
        assert len(g) == 84                      # 7 grahas x 12 houses
        for p in _GRAHAS:
            for h in range(1, 13):
                assert (p, h) in g, (p, h)

    def test_every_citation_resolves(self):
        for s in all_house_effects().values():
            assert verify(s.source)

    def test_every_cell_has_text(self):
        for s in all_house_effects().values():
            assert s.text.strip()

    def test_all_cite_saravali_30(self):
        for s in all_house_effects().values():
            assert s.source.work == "SARAVALI-30"


class TestBlockArithmetic:
    """The mapping is by position; the 8th-house Mars sloka proves it (effect = longevity/death)."""

    def test_mars_eighth_is_short_lived(self):
        # sl.33 prints "9h" (OCR of 8th); its effect — short-lived, deformed body — is the 8th house.
        assert "short-lived" in planet_in_house("Mars", 8).text

    def test_mars_seventh_is_about_the_wife(self):
        # sl.32's digit was destroyed ("?h"); "lose his wife" is unmistakably the 7th house.
        assert "wife" in planet_in_house("Mars", 7).text

    def test_sun_first_is_the_ascendant(self):
        assert "Ascendant" in planet_in_house("Sun", 1).text

    def test_saturn_twelfth_is_last_cell(self):
        assert "12th" in planet_in_house("Saturn", 12).text


class TestHousePhraseRepair:
    @pytest.mark.parametrize("planet,house", [
        ("Mars", 6), ("Mars", 7), ("Mars", 8), ("Sun", 7),
        ("Jupiter", 5), ("Jupiter", 6), ("Venus", 5),
    ])
    def test_corrupted_digit_cells_read_the_right_house(self, planet, house):
        fixed = normalize_house_phrase(planet_in_house(planet, house).text, house)
        # the leading clause now names the true house, not the OCR digit
        assert f"{house}th" in fixed.split(",")[0]

    def test_correct_digit_left_verbatim(self):
        # Moon-9th already prints "9h"; repair must not rewrite a correct cell.
        raw = planet_in_house("Moon", 9).text
        assert normalize_house_phrase(raw, 9) == raw

    def test_ascendant_wording_left_verbatim(self):
        raw = planet_in_house("Sun", 1).text
        assert normalize_house_phrase(raw, 1) == raw

    def test_no_comma_returns_unchanged(self):
        assert normalize_house_phrase("no clause here", 5) == "no clause here"


class TestGuards:
    def test_bad_planet_raises(self):
        with pytest.raises(ValueError):
            planet_in_house("Rahu", 1)

    def test_bad_house_raises(self):
        with pytest.raises(ValueError):
            planet_in_house("Sun", 13)
