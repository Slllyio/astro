"""Per-worker initializer for the Stage 2 ETL multiprocessing pool.

CRITICAL CORRECTNESS NOTE
─────────────────────────
pyswisseph keeps ayanamsa state and ephemeris path in C-extension globals
that DO NOT transfer across process boundaries. `multiprocessing.Pool`
forks fresh Python interpreters; each worker starts with the C-extension
defaults (tropical zodiac, no ephemeris path set).

Skipping this initializer = silent corruption: every per-row computation
in workers would use TROPICAL longitudes while the main process believes
it's running sidereal Lahiri. The math still produces valid numbers, just
shifted by ~23.85° (the current ayanamsa). The dataset would train an ML
model that lies.

This module is the single seam where that risk is contained. Run it as
the `initializer` argument to `multiprocessing.Pool`.
"""
from __future__ import annotations

import swisseph as swe


def init_worker() -> None:
    """Configure per-process pyswisseph state. Must be the `initializer`
    argument when constructing the multiprocessing Pool."""
    # Use built-in Moshier ephemeris (no external SE files required, ~6"
    # accuracy across the historical date range we care about).
    swe.set_ephe_path(None)
    # Lahiri sidereal — the project-wide Vedic ayanamsa convention.
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def assert_lahiri_active() -> None:
    """Sanity check: confirm the current process has Lahiri sidereal set.

    Used in tests to prove the worker initializer ran correctly, AND
    callable defensively in CLI scripts to fail loudly if the user
    forgot the initializer. The ayanamsa for J2000.0 (JD 2451545.0)
    under Lahiri is ~23.85°; under no ayanamsa (tropical), it's 0.0.
    """
    j2000 = 2451545.0
    ayanamsa = swe.get_ayanamsa_ut(j2000)
    if ayanamsa < 23.0:
        raise RuntimeError(
            f"Lahiri sidereal mode is not active in this process. "
            f"Ayanamsa at J2000 reads {ayanamsa:.4f}, expected ~23.85. "
            f"Did you forget to call init_worker()?"
        )
