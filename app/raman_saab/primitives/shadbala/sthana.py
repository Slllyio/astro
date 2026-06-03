"""Sthana Bala — positional strength component of Shadbala (5 sub-components).

Usage:
    from app.raman_saab.primitives.shadbala import sthana
    sh = sthana.sthana_bala("Sun", chart)   # -> Shashtiamsas (float)

Reference: B.V. Raman, *Graha & Bhava Balas* (GBB-3), §1.
All helpers return **Shashtiamsas** (1 Rupa = 60 Shashtiamsas). Nodes get 0.

Sub-components (GBB-3:699):
  Ochcha       — corrected arc from the deep-debilitation point / 3.
  Saptavargaja — Σ over the 7 vargas (D1,D2,D3,D7,D9,D12,D30) of the dignity
                 value of the planet vs. each varga lord. The 45-Sh Moolatrikona
                 tier applies ONLY in D1 (GBB-3:469-476).
  Ojayugma     — +15 for matching rasi parity, +15 for matching navamsa parity.
  Kendra       — 60/30/15 by **rasi-house** (by SIGN, not Bhava — GBB-3:609).
  Drekkana     — 15 if the planet sits in its sex-decanate (GBB-3:653-671).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import relationships as r
from app.raman_saab.primitives.dignity import _compound_relation

from app.raman_saab.primitives import varga_lords as vl

_SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Saptavargaja dignity ladder (Shashtiamsas), GBB-3:462-476. 45 ONLY in D1.
_DIGNITY_SH: Final[dict[str, float]] = {
    "moolatrikona": 45.0, "own": 30.0, "great_friend": 22.5, "friend": 15.0,
    "neutral": 7.5, "enemy": 3.75, "great_enemy": 1.875}

# Drekkana-bala sex -> required decanate index (0,1,2), GBB-3:653-671.
# Masculine {Sun, Jupiter, Mars} -> 1st (0); Hermaphrodite {Saturn, Mercury} -> 2nd (1);
# Feminine {Moon, Venus} -> 3rd (2).
_SEX_DECAN: Final[dict[str, int]] = {
    "Sun": 0, "Jupiter": 0, "Mars": 0, "Saturn": 1, "Mercury": 1, "Moon": 2, "Venus": 2}

# Ojayugma preference: ODD for Sun/Mars/Jupiter/Mercury/Saturn; EVEN for Moon/Venus.
_ODD_PREF: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Jupiter", "Mercury", "Saturn"})


def ochcha_bala(planet: str, chart: RamanChart) -> float:
    """Exaltation strength = corrected arc from the deep-debilitation point / 3.

    0 at deep debilitation, 60 at deep exaltation (GBB-3:43-115).
    """
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    debil_sign, debil_deg = r.DEBILITATION[planet]            # (sign 1..12, deg)
    debil_lon = (debil_sign - 1) * 30 + debil_deg             # deep-debilitation longitude
    diff = (chart.planets[planet].lon - debil_lon) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return round(diff / 3.0, 3)


def _d3(lon: float) -> str:
    """D3 (drekkana) lord — mirrors dispositor.drekkana_lord_of (no varga.drekkana_sign exists)."""
    sign_idx = int(lon // 30)
    drek = int((lon % 30) // 10)                              # 0, 1, 2
    return SIGN_LORDS[((sign_idx + drek * 4) % 12) + 1]       # classical +0/+4/+8 signs


def _varga_lord(planet: str, lon: float, varga_name: str) -> str:
    """Lord of the divisional sign holding `lon` in the named varga."""
    if varga_name == "D1":
        return SIGN_LORDS[int(lon // 30) + 1]
    if varga_name == "D2":
        return vl.hora_lord_of(lon)
    if varga_name == "D3":
        # varga.py exposes no drekkana_sign helper (Phase 0); use the local fallback.
        return SIGN_LORDS[varga.drekkana_sign(lon)] if hasattr(varga, "drekkana_sign") else _d3(lon)
    if varga_name == "D7":
        return vl.saptamsa_lord_of(lon)
    if varga_name == "D9":
        return SIGN_LORDS[varga.navamsa_sign(lon)]
    if varga_name == "D12":
        return vl.dwadasamsa_lord_of(lon)
    if varga_name == "D30":
        return vl.thrimsamsa_lord_of(lon)
    raise ValueError(varga_name)


def _ladder_key(compound: str, naisargika: str) -> str:
    """Map the project's 3-state compound relation onto GBB's 7-rung ladder.

    Great friend if compound==friend AND naisargika==friend; great enemy if both enemy;
    otherwise the ordinary friend/enemy/neutral rung. Verified lossless in plan review.
    """
    if compound == "friend":
        return "great_friend" if naisargika == "friend" else "friend"
    if compound == "enemy":
        return "great_enemy" if naisargika == "enemy" else "enemy"
    return "neutral"


def saptavargaja_bala(planet: str, chart: RamanChart) -> float:
    """Σ over D1,D2,D3,D7,D9,D12,D30 of the dignity value vs. each varga lord (GBB-3:447-543)."""
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    lon = chart.planets[planet].lon
    total = 0.0
    for vname in ("D1", "D2", "D3", "D7", "D9", "D12", "D30"):
        lord = _varga_lord(planet, lon, vname)
        if lord == planet:
            # Own varga. The 45-Sh Moolatrikona tier applies ONLY in the Rasi (D1).
            if vname == "D1":
                s, d = int(lon // 30) + 1, lon % 30.0
                mt_s, lo, hi = r.MOOLATRIKONA[planet]
                total += _DIGNITY_SH["moolatrikona"] if (s == mt_s and lo <= d < hi) else _DIGNITY_SH["own"]
            else:
                total += _DIGNITY_SH["own"]
            continue
        rel = _compound_relation(planet, lord, chart)          # friend|enemy|neutral (Phase 1a)
        nat = r.naisargika(planet, lord)
        total += _DIGNITY_SH[_ladder_key(rel, nat)]
    return round(total, 3)


def ojayugma_bala(planet: str, chart: RamanChart) -> float:
    """+15 for matching rasi parity, +15 for matching navamsa parity (GBB-3:546-601)."""
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    p = chart.planets[planet]
    prefers_odd = planet in _ODD_PREF
    rasi_odd = p.sign % 2 == 1
    nav_odd = p.navamsa_sign % 2 == 1
    val = 0.0
    if rasi_odd == prefers_odd:
        val += 15.0
    if nav_odd == prefers_odd:
        val += 15.0
    return val


def kendra_bala(planet: str, chart: RamanChart) -> float:
    """60 in a Kendra, 30 in a Panapara, 15 in an Apoklima — by SIGN (rasi), GBB-3:609."""
    if planet not in _SEVEN or planet not in chart.planets:
        return 0.0
    h = chart.planets[planet].rasi_house
    if h in (1, 4, 7, 10):
        return 60.0
    if h in (2, 5, 8, 11):
        return 30.0
    return 15.0


def drekkana_bala(planet: str, chart: RamanChart) -> float:
    """15 if the planet sits in its sex-decanate, else 0 (GBB-3:653-671)."""
    if planet not in _SEX_DECAN or planet not in chart.planets:
        return 0.0
    decan = int((chart.planets[planet].lon % 30) // 10)       # 0, 1, 2
    return 15.0 if decan == _SEX_DECAN[planet] else 0.0


def sthana_bala(planet: str, chart: RamanChart) -> float:
    """Total Sthana Bala = Σ of the 5 sub-components (Shashtiamsas, GBB-3:699)."""
    return round(
        ochcha_bala(planet, chart)
        + saptavargaja_bala(planet, chart)
        + ojayugma_bala(planet, chart)
        + kendra_bala(planet, chart)
        + drekkana_bala(planet, chart),
        3,
    )
