"""Tests for app.medini.astrocartography.compute_planetary_lines.

Astrocartography lines are deterministic celestial geometry. The Bangalore
1990-07-15 12:00 IST baseline is reused from the rest of the test suite as
the canonical pinning anchor.
"""
from __future__ import annotations

import math

import pytest
import swisseph as swe

from app.medini.astrocartography import (
    _BASE_PLANETS,
    _normalize_longitude,
    compute_planetary_lines,
)


# Bangalore 1990-07-15 12:00 IST = UTC 06:30. Same baseline pinned in
# test_dasha_dates.py / test_lagna.py / test_persistence.py.
BANGALORE_JD = swe.julday(1990, 7, 15, 6.5, swe.GREG_CAL)


@pytest.fixture(scope="module")
def bangalore_lines() -> list[dict]:
    return compute_planetary_lines(BANGALORE_JD)


# ---------- Shape invariants ----------

def test_total_line_count_is_36(bangalore_lines: list[dict]) -> None:
    """4 angles (MC, IC, Asc, Desc) x 9 grahas = 36 lines."""
    assert len(bangalore_lines) == 36


def test_each_planet_has_4_lines(bangalore_lines: list[dict]) -> None:
    by_planet: dict[str, int] = {}
    for line in bangalore_lines:
        by_planet[line["planet"]] = by_planet.get(line["planet"], 0) + 1
    assert sorted(by_planet) == sorted(
        ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]
    )
    assert all(c == 4 for c in by_planet.values())


def test_each_line_has_valid_coords(bangalore_lines: list[dict]) -> None:
    for line in bangalore_lines:
        assert len(line["coords"]) >= 2, f"{line['planet']}-{line['angle']} should have multiple points"
        for lat, lon in line["coords"]:
            assert -90.0 <= lat <= 90.0, f"lat {lat} out of range"
            assert -180.0 <= lon <= 180.0, f"lon {lon} out of range"


def test_angle_values_are_complete(bangalore_lines: list[dict]) -> None:
    angles = {line["angle"] for line in bangalore_lines}
    assert angles == {"MC", "IC", "Asc", "Desc"}


# ---------- MC/IC: vertical lines (constant longitude) ----------

def test_mc_line_is_vertical(bangalore_lines: list[dict]) -> None:
    """MC lines are at constant longitude — varying latitude only."""
    sun_mc = next(l for l in bangalore_lines if l["planet"] == "Sun" and l["angle"] == "MC")
    longitudes = {round(c[1], 6) for c in sun_mc["coords"]}
    assert len(longitudes) == 1, f"Sun-MC should have constant lon, got {longitudes}"


def test_ic_is_180_opposite_mc(bangalore_lines: list[dict]) -> None:
    """For each planet, IC line should be at MC longitude + 180° (mod 360)."""
    for planet in ("Sun", "Moon", "Mars", "Jupiter", "Saturn"):
        mc = next(l for l in bangalore_lines if l["planet"] == planet and l["angle"] == "MC")
        ic = next(l for l in bangalore_lines if l["planet"] == planet and l["angle"] == "IC")
        mc_lon = mc["coords"][0][1]
        ic_lon = ic["coords"][0][1]
        # Expected IC lon = (MC + 180) normalized to [-180, 180]
        expected = _normalize_longitude(mc_lon + 180.0)
        assert abs(ic_lon - expected) < 1e-6, (
            f"{planet}: MC={mc_lon}, IC={ic_lon}, expected_IC={expected}"
        )


def test_bangalore_sun_mc_near_indian_subcontinent(bangalore_lines: list[dict]) -> None:
    """At noon-IST in Bangalore, the Sun is near the upper meridian, so its
    MC line should fall near India's longitude (~78° E). Solar noon vs civil
    noon offset puts it within ~15° of 78°."""
    sun_mc = next(l for l in bangalore_lines if l["planet"] == "Sun" and l["angle"] == "MC")
    lon = sun_mc["coords"][0][1]
    assert 60.0 <= lon <= 95.0, f"Sun-MC should be near India (~78E), got {lon}"


# ---------- Ketu opposite Rahu invariant ----------

def test_ketu_mc_is_180_opposite_rahu_mc(bangalore_lines: list[dict]) -> None:
    """Ketu (south node) is Rahu reflected: its MC line should sit 180° from
    Rahu's MC. Equivalently, Ketu-MC should equal Rahu-IC."""
    rahu_mc = next(l for l in bangalore_lines if l["planet"] == "Rahu" and l["angle"] == "MC")
    ketu_mc = next(l for l in bangalore_lines if l["planet"] == "Ketu" and l["angle"] == "MC")
    rahu_lon = rahu_mc["coords"][0][1]
    ketu_lon = ketu_mc["coords"][0][1]
    expected = _normalize_longitude(rahu_lon + 180.0)
    assert abs(ketu_lon - expected) < 1e-6


# ---------- Asc/Desc curves: latitude span and circumpolar truncation ----------

def test_asc_curve_spans_mid_latitudes(bangalore_lines: list[dict]) -> None:
    """Asc lines should sample mid-latitudes; circumpolar zones (where
    |tan(phi)*tan(dec)| > 1) are skipped, so the curve doesn't reach the
    poles. Expect at least 30 sample points for any planet's Asc."""
    sun_asc = next(l for l in bangalore_lines if l["planet"] == "Sun" and l["angle"] == "Asc")
    assert len(sun_asc["coords"]) >= 30


def test_asc_and_desc_are_distinct_curves(bangalore_lines: list[dict]) -> None:
    """At any given latitude, Asc and Desc are at different longitudes (they
    are the eastern-rising and western-setting lines respectively)."""
    sun_asc = next(l for l in bangalore_lines if l["planet"] == "Sun" and l["angle"] == "Asc")
    sun_desc = next(l for l in bangalore_lines if l["planet"] == "Sun" and l["angle"] == "Desc")
    asc_by_lat = {round(c[0], 4): c[1] for c in sun_asc["coords"]}
    desc_by_lat = {round(c[0], 4): c[1] for c in sun_desc["coords"]}
    common = set(asc_by_lat) & set(desc_by_lat)
    assert common, "Asc and Desc should share some sampled latitudes"
    for lat in common:
        assert abs(asc_by_lat[lat] - desc_by_lat[lat]) > 1e-3, (
            f"Asc and Desc identical at lat {lat}"
        )


# ---------- Determinism ----------

def test_compute_is_deterministic() -> None:
    """Same JD must produce identical lines on every call."""
    a = compute_planetary_lines(BANGALORE_JD)
    b = compute_planetary_lines(BANGALORE_JD)
    assert a == b


# ---------- Helper functions ----------

@pytest.mark.parametrize("input_lon,expected", [
    (0.0, 0.0),
    (180.0, -180.0),    # 180 wraps to -180
    (-180.0, -180.0),
    (361.0, 1.0),
    (-361.0, -1.0),
    (540.0, -180.0),    # 540 → 180 → -180
])
def test_normalize_longitude(input_lon: float, expected: float) -> None:
    assert math.isclose(_normalize_longitude(input_lon), expected, abs_tol=1e-9)


def test_base_planets_table_has_8_entries() -> None:
    """Sun, Moon, 5 classical planets, Rahu = 8. Ketu is derived from Rahu
    inside compute_planetary_lines, so it is NOT in the BASE_PLANETS table."""
    assert len(_BASE_PLANETS) == 8
    assert "Ketu" not in _BASE_PLANETS
    assert "Rahu" in _BASE_PLANETS


# ---------- Segment continuity (2026-08-05) ----------
#
# The bug these guard: the module computed segment splits at antimeridian crossings
# and circumpolar gaps, then flattened them back into one polyline and threw the
# splits away. Leaflet then drew a straight line across the break — a horizontal
# streak spanning the whole map. Measured on a real natal moment it produced three
# (Venus Desc jumped -179.99 -> +165.95). Nothing caught it, because every existing
# test checks counts, verticality and opposition, all of which a stitched line
# satisfies. Continuity was the one unchecked property.

from app.medini.astrocartography import _ASC_DESC_LAT_STEP  # noqa: E402

# A natal moment with planets near the dateline, so the antimeridian path is live.
DATELINE_JD = swe.julday(1989, 10, 12, 4.533, swe.GREG_CAL)   # Mainpuri, UT


@pytest.mark.parametrize("jd", [BANGALORE_JD, DATELINE_JD])
def test_no_segment_jumps_the_antimeridian(jd: float) -> None:
    """Within a segment, consecutive points must never jump >180 deg of longitude.

    A jump that large is the renderer being told to draw the long way round the
    globe, which is the streak this fix removes."""
    for line in compute_planetary_lines(jd):
        for s_i, seg in enumerate(line["segments"]):
            for (_la1, lo1), (_la2, lo2) in zip(seg, seg[1:]):
                assert abs(lo2 - lo1) <= 180.0, (
                    f"{line['planet']}-{line['angle']} segment {s_i} jumps the "
                    f"antimeridian: {lo1:.2f} -> {lo2:.2f}"
                )


@pytest.mark.parametrize("jd", [BANGALORE_JD, DATELINE_JD])
def test_no_segment_skips_a_circumpolar_gap(jd: float) -> None:
    """Within a segment, latitude must advance by exactly one sample step.

    A larger stride means the segment spans latitudes where the planet is
    circumpolar (never rises or sets), so the drawn line passes through a region
    where no such point exists."""
    for line in compute_planetary_lines(jd):
        if line["angle"] not in ("Asc", "Desc"):
            continue
        for s_i, seg in enumerate(line["segments"]):
            for (la1, _lo1), (la2, _lo2) in zip(seg, seg[1:]):
                assert abs(la2 - la1) <= _ASC_DESC_LAT_STEP, (
                    f"{line['planet']}-{line['angle']} segment {s_i} skips a "
                    f"circumpolar gap: lat {la1} -> {la2}"
                )


def test_segments_partition_coords_exactly() -> None:
    """`segments` must be a lossless re-grouping of `coords` — no point invented,
    dropped or reordered. `coords` stays flattened for existing consumers, so the
    two views have to agree."""
    for line in compute_planetary_lines(DATELINE_JD):
        flat = [pt for seg in line["segments"] for pt in seg]
        # single-point runs are dropped from segments (undrawable), so segments
        # may be a subsequence of coords, never a superset or a reordering
        assert len(flat) <= len(line["coords"])
        it = iter(line["coords"])
        assert all(pt in it for pt in flat), (
            f"{line['planet']}-{line['angle']}: segments are not an ordered "
            f"subsequence of coords"
        )


def test_the_dateline_chart_actually_exercises_the_antimeridian() -> None:
    """Guard the guard, and the clearest statement of the bug.

    If this natal moment ever stopped crossing the dateline, the continuity tests
    above would keep passing while testing nothing. So assert the crossing is real:
    the flattened `coords` (kept as-is for existing consumers) still contains the raw
    >180 deg jump, and `segments` — the view renderers draw — contains none. That gap
    between the two IS the fix.

    Note the split can leave a 1-point run on the far side, which is dropped from
    `segments` because a polyline needs two points; that is why this asserts on the
    jump rather than on a segment count."""
    lines = compute_planetary_lines(DATELINE_JD)
    flat_jumps = sum(
        1 for l in lines
        for a, b in zip(l["coords"], l["coords"][1:]) if abs(b[1] - a[1]) > 180.0
    )
    assert flat_jumps >= 1, (
        "this natal moment no longer crosses the antimeridian — the continuity "
        "tests would be vacuous; pick a moment that does"
    )
    seg_jumps = sum(
        1 for l in lines for s in l["segments"]
        for a, b in zip(s, s[1:]) if abs(b[1] - a[1]) > 180.0
    )
    assert seg_jumps == 0, "segments must never contain the jump that coords does"
