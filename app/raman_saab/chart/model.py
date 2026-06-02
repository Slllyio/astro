from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Mapping, Optional
from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS

@dataclass(frozen=True)
class BirthData:
    name: str; year: int; month: int; day: int
    hour: int; minute: int; tz_offset: float
    latitude: float; longitude: float

@dataclass(frozen=True)
class ShadbalaBreakdown:
    sthana: float; dig: float; kala: float
    cheshta: float; naisargika: float; drik: float; total: float

@dataclass(frozen=True)
class SpecialPoint:
    name: str; lon: float; sign: int; bhava: int; navamsa_sign: int

@dataclass(frozen=True)
class MarakaUnit:
    graha: str; tier: Literal["primary","secondary","tertiary"]; strength_rank: int

@dataclass(frozen=True)
class MarakaPoints:
    units: tuple[MarakaUnit, ...]; drekkana22_lord: str; navamsa64_lord: str

@dataclass(frozen=True)
class BalarishtaState:
    applies: bool; cancelled: bool; reasons: tuple[str, ...]

@dataclass(frozen=True)
class PlanetPos:
    name: str
    lon: float
    sign: int
    rasi_house: int
    bhava: int
    bhava_sandhi: bool
    nakshatra: int
    pada: int
    retrograde: bool
    navamsa_sign: int
    vargottama: bool
    dispositor: str
    combust_fraction: float = 0.0
    shadbala_rupas: Optional[ShadbalaBreakdown] = None   # Phase 1
    ishta: Optional[float] = None                         # Phase 1
    kashta: Optional[float] = None                        # Phase 1

@dataclass(frozen=True)
class RamanChart:
    ayanamsa: str
    jd_ut: Optional[float]            # None for from_stated_positions (no ephemeris)
    asc_sign: int
    asc_lon: float
    bhava_madhyas: tuple[float, ...]
    bhava_sandhis: tuple[float, ...]
    planets: Mapping[str, PlanetPos]
    birth: Optional[BirthData] = None
    upagrahas: Optional[Mapping[str, SpecialPoint]] = None  # Phase 1
    arudha_lagna: Optional[SpecialPoint] = None           # Phase 1
    karakamsa: Optional[SpecialPoint] = None              # Phase 1
    maraka_points: Optional[MarakaPoints] = None          # Phase 1
    balarishta: Optional[BalarishtaState] = None          # Phase 1

    @classmethod
    def from_stated_positions(cls, stated: Mapping[str, Mapping[str, float]], *,
                              asc_lon: float, ayanamsa: str) -> "RamanChart":
        """Build a chart from a book's printed positions (Track-B / Tier-3 tests).
        `stated[planet] = {"lon": float, "bhava": int}`. Bhava is taken as given;
        rasi_house / navamsa / nakshatra / dispositor are derived from lon."""
        asc_sign = int(asc_lon // 30) + 1
        planets: dict[str, PlanetPos] = {}
        for name, d in stated.items():
            lon = float(d["lon"]); sign = int(lon // 30) + 1
            nak, pada = varga.nakshatra_pada(lon)
            nav = varga.navamsa_sign(lon)
            planets[name] = PlanetPos(
                name=name, lon=lon, sign=sign,
                rasi_house=((sign - asc_sign) % 12) + 1,
                bhava=int(d["bhava"]), bhava_sandhi=False,
                nakshatra=nak, pada=pada, retrograde=False,
                navamsa_sign=nav, vargottama=(nav == sign),
                dispositor=SIGN_LORDS[sign])
        return cls(ayanamsa=ayanamsa, jd_ut=None, asc_sign=asc_sign, asc_lon=asc_lon,
                   bhava_madhyas=(), bhava_sandhis=(), planets=planets)
