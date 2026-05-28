"""Shadbala — six-fold planetary strength. Phase 0: Sthana-bala only.

Per BPHS Adhyaya 27 the total strength of a planet (in *virupa* units;
60 virupa = 1 *rupa*) is the sum of six components:

    Sthana-bala     — positional strength (this module — Phase 0)
    Dig-bala        — directional strength (Phase 1)
    Kala-bala       — temporal strength (Phase 1)
    Cheshta-bala    — motional strength (Phase 1)
    Naisargika-bala — natural / innate strength (Phase 1; trivial constants)
    Drik-bala       — aspectual strength (Phase 1)

Sthana-bala itself decomposes into five sub-components:

    Uchcha bala         — arc from debilitation point (0–60 virupa).
    Saptavargaja bala   — compound dignity over 7 divisional charts (max ~315).
                          Phase 0 simplifies this to D1 dignity only,
                          using ``naisargika_relation`` rather than the full
                          compound relation. Phase 1 fills out D2/D3/D7/
                          D9/D12/D30 using ``compound_relation``.
    Oja-Yugma bala      — masculine / feminine sign alignment in D1 and D9
                          (max 30 virupa).
    Kendradi bala       — kendra / panaphara / apoklima house (60 / 30 / 15).
    Drekkana bala       — planet's gender aligned with its drekkana (15).

References: BPHS 27.6–27.55 (Sphuta Bala Adhyaya).
"""
from __future__ import annotations

from app.core.dignity import (
    DEBILITATION,
    EXALTATION,
    SIGN_RULERS,
    dignity_state_compound,
    is_debilitated,
    is_exalted,
    is_moolatrikona,
    is_own_sign,
    naisargika_relation,
)

# --------------------------------------------------------------------------- #
# Planet-gender classification (BPHS 27)                                      #
# --------------------------------------------------------------------------- #
# Note: BPHS uses DIFFERENT gender classifications for Drekkana-bala vs
# Oja-Yugma-bala — Mercury and Saturn are *neuter* for Drekkana (1st/2nd/3rd
# decanate alignment) but *masculine* for Oja-Yugma (odd/even sign parity).
# Phase-1 audit fix: previously Mercury/Saturn were treated as Oja-Yugma
# neuter (=0), suppressing their strength. BPHS 27.28-30 is explicit that
# Mercury and Saturn gain odd-sign strength alongside Sun/Mars/Jupiter.

# Drekkana classifications (BPHS 27.31-32)
_DREKKANA_MALE: frozenset[str] = frozenset({"Sun", "Mars", "Jupiter"})
_DREKKANA_NEUTER: frozenset[str] = frozenset({"Mercury", "Saturn"})
_DREKKANA_FEMALE: frozenset[str] = frozenset({"Moon", "Venus"})

# Oja-Yugma classifications (BPHS 27.28-30) — Mercury & Saturn are MALE here.
_OJA_YUGMA_MALE: frozenset[str] = frozenset(
    {"Sun", "Mars", "Jupiter", "Mercury", "Saturn"}
)
_OJA_YUGMA_FEMALE: frozenset[str] = frozenset({"Moon", "Venus"})

_KNOWN_PLANETS: frozenset[str] = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
     "Rahu", "Ketu"}
)

# Saptavargaja virupa values per BPHS 27.19-22 (Phase-2 full 9-tier table).
# Phase-1 (3-tier naisargika) and Phase-2 (5-tier compound) tables both
# encoded here; the 3-tier entries (friendly/neutral/inimical) remain as
# a fallback when chart context isn't available.
_SAPTAVARGAJA_D1_VIRUPA: dict[str, float] = {
    # Anchor tiers (sign-based, no chart context needed)
    "moolatrikona": 45.0,
    "own":          30.0,
    "exalted":      20.0,
    "debilitated":   0.0,
    # 3-tier naisargika fallback (when chart not provided)
    "friendly":     15.0,
    "neutral":       7.5,
    "inimical":      3.75,
    # 5-tier compound (BPHS canonical when chart provided)
    "adhi_mitra":   15.0,    # naisargika friend + temporal friend
    "mitra":         7.5,    # naisargika neutral + temporal friend
    "sama":          3.75,   # mixed (friend+enemy or enemy+friend)
    "shatru":        1.875,  # naisargika neutral + temporal enemy
    "adhi_shatru":   0.0,    # naisargika enemy + temporal enemy
}

# House categories per BPHS 27. Note: 60/30/15 is the Kendradi-bala scale.
_KENDRA: frozenset[int] = frozenset({1, 4, 7, 10})
_PANAPHARA: frozenset[int] = frozenset({2, 5, 8, 11})
_APOKLIMA: frozenset[int] = frozenset({3, 6, 9, 12})


# Naisargika-bala — constant per-planet "innate" strength per BPHS 27.34.
# Saturn weakest, Sun strongest, descending in 60/7 ≈ 8.571 steps. Sources
# unanimously cite these in the order Sun > Moon > Venus > Jupiter >
# Mercury > Mars > Saturn. Some texts give Naisargika-bala in *virupa*,
# others in *rupa* (60 virupa per rupa); we use virupa for consistency
# with the rest of Shadbala.
_NAISARGIKA_BALA: dict[str, float] = {
    "Sun":     60.000,    # 60 × 7/7 — most natural strength
    "Moon":    51.429,    # 60 × 6/7
    "Venus":   42.857,    # 60 × 5/7
    "Jupiter": 34.286,    # 60 × 4/7
    "Mercury": 25.714,    # 60 × 3/7
    "Mars":    17.143,    # 60 × 2/7
    "Saturn":   8.571,    # 60 × 1/7
}


# Maximum theoretical Phase-2 Shadbala in virupa per planet.
# Sthana 210 + Dig 60 + Kala 60 + Cheshta 60 + Naisargika 60 + Drik 60 = 510.
# Naisargika max is 60 (Sun); other planets cap lower per the table above.
# For STRENGTH-NORMALISATION purposes (e.g. Vipareeta strength formula), we
# use a per-planet ceiling that accounts for each planet's naisargika cap.
def _max_shadbala_ceiling(planet: str) -> float:
    """Maximum theoretical Shadbala (virupa) for a planet — Phase-2 build.

    Components contribute (with planet-specific caps):
        Sthana   ≤ 210
        Dig      ≤ 60
        Kala     ≤ 60   (Phase 2 — partial)
        Cheshta  ≤ 60
        Naisargika ≤ Sun's 60; each other planet has lower cap (see table)
        Drik     ≤ 60
    Total per planet = 510 (Sun) down to ≈ 458.5 (Saturn).
    """
    nais_cap = _NAISARGIKA_BALA.get(planet, 0.0)
    return 210.0 + 60.0 + 60.0 + 60.0 + nais_cap + 60.0


# --------------------------------------------------------------------------- #
# Sub-component: Uchcha (exaltation) bala                                     #
# --------------------------------------------------------------------------- #

def _exalt_longitude(planet: str) -> float | None:
    """Absolute longitude (deg) of the planet's deep exaltation point.

    Returns ``None`` for the nodes (no classical exaltation arc applied
    here — Phase 0 leaves nodal uchcha at 0).
    """
    deep_exalt_degree_in_sign: dict[str, float] = {
        "Sun":     10.0,   # Aries 10°
        "Moon":     3.0,   # Taurus 3°
        "Mars":    28.0,   # Capricorn 28°
        "Mercury": 15.0,   # Virgo 15°
        "Jupiter":  5.0,   # Cancer 5°
        "Venus":   27.0,   # Pisces 27°
        "Saturn":  20.0,   # Libra 20°
    }
    if planet not in deep_exalt_degree_in_sign:
        return None
    sign = EXALTATION[planet]  # 1-indexed
    return (sign - 1) * 30.0 + deep_exalt_degree_in_sign[planet]


def uchcha_bala(planet: str, longitude: float) -> float:
    """Exaltation strength in virupa: arc from the planet's neecha point / 3.

    At deep exaltation: 60 virupa (maximum).
    At deep debilitation (180° opposite): 0 virupa (minimum).
    Linear interpolation between.

    Rahu/Ketu return 0 in Phase 0.
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    exalt_lon = _exalt_longitude(planet)
    if exalt_lon is None:
        return 0.0
    # Debilitation longitude is 180° from exaltation.
    debil_lon = (exalt_lon + 180.0) % 360.0
    # Shortest arc from the debilitation point.
    diff = (longitude - debil_lon) % 360.0
    arc = min(diff, 360.0 - diff)
    return arc / 3.0


# --------------------------------------------------------------------------- #
# Sub-component: Saptavargaja bala (Phase 0 simplification: D1 only)          #
# --------------------------------------------------------------------------- #

def _dignity_virupa_d1(
    planet: str,
    sign: int,
    longitude: float | None = None,
    chart: dict | None = None,
) -> float:
    """Virupa value of the planet's dignity in D1 per BPHS 27.19-22.

    Two paths:

    1. **Compound 5-tier** (when ``chart`` is provided): uses BPHS-canonical
       9-tier resolution via ``dignity_state_compound``:
           moolatrikona (45) > own (30) > exalted (20) > debilitated (0)
           > adhi_mitra (15) > mitra (7.5) > sama (3.75) >
             shatru (1.875) > adhi_shatru (0)

    2. **Naisargika 3-tier fallback** (when ``chart`` is None — Phase-1
       behaviour, kept for backward compatibility with unit tests that
       only have planet+sign): collapses adhi_mitra/mitra into "friendly"
       (15), sama into "neutral" (7.5), and shatru/adhi_shatru into
       "inimical" (3.75).

    ``longitude`` enables Moolatrikona detection in both paths.
    """
    # Moolatrikona check is sign+longitude based, same in both paths.
    if longitude is not None and is_moolatrikona(planet, longitude):
        return _SAPTAVARGAJA_D1_VIRUPA["moolatrikona"]

    if chart is not None:
        # Phase-2 compound 5-tier path.
        state = dignity_state_compound(
            planet, sign, chart, longitude=longitude
        )
        return _SAPTAVARGAJA_D1_VIRUPA[state]

    # Phase-1 naisargika 3-tier fallback (no chart provided).
    if is_own_sign(planet, sign):
        return _SAPTAVARGAJA_D1_VIRUPA["own"]
    if is_exalted(planet, sign):
        return _SAPTAVARGAJA_D1_VIRUPA["exalted"]
    if is_debilitated(planet, sign):
        return _SAPTAVARGAJA_D1_VIRUPA["debilitated"]
    ruler = SIGN_RULERS[sign]
    try:
        relation = naisargika_relation(planet, ruler)
    except ValueError:
        return 0.0
    if relation == "friend":
        return _SAPTAVARGAJA_D1_VIRUPA["friendly"]
    if relation == "enemy":
        return _SAPTAVARGAJA_D1_VIRUPA["inimical"]
    return _SAPTAVARGAJA_D1_VIRUPA["neutral"]


def saptavargaja_bala_d1(
    planet: str,
    d1_sign: int,
    *,
    longitude: float | None = None,
    chart: dict | None = None,
) -> float:
    """Phase-2 Saptavargaja-bala D1 with optional compound dignity.

    Range: 0 (debilitated / adhi_shatru) to 45 (moolatrikona).

    When ``chart`` is provided, uses BPHS 5-tier compound resolution
    (adhi_mitra/mitra/sama/shatru/adhi_shatru). Without it, falls back
    to the 3-tier naisargika simplification (Phase-1 behaviour).

    Phase 2b will extend this from D1 only to all 7 vargas
    (D1/D2/D3/D7/D9/D12/D30), summing each varga's virupa for the full
    Saptavargaja-bala (max ~315).
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    if not (1 <= d1_sign <= 12):
        raise ValueError(f"d1_sign out of range: {d1_sign!r}")
    return _dignity_virupa_d1(
        planet, d1_sign, longitude=longitude, chart=chart
    )


# --------------------------------------------------------------------------- #
# Sub-component: Oja-Yugma bala                                               #
# --------------------------------------------------------------------------- #

def oja_yugma_bala(planet: str, d1_sign: int, d9_sign: int) -> float:
    """Masculine/feminine sign alignment in Rashi (D1) and Navamsa (D9).

    Per BPHS 27.28-30:
    - Male planets (Sun, Mars, Jupiter, Mercury, Saturn) → +15 per odd
      sign placement.
    - Female planets (Moon, Venus) → +15 per even sign placement.
    - Lunar nodes (Rahu, Ketu) → 0 (no classical Oja-Yugma assignment).

    Phase-1 audit fix: Mercury and Saturn — previously treated as neuter
    here (=0) — now correctly classified as masculine per BPHS 27.28.
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    if not (1 <= d1_sign <= 12) or not (1 <= d9_sign <= 12):
        raise ValueError(f"sign out of range: d1={d1_sign} d9={d9_sign}")
    if planet not in _OJA_YUGMA_MALE and planet not in _OJA_YUGMA_FEMALE:
        return 0.0
    is_odd_d1 = (d1_sign % 2) == 1
    is_odd_d9 = (d9_sign % 2) == 1
    bala = 0.0
    if planet in _OJA_YUGMA_MALE:
        if is_odd_d1:
            bala += 15.0
        if is_odd_d9:
            bala += 15.0
    else:
        if not is_odd_d1:
            bala += 15.0
        if not is_odd_d9:
            bala += 15.0
    return bala


# --------------------------------------------------------------------------- #
# Sub-component: Kendradi bala                                                #
# --------------------------------------------------------------------------- #

def kendradi_bala(house: int) -> float:
    """60 virupa in kendra, 30 in panaphara, 15 in apoklima."""
    if not (1 <= house <= 12):
        raise ValueError(f"house out of range: {house!r}")
    if house in _KENDRA:
        return 60.0
    if house in _PANAPHARA:
        return 30.0
    return 15.0  # _APOKLIMA — the remaining 3, 6, 9, 12.


# --------------------------------------------------------------------------- #
# Sub-component: Drekkana bala                                                #
# --------------------------------------------------------------------------- #

def drekkana_bala(planet: str, longitude: float) -> float:
    """15 virupa when a planet's gender aligns with its drekkana.

    Drekkanas split a sign into three 10° decanates per BPHS 27.31-32:
    - 0°–10°  → 1st drekkana: male planets (Sun, Mars, Jupiter) gain.
    - 10°–20° → 2nd drekkana: neuter planets (Mercury, Saturn) gain.
    - 20°–30° → 3rd drekkana: female planets (Moon, Venus) gain.

    Nodes get 0 (no classical drekkana-bala assignment).
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    if planet in {"Rahu", "Ketu"}:
        return 0.0
    deg_in_sign = longitude % 30.0
    if 0.0 <= deg_in_sign < 10.0:
        return 15.0 if planet in _DREKKANA_MALE else 0.0
    if 10.0 <= deg_in_sign < 20.0:
        return 15.0 if planet in _DREKKANA_NEUTER else 0.0
    return 15.0 if planet in _DREKKANA_FEMALE else 0.0


# --------------------------------------------------------------------------- #
# Sthana-bala aggregate                                                       #
# --------------------------------------------------------------------------- #

def sthana_bala(
    planet: str,
    *,
    longitude: float,
    d1_sign: int,
    d9_sign: int,
    house: int,
    chart: dict | None = None,
) -> dict[str, float]:
    """Aggregate Sthana-bala. Returns the five sub-components plus total.

    All values are in virupa. When ``chart`` is provided, Saptavargaja
    uses the Phase-2 5-tier compound dignity resolution; otherwise falls
    back to Phase-1 3-tier naisargika.
    """
    u = uchcha_bala(planet, longitude)
    s = saptavargaja_bala_d1(planet, d1_sign, longitude=longitude, chart=chart)
    o = oja_yugma_bala(planet, d1_sign, d9_sign)
    k = kendradi_bala(house)
    d = drekkana_bala(planet, longitude)
    return {
        "uchcha":          u,
        "saptavargaja_d1": s,
        "oja_yugma":       o,
        "kendradi":        k,
        "drekkana":        d,
        "total":           u + s + o + k + d,
    }


# --------------------------------------------------------------------------- #
# Dig-bala (BPHS 27.36) — Phase 2                                             #
# --------------------------------------------------------------------------- #

# Per BPHS 27.36, each of the seven lights has a strongest direction (dig)
# corresponding to a kendra house from Lagna. At its strongest direction the
# planet earns 60 virupa; at the opposite direction, 0; linear in between.
#   Sun, Mars     → 10th house (Madhya / midheaven — energetic, action)
#   Moon, Venus   → 4th house  (Patala / IC — receptive, comfort)
#   Mercury, Jup. → 1st house  (Lagna — wisdom, expression)
#   Saturn        → 7th house  (Descendant — labour, duty)
# Rahu/Ketu have no classical Dig-bala (shadow points).
_DIG_BALA_MAX_HOUSE: dict[str, int] = {
    "Sun":     10,
    "Mars":    10,
    "Moon":     4,
    "Venus":    4,
    "Mercury":  1,
    "Jupiter":  1,
    "Saturn":   7,
}


def dig_bala(planet: str, house: int) -> float:
    """Directional strength per BPHS 27.36 (whole-sign approximation).

    Returns virupa in [0, 60]:
    - 60 virupa at the planet's strongest house (its "dig").
    - 0 virupa at the opposite house (7th from the strongest).
    - Linear in the shortest whole-sign distance between the two.

    Rahu/Ketu return 0 (no classical Dig-bala).
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    if not (1 <= house <= 12):
        raise ValueError(f"house out of range: {house!r}")
    if planet not in _DIG_BALA_MAX_HOUSE:
        return 0.0
    max_h = _DIG_BALA_MAX_HOUSE[planet]
    worst_h = ((max_h - 1 + 6) % 12) + 1
    diff = (house - worst_h) % 12
    shortest = min(diff, 12 - diff)
    return (shortest / 6.0) * 60.0


# --------------------------------------------------------------------------- #
# Paksha-bala (BPHS 27.32-33) — Phase 2 single Kala-bala component            #
# --------------------------------------------------------------------------- #
#
# Paksha-bala = lunar-phase strength. Computed from the angular distance
# between Sun and Moon (0–180° after wrapping):
#   - Benefics (Jupiter, Venus, Moon, Mercury) gain strength in the BRIGHT
#     fortnight (Sun→Moon separation 0°→180°). 60 virupa at full Moon.
#   - Malefics (Sun, Mars, Saturn) and nodes gain in the DARK fortnight.
#     60 virupa at new Moon (conjunction).
#
# BPHS 27.32 doubles the Moon's Paksha-bala (60 → ~120) since it is the
# Moon's own phase. Phase 2 implements the standard one-component version
# and notes the Moon-doubling rule for Phase 2b.
#
# This is one of 8 Kala-bala sub-components per BPHS 27. The others
# (Natonnata / Tribhaga / Abda / Masa / Vara / Hora / Ayana / Yuddha)
# are deferred to Phase 2b. Naming the public function ``paksha_bala``
# rather than ``kala_bala`` so the future full Kala-bala can be a clean
# sum without API churn.

_PAKSHA_BENEFICS: frozenset[str] = frozenset(
    {"Jupiter", "Venus", "Moon", "Mercury"}
)
_PAKSHA_MALEFICS_AND_NODES: frozenset[str] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)


def paksha_bala(
    planet: str, sun_longitude: float, moon_longitude: float
) -> float:
    """Lunar-phase strength per BPHS 27.32-33 (Phase-2 single component).

    Range: 0 to 60 virupa. Benefics peak at full Moon (separation 180°);
    malefics peak at new Moon (separation 0°). The Moon's own paksha-bala
    is NOT doubled here — Phase 2b will add that classical refinement.
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    # Shortest arc between Sun and Moon in [0, 180].
    diff = (moon_longitude - sun_longitude) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    # Linear: 0..180° maps to 0..60 virupa for benefics; reversed for malefics.
    benefic_virupa = diff * 60.0 / 180.0
    if planet in _PAKSHA_BENEFICS:
        return benefic_virupa
    if planet in _PAKSHA_MALEFICS_AND_NODES:
        return 60.0 - benefic_virupa
    return 0.0


# --------------------------------------------------------------------------- #
# Drik-bala (BPHS 27.38) — Phase 2 simplified                                 #
# --------------------------------------------------------------------------- #
#
# Drik-bala = net aspectual strength. Each other planet contributes positive
# virupa if benefic, negative if malefic, weighted by its aspect strength
# onto the target. Classical Parashara divides the net sum by 4 (BPHS 27.38).
#
# Aspect strength factors per BPHS 26 (graha drishti):
#   7th house from aspecter           → 60 virupa (full, universal)
#   Mars: 4th, 8th from aspecter      → 60 (planet-specific upgrade)
#   Jupiter: 5th, 9th                 → 60
#   Saturn: 3rd, 10th                 → 60
#   Rahu, Ketu: 5th, 9th              → 60 (project convention, Jupiter-style
#                                            per the locked decision in
#                                            project_astro_locked_decisions.md)
# Partial aspects (1/4, 1/2, 3/4 views from other houses) are omitted in
# Phase 2 — Phase 2b will add them for a finer-grained signal.
#
# Benefic / malefic classification:
#   Benefic:  Jupiter, Venus, Moon, Mercury (Phase-2 simplification — we
#             ignore the "Mercury becomes malefic when conjunct malefic"
#             rule for now)
#   Malefic:  Sun, Mars, Saturn, Rahu, Ketu

_DRIK_BENEFIC: frozenset[str] = frozenset(
    {"Jupiter", "Venus", "Moon", "Mercury"}
)
_DRIK_MALEFIC: frozenset[str] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)


def _aspect_strength_full(
    aspecter: str, aspecter_sign: int, target_sign: int
) -> float:
    """Return full-aspect virupa (0 or 60) from aspecter to target.

    Phase 2 emits 0 or 60 only (full-aspect rules per BPHS 26 plus the
    project's locked nodal convention). Phase 2b adds the 1/4, 1/2, 3/4
    partial-aspect tiers.
    """
    # Whole-sign distance: ((target - aspecter) mod 12) + 1 → 1..12
    house_distance = ((target_sign - aspecter_sign) % 12) + 1
    if house_distance == 7:
        return 60.0
    if aspecter == "Mars" and house_distance in (4, 8):
        return 60.0
    if aspecter == "Jupiter" and house_distance in (5, 9):
        return 60.0
    if aspecter == "Saturn" and house_distance in (3, 10):
        return 60.0
    if aspecter in {"Rahu", "Ketu"} and house_distance in (5, 9):
        return 60.0
    return 0.0


def drik_bala(planet: str, chart: dict) -> float:
    """Drik-bala in virupa per BPHS 27.38 (Phase-2 simplified).

    Net aspectual strength: (benefic_sum − malefic_sum) / 4. Can be
    negative when malefic aspects dominate. Returns 0 when the target
    planet is missing from the chart.

    Phase-2 simplification: only full aspects (60 virupa) are counted —
    the partial-aspect tiers (1/4, 1/2, 3/4) from the universal-aspect
    rule are deferred to Phase 2b.
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    target_entry = chart.get(planet)
    if not target_entry:
        return 0.0
    target_sign = target_entry.get("sign")
    if not isinstance(target_sign, int) or not (1 <= target_sign <= 12):
        return 0.0

    benefic_sum = 0.0
    malefic_sum = 0.0
    for aspecter, entry in chart.items():
        if aspecter == planet or aspecter not in _KNOWN_PLANETS:
            continue
        aspecter_sign = entry.get("sign")
        if not isinstance(aspecter_sign, int) or not (1 <= aspecter_sign <= 12):
            continue
        strength = _aspect_strength_full(aspecter, aspecter_sign, target_sign)
        if strength == 0.0:
            continue
        if aspecter in _DRIK_BENEFIC:
            benefic_sum += strength
        elif aspecter in _DRIK_MALEFIC:
            malefic_sum += strength

    return (benefic_sum - malefic_sum) / 4.0


# --------------------------------------------------------------------------- #
# Cheshta-bala (BPHS 27.36-37) — Phase 2 partial                              #
# --------------------------------------------------------------------------- #
#
# Classical Cheshta-bala assigns virupa based on the planet's motion type
# (eight categories per BPHS 27): vakra/anuvakra/vikala/manda/mandatara/
# sama/chara/atichara. Full implementation requires the planet's actual
# mean-vs-instantaneous speed comparison — Phase 2b work.
#
# Phase 2 simplification:
#   Retrograde (vakra)  → 60 virupa (the strongest category)
#   Direct motion       → 30 virupa (treated as "average" sama category)
#   Sun, Moon           → 0 virupa  (classically computed via Ayana-bala,
#                                    a Kala-bala sub-component; placeholder)
# Rahu/Ketu are always retrograde geometrically; the Cheshta-bala convention
# does not apply to them — return 0 in Phase 2.

_CHESHTA_RETROGRADE_VIRUPA: float = 60.0
_CHESHTA_DIRECT_VIRUPA: float = 30.0

# Planets that get Cheshta-bala in the classical sense (5 star-planets).
# Sun and Moon get their motional strength from Ayana-bala instead.
_CHESHTA_STAR_PLANETS: frozenset[str] = frozenset(
    {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
)


def cheshta_bala(planet: str, is_retrograde: bool) -> float:
    """Motional strength per BPHS 27.36-37 (Phase-2 simplified).

    - Retrograde star-planet (Mars/Mercury/Jupiter/Venus/Saturn): 60 virupa
    - Direct star-planet: 30 virupa
    - Sun, Moon: 0 (classically derived via Ayana-bala; Phase 2b)
    - Rahu, Ketu: 0 (no classical Cheshta-bala for nodes)

    Phase 2b will replace this with the full 8-category formula using
    actual planetary speed vs the planet's mean speed.
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    if planet not in _CHESHTA_STAR_PLANETS:
        return 0.0
    return _CHESHTA_RETROGRADE_VIRUPA if is_retrograde else _CHESHTA_DIRECT_VIRUPA


# --------------------------------------------------------------------------- #
# Bhava-bala (BPHS 28) — Phase 2 partial: Bhavadhipati only                   #
# --------------------------------------------------------------------------- #
#
# BPHS 28 defines Bhava-bala for each house from three sub-components:
#   1. Bhavadhipati-bala — Shadbala of the house's lord
#   2. Bhava-Dig-bala    — directional via the house's natural significator
#   3. Bhava-Drishti-bala — net aspects on the house cusp
#
# Phase 2 ships only Bhavadhipati (the biggest classical contribution).
# Phase 2b adds the other two sub-components.

def bhavadhipati_bala(house: int, chart: dict, asc_sign: int) -> float:
    """Shadbala of the house's lord (BPHS 28.1).

    Computes the full Shadbala of whichever planet rules the sign that
    falls in the requested house from the given Lagna. The chart entry
    for the lord must carry at least ``sign``; a missing ``longitude``
    falls back to mid-sign (15°), and a missing ``d9_sign`` falls back
    to the D1 sign (overestimates own-sign virupa).

    Returns 0 virupa when the lord planet is missing from the chart.
    """
    if not (1 <= house <= 12):
        raise ValueError(f"house out of range: {house!r}")
    if not (1 <= asc_sign <= 12):
        raise ValueError(f"asc_sign out of range: {asc_sign!r}")

    house_sign = ((asc_sign - 1 + house - 1) % 12) + 1
    lord = SIGN_RULERS[house_sign]

    lord_entry = chart.get(lord)
    if not lord_entry:
        return 0.0

    lord_sign = lord_entry.get("sign")
    if not isinstance(lord_sign, int):
        return 0.0
    lord_longitude = lord_entry.get("longitude")
    if not isinstance(lord_longitude, (int, float)):
        lord_longitude = (lord_sign - 1) * 30.0 + 15.0
    lord_d9 = lord_entry.get("d9_sign", lord_sign)
    lord_house = ((lord_sign - asc_sign) % 12) + 1

    breakdown = shadbala_total(
        lord,
        longitude=float(lord_longitude),
        d1_sign=lord_sign,
        d9_sign=lord_d9,
        house=lord_house,
        chart=chart,
    )
    return breakdown["total"]


def bhava_bala(house: int, chart: dict, asc_sign: int) -> dict[str, float]:
    """Aggregate Bhava-bala for one house (BPHS 28, Phase-2 partial).

    Returns the three sub-components plus total in virupa. Phase 2 fills
    only ``bhavadhipati``; ``bhava_dig`` and ``bhava_drishti`` are
    Phase 2b stubs returning 0.
    """
    bha = bhavadhipati_bala(house, chart, asc_sign)
    return {
        "bhavadhipati":  bha,
        "bhava_dig":     0.0,
        "bhava_drishti": 0.0,
        "total":         bha,
    }


# --------------------------------------------------------------------------- #
# Naisargika-bala (BPHS 27.34) — Phase 2 partial                              #
# --------------------------------------------------------------------------- #

def naisargika_bala(planet: str) -> float:
    """Constant per-planet innate strength in virupa per BPHS 27.34.

    Sun 60 → Saturn 8.571 in 60/7 steps. Lunar nodes return 0 (no
    classical naisargika-bala — they are shadow points).
    """
    if planet not in _KNOWN_PLANETS:
        raise ValueError(f"unknown planet: {planet!r}")
    return _NAISARGIKA_BALA.get(planet, 0.0)


# --------------------------------------------------------------------------- #
# Shadbala total (Phase 2 partial: Naisargika filled; others Phase 2b)        #
# --------------------------------------------------------------------------- #

def shadbala_total(
    planet: str,
    *,
    longitude: float,
    d1_sign: int,
    d9_sign: int,
    house: int,
    chart: dict | None = None,
) -> dict[str, float]:
    """Total Shadbala in virupa.

    Phase 2 partial: Sthana (with compound dignity when chart provided) +
    Naisargika filled. Dig, Kala, Cheshta, Drik return 0 pending Phase 2b.
    """
    sthana_breakdown = sthana_bala(
        planet,
        longitude=longitude,
        d1_sign=d1_sign,
        d9_sign=d9_sign,
        house=house,
        chart=chart,
    )
    dig = dig_bala(planet, house)
    nais = naisargika_bala(planet)
    # Cheshta requires retrograde flag from the chart. If chart provided,
    # extract it; otherwise default to direct motion (0 for Sun/Moon path).
    if chart is not None:
        entry = chart.get(planet, {})
        is_retro = bool(entry.get("is_retrograde", False))
        ches = cheshta_bala(planet, is_retro)
        drik = drik_bala(planet, chart)
        # Paksha is currently the only Kala-bala sub-component (Phase 2);
        # Phase 2b will add the other 7 sub-components.
        sun_lon = (chart.get("Sun", {}).get("longitude") or 0.0)
        moon_lon = (chart.get("Moon", {}).get("longitude") or 0.0)
        kala = paksha_bala(planet, float(sun_lon), float(moon_lon))
    else:
        ches = 0.0
        drik = 0.0
        kala = 0.0
    total = sthana_breakdown["total"] + dig + kala + nais + ches + drik
    return {
        "sthana":     sthana_breakdown["total"],
        "dig":        dig,
        "kala":       kala,
        "cheshta":    ches,
        "naisargika": nais,
        "drik":       drik,
        "total":      total,
    }


__all__ = [
    "uchcha_bala",
    "saptavargaja_bala_d1",
    "oja_yugma_bala",
    "kendradi_bala",
    "drekkana_bala",
    "sthana_bala",
    "dig_bala",
    "cheshta_bala",
    "naisargika_bala",
    "drik_bala",
    "paksha_bala",
    "bhavadhipati_bala",
    "bhava_bala",
    "shadbala_total",
]
