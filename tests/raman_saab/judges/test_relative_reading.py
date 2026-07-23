"""Derivative-house relative reading — `judges/relative_reading.py`.

Pins the Bhavat-Bhavam rotation on Track-B synthetic charts (no swisseph): each relative's
kāraka-house becomes their lagna, derived matters count from it, and a malefic in a derived house
raises the affliction note. Each test states the derivative-house fact it checks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.judges.relative_reading import (
    build_family_derivative_reading, build_relative_reading)


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    """Track-B chart from explicit longitudes; asc_lon 5.0 -> Aries ascendant (sign 1)."""
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


class TestRelativeReading:
    def test_relative_base_houses(self) -> None:
        """The relative's lagna is their kāraka-house: mother=4th, father=9th, spouse=7th."""
        c = _chart({"Sun": 5.0})
        assert build_relative_reading(c, "mother").base_house == 4
        assert build_relative_reading(c, "father").base_house == 9
        assert build_relative_reading(c, "spouse").base_house == 7

    def test_mothers_longevity_is_the_8th_from_the_4th(self) -> None:
        """The mother's longevity = the 8th-from-4th = the native's 11th house."""
        r = build_relative_reading(_chart({"Sun": 5.0}), "mother")
        longevity = next(m for m in r.matters if m.matter == "longevity")
        assert longevity.offset == 8 and longevity.native_house == 11

    def test_malefic_in_a_derived_house_raises_affliction(self) -> None:
        """Saturn in the native's 11th (= the mother's derived longevity house) -> an affliction
        note on that matter."""
        c = _chart({"Saturn": 305.0})   # Aquarius -> the 11th from an Aries lagna
        r = build_relative_reading(c, "mother")
        longevity = next(m for m in r.matters if m.matter == "longevity")
        assert "Saturn" in longevity.occupants
        assert longevity.affliction is not None

    def test_spouse_carries_the_raman_explicit_anchor(self) -> None:
        """The spouse reading cites Raman's own 7th-from-7th maraka rotation (RAMAN_EXPLICIT)."""
        r = build_relative_reading(_chart({"Sun": 5.0}), "spouse")
        assert any(n.provenance == "RAMAN_EXPLICIT" for n in r.notes)

    def test_unknown_role_raises(self) -> None:
        """An unknown relative role is a hard error (no silent default)."""
        with pytest.raises(ValueError):
            build_relative_reading(_chart({"Sun": 5.0}), "cousin")

    def test_family_reading_covers_five_relatives(self) -> None:
        """The family reading rotates all five relatives."""
        fr = build_family_derivative_reading(_chart({"Sun": 5.0}))
        assert {r.role for r in fr.relatives} == {"mother", "father", "spouse", "sibling", "child"}


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_relative_surface(self) -> None:
        """The D1 verdict path imports nothing from this surface — ratchet untouched."""
        import app.raman_saab.judges.house_template as ht
        assert "relative_reading" not in Path(ht.__file__).read_text(encoding="utf-8")
