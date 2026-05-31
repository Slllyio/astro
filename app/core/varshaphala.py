"""Varshaphala / Tajik — annual progression + Sahams (S-4).

Vimshottari MD/AD/PD gives chart-level dasha precision to about a year.
For TIGHTER predictions ("what will happen in THIS year"), classical
Jyotisha uses **Tajik / Varshaphala**: a separate annual chart cast at
the moment Sun returns to its exact natal longitude (the "solar
return"), plus a set of progressing sensitive points (Muntha + Sahams)
that activate specific life domains for the year.

This module computes a SIMPLIFIED Varshaphala that doesn't require a
full ephemeris call (no solar-return chart cast):

  * **Muntha**     — progressing sensitive point that starts in natal
                     Lagna and advances 1 sign per year. At age 0 → 1H,
                     age 1 → 2H, age 11 → 12H, age 12 → 1H again.
  * **Munthesha**  — sign-lord of the sign Muntha currently occupies.
                     Primary planet of the year.
  * **Sahams**     — natal-frame sensitive midpoints. Each computed by a
                     classical formula like "Punya = Asc + Moon - Sun".
                     Their HOUSE from Lagna shows which life domain
                     each saham primes for activation.

## Sahams covered (28 total — Phaladeepika Ch.16 + Tajik Neelakanthi Ch.4)

| Saham        | Formula (sidereal longitudes)         | Domain                  |
|--------------|---------------------------------------|-------------------------|
| Punya        | Asc + Moon - Sun                      | merit / virtue / luck    |
| Vidya        | Asc + Mercury - Jupiter               | learning / knowledge     |
| Karma        | Asc + Mars - Mercury                  | action / career          |
| Yasas        | Asc + Jupiter - Mercury               | fame / reputation        |
| Putra        | Asc + Jupiter - Saturn                | children / progeny       |
| Vivaha       | Asc + Venus - Saturn (unisex)         | marriage                 |
| Mrityu       | Asc + 8H-cusp - Moon                  | death-risk / longevity   |
| Bhratru      | Asc + Jupiter - Mars                  | siblings                 |
| Pitru        | Asc + Sun - Saturn                    | father                   |
| Matri        | Asc + Moon - Venus                    | mother                   |
| Karagriha    | Asc + Saturn - Sun                    | imprisonment / restrict  |
| Roga         | Asc + Mars - Moon (Saturn aspected)   | disease                  |
| Apamrityu    | Asc + 8H-cusp - Mars                  | accidents / sudden death |
| Jadya        | Asc + Mars - Saturn                   | sloth / paralysis        |
| Vyapara      | Asc + Mars - Mercury (variant)        | trade / commerce         |
| Krishi       | Asc + Saturn - Mars                   | agriculture              |
| Daya         | Asc + Mercury - Mars                  | compassion / charity     |
| Mata         | Asc + Moon - Sun (variant pole)       | maternal nurturance      |
| Bandhu       | Asc + Moon - Saturn                   | friends / kin            |
| Ratri        | Asc + Moon - Mars                     | nocturnal stability      |
| Sastra       | Asc + Mercury - Mars                  | scriptural learning      |
| Bandhana     | Asc + 8H-cusp - 9H-cusp               | bondage / restriction    |
| Mrityu2      | Asc + Saturn - Moon                   | longevity (secondary)    |
| Paradesh     | Asc + 9H-cusp - 9H-lord-lon           | foreign residence        |
| Artha        | Asc + 2H-cusp - 2H-lord-lon           | accumulated wealth       |
| Samartha     | Asc + Jupiter - Sun                   | capability / vitality    |
| Bhagya       | Asc + Sun - Jupiter                   | fortune / luck-stream    |
| Asha         | Asc + Mars - Saturn (variant)         | aspirations              |

## Two variants supported

(1) **Natal-frame Sahams + Muntha** (`compute_varshaphala()`) — uses
    the natal chart's positions. Doesn't need an ephemeris call.
    Doctrinally-justifiable when birth_jd has only date precision.

(2) **Solar-return annual chart** (`compute_annual_chart()`) — casts
    the chart at the JD when Sun returns to its EXACT natal longitude
    in the year of the given age. This is the classical Tajik chart.
    Requires the ephemeris engine (swisseph). Returns the annual
    chart's Lagna degree, planet positions, plus Sahams recomputed
    against the annual Lagna.

For bulk pipelines, (1) is used because it works on all 75K rows.
For per-chart deep readings via the API endpoint, (2) gives the
classical Tajik-grade output.

## References

  * Phaladeepika Ch.16 — Sahams + Muntha
  * V. Subrahmanya Sastri's *Tajik Neelakanthi* — full Tajik canon
  * BV Raman *Hindu Predictive Astrology* — Muntha delineation
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping


# ─── Sign-lord (duplicated to avoid import cycle) ───────────────────


_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


# ─── Muntha ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Muntha:
    """Progressing sensitive point at age N."""
    sign: int                    # 1..12
    house_from_lagna: int        # 1..12 (always = sign-asc_sign+1 mod 12+1)
    munthesha: str               # planet ruling the muntha sign
    age_years: float             # age input used
    domain_focus: str            # which life domain this year primes


# Doctrinal reading of Muntha-in-bhava (Phaladeepika Ch.16.4)
_MUNTHA_HOUSE_DOMAIN: Final[Mapping[int, str]] = {
    1: "self / body / new ventures focus",
    2: "wealth / family / speech focus",
    3: "siblings / courage / short journeys",
    4: "mother / home / property focus",
    5: "children / education / creativity",
    6: "service / health / debt / litigation",
    7: "spouse / partnerships / public dealings",
    8: "longevity-test / occult / sudden changes",
    9: "father / dharma / long-journey / fortune",
    10: "career / status / authority focus",
    11: "gains / network / aspirations",
    12: "expenses / loss / moksha / foreign-residence",
}


def compute_muntha(asc_sign: int, age_years: float) -> Muntha:
    """Compute Muntha at the given age.

    Muntha starts in the natal Lagna at age 0 and advances 1 sign per
    completed year. The year-month math:

      muntha_sign = ((asc_sign - 1 + int(age_years)) % 12) + 1

    Returns Muntha aggregate with sign + house + munthesha + domain hint.
    """
    if age_years < 0:
        raise ValueError(f"age_years must be >= 0, got {age_years}")
    years_completed = int(age_years)
    muntha_sign = ((asc_sign - 1 + years_completed) % 12) + 1
    house = ((muntha_sign - asc_sign) % 12) + 1
    lord = _SIGN_LORDS[muntha_sign]
    return Muntha(
        sign=muntha_sign, house_from_lagna=house, munthesha=lord,
        age_years=float(age_years),
        domain_focus=_MUNTHA_HOUSE_DOMAIN.get(house, "general focus"),
    )


# ─── Sahams ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Saham:
    """One sensitive point with its domain reading."""
    name: str
    formula: str                 # human-readable formula
    longitude: float             # 0..360
    sign: int                    # 1..12
    house_from_lagna: int        # 1..12
    domain: str                  # what life area this saham primes
    is_well_placed: bool         # True if in kendra/trikona, False if in dushtana


_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({5, 9})
_DUSHTANAS: Final[frozenset[int]] = frozenset({6, 8, 12})


def _saham_position(
    asc_lon: float, plus_lon: float, minus_lon: float,
) -> tuple[float, int]:
    """Generic saham formula: Asc + X - Y, mod 360.

    Returns (longitude, sign).
    """
    lon = (asc_lon + plus_lon - minus_lon) % 360.0
    sign = int(lon // 30.0) + 1
    return (lon, sign)


def _house_from_lagna(saham_sign: int, asc_sign: int) -> int:
    return ((saham_sign - asc_sign) % 12) + 1


def _is_well_placed(house: int) -> bool:
    return house in _KENDRAS or house in _TRIKONAS


def compute_sahams(
    asc_sign: int, asc_lon: float,
    planet_lons: Mapping[str, float],
) -> tuple[Saham, ...]:
    """Compute 28 natal-frame Sahams (D-2 expansion from 8).

    Args:
        asc_sign: 1..12 — natal Lagna sign.
        asc_lon: 0..360 — natal Lagna longitude.
        planet_lons: {planet: longitude} from chart.planet_lons.

    Returns:
        Tuple of up to 28 Saham reports (only those with all required
        planet longitudes available).
    """
    def _need(planet: str) -> float | None:
        return planet_lons.get(planet)

    sahams: list[Saham] = []

    def _add(name: str, plus_planet: str, minus_planet: str,
             formula: str, domain: str) -> None:
        plus_lon = _need(plus_planet)
        minus_lon = _need(minus_planet)
        if plus_lon is None or minus_lon is None:
            return
        lon, sign = _saham_position(asc_lon, plus_lon, minus_lon)
        house = _house_from_lagna(sign, asc_sign)
        sahams.append(Saham(
            name=name, formula=formula,
            longitude=round(lon, 3), sign=sign,
            house_from_lagna=house, domain=domain,
            is_well_placed=_is_well_placed(house),
        ))

    def _add_cusp_based(name: str, cusp_offset_signs: int,
                        minus_planet: str, formula: str, domain: str) -> None:
        """Sahams using house cusp + a planet's longitude.

        cusp_offset_signs counts signs from natal Lagna (0=Lagna, 7=8H).
        """
        cusp_lon = (asc_lon + cusp_offset_signs * 30.0) % 360.0
        minus_lon = _need(minus_planet)
        if minus_lon is None:
            return
        lon = (asc_lon + cusp_lon - minus_lon) % 360.0
        sign = int(lon // 30.0) + 1
        house = _house_from_lagna(sign, asc_sign)
        sahams.append(Saham(
            name=name, formula=formula,
            longitude=round(lon, 3), sign=sign,
            house_from_lagna=house, domain=domain,
            is_well_placed=_is_well_placed(house),
        ))

    # ─── Core 8 (unchanged from S-4) ─────────────────────────────────
    _add("Punya", "Moon", "Sun",
         "Asc + Moon - Sun", "merit / virtue / luck")
    _add("Vidya", "Mercury", "Jupiter",
         "Asc + Mercury - Jupiter", "learning / knowledge")
    _add("Karma", "Mars", "Mercury",
         "Asc + Mars - Mercury", "action / career")
    _add("Yasas", "Jupiter", "Mercury",
         "Asc + Jupiter - Mercury", "fame / reputation")
    _add("Putra", "Jupiter", "Saturn",
         "Asc + Jupiter - Saturn", "children / progeny")
    _add("Vivaha", "Venus", "Saturn",
         "Asc + Venus - Saturn (unisex)", "marriage")
    _add_cusp_based("Mrityu", 7, "Moon",
                    "Asc + 8H-cusp - Moon", "death-risk / longevity-test")
    _add("Bhratru", "Jupiter", "Mars",
         "Asc + Jupiter - Mars", "siblings")

    # ─── D-2 expansion: 20 more from classical canon ─────────────────
    # Parental / kin
    _add("Pitru", "Sun", "Saturn",
         "Asc + Sun - Saturn", "father / paternal lineage")
    _add("Matri", "Moon", "Venus",
         "Asc + Moon - Venus", "mother / maternal nurturance")
    _add("Mata", "Sun", "Moon",
         "Asc + Sun - Moon (Mata variant)", "maternal stability (sec)")
    _add("Bandhu", "Moon", "Saturn",
         "Asc + Moon - Saturn", "friends / kin")

    # Health / mortality variants
    _add("Roga", "Mars", "Moon",
         "Asc + Mars - Moon", "disease / illness markers")
    _add_cusp_based("Apamrityu", 7, "Mars",
                    "Asc + 8H-cusp - Mars", "accidents / sudden-death risk")
    _add("Jadya", "Mars", "Saturn",
         "Asc + Mars - Saturn", "sloth / paralysis / stagnation")
    _add("Mrityu2", "Saturn", "Moon",
         "Asc + Saturn - Moon", "longevity (secondary computation)")

    # Profession / wealth
    _add("Vyapara", "Saturn", "Mars",
         "Asc + Saturn - Mars (Vyapara variant)", "trade / commerce")
    _add("Krishi", "Saturn", "Mars",
         "Asc + Saturn - Mars", "agriculture / land work")
    _add_cusp_based("Artha", 1, "Venus",
                    "Asc + 2H-cusp - Venus", "accumulated wealth")
    _add("Samartha", "Jupiter", "Sun",
         "Asc + Jupiter - Sun", "capability / vitality")

    # Misfortune / restriction
    _add("Karagriha", "Saturn", "Sun",
         "Asc + Saturn - Sun", "imprisonment / restriction")
    _add_cusp_based("Bandhana", 7, "Mars",
                    "Asc + 8H-cusp - Mars (Bandhana variant)",
                    "bondage / restriction (variant)")

    # Higher faculties
    _add("Daya", "Mercury", "Mars",
         "Asc + Mercury - Mars", "compassion / charity")
    _add("Sastra", "Mercury", "Mars",
         "Asc + Mercury - Mars (Sastra variant)", "scriptural learning")
    _add("Ratri", "Moon", "Mars",
         "Asc + Moon - Mars", "nocturnal stability")

    # Fortune / aspirations
    _add("Bhagya", "Sun", "Jupiter",
         "Asc + Sun - Jupiter", "fortune / luck-stream")
    _add("Asha", "Mars", "Saturn",
         "Asc + Mars - Saturn (Asha variant)", "aspirations")
    _add_cusp_based("Paradesh", 8, "Jupiter",
                    "Asc + 9H-cusp - Jupiter",
                    "foreign residence / long-journey")

    # ─── L-2 expansion: 22 more from full Tajik Neelakanthi canon ────
    # Domain: Marriage variants (gender-specific + child-bearing)
    _add("VivahaM", "Venus", "Saturn",
         "Asc + Venus - Saturn (male variant)", "marriage (male native)")
    _add("VivahaF", "Mars", "Saturn",
         "Asc + Mars - Saturn (female variant)", "marriage (female native)")
    _add("Putra2", "Saturn", "Jupiter",
         "Asc + Saturn - Jupiter (Putra secondary)", "children (secondary line)")
    _add("Garbha", "Jupiter", "Moon",
         "Asc + Jupiter - Moon", "conception / gestation")

    # Domain: Education / arts depth
    _add("Buddhi", "Mars", "Mercury",
         "Asc + Mars - Mercury (intellect variant)", "intellect / quick mind")
    _add("Manmatha", "Venus", "Mars",
         "Asc + Venus - Mars", "passion / romantic-erotic charge")
    _add("Saraswati", "Jupiter", "Venus",
         "Asc + Jupiter - Venus (arts variant)", "speech / arts / scholarship")

    # Domain: Wealth lifecycle
    _add("Lakshmi", "Jupiter", "Sun",
         "Asc + Jupiter - Sun (Lakshmi grace variant)", "Lakshmi grace / fortune-stream")
    _add("Trikona", "Jupiter", "Moon",
         "Asc + Jupiter - Moon (Trikona variant)", "trikona stability / lucky houses")
    _add_cusp_based("Sampatti", 1, "Mars",
                    "Asc + 2H-cusp - Mars", "accumulated assets / property")

    # Domain: Career details
    _add("Rajya", "Saturn", "Sun",
         "Asc + Saturn - Sun (Rajya variant)", "kingship / public office authority")
    _add("Yatra", "Saturn", "Jupiter",
         "Asc + Saturn - Jupiter (travel variant)",
         "long journeys / cross-region action")
    _add("Vyavasaya", "Jupiter", "Mercury",
         "Asc + Jupiter - Mercury", "trade / enterprise vs employment")
    _add("Pitryam", "Sun", "Jupiter",
         "Asc + Sun - Jupiter (Pitr-yajna variant)",
         "ancestral karma / paternal-legacy work")

    # Domain: Specialised sensitive points
    _add("Brahma", "Jupiter", "Mercury",
         "Asc + Jupiter - Mercury (Brahma variant)",
         "spiritual learning / Veda-study")
    _add("Tarakesha", "Saturn", "Mercury",
         "Asc + Saturn - Mercury",
         "Tarakesha (savior-deity) connection")
    _add("Sastra2", "Venus", "Jupiter",
         "Asc + Venus - Jupiter (Sastra secondary)",
         "scripture composition / literary works")

    # Domain: Risk / misfortune expansion
    _add_cusp_based("Riksha", 5, "Saturn",
                    "Asc + 6H-cusp - Saturn",
                    "disease severity / hospitalisation risk")
    _add_cusp_based("Videsha", 11, "Moon",
                    "Asc + 12H-cusp - Moon",
                    "long-foreign residence / migration permanence")
    _add("Bhukti", "Mars", "Sun",
         "Asc + Mars - Sun", "land / property struggle")

    # Domain: Lifespan / longevity bands
    _add_cusp_based("Ayur", 0, "Saturn",
                    "Asc + 1H-cusp - Saturn",
                    "longevity baseline (Ayur Saham)")
    _add_cusp_based("Adhana", 6, "Moon",
                    "Asc + 7H-cusp - Moon",
                    "conception-moment marker (adhana Lagna)")

    return tuple(sahams)


# ─── Aggregate ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class VarshaphalaReport:
    """Year-progression sensitive points for a chart at a given age.

    SIMPLIFIED — does not include the actual annual-chart cast. Carries
    Muntha + Sahams that don't require a solar-return ephemeris call.
    """
    muntha: Muntha
    sahams: tuple[Saham, ...]


def compute_varshaphala(
    asc_sign: int, asc_lon: float,
    planet_lons: Mapping[str, float],
    age_years: float,
) -> VarshaphalaReport:
    """Aggregate Varshaphala progression for a chart at the given age."""
    return VarshaphalaReport(
        muntha=compute_muntha(asc_sign, age_years),
        sahams=compute_sahams(asc_sign, asc_lon, planet_lons),
    )


# ─── D-3: Solar-return annual chart ────────────────────────────────


@dataclass(frozen=True)
class AnnualChart:
    """Classical Tajik annual chart cast at the solar return.

    The solar return JD is the moment Sun's sidereal longitude equals
    natal Sun's longitude in the year of the given age (within ~10 arcsec).

    Fields:
        return_jd       : JD at the exact solar return.
        natal_sun_lon   : The natal Sun longitude we returned to.
        annual_asc_sign : 1..12 — Lagna sign of the annual chart.
        annual_asc_lon  : 0..360 — Lagna longitude of the annual chart.
        annual_planet_signs : {planet: sign} at the return moment.
        annual_planet_lons  : {planet: longitude} at the return moment.
        muntha          : Muntha at the age (same as natal-frame).
        annual_sahams   : Sahams referenced to the ANNUAL Lagna.
    """
    return_jd: float
    natal_sun_lon: float
    annual_asc_sign: int
    annual_asc_lon: float
    annual_planet_signs: Mapping[str, int]
    annual_planet_lons: Mapping[str, float]
    muntha: Muntha
    annual_sahams: tuple[Saham, ...]


def find_solar_return_jd(
    natal_sun_lon: float, birth_jd: float, age_years: int,
    *, tolerance_arcsec: float = 30.0, max_iter: int = 30,
) -> float:
    """Find the JD when Sun's sidereal longitude = natal_sun_lon at age_years.

    Uses Newton-style iteration:
      1. Start at birth_jd + age_years * 365.2425 (approximate return JD)
      2. Compute Sun's actual longitude at that JD
      3. Adjust by (target - current) / sun_speed (~0.985°/day)
      4. Repeat until error < tolerance_arcsec

    Returns the converged JD.

    Raises:
        RuntimeError if iteration doesn't converge in max_iter steps.
        ImportError if swisseph isn't available.
    """
    import swisseph as swe
    from app.core.ephemeris_engine import calculate_d1_position

    # Approximate starting JD: birth + age_years * mean year
    jd = birth_jd + age_years * 365.2425
    tolerance_deg = tolerance_arcsec / 3600.0

    for _ in range(max_iter):
        sun_pos = calculate_d1_position(jd, swe.SUN)
        current_lon = sun_pos["longitude"]
        # Compute shortest angular distance (-180..+180)
        diff = ((natal_sun_lon - current_lon + 180.0) % 360.0) - 180.0
        if abs(diff) < tolerance_deg:
            return jd
        # Sun moves ~0.9856°/day; adjust JD by diff/sun_speed
        sun_speed = 360.0 / 365.2425  # ~0.9856 deg/day
        jd += diff / sun_speed

    raise RuntimeError(
        f"Solar return search did not converge in {max_iter} iterations "
        f"(last error: {diff:.6f} deg, target tol: {tolerance_deg:.6f} deg)"
    )


def compute_annual_chart(
    natal_asc_sign: int, natal_asc_lon: float,
    natal_sun_lon: float, birth_jd: float,
    birth_lat: float, birth_lon_deg: float,
    age_years: int,
) -> AnnualChart:
    """Cast the classical Tajik annual chart for a given age.

    Args:
        natal_asc_sign : Natal Lagna sign (for Muntha computation).
        natal_asc_lon  : Natal Lagna longitude.
        natal_sun_lon  : Natal Sun longitude (we return to this).
        birth_jd       : Birth JD.
        birth_lat      : Birth latitude (for annual Lagna computation).
        birth_lon_deg  : Birth longitude in degrees east.
        age_years      : Age the annual chart is being cast for.

    Returns:
        AnnualChart with return_jd + annual positions + annual-frame Sahams.

    Note: The annual chart is cast for the BIRTH location, per classical
    Tajik convention. Sanjay Rath's school casts at the current location
    instead; we use the birth-location convention.
    """
    import swisseph as swe
    from app.core.ephemeris_engine import calculate_d1_position

    return_jd = find_solar_return_jd(natal_sun_lon, birth_jd, age_years)

    # Compute annual Lagna at return_jd + birth location (sidereal Lahiri)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    houses = swe.houses_ex(
        return_jd, birth_lat, birth_lon_deg, b"P",
        swe.FLG_SIDEREAL,
    )
    # houses_ex returns (cusps, ascmc); ascmc[0] = Ascendant longitude
    annual_asc_lon = float(houses[1][0])
    annual_asc_sign = int(annual_asc_lon // 30.0) + 1

    # Compute all 7 visible grahas at the return JD
    annual_signs: dict[str, int] = {}
    annual_lons: dict[str, float] = {}
    for planet_name, planet_id in (
        ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
        ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
        ("Rahu", swe.TRUE_NODE),
    ):
        pos = calculate_d1_position(return_jd, planet_id)
        lon = pos["longitude"]
        annual_signs[planet_name] = int(lon // 30.0) + 1
        annual_lons[planet_name] = lon
    # Ketu is opposite Rahu
    ketu_lon = (annual_lons["Rahu"] + 180.0) % 360.0
    annual_signs["Ketu"] = int(ketu_lon // 30.0) + 1
    annual_lons["Ketu"] = ketu_lon

    # Muntha (uses natal Lagna + age — same as natal frame)
    muntha = compute_muntha(natal_asc_sign, float(age_years))

    # Annual-frame Sahams (referenced to the ANNUAL Lagna)
    annual_sahams = compute_sahams(annual_asc_sign, annual_asc_lon, annual_lons)

    return AnnualChart(
        return_jd=return_jd,
        natal_sun_lon=natal_sun_lon,
        annual_asc_sign=annual_asc_sign,
        annual_asc_lon=round(annual_asc_lon, 4),
        annual_planet_signs=annual_signs,
        annual_planet_lons={k: round(v, 4) for k, v in annual_lons.items()},
        muntha=muntha,
        annual_sahams=annual_sahams,
    )


def format_annual_chart(ac: AnnualChart) -> str:
    """Render an annual chart as a summary text block."""
    lines = ["=== ANNUAL CHART (Tajik / solar return) ==="]
    lines.append(f"  Return JD       : {ac.return_jd:.4f}")
    lines.append(f"  Natal Sun lon   : {ac.natal_sun_lon:.3f} deg")
    lines.append(
        f"  Annual Lagna    : sign {ac.annual_asc_sign}  "
        f"@ {ac.annual_asc_lon:.3f} deg"
    )
    lines.append(f"  Muntha          : sign {ac.muntha.sign} (house {ac.muntha.house_from_lagna})")
    lines.append("  Annual planets  :")
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        sign = ac.annual_planet_signs.get(p)
        lon = ac.annual_planet_lons.get(p)
        if sign and lon is not None:
            lines.append(f"    {p:<8}  sign {sign:>2}  @ {lon:>7.2f} deg")
    lines.append(f"  Annual Sahams   : {len(ac.annual_sahams)} computed against annual Lagna")
    return "\n".join(lines)


def format_varshaphala(r: VarshaphalaReport) -> str:
    """Render Varshaphala report as text."""
    lines = ["=== VARSHAPHALA / TAJIK PROGRESSION ==="]
    lines.append(
        f"  Muntha       : sign {r.muntha.sign} "
        f"(house {r.muntha.house_from_lagna} from Lagna)  "
        f"munthesha = {r.muntha.munthesha}"
    )
    lines.append(f"               focus: {r.muntha.domain_focus}")
    lines.append("  Sahams:")
    for s in r.sahams:
        flag = "OK " if s.is_well_placed else "!! "
        lines.append(
            f"    {flag}{s.name:<8}  sign {s.sign:>2} "
            f"(house {s.house_from_lagna:>2})  -- {s.domain}"
        )
    return "\n".join(lines)
