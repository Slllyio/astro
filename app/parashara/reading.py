"""The Parashara reading — everything the engine knows, assembled for one nativity.

The capstone that turns the primitives into an engine: cast a chart, then produce a single cited
BPHS reading combining the four capabilities built so far —

  * the twelve bhava verdicts (Parashara's own ch.11 prosperity/annihilation method),
  * each graha's Vimsopaka strength (ch.7),
  * the applicable conditional dashas (ch.46), and
  * the natural longevity span (Nisargayu, ch.43).

Every element carries the BPHS citation the underlying primitive already holds, so the whole
reading is traceable to Parashara's own slokas.

Honest scope: the dasha timelines are reported FROM THE START of the birth mahadasha
(`elapsed_fraction=0`), not adjusted for the balance-at-birth — that needs Bhayat/Bhabhog (the
Moon's ghatika position), a birth-time-precision step flagged on the output rather than faked. The
Nisargayu span is the pre-reduction natural figure (its own flag). Nothing here is presented as more
settled than it is.

Usage:
    from app.parashara.chart.cast import cast
    from app.parashara.reading import read
    r = read(cast(year=1990, month=7, day=15, hour=12, minute=0,
                   tz_offset=5.5, latitude=12.97, longitude=77.59))
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.parashara.chart.bhava_chart import judge_all_bhavas
from app.parashara.chart.brahma_graha import BrahmaGraha, brahma_graha
from app.parashara.chart.cast import ParasharaChart
from app.parashara.chart.vimsopaka_chart import vimsopaka_all
from app.parashara.primitives.rasi_dasha import RasiDashaPeriod
from app.parashara.primitives.sthira_dasha import sthira_timeline
from app.parashara.judges.bhava_prosperity import BhavaVerdict
from app.parashara.primitives import ashtottari_dasha as ash
from app.parashara.primitives import yogini_dasha as yog
from app.parashara.primitives.baladi_avastha import baladi_from_longitude
from app.parashara.primitives.jagradadi_avastha import jagradadi_avastha
from app.parashara.primitives.longevity import NisargayuSpan, nisargayu_span
from app.parashara.primitives.nakshatra_dasha import DashaPeriod
from app.parashara.primitives.relationships import GRAHAS, SIGN_LORDS
from app.parashara.primitives.shadbala.total import PartialShadbala, partial_shadbala_all
from app.parashara.primitives.vimsopaka import VimsopakaScore


@dataclass(frozen=True)
class DashaReading:
    system: str
    applicable: bool
    reason: str                          # why it applies / does not
    timeline: tuple[DashaPeriod, ...]    # from the start of the birth mahadasha (see module note)


@dataclass(frozen=True)
class GrahaAvastha:
    """A graha's two computable avastha states (ch.45)."""
    baladi: str          # bala | kumara | yuva | vriddha | mrita (age-state by degree)
    baladi_grade: float
    jagradadi: str       # jagrat | swapna | sushupti (awake/dreaming/sleeping by dignity)
    jagradadi_grade: float


@dataclass(frozen=True)
class SthiraReading:
    """Sthira (rasi) dasha, seeded by the Brahma Graha computed from the chart's strengths."""
    brahma_graha: BrahmaGraha
    timeline: tuple[RasiDashaPeriod, ...]


@dataclass(frozen=True)
class ParasharaReading:
    chart: ParasharaChart
    bhavas: Mapping[int, BhavaVerdict]
    vimsopaka: Mapping[str, VimsopakaScore]
    shadbala: Mapping[str, PartialShadbala]   # PARTIAL: Sthana + Dig + Naisargika + Kala:Paksha
    avasthas: Mapping[str, GrahaAvastha]
    dashas: tuple[DashaReading, ...]
    sthira: SthiraReading                # rasi dasha, seeded end-to-end via the Brahma Graha
    nisargayu: NisargayuSpan
    balance_adjusted: bool               # False: timelines are not birth-balance-adjusted


def _rahu_house_from(chart: ParasharaChart) -> tuple[int, int | None]:
    """Rahu's house from the lagna, and from the lagna LORD's sign (for Ashtottari applicability)."""
    def sign_of(lon: float) -> int:
        return int(lon % 360.0 // 30) + 1
    rahu_sign = sign_of(chart.longitudes["Rahu"])
    from_lagna = ((rahu_sign - chart.asc_sign) % 12) + 1
    lord = SIGN_LORDS[chart.asc_sign]
    lord_lon = chart.longitudes.get(lord)
    from_lord = (((rahu_sign - sign_of(lord_lon)) % 12) + 1) if lord_lon is not None else None
    return from_lagna, from_lord


def _dashas(chart: ParasharaChart) -> tuple[DashaReading, ...]:
    nak = chart.janma_nakshatra
    # Yogini is a general system (no adoption condition stated) — always reported.
    yogini = DashaReading(
        system="yogini", applicable=True,
        reason="general system (no special adoption condition)",
        timeline=yog.timeline(nak))
    # Ashtottari is conditional on Rahu's placement.
    from_lagna, from_lord = _rahu_house_from(chart)
    ash_ok = ash.is_applicable(rahu_house_from_lagna=from_lagna,
                               rahu_house_from_lagna_lord=from_lord)
    ashtottari = DashaReading(
        system="ashtottari", applicable=ash_ok,
        reason=("Rahu not in Lagna/Kendra or a trikona from the lagna lord"
                if ash_ok else "Rahu in Lagna/Kendra or a trikona from the lagna lord"),
        timeline=ash.timeline(nak) if ash_ok else ())
    return (yogini, ashtottari)


def _avasthas(chart: ParasharaChart) -> dict[str, GrahaAvastha]:
    """Baladi (age-state by degree) + Jagradadi (awake/dreaming/sleeping by dignity) per graha.
    The seven grahas only — ch.45's avasthas have no nodes."""
    out: dict[str, GrahaAvastha] = {}
    for g in GRAHAS:
        lon = chart.longitudes.get(g)
        if lon is None:
            continue
        b = baladi_from_longitude(lon)
        j = jagradadi_avastha(g, int(lon % 360.0 // 30) + 1)
        out[g] = GrahaAvastha(baladi=b.state, baladi_grade=b.grade,
                              jagradadi=j.state, jagradadi_grade=j.grade)
    return out


def read(chart: ParasharaChart) -> ParasharaReading:
    """Assemble the full Parashara reading for a cast chart."""
    return ParasharaReading(
        chart=chart,
        bhavas=judge_all_bhavas(chart.longitudes, asc_sign=chart.asc_sign,
                                moon_waxing=chart.moon_waxing),
        vimsopaka=vimsopaka_all(chart.longitudes, scheme="shodasavarga"),
        shadbala=partial_shadbala_all(chart.longitudes, asc_sign=chart.asc_sign,
                                      asc_longitude=chart.asc_longitude,
                                      moon_waxing=chart.moon_waxing,
                                      speeds=chart.speeds, ayanamsa=chart.ayanamsa),
        avasthas=_avasthas(chart),
        dashas=_dashas(chart),
        sthira=_sthira(chart),
        nisargayu=nisargayu_span(chart.longitudes),
        balance_adjusted=False,
    )


def _sthira(chart: ParasharaChart) -> SthiraReading:
    bg = brahma_graha(chart)
    return SthiraReading(brahma_graha=bg, timeline=sthira_timeline(bg.sign))
