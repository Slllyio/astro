from __future__ import annotations
import logging
import swisseph as swe
from app.raman_saab.chart import cusps, varga
from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.constants import SWE_PLANETS, SIGN_LORDS
from app.raman_saab.chart.model import BirthData, PlanetPos, RamanChart

logger = logging.getLogger(__name__)
swe.set_ephe_path(None)  # built-in Moshier ephemeris (mirrors app/core)
_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

def _jd_ut(b: BirthData) -> float:
    utc_hour = (b.hour + b.minute / 60.0) - b.tz_offset
    return swe.julday(b.year, b.month, b.day, utc_hour, swe.GREG_CAL)

def cast_chart(birth: BirthData, *, ayanamsa: str = "raman") -> RamanChart:
    """Birth data -> RamanChart. ONLY place that touches swisseph; ayanamsa isolated."""
    jd = _jd_ut(birth)
    with sidereal_mode(ayanamsa):
        # 1. Lagna + Porphyry cusps (reinterpreted as Vedic bhava-madhyas).
        cusp_arr, ascmc = swe.houses_ex(jd, birth.latitude, birth.longitude, b"O", swe.FLG_SIDEREAL)
        madhyas = tuple(float(x) for x in cusp_arr[:12])       # house 1..12 madhyas
        sandhis = cusps.sandhis_from_madhyas(madhyas)
        asc_lon = float(ascmc[0]); asc_sign = int(asc_lon // 30) + 1

        # 2. Planets.
        raw: dict[str, tuple[float, bool]] = {}
        for name, pid in SWE_PLANETS.items():
            res, _ = swe.calc_ut(jd, pid, _FLAGS)
            raw[name] = (float(res[0]) % 360.0, res[3] < 0)     # lon, retrograde
        node, _ = swe.calc_ut(jd, swe.MEAN_NODE, _FLAGS)        # Raman used the MEAN node
        raw["Rahu"] = (float(node[0]) % 360.0, True)
        raw["Ketu"] = ((float(node[0]) + 180.0) % 360.0, True)

    planets: dict[str, PlanetPos] = {}
    for name, (lon, retro) in raw.items():
        sign = int(lon // 30) + 1
        nak, pada = varga.nakshatra_pada(lon)
        nav = varga.navamsa_sign(lon)
        planets[name] = PlanetPos(
            name=name, lon=lon, sign=sign,
            rasi_house=((sign - asc_sign) % 12) + 1,
            bhava=cusps.bhava_of(lon, sandhis),
            bhava_sandhi=cusps.is_on_sandhi(lon, sandhis),
            nakshatra=nak, pada=pada, retrograde=retro,
            navamsa_sign=nav, vargottama=(nav == sign),
            dispositor=SIGN_LORDS[sign])
    return RamanChart(ayanamsa=ayanamsa, jd_ut=jd, asc_sign=asc_sign, asc_lon=asc_lon,
                      bhava_madhyas=madhyas, bhava_sandhis=sandhis, planets=planets, birth=birth)
