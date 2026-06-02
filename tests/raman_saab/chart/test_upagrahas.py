"""Tests for Gulika & Mandi upagrahas (Task 4 — Phase 1b).

Structural test: signs are valid (1..12), longitudes in [0, 360).
External pin: EXPECTED_SIGN is left None — see report for status.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.chart import upagrahas as u

# Canonical baseline: Bangalore 1990-07-15 12:00 IST, lat 12.97, lon 77.59
_BLR = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


def test_gulika_mandi_return_points_in_valid_signs() -> None:
    """Gulika and Mandi must return SpecialPoints with valid sign numbers and longitudes."""
    g = u.gulika(_BLR, ayanamsa="raman")
    m = u.mandi(_BLR, ayanamsa="raman")
    assert g.name == "Gulika" and 1 <= g.sign <= 12 and 0.0 <= g.lon < 360.0
    assert m.name == "Mandi" and 1 <= m.sign <= 12 and 0.0 <= m.lon < 360.0


def test_gulika_and_mandi_are_distinct() -> None:
    """Gulika (start) and Mandi (end) of Saturn's part must produce different longitudes."""
    g = u.gulika(_BLR, ayanamsa="raman")
    m = u.mandi(_BLR, ayanamsa="raman")
    # They are separated by ~1/8 of the day arc; longitudes must differ.
    assert g.lon != m.lon


def test_gulika_navamsa_sign_is_valid() -> None:
    """navamsa_sign must be in 1..12."""
    g = u.gulika(_BLR, ayanamsa="raman")
    assert 1 <= g.navamsa_sign <= 12


@pytest.mark.external_pin
def test_gulika_sign_matches_reference() -> None:
    """PIN: external reference Gulika sign for the Bangalore baseline.

    Status: UNRESOLVED — external source (drikpanchang.com / Jagannatha Hora)
    could not be queried during this session.  Computed Gulika sign = 8 (Scorpio)
    for the Bangalore 1990-07-15 12:00 IST baseline using the day-birth,
    Sunday lord (Sun, index 0), Saturn at part index 6 formula.

    To resolve: check drikpanchang.com or Jagannatha Hora for this chart's
    Gulika sign and fill EXPECTED_SIGN below.  If it disagrees, adjust
    start-vs-end convention or day/night sequence offset in upagrahas.py.
    """
    g = u.gulika(_BLR, ayanamsa="raman")
    EXPECTED_SIGN: int | None = None  # <-- fill from external source to pin
    if EXPECTED_SIGN is not None:
        assert g.sign == EXPECTED_SIGN
