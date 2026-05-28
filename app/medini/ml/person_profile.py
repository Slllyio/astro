"""Comprehensive person profile generator — the rich classical view.

Pulls EVERYTHING the doctrine cares about for one person:

  A. Identity: name, DOB, time, place, ascendant degree + lord
  B. Natal positions: each planet → longitude, sign, degree_in_sign,
     nakshatra + pada + lord, house from Lagna, houses_ruled
  C. Divisional charts (14 vargas): per-varga per-planet sign + house +
     houses_ruled
  D. Jaimini 8-karaka scheme: AK, AmK, BK, MK, PK, GK, DK, + 8th karaka
  E. Active dasha at any date
  F. Events list with active dasha + full transit context

Built on top of:
  - persons.parquet, charts.parquet (Silver Tier 0/1)
  - app/core/shodashavarga.compute_divisional_charts (varga math)
  - app/core/nakshatra (pada + nakshatra-lord lookups)
  - app/medini/etl/build_event_transits (transit features)

Usage:
    from app.medini.ml.person_profile import person_profile
    print(person_profile("ADB:2411626.0931"))
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Final, Any

import pandas as pd
import swisseph as swe

from app.core.ephemeris_engine import (
    PLANETS, ZODIAC_SIGNS, calculate_ascendant, calculate_d1_position,
    calculate_ketu_d1, whole_sign_house,
)
from app.core.nakshatra import (
    NAKSHATRAS, nakshatra_for_longitude,
)
from app.core.shodashavarga import (
    SHODASHAVARGA_DIVISORS, SHODASHAVARGA_NAMES,
    compute_divisional_charts,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")

# Canonical 9 grahas.
_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

# BPHS Ch.3 sign rulerships (1-indexed; sign 1 = Aries).
_SIGN_RULERS: Final[dict[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# Jaimini 8-karaka labels in classical order (Putra Karaka in 8th slot is
# the secondary Putra Karaka per Rao's 8-karaka scheme; primary PK is at
# index 4).
_JAIMINI_KARAKA_LABELS: Final[tuple[str, ...]] = (
    "AK_Atmakaraka",      # Self / soul
    "AmK_Amatyakaraka",   # Mind / advisor
    "BK_Bhratrukaraka",   # Siblings
    "MK_Matrukaraka",     # Mother
    "PK_Putrakaraka",     # Children (primary)
    "GK_Gnatikaraka",     # Relatives
    "DK_Darakaraka",      # Spouse
    "PK2_PutraKaraka2",   # 8th karaka (8-karaka scheme)
)


def _houses_ruled_by_planet(planet: str, lagna_sign: int) -> tuple[int, ...]:
    """Houses this planet rules natally given the person's Lagna sign."""
    if planet in ("Rahu", "Ketu"):
        return ()
    houses: list[int] = []
    for sign in range(1, 13):
        if _SIGN_RULERS[sign] == planet:
            houses.append(((sign - lagna_sign) % 12) + 1)
    return tuple(sorted(houses))


def _compute_full_natal_chart(jd: float, lat: float, lon: float) -> dict:
    """Compute all 9 graha positions + ascendant for a moment + place."""
    asc = calculate_ascendant(jd, lat, lon)
    planet_data: dict[str, dict] = {}
    for name, swe_id in PLANETS.items():
        planet_data[name] = calculate_d1_position(jd, swe_id)
    planet_data["Ketu"] = calculate_ketu_d1(planet_data["Rahu"])
    return {"ascendant": asc, "planets": planet_data}


def _compute_jaimini_karakas(planets: dict) -> list[dict]:
    """Rank the 7 visible planets by degree-within-sign, with Rahu's
    longitude inverted (30 - lon), to derive the 8-karaka scheme.

    Ketu is excluded from karaka derivation per the locked Jaimini scheme
    (Narasimha Rao 8-karaka per project doctrine-decisions.md D-1).
    """
    ranked: list[tuple[str, float]] = []
    for graha in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        d = planets[graha]["degree_in_sign"]
        ranked.append((graha, d))
    # Rahu uses inverted longitude (30 - degree_in_sign).
    rahu_d = planets["Rahu"]["degree_in_sign"]
    ranked.append(("Rahu", 30.0 - rahu_d))

    # Sort descending by ranking score; highest gets AK.
    ranked.sort(key=lambda kv: kv[1], reverse=True)

    out: list[dict] = []
    for i, (planet, score) in enumerate(ranked):
        if i >= len(_JAIMINI_KARAKA_LABELS):
            break
        p = planets[planet]
        out.append({
            "karaka": _JAIMINI_KARAKA_LABELS[i],
            "planet": planet,
            "sign": p["sign"],
            "sign_name": ZODIAC_SIGNS[p["sign"] - 1],
            "degree_in_sign": p["degree_in_sign"],
            "ranking_score": score,
        })
    return out


def _per_planet_nakshatra_info(lon: float) -> dict:
    """Nakshatra + pada + nakshatra-lord for a sidereal longitude."""
    info = nakshatra_for_longitude(lon)
    idx = info["index"]
    return {
        "nakshatra_index": idx,
        "nakshatra_name": NAKSHATRAS[idx],
        "pada": info["pada"],
        "nakshatra_lord": info["lord"],
        "longitude_in_nakshatra": info["longitude_in_nakshatra"],
    }


def _build_divisional_summary(
    d1_chart: dict, asc_lon: float,
) -> list[dict]:
    """For each varga (D2..D60), compute per-planet sign + house + lordships.

    The varga's own Lagna sign is computed by applying the same divisional
    formula to the natal ascendant longitude. Houses are whole-sign from
    the varga Lagna.
    """
    # Build d1_chart in shape compute_divisional_charts wants.
    cdc_input: dict[str, dict] = {}
    for graha in _GRAHAS:
        cdc_input[graha] = d1_chart[graha]

    all_vargas = compute_divisional_charts(cdc_input)

    # Compute the varga-Lagna for each divisor.
    from app.core.shodashavarga import compute_divisional_longitude
    rows: list[dict] = []

    # Include D1 explicitly as the natal chart.
    asc_d1_sign = int(asc_lon // 30) + 1
    rows.append({
        "varga": "D1_Rashi",
        "varga_lagna_lon": asc_lon,
        "varga_lagna_sign": asc_d1_sign,
        "varga_lagna_sign_name": ZODIAC_SIGNS[asc_d1_sign - 1],
        "varga_lagna_lord": _SIGN_RULERS[asc_d1_sign],
        "planets": _planets_for_varga(d1_chart, asc_d1_sign),
    })

    for divisor in SHODASHAVARGA_DIVISORS:
        varga_name = SHODASHAVARGA_NAMES[divisor]
        # Varga Lagna sign.
        varga_asc_lon = compute_divisional_longitude(asc_lon, divisor) % 360.0
        varga_asc_sign = int(varga_asc_lon // 30) + 1
        # Per-planet positions in this varga.
        varga_chart = all_vargas[varga_name]
        planets_summary = _planets_for_varga(varga_chart, varga_asc_sign)
        rows.append({
            "varga": varga_name,
            "varga_lagna_lon": varga_asc_lon,
            "varga_lagna_sign": varga_asc_sign,
            "varga_lagna_sign_name": ZODIAC_SIGNS[varga_asc_sign - 1],
            "varga_lagna_lord": _SIGN_RULERS[varga_asc_sign],
            "planets": planets_summary,
        })
    return rows


def _planets_for_varga(
    varga_chart: dict, varga_lagna_sign: int,
) -> list[dict]:
    """Per-planet sign + house + houses ruled within ONE varga."""
    out: list[dict] = []
    for graha in _GRAHAS:
        p = varga_chart[graha]
        out.append({
            "planet": graha,
            "sign": p["sign"],
            "sign_name": ZODIAC_SIGNS[p["sign"] - 1],
            "degree_in_sign": p["degree_in_sign"],
            "house": whole_sign_house(varga_lagna_sign, p["sign"]),
            "houses_ruled": _houses_ruled_by_planet(graha, varga_lagna_sign),
            "is_retrograde": bool(p.get("is_retrograde", False)),
        })
    return out


def person_profile(
    person_id: str, data_dir: Path = DEFAULT_DATA_DIR,
) -> dict:
    """Build the comprehensive profile dict for one person.

    Returns a structured dict with keys:
      - identity:        name, DOB, time, place, source
      - natal_chart:     ascendant, 9 planets with all metadata
      - jaimini_karakas: 8-karaka assignments
      - divisional_charts: 15 vargas (D1..D60) with per-planet detail
    """
    persons = pd.read_parquet(data_dir / "persons.parquet")
    row = persons[persons["person_id"] == person_id]
    if len(row) == 0:
        raise KeyError(f"No person with id {person_id!r}")
    p = row.iloc[0]
    if pd.isna(p["birth_jd"]) or pd.isna(p["birth_lat"]) or pd.isna(p["birth_lon"]):
        raise ValueError(
            f"{person_id} has incomplete birth data — cannot compute chart"
        )

    chart = _compute_full_natal_chart(
        jd=float(p["birth_jd"]),
        lat=float(p["birth_lat"]),
        lon=float(p["birth_lon"]),
    )
    asc = chart["ascendant"]
    asc_sign = asc["sign"]
    planets = chart["planets"]

    natal_planets: list[dict] = []
    for graha in _GRAHAS:
        gp = planets[graha]
        nak = _per_planet_nakshatra_info(gp["longitude"])
        natal_planets.append({
            "planet": graha,
            "longitude": gp["longitude"],
            "sign": gp["sign"],
            "sign_name": ZODIAC_SIGNS[gp["sign"] - 1],
            "degree_in_sign": gp["degree_in_sign"],
            "house": whole_sign_house(asc_sign, gp["sign"]),
            "houses_ruled": _houses_ruled_by_planet(graha, asc_sign),
            "is_retrograde": bool(gp.get("is_retrograde", False)),
            "nakshatra": nak["nakshatra_name"],
            "nakshatra_index": nak["nakshatra_index"],
            "pada": nak["pada"],
            "nakshatra_lord": nak["nakshatra_lord"],
        })

    return {
        "identity": {
            "person_id": person_id,
            "name": str(p["name"]),
            "birth_date": str(p["birth_date"]),
            "birth_time": str(p["birth_time"])
            if pd.notna(p["birth_time"]) else None,
            "birth_time_confidence": (
                float(p["birth_time_confidence"])
                if pd.notna(p["birth_time_confidence"]) else None
            ),
            "birth_lat": float(p["birth_lat"]),
            "birth_lon": float(p["birth_lon"]),
            "tz_offset": (
                float(p["tz_offset"])
                if pd.notna(p["tz_offset"]) else None
            ),
            "source": str(p["source"]),
        },
        "natal_chart": {
            "ascendant": {
                "longitude": asc["longitude"],
                "sign": asc_sign,
                "sign_name": ZODIAC_SIGNS[asc_sign - 1],
                "degree_in_sign": asc["degree_in_sign"],
                "nakshatra": _per_planet_nakshatra_info(asc["longitude"]),
                "lord": _SIGN_RULERS[asc_sign],
            },
            "planets": natal_planets,
        },
        "jaimini_karakas": _compute_jaimini_karakas(planets),
        "divisional_charts": _build_divisional_summary(planets, asc["longitude"]),
    }


def format_profile(profile: dict, *, max_vargas: int | None = None) -> str:
    """Pretty-print a person profile dict as a human-readable report."""
    lines: list[str] = []
    add = lines.append

    # ---- A. Identity ----
    i = profile["identity"]
    add("=" * 78)
    add(f"  {i['name'].upper()}")
    add("=" * 78)
    add(f"  Person ID         : {i['person_id']}")
    add(f"  Date of Birth     : {i['birth_date']}")
    add(f"  Time of Birth     : {i['birth_time'] or '(unknown)'}  "
        f"[confidence={i['birth_time_confidence']}]")
    add(f"  Place (lat, lon)  : {i['birth_lat']:.4f}°N, {i['birth_lon']:.4f}°E  "
        f"(tz={i['tz_offset']})")
    add(f"  Source            : {i['source']}")

    # ---- B. Natal chart ----
    nc = profile["natal_chart"]
    asc = nc["ascendant"]
    add("")
    add("-" * 78)
    add("  GENERAL INFO — Ascendant & Planet Positions")
    add("-" * 78)
    add(f"  Ascendant (Lagna) : {asc['sign_name']:11s}  "
        f"{asc['degree_in_sign']:6.2f}° in sign  "
        f"(lord: {asc['lord']})  "
        f"Nakshatra: {asc['nakshatra']['nakshatra_name']} pada {asc['nakshatra']['pada']}")
    add("")
    add(f"  {'Planet':<8} {'Sign':<12} {'Deg':>7} {'Hse':>4} "
        f"{'Rules':<8} {'Nakshatra':<18} {'Pada':>5} {'NakLord':<9} Rx")
    add(f"  {'-'*8} {'-'*12} {'-'*7} {'-'*4} {'-'*8} {'-'*18} {'-'*5} {'-'*9} --")
    for pl in nc["planets"]:
        rules = ",".join(str(h) for h in pl["houses_ruled"]) or "—"
        rx = "Rx" if pl["is_retrograde"] else ""
        add(f"  {pl['planet']:<8} {pl['sign_name']:<12} "
            f"{pl['degree_in_sign']:6.2f}° {pl['house']:>4} "
            f"{rules:<8} {pl['nakshatra']:<18} {pl['pada']:>5} "
            f"{pl['nakshatra_lord']:<9} {rx}")

    # ---- C. Jaimini karakas ----
    add("")
    add("-" * 78)
    add("  JAIMINI 8-KARAKA SCHEME (degree-within-sign ranking; Rahu inverted)")
    add("-" * 78)
    add(f"  {'Karaka':<22} {'Planet':<8} {'Sign':<12} {'Deg':>7}  ranking-score")
    add(f"  {'-'*22} {'-'*8} {'-'*12} {'-'*7}  -------------")
    for k in profile["jaimini_karakas"]:
        add(f"  {k['karaka']:<22} {k['planet']:<8} {k['sign_name']:<12} "
            f"{k['degree_in_sign']:6.2f}°  {k['ranking_score']:.4f}")

    # ---- D. Divisional charts ----
    add("")
    add("-" * 78)
    add("  DIVISIONAL CHARTS (Shodashavarga — 15 vargas)")
    add("-" * 78)
    vargas = profile["divisional_charts"]
    if max_vargas is not None:
        vargas = vargas[:max_vargas]
    for v in vargas:
        add("")
        add(f"  [{v['varga']}]   Varga-Lagna: {v['varga_lagna_sign_name']:11s} "
            f"({v['varga_lagna_lon']:.2f}°, lord: {v['varga_lagna_lord']})")
        add(f"    {'Planet':<8} {'Sign':<12} {'Deg':>7} {'Hse':>4} "
            f"{'Rules in this varga':<22}")
        add(f"    {'-'*8} {'-'*12} {'-'*7} {'-'*4} {'-'*22}")
        for pp in v["planets"]:
            rules = ",".join(str(h) for h in pp["houses_ruled"]) or "—"
            add(f"    {pp['planet']:<8} {pp['sign_name']:<12} "
                f"{pp['degree_in_sign']:6.2f}° {pp['house']:>4} {rules:<22}")

    return "\n".join(lines)
