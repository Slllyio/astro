"""The Parashara reading — everything the engine knows, assembled for one nativity.

The capstone that turns the primitives into an engine: cast a chart, then produce a single cited
BPHS reading combining the capabilities built so far —

  * the twelve bhava verdicts (Parashara's own ch.11 prosperity/annihilation method),
  * each graha's Vimsopaka strength (ch.7) and complete six-fold Shadbala (ch.27),
  * each house-lord's placement and its ch.24 effect,
  * the planetary avasthas (ch.45),
  * the applicable conditional dashas (ch.46) and the Sthira rasi dasha, and
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
from app.parashara.doctrine.bhava_lord_effects import BhavaLordEffect, effect_of
from app.parashara.doctrine.chandra_yogas import ChandraYoga, detect as detect_chandra_yogas
from app.parashara.doctrine.mahapurusha import MahapurushaYoga, detect as detect_mahapurusha
from app.parashara.doctrine.nabhasa import NabhasaYoga, asraya_yoga, sankhya_yoga
from app.parashara.doctrine.special_yogas import SpecialYoga, detect as detect_special_yogas
from app.parashara.doctrine.vargottama import vargottama_bodies
from app.parashara.primitives import ashtakavarga as _av
from app.parashara.primitives.rasi_dasha import RasiDashaPeriod
from app.parashara.primitives.sthira_dasha import sthira_timeline
from app.parashara.judges.bhava_prosperity import BhavaVerdict
from app.parashara.primitives import ashtottari_dasha as ash
from app.parashara.primitives import vimshottari_dasha as vim
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
class BhavaLordPlacement:
    """Where a house's lord sits, and Parashara's ch.24 effect for that placement."""
    house: int                           # 1..12 — the bhava whose lord this is
    lord: str                            # the graha lording that bhava's sign
    in_house: int                        # 1..12 — the house the lord occupies
    effect: BhavaLordEffect | None       # ch.24 sloka (None only if OCR left the pair unrecoverable)


@dataclass(frozen=True)
class ParasharaReading:
    chart: ParasharaChart
    bhavas: Mapping[int, BhavaVerdict]
    vimsopaka: Mapping[str, VimsopakaScore]
    shadbala: Mapping[str, PartialShadbala]   # the complete six-fold Shadbala (Sthana..Kala)
    avasthas: Mapping[str, GrahaAvastha]
    bhava_lord_effects: Mapping[int, BhavaLordPlacement]  # ch.24 — each house's lord's placement
    nabhasa: tuple[NabhasaYoga, ...]     # ch.35 — detected Asraya/Sankhya distribution yogas
    chandra_yogas: tuple[ChandraYoga, ...]  # ch.37 — lunar yogas (Sunapha..Kemadruma, Adhi)
    mahapurusha: tuple[MahapurushaYoga, ...]  # Pancha Mahapurusha (Saravali ch.37, allied)
    special_yogas: tuple[SpecialYoga, ...]    # ch.36 "many other yogas" — Gaja-Kesari (strict)
    vargottama: tuple[str, ...]          # bodies in the same sign in D1 and D9 (Saravali ch.3)
    sav: Mapping[int, int]               # Sarvashtakavarga bindus per sign 1..12 (ch.66; total 337)
    bav: Mapping[str, Mapping[int, int]]  # each graha's Bhinnashtakavarga per sign (ch.66)
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
    # Vimshottari is the primary system — "the most appropriate and the best of all Dasas"
    # (BPHS-46 sl.12-14) — general, always reported first.
    vimshottari = DashaReading(
        system="vimshottari", applicable=True,
        reason="the primary 120-year system (BPHS-46 sl.12-14)",
        timeline=vim.timeline(nak))
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
    return (vimshottari, yogini, ashtottari)


def _graha_signs(chart: ParasharaChart) -> dict[str, int]:
    """The seven grahas' signs (1..12) — the input Ashtakavarga's references need."""
    return {g: int(chart.longitudes[g] % 360.0 // 30) + 1
            for g in _av.PLANETS if g in chart.longitudes}


def _bhava_lord_effects(chart: ParasharaChart) -> dict[int, BhavaLordPlacement]:
    """For each of the twelve houses: its lord, where the lord sits, and Parashara's ch.24 effect."""
    def sign_of(lon: float) -> int:
        return int(lon % 360.0 // 30) + 1
    out: dict[int, BhavaLordPlacement] = {}
    for house in range(1, 13):
        house_sign = ((chart.asc_sign - 1 + house - 1) % 12) + 1
        lord = SIGN_LORDS[house_sign]
        lord_lon = chart.longitudes.get(lord)
        if lord_lon is None:
            continue
        in_house = ((sign_of(lord_lon) - chart.asc_sign) % 12) + 1
        out[house] = BhavaLordPlacement(house=house, lord=lord, in_house=in_house,
                                        effect=effect_of(house, in_house))
    return out


def _nabhasa(chart: ParasharaChart) -> tuple[NabhasaYoga, ...]:
    """Detected Nabhasa distribution yogas (ch.35): the Asraya yoga if all seven share a modality,
    and the Sankhya yoga for how many signs they occupy (its operability flagged, per Parashara)."""
    signs = {g: int(chart.longitudes[g] % 360.0 // 30) + 1
             for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
             if g in chart.longitudes}
    found = [y for y in (asraya_yoga(signs), sankhya_yoga(signs)) if y is not None]
    return tuple(found)


def _chandra_yogas(chart: ParasharaChart) -> tuple[ChandraYoga, ...]:
    """Lunar yogas reckoned from the Moon (ch.37)."""
    signs = {g: int(lon % 360.0 // 30) + 1 for g, lon in chart.longitudes.items()}
    moon_sign = signs.get("Moon")
    if moon_sign is None:
        return ()
    return detect_chandra_yogas(signs, moon_sign=moon_sign, asc_sign=chart.asc_sign)


def _mahapurusha(chart: ParasharaChart) -> tuple[MahapurushaYoga, ...]:
    """Pancha Mahapurusha yogas (Saravali ch.37): a non-luminary in own/exaltation, in a kendra."""
    signs = {g: int(lon % 360.0 // 30) + 1 for g, lon in chart.longitudes.items()}
    return detect_mahapurusha(signs, asc_sign=chart.asc_sign)


def _special_yogas(chart: ParasharaChart) -> tuple[SpecialYoga, ...]:
    """Ch.36 special yogas (Gaja-Kesari), which need longitudes (combustion) and Jupiter's motion."""
    return detect_special_yogas(chart.longitudes, asc_sign=chart.asc_sign,
                                moon_waxing=chart.moon_waxing,
                                jupiter_retrograde=chart.speeds.get("Jupiter", 0.0) < 0.0)


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
                                      speeds=chart.speeds, ayanamsa=chart.ayanamsa,
                                      kala_ctx=chart.kala),
        avasthas=_avasthas(chart),
        bhava_lord_effects=_bhava_lord_effects(chart),
        nabhasa=_nabhasa(chart),
        chandra_yogas=_chandra_yogas(chart),
        mahapurusha=_mahapurusha(chart),
        special_yogas=_special_yogas(chart),
        vargottama=vargottama_bodies(chart.longitudes, asc_longitude=chart.asc_longitude),
        sav=_av.sarvashtakavarga(_graha_signs(chart), asc_sign=chart.asc_sign),
        bav={g: _av.bhinnashtakavarga(g, _graha_signs(chart), asc_sign=chart.asc_sign)
             for g in _av.PLANETS},
        dashas=_dashas(chart),
        sthira=_sthira(chart),
        nisargayu=nisargayu_span(chart.longitudes),
        balance_adjusted=False,
    )


def _sthira(chart: ParasharaChart) -> SthiraReading:
    bg = brahma_graha(chart)
    return SthiraReading(brahma_graha=bg, timeline=sthira_timeline(bg.sign))
