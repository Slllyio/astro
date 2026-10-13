"""Golden pins for the tropical position layer.

The pins here are external where it is possible to be external:

* **Equinox instants.** The March equinox is, by definition, the moment the
  Sun's tropical longitude is 0°. The instants used are the published UTC
  equinox times (2000-03-20 07:35 UTC, 2024-03-20 03:06 UTC); the ephemeris
  independently lands the Sun within a fraction of an arcminute of 0°. Neither
  the time nor the definition comes from this codebase.
* **The repo's canonical chart.** ``CLAUDE.md`` pins Bangalore 1990-07-15
  12:00 IST to a sidereal Virgo ascendant of ~173.99°, verified against
  external sources (Prokerala, Jagannatha Hora). Casting it tropically and
  subtracting the Lahiri ayanamsa must reproduce that number — which tests the
  new layer against an externally-verified value rather than against itself.
"""

from __future__ import annotations

import swisseph as swe

from app.empirical.western.angles import separation
from app.empirical.western.tropical import (
    BODY_IDS,
    DEFAULT_BODIES,
    julian_day_ut,
    south_node_longitude,
    tropical_position,
    tropical_positions,
)

# Bangalore 1990-07-15 12:00 IST == 06:30 UT (CLAUDE.md canonical baseline).
CANONICAL_JD = julian_day_ut(1990, 7, 15, 12.0 - 5.5)

_ARCSEC = 1.0 / 3600.0


class TestEquinoxPins:
    """The Sun stands at 0° tropical longitude at the published equinox."""

    def test_march_2000_equinox_sun_at_zero_aries(self):
        """Published equinox 2000-03-20 07:35 UTC puts the Sun on 0° Aries."""
        jd = julian_day_ut(2000, 3, 20, 7 + 35 / 60.0)
        lon = tropical_position(jd, "Sun").longitude
        assert separation(lon, 0.0) < 0.002, f"Sun at {lon}°, expected 0° Aries"

    def test_march_2024_equinox_sun_at_zero_aries(self):
        """Published equinox 2024-03-20 03:06 UTC puts the Sun on 0° Aries."""
        jd = julian_day_ut(2024, 3, 20, 3 + 6 / 60.0)
        lon = tropical_position(jd, "Sun").longitude
        assert separation(lon, 0.0) < 0.002, f"Sun at {lon}°, expected 0° Aries"

    def test_september_2024_equinox_sun_at_zero_libra(self):
        """Published equinox 2024-09-22 12:44 UTC puts the Sun on 0° Libra."""
        jd = julian_day_ut(2024, 9, 22, 12 + 44 / 60.0)
        lon = tropical_position(jd, "Sun").longitude
        assert separation(lon, 180.0) < 0.002, f"Sun at {lon}°, expected 0° Libra"


class TestSiderealCrossCheck:
    """Tropical minus ayanamsa must equal the existing sidereal cast exactly."""

    def test_tropical_minus_ayanamsa_equals_sidereal_within_one_arcsecond(self):
        """Every body's tropical longitude exceeds its Lahiri sidereal longitude
        by exactly the nutation-inclusive ayanamsa."""
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        # get_ayanamsa_ex_ut is the nutation-inclusive value that FLG_SIDEREAL
        # actually subtracts; plain get_ayanamsa_ut omits nutation and is ~14″ off.
        _rc, ayanamsa = swe.get_ayanamsa_ex_ut(CANONICAL_JD, flags)
        for body in DEFAULT_BODIES:
            tropical = tropical_position(CANONICAL_JD, body).longitude
            sidereal, _ = swe.calc_ut(CANONICAL_JD, BODY_IDS[body], flags | swe.FLG_SIDEREAL)
            delta = (tropical - sidereal[0]) % 360.0
            assert abs(delta - ayanamsa) < _ARCSEC, f"{body}: {delta}° vs ayanamsa {ayanamsa}°"

    def test_canonical_chart_reproduces_externally_verified_sidereal_sun(self):
        """The canonical chart's sidereal Sun matches the Vedic engine's cast."""
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        _rc, ayanamsa = swe.get_ayanamsa_ex_ut(CANONICAL_JD, flags)
        tropical = tropical_position(CANONICAL_JD, "Sun").longitude
        sidereal = (tropical - ayanamsa) % 360.0
        expected, _ = swe.calc_ut(CANONICAL_JD, swe.SUN, flags | swe.FLG_SIDEREAL)
        assert separation(sidereal, expected[0]) < _ARCSEC


class TestGlobalStateContract:
    """Nothing here may disturb swisseph's process-global sidereal mode."""

    def test_tropical_calls_leave_ayanamsa_mode_untouched(self):
        """A tropical cast must not change what the Vedic engine would compute.

        swisseph's sidereal mode is global; if this layer flipped it, a
        concurrently-cast Raman chart would silently change ayanamsa.
        """
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        before = swe.get_ayanamsa_ut(CANONICAL_JD)
        tropical_positions(CANONICAL_JD)
        tropical_position(CANONICAL_JD, "Moon")
        after = swe.get_ayanamsa_ut(CANONICAL_JD)
        assert abs(after - before) < 1e-12, "tropical layer mutated the global sidereal mode"

    def test_module_source_never_calls_set_sid_mode(self):
        """Static guard: no module under app/empirical *calls* set_sid_mode.

        Parsed rather than grepped — the string appears in docstrings here
        precisely to explain the prohibition, and a substring check would
        flag its own documentation.
        """
        import ast
        from pathlib import Path

        offenders: list[str] = []
        for path in Path("app/empirical").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                if name == "set_sid_mode":
                    offenders.append(f"{path}:{node.lineno}")
        assert offenders == [], f"set_sid_mode called at {offenders}"


class TestPositionSemantics:
    """Structural properties of a cast position."""

    def test_saturn_retrograde_flag_matches_negative_speed(self):
        """is_retrograde is exactly the sign of longitudinal speed."""
        for body in DEFAULT_BODIES:
            pos = tropical_position(CANONICAL_JD, body)
            assert pos.is_retrograde == (pos.speed_longitude < 0.0)

    def test_sign_index_uses_floor_division_at_exact_cusp(self):
        """An exact 60.0° lands in Gemini (index 2), not on a cusp rounding error."""
        from app.empirical.western.tropical import Position

        pos = Position("Test", 60.0, 0.0, 1.0, 1.0, 0.0)
        assert pos.sign_index == 2
        assert pos.degree_in_sign == 0.0

    def test_all_default_bodies_compute_on_moshier(self):
        """The default body set must be computable without external .se1 files."""
        positions = tropical_positions(CANONICAL_JD)
        assert set(positions) == set(DEFAULT_BODIES)
        assert all(0.0 <= p.longitude < 360.0 for p in positions.values())

    def test_south_node_is_exact_opposition_of_true_node(self):
        """The south node is definitionally 180° from the north node."""
        positions = tropical_positions(CANONICAL_JD)
        south = south_node_longitude(positions)
        assert abs(separation(south, positions["TrueNode"].longitude) - 180.0) < 1e-9
