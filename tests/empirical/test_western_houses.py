"""House-system pins, and the NULL contract at high latitude.

The load-bearing test in this file is
:meth:`TestPolarNull.test_placidus_returns_null_inside_polar_circle`. Swiss
Ephemeris does not fail loudly there — it substitutes Porphyry and sets an
error flag. Twelve plausible floats come back. Anything that treats them as
Placidus cusps produces a feature that is systematically wrong for exactly the
high-latitude subset of the corpus, and birth geography is already the
strongest chartless predictor available (lat/lon/date alone: AUC 0.744 on
marriage). A wrong-but-plausible geographic feature is the worst possible
input to this tournament, so the layer returns ``None`` instead.
"""

from __future__ import annotations

import swisseph as swe

from app.empirical.western.angles import separation
from app.empirical.western.houses import (
    HOUSE_SYSTEMS,
    QUADRANT_SYSTEMS,
    house_cusps,
    house_of,
)
from app.empirical.western.tropical import julian_day_ut

CANONICAL_JD = julian_day_ut(1990, 7, 15, 12.0 - 5.5)
BANGALORE = (12.97, 77.59)

# Well inside the Arctic circle: Tromsø, Norway.
TROMSO = (69.65, 18.96)


class TestCanonicalChart:
    """Pinned against the repo's externally-verified canonical baseline."""

    def test_sidereal_ascendant_matches_documented_virgo_lagna(self):
        """Tropical asc minus Lahiri ayanamsa reproduces the documented 173.99°.

        ``CLAUDE.md`` pins this chart to a sidereal Virgo lagna of ~173.99°,
        cross-checked against Prokerala and Jagannatha Hora. This validates the
        new tropical house layer against an external number, not against itself.
        """
        cusps = house_cusps(CANONICAL_JD, *BANGALORE, system="placidus")
        assert cusps is not None
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        _rc, ayanamsa = swe.get_ayanamsa_ex_ut(CANONICAL_JD, swe.FLG_SWIEPH)
        sidereal_asc = (cusps.ascendant - ayanamsa) % 360.0
        assert abs(sidereal_asc - 173.99) < 0.01, f"sidereal asc {sidereal_asc}°"

    def test_first_cusp_is_the_ascendant(self):
        """For every quadrant system, cusp 1 is the rising degree."""
        for system in ("placidus", "koch", "regiomontanus", "campanus"):
            cusps = house_cusps(CANONICAL_JD, *BANGALORE, system=system)
            assert cusps is not None
            assert separation(cusps.cusps[0], cusps.ascendant) < 1e-9

    def test_tenth_cusp_is_the_midheaven_for_quadrant_systems(self):
        """Placidus and Koch put the MC on cusp 10 by construction."""
        for system in ("placidus", "koch"):
            cusps = house_cusps(CANONICAL_JD, *BANGALORE, system=system)
            assert cusps is not None
            assert separation(cusps.cusps[9], cusps.midheaven) < 1e-9


class TestPolarNull:
    """Undefined must surface as NULL, never as a silent substitution."""

    def test_placidus_returns_null_inside_polar_circle(self):
        """Placidus is undefined at 69.65°N — the layer returns None."""
        assert house_cusps(CANONICAL_JD, *TROMSO, system="placidus") is None

    def test_koch_returns_null_inside_polar_circle(self):
        """Koch shares Placidus's dependence on the diurnal circles."""
        assert house_cusps(CANONICAL_JD, *TROMSO, system="koch") is None

    def test_whole_sign_still_defined_inside_polar_circle(self):
        """Sign-based systems never reference the horizon, so they stay defined."""
        cusps = house_cusps(CANONICAL_JD, *TROMSO, system="whole_sign")
        assert cusps is not None
        assert len(cusps.cusps) == 12

    def test_every_quadrant_system_is_declared(self):
        """The systems that can go NULL are exactly the horizon-dependent ones."""
        assert QUADRANT_SYSTEMS <= set(HOUSE_SYSTEMS)
        assert "whole_sign" not in QUADRANT_SYSTEMS
        assert "equal" not in QUADRANT_SYSTEMS


class TestHouseAssignment:
    """house_of must partition the circle, including across 0° Aries."""

    def test_every_body_lands_in_exactly_one_house(self):
        """Twelve cusps partition the circle: every longitude gets one house."""
        cusps = house_cusps(CANONICAL_JD, *BANGALORE, system="placidus")
        assert cusps is not None
        for tenth in range(3600):
            house = house_of(tenth / 10.0, cusps.cusps)
            assert 1 <= house <= 12

    def test_cusp_longitude_belongs_to_its_own_house(self):
        """A longitude exactly on cusp N is in house N, not house N-1."""
        cusps = house_cusps(CANONICAL_JD, *BANGALORE, system="placidus")
        assert cusps is not None
        for i, cusp in enumerate(cusps.cusps):
            assert house_of(cusp, cusps.cusps) == i + 1

    def test_house_spanning_zero_aries_is_handled(self):
        """Arc containment, not subtraction — a house crossing 0° still works."""
        # Cusps deliberately straddling the Aries point.
        cusps = tuple((350.0 + 30.0 * i) % 360.0 for i in range(12))
        assert house_of(355.0, cusps) == 1
        assert house_of(5.0, cusps) == 1
        assert house_of(25.0, cusps) == 2
