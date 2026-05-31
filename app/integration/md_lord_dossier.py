"""M3 — MD-lord natal dossier (BPHS Ch.46 Dasha Phala).

For the active MD lord, produce a full natal profile that a master
astrologer would consult before pronouncing on the MD period.

BPHS Ch.46 (Dasha Phala) says the lord of the running dasha gives
results "according to its placement, lordship, and dignity". This module
flattens those three dimensions into a single typed object.

Public surface
--------------
- ``build_md_lord_dossier(reading, *, target_jd=None, md_lord=None)``
  -> ``MDLordDossier``

When ``md_lord`` is None, the dossier is built for whichever MD is
active at ``target_jd`` (defaults to now). Pass ``md_lord`` explicitly
to read a future or past MD lord's natal profile.

Output fields (12+):
- planet, house, sign, sign_name
- dignity (own / exalted / debilitated / friendly / enemy / neutral)
- baladi avastha (life-stage), deeptadi avastha (mental state)
- is_retrograde, conjunctions (planets within 8° same sign)
- houses_ruled (relative to current lagna)
- functional_role (yogakaraka / maraka / badhakesh / benefic / malefic)
- aspects_to (which houses Saturn-style 10, 3rd, or Jupiter-style 5, 9)
- yogas_participated_in (list of yoga names that include this planet)
- atmakaraka_match (True if this is the AK)
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.core.functional_roles import functional_roles as _track_b_functional_roles
from app.integration.dasha_now import md_at_jd
from app.integration.gap_annotator import annotate_with_gap_modules


_SIGN_NAMES = (
    "", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Exaltation + debilitation signs per planet (BPHS standard).
_EXALTED: dict[str, int] = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6,
    "Jupiter": 4, "Venus": 12, "Saturn": 7,
}
_DEBILITATED: dict[str, int] = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12,
    "Jupiter": 10, "Venus": 6, "Saturn": 1,
}

# Own signs per planet (Mars: Aries+Scorpio; Mercury: Gemini+Virgo; etc.)
_OWN_SIGNS: dict[str, tuple[int, ...]] = {
    "Sun": (5,), "Moon": (4,), "Mars": (1, 8),
    "Mercury": (3, 6), "Jupiter": (9, 12),
    "Venus": (2, 7), "Saturn": (10, 11),
}

# Sign rulership: sign -> planet
_SIGN_LORDS: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun",
    6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn",
    11: "Saturn", 12: "Jupiter",
}

# Friend/enemy table per BPHS Ch.4. Each planet's friends.
_FRIENDS: dict[str, frozenset[str]] = {
    "Sun":     frozenset({"Moon", "Mars", "Jupiter"}),
    "Moon":    frozenset({"Sun", "Mercury"}),
    "Mars":    frozenset({"Sun", "Moon", "Jupiter"}),
    "Mercury": frozenset({"Sun", "Venus"}),
    "Jupiter": frozenset({"Sun", "Moon", "Mars"}),
    "Venus":   frozenset({"Mercury", "Saturn"}),
    "Saturn":  frozenset({"Mercury", "Venus"}),
}

# Each planet's standard Parashari aspects (additional to 7th).
# All planets aspect the 7th.
_SPECIAL_ASPECTS: dict[str, tuple[int, ...]] = {
    "Sun":     (),
    "Moon":    (),
    "Mars":    (4, 8),
    "Mercury": (),
    "Jupiter": (5, 9),
    "Venus":   (),
    "Saturn":  (3, 10),
    "Rahu":    (5, 9),   # modern Sukra Nadi (per project D-1 lock)
    "Ketu":    (5, 9),
}


class MDLordDossier(BaseModel):
    """Full natal profile of one MD lord."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    planet: str
    md_start_date: str
    md_end_date: str
    age_at_md_start: float
    age_at_md_end: float

    # Natal placement
    house: int = Field(ge=1, le=12)
    sign: int = Field(ge=1, le=12)
    sign_name: str
    degree_in_sign: float = Field(ge=0.0, lt=30.0)
    is_retrograde: bool

    # Dignity
    dignity: str  # exalted / debilitated / own / friendly / enemy / neutral

    # Avastha (from Gap-F)
    baladi_stage: str | None = None
    baladi_multiplier: float | None = None
    deeptadi_state: str | None = None
    deeptadi_multiplier: float | None = None

    # Lordship + functional role
    houses_ruled_from_lagna: tuple[int, ...]
    functional_role: str  # yogakaraka / maraka / badhakesh / benefic / malefic / lagna_lord / neutral

    # Conjunctions (planets within 8° in the same sign)
    conjunctions: tuple[str, ...]

    # Aspects given (houses receiving this planet's drishti)
    houses_aspected: tuple[int, ...]

    # Yogas this planet participates in (rule IDs from the reading)
    yogas_participated_in: tuple[str, ...]

    # Is this the chart's Atmakaraka?
    is_atmakaraka: bool

    # Narrative summary (one-line)
    summary: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dignity_for(planet: str, sign: int) -> str:
    """Determine dignity per BPHS table."""
    if _EXALTED.get(planet) == sign:
        return "exalted"
    if _DEBILITATED.get(planet) == sign:
        return "debilitated"
    if sign in _OWN_SIGNS.get(planet, ()):
        return "own"
    sign_lord = _SIGN_LORDS.get(sign)
    if sign_lord and planet != sign_lord:
        if sign_lord in _FRIENDS.get(planet, frozenset()):
            return "friendly"
        # Default is neutral; full enemy logic per BPHS Ch.4 would
        # require enemy table — kept simple here.
        return "neutral"
    return "neutral"


def _houses_aspected(planet: str, house: int) -> tuple[int, ...]:
    """Compute houses receiving the planet's drishti from its placement."""
    # 7th aspect is universal
    base = {((house - 1 + 6) % 12) + 1}
    for offset in _SPECIAL_ASPECTS.get(planet, ()):
        base.add(((house - 1 + offset - 1) % 12) + 1)
    return tuple(sorted(base))


def _conjunctions(
    planet: str, planet_data: dict, all_planets: dict, orb: float = 8.0,
) -> tuple[str, ...]:
    """Planets within ``orb`` degrees of ``planet`` in the same sign."""
    sign = planet_data.get("sign")
    lon = planet_data.get("longitude")
    if sign is None or lon is None:
        return ()
    out: list[str] = []
    for other_name, other_data in all_planets.items():
        if other_name == planet:
            continue
        if other_data.get("sign") != sign:
            continue
        other_lon = other_data.get("longitude")
        if other_lon is None:
            continue
        if abs(other_lon - lon) <= orb:
            out.append(other_name)
    return tuple(sorted(out))


def _atmakaraka(planets: dict, mode: int = 7) -> str | None:
    """Highest degree-in-sign among the 7 classical planets per Jaimini."""
    ak: str | None = None
    ak_deg = -1.0
    candidates = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    if mode == 8:
        candidates = candidates + ("Rahu",)
    for name in candidates:
        body = planets.get(name) or {}
        deg = body.get("degree_in_sign")
        if isinstance(deg, (int, float)) and deg > ak_deg:
            ak_deg = float(deg)
            ak = name
    return ak


def _yogas_participated(
    reading: Mapping[str, Any], planet: str,
) -> tuple[str, ...]:
    """Find rule IDs of yoga findings that mention this planet."""
    out: set[str] = set()

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("classification") == "yoga":
                evidence = " ".join(str(e) for e in (node.get("evidence") or []))
                text = (node.get("verdict", "") + " " + evidence).lower()
                if planet.lower() in text:
                    out.add(node.get("rule", ""))
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(reading)
    return tuple(sorted(out))


def _summary_line(
    planet: str, house: int, sign_name: str, dignity: str,
    functional_role: str, baladi: str | None,
) -> str:
    """Compose a single readable line."""
    bits = [f"{planet} in {house}H {sign_name}"]
    if dignity not in ("neutral",):
        bits.append(f"({dignity})")
    if functional_role and functional_role != "neutral":
        bits.append(f"[{functional_role}]")
    if baladi:
        bits.append(f"baladi={baladi}")
    return " ".join(bits)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_md_lord_dossier(
    reading: Mapping[str, Any],
    *,
    target_jd: float | None = None,
    md_lord: str | None = None,
) -> MDLordDossier:
    """Build a natal dossier for the MD lord active at ``target_jd``.

    If ``md_lord`` is supplied, the dossier is built for that planet
    regardless of which MD is active at target_jd (useful for inspecting
    a past or future MD).
    """
    md = md_at_jd(reading, target_jd=target_jd)
    planet = md_lord or md.md_lord

    chart = reading.get("chart") or {}
    planets = chart.get("planets") or {}
    asc_sign = int((chart.get("cusps") or {}).get("sign", 1))

    body = planets.get(planet)
    if not isinstance(body, dict):
        raise ValueError(
            f"planet {planet!r} not found in reading.chart.planets"
        )

    house = int(body.get("house", 0))
    sign = int(body.get("sign", 0))
    sign_name = _SIGN_NAMES[sign] if 1 <= sign <= 12 else "?"
    degree_in_sign = float(body.get("degree_in_sign", 0.0))
    is_retrograde = bool(body.get("is_retrograde", False))

    dignity = _dignity_for(planet, sign)

    # Avastha via Gap modules
    baladi_stage: str | None = None
    baladi_mult: float | None = None
    deeptadi_state: str | None = None
    deeptadi_mult: float | None = None
    try:
        gap = annotate_with_gap_modules(reading)
        f = gap.gap_modules.get("F")
        if f and f.available:
            bal_block = (f.result or {}).get("baladi") or {}
            deep_block = (f.result or {}).get("deeptadi") or {}
            bal_p = bal_block.get(planet) or {}
            deep_p = deep_block.get(planet) or {}
            baladi_stage = bal_p.get("stage")
            baladi_mult = bal_p.get("strength_multiplier")
            deeptadi_state = deep_p.get("state")
            deeptadi_mult = deep_p.get("strength_multiplier")
    except Exception:
        pass

    # Lordships + functional role
    houses_ruled: tuple[int, ...] = ()
    functional_role = "neutral"
    try:
        roles = _track_b_functional_roles(asc_sign)
        role = roles.get(planet)
        if role is not None:
            houses_ruled = tuple(role.houses_ruled)
            # Pick the most prominent flag
            if getattr(role, "is_yogakaraka", False):
                functional_role = "yogakaraka"
            elif getattr(role, "is_badhakesh", False):
                functional_role = "badhakesh"
            elif getattr(role, "is_maraka", False):
                functional_role = "maraka"
            elif getattr(role, "is_functional_benefic", False):
                functional_role = "benefic"
            elif getattr(role, "is_functional_malefic", False):
                functional_role = "malefic"
            elif getattr(role, "is_lagna_lord", False):
                functional_role = "lagna_lord"
    except Exception:
        pass

    conjunctions = _conjunctions(planet, body, planets)
    houses_aspected = _houses_aspected(planet, house)
    yogas = _yogas_participated(reading, planet)
    ak = _atmakaraka(planets, mode=7)
    is_atmakaraka = (ak == planet)
    summary = _summary_line(
        planet, house, sign_name, dignity, functional_role, baladi_stage,
    )

    return MDLordDossier(
        planet=planet,
        md_start_date=md.start_date,
        md_end_date=md.end_date,
        age_at_md_start=md.age_at_start_years,
        age_at_md_end=md.age_at_end_years,
        house=house,
        sign=sign,
        sign_name=sign_name,
        degree_in_sign=degree_in_sign,
        is_retrograde=is_retrograde,
        dignity=dignity,
        baladi_stage=baladi_stage,
        baladi_multiplier=baladi_mult,
        deeptadi_state=deeptadi_state,
        deeptadi_multiplier=deeptadi_mult,
        houses_ruled_from_lagna=houses_ruled,
        functional_role=functional_role,
        conjunctions=conjunctions,
        houses_aspected=houses_aspected,
        yogas_participated_in=yogas,
        is_atmakaraka=is_atmakaraka,
        summary=summary,
    )
