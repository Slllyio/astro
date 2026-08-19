"""Run-5 golden-case registry — loader, OCR validator, and held-out split.

The registry (``data/raman_saab/nh_golden_cases_v2.json``) holds every
own-death verdict extractable from *Notable Horoscopes* (~57 cases; archive.org
``NotableHoroscopesBVR``): Raman's PRINTED planetary positions (his ayanamsa,
his data), his stated MD/AD at death, the planets he names as killers, and
mechanism tags. Verbatim quotes live in ``docs/raman_saab/sources/NH_EXCERPTS.md``.

**OCR auto-validation (objective, pre-split):** a case is usable only if the
Vimshottari timeline built from the PRINTED Moon reproduces Raman's stated MD
at death. The stated AD is checked and RECORDED as a flag (``ad_anchor_ok``)
but is not a hard filter: run 4 proved (Gandhi) that Raman's own dasha
arithmetic can disagree with his printed Moon at AD granularity even when the
transcription is verbatim-correct, so an AD-hard filter would conflate his
internal rounding with OCR error. Dual printed birth dates ("23rd/24th May")
are disambiguated by trying each candidate; the passing date is recorded.

**Date repair (objective, position-driven):** OCR also corrupts the printed
birth DATE (e.g. Marx "15th May 1818" for the historical 5 May — the printed
positions fit 5 May, not 15 May). Before anchoring, the validator scans
birth-date candidates within ±15 days; if some date fits the printed
positions decisively better (≥6 of 8 planets within 1.5° of a Raman-frame
ephemeris, and ≥2 more matching planets than the printed date), that date is
adopted and recorded. The repair consults ONLY the printed positions — never
the death verdict — so it cannot leak the label.

A ±2° cross-check against a Raman-frame ephemeris flags (never excludes)
residual suspect planets — Raman's printed values legitimately differ from
modern ephemerides by up to ~1° (more for his ancient reconstructions).

**Split:** validated Tier-A cases are shuffled with SPLIT_SEED and halved into
``calibration`` and ``held_out``. Weights may be tuned on the calibration half
ONLY; the held-out half is scored once, after the RUN5 freeze.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import swisseph as swe

from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab.chart_bundle import GRAHAS, ChartBundle, bundle_from_positions

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path("data/raman_saab/nh_golden_cases_v2.json")
SPLIT_SEED = 20260704
_CROSS_CHECK_ORB_DEG = 2.0


@dataclass
class GoldenCaseV2:
    key: str
    name: str
    tier: str
    birth_dates: list
    hour_local: float
    time_basis: str
    calendar: str
    lat: float
    lon_east: float
    death: object                # [y,m,d] or {"age_years": x}
    death_precision: str         # day | year | age
    positions: dict              # graha -> degrees (float); may be empty
    lagna_lon: float | None
    raman_md: str | None
    raman_ad: str | None
    named_killers: list
    stated_band: str | None
    mechanisms: list
    retro: list
    exclude: bool
    exclude_reason: str | None
    # filled by validation:
    valid: bool = False
    birth_date_used: list | None = None
    date_repaired: bool = False
    birth_jd: float = 0.0
    death_jd: float = 0.0
    ad_anchor_ok: bool | None = None
    fail_reason: str | None = None
    suspect_planets: list = field(default_factory=list)


def _dms_to_deg(v) -> float:
    return float(v[0]) + float(v[1]) / 60.0


def _cal(case_cal: str) -> int:
    return swe.JUL_CAL if case_cal == "julian" else swe.GREG_CAL


def load_registry(path: Path = REGISTRY_PATH) -> list[GoldenCaseV2]:
    raw = json.loads(Path(path).read_text())
    out = []
    for c in raw["cases"]:
        pos = {g: _dms_to_deg(v) for g, v in (c.get("positions_dms") or {}).items()}
        if pos and "Ketu" not in pos and "Rahu" in pos:
            pos["Ketu"] = (pos["Rahu"] + 180.0) % 360.0
        out.append(GoldenCaseV2(
            key=c["key"], name=c["name"], tier=c["tier"],
            birth_dates=c["birth_dates"], hour_local=c["hour_local"],
            time_basis=c.get("time_basis", "LMT"),
            calendar=c.get("calendar", "gregorian"),
            lat=c["lat"], lon_east=c["lon_east"],
            death=c["death"], death_precision=c["death_precision"],
            positions=pos,
            lagna_lon=_dms_to_deg(c["lagna_dms"]) if c.get("lagna_dms") else None,
            raman_md=c.get("raman_md"), raman_ad=c.get("raman_ad"),
            named_killers=c.get("named_killers", []),
            stated_band=c.get("stated_band"),
            mechanisms=c.get("mechanisms", []),
            retro=c.get("retro", []),
            exclude=bool(c.get("exclude")), exclude_reason=c.get("exclude_reason"),
        ))
    return out


def _tz_hours(case: GoldenCaseV2) -> float:
    if case.time_basis == "IST":
        return 5.5
    return case.lon_east / 15.0  # LMT


def _birth_jd(case: GoldenCaseV2, date) -> float:
    y, m, d = date
    return swe.julday(int(y), int(m), int(d),
                      case.hour_local - _tz_hours(case), _cal(case.calendar))


def _death_jd(case: GoldenCaseV2, birth_jd: float) -> float:
    if isinstance(case.death, dict):
        return birth_jd + case.death["age_years"] * D.DAYS_PER_VEDIC_YEAR
    y, m, d = case.death
    cal = _cal(case.calendar) if int(y) < 1752 else swe.GREG_CAL
    return swe.julday(int(y), int(m), int(d), 12.0, cal)


def _md_ad_at(moon_lon: float, birth_jd: float, jd: float):
    mds = D.md_intervals(moon_lon, birth_jd)
    md = D.lord_at(jd, mds)
    ad = D.lord_at(jd, D.ad_intervals(moon_lon, birth_jd))
    return md, ad


def _cross_check(case: GoldenCaseV2, birth_jd: float) -> list[str]:
    """Planets whose printed position is >2° from a Raman-frame ephemeris."""
    suspects = []
    try:
        swe.set_sid_mode(swe.SIDM_RAMAN)
        flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
        ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
               "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
               "Venus": swe.VENUS, "Saturn": swe.SATURN,
               "Rahu": swe.MEAN_NODE}
        for g, pid in ids.items():
            if g not in case.positions:
                continue
            eph = swe.calc_ut(birth_jd, pid, flags)[0][0] % 360.0
            diff = abs((case.positions[g] - eph + 180.0) % 360.0 - 180.0)
            if diff > _CROSS_CHECK_ORB_DEG:
                suspects.append(f"{g}:{diff:.1f}deg")
    except Exception as exc:  # noqa: BLE001 — ancient dates may stress moshier
        suspects.append(f"ephemeris_unavailable:{exc}")
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    return suspects


_EPH_IDS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
_REPAIR_ORB_DEG = 1.5
_REPAIR_SPAN_DAYS = 15
_REPAIR_MIN_FIT = 6
_REPAIR_MIN_GAIN = 2


def _position_fit(case: GoldenCaseV2, bjd: float) -> int:
    """How many of the 8 printed positions match a Raman-frame ephemeris."""
    try:
        swe.set_sid_mode(swe.SIDM_RAMAN)
        flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
        n = 0
        for g, pid in _EPH_IDS.items():
            if g not in case.positions:
                continue
            eph = swe.calc_ut(bjd, pid, flags)[0][0] % 360.0
            if abs((case.positions[g] - eph + 180.0) % 360.0 - 180.0) <= _REPAIR_ORB_DEG:
                n += 1
        return n
    except Exception:  # noqa: BLE001
        return -1
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)


def _repair_date(case: GoldenCaseV2) -> tuple[float, bool]:
    """Best-fitting birth_jd for the PRINTED positions (label-blind).

    Scans ±_REPAIR_SPAN_DAYS around the first printed date; adopts an
    alternative only on a decisive positional fit. Returns (birth_jd,
    repaired?).
    """
    base_jd = _birth_jd(case, case.birth_dates[0])
    candidates = [(_birth_jd(case, d), False) for d in case.birth_dates]
    base_fit = max((_position_fit(case, jd) for jd, _ in candidates),
                   default=-1)
    best_jd, best_fit = candidates[0][0], base_fit
    for jd, _ in candidates:
        if _position_fit(case, jd) == base_fit:
            best_jd = jd
            break
    for off in range(-_REPAIR_SPAN_DAYS, _REPAIR_SPAN_DAYS + 1):
        if off == 0:
            continue
        jd = base_jd + off
        fit = _position_fit(case, jd)
        if fit > best_fit:
            best_jd, best_fit = jd, fit
    repaired = (best_fit >= _REPAIR_MIN_FIT
                and best_fit - base_fit >= _REPAIR_MIN_GAIN)
    if not repaired:
        return best_jd if best_fit == base_fit else base_jd, False
    return best_jd, True


def validate_case(case: GoldenCaseV2) -> GoldenCaseV2:
    """Populate .valid/.birth_jd/.death_jd via the printed-Moon MD anchor."""
    if case.exclude:
        case.fail_reason = f"pre-excluded: {case.exclude_reason}"
        return case
    required = set(GRAHAS)
    if not required.issubset(case.positions) or case.lagna_lon is None:
        case.fail_reason = "positions incomplete"
        return case
    if case.raman_md is None:
        case.fail_reason = "no stated MD"
        return case
    moon = case.positions["Moon"]

    # candidate birth JDs: each printed date, plus the position-fit repair.
    # A decisive repair goes FIRST — the printed date can pass the MD check
    # by luck while contradicting the printed positions (Marx: "15th" May
    # for the position-fitting 5 May).
    cand: list[tuple[float, list | None, bool]] = [
        (_birth_jd(case, d), list(d), False) for d in case.birth_dates
    ]
    rep_jd, repaired = _repair_date(case)
    if repaired and all(abs(rep_jd - jd) > 1e-6 for jd, _, _ in cand):
        cand.insert(0, (rep_jd, None, True))

    for bjd, date, was_repair in cand:
        djd = _death_jd(case, bjd)
        if not (0 < djd - bjd <= 130 * 366.0):
            continue
        md, ad = _md_ad_at(moon, bjd, djd)
        if md == case.raman_md:
            case.valid = True
            case.birth_date_used = date
            case.date_repaired = was_repair
            case.birth_jd, case.death_jd = bjd, djd
            case.ad_anchor_ok = (ad == case.raman_ad) if case.raman_ad else None
            case.suspect_planets = _cross_check(case, bjd)
            return case
    case.fail_reason = f"MD anchor mismatch (want {case.raman_md})"
    return case


def bundle_for(case: GoldenCaseV2) -> ChartBundle:
    retro = {g: (g in case.retro) for g in GRAHAS} if case.retro else None
    return bundle_from_positions(case.positions, case.lagna_lon,
                                 birth_jd=case.birth_jd, person_id=case.key,
                                 retrograde=retro)


def validate_all(path: Path = REGISTRY_PATH) -> list[GoldenCaseV2]:
    return [validate_case(c) for c in load_registry(path)]


def split(cases: list[GoldenCaseV2], seed: int = SPLIT_SEED
          ) -> tuple[list[GoldenCaseV2], list[GoldenCaseV2]]:
    """Seeded 50/50 split of VALID Tier-A cases -> (calibration, held_out)."""
    usable = sorted((c for c in cases if c.valid and c.tier == "A"),
                    key=lambda c: c.key)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(usable))
    half = (len(usable) + 1) // 2
    calib = [usable[i] for i in sorted(order[:half])]
    held = [usable[i] for i in sorted(order[half:])]
    return calib, held


def write_validation_report(cases: list[GoldenCaseV2], out: Path) -> dict:
    payload = {
        "n_total": len(cases),
        "n_valid": sum(c.valid for c in cases),
        "cases": [{
            "key": c.key, "valid": c.valid, "tier": c.tier,
            "birth_date_used": c.birth_date_used,
            "fail_reason": c.fail_reason,
            "suspect_planets": c.suspect_planets,
        } for c in cases],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1))
    return payload


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cases = validate_all()
    rep = write_validation_report(
        cases, Path("data/raman_saab/nh_golden_validation.json"))
    calib, held = split(cases)
    print(f"total={rep['n_total']} valid={rep['n_valid']} "
          f"calibration={len(calib)} held_out={len(held)}")
    for c in cases:
        mark = "OK " if c.valid else "-- "
        extra = (f" [suspect: {','.join(c.suspect_planets)}]"
                 if c.valid and c.suspect_planets else
                 (f" ({c.fail_reason})" if not c.valid else ""))
        print(f"  {mark}{c.key:<20}{extra}")
    print("calibration:", [c.key for c in calib])
    print("held_out:   ", [c.key for c in held])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
