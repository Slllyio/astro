from __future__ import annotations
"""
Maraka point set — tiered death-inflicting planets, 22nd-drekkana lord, and
64th-navamsa lord — for Raman Saab condition predicates.

Usage:
    python -m app.raman_saab.primitives.maraka   (no CLI; import-only module)

Doctrine: HTJAH-I:776-814 (overview §8.2) + HTJAH-II:3692-3695 (22nd drekkana)
          + HTJAH-II:4544 (64th navamsa from the Moon).

Phase 1c-3 backfill (now that Shadbala exists):
  - MarakaUnit.strength_rank is the graha's rank among the 7 by total Shadbala
    (1 = strongest), read from chart.planets[g].shadbala_rupas.total — guarded to 0
    when Shadbala is absent (Track-B / stated-positions charts).
  - The "weakest planet in the chart" (lowest total Shadbala) is added as a tertiary
    maraka when Shadbala is filled (GBB-8 / overview §8.2).

Deferred to Phase 2 (needs drishti engine):
  - "Associate" currently means conjunct (same rasi-house only).
  - Aspect-based association will be added when doctrine/drishti.py is available.
"""
from typing import Final
from app.raman_saab.chart.model import RamanChart, MarakaUnit, MarakaPoints
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.doctrine import drishti
from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS, NATURAL_BENEFICS

# The 7 visible grahas that can carry Shadbala (nodes never do).
_SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


# ── house-arithmetic helpers ──────────────────────────────────────────────────

def _lord_of(house: int, asc_sign: int) -> str:
    """Sign-lord of rasi-house `house` (1-12) counted from `asc_sign`."""
    return SIGN_LORDS[((asc_sign - 1) + (house - 1)) % 12 + 1]


def _occupants(house: int, chart: RamanChart) -> list[str]:
    """All planet names currently in rasi-house `house`."""
    return [n for n, p in chart.planets.items() if p.rasi_house == house]


# ── 22nd-drekkana lord ────────────────────────────────────────────────────────

def _drekkana22_lord(asc_lon: float) -> str:
    """Lord of the 22nd drekkana reckoned from the LAGNA drekkana (HTJAH-II:3692-3695).

    Offset is +22 in the 36-decanate cycle, PINNED to Raman's printed worked example:
        Lagna 27° Aquarius (3rd decan of Aquarius, index 32)
        -> 22nd drekkana = (32 + 22) % 36 = 18 = 1st decan of Libra
        -> lord Venus.
    (A textbook '8th-house decanate' derivation sometimes yields +21; Raman's
    printed example is the authority and selects +22. Under both offsets the
    lord for the cited example happens to be Venus, so the pin is doubly robust.)
    """
    # Each sign contributes 3 decans; lagna_drekkana_index = sign_index*3 + decan_within_sign.
    sign_idx = int(asc_lon // 30)          # 0-based sign index (0=Aries..11=Pisces)
    decan = int((asc_lon % 30) // 10)      # 0, 1, or 2 within the sign
    g = (sign_idx * 3 + decan + 22) % 36  # 0-based drekkana index in the 36-decan cycle

    # Convert drekkana index back to sign: first decan of sign X -> sign lord of X,
    # second decan -> lord of sign (X+4), third decan -> lord of sign (X+8) (fire/air/water triplicity).
    # Formula: sign (1-based) = ((g//3) + (g%3)*4) % 12 + 1
    sign = ((g // 3) + (g % 3) * 4) % 12 + 1   # 1-based sign (1=Aries..12=Pisces)
    return SIGN_LORDS[sign]


# ── 64th-navamsa lord ─────────────────────────────────────────────────────────

def _navamsa64_lord(chart: RamanChart) -> str:
    """Lord of the 64th Navamsa reckoned from the MOON (HTJAH-II:4544).

    Raman's text: 'the lord of the 64th Navamsa occupied by the Moon'.
    Offset +63: the Moon's own navamsa counts as the 1st, so the 64th is
    63 steps further. Each sign contains 9 navamsas; 108 total in the zodiac.
    Falls back to the Lagna longitude only when the Moon is absent from the
    chart (sparse Track-B charts); normal charts always include the Moon.

    NOTE: no Raman worked example disambiguates +63 vs +64; an external pin
    (Jagannatha Hora / drikpanchang for the canonical Bangalore chart) should
    confirm the offset before this point is used in Phase-4 death-timing.
    """
    ref_lon = chart.planets["Moon"].lon if "Moon" in chart.planets else chart.asc_lon
    # Navamsa index of ref_lon (0-based in 0..107)
    nav_idx = int(ref_lon // (30.0 / 9))   # each navamsa = 3°20' = 30/9 degrees
    g = (nav_idx + 63) % 108               # +63 -> 64th navamsa (1-indexed)
    return SIGN_LORDS[(g % 12) + 1]        # sign lord of the navamsa's sign


# ── Shadbala-driven strength helpers (Phase 1c-3) ─────────────────────────────

def _shadbala_totals(chart: RamanChart) -> dict[str, float]:
    """Total Shadbala (Shashtiamsas) for each of the 7 visible grahas that carry it.

    Returns an empty dict when no planet has Shadbala filled (Track-B charts), so the
    callers fall back to the stubbed strength_rank=0 / no-weakest-tertiary behaviour.
    """
    return {
        g: chart.planets[g].shadbala_rupas.total
        for g in _SEVEN
        if g in chart.planets and chart.planets[g].shadbala_rupas is not None
    }


def _strength_ranks(totals: dict[str, float]) -> dict[str, int]:
    """Rank the grahas by total Shadbala descending (1 = strongest). Empty -> empty."""
    ordered = sorted(totals, key=lambda g: totals[g], reverse=True)
    return {g: i + 1 for i, g in enumerate(ordered)}


def _weakest_planet(totals: dict[str, float]) -> str | None:
    """The graha with the lowest total Shadbala, or None when no Shadbala is present."""
    if not totals:
        return None
    return min(totals, key=lambda g: totals[g])


# ── main public function ──────────────────────────────────────────────────────

def maraka_points(chart: RamanChart) -> MarakaPoints:
    """Tiered maraka set per HTJAH-I:776-814 (overview §8.2).

    Tiers
    -----
    primary  : lords of 2nd & 7th + malefic occupants of 2/7 +
               malefic associates (conjunct) of those lords.
    secondary: benefics conjunct 2/7 lords + lords of 3rd & 8th.
    tertiary : Saturn touching (conjunct) any maraka house-lord +
               lords of 6th & 8th (8th lord is also secondary; earlier
               tier assignment is kept via seen.setdefault).

    Rahu/Ketu are excluded (no lordship; they act per dispositor/conjunction
    in Phase 2).  When the chart carries Shadbala (ephemeris charts), each unit's
    strength_rank is its rank among the 7 by total Shadbala (1 = strongest) and the
    weakest planet (lowest total Shadbala) is added as a tertiary maraka; on Track-B
    charts (no Shadbala) strength_rank stays 0 and no weakest-planet tertiary is added.
    """
    asc = chart.asc_sign
    seen: dict[str, str] = {}   # graha -> first (strongest) tier assigned

    def add(graha: str, tier: str) -> None:
        if graha in ("Rahu", "Ketu"):
            return
        seen.setdefault(graha, tier)

    l2 = _lord_of(2, asc)
    l7 = _lord_of(7, asc)
    l3 = _lord_of(3, asc)
    l8 = _lord_of(8, asc)
    l6 = _lord_of(6, asc)
    death_lords = {l2, l7}

    # Houses occupied by the 2nd and 7th lords (for conjunction detection)
    death_lord_houses: set[int] = {
        chart.planets[l].rasi_house
        for l in death_lords
        if l in chart.planets
    }

    # ── primary ──────────────────────────────────────────────────────────────
    add(l2, "primary")
    add(l7, "primary")
    for h in (2, 7):
        for occ in _occupants(h, chart):
            if occ in NATURAL_MALEFICS:
                add(occ, "primary")
    # malefic associates of the 2nd/7th lords — conjunct OR aspecting (drishti, Phase 2)
    for name, p in chart.planets.items():
        if name not in NATURAL_MALEFICS:
            continue
        conjunct = p.rasi_house in death_lord_houses
        aspects = any(lord in chart.planets and drishti.aspects_planet(name, lord, chart)
                      for lord in death_lords)
        if conjunct or aspects:
            add(name, "primary")

    # ── secondary ────────────────────────────────────────────────────────────
    # benefics conjunct the 2nd/7th lords
    for name, p in chart.planets.items():
        if name in NATURAL_BENEFICS and p.rasi_house in death_lord_houses:
            add(name, "secondary")
    add(l3, "secondary")
    add(l8, "secondary")

    # ── tertiary ─────────────────────────────────────────────────────────────
    if "Saturn" in chart.planets and chart.planets["Saturn"].rasi_house in death_lord_houses:
        add("Saturn", "tertiary")
    add(l6, "tertiary")
    add(l8, "tertiary")  # 8th lord gets secondary above; this is a no-op via setdefault

    # Weakest planet in the chart (lowest total Shadbala) — only when Shadbala filled.
    totals = _shadbala_totals(chart)
    weakest = _weakest_planet(totals)
    if weakest is not None:
        add(weakest, "tertiary")

    # Rank by total Shadbala (1 = strongest); 0 when the chart carries no Shadbala.
    ranks = _strength_ranks(totals)

    units = tuple(
        MarakaUnit(graha=g, tier=t, strength_rank=ranks.get(g, 0))
        for g, t in seen.items()
    )
    return MarakaPoints(
        units=units,
        drekkana22_lord=_drekkana22_lord(chart.asc_lon),
        navamsa64_lord=_navamsa64_lord(chart),
    )
