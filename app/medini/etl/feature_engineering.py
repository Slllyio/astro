"""The Vedic Tensor: ~150 ML features per natal chart.

Three vectors:
  - Base    : longitudes, pairwise angular distances, nakshatras,
              houses-from-Lagna, Kurma tattvas (~70 cols)
  - Kinematic: velocity, retrograde, stationary, combustion intensity,
              ecliptic latitude, declination, out-of-bounds (~36 cols)
  - Vedic   : Ashtakavarga (SAV per house, BAV in current sign),
              D9/D10 placements, dispositor chain, final dispositor (~50 cols)

Pure functions; no IO; no DB; no global state. Composes existing project
primitives (ephemeris_engine, nakshatra, kurma_chakra, ashtakavarga,
shodashavarga) — does NOT re-implement astronomy.

Usage:
    from app.medini.etl.feature_engineering import compute_chart_features
    features = compute_chart_features(jd=2448087.77, latitude=12.97, longitude=77.59)
    # features is a dict[str, float|int|str] with ~150 entries
"""
from __future__ import annotations

import itertools
import math
from typing import Any

import swisseph as swe

from app.core.ashtakavarga import compute_ashtakavarga
from app.core.avastha import _DRISHTI_HOUSES
from app.core.ephemeris_engine import (
    DASHA_LORDS,
    DAYS_PER_VEDIC_YEAR,
    PLANETS,
    ZODIAC_SIGNS,
    calculate_ascendant,
    calculate_vimshottari_mahadasha,
    whole_sign_house,
)
from app.core.nakshatra import nakshatra_for_longitude
from app.core.panchanga import compute_panchanga
from app.core.pratyantar import compute_pratyantars
from app.core.shodashavarga import compute_divisional_charts
from app.core.yogas import detect_yogas
from app.medini.kurma_chakra import region_for_nakshatra, tattva_for_region


# ---------- Constants ----------

# Ordered planet list. Order matters for column naming consistency:
# `dist_sun_moon` always means Sun-Moon, never Moon-Sun. Pairs derived from
# itertools.combinations preserve this order.
GRAHAS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

# Per-planet combustion orbs (degrees). Classical Vedic: Mercury 12°, Venus 10°
# Mars 17°, Jupiter 11°, Saturn 15°, Moon 12°. Sun is always its own combustion
# axis (intensity = 1 by definition); nodes don't combust in classical thought.
COMBUSTION_ORB: dict[str, float] = {
    "Sun": 0.0,        # unused — Sun's intensity is always 1.0 by convention
    "Moon": 12.0,
    "Mars": 17.0,
    "Mercury": 12.0,
    "Jupiter": 11.0,
    "Venus": 10.0,
    "Saturn": 15.0,
    "Rahu": 0.0,       # nodes don't combust; intensity stays 0.0
    "Ketu": 0.0,
}

# Sign rulerships for the dispositor chain. Indexed by sign 1..12.
# Classical Vedic (no Uranus/Neptune/Pluto rulerships, no nodal rulerships).
SIGN_RULERS: dict[int, str] = {
    1: "Mars",      # Aries
    2: "Venus",     # Taurus
    3: "Mercury",   # Gemini
    4: "Moon",      # Cancer
    5: "Sun",       # Leo
    6: "Mercury",   # Virgo
    7: "Venus",     # Libra
    8: "Mars",      # Scorpio
    9: "Jupiter",   # Sagittarius
    10: "Saturn",   # Capricorn
    11: "Saturn",   # Aquarius
    12: "Jupiter",  # Pisces
}

# Earth's axial tilt: Out-of-Bounds threshold for declination.
OUT_OF_BOUNDS_DECLINATION = 23.4367
STATIONARY_VEL_THRESHOLD = 0.05  # degrees/day; below = effectively stationary

# Vimshottari planets where 3rd-derivative (jerk) carries genuine signal rather
# than numerical noise on the ±1-day window. Fast inner planets change velocity
# too rapidly for finite-difference jerk to be informative; slow planets
# (Jupiter through Ketu) have smooth velocity profiles around stations.
JERK_TRACKED_PLANETS: tuple[str, ...] = ("Jupiter", "Saturn", "Rahu", "Ketu")

# Earliest age (years) at which an Antardasha sub-period is considered to
# "open in adulthood". Used by the dasha-timeline helper for the
# `first_<planet>_antardasha_after_<N>` features. 16 is the classical
# threshold for relational/career events to begin manifesting.
ANTARDASHA_ADULTHOOD_AGE = 16


# ---------- Low-level swisseph wrappers ----------

def _planet_full_state(jd: float, planet_id: int) -> dict[str, float]:
    """Compute lon, lat, vel for a planet under sidereal Lahiri.

    `swe.calc_ut` returns 6 values when FLG_SPEED is set: [lon, lat, dist,
    lon_speed, lat_speed, dist_speed]. We surface lon, ecliptic latitude,
    and lon_speed (the daily motion in degrees).
    """
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result, _ = swe.calc_ut(jd, planet_id, flags)
    return {
        "lon": float(result[0]),
        "lat": float(result[1]),
        "vel": float(result[3]),
    }


def _planet_declination(jd: float, planet_id: int) -> float:
    """Equatorial declination (degrees from celestial equator).

    `FLG_EQUATORIAL` returns [RA, dec, dist, RA_speed, dec_speed, dist_speed].
    Independent of sidereal/tropical mode (declination is an equatorial
    coordinate, not ecliptic).
    """
    result, _ = swe.calc_ut(jd, planet_id, swe.FLG_EQUATORIAL)
    return float(result[1])


def circular_distance_180(lon_a: float, lon_b: float) -> float:
    """Shortest angular distance on the 0..180° interval.

    Pisces/Aries cusp safe: dist(359°, 2°) = 3°, not 357°. Bounded to
    [0, 180] so the model doesn't have to learn that 270° and 90° are
    "the same distance from a square." Also: ML models like compact ranges.
    """
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def combustion_intensity(sun_lon: float, planet_lon: float, planet: str) -> float:
    """0.0–1.0 continuous combustion score.

    1.0 = exact Cazimi (planet conjunct Sun within ~17' of arc).
    Linear decay to 0.0 at the edge of the per-planet combustion orb.
    Outside the orb: 0.0.

    Sun's own column is always 1.0 by convention. Nodes never combust
    (their COMBUSTION_ORB entry is 0.0, which yields max(0, 1 - inf) = 0).
    """
    if planet == "Sun":
        return 1.0
    orb_max = COMBUSTION_ORB.get(planet, 0.0)
    if orb_max <= 0.0:
        return 0.0
    orb = circular_distance_180(sun_lon, planet_lon)
    if orb > orb_max:
        return 0.0
    return max(0.0, 1.0 - (orb / orb_max))


# ---------- d1_chart construction (for Phase A modules to consume) ----------

def _build_d1_chart(
    states: dict[str, dict[str, float]],
    ascendant_sign: int,
) -> dict[str, dict[str, Any]]:
    """Build the d1_chart shape that ashtakavarga / shodashavarga / yogas
    expect: {planet: {longitude, sign, sign_name, degree_in_sign,
    is_retrograde, name, house}}."""
    chart: dict[str, dict[str, Any]] = {}
    for planet, state in states.items():
        lon = state["lon"]
        sign_idx = int(lon // 30)
        sign = sign_idx + 1
        chart[planet] = {
            "name": planet,
            "longitude": lon,
            "sign": sign,
            "sign_name": ZODIAC_SIGNS[sign_idx],
            "degree_in_sign": lon % 30.0,
            "is_retrograde": state["vel"] < 0,
            "house": whole_sign_house(ascendant_sign, sign),
        }
    return chart


# ---------- Dispositor chain ----------

def compute_dispositor(planet: str, planet_sign: int) -> str:
    """Immediate dispositor: the planet ruling the sign this planet sits in.

    Nodes (Rahu/Ketu) DO have dispositors per classical Parashara: the
    lord of their occupied sign. So Rahu in Cancer is disposited by Moon.
    """
    return SIGN_RULERS.get(planet_sign, "none")


def compute_dispositor_chain_depth(
    planet: str,
    chart_signs: dict[str, int],
    max_hops: int = 12,
) -> int:
    """How many dispositor hops until the chain terminates (a planet in
    its own sign disposits itself = chain ends).

    Returns 0 if `planet` is already in its own sign (self-disposited).
    Returns max_hops if the chain never terminates within max_hops
    (indicates a non-terminating cycle).
    """
    visited: set[str] = set()
    current = planet
    for hop in range(max_hops):
        sign = chart_signs.get(current)
        if sign is None:
            return hop
        ruler = SIGN_RULERS.get(sign, "none")
        if ruler == current:
            return hop  # self-disposited; chain terminates here
        if ruler in visited or ruler == "none":
            return hop
        visited.add(current)
        current = ruler
    return max_hops


def compute_final_dispositor(chart_signs: dict[str, int]) -> str:
    """Identify the "CEO of the chart" — the planet that all chains
    eventually flow into.

    Algorithm:
      1. Find self-disposited planets (in their own sign). These are
         chain terminators.
      2. For each other planet, walk its chain to a self-disposited
         endpoint and accumulate vote counts.
      3. The self-disposited planet with the highest vote count wins.
         Tie-break alphabetically (deterministic).
      4. If no planet is self-disposited (extremely rare in real charts),
         return "none".

    Excludes nodes from being final dispositors (classical convention).
    """
    self_disposited = {
        p for p in chart_signs
        if p not in ("Rahu", "Ketu") and SIGN_RULERS.get(chart_signs[p]) == p
    }
    if not self_disposited:
        return "none"

    votes: dict[str, int] = {p: 0 for p in self_disposited}
    for planet in chart_signs:
        if planet in ("Rahu", "Ketu"):
            continue  # nodes don't vote in classical chain analysis
        # Walk the chain
        current = planet
        seen: set[str] = set()
        while current not in self_disposited and current not in seen and current != "none":
            seen.add(current)
            sign = chart_signs.get(current)
            if sign is None:
                break
            current = SIGN_RULERS.get(sign, "none")
        if current in self_disposited:
            votes[current] += 1

    # Highest votes wins; alphabetical tie-break
    return max(sorted(self_disposited), key=lambda p: votes[p])


# ---------- The big composition ----------

def _compute_dasha_timeline_features(
    jd_birth: float,
    moon_longitude: float,
) -> dict[str, float]:
    """Continuous lifetime-Vimshottari encoding — 19 floats per chart.

    Returns:
      - `natal_dasha_remaining_years`: years left in the birth Mahadasha
        at t=birth. Always positive, range [0, ~19.0].
      - `dasha_start_age_<planet>` × 9: age (years) at which `<planet>`'s
        first Mahadasha opens in the lifetime cycle. Negative for the
        natal lord (its MD opened pre-birth) and any preceding lords if
        we cycled them in; positive for all subsequent.
      - `first_<planet>_antardasha_after_16` × 9: age at which the first
        Antardasha sub-period of `<planet>` opens at or after the
        adulthood threshold (ANTARDASHA_ADULTHOOD_AGE = 16).

    Approach: walk the 9 Mahadashas of the 120-year cycle starting from
    the natal lord (cycling through DASHA_LORDS). For each MD, expand
    into 9 ADs via the canonical `_antar_sequence` from app.core.antardasha.
    All ages computed in Vedic-year units (DAYS_PER_VEDIC_YEAR = 365.2425)
    to match the rest of the pipeline.

    A 120-year sweep guarantees every planet has at least one AD after
    age 16 for any realistic birth scenario — but we still emit NaN
    when not found (defensive; XGBoost handles NaN natively as missing).
    """
    # Reuses the production Mahadasha primitive — single source of truth
    # so test_dasha_dates.py's date pins automatically validate this code.
    md = calculate_vimshottari_mahadasha(moon_longitude, jd_birth)
    natal_lord: str = md["mahadasha_lord"]
    natal_total: float = md["total_duration_years"]
    natal_elapsed: float = md["time_elapsed_years"]
    natal_remaining: float = natal_total - natal_elapsed

    # Map planet name -> Vimshottari years (e.g. Mercury -> 17)
    lord_years: dict[str, int] = {name: yrs for name, yrs in DASHA_LORDS}
    lord_names: list[str] = [name for name, _ in DASHA_LORDS]
    start_idx = lord_names.index(natal_lord)

    # Walk the 9 Mahadashas in cycle order. The natal lord's MD began
    # `natal_elapsed` years before birth → start_age = -natal_elapsed.
    md_sequence: list[tuple[str, float, float]] = []  # (lord, start_age, total_years)
    cursor_age = -natal_elapsed
    for offset in range(len(lord_names)):
        lord = lord_names[(start_idx + offset) % len(lord_names)]
        years = float(lord_years[lord])
        md_sequence.append((lord, cursor_age, years))
        cursor_age += years

    # Each planet appears exactly once in the 9-MD cycle → its
    # dasha_start_age is the start of that MD.
    dasha_start_age: dict[str, float] = {
        lord.lower(): start_age for lord, start_age, _ in md_sequence
    }

    # Antardasha first-after-adulthood scan. Sub-period order follows the
    # same Vimshottari cycle as MDs, rotated so the first AD = MD lord.
    first_ad_after_16: dict[str, float] = {}
    for md_lord, md_start_age, md_total_years in md_sequence:
        # Cycle ADs starting from the MD lord. Inside one MD, AD durations
        # sum exactly to md_total_years (proportional split).
        md_lord_idx = lord_names.index(md_lord)
        ad_cursor_age = md_start_age
        for offset in range(len(lord_names)):
            ad_lord = lord_names[(md_lord_idx + offset) % len(lord_names)]
            ad_lord_yrs = lord_years[ad_lord]
            ad_duration = md_total_years * ad_lord_yrs / 120.0
            ad_start_age = ad_cursor_age
            ad_cursor_age += ad_duration
            if (
                ad_start_age >= ANTARDASHA_ADULTHOOD_AGE
                and ad_lord.lower() not in first_ad_after_16
            ):
                first_ad_after_16[ad_lord.lower()] = ad_start_age
        # Short-circuit once every planet has its first-after-16 AD recorded
        if len(first_ad_after_16) == len(lord_names):
            break

    features: dict[str, float] = {
        "natal_dasha_remaining_years": natal_remaining,
    }
    for lord in lord_names:
        lc = lord.lower()
        features[f"dasha_start_age_{lc}"] = dasha_start_age[lc]
        # NaN if no AD-after-16 found (theoretically impossible for a
        # full 120-yr sweep but we don't trust math we haven't tested)
        features[f"first_{lc}_antardasha_after_16"] = first_ad_after_16.get(
            lc, float("nan"),
        )
    return features


# ---------- Round 5 Vedic feature helpers ----------

# Whole-sign house distance: returns 1..12 (1 = same sign, 7 = opposition).
# Mirrors the convention in `app.core.avastha._drishti_hits`.
def _whole_sign_house_distance(from_sign: int, to_sign: int) -> int:
    return ((to_sign - from_sign) % 12) + 1


def _compute_drishti_matrix(d1_chart: dict[str, dict]) -> dict[str, int]:
    """81 binary cols: ``drishti_<from>_<to>`` = 1 iff `<from>` planet at its
    natal sign casts a classical Vedic whole-sign drishti onto the sign of
    `<to>` planet. Excludes self-aspects (always 0).

    Uses the canonical Parashara table from app.core.avastha:
      - Sun, Moon, Mercury, Venus: 7th only (opposition)
      - Mars: 4th, 7th, 8th
      - Jupiter, Rahu, Ketu: 5th, 7th, 9th
      - Saturn: 3rd, 7th, 10th

    These are the textbook directional aspects every classical prediction
    relies on. A 9×9 matrix lets the model see "who is aspecting whom"
    without having to discover the asymmetric rule from `dist_*` features.
    """
    features: dict[str, int] = {}
    for from_planet in GRAHAS:
        from_sign = d1_chart[from_planet]["sign"]
        houses = _DRISHTI_HOUSES.get(from_planet, frozenset())
        for to_planet in GRAHAS:
            if from_planet == to_planet:
                features[f"drishti_{from_planet.lower()}_{to_planet.lower()}"] = 0
                continue
            to_sign = d1_chart[to_planet]["sign"]
            distance = _whole_sign_house_distance(from_sign, to_sign)
            hit = 1 if distance in houses else 0
            features[f"drishti_{from_planet.lower()}_{to_planet.lower()}"] = hit
    return features


# Six extra divisional charts beyond the existing D1/D9/D10. Picked for
# event-type relevance: D2=wealth, D3=siblings/courage, D7=children,
# D12=parents, D24=education, D30=misfortunes/health.
EXTRA_VARGAS: tuple[tuple[str, str], ...] = (
    ("D2_Hora", "d2"),
    ("D3_Drekkana", "d3"),
    ("D4_Chaturthamsa", "d4"),
    ("D7_Saptamsa", "d7"),
    ("D12_Dwadasamsa", "d12"),
    ("D24_Chaturvimsamsa", "d24"),
    ("D30_Trimsamsa", "d30"),
)


def _compute_extra_varga_features(
    vargas: dict[str, dict[str, dict]],
) -> dict[str, int]:
    """7 vargas × 9 planet signs = 63 placement cols.

    Each `<varga>_<planet>_sign` is the sign (1..12) of that planet in
    that divisional chart. D9 / D10 already emitted by the main pipeline.
    """
    features: dict[str, int] = {}
    for varga_key, prefix in EXTRA_VARGAS:
        chart = vargas.get(varga_key, {})
        for planet in GRAHAS:
            features[f"{prefix}_{planet.lower()}_sign"] = (
                chart.get(planet, {}).get("sign", 0)
            )
    return features


def _compute_house_frames_features(
    d1_chart: dict[str, dict], moon_sign: int, sun_sign: int,
) -> dict[str, int]:
    """House-from-Moon (Chandra Lagna) + House-from-Sun (Surya Lagna) for
    each planet. 18 cols total.

    Many classical rules reference these alternative reference frames:
      - Sade Sati defined from natal Moon (not Lagna)
      - Jupiter's "best transit" houses 5/9/11 measured from natal Moon
      - Adhi Yoga = benefics in 6/7/8 *from Moon*
    """
    features: dict[str, int] = {}
    for planet in GRAHAS:
        p_sign = d1_chart[planet]["sign"]
        features[f"house_from_moon_{planet.lower()}"] = (
            _whole_sign_house_distance(moon_sign, p_sign)
        )
        features[f"house_from_sun_{planet.lower()}"] = (
            _whole_sign_house_distance(sun_sign, p_sign)
        )
    return features


def _compute_panchanga_features(jd: float) -> dict[str, Any]:
    """5 cols: tithi index, tithi paksha, karana index, panchanga yoga
    index, vara (weekday). All standard Panchanga elements used in
    muhurta and event-day classification.
    """
    p = compute_panchanga(jd)
    return {
        "panchanga_tithi": p["tithi"]["index"],
        "panchanga_paksha": p["tithi"]["paksha"],          # "Shukla"/"Krishna"
        "panchanga_karana": p["karana"]["index"],
        "panchanga_yoga": p["yoga"]["index"],
        "panchanga_vara": p["vara"]["index"],
    }


# Fixed roster of named yogas detected by app.core.yogas.detect_yogas.
# Each yoga is emitted as a binary col so the model gets a compressed
# representation of high-order planetary patterns.
EXPECTED_YOGA_NAMES: tuple[str, ...] = (
    "Bhadra", "Hamsa", "Malavya", "Ruchaka", "Sasa",  # Pancha Mahapurusha
    "Gajakesari", "Budha-Aditya",
)


def _compute_yoga_features(
    d1_chart: dict[str, dict], ascendant: dict[str, Any],
) -> dict[str, int]:
    """7 binary cols, one per known yoga from app.core.yogas.detect_yogas.

    Detected yogas: Pancha Mahapurusha (Bhadra/Hamsa/Malavya/Ruchaka/Sasa),
    Gajakesari, Budha-Aditya. Each compresses a 3-feature interaction
    (planet + dignity + house) into one binary flag — improves XGBoost
    sample efficiency on rarer event classes.
    """
    present = {y["name"] for y in detect_yogas(d1_chart, ascendant)}
    return {
        f"yoga_{name.lower().replace('-', '_')}": int(name in present)
        for name in EXPECTED_YOGA_NAMES
    }


# ---------- Round 5b: Continuous-precision layer ----------
#
# Classical Vedic uses 12-house discrete buckets because the sages
# couldn't run statistics by hand. ML can — so for every whole-sign
# feature we ALSO emit the underlying continuous degree value. The
# model can then learn sub-house thresholds (e.g. "tight 3° orb" vs
# "loose 8° orb" Saturn 7th aspect = different effects).
#
# These features don't replace the discrete ones — they augment.
# The discrete buckets compress strong signal; the continuous
# values let the model find precision-driven thresholds the sages
# couldn't have seen.

# Classical drishti house numbers (1-indexed) → target angles in degrees.
# House N from a planet sits at (N-1)*30° around the wheel.
# Includes the conjunction (house 1 = 0°) as a "0th aspect" because
# co-residency carries strong influence even though it's not "drishti".
def _aspect_target_angles(planet: str) -> list[float]:
    """Degrees from the planet at which it casts an aspect/conjunction.

    Conjunction (0°) always counts. Plus the classical aspect houses for
    the planet, converted to angles: house N → (N-1)*30°.
    """
    angles = [0.0]  # conjunction
    for house in _DRISHTI_HOUSES.get(planet, frozenset()):
        angles.append(float((house - 1) * 30))
    return angles


def _signed_arc(from_lon: float, to_lon: float) -> float:
    """Signed forward arc from `from` to `to`, in [0, 360)."""
    return (to_lon - from_lon) % 360.0


def _min_aspect_orb(
    from_planet: str, from_lon: float, to_lon: float,
) -> float:
    """Tightest orb (degrees) from `from_planet` to ANY of its classical
    aspect/conjunction angles toward `to_lon`. Returns 180.0 if `from`
    has no aspect rule (defensive — shouldn't happen for the 9 grahas).

    Smaller orb = tighter aspect = stronger classical effect. The model
    can learn that orb-thresholds matter: a Saturn 7th-aspect within 3°
    behaves differently than one at 25° (same whole-sign bucket).
    """
    targets = _aspect_target_angles(from_planet)
    if not targets:
        return 180.0
    arc = _signed_arc(from_lon, to_lon)
    return min(
        min(abs(arc - target), abs(arc - target - 360.0), abs(arc - target + 360.0))
        for target in targets
    )


def _compute_aspect_orb_matrix(
    states: dict[str, dict],
) -> dict[str, float]:
    """81 continuous-orb cols: `aspect_orb_<from>_<to>` = degrees from
    `from` planet to its nearest classical aspect angle toward `to`'s
    actual longitude.

    Diagonal (self): 0.0 (planet is exactly at itself).

    Pairs with the binary `drishti_*` matrix:
      - `drishti_saturn_mars` = 1 (whole-sign 3rd aspect hit)
      - `aspect_orb_saturn_mars` = 4.2 (4.2° from the exact 60° angle)
    Together: the model sees BOTH the categorical hit AND the precision.
    """
    features: dict[str, float] = {}
    for from_p in GRAHAS:
        from_lon = states[from_p]["lon"]
        for to_p in GRAHAS:
            if from_p == to_p:
                features[f"aspect_orb_{from_p.lower()}_{to_p.lower()}"] = 0.0
                continue
            to_lon = states[to_p]["lon"]
            features[f"aspect_orb_{from_p.lower()}_{to_p.lower()}"] = (
                _min_aspect_orb(from_p, from_lon, to_lon)
            )
    return features


def _compute_continuous_precision_features(
    states: dict[str, dict],
    ascendant: dict[str, Any],
) -> dict[str, float]:
    """Continuous analogs of the discrete whole-sign features.

    Cols emitted:
      - `house_pos_<planet>` × 9: continuous house number in [0, 12).
        Whole-sign equivalent is `house_<planet>` (1..12 integer).
      - `nak_pos_<planet>` × 9: position within nakshatra in [0, 1).
        Whole-nakshatra equivalent is `nak_<planet>` (0..26 integer).
      - `lagna_degree_in_sign`: float [0, 30). Continuous companion to
        `lagna_sign`.
      - `tithi_angle`: lunar elongation in [0, 360). Continuous
        companion to `panchanga_tithi`.
      - `yoga_angle`: (sun + moon) % 360 — continuous Panchanga yoga.
      - `moon_phase_normalized`: tithi_angle / 360 in [0, 1) — same
        info as tithi_angle but on a unit interval (helps XGBoost
        symmetric split on full vs new moon).
    """
    asc_lon = ascendant["longitude"]
    features: dict[str, float] = {}
    nak_span = 360.0 / 27.0
    for planet in GRAHAS:
        lon = states[planet]["lon"]
        # Continuous house position from Lagna
        features[f"house_pos_{planet.lower()}"] = ((lon - asc_lon) % 360.0) / 30.0
        # Position within current nakshatra, normalized to [0, 1)
        features[f"nak_pos_{planet.lower()}"] = (lon % nak_span) / nak_span

    features["lagna_degree_in_sign"] = asc_lon % 30.0
    sun_lon = states["Sun"]["lon"]
    moon_lon = states["Moon"]["lon"]
    tithi_angle = (moon_lon - sun_lon) % 360.0
    features["tithi_angle"] = tithi_angle
    features["yoga_angle"] = (sun_lon + moon_lon) % 360.0
    features["moon_phase_normalized"] = tithi_angle / 360.0
    return features


def _compute_divisional_longitude_features(
    vargas: dict[str, dict[str, dict]],
) -> dict[str, float]:
    """Continuous degree-in-sign for the marriage + career + parent
    vargas (D9, D10, D12). 27 cols.

    Whole-sign companion `d9_<planet>_sign` (etc.) already exists in
    the discrete pipeline. This adds the sub-sign precision the sages
    couldn't tabulate.
    """
    features: dict[str, float] = {}
    for varga_key, prefix in (
        ("D9_Navamsa", "d9"),
        ("D10_Dasamsa", "d10"),
        ("D12_Dwadasamsa", "d12"),
    ):
        chart = vargas.get(varga_key, {})
        for planet in GRAHAS:
            entry = chart.get(planet, {})
            features[f"{prefix}_{planet.lower()}_deg"] = float(
                entry.get("degree_in_sign", 0.0)
            )
    return features


def compute_active_pratyantar(
    event_jd: float, jd_birth: float, moon_longitude: float,
) -> dict[str, Any]:
    """Pratyantar (sub-sub-period) active at ``event_jd``.

    Returns {active_pd_lord: str, pd_elapsed_years: float}.

    Pratyantar = AD / 9. Each PT is roughly weeks to months. Where MD/AD
    give the "season", PT pinpoints the specific event window.

    Outside the natal 120-year window → sentinel "none" / NaN.
    """
    dasha = active_dasha_at(event_jd, jd_birth, moon_longitude)
    if dasha["active_md_lord"] == "none":
        return {
            "active_pd_lord": "none",
            "pd_elapsed_years": float("nan"),
        }
    # Reconstruct the active AD as an AntardashaPeriod so we can feed
    # compute_pratyantars (which expects start_jd + end_jd of one AD).
    md_lord = dasha["active_md_lord"]
    ad_lord = dasha["active_ad_lord"]
    cycle = compute_full_mahadasha_cycle(jd_birth, moon_longitude)
    # Find the MD's start/end JDs from the cycle
    md_start_jd = 0.0
    md_end_jd = 0.0
    for lord, start, end in cycle:
        if lord == md_lord and start <= event_jd <= end:
            md_start_jd, md_end_jd = start, end
            break
    md_total_years = (md_end_jd - md_start_jd) / DAYS_PER_VEDIC_YEAR

    # Walk ADs to find the active AD's start/end
    lord_years: dict[str, int] = {name: yrs for name, yrs in DASHA_LORDS}
    lord_names: list[str] = [name for name, _ in DASHA_LORDS]
    md_lord_idx = lord_names.index(md_lord)
    ad_cursor = md_start_jd
    ad_start = md_start_jd
    ad_end = md_end_jd
    for offset in range(len(lord_names)):
        candidate_lord = lord_names[(md_lord_idx + offset) % len(lord_names)]
        ad_duration_days = (
            md_total_years * lord_years[candidate_lord] / 120.0
            * DAYS_PER_VEDIC_YEAR
        )
        seg_end = ad_cursor + ad_duration_days
        if candidate_lord == ad_lord and ad_cursor <= event_jd <= seg_end:
            ad_start, ad_end = ad_cursor, seg_end
            break
        ad_cursor = seg_end

    ad_period = {
        "maha_lord": md_lord,
        "antar_lord": ad_lord,
        "start_jd": ad_start,
        "end_jd": ad_end,
    }
    pratyantars = compute_pratyantars(ad_period)  # type: ignore[arg-type]
    for pt in pratyantars:
        if pt["start_jd"] <= event_jd <= pt["end_jd"]:
            return {
                "active_pd_lord": pt["pratyantar_lord"],
                "pd_elapsed_years": (
                    (event_jd - pt["start_jd"]) / DAYS_PER_VEDIC_YEAR
                ),
            }
    return {"active_pd_lord": "none", "pd_elapsed_years": float("nan")}


def compute_full_mahadasha_cycle(
    jd_birth: float, moon_longitude: float,
) -> list[tuple[str, float, float]]:
    """Return the 9 Mahadashas spanning a full 120-year Vimshottari cycle
    anchored to ``jd_birth`` as (lord, start_jd, end_jd) tuples in cycle
    order, starting with the natal lord.

    The natal MD started ``years_elapsed`` years before ``jd_birth``
    (because birth occurred mid-MD). Each subsequent MD starts where the
    previous one ends, with duration = lord's Vimshottari weight in years.

    The whole cycle ends at ``jd_birth + (120 - years_elapsed) * DAYS_PER_VEDIC_YEAR``.
    """
    md = calculate_vimshottari_mahadasha(moon_longitude, jd_birth)
    natal_lord: str = md["mahadasha_lord"]
    natal_total: float = md["total_duration_years"]
    natal_elapsed: float = md["time_elapsed_years"]

    lord_years: dict[str, int] = {name: yrs for name, yrs in DASHA_LORDS}
    lord_names: list[str] = [name for name, _ in DASHA_LORDS]
    start_idx = lord_names.index(natal_lord)

    cursor_jd = jd_birth - natal_elapsed * DAYS_PER_VEDIC_YEAR
    cycle: list[tuple[str, float, float]] = []
    for offset in range(len(lord_names)):
        lord = lord_names[(start_idx + offset) % len(lord_names)]
        if offset == 0:
            years = natal_total
        else:
            years = float(lord_years[lord])
        start = cursor_jd
        end = start + years * DAYS_PER_VEDIC_YEAR
        cycle.append((lord, start, end))
        cursor_jd = end
    return cycle


def active_dasha_at(
    event_jd: float, jd_birth: float, moon_longitude: float,
) -> dict[str, Any]:
    """Active Mahadasha + Antardasha at an arbitrary ``event_jd``.

    Returns a dict with:
      - ``active_md_lord``: str
      - ``active_ad_lord``: str
      - ``md_elapsed_years``: float (years from MD start to event)
      - ``ad_elapsed_years``: float (years from AD start to event)

    Outside the natal 120-year window the function returns sentinel
    "none" lords and NaN elapsed values — XGBoost treats those as
    missing.
    """
    cycle = compute_full_mahadasha_cycle(jd_birth, moon_longitude)
    cycle_start = cycle[0][1]
    cycle_end = cycle[-1][2]
    if event_jd < cycle_start or event_jd > cycle_end:
        return {
            "active_md_lord": "none",
            "active_ad_lord": "none",
            "md_elapsed_years": float("nan"),
            "ad_elapsed_years": float("nan"),
        }

    # Find which MD covers event_jd
    md_lord: str = cycle[0][0]
    md_start: float = cycle[0][1]
    md_end: float = cycle[0][2]
    for lord, start, end in cycle:
        if start <= event_jd <= end:
            md_lord, md_start, md_end = lord, start, end
            break

    md_elapsed_years = (event_jd - md_start) / DAYS_PER_VEDIC_YEAR
    md_total_years = (md_end - md_start) / DAYS_PER_VEDIC_YEAR

    # Divide MD into 9 ADs starting with MD lord (same rotation as
    # compute_antardashas). Find which AD covers event_jd.
    lord_years: dict[str, int] = {name: yrs for name, yrs in DASHA_LORDS}
    lord_names: list[str] = [name for name, _ in DASHA_LORDS]
    md_lord_idx = lord_names.index(md_lord)

    ad_cursor = md_start
    ad_lord = md_lord
    ad_start = md_start
    for offset in range(len(lord_names)):
        candidate_lord = lord_names[(md_lord_idx + offset) % len(lord_names)]
        ad_duration_years = md_total_years * lord_years[candidate_lord] / 120.0
        ad_end = ad_cursor + ad_duration_years * DAYS_PER_VEDIC_YEAR
        if ad_cursor <= event_jd <= ad_end:
            ad_lord = candidate_lord
            ad_start = ad_cursor
            break
        ad_cursor = ad_end

    ad_elapsed_years = (event_jd - ad_start) / DAYS_PER_VEDIC_YEAR

    return {
        "active_md_lord": md_lord,
        "active_ad_lord": ad_lord,
        "md_elapsed_years": md_elapsed_years,
        "ad_elapsed_years": ad_elapsed_years,
    }


def _compute_kinematic_derivatives(jd: float) -> dict[str, float]:
    """Higher-order time derivatives of planetary longitudes — 13 floats.

    Acceleration (deg/day²) computed via central difference on velocities:
      acc(t) = (vel(t+1d) - vel(t-1d)) / 2

    Jerk (deg/day³) computed via central difference on accelerations,
    expanded so we only need vel samples at jd±1 and jd±2:
      jerk(t) = (acc(t+1d) - acc(t-1d)) / 2
              = (vel(t+2d) - vel(t)) / 2 / 2 - (vel(t) - vel(t-2d)) / 2 / 2
              = (vel(t+2d) - 2*vel(t) + vel(t-2d)) ... no wait
    Cleaner: just compute acc at jd±1 directly, then take their difference.

    Restricted to JERK_TRACKED_PLANETS (the slow ones: Jupiter, Saturn,
    Rahu, Ketu) because fast planet velocities change too rapidly within
    ±2 days for finite-difference jerk to carry signal over noise.

    Ketu mirrors Rahu's velocity profile (180° opposed, same time
    derivative), so we reuse Rahu's samples — saves 4 swisseph calls.
    """
    features: dict[str, float] = {}

    # ── Acceleration for all 9 planets ──
    # 8 chara grahas (Sun..Saturn + Rahu) via swisseph; Ketu mirrors Rahu.
    vel_prev: dict[str, float] = {}
    vel_next: dict[str, float] = {}
    for planet in GRAHAS:
        if planet == "Ketu":
            # Ketu inherits Rahu's velocity sign (matches the convention
            # used by compute_chart_features). Same time derivative.
            vel_prev[planet] = vel_prev["Rahu"]
            vel_next[planet] = vel_next["Rahu"]
        else:
            vel_prev[planet] = _planet_full_state(jd - 1.0, PLANETS[planet])["vel"]
            vel_next[planet] = _planet_full_state(jd + 1.0, PLANETS[planet])["vel"]

    for planet in GRAHAS:
        acc = (vel_next[planet] - vel_prev[planet]) / 2.0
        features[f"acc_{planet.lower()}"] = acc

    # ── Jerk for slow planets only ──
    # Needs vel samples at jd-2 and jd+2 to compute acc at jd±1.
    for planet in JERK_TRACKED_PLANETS:
        if planet == "Ketu":
            # Reuse Rahu samples — same caveat as above.
            vel_m2 = _planet_full_state(jd - 2.0, PLANETS["Rahu"])["vel"]
            vel_p2 = _planet_full_state(jd + 2.0, PLANETS["Rahu"])["vel"]
            vel_now = _planet_full_state(jd, PLANETS["Rahu"])["vel"]
        else:
            vel_m2 = _planet_full_state(jd - 2.0, PLANETS[planet])["vel"]
            vel_p2 = _planet_full_state(jd + 2.0, PLANETS[planet])["vel"]
            vel_now = _planet_full_state(jd, PLANETS[planet])["vel"]
        acc_minus1 = (vel_now - vel_m2) / 2.0
        acc_plus1 = (vel_p2 - vel_now) / 2.0
        jerk = (acc_plus1 - acc_minus1) / 2.0
        features[f"jerk_{planet.lower()}"] = jerk

    return features


def compute_chart_features(
    jd: float,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Compute the full Vedic Tensor for one birth chart.

    Returns a flat dict with ~150 keys (column names follow the
    `<group>_<planet>` convention so a SHAP report stays readable).

    Args:
        jd:        Julian Day in UT for the birth moment.
        latitude:  Birth lat in WGS-84 (-90..90).
        longitude: Birth lon in WGS-84 (-180..180).

    Raises:
        ValueError: if pyswisseph rejects the inputs (e.g. extreme
        historical date outside ephemeris range).
    """
    # ── Step 1: positions for the 8 chara grahas (Sun..Saturn + Rahu) ──
    states: dict[str, dict[str, float]] = {}
    for planet, planet_id in PLANETS.items():
        states[planet] = _planet_full_state(jd, planet_id)

    # ── Step 2: Ketu = Rahu reflected through the celestial origin ──
    rahu = states["Rahu"]
    states["Ketu"] = {
        "lon": (rahu["lon"] + 180.0) % 360.0,
        "lat": -rahu["lat"],
        # Ketu inherits Rahu's velocity sign convention (mean nodes are
        # always "retrograde"; true nodes oscillate). We mirror Rahu's vel.
        "vel": rahu["vel"],
    }

    # ── Step 3: declinations (FLG_EQUATORIAL) ──
    declinations: dict[str, float] = {}
    for planet, planet_id in PLANETS.items():
        declinations[planet] = _planet_declination(jd, planet_id)
    declinations["Ketu"] = -declinations["Rahu"]

    # ── Step 4: ascendant + d1_chart ──
    ascendant = calculate_ascendant(jd, latitude, longitude)
    d1_chart = _build_d1_chart(states, ascendant["sign"])

    # ── Step 5: Phase-A heavy lifting (BAV/SAV + Vargas) — single source of truth ──
    bav_matrix = compute_ashtakavarga(d1_chart, ascendant)
    vargas = compute_divisional_charts(d1_chart)

    # ── Step 6: dispositor chain ──
    chart_signs = {p: d1_chart[p]["sign"] for p in GRAHAS}
    dispositors = {p: compute_dispositor(p, chart_signs[p]) for p in GRAHAS}
    final_disp = compute_final_dispositor(chart_signs)
    chain_depths = {p: compute_dispositor_chain_depth(p, chart_signs) for p in GRAHAS}

    # ── Step 7: assemble the flat feature dict ──
    features: dict[str, Any] = {}

    # Vector 1: Base
    sun_lon = states["Sun"]["lon"]
    for planet in GRAHAS:
        s = states[planet]
        p_lower = planet.lower()
        features[f"lon_{p_lower}"] = s["lon"]
        nak = nakshatra_for_longitude(s["lon"])
        features[f"nak_{p_lower}"] = nak["index"]
        features[f"house_{p_lower}"] = d1_chart[planet]["house"]
        # Tattva: lookup region from nakshatra → tattva. Coerce categorical.
        region = region_for_nakshatra(nak["index"])
        features[f"tattva_{p_lower}"] = tattva_for_region(region)

    for p1, p2 in itertools.combinations(GRAHAS, 2):
        features[f"dist_{p1.lower()}_{p2.lower()}"] = circular_distance_180(
            states[p1]["lon"], states[p2]["lon"]
        )

    # Vector 2: Kinematic
    for planet in GRAHAS:
        s = states[planet]
        p_lower = planet.lower()
        features[f"vel_{p_lower}"] = s["vel"]
        features[f"rx_{p_lower}"] = 1 if s["vel"] < 0 else 0
        features[f"stationary_{p_lower}"] = (
            1 if abs(s["vel"]) < STATIONARY_VEL_THRESHOLD else 0
        )
        features[f"combust_{p_lower}"] = combustion_intensity(sun_lon, s["lon"], planet)
        features[f"lat_{p_lower}"] = s["lat"]
        features[f"dec_{p_lower}"] = declinations[planet]
        features[f"oob_{p_lower}"] = (
            1 if abs(declinations[planet]) > OUT_OF_BOUNDS_DECLINATION else 0
        )

    # Vector 3: Vedic — Ashtakavarga
    for i, score in enumerate(bav_matrix["sav"], start=1):
        features[f"sav_house_{i}"] = score
    for planet, bindu_per_sign in bav_matrix["bav_per_planet"].items():
        # planet's own sign-bindu count (the actually-varying piece)
        sign_idx_zero = states[planet]["lon"] // 30  # 0..11
        features[f"bav_in_sign_{planet.lower()}"] = bindu_per_sign[int(sign_idx_zero)]

    # Vector 3: Vedic — D9 / D10 placements
    d9 = vargas.get("D9_Navamsa", {})
    d10 = vargas.get("D10_Dasamsa", {})
    for planet in GRAHAS:
        features[f"d9_{planet.lower()}_sign"] = d9.get(planet, {}).get("sign", 0)
        features[f"d10_{planet.lower()}_sign"] = d10.get(planet, {}).get("sign", 0)

    # Vector 3: Vedic — dispositor graph
    for planet in GRAHAS:
        features[f"dispositor_{planet.lower()}"] = dispositors[planet]
        features[f"disp_depth_{planet.lower()}"] = chain_depths[planet]
    features["final_dispositor"] = final_disp

    # Lagna metadata
    features["lagna_lon"] = ascendant["longitude"]
    features["lagna_sign"] = ascendant["sign"]

    # Vector 4: Chronological scaffolding (Vimshottari Mahadasha + Antardasha)
    # 19 continuous floats encoding the full 120-year lifetime schedule.
    # Moon longitude is taken from the natal state computed above.
    features.update(
        _compute_dasha_timeline_features(jd, states["Moon"]["lon"]),
    )

    # Vector 5: Higher-order kinematics (acceleration + jerk)
    # 13 continuous floats; jerk restricted to slow planets where the
    # ±1-day finite difference carries genuine signal over noise.
    features.update(_compute_kinematic_derivatives(jd))

    # Vector 6 (Round 5a): Classical Vedic feature stack
    # 81 drishti + 63 extra varga + 18 house frames + 5 panchanga + 7 yogas
    features.update(_compute_drishti_matrix(d1_chart))
    features.update(_compute_extra_varga_features(vargas))
    features.update(_compute_house_frames_features(
        d1_chart, d1_chart["Moon"]["sign"], d1_chart["Sun"]["sign"],
    ))
    features.update(_compute_panchanga_features(jd))
    features.update(_compute_yoga_features(d1_chart, ascendant))

    # Vector 7 (Round 5b): Continuous-precision layer
    # The sages used whole-sign houses because they had no statistics.
    # ML can use exact degrees. These features augment (don't replace)
    # the discrete buckets so the model has both compression and precision.
    # 81 aspect orbs + 9 house_pos + 9 nak_pos + 3 lagna/tithi/yoga + 1 moon phase
    # + 27 divisional longitudes (D9/D10/D12 × 9 planets)
    features.update(_compute_aspect_orb_matrix(states))
    features.update(_compute_continuous_precision_features(states, ascendant))
    features.update(_compute_divisional_longitude_features(vargas))

    return features


# ---------- Schema introspection (for tests + Stage 3 validation) ----------

def expected_feature_columns() -> list[str]:
    """Return the canonical list of feature column names produced by
    `compute_chart_features`. Used by the schema regression test to
    catch silent column-name drift.
    """
    cols: list[str] = []

    # Base
    for p in GRAHAS:
        p = p.lower()
        cols.extend([f"lon_{p}", f"nak_{p}", f"house_{p}", f"tattva_{p}"])
    for p1, p2 in itertools.combinations(GRAHAS, 2):
        cols.append(f"dist_{p1.lower()}_{p2.lower()}")

    # Kinematic
    for p in GRAHAS:
        p = p.lower()
        cols.extend([
            f"vel_{p}", f"rx_{p}", f"stationary_{p}", f"combust_{p}",
            f"lat_{p}", f"dec_{p}", f"oob_{p}",
        ])

    # Vedic — Ashtakavarga
    cols.extend([f"sav_house_{i}" for i in range(1, 13)])
    for p in GRAHAS:
        # bav_in_sign only emitted for the 7 chara grahas (BAV table)
        if p in ("Rahu", "Ketu"):
            continue
        cols.append(f"bav_in_sign_{p.lower()}")

    # Vedic — Vargas
    for p in GRAHAS:
        cols.append(f"d9_{p.lower()}_sign")
    for p in GRAHAS:
        cols.append(f"d10_{p.lower()}_sign")

    # Vedic — Dispositors
    for p in GRAHAS:
        cols.append(f"dispositor_{p.lower()}")
    for p in GRAHAS:
        cols.append(f"disp_depth_{p.lower()}")
    cols.append("final_dispositor")

    # Lagna
    cols.extend(["lagna_lon", "lagna_sign"])

    # Vector 4: Chronological scaffolding (Vimshottari)
    # natal_dasha_remaining_years + 9 dasha_start_age_<planet> + 9 first_<planet>_antardasha_after_16
    cols.append("natal_dasha_remaining_years")
    # Use DASHA_LORDS order (Ketu-Venus-Sun-Moon-Mars-Rahu-Jupiter-Saturn-Mercury)
    # so the test pin order matches the canonical sequence.
    dasha_lord_names = [name for name, _ in DASHA_LORDS]
    for lord in dasha_lord_names:
        cols.append(f"dasha_start_age_{lord.lower()}")
    for lord in dasha_lord_names:
        cols.append(f"first_{lord.lower()}_antardasha_after_16")

    # Vector 5: Higher-order kinematics
    for p in GRAHAS:
        cols.append(f"acc_{p.lower()}")
    for p in JERK_TRACKED_PLANETS:
        cols.append(f"jerk_{p.lower()}")

    # Vector 6 (Round 5a): Classical Vedic stack (whole-sign)
    # Drishti matrix: 9x9 - 9 self = 81 (but we keep self diagonals as 0 for
    # consistent ordering; total = 81 cols).
    for from_p in GRAHAS:
        for to_p in GRAHAS:
            cols.append(f"drishti_{from_p.lower()}_{to_p.lower()}")
    # Extra divisional charts: 7 vargas × 9 planets = 63
    for _, prefix in EXTRA_VARGAS:
        for p in GRAHAS:
            cols.append(f"{prefix}_{p.lower()}_sign")
    # House frames: 9 from-Moon + 9 from-Sun = 18
    for p in GRAHAS:
        cols.append(f"house_from_moon_{p.lower()}")
    for p in GRAHAS:
        cols.append(f"house_from_sun_{p.lower()}")
    # Panchanga: 5 cols
    cols.extend([
        "panchanga_tithi", "panchanga_paksha",
        "panchanga_karana", "panchanga_yoga", "panchanga_vara",
    ])
    # Named yogas: 7 binary
    for name in EXPECTED_YOGA_NAMES:
        cols.append(f"yoga_{name.lower().replace('-', '_')}")

    # Vector 7 (Round 5b): Continuous-precision layer
    # Aspect-orb matrix 9x9 (continuous companion to drishti): 81
    for from_p in GRAHAS:
        for to_p in GRAHAS:
            cols.append(f"aspect_orb_{from_p.lower()}_{to_p.lower()}")
    # Continuous house position from Lagna: 9
    for p in GRAHAS:
        cols.append(f"house_pos_{p.lower()}")
    # Position within nakshatra (0..1): 9
    for p in GRAHAS:
        cols.append(f"nak_pos_{p.lower()}")
    # Lagna degree-in-sign + tithi/yoga angles + moon phase: 4
    cols.extend([
        "lagna_degree_in_sign",
        "tithi_angle", "yoga_angle", "moon_phase_normalized",
    ])
    # Divisional longitudes for D9/D10/D12 (3 × 9 = 27)
    for prefix in ("d9", "d10", "d12"):
        for p in GRAHAS:
            cols.append(f"{prefix}_{p.lower()}_deg")

    return cols
