"""Panchanga (five limbs of Vedic time) tests.

Pinned baseline: **Bangalore 1990-07-15 12:00 IST** (UTC 06:30).
That date was a Sunday, with the Moon near 356.32 deg sidereal Lahiri
(Revati nakshatra). Tithi/yoga formulas are sanity-checked against the
same formulas applied to engine longitudes -- a structural cross-check
that the panchanga module implements the formula correctly, not a
self-validating tautology, because the engine is the independently
verified source of truth for sidereal longitudes.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from app.core.ephemeris_engine import calculate_d1_position, calculate_jd
from app.core.panchanga import (
    KARANA_MOVABLE,
    YOGA_NAMES,
    compute_panchanga,
)


# ---------------------------------------------------------------------------
# Pinned moment: 1990-07-15 12:00 IST in Bangalore
# ---------------------------------------------------------------------------

# IST = UTC+5:30. Hour=12 local + tz_offset=5.5 -> 06:30 UTC.
BANGALORE_JD = calculate_jd(1990, 7, 15, 12.0, 5.5)


# ---------------------------------------------------------------------------
# Vara (weekday): pinned externally-verifiable dates.
# ---------------------------------------------------------------------------


def test_vara_1990_07_15_is_sunday() -> None:
    result = compute_panchanga(BANGALORE_JD)
    assert result["vara"]["name"] == "Sunday"
    # Mapping for ``int(jd + 1.5) % 7`` is 0=Sunday..6=Saturday
    # (verified against pinned external dates).
    assert result["vara"]["index"] == 0


def test_vara_known_monday() -> None:
    # 1990-07-16 12:00 IST -- the day after the pinned Sunday.
    jd = calculate_jd(1990, 7, 16, 12.0, 5.5)
    result = compute_panchanga(jd)
    assert result["vara"]["name"] == "Monday"
    assert result["vara"]["index"] == 1


def test_vara_known_saturday() -> None:
    # 2000-01-01 12:00 UTC was a Saturday.
    jd = calculate_jd(2000, 1, 1, 12.0, 0.0)
    result = compute_panchanga(jd)
    assert result["vara"]["name"] == "Saturday"
    assert result["vara"]["index"] == 6


# ---------------------------------------------------------------------------
# Tithi: cross-check formula application (NOT engine self-validation -- the
# engine is the trusted source for sidereal longitudes; we only verify that
# panchanga applies the standard formula on top correctly).
# ---------------------------------------------------------------------------


def test_tithi_matches_formula_on_engine_longitudes() -> None:
    sun_lon = calculate_d1_position(BANGALORE_JD, swe.SUN)["longitude"]
    moon_lon = calculate_d1_position(BANGALORE_JD, swe.MOON)["longitude"]
    expected_index = int(((moon_lon - sun_lon) % 360) / 12)

    result = compute_panchanga(BANGALORE_JD)
    assert result["tithi"]["index"] == expected_index
    # Sanity bounds.
    assert 0 <= result["tithi"]["index"] <= 29
    assert result["tithi"]["paksha"] in ("Shukla", "Krishna")


# ---------------------------------------------------------------------------
# Yoga: same cross-check approach.
# ---------------------------------------------------------------------------


def test_yoga_matches_formula_on_engine_longitudes() -> None:
    sun_lon = calculate_d1_position(BANGALORE_JD, swe.SUN)["longitude"]
    moon_lon = calculate_d1_position(BANGALORE_JD, swe.MOON)["longitude"]
    expected_index = int(((sun_lon + moon_lon) % 360) / (360.0 / 27))

    result = compute_panchanga(BANGALORE_JD)
    assert result["yoga"]["index"] == expected_index
    assert result["yoga"]["name"] == YOGA_NAMES[expected_index]


# ---------------------------------------------------------------------------
# Nakshatra: pinned Moon position from external tooling.
# ---------------------------------------------------------------------------


def test_nakshatra_1990_07_15_bangalore_is_revati() -> None:
    result = compute_panchanga(BANGALORE_JD)
    nak = result["nakshatra"]
    assert nak["index"] == 26
    assert nak["name"] == "Revati"


# ---------------------------------------------------------------------------
# Tithi boundary tests (synthetic Sun/Moon longitudes via monkeypatching).
#
# We patch the engine call inside ``app.core.panchanga`` so we can drive the
# tithi/karana logic with arbitrary deltas without depending on the ephemeris.
# The ``_FAKE_SUN``/``_FAKE_MOON`` pair is wired so that
# (moon - sun) % 360 == ``delta``.
# ---------------------------------------------------------------------------


def _patch_sun_moon(monkeypatch: pytest.MonkeyPatch, delta_deg: float) -> None:
    """Stub ``calculate_d1_position`` inside ``app.core.panchanga``.

    Returns a constant Sun longitude of 0 deg and Moon longitude of
    ``delta_deg`` (mod 360), so the panchanga module sees
    ``(moon - sun) % 360 == delta_deg``.
    """
    sun_lon = 0.0
    moon_lon = delta_deg % 360.0

    def fake_calculate_d1_position(jd: float, planet_id: int) -> dict:
        if planet_id == swe.SUN:
            return {"longitude": sun_lon}
        if planet_id == swe.MOON:
            return {"longitude": moon_lon}
        raise AssertionError(f"unexpected planet id: {planet_id}")

    monkeypatch.setattr(
        "app.core.panchanga.calculate_d1_position",
        fake_calculate_d1_position,
    )


# Index 0 -> delta in [0, 12); pick the midpoint.
def test_tithi_index_0_is_pratipada_shukla(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 6.0)
    result = compute_panchanga(jd=0.0)
    assert result["tithi"]["index"] == 0
    assert result["tithi"]["name"] == "Pratipada"
    assert result["tithi"]["paksha"] == "Shukla"


# Index 14 -> delta in [168, 180); midpoint 174.
def test_tithi_index_14_is_purnima_shukla(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 174.0)
    result = compute_panchanga(jd=0.0)
    assert result["tithi"]["index"] == 14
    assert result["tithi"]["name"] == "Purnima"
    assert result["tithi"]["paksha"] == "Shukla"


# Index 15 -> delta in [180, 192); midpoint 186.
def test_tithi_index_15_is_pratipada_krishna(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 186.0)
    result = compute_panchanga(jd=0.0)
    assert result["tithi"]["index"] == 15
    assert result["tithi"]["name"] == "Pratipada"
    assert result["tithi"]["paksha"] == "Krishna"


# Index 29 -> delta in [348, 360); midpoint 354.
def test_tithi_index_29_is_amavasya_krishna(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 354.0)
    result = compute_panchanga(jd=0.0)
    assert result["tithi"]["index"] == 29
    assert result["tithi"]["name"] == "Amavasya"
    assert result["tithi"]["paksha"] == "Krishna"


# ---------------------------------------------------------------------------
# Karana boundary tests
# ---------------------------------------------------------------------------


# Index 0 -> delta in [0, 6); Kimstughna.
def test_karana_index_0_is_kimstughna(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 3.0)
    result = compute_panchanga(jd=0.0)
    assert result["karana"]["index"] == 0
    assert result["karana"]["name"] == "Kimstughna"


# Index 1 -> delta in [6, 12); first movable karana = Bava.
def test_karana_index_1_is_bava(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 9.0)
    result = compute_panchanga(jd=0.0)
    assert result["karana"]["index"] == 1
    assert result["karana"]["name"] == "Bava"
    assert KARANA_MOVABLE[0] == "Bava"


# Index 8 -> delta in [48, 54); cycle wrap: (8-1) % 7 == 0 -> Bava again.
def test_karana_index_8_is_bava_after_cycle_wrap(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 51.0)
    result = compute_panchanga(jd=0.0)
    assert result["karana"]["index"] == 8
    assert result["karana"]["name"] == "Bava"


# Index 57 -> delta in [342, 348); Shakuni.
def test_karana_index_57_is_shakuni(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 345.0)
    result = compute_panchanga(jd=0.0)
    assert result["karana"]["index"] == 57
    assert result["karana"]["name"] == "Shakuni"


# Index 58 -> delta in [348, 354); Chatushpada.
def test_karana_index_58_is_chatushpada(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 351.0)
    result = compute_panchanga(jd=0.0)
    assert result["karana"]["index"] == 58
    assert result["karana"]["name"] == "Chatushpada"


# Index 59 -> delta in [354, 360); Naga.
def test_karana_index_59_is_naga(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_sun_moon(monkeypatch, 357.0)
    result = compute_panchanga(jd=0.0)
    assert result["karana"]["index"] == 59
    assert result["karana"]["name"] == "Naga"


# ---------------------------------------------------------------------------
# Result-shape sanity check.
# ---------------------------------------------------------------------------


def test_panchanga_result_has_all_five_limbs() -> None:
    result = compute_panchanga(BANGALORE_JD)
    for key in ("tithi", "karana", "yoga", "vara", "nakshatra"):
        assert key in result, f"missing limb: {key}"
    # Each limb must expose at least an index + name.
    for key in ("tithi", "karana", "yoga", "vara", "nakshatra"):
        assert "index" in result[key]
        assert "name" in result[key]
