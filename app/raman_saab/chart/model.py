from __future__ import annotations
import dataclasses
from dataclasses import dataclass
from typing import Literal, Mapping, Optional
from app.raman_saab.chart import varga
from app.raman_saab.chart.constants import SIGN_LORDS

@dataclass(frozen=True)
class BirthData:
    name: str; year: int; month: int; day: int
    hour: int; minute: int; tz_offset: float
    latitude: float; longitude: float
    #: Native's sex, where the source states it — Raman's factor 7 makes it a judgment input
    #: ("The age, position, status and SEX of the subject", HTJAH-I:486), and the Beeja/Kshetra
    #: sphutas are sex-assigned across the couple (Beeja for a male chart, Kshetra for a female
    #: one, HTJAH-I:5517-5520; the fertility-gate REVERSAL record explains why this matters).
    #: "M" / "F" / None. None is the honest default: most printed charts do not state it, and
    #: nothing may guess it — a sex-gated technique simply does not run when it is unknown.
    sex: Optional[Literal["M", "F"]] = None

    def __post_init__(self) -> None:
        """Validate at the boundary so a typo (lat 200, month 13) fails loudly with a clear message
        instead of producing a wrong chart or a raw swisseph error downstream."""
        checks = (("month", self.month, 1, 12), ("day", self.day, 1, 31),
                  ("hour", self.hour, 0, 23), ("minute", self.minute, 0, 59),
                  ("latitude", self.latitude, -90.0, 90.0),
                  ("longitude", self.longitude, -180.0, 180.0),
                  ("tz_offset", self.tz_offset, -12.0, 14.0))
        for field, value, lo, hi in checks:
            if not (lo <= value <= hi):
                raise ValueError(f"BirthData.{field} must be in [{lo}, {hi}], got {value!r}")
        if self.sex not in (None, "M", "F"):
            raise ValueError(f'BirthData.sex must be "M", "F" or None, got {self.sex!r}')

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
    # append-only 2026-08-17 (report critique item: per-planet maraka reasons): the qualifying
    # clause(s) that placed this graha at its kept tier, e.g. ("lord of the 2nd",
    # "malefic conjunct the 7th lord Jupiter"). Recorded by primitives/maraka.py at add();
    # empty on units built before the field existed (default keeps old constructors valid).
    reasons: tuple[str, ...] = ()

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
        asc_sign = int((asc_lon % 360.0) // 30) + 1
        planets: dict[str, PlanetPos] = {}
        for name, d in stated.items():
            lon = float(d["lon"]) % 360.0; sign = int(lon // 30) + 1
            nak, pada = varga.nakshatra_pada(lon)
            nav = varga.navamsa_sign(lon)
            planets[name] = PlanetPos(
                name=name, lon=lon, sign=sign,
                rasi_house=((sign - asc_sign) % 12) + 1,
                bhava=int(d["bhava"]), bhava_sandhi=False,
                nakshatra=nak, pada=pada, retrograde=False,
                navamsa_sign=nav, vargottama=(nav == sign),
                dispositor=SIGN_LORDS[sign])
        chart = cls(ayanamsa=ayanamsa, jd_ut=None, asc_sign=asc_sign, asc_lon=asc_lon,
                    bhava_madhyas=(), bhava_sandhis=(), planets=planets)
        # Combustion pass — the same one `chart.adapter` runs for a fresh cast, and it belongs
        # here just as much. `combust_fraction` needs ONLY the Sun's longitude and the planet's,
        # both of which a printed chart supplies; without this pass it stayed silently 0.0 on
        # every book chart, so the engine read every graha as un-combust.
        #
        # That mattered because combustion is a factor Raman applies CATEGORICALLY on exactly
        # these charts. HTJAH-I:3780-3790, Chart No. 59, of the third lord: "in the Rashi he is
        # with an inimical planet Sun and has become combust. This makes him weak in the chart."
        # It is also the citation behind the B1 dominant-factor guard (HTJAH-I:3788) — a rule
        # derived from a printed book chart, which the engine could not apply to printed book
        # charts.
        from app.raman_saab.primitives import combustion as _combustion
        return dataclasses.replace(chart, planets={
            n: dataclasses.replace(p, combust_fraction=_combustion.combust_fraction(n, chart))
            for n, p in planets.items()})
