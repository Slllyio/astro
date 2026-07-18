"""Candidate generation for birth-time rectification — equivalence classes, not minutes.

Chart judgment is PIECEWISE-CONSTANT in birth time: two candidate times judge identically
unless a boundary lies between them (lagna sign, navamsa lagna ~13 min, Moon nakshatra/
pada, a planet's sign cusp, a bhava-sandhi crossing, or a Dasha/Bhukti/Pratyantar lord
flip at a registered event date). So the candidate space is walked with an adaptive probe
and BISECTED at boundaries, emitting one representative per equivalence class — never a
naive minute grid through the expensive full cast.

Two chart tiers:
  * Tier-L (light)  — positions-only ``RamanChart`` built from ~10 swisseph calls
    (mirrors ``adapter.cast_chart`` lines 24-56; NO Shadbala/upagraha/maraka passes).
    Sufficient for ``timer_set`` / ``active_houses`` / ``pratyantar_on`` / ``maraka_set``
    (which has a documented Track-B fallback). Used for ALL event scoring.
  * Tier-F (full)   — ``adapter.cast_chart`` (eager Shadbala). Only for the natal-fact
    channel (``judge_house`` needs Shadbala) on top-K candidates.

Usage:
    from app.raman_saab.rectification import candidates as C
    cands = C.generate_candidates(
        year=1989, month=10, day=12, latitude=27.23, longitude=79.03, tz_offset=5.5,
        window_local_hours=(9.0, 11.0), ayanamsas=("raman", "lahiri"),
        event_jds=(vim.date_to_jd(2017, 12, 4),))
    cache = C.ChartCache()
    chart_light = cache.light(cands[0])
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Final, Optional

import swisseph as swe

from app.raman_saab.chart import cusps, varga
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.constants import SIGN_LORDS, SWE_PLANETS
from app.raman_saab.chart.model import BirthData, PlanetPos, RamanChart
from app.raman_saab.primitives import vimshottari as vim

_FLAGS: Final[int] = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
_SIGNS: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
#: Initial walk step (seconds). The finest recurring boundary is the navamsa lagna
#: (~13 min of clock time), so 4 minutes over-samples it; bisection then localises.
_WALK_STEP_S: Final[float] = 240.0
#: Bisection tolerance (seconds) for locating a boundary.
_BISECT_TOL_S: Final[float] = 5.0
_DAY_S: Final[float] = 86400.0


@dataclass(frozen=True)
class ProbeState:
    """Everything piecewise-discrete about a candidate birth instant (one ayanamsa)."""
    jd_ut: float
    ayanamsa: str
    asc_sign: int
    asc_lon: float
    navamsa_lagna: int
    moon_lon: float
    moon_nakshatra: int
    moon_pada: int
    planet_signs: tuple[int, ...]        # SWE order + Rahu, Ketu
    bhava_vector: tuple[int, ...]        # cusp-based bhava per planet (same order)
    sandhi_flags: tuple[bool, ...]


@dataclass(frozen=True)
class CandidateChart:
    """One equivalence class of birth times under one ayanamsa: its representative
    instant, the CLAIMABLE resolution (the class interval), the discrete features, the
    per-registered-event (MD, AD, PD) lord triples, and the human-readable labels of the
    boundaries that bound the class."""
    ayanamsa: str
    birth: BirthData                     # representative, rounded to the minute in-class
    birth_jd: float                      # representative instant (UT), un-rounded
    time_str: str                        # local "HH:MM:SS" of the representative
    class_id: str
    interval_local: tuple[str, str]      # local "HH:MM:SS" bounds of the class
    features: ProbeState
    period_triples: tuple[tuple[str, Optional[str], Optional[str]], ...]
    boundaries: tuple[str, ...]


@dataclass(frozen=True)
class _Probe:
    state: ProbeState
    chart: RamanChart                    # Tier-L
    triples: tuple[tuple[str, Optional[str], Optional[str]], ...]
    key: str


def _local_hms(jd_ut: float, tz_offset: float) -> str:
    """UT Julian Day -> local 'HH:MM:SS' (civil clock at the birth place)."""
    y, mo, d, hour = swe.revjul(jd_ut + tz_offset / 24.0, swe.GREG_CAL)
    total_s = round(hour * 3600.0)
    hh, rem = divmod(total_s, 3600)
    mm, ss = divmod(rem, 60)
    return f"{int(hh) % 24:02d}:{int(mm):02d}:{int(ss):02d}"


def light_chart(jd_ut: float, latitude: float, longitude: float,
                ayanamsa: str) -> RamanChart:
    """Positions-only ``RamanChart`` at ``jd_ut`` — mirrors ``adapter.cast_chart``
    lines 24-56 (same Porphyry madhyas, MEAN node, PlanetPos fields) but SKIPS the
    combustion/Shadbala/upagraha/maraka passes. ``shadbala_rupas`` stays None, so the
    strength-dependent judges must never see this chart (scoring enforces the tier)."""
    with sidereal_mode(ayanamsa):
        cusp_arr, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b"O", swe.FLG_SIDEREAL)
        madhyas = tuple(float(x) for x in cusp_arr[:12])
        sandhis = cusps.sandhis_from_madhyas(madhyas)
        asc_lon = float(ascmc[0])
        asc_sign = int(asc_lon // 30) + 1
        raw: dict[str, tuple[float, bool]] = {}
        for name, pid in SWE_PLANETS.items():
            res, _ = swe.calc_ut(jd_ut, pid, _FLAGS)
            raw[name] = (float(res[0]) % 360.0, res[3] < 0)
        node, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, _FLAGS)
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
    return RamanChart(ayanamsa=ayanamsa, jd_ut=jd_ut, asc_sign=asc_sign, asc_lon=asc_lon,
                      bhava_madhyas=madhyas, bhava_sandhis=sandhis, planets=planets)


def _probe(jd_ut: float, latitude: float, longitude: float, ayanamsa: str,
           event_jds: tuple[float, ...]) -> _Probe:
    chart = light_chart(jd_ut, latitude, longitude, ayanamsa)
    order = tuple(SWE_PLANETS) + ("Rahu", "Ketu")
    moon = chart.planets["Moon"]
    state = ProbeState(
        jd_ut=jd_ut, ayanamsa=ayanamsa,
        asc_sign=chart.asc_sign, asc_lon=chart.asc_lon,
        navamsa_lagna=varga.navamsa_sign(chart.asc_lon),
        moon_lon=moon.lon, moon_nakshatra=moon.nakshatra, moon_pada=moon.pada,
        planet_signs=tuple(chart.planets[n].sign for n in order),
        bhava_vector=tuple(chart.planets[n].bhava for n in order),
        sandhi_flags=tuple(chart.planets[n].bhava_sandhi for n in order))
    triples: list[tuple[str, Optional[str], Optional[str]]] = []
    for ejd in event_jds:
        pd = vim.pratyantar_on(chart, ejd)
        if pd is None:
            triples.append(("?", None, None))
        else:
            triples.append((pd.maha, pd.antar, pd.pratyantar))
    return _Probe(state=state, chart=chart, triples=tuple(triples),
                  key=_feature_key(state, tuple(triples)))


def _feature_key(state: ProbeState,
                 triples: tuple[tuple[str, Optional[str], Optional[str]], ...]) -> str:
    """Stable hash of every piecewise-discrete feature — two instants with the same key
    are judged identically by the event-scoring machinery."""
    parts = (state.ayanamsa, state.asc_sign, state.navamsa_lagna, state.moon_nakshatra,
             state.moon_pada, state.planet_signs, state.bhava_vector, state.sandhi_flags,
             triples)
    return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]


def _boundary_labels(a: _Probe, b: _Probe, event_jds: tuple[float, ...]) -> tuple[str, ...]:
    """Human-readable names of the features that differ between two adjacent probes."""
    out: list[str] = []
    sa, sb = a.state, b.state
    if sa.asc_sign != sb.asc_sign:
        out.append(f"lagna {_SIGNS[sa.asc_sign - 1]}->{_SIGNS[sb.asc_sign - 1]}")
    if sa.navamsa_lagna != sb.navamsa_lagna:
        out.append(f"navamsa lagna {_SIGNS[sa.navamsa_lagna - 1]}->"
                   f"{_SIGNS[sb.navamsa_lagna - 1]}")
    if (sa.moon_nakshatra, sa.moon_pada) != (sb.moon_nakshatra, sb.moon_pada):
        out.append(f"Moon nakshatra/pada {sa.moon_nakshatra}.{sa.moon_pada}->"
                   f"{sb.moon_nakshatra}.{sb.moon_pada}")
    if sa.planet_signs != sb.planet_signs:
        out.append("planet sign cusp")
    if sa.bhava_vector != sb.bhava_vector or sa.sandhi_flags != sb.sandhi_flags:
        out.append("bhava/sandhi shift")
    for i, (ta, tb) in enumerate(zip(a.triples, b.triples)):
        if ta != tb:
            out.append(f"dasha chain at event#{i + 1} {'/'.join(x or '-' for x in ta)}"
                       f"->{'/'.join(x or '-' for x in tb)}")
    return tuple(out) if out else ("(unlabelled feature shift)",)


def _bisect(lo: _Probe, hi: _Probe, latitude: float, longitude: float, ayanamsa: str,
            event_jds: tuple[float, ...]) -> tuple[float, _Probe]:
    """Locate the boundary between two differing probes to ±_BISECT_TOL_S seconds.
    Returns (boundary_jd, probe-at-or-after-boundary)."""
    lo_jd, hi_jd = lo.state.jd_ut, hi.state.jd_ut
    hi_probe = hi
    while (hi_jd - lo_jd) * _DAY_S > _BISECT_TOL_S:
        mid_jd = (lo_jd + hi_jd) / 2.0
        mid = _probe(mid_jd, latitude, longitude, ayanamsa, event_jds)
        if mid.key == lo.key:
            lo_jd = mid_jd
        else:
            hi_jd, hi_probe = mid_jd, mid
    return hi_jd, hi_probe


def generate_candidates(
    *, year: int, month: int, day: int,
    latitude: float, longitude: float, tz_offset: float,
    window_local_hours: tuple[float, float],
    ayanamsas: tuple[str, ...] = ("raman", "lahiri"),
    event_jds: tuple[float, ...] = (),
    walk_step_s: float = _WALK_STEP_S,
) -> tuple[CandidateChart, ...]:
    """Walk the local-time window under each ayanamsa, bisect every feature boundary,
    and emit one ``CandidateChart`` per equivalence class (representative = midpoint)."""
    lo_h, hi_h = window_local_hours
    if not hi_h > lo_h:
        raise ValueError(f"empty window {window_local_hours}")
    out: list[CandidateChart] = []
    for ayanamsa in ayanamsas:
        start_jd = swe.julday(year, month, day, lo_h - tz_offset, swe.GREG_CAL)
        end_jd = swe.julday(year, month, day, hi_h - tz_offset, swe.GREG_CAL)
        classes: list[tuple[float, float, _Probe, tuple[str, ...]]] = []
        cur_start = start_jd
        cur = _probe(cur_start, latitude, longitude, ayanamsa, event_jds)
        opening: tuple[str, ...] = ("window start",)
        jd = cur_start
        while jd < end_jd:
            nxt_jd = min(jd + walk_step_s / _DAY_S, end_jd)
            nxt = _probe(nxt_jd, latitude, longitude, ayanamsa, event_jds)
            if nxt.key != cur.key:
                b_jd, b_probe = _bisect(cur, nxt, latitude, longitude, ayanamsa, event_jds)
                labels = _boundary_labels(cur, b_probe, event_jds)
                classes.append((cur_start, b_jd, cur, opening + labels))
                cur_start, cur, opening = b_jd, b_probe, labels
            jd = nxt_jd
        classes.append((cur_start, end_jd, cur, opening + ("window end",)))

        for c_start, c_end, probe0, labels in classes:
            mid_jd = (c_start + c_end) / 2.0
            rep = _probe(mid_jd, latitude, longitude, ayanamsa, event_jds)
            # Representative BirthData rounded to the whole minute, clamped in-class.
            y, mo, d, hour_l = swe.revjul(mid_jd + tz_offset / 24.0, swe.GREG_CAL)
            hh = int(hour_l)
            mm = int(round((hour_l - hh) * 60.0))
            if mm == 60:
                hh, mm = hh + 1, 0
            birth = BirthData(name="candidate", year=int(y), month=int(mo), day=int(d),
                              hour=hh % 24, minute=mm, tz_offset=tz_offset,
                              latitude=latitude, longitude=longitude)
            out.append(CandidateChart(
                ayanamsa=ayanamsa, birth=birth, birth_jd=mid_jd,
                time_str=_local_hms(mid_jd, tz_offset),
                class_id=rep.key,
                interval_local=(_local_hms(c_start, tz_offset),
                                _local_hms(c_end, tz_offset)),
                features=rep.state, period_triples=rep.triples, boundaries=labels))
    return tuple(out)


class ChartCache:
    """Memoises charts per (class_id, tier) — mirrors tune_thresholds' _ChartCache.
    Guarantees the expensive full cast runs at most once per surviving candidate."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], RamanChart] = {}

    def light(self, cand: CandidateChart) -> RamanChart:
        key = (cand.class_id, "L")
        if key not in self._cache:
            self._cache[key] = light_chart(
                cand.birth_jd, cand.birth.latitude, cand.birth.longitude, cand.ayanamsa)
        return self._cache[key]

    def full(self, cand: CandidateChart) -> RamanChart:
        key = (cand.class_id, "F")
        if key not in self._cache:
            self._cache[key] = cast_chart(cand.birth, ayanamsa=cand.ayanamsa)
        return self._cache[key]
