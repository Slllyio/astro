"""Drik Bala — aspectual strength component of Shadbala.

Reference: B.V. Raman, Graha & Bhava Balas, Chapter 8 (Drik Bala).

Usage:
    python -m app.raman_saab.primitives.shadbala.drik
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart

# Visesha (special) aspect: (lo, hi) arc window -> bonus Shashtiamsas, GBB-8:172-191.
_VISESHA: Final[dict[str, list[tuple[float, float, float]]]] = {
    "Mars": [(90, 120, 15.0), (210, 240, 15.0)],
    "Jupiter": [(120, 150, 30.0), (240, 270, 30.0)],
    "Saturn": [(60, 90, 45.0), (270, 300, 45.0)],
}
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})  # + waning Moon, bad Mercury


def dristi_value(K: float) -> float:
    """Sripathi piecewise aspect strength (Shashtiamsas) for separation K (degrees).

    Verified continuous against Raman's anchors:
      30->0, 60->15, 90->45, 150->0, 180->60, 300->0.
    The 30-60 branch is (K-30)/2 — NOT K-30 (a common extraction error).
    """
    K %= 360.0
    if 30 <= K < 60:    return (K - 30) / 2.0
    if 60 <= K < 90:    return (K - 60) + 15.0
    if 90 <= K < 120:   return 45.0 - (K - 90) / 2.0
    if 120 <= K < 150:  return 150.0 - K
    if 150 <= K < 180:  return (K - 150) * 2.0
    if 180 <= K <= 300: return (300.0 - K) / 2.0
    return 0.0


def _is_malefic(planet: str, chart: RamanChart) -> bool:
    """Computable v1 benefic/malefic split (GBB-8).

    Malefics: Sun, Mars, Saturn, waning Moon.
    Benefics: Jupiter, Venus, waxing Moon, Mercury (Mercury-with-malefic refinement deferred to Phase 1c-3).
    """
    if planet in _MALEFICS:
        return True
    if planet == "Moon" and "Sun" in chart.planets:           # waning Moon = malefic
        sep = (chart.planets["Moon"].lon - chart.planets["Sun"].lon) % 360.0
        return sep > 180.0
    return False                                              # Jupiter, Venus, waxing Moon, Mercury: benefic


def drik_bala(planet: str, chart: RamanChart) -> float:
    """Aspectual strength in Shashtiamsas = (signed Dristi Pinda) / 4 (GBB-8:241).

    Benefic aspects add, malefic subtract; Mars/Jupiter/Saturn add Visesha Dristi.

    Note: Mercury's "well/badly associated" refinement is deferred to Phase 1c-3.
    Waning Moon is treated as malefic by phase computation (Sun present in chart).
    """
    if planet not in chart.planets:
        return 0.0
    target = chart.planets[planet].lon
    pinda = 0.0
    for other, p in chart.planets.items():
        if other == planet or other in ("Rahu", "Ketu"):
            continue
        K = (target - p.lon) % 360.0
        val = dristi_value(K)
        for lo, hi, bonus in _VISESHA.get(other, []):
            if lo <= K < hi:
                val += bonus
        if val == 0.0:
            continue
        pinda += -val if _is_malefic(other, chart) else val
    return round(pinda / 4.0, 3)
