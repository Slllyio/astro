from __future__ import annotations

from typing import Any

import swisseph as swe

# Configure swisseph to use built-in Moshier ephemeris
swe.set_ephe_path(None)

# Mean Gregorian year. Standard Vimshottari constant in Parashara/Jagannatha Hora.
# Do NOT replace with 365.25 (Julian year) - over a 19-yr Saturn MD that is ~5 days
# of drift. See Phase 2 plan constraint #2.
DAYS_PER_VEDIC_YEAR = 365.2425

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.TRUE_NODE, # Using True Node as required
}

# Vimshottari Dasha Lords in order from Ketu
DASHA_LORDS = [
    ("Ketu", 7),
    ("Venus", 20),
    ("Sun", 6),
    ("Moon", 10),
    ("Mars", 7),
    ("Rahu", 18),
    ("Jupiter", 16),
    ("Saturn", 19),
    ("Mercury", 17)
]

def to_decimal_hours(hour: int, minute: int) -> float:
    return hour + (minute / 60.0)

def calculate_jd(year: int, month: int, day: int, hour: float, tz_offset: float) -> float:
    # Convert local time to UTC
    utc_hour = hour - tz_offset
    
    # Calculate Julian Day using Gregorian calendar
    # swe.julday takes year, month, day, hour in UTC, calendar type (1 = Gregorian)
    jd = swe.julday(year, month, day, utc_hour, swe.GREG_CAL)
    return jd

def get_ayanamsa(jd: float) -> float:
    # Set Lahiri (Chitra Paksha) Ayanamsa
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.get_ayanamsa_ut(jd)

def calculate_d1_position(jd: float, planet_id: int) -> dict[str, Any]:
    # Set Sidereal mode for Vedic
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Get sidereal planetary position (flag = swe.FLG_SIDEREAL)
    # Also use swe.FLG_SPEED to determine retrograde motion
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    res, rflag = swe.calc_ut(jd, planet_id, flags)
    
    longitude = res[0]
    speed = res[3]
    
    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30
    
    return {
        "longitude": longitude,
        "sign": sign_index + 1, # 1-indexed (1=Aries)
        "sign_name": ZODIAC_SIGNS[sign_index],
        "degree_in_sign": degree_in_sign,
        "is_retrograde": speed < 0
    }

def calculate_ketu_d1(rahu_pos: dict[str, Any]) -> dict[str, Any]:
    # Ketu is exactly 180 degrees from Rahu
    ketu_long = (rahu_pos["longitude"] + 180) % 360
    sign_index = int(ketu_long // 30)
    degree_in_sign = ketu_long % 30
    
    return {
        "longitude": ketu_long,
        "sign": sign_index + 1,
        "sign_name": ZODIAC_SIGNS[sign_index],
        "degree_in_sign": degree_in_sign,
        "is_retrograde": rahu_pos["is_retrograde"]
    }

def calculate_divisional_longitude(longitude: float, divisor: int) -> float:
    """
    Generic divisional chart longitude calculation.
    """
    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30
    
    if divisor == 9: # Navamsa
        # Each Navamsa is 3 degrees 20 minutes (3.3333... degrees)
        navamsa_part = int(degree_in_sign // (30 / 9))
        
        # Starting sign depends on the element of the D1 sign
        element = sign_index % 4 # 0=Fire (Aries, Leo, Sag), 1=Earth, 2=Air, 3=Water
        
        if element == 0:
            start_sign = 0 # Aries
        elif element == 1:
            start_sign = 9 # Capricorn
        elif element == 2:
            start_sign = 6 # Libra
        else: # element == 3
            start_sign = 3 # Cancer
            
        navamsa_sign_index = (start_sign + navamsa_part) % 12
        return (navamsa_sign_index * 30) + ((degree_in_sign % (30 / 9)) * 9)

    elif divisor == 10: # Dasamsa
        # Each Dasamsa is 3 degrees
        dasamsa_part = int(degree_in_sign // 3)
        
        # Odd sign starts from itself, Even sign starts from 9th from itself
        if sign_index % 2 == 0: # Odd signs (0, 2, 4...) -> 1st, 3rd, 5th...
            start_sign = sign_index
        else:
            start_sign = (sign_index + 8) % 12 # 9th sign from current is +8 index
            
        dasamsa_sign_index = (start_sign + dasamsa_part) % 12
        return (dasamsa_sign_index * 30) + ((degree_in_sign % 3) * 10)
        
    return longitude

def calculate_ascendant(jd: float, latitude: float, longitude: float) -> dict[str, Any]:
    """Sidereal Lahiri ascendant (Lagna) for a moment + location.

    Uses Swiss Ephemeris's whole-sign houses ('W'). The ascendant value itself
    is independent of house system; we pick whole-sign because it's the Vedic
    convention and lets the same call return whole-sign house cusps if needed
    later.

    The latitude/longitude inputs follow the WGS-84 convention: latitude in
    [-90, +90], longitude in [-180, +180] with east positive.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL
    _cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b"W", flags)
    asc_lon = ascmc[0]
    sign_index = int(asc_lon // 30)
    return {
        "longitude": asc_lon,
        "sign": sign_index + 1,
        "sign_name": ZODIAC_SIGNS[sign_index],
        "degree_in_sign": asc_lon % 30,
    }


def whole_sign_house(ascendant_sign: int, planet_sign: int) -> int:
    """House number (1..12) for a planet under whole-sign Vedic counting.

    The 1st house IS the ascendant's sign. Houses count forward from there:
    asc=Virgo (6), planet in Libra (7) -> 2nd house. asc=Pisces (12), planet
    in Aries (1) -> 2nd house (wrap).
    """
    if not (1 <= ascendant_sign <= 12 and 1 <= planet_sign <= 12):
        raise ValueError(
            f"signs must be 1..12, got asc={ascendant_sign} planet={planet_sign}"
        )
    return ((planet_sign - ascendant_sign) % 12) + 1


def position_from_longitude(longitude: float, is_retrograde: bool) -> dict[str, Any]:
    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30
    return {
        "longitude": longitude,
        "sign": sign_index + 1,
        "sign_name": ZODIAC_SIGNS[sign_index],
        "degree_in_sign": degree_in_sign,
        "is_retrograde": is_retrograde
    }

def calculate_vimshottari_mahadasha(moon_longitude: float, birth_jd: float) -> dict[str, Any]:
    # Moon Nakshatra (span is 13 degrees 20 minutes = 13.333333... degrees)
    nakshatra_span = 360 / 27
    # Use floor division to keep nakshatra_index consistent with degree_elapsed
    # below. With `int(moon_lon / nak)` the integer cast disagreed with `% nak`
    # at exact boundaries (e.g. moon_lon=40.0) because `/` rounds to nearest fp
    # while `%` is floor-based. Floor division matches `%` by construction.
    nakshatra_index = int(moon_longitude // nakshatra_span)

    # Calculate degree elapsed in the current nakshatra
    degree_elapsed = moon_longitude % nakshatra_span
    fraction_elapsed = degree_elapsed / nakshatra_span

    # Dasha lord index
    lord_index = nakshatra_index % 9
    current_lord, total_years = DASHA_LORDS[lord_index]

    years_elapsed = fraction_elapsed * total_years
    years_remaining = total_years - years_elapsed

    # Calendar dates via Julian Day arithmetic, then swe.revjul to Gregorian.
    # Avoiding datetime.timedelta avoids leap-year drift across multi-decade spans
    # and keeps the calendar model consistent with Swiss Ephemeris itself.
    # See Phase 2 plan constraint #2.
    start_jd = birth_jd - (years_elapsed * DAYS_PER_VEDIC_YEAR)
    end_jd = birth_jd + (years_remaining * DAYS_PER_VEDIC_YEAR)

    sy, sm, sd, _ = swe.revjul(start_jd, swe.GREG_CAL)
    ey, em, ed, _ = swe.revjul(end_jd, swe.GREG_CAL)
    start_date = f"{int(sy):04d}-{int(sm):02d}-{int(sd):02d}"
    end_date = f"{int(ey):04d}-{int(em):02d}-{int(ed):02d}"

    return {
        "mahadasha_lord": current_lord,
        "start_date": start_date,
        "end_date": end_date,
        "time_elapsed_years": years_elapsed,
        "total_duration_years": total_years,
        "years_remaining": years_remaining,
    }

def calculate_all_charts(
    year: int, month: int, day: int, hour: int, minute: int, tz_offset: float,
    latitude: float | None = None, longitude: float | None = None,
) -> dict[str, Any]:
    """Compute D1/D9/D10 + Mahadasha (always) and ascendant + per-planet houses
    (only when both `latitude` and `longitude` are provided).

    Lat/lon are optional so the transit daemon can call this for "where are
    the planets right now" without supplying meaningless geographic anchors —
    the ascendant of a transit chart isn't astrologically interesting. When
    omitted, the response's `ascendant` field is `None` and d1 entries do
    NOT carry a `house` key.
    """
    utc_hour_decimal = to_decimal_hours(hour, minute)
    jd = calculate_jd(year, month, day, utc_hour_decimal, tz_offset)
    ayanamsa = get_ayanamsa(jd)
    
    d1_chart = {}
    d9_chart = {}
    d10_chart = {}
    
    for name, planet_id in PLANETS.items():
        d1_pos = calculate_d1_position(jd, planet_id)
        d1_pos["name"] = name
        d1_chart[name] = d1_pos
        
        # Calculate D9
        d9_long = calculate_divisional_longitude(d1_pos["longitude"], 9)
        d9_pos = position_from_longitude(d9_long, d1_pos["is_retrograde"])
        d9_pos["name"] = name
        d9_chart[name] = d9_pos
        
        # Calculate D10
        d10_long = calculate_divisional_longitude(d1_pos["longitude"], 10)
        d10_pos = position_from_longitude(d10_long, d1_pos["is_retrograde"])
        d10_pos["name"] = name
        d10_chart[name] = d10_pos
        
    # Calculate Ketu based on True Node (Rahu)
    ketu_d1 = calculate_ketu_d1(d1_chart["Rahu"])
    ketu_d1["name"] = "Ketu"
    d1_chart["Ketu"] = ketu_d1
    
    d9_ketu_long = calculate_divisional_longitude(ketu_d1["longitude"], 9)
    d9_ketu = position_from_longitude(d9_ketu_long, ketu_d1["is_retrograde"])
    d9_ketu["name"] = "Ketu"
    d9_chart["Ketu"] = d9_ketu
    
    d10_ketu_long = calculate_divisional_longitude(ketu_d1["longitude"], 10)
    d10_ketu = position_from_longitude(d10_ketu_long, ketu_d1["is_retrograde"])
    d10_ketu["name"] = "Ketu"
    d10_chart["Ketu"] = d10_ketu
    
    mahadasha = calculate_vimshottari_mahadasha(d1_chart["Moon"]["longitude"], jd)

    # Ascendant + per-planet whole-sign houses (only when geographic anchor given).
    ascendant: dict[str, Any] | None = None
    if latitude is not None and longitude is not None:
        ascendant = calculate_ascendant(jd, latitude, longitude)
        for name, pos in d1_chart.items():
            pos["house"] = whole_sign_house(ascendant["sign"], pos["sign"])

    # Phase 3 feature integration: each module computed in parallel by a
    # specialized agent; we just thread the right inputs through here.
    # These imports live inside the function so they don't load at module
    # import time (and so the daemon's transit-only path can avoid them
    # if needed in future profiling).
    from app.core.antardasha import compute_antardashas
    from app.core.ashtakavarga import compute_ashtakavarga
    from app.core.avastha import compute_avasthas
    from app.core.nakshatra import nakshatra_for_longitude
    from app.core.panchanga import compute_panchanga
    from app.core.pratyantar import compute_all_pratyantars
    from app.core.shodashavarga import compute_divisional_charts
    from app.core.yogas import detect_yogas

    # Per-planet nakshatra annotation merged inline into the existing d1
    # entries so consumers see chart["d1"]["Saturn"]["nakshatra"] cleanly.
    for pos in d1_chart.values():
        pos["nakshatra"] = nakshatra_for_longitude(pos["longitude"])

    antardashas = compute_antardashas(d1_chart["Moon"]["longitude"], jd)
    pratyantars = compute_all_pratyantars(antardashas)
    divisional_charts = compute_divisional_charts(d1_chart)
    panchanga = compute_panchanga(jd)
    yogas = detect_yogas(d1_chart, ascendant) if ascendant is not None else []
    # Ashtakavarga (BAV/SAV) requires the Lagna sign as the 8th contributor;
    # only compute when an ascendant was supplied.
    ashtakavarga = (
        compute_ashtakavarga(d1_chart, ascendant) if ascendant is not None else None
    )
    # Avastha is per-planet and pure (no lat/lon dependency); always compute.
    avasthas = compute_avasthas(d1_chart)

    return {
        "jd": jd,
        "birth_jd": jd,
        "ayanamsa": ayanamsa,
        "ascendant": ascendant,
        "d1": d1_chart,
        "d9": d9_chart,
        "d10": d10_chart,
        "current_mahadasha": mahadasha,
        "antardashas": antardashas,
        "pratyantars": pratyantars,
        "divisional_charts": divisional_charts,
        "panchanga": panchanga,
        "yogas": yogas,
        "ashtakavarga": ashtakavarga,
        "avasthas": avasthas,
    }
