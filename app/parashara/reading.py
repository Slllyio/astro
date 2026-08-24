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

Honest scope: the dasha timelines ARE birth-balance-adjusted — the birth mahadasha shows its
remaining span from the Moon's arc through its nakshatra (BPHS-46:21-22, arc-proportional
Bhayat/Bhabhog); the strict time-based ghatika variant is a later refinement. The
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
from app.parashara.doctrine.argala import Argala, argala_for
from app.parashara.doctrine.bhava_lord_effects import BhavaLordEffect, effect_of
from app.parashara.doctrine import functional_by_lagna as fbl
from app.parashara.doctrine.gulika import GulikaEffect, effect_in_house as gulika_effect_in_house
from app.parashara.doctrine.maraka import Maraka, maraka_planets
from app.parashara.doctrine.saravali_grids import planet_in_house
from app.parashara.doctrine.saravali_dignity import active_concentrations
from app.parashara.doctrine.chara_karaka import chara_karakas, karakamsa, ROLE_NAMES
from app.parashara.primitives.upagrahas import upagrahas as _upagrahas
from app.parashara.doctrine.upagraha_effects import house_effect as _upagraha_house_effect
from app.parashara.chart.shodasavarga import shodasavarga_all as _shodasavarga_all
from app.parashara.doctrine.drekkana import Drekkana, drekkana_all as _drekkana_all
from app.parashara.chart.sudarshana import SudarshanaPosition, sudarshana_positions as _sudarshana
from app.parashara.doctrine.arudha import (
    bhava_arudhas as _bhava_arudhas,
    pada_finance as _pada_finance,
    spouse_from_upapada as _spouse_from_upapada,
    PadaFinance,
    SpouseFromUpapada,
    PADA_NAMES,
)
from app.parashara.doctrine.saravali_conjunctions import (
    active_conjunctions,
    active_triple_conjunctions,
)
from app.parashara.doctrine.corpus_index import Sloka
from app.parashara.doctrine.chandra_yogas import ChandraYoga, detect as detect_chandra_yogas
from app.parashara.doctrine.mahapurusha import MahapurushaYoga, detect as detect_mahapurusha
from app.parashara.doctrine.nabhasa import NabhasaYoga, asraya_yoga, sankhya_yoga
from app.parashara.doctrine.solar_yogas import SolarYoga, detect as detect_solar_yogas
from app.parashara.doctrine.special_yogas import SpecialYoga, detect as detect_special_yogas
from app.parashara.doctrine.dhana_yogas import DhanaYoga, detect as detect_dhana_yogas
from app.parashara.doctrine.daridra_yogas import DaridraYoga, detect as detect_daridra_yogas
from app.parashara.doctrine.vargottama import vargottama_bodies
from app.parashara.primitives import ashtakavarga as _av
from app.parashara.primitives.rasi_dasha import RasiDashaPeriod
from app.parashara.primitives.sthira_dasha import sthira_timeline
from app.parashara.judges.bhava_prosperity import BhavaVerdict
from app.parashara.judges.richer_bhava import RicherBhavaVerdict, richer_all_bhavas
from app.parashara.primitives import ashtottari_dasha as ash
from app.parashara.primitives import conditional_dasha_systems as cds
from app.parashara.primitives import vimshottari_dasha as vim
from app.parashara.primitives import yogini_dasha as yog
from app.parashara.primitives.baladi_avastha import baladi_from_longitude
from app.parashara.primitives.deeptadi_avastha import deeptadi
from app.parashara.primitives.jagradadi_avastha import jagradadi_avastha
from app.parashara.primitives.lajjitadi_avastha import (
    AVASTHAS as _LAJJITADI_ORDER,
    destroys_its_house,
    lajjitadi,
)
from app.parashara.primitives.longevity import (
    HaranaReducedSpan,
    NisargayuFull,
    NisargayuSpan,
    nisargayu_full,
    nisargayu_span,
)
from app.parashara.primitives.nakshatra_dasha import DashaPeriod, bhukti_timeline
from app.parashara.primitives.relationships import GRAHAS, SIGN_LORDS
from app.parashara.primitives.shadbala.total import PartialShadbala, partial_shadbala_all
from app.parashara.primitives.vimsopaka import VimsopakaScore


@dataclass(frozen=True)
class DashaReading:
    system: str
    applicable: bool
    reason: str                          # why it applies / does not
    timeline: tuple[DashaPeriod, ...]    # from the start of the birth mahadasha (see module note)
    #: per-mahadasha antardashas (bhuktis): (mahadasha_lord, (bhukti periods...)). Populated for the
    #: primary Vimshottari system; empty for the others.
    bhuktis: tuple[tuple[str, tuple[DashaPeriod, ...]], ...] = ()


@dataclass(frozen=True)
class GrahaAvastha:
    """A graha's computable avastha states (ch.45): Baladi, Jagradadi and Deeptadi."""
    baladi: str          # bala | kumara | yuva | vriddha | mrita (age-state by degree)
    baladi_grade: float
    jagradadi: str       # jagrat | swapna | sushupti (awake/dreaming/sleeping by dignity)
    jagradadi_grade: float
    deeptadi: str        # Deepta | Swastha | Pramudita | Santa | Deena | Khala (dignity/placement)
    deeptadi_vikala: bool  # also shares its sign with a malefic
    deeptadi_kopa: bool    # also combust
    lajjitadi: tuple[str, ...]  # any of Lajjita/Garvita/Kshudita/Trushita/Mudita/Kshobhita (ch.45)
    lajjitadi_destroys_house: bool  # holds Kshudita or Kshobhita -> its house is destroyed


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
    richer_bhavas: Mapping[int, RicherBhavaVerdict]   # ch.11 + strength (Vimsopaka/SAV/dignity) + yoga
    vimsopaka: Mapping[str, VimsopakaScore]
    shadbala: Mapping[str, PartialShadbala]   # the complete six-fold Shadbala (Sthana..Kala)
    avasthas: Mapping[str, GrahaAvastha]
    bhava_lord_effects: Mapping[int, BhavaLordPlacement]  # ch.24 — each house's lord's placement
    argala: Mapping[int, tuple[Argala, ...]]  # ch.31 — the argalas acting on each house
    functional_class: Mapping[str, str]  # ch.34 — each graha's functional nature for this lagna
    yogakarakas: tuple[str, ...]         # ch.34 — grahas owning both a kendra and a trikona
    marakas: tuple[str, ...]             # ch.34 — grahas lording a maraka (2nd/7th) house
    maraka_planets: tuple[Maraka, ...]   # ch.44 — the fuller maraka set (lords + malefics in/with)
    planet_house_effects: Mapping[str, tuple[int, Sloka]]  # Saravali ch.30 — graha in its house
    dignity_concentrations: Mapping[str, tuple[int, Sloka]]  # Saravali ch.45 — N grahas share a dignity
    chara_karakas: Mapping[str, str]     # BPHS ch.32 — the 7 movable karakas (role -> planet)
    karakamsa_sign: int                  # BPHS ch.33 — navamsa sign of the Atmakaraka
    conjunctions: tuple[tuple[frozenset, Sloka], ...]  # Saravali ch.15 — active two-graha yogas
    triple_conjunctions: tuple[tuple[frozenset, Sloka], ...]  # Saravali ch.16 — active three-graha yogas
    upagrahas: Mapping[str, float]       # BPHS ch.3 — the five Sun-derived sub-planet longitudes
    upagraha_house_effects: Mapping[str, tuple[int, Sloka]]  # BPHS ch.25 — each upagraha in its house
    shodasavarga: Mapping[str, Mapping[str, int]]  # BPHS ch.6-7 — each body's 16 divisional signs
    drekkanas: Mapping[str, Drekkana]    # BPHS ch.6 — each body's decanate (index, sign, lord, deity)
    sudarshana: Mapping[str, SudarshanaPosition]   # BPHS ch.74 — each body's house from Lagna/Moon/Sun
    arudhas: Mapping[int, int]           # BPHS ch.29-30 — each house's Arudha pada sign (1=Arudha Lagna)
    pada_finance: PadaFinance            # BPHS ch.29 sl.8-15 — wealth from the 11th-from-Arudha-Lagna
    spouse_from_upapada: SpouseFromUpapada  # BPHS ch.30 sl.7-12 — marriage from the 2nd-from-Upapada
    gulika_sign: int                     # Gulika/Mandi's sign (1..12), BPHS ch.3
    gulika_house: int                    # Gulika's house from the lagna (1..12)
    gulika_effect: GulikaEffect | None   # ch.25 — Gulika's effect in that house
    nabhasa: tuple[NabhasaYoga, ...]     # ch.35 — detected Asraya/Sankhya distribution yogas
    chandra_yogas: tuple[ChandraYoga, ...]  # ch.37 — lunar yogas (Sunapha..Kemadruma, Adhi)
    solar_yogas: tuple[SolarYoga, ...]   # ch.38 — Vesi/Vasi/Ubhayachari (from the Sun)
    mahapurusha: tuple[MahapurushaYoga, ...]  # Pancha Mahapurusha (Saravali ch.37, allied)
    special_yogas: tuple[SpecialYoga, ...]    # ch.36 "many other yogas" — Gaja-Kesari (strict)
    dhana_yogas: tuple[DhanaYoga, ...]        # ch.41 — crisp wealth combinations
    daridra_yogas: tuple[DaridraYoga, ...]    # ch.42 — crisp penury combinations
    vargottama: tuple[str, ...]          # bodies in the same sign in D1 and D9 (Saravali ch.3)
    sav: Mapping[int, int]               # Sarvashtakavarga bindus per sign 1..12 (ch.66; total 337)
    bav: Mapping[str, Mapping[int, int]]  # each graha's Bhinnashtakavarga per sign (ch.66)
    dashas: tuple[DashaReading, ...]
    sthira: SthiraReading                # rasi dasha, seeded end-to-end via the Brahma Graha
    nisargayu: NisargayuSpan
    nisargayu_haranas: HaranaReducedSpan
    nisargayu_full: NisargayuFull       # BPHS ch.43 — planetary (post-harana) + ascendant contribution
    balance_adjusted: bool               # True: timelines use the Moon's-arc birth balance


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


def _birth_balance(chart: ParasharaChart) -> float:
    """The fraction of the birth mahadasha already elapsed at birth — the Moon's arc THROUGH its
    nakshatra (BPHS-46:21-22, the Bhayat/Bhabhog balance, in its arc-proportional form). The Moon's
    longitude is already in the chart, so this needs no extra input; the strict time-based
    Bhayat/Bhabhog (ghatika) variant is a later refinement."""
    nak_span = 360.0 / 27.0
    return (chart.longitudes["Moon"] % nak_span) / nak_span


def _count_dasha_applicability(chart: ParasharaChart) -> dict[str, bool]:
    """Evaluate the adoption condition of each of the seven count-from-anchor dashas (ch.46), from
    primitives the chart already carries (the lagna's Hora/Navamsa/Dwadasamsa, lord placements,
    Vargottama, day/night)."""
    from app.parashara.doctrine.vargottama import is_vargottama
    from app.raman_saab.chart import varga as _varga         # substrate: pure division arithmetic

    asc = chart.asc_longitude % 360.0
    hora_lord = "Sun" if _varga.varga_sign(asc, 2) == 5 else "Moon"   # Leo=Sun's hora, Cancer=Moon's
    d9 = _varga.varga_sign(asc, 9)
    d12 = _varga.varga_sign(asc, 12)

    def lord_house(house: int) -> int | None:
        lord = SIGN_LORDS[((chart.asc_sign - 1 + house - 1) % 12) + 1]
        lon = chart.longitudes.get(lord)
        return None if lon is None else ((int(lon % 360.0 // 30) + 1 - chart.asc_sign) % 12) + 1

    return {
        "shodasottari": (hora_lord == "Moon" and not chart.moon_waxing)
                        or (hora_lord == "Sun" and chart.moon_waxing),
        "dwadasottari": d9 in (2, 7),                        # lagna in a Venus navamsa
        "panchottari": chart.asc_sign == 4 and d12 == 4,     # Cancer lagna in Cancer dwadasamsa
        "shatabdika": is_vargottama(chart.asc_longitude),
        "chaturashiti_sama": lord_house(10) == 10,
        "dwisaptati_sama": lord_house(1) in (1, 7),
        "shattrimsat_sama": chart.kala.is_day and hora_lord == "Sun",
    }


def _dashas(chart: ParasharaChart) -> tuple[DashaReading, ...]:
    nak = chart.janma_nakshatra
    elapsed = _birth_balance(chart)
    # Vimshottari is the primary system — "the most appropriate and the best of all Dasas"
    # (BPHS-46 sl.12-14) — general, always reported first, balance-adjusted from the Moon's arc.
    vim_periods = vim.timeline(nak, elapsed_fraction=elapsed)
    _vim_index = {lord: i for i, (lord, _) in enumerate(vim.CYCLE)}
    vim_bhuktis: list[tuple[str, tuple[DashaPeriod, ...]]] = []
    for i, p in enumerate(vim_periods):
        md_years = vim.CYCLE[_vim_index[p.lord]][1]
        # The birth mahadasha truly began `elapsed` of its length BEFORE birth; anchor its bhuktis
        # there so the running bhukti and every future date are correct (later mahadashas start clean).
        md_start = p.start_year - elapsed * md_years if i == 0 else p.start_year
        vim_bhuktis.append((p.lord, bhukti_timeline(vim.CYCLE, _vim_index[p.lord],
                                                    mahadasha_start_year=md_start)))
    vimshottari = DashaReading(
        system="vimshottari", applicable=True,
        reason="the primary 120-year system (BPHS-46 sl.12-14)",
        timeline=vim_periods, bhuktis=tuple(vim_bhuktis))
    # Yogini is a general system (no adoption condition stated) — always reported.
    yogini = DashaReading(
        system="yogini", applicable=True,
        reason="general system (no special adoption condition)",
        timeline=yog.timeline(nak, elapsed_fraction=elapsed))
    # Ashtottari is conditional on Rahu's placement.
    from_lagna, from_lord = _rahu_house_from(chart)
    ash_ok = ash.is_applicable(rahu_house_from_lagna=from_lagna,
                               rahu_house_from_lagna_lord=from_lord)
    ashtottari = DashaReading(
        system="ashtottari", applicable=ash_ok,
        reason=("Rahu not in Lagna/Kendra or a trikona from the lagna lord"
                if ash_ok else "Rahu in Lagna/Kendra or a trikona from the lagna lord"),
        timeline=ash.timeline(nak, elapsed_fraction=elapsed) if ash_ok else ())

    # The seven count-from-anchor conditional systems (ch.46), each reported with its adoption
    # condition met-or-not (like Ashtottari).
    applic = _count_dasha_applicability(chart)
    count_systems = []
    for name, sysdef in cds.SYSTEMS.items():
        ok = applic.get(name, False)
        count_systems.append(DashaReading(
            system=name, applicable=ok,
            reason=f"{sysdef.applicability} — {'met' if ok else 'not met'}",
            timeline=sysdef.timeline(nak, elapsed_fraction=elapsed) if ok else ()))
    return (vimshottari, yogini, ashtottari, *count_systems)


def _argala(chart: ParasharaChart) -> dict[int, tuple[Argala, ...]]:
    """The argalas (ch.31) acting on each of the twelve houses (keyed by house 1..12)."""
    signs = {g: int(lon % 360.0 // 30) + 1 for g, lon in chart.longitudes.items()}
    return {h: argala_for(((chart.asc_sign - 1 + h - 1) % 12) + 1, signs) for h in range(1, 13)}


def _planet_house_effects(chart: ParasharaChart) -> dict[str, tuple[int, Sloka]]:
    """For each graha, its house from the lagna and Saravali's effect for that placement (ch.30)."""
    out: dict[str, tuple[int, Sloka]] = {}
    for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        lon = chart.longitudes.get(g)
        if lon is None:
            continue
        house = ((int(lon % 360.0 // 30) + 1 - chart.asc_sign) % 12) + 1
        eff = planet_in_house(g, house)
        if eff is not None:
            out[g] = (house, eff)
    return out


def _upagraha_house_effects(chart: ParasharaChart) -> dict[str, tuple[int, Sloka]]:
    """Each Sun-derived upagraha's house from the lagna and Parashara's effect for it (BPHS ch.25)."""
    out: dict[str, tuple[int, Sloka]] = {}
    for name, lon in _upagrahas(chart.longitudes["Sun"]).items():
        house = ((int(lon % 360.0 // 30) + 1 - chart.asc_sign) % 12) + 1
        eff = _upagraha_house_effect(name, house)
        if eff is not None:
            out[name] = (house, eff)
    return out


def _graha_signs_with_nodes(chart: ParasharaChart) -> dict[str, int]:
    """Every body's sign (1..12), nodes included — for maraka (Rahu/Ketu are malefics)."""
    return {g: int(lon % 360.0 // 30) + 1 for g, lon in chart.longitudes.items()}


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


def _solar_yogas(chart: ParasharaChart) -> tuple[SolarYoga, ...]:
    """Solar yogas reckoned from the Sun (ch.38)."""
    signs = {g: int(lon % 360.0 // 30) + 1 for g, lon in chart.longitudes.items()}
    sun_sign = signs.get("Sun")
    if sun_sign is None:
        return ()
    return detect_solar_yogas(signs, sun_sign=sun_sign)


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
        d = deeptadi(g, chart.longitudes, speeds=chart.speeds)
        lj = lajjitadi(g, chart.longitudes, asc_sign=chart.asc_sign)
        out[g] = GrahaAvastha(baladi=b.state, baladi_grade=b.grade,
                              jagradadi=j.state, jagradadi_grade=j.grade,
                              deeptadi=d.state, deeptadi_vikala=d.vikala, deeptadi_kopa=d.kopa,
                              lajjitadi=tuple(a for a in _LAJJITADI_ORDER if a in lj),
                              lajjitadi_destroys_house=destroys_its_house(lj))
    return out


def transits_on(chart: ParasharaChart, *, year: int, month: int, day: int,
                hour: int = 12, minute: int = 0, tz_offset: float = 0.0):
    """Gochara (ch.70) for a transit date: each graha's transit judged by its NATAL ashtakavarga.

    A capability offered separately from the natal `read` (a transit needs a date, which the
    deterministic natal reading has no business carrying). Returns {graha: TransitJudgment}.
    """
    from app.parashara.chart.ephemeris import transit_signs
    from app.parashara.doctrine.gochara import all_transits
    ts = transit_signs(year=year, month=month, day=day, hour=hour, minute=minute, tz_offset=tz_offset)
    return all_transits(_graha_signs(chart), ts, asc_sign=chart.asc_sign)


def running_dasha(chart: ParasharaChart) -> tuple[str, str, str]:
    """The Vimshottari (mahadasha, bhukti, pratyantar) lords running AT BIRTH (BPHS ch.46).

    Uses the Moon's-arc balance to place birth within the mahadasha, then within the bhukti, then the
    pratyantar — the "where are we" query, and the natural home for pratyantar depth."""
    from app.parashara.primitives.nakshatra_dasha import pratyantar_timeline
    elapsed = _birth_balance(chart)
    md_index = vim.seed(chart.janma_nakshatra).index
    md_years = vim.CYCLE[md_index][1]
    into_md = elapsed * md_years
    bhuktis = bhukti_timeline(vim.CYCLE, md_index)
    bi = next(i for i, b in enumerate(bhuktis) if b.start_year <= into_md < b.end_year)
    into_bhukti = into_md - bhuktis[bi].start_year
    prats = pratyantar_timeline(vim.CYCLE, md_index, bi)
    pr = next(p for p in prats if p.start_year <= into_bhukti < p.end_year)
    return vim.CYCLE[md_index][0], bhuktis[bi].lord, pr.lord


def read(chart: ParasharaChart) -> ParasharaReading:
    """Assemble the full Parashara reading for a cast chart."""
    shadbala = partial_shadbala_all(chart.longitudes, asc_sign=chart.asc_sign,
                                    asc_longitude=chart.asc_longitude,
                                    moon_waxing=chart.moon_waxing,
                                    speeds=chart.speeds, ayanamsa=chart.ayanamsa,
                                    kala_ctx=chart.kala)
    _nisargayu_full = nisargayu_full(chart)
    return ParasharaReading(
        chart=chart,
        bhavas=judge_all_bhavas(chart.longitudes, asc_sign=chart.asc_sign,
                                moon_waxing=chart.moon_waxing),
        # the richer verdict gets the full six-fold Shadbala here (a cast chart can compute it).
        richer_bhavas=richer_all_bhavas(chart.longitudes, asc_sign=chart.asc_sign,
                                        moon_waxing=chart.moon_waxing,
                                        shadbala_rupas={g: s.rupas for g, s in shadbala.items()}),
        vimsopaka=vimsopaka_all(chart.longitudes, scheme="shodasavarga"),
        shadbala=shadbala,
        avasthas=_avasthas(chart),
        bhava_lord_effects=_bhava_lord_effects(chart),
        argala=_argala(chart),
        functional_class=fbl.classify_all(chart.asc_sign),
        yogakarakas=fbl.yogakaraka(chart.asc_sign),
        marakas=tuple(p for p in fbl.classify_all(chart.asc_sign)
                      if fbl.is_maraka(p, chart.asc_sign)),
        maraka_planets=maraka_planets(_graha_signs_with_nodes(chart), asc_sign=chart.asc_sign),
        planet_house_effects=_planet_house_effects(chart),
        dignity_concentrations=active_concentrations(
            {g: int(chart.longitudes[g] % 360.0 // 30) + 1
             for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
             if g in chart.longitudes}),
        chara_karakas=chara_karakas(chart.longitudes),
        karakamsa_sign=karakamsa(chart.longitudes),
        conjunctions=tuple(active_conjunctions(chart.longitudes)),
        triple_conjunctions=tuple(active_triple_conjunctions(chart.longitudes)),
        upagrahas=_upagrahas(chart.longitudes["Sun"]),
        upagraha_house_effects=_upagraha_house_effects(chart),
        shodasavarga=_shodasavarga_all(chart.longitudes),
        drekkanas=_drekkana_all(chart.longitudes),
        sudarshana=_sudarshana(chart),
        arudhas=_bhava_arudhas(chart),
        pada_finance=_pada_finance(chart),
        spouse_from_upapada=_spouse_from_upapada(chart),
        gulika_sign=int(chart.gulika % 360.0 // 30) + 1,
        gulika_house=((int(chart.gulika % 360.0 // 30) + 1 - chart.asc_sign) % 12) + 1,
        gulika_effect=gulika_effect_in_house(
            ((int(chart.gulika % 360.0 // 30) + 1 - chart.asc_sign) % 12) + 1),
        nabhasa=_nabhasa(chart),
        chandra_yogas=_chandra_yogas(chart),
        solar_yogas=_solar_yogas(chart),
        dhana_yogas=detect_dhana_yogas(chart.longitudes, asc_sign=chart.asc_sign),
        daridra_yogas=detect_daridra_yogas(chart.longitudes, asc_sign=chart.asc_sign),
        mahapurusha=_mahapurusha(chart),
        special_yogas=_special_yogas(chart),
        vargottama=vargottama_bodies(chart.longitudes, asc_longitude=chart.asc_longitude),
        sav=_av.sarvashtakavarga(_graha_signs(chart), asc_sign=chart.asc_sign),
        bav={g: _av.bhinnashtakavarga(g, _graha_signs(chart), asc_sign=chart.asc_sign)
             for g in _av.PLANETS},
        dashas=_dashas(chart),
        sthira=_sthira(chart),
        nisargayu=nisargayu_span(chart.longitudes),
        nisargayu_haranas=_nisargayu_full.haranas,
        nisargayu_full=_nisargayu_full,
        balance_adjusted=True,
    )


def _sthira(chart: ParasharaChart) -> SthiraReading:
    bg = brahma_graha(chart)
    return SthiraReading(brahma_graha=bg, timeline=sthira_timeline(bg.sign))
