"""Degree-resolved strength features — the real-birth degree engine (M1).

The sign-only scorer in ``house_judgment.py`` reads whole-sign placement and
per-sign dignity even when handed exact longitudes, so a genuinely
degree-accurate chart scores identically to its sign reconstruction. This module
supplies the degree-resolved quantities the scorer is blind to, and is invoked
**only for ``chart.degree_resolved`` charts** (real printed longitudes). For
sign-reconstructed charts (pada-midpoint longitudes) none of this runs, so the
established sign numbers and the ch. IV anchor are byte-identical.

Every quantity here is doctrinally fixed (BPHS / classical Shadbala), not fit to
any corpus; the weights reuse or are pinned to the scorer's existing ``_DIGNITY_W``
magnitudes. Three features, each targeting a documented miss of the sign engine:

1. **Bhāva-chalita placement** (``chalit_houses``) — Sripati cusps. A planet the
   whole-sign map puts in the 8th but which sits within ±15° of the 7th/9th cusp
   is re-classed to the bhāva it actually occupies. Attacks the dusthāna
   under-score (any 8th placement read as weakening).
2. **Degree-graded dignity** (``dignity_depth_delta``, ``moolatrikona_finding``) —
   deep vs shallow exaltation/debilitation by Uccha-bala, and moolatrikona as a
   tier above ordinary own-sign. Attacks the benefic over-credit.
3. **Combustion** (``combustion_finding``) — an astangata planet, orb-graded,
   loses strength. A phenomenon the sign engine cannot see at all.
"""
from __future__ import annotations

from app.core.dignity import EXALTATION, is_moolatrikona
from app.core.planet_state import COMBUSTION_ORBS, angular_separation, is_combust
from app.reading.computations.bhava_chalit import _chalit_bhava

# BPHS deep-exaltation (paramoccha) degrees, as absolute sidereal longitude of the
# exact uchcha point: Sun 10° Aries, Moon 3° Taurus, Mars 28° Capricorn, Mercury
# 15° Virgo, Jupiter 5° Cancer, Venus 27° Pisces, Saturn 20° Libra.
DEEP_EXALT_DEG: dict[str, float] = {
    "Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0,
    "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0,
}

# Combustion weight: astangata is a real debility the scorer's whole-sign
# Sun-conjunction (-0.7) under-states. Pinned to the inimical-dignity magnitude and
# orb-graded (deepest at exact conjunction, zero at the combustion boundary), so it
# never double-counts more than the classical loss.
_COMBUST_W = -0.8
# Moolatrikona sits between own-sign (1.2) and exaltation (1.6): the root-trine is
# stronger than plain own-sign. A single fixed tier, not fit.
_MOOLATRIKONA_W = 1.4
_OWN_W = 1.2


def _sep_from_deep_exalt(planet: str, lon: float) -> float | None:
    """Angular distance (0..180°) of ``lon`` from the planet's exact exaltation
    degree. None for Rahu/Ketu (no classical exaltation degree)."""
    deep = DEEP_EXALT_DEG.get(planet)
    if deep is None:
        return None
    return angular_separation(lon, deep)


def uccha_bala(planet: str, lon: float) -> float | None:
    """Classical Uccha-bala normalised to [0,1]: 1.0 at the exact exaltation
    degree, 0.0 at the exact debilitation degree (180° away), linear between."""
    sep = _sep_from_deep_exalt(planet, lon)
    if sep is None:
        return None
    return 1.0 - sep / 180.0


def dignity_depth_delta(planet: str, sign: int, lon: float) -> float:
    """Degree refinement of a SIGN-level exaltation/debilitation, as a delta to add
    to the flat dignity finding (0.0 when not in the exalt/debil sign or when depth
    matches the flat grade). Shallow exaltation (near the far edge of the exalt
    sign) is credited less than the flat +1.6; deep debilitation, penalised more.

    The flat weight is scaled by the within-sign Uccha fraction, re-normalised so a
    planet at the exact exalt/debil degree keeps the full flat magnitude and one at
    the opposite sign edge tapers toward the own-sign baseline. Doctrine-fixed."""
    u = uccha_bala(planet, lon)
    if u is None:
        return 0.0
    exalt_sign = EXALTATION.get(planet)
    debil_sign = ((exalt_sign - 1 + 6) % 12) + 1 if exalt_sign else None
    if sign == exalt_sign:
        # Flat grade is +1.6. Within the exalt sign u ∈ ~[0.83, 1.0]; map that band
        # to [own_w, 1.6] so a shallow exaltation shades toward ordinary own-sign.
        frac = max(0.0, min(1.0, (u - (1.0 - 30.0 / 180.0)) / (30.0 / 180.0)))
        scaled = _OWN_W + (1.6 - _OWN_W) * frac
        return round(scaled - 1.6, 2)             # ≤ 0: trims shallow over-credit
    if sign == debil_sign:
        # Flat grade is -1.6. Deeper debilitation (u near 0) → keep full; shallow
        # (near the sign edge, u larger) → soften toward -own_w.
        frac = max(0.0, min(1.0, (u) / (30.0 / 180.0)))
        scaled = -_OWN_W + (-1.6 + _OWN_W) * (1.0 - frac)
        return round(scaled - (-1.6), 2)          # ≥ 0: softens shallow debilitation
    return 0.0


def moolatrikona_delta(planet: str, sign: int, lon: float) -> float:
    """Extra credit when a planet in its OWN sign is within its moolatrikona range
    (a tier above ordinary own-sign). Delta over the flat own-sign weight; 0.0
    otherwise. The sign scorer already fires own-sign at 1.2."""
    if is_moolatrikona(planet, lon):
        return round(_MOOLATRIKONA_W - _OWN_W, 2)
    return 0.0


def combustion_weight(planet: str, planet_lon: float, sun_lon: float) -> float:
    """Orb-graded combustion penalty (≤ 0). Deepest at exact conjunction with the
    Sun, tapering linearly to 0 at the planet's combustion boundary. 0.0 for a
    non-combust planet or one without a combustion orb (Sun/Rahu/Ketu)."""
    if not is_combust(planet, planet_lon, sun_lon):
        return 0.0
    orb = COMBUSTION_ORBS.get(planet)
    if not orb:
        return 0.0
    sep = angular_separation(planet_lon, sun_lon)
    return round(_COMBUST_W * (1.0 - sep / orb), 2)


def chalit_houses(chart) -> dict[str, int]:
    """Sripati bhāva-chalita house (1..12) for every graha, from real longitudes.
    Replaces the whole-sign placement map for degree-resolved charts."""
    lagna_lon = chart.bundle.chart.asc_lon
    lons = chart.bundle.chart.planet_lons
    return {p: _chalit_bhava(lons[p], lagna_lon) for p in lons}
