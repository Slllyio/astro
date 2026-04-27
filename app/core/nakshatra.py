"""Nakshatra + Pada lookup for sidereal longitudes.

This module is a pure-function lookup: given a sidereal Lahiri longitude
in degrees, return the nakshatra (0..26), the pada (1..4), the Vimshottari
ruling lord, and the longitude offset within the nakshatra.

Conventions (locked in to match `app/core/ephemeris_engine.py`):

- Nakshatra span: ``360 / 27`` (≈ 13.333°). Kept as the live division —
  not pre-computed to ``13.333...`` — so floating-point arithmetic matches
  the engine's existing Mahadasha math exactly.
- Pada span: ``span / 4`` (≈ 3.333° each, four padas per nakshatra).
- Cusp convention: floor division (``lon // span``). At an exact boundary,
  e.g. ``longitude == 40.0`` (start of nakshatra index 3 / Rohini), the
  position is treated as belonging to the *current* nakshatra (index 3).
  Equivalently, ``longitude == 13.3333...`` is just past Ashwini and lands
  in Bharani pada 1, while ``longitude == 13.32`` is still inside Ashwini
  pada 4. See `calculate_vimshottari_mahadasha` in
  `app/core/ephemeris_engine.py` for the precedent.
- Indices are Pythonic 0..26 for nakshatras; padas use the conventional
  Vedic 1..4 numbering.
- The lord cycle (Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn,
  Mercury) is the same 9-lord Vimshottari sequence used by `DASHA_LORDS`
  in the engine, repeated three times across the 27 nakshatras.
- Longitude inputs slightly below 0 or slightly above 360 are normalized
  to ``[0, 360)`` via ``longitude % 360.0`` before lookup.
"""
from __future__ import annotations

from typing import TypedDict

NAKSHATRAS: tuple[str, ...] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

NAKSHATRA_LORDS: tuple[str, ...] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
) * 3  # 27 entries — the 9-lord cycle repeats three times across the zodiac.


class NakshatraInfo(TypedDict):
    index: int                      # 0..26
    name: str
    pada: int                       # 1..4
    lord: str                       # one of the 9 Vimshottari lords
    longitude_in_nakshatra: float   # 0..(360/27)


def nakshatra_for_longitude(longitude: float) -> NakshatraInfo:
    """Return nakshatra + pada info for a sidereal longitude (0..360).

    Use floor division to match the nakshatra-cusp convention used elsewhere
    in this project: at exact boundaries (e.g., longitude=40.0), the position
    is treated as belonging to the *previous* nakshatra (consistent with
    `lon // span` behavior). See app/core/ephemeris_engine.py around the
    Mahadasha calculation for the precedent.

    Inputs slightly below 0 or slightly above 360 are normalized via
    ``longitude % 360.0`` before lookup, so e.g. ``-1.0`` and ``361.0``
    behave as ``359.0`` and ``1.0`` respectively.
    """
    lon = longitude % 360.0

    nakshatra_span = 360 / 27           # ≈ 13.333°
    pada_span = nakshatra_span / 4      # ≈ 3.333°

    # Floor division pins boundaries to the *current* nakshatra. We still
    # clamp to 26 to defend against an exact lon=360.0 input that survived
    # normalization due to floating-point quirks (`360.0 % 360.0` is 0.0
    # in CPython, but explicit clamping costs nothing and removes a class
    # of edge cases).
    nak_index = int(lon // nakshatra_span)
    if nak_index > 26:
        nak_index = 26

    longitude_in_nak = lon - (nak_index * nakshatra_span)

    pada_index = int(longitude_in_nak // pada_span)
    if pada_index > 3:
        pada_index = 3
    pada = pada_index + 1  # 1..4 per Vedic convention

    return NakshatraInfo(
        index=nak_index,
        name=NAKSHATRAS[nak_index],
        pada=pada,
        lord=NAKSHATRA_LORDS[nak_index],
        longitude_in_nakshatra=longitude_in_nak,
    )
