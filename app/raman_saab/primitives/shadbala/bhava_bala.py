"""Bhava Bala — House Strength (Shashtiamsas).

Reference: B.V. Raman, Graha & Bhava Balas §8.

Three components, all in Shashtiamsas (divide by 60 for Rupas):
  1. Bhavadhipati Bala  — the bhava-lord's total Shadbala (passed in).
  2. Bhavadig Bala      — strength from sign-class NIL house proximity.
  3. Bhava Drig Bala    — aspectual strength on the bhava-madhya.

Usage:
    python -m app.raman_saab.primitives.shadbala.bhava_bala
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.shadbala.drik import dristi_value, _is_malefic

# ---------------------------------------------------------------------------
# Sign-class NIL houses (GBB §8).
# Nara      {Gem, Vir, Lib, Aqu}           → 7; Sag 1st half (deg < 15) → 7
# Jalachara {Can, Pis}                      → 10; Cap 2nd half (deg >= 15) → 10
# Chatushpada {Ari, Tau, Leo}               → 4; Sag 2nd half (deg >= 15) → 4; Cap 1st half (deg < 15) → 4
# Keeta     {Sco}                           → 1
# ---------------------------------------------------------------------------

# Simple (non-split) sign → NIL house class ref (for signs without degree-split).
_SIMPLE_SIGN_REF: Final[dict[int, int]] = {
    1: 4,   # Aries  → Chatushpada
    2: 4,   # Taurus → Chatushpada
    3: 7,   # Gemini → Nara
    4: 10,  # Cancer → Jalachara
    5: 4,   # Leo    → Chatushpada
    6: 7,   # Virgo  → Nara
    7: 7,   # Libra  → Nara
    8: 1,   # Scorpio → Keeta
    # 9  Sagittarius — split by degree
    # 10 Capricorn   — split by degree
    11: 7,  # Aquarius → Nara
    12: 10, # Pisces   → Jalachara
}

# Planets that receive FULL (1×) dristi weight for BhavaDrig (all others → ¼).
_FULL_DRISTI_PLANETS: Final[frozenset[str]] = frozenset({"Jupiter", "Mercury"})


def sign_class_ref(sign: int, deg: float = 0.0) -> int:
    """Return the NIL house (Shashtiamsa reference house) for a bhava-madhya's sign.

    Args:
        sign: Sign number 1–12 (1=Aries, …, 12=Pisces).
        deg:  Degree within the sign (0–29.999…). Only relevant for Sagittarius (9)
              and Capricorn (10), which are split at 15°.

    Returns:
        NIL house integer: 1 (Keeta), 4 (Chatushpada), 7 (Nara), or 10 (Jalachara).
    """
    if sign == 9:  # Sagittarius — split at 15°
        return 7 if deg < 15.0 else 4
    if sign == 10:  # Capricorn — split at 15°
        return 4 if deg < 15.0 else 10
    return _SIMPLE_SIGN_REF[sign]


def bhavadig_bala(bhava: int, sign: int, deg: float = 0.0) -> float:
    """Bhavadig Bala in Shashtiamsas.

    Formula: d = |ref − bhava|; if d > 6 use (12 − d); result = d × 10.

    Args:
        bhava: House number 1–12.
        sign:  Sign number of the bhava-madhya (1=Aries … 12=Pisces).
        deg:   Degree within the sign (for Sag/Cap split signs).

    Returns:
        Bhavadig Bala as a float (Shashtiamsas, range 0–60).
    """
    ref = sign_class_ref(sign, deg)
    d = abs(ref - bhava)
    if d > 6:
        d = 12 - d
    return float(d * 10)


def bhava_drig_bala(bhava_madhya: float, chart: RamanChart) -> float:
    """Bhava Drig Bala — aspectual strength on the bhava-madhya (Shashtiamsas).

    Each aspecting planet contributes:
      - Full (1×) dristi for Jupiter and Mercury.
      - Quarter (¼×) dristi for all other planets.
    The signed pinda is then divided by 4 (matching the graha Drik Bala convention).
    Benefic aspects add, malefic aspects subtract. Rahu/Ketu are excluded.

    Args:
        bhava_madhya: Ecliptic longitude of the bhava-madhya (degrees, tropical/sidereal
                      consistent with chart.planets).
        chart:        RamanChart providing the aspecting planets.

    Returns:
        Signed Bhava Drig Bala in Shashtiamsas.
    """
    pinda = 0.0
    for planet, pos in chart.planets.items():
        if planet in ("Rahu", "Ketu"):
            continue
        # Separation: from the planet to the madhya (K = target - aspector, mod 360)
        K = (bhava_madhya - pos.lon) % 360.0
        base_val = dristi_value(K)
        if base_val == 0.0:
            continue
        # Weight: full for Jupiter/Mercury, quarter for all others
        weight = 1.0 if planet in _FULL_DRISTI_PLANETS else 0.25
        weighted = base_val * weight
        # Sign: benefic adds, malefic subtracts
        pinda += -weighted if _is_malefic(planet, chart) else weighted

    return round(pinda / 4.0, 3)


def bhava_bala(
    bhava: int,
    chart: RamanChart,
    lord_shadbala: float,
    bhava_madhya: float,
    bhava_sign: int,
    bhava_sign_deg: float = 0.0,
) -> float:
    """Total Bhava Bala (Shashtiamsas) = Bhavadhipati + Bhavadig + BhavaDrig.

    Args:
        bhava:          House number 1–12.
        chart:          RamanChart (for aspecting planets in BhavaDrig).
        lord_shadbala:  Total Shadbala of the bhava-lord in Shashtiamsas
                        (Bhavadhipati Bala — passed in from a prior Shadbala computation).
        bhava_madhya:   Ecliptic longitude of this bhava's madhya (degrees).
        bhava_sign:     Sign number (1–12) of the bhava-madhya.
        bhava_sign_deg: Degree within that sign (0–29.999…), for Sag/Cap splits.

    Returns:
        Total Bhava Bala in Shashtiamsas as a float.
    """
    bhavadhipati = lord_shadbala
    bhavadig = bhavadig_bala(bhava, bhava_sign, bhava_sign_deg)
    bhava_drig = bhava_drig_bala(bhava_madhya, chart)
    return round(bhavadhipati + bhavadig + bhava_drig, 3)
