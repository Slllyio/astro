"""Special Lagnas — 5 alternative reading frames (S-3).

The natal Ascendant (D1 Lagna) is one of MANY possible reference points
for chart reading. Classical Jyotisha uses several specialized lagnas,
each giving the SAME chart a different lens for different domains. A
master astrologer asking "will this person become wealthy" doesn't only
look at natal-bhava-2 — they cross-reference Indu Lagna's 2H + Sree
Lagna's 2H + (if relevant) Hora Lagna's 2H to see if the wealth
signature converges across multiple frames.

This module computes 5 special lagnas:

  1. Bhava Lagna  (BL) — advances 30° every 2 hours from sunrise.
                          ACTION-oriented frame.
  2. Hora Lagna   (HL) — advances 30° every 1 hour from sunrise.
                          WEALTH-PACE frame.
  3. Ghati Lagna  (GL) — advances 30° every 24 minutes from sunrise.
                          POWER/STATUS frame.
  4. Indu Lagna   (IL) — from Moon-lord + Lagna-lord kala values.
                          WEALTH-SOURCE / sustenance frame.
  5. Sree Lagna   (SL) — from Lagna + Moon's nakshatra portion.
                          LAKSHMI-GRACE / prosperity frame.

## Precision caveats

BL / HL / GL all advance from SUNRISE. For pure accuracy we need real
sunrise time per (date, lat, lon). This module uses a simplified local-
solar-hour proxy (same heuristic as is_day_birth in the bulk ETL):

    hour_local ≈ (jd_fraction + 0.5) * 24 + (birth_lon / 15)

The proxy is good to ~10 minutes for mid-latitudes near equinoxes;
worse at extreme latitudes or solstices. The returned reports carry
precision_caveat fields to flag this.

IL and SL don't depend on sunrise — they're exact from chart data.

## References

  * BPHS Ch.27 — Lagna varieties
  * Phaladeepika Ch.4 — special lagnas in delineation
  * Brihat Parashara — Sree Lagna formula
  * KN Rao — *Predicting Marriage* — Indu Lagna delineation
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping


# ─── Constants ──────────────────────────────────────────────────────


# Indu Lagna kala values per planet (KN Rao's table, classical).
# Lagna-lord and Moon-nakshatra-lord both contribute.
INDU_KALA: Final[Mapping[str, int]] = {
    "Sun":     30,
    "Moon":    16,
    "Mars":     6,
    "Mercury":  8,
    "Jupiter": 10,
    "Venus":   12,
    "Saturn":   1,
}

# Sign-lord table for Lagna-lord lookup
_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# Nakshatra-lord cycle (Vimshottari order; repeats every 9 nakshatras)
_NAKSHATRA_LORDS: Final[tuple[str, ...]] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
)


@dataclass(frozen=True)
class SpecialLagna:
    """One special lagna with sign + longitude + precision metadata."""
    name: str                    # Bhava / Hora / Ghati / Indu / Sree
    sign: int                    # 1..12
    longitude: float             # 0..360 (where computable)
    domain_lens: str             # which life domain this lagna best reads
    precision: str               # "exact" / "approximate (sunrise proxy)"


@dataclass(frozen=True)
class SpecialLagnasReport:
    """All 5 special lagnas for one chart."""
    bhava_lagna: SpecialLagna | None     # None if birth_jd / lon missing
    hora_lagna: SpecialLagna | None
    ghati_lagna: SpecialLagna | None
    indu_lagna: SpecialLagna             # always computable
    sree_lagna: SpecialLagna             # always computable


# ─── Time-of-day helpers ────────────────────────────────────────────


def _local_solar_hour(birth_jd: float, birth_lon: float) -> float:
    """Approximate local-solar hour-of-day [0, 24).

    Same heuristic as build_person_master_readings._enrich_dossier_with_
    master_inputs: jd_fraction * 24 + longitude/15, mod 24. Not equation-
    of-time corrected.
    """
    jd_frac = birth_jd % 1.0
    hour_ut = ((jd_frac + 0.5) * 24.0) % 24.0
    return (hour_ut + birth_lon / 15.0) % 24.0


def _hours_since_sunrise_approx(birth_jd: float, birth_lon: float) -> float:
    """Hours since 6:00 local solar (simplified sunrise = 6 AM).

    Returns 0..24. If birth is before 6 AM (pre-sunrise), wraps:
    e.g. 3 AM birth → 21 hours since previous day's sunrise.
    """
    h = _local_solar_hour(birth_jd, birth_lon)
    diff = (h - 6.0) % 24.0
    return diff


def _sign_from_lon(longitude: float) -> int:
    return int(longitude % 360.0 // 30.0) + 1


# ─── BL / HL / GL — time-since-sunrise lagnas ───────────────────────


def compute_bhava_lagna(
    sun_lon: float, birth_jd: float | None, birth_lon: float | None,
) -> SpecialLagna | None:
    """Bhava Lagna — action-oriented lens. Advances 30° per 2 hours."""
    if birth_jd is None or birth_lon is None:
        return None
    hrs = _hours_since_sunrise_approx(birth_jd, birth_lon)
    bl_lon = (sun_lon + hrs * 15.0) % 360.0
    return SpecialLagna(
        name="Bhava", sign=_sign_from_lon(bl_lon),
        longitude=round(bl_lon, 3),
        domain_lens="action / event-timing",
        precision="approximate (sunrise proxy = 6AM local solar)",
    )


def compute_hora_lagna(
    sun_lon: float, birth_jd: float | None, birth_lon: float | None,
) -> SpecialLagna | None:
    """Hora Lagna — wealth-velocity lens. Advances 30° per 1 hour."""
    if birth_jd is None or birth_lon is None:
        return None
    hrs = _hours_since_sunrise_approx(birth_jd, birth_lon)
    hl_lon = (sun_lon + hrs * 30.0) % 360.0
    return SpecialLagna(
        name="Hora", sign=_sign_from_lon(hl_lon),
        longitude=round(hl_lon, 3),
        domain_lens="wealth velocity / income pace",
        precision="approximate (sunrise proxy)",
    )


def compute_ghati_lagna(
    sun_lon: float, birth_jd: float | None, birth_lon: float | None,
) -> SpecialLagna | None:
    """Ghati Lagna — power/status lens. Advances 30° per 24 minutes (1 ghati)."""
    if birth_jd is None or birth_lon is None:
        return None
    hrs = _hours_since_sunrise_approx(birth_jd, birth_lon)
    # 30° per 0.4 hours (24 min) = 75°/hr
    gl_lon = (sun_lon + hrs * 75.0) % 360.0
    return SpecialLagna(
        name="Ghati", sign=_sign_from_lon(gl_lon),
        longitude=round(gl_lon, 3),
        domain_lens="political power / professional status",
        precision="approximate (sunrise proxy)",
    )


# ─── IL — chart-only lagna ──────────────────────────────────────────


def compute_indu_lagna(
    asc_sign: int, moon_sign: int, moon_nakshatra_index: int,
) -> SpecialLagna:
    """Indu Lagna — wealth-source / sustenance lens.

    Classical formula (KN Rao, *Predicting Marriage*):
      1. Get Lagna-lord (sign-lord of asc_sign).
      2. Get Moon's nakshatra-lord.
      3. Sum their kala values from INDU_KALA.
      4. (sum mod 12) signs counted FROM Moon's sign = Indu Lagna sign.
    """
    lagna_lord = _SIGN_LORDS[asc_sign]
    nak_lord = _NAKSHATRA_LORDS[moon_nakshatra_index % 9]
    # Kala values; default 0 if lord is Rahu/Ketu (not in classical table —
    # treat as 0 contribution).
    k1 = INDU_KALA.get(lagna_lord, 0)
    k2 = INDU_KALA.get(nak_lord, 0)
    total = k1 + k2
    # Count (total mod 12) signs FROM moon_sign. If result is 0, use 12.
    offset = total % 12
    if offset == 0:
        offset = 12
    il_sign = ((moon_sign - 1 + offset - 1) % 12) + 1
    return SpecialLagna(
        name="Indu", sign=il_sign,
        longitude=(il_sign - 1) * 30.0 + 15.0,  # mid-sign placeholder
        domain_lens="wealth source / sustained prosperity",
        precision="exact (chart-only)",
    )


# ─── SL — chart-only lagna ──────────────────────────────────────────


def compute_sree_lagna(
    asc_lon: float, moon_lon: float,
) -> SpecialLagna:
    """Sree Lagna — Lakshmi-grace / prosperity lens.

    Classical formula (BPHS / Sanjay Rath):
      SL_lon = Lagna_lon + Moon's longitude within its nakshatra,
               scaled to 360°.

    The intuition: Sree Lagna fuses the Lagna's "self" with the Moon's
    "fortune-portion" of its current nakshatra. A native born at Moon's
    nakshatra-start has SL = Lagna; born at nakshatra-end has SL = Lagna
    + 360/27° (one nakshatra further).

    Simpler computational form:
      SL_lon = (asc_lon + (moon_lon mod (360/27)) * 27) % 360
    The factor *27 expands Moon's position-within-nakshatra (0..13°20')
    to a full 360° scaling, then added to Lagna longitude.
    """
    nak_span = 360.0 / 27.0  # 13°20'
    moon_within_nak = moon_lon % nak_span
    # Scale to full sign-cycle: position-in-nakshatra (0..nak_span) → (0..360)
    scaled = (moon_within_nak / nak_span) * 360.0
    sl_lon = (asc_lon + scaled) % 360.0
    return SpecialLagna(
        name="Sree", sign=_sign_from_lon(sl_lon),
        longitude=round(sl_lon, 3),
        domain_lens="Lakshmi grace / prosperity / luck",
        precision="exact (chart-only)",
    )


# ─── Aggregate ──────────────────────────────────────────────────────


def compute_all_special_lagnas(
    asc_sign: int, asc_lon: float,
    sun_lon: float, moon_sign: int, moon_lon: float,
    moon_nakshatra_index: int,
    birth_jd: float | None = None,
    birth_lon: float | None = None,
) -> SpecialLagnasReport:
    """Compute all 5 special lagnas for one chart.

    IL and SL always populate (chart-only). BL / HL / GL populate only
    when birth_jd + birth_lon are supplied (need time-of-day proxy).
    """
    return SpecialLagnasReport(
        bhava_lagna=compute_bhava_lagna(sun_lon, birth_jd, birth_lon),
        hora_lagna=compute_hora_lagna(sun_lon, birth_jd, birth_lon),
        ghati_lagna=compute_ghati_lagna(sun_lon, birth_jd, birth_lon),
        indu_lagna=compute_indu_lagna(asc_sign, moon_sign, moon_nakshatra_index),
        sree_lagna=compute_sree_lagna(asc_lon, moon_lon),
    )


def format_special_lagnas(r: SpecialLagnasReport) -> str:
    """Render special lagnas as a summary."""
    lines = ["=== SPECIAL LAGNAS (5 alternative reading frames) ==="]
    for sl in (r.bhava_lagna, r.hora_lagna, r.ghati_lagna,
               r.indu_lagna, r.sree_lagna):
        if sl is None:
            lines.append("  (skipped — needs birth time)")
            continue
        lines.append(
            f"  {sl.name:<6} Lagna : sign {sl.sign:>2}  "
            f"@ {sl.longitude:>6.1f} deg  -- {sl.domain_lens}  "
            f"[{sl.precision}]"
        )
    return "\n".join(lines)
