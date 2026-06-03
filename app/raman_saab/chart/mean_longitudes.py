"""Mean longitudes + seegrochchas via Raman's epoch method (GBB-6:88-104).

Usage:
    python -m app.raman_saab.chart.mean_longitudes --jd 2421977.8681 --year 1918
"""
from __future__ import annotations

from typing import Final

import swisseph as swe

# ---------------------------------------------------------------------------
# Epoch: 1900-01-01 00:00 at 76°E Ujjain.
# In UT that is 76/360 day *earlier* than 00:00 UT (Ujjain is east of Greenwich).
# ---------------------------------------------------------------------------
_EPOCH_JD: Final[float] = swe.julday(1900, 1, 1, 0.0, swe.GREG_CAL) - 76.0 / 360.0

# (epoch longitude constant, daily mean motion °/day).
# Verified to reproduce Raman's GBB Standard Horoscope stated means to ≤0.12°.
_MEAN: Final[dict[str, tuple[float, float]]] = {
    "Sun":     (257.4568, 0.98560),
    "Mars":    (270.22,   0.52402),
    "Jupiter": (220.04,   0.08310),
    "Saturn":  (236.74,   0.03344),
}
_SEEG_INNER: Final[dict[str, tuple[float, float]]] = {
    "Mercury": (164.0,   4.0923),
    "Venus":   (328.51,  1.60214),
}


def interval_days(jd_ut: float) -> float:
    """Interval in days from the 76°E epoch (1900-01-01 00:00 Ujjain) to the birth moment (UT)."""
    return jd_ut - _EPOCH_JD


def mean_and_seeg_from_interval(interval: float, *, t: int) -> dict[str, dict[str, float]]:
    """Compute mean longitudes + seegrochchas using Raman's epoch method (GBB-6:88-104).

    Args:
        interval: Days from the 76°E epoch to birth (UT); use ``interval_days(jd_ut)``.
        t:        Birth year − 1900 (e.g. 18 for 1918).

    Returns:
        ``{"mean": {planet: deg, ...}, "seeg": {planet: deg, ...}}`` — all mod 360.
        Mean longitudes are sidereal in Raman's frame (consistent with the chart's
        true sidereal longitudes, so no ayanamsa enters the Cheshta arc).
    """
    mean: dict[str, float] = {p: (c + m * interval) % 360.0 for p, (c, m) in _MEAN.items()}

    # Year-dependent secular corrections (GBB-6:92-93)
    mean["Jupiter"] = (mean["Jupiter"] - (3.33 + 0.0067 * t)) % 360.0
    mean["Saturn"]  = (mean["Saturn"]  + (5.0  + 0.001  * t)) % 360.0

    # Inner planets: mean longitude = Mean Sun (GBB-6:97)
    mean["Mercury"] = mean["Venus"] = mean["Sun"]

    # Seegrochchas
    # Superior planets (Mars, Jupiter, Saturn): seegrochcha = Mean Sun
    seeg: dict[str, float] = {p: mean["Sun"] for p in ("Mars", "Jupiter", "Saturn")}

    # Inner planets: own seegrochcha formula with year correction
    seeg["Mercury"] = (
        _SEEG_INNER["Mercury"][0]
        + _SEEG_INNER["Mercury"][1] * interval
        + (6.67 - 0.00133 * t)
    ) % 360.0
    seeg["Venus"] = (
        _SEEG_INNER["Venus"][0]
        + _SEEG_INNER["Venus"][1] * interval
        - (5.0 + 0.001 * t)
    ) % 360.0

    return {"mean": mean, "seeg": seeg}


def mean_longitudes(jd_ut: float, year: int) -> dict[str, dict[str, float]]:
    """Convenience wrapper: mean longitudes + seegrochchas for a birth JD (UT) and civil year."""
    return mean_and_seeg_from_interval(interval_days(jd_ut), t=year - 1900)
