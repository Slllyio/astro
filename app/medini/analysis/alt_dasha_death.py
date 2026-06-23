"""Fast gate: do classical ALTERNATE dashas time death better than Vimshottari?

We've mined the Parashari Vimshottari maraka signal (small, real). This screens the
death-specific dashas the engine already implements but never tested — Ashtottari (a
classical *death* dasha) and Yogini (health/death) — against the same maraka doctrine:
at each death, is the active dasha lord a maraka, more than that lord's share of its
own cycle predicts? Per-person dasha-length-weighted baseline; binomial z-test (the
`validate_maraka` methodology, generalised to any dasha).

Run: python -m app.medini.analysis.alt_dasha_death
Advance a dasha to the full held-out backtest only if lift>1 at p<0.01 (strict — many
techniques tested). Negatives are kept.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from app.core.yogas import SIGN_RULERS
from app.core.shodashavarga import compute_divisional_longitude
from app.core.yogini_ashtottari_dasha import (
    ASHTOTTARI_LORDS, ASHTOTTARI_PERIOD_YEARS, YOGINI_LORDS, YOGINI_PERIOD_YEARS,
    YOGINI_PRESIDING_PLANET, ashtottari_active_at, ashtottari_applicable,
    yogini_active_at,
)
from app.medini.analysis.doctrine_validator import (
    DASHA_LORDS, LORD_SHARE, _MARAKA_GRAHAS, _house_lord, _maraka_set, _norm_sf,
    open_catalog,
)

# Per-dasha lord → planet map + that planet's share of the cycle (for the baseline).
_VIMSHOTTARI_TOTAL = sum(y for _, y in DASHA_LORDS)
_ASHTOTTARI_TOTAL = sum(ASHTOTTARI_PERIOD_YEARS)
_YOGINI_TOTAL = sum(YOGINI_PERIOD_YEARS)

# planet → share of cycle (sum of that planet's periods / total)
_VIM_SHARE = {lord: yrs / _VIMSHOTTARI_TOTAL for lord, yrs in DASHA_LORDS}
_ASH_SHARE = {lord: yrs / _ASHTOTTARI_TOTAL
              for lord, yrs in zip(ASHTOTTARI_LORDS, ASHTOTTARI_PERIOD_YEARS)}
_YOG_SHARE: dict[str, float] = {}
for _yname, _yyrs in zip(YOGINI_LORDS, YOGINI_PERIOD_YEARS):
    _p = YOGINI_PRESIDING_PLANET[_yname]
    _YOG_SHARE[_p] = _YOG_SHARE.get(_p, 0.0) + _yyrs / _YOGINI_TOTAL


@dataclass(frozen=True)
class DashaResult:
    name: str
    n: int
    observed: float
    expected: float
    lift: float
    z: float
    p_value: float


def _test_dasha(rows: list, active_planet: Callable[[dict], str | None],
                share: dict[str, float], name: str) -> DashaResult:
    """Generic maraka-clustering test for one dasha system.

    `active_planet(row)` → the planet ruling the dasha active at the death (or None);
    `share` maps planet → fraction of the cycle it owns (the per-person baseline)."""
    obs = n = 0
    exp = 0.0
    for r in rows:
        planet = active_planet(r)
        if planet is None:
            continue
        mset = r["maraka"]
        n += 1
        obs += planet in mset
        exp += sum(share.get(m, 0.0) for m in mset)
    er = exp / n if n else 0.0
    orr = obs / n if n else 0.0
    se = math.sqrt(n * er * (1 - er)) if n and 0 < er < 1 else 0.0
    z = (obs - exp) / se if se else 0.0
    p = 2.0 * _norm_sf(abs(z))
    return DashaResult(name, n, round(orr, 4), round(er, 4),
                       round(orr / er, 3) if er else 0.0, round(z, 2), round(p, 6))


def _load_deaths(con) -> list[dict]:
    house_cols = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT e.event_jd, c.birth_jd_used AS bjd, c.asc_sign, c.moon_nakshatra,
                   c.rahu_house, {house_cols}
            FROM events_with_dasha e JOIN charts c USING(person_id)
            WHERE e.event_class='death_cause_unspecified' AND e.event_jd IS NOT NULL
              AND c.asc_sign IS NOT NULL AND c.moon_nakshatra IS NOT NULL
              AND c.birth_jd_used IS NOT NULL"""
    ).fetchall()
    out = []
    nc = len(_MARAKA_GRAHAS)
    for r in rows:
        ejd, bjd, asc, moon_nak, rahu_h = r[0], r[1], int(r[2]), int(r[3]), r[4]
        houses = r[5:5 + nc]
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        lagna_lord = SIGN_RULERS[asc]
        out.append({
            "ejd": float(ejd), "bjd": float(bjd), "asc": asc, "moon_nak": moon_nak,
            "maraka": _maraka_set(asc, gh, "full"),
            "rahu_h": int(rahu_h) if rahu_h is not None else None,
            "lagna_lord_h": gh.get(lagna_lord),
        })
    return out


def run(con=None) -> list[DashaResult]:
    own = con is None
    con = con or open_catalog()
    try:
        rows = _load_deaths(con)
    finally:
        if own:
            con.close()

    def ash(r):
        p = ashtottari_active_at(r["moon_nak"], r["bjd"], r["ejd"])
        return p.lord if p else None

    def ash_applicable(r):
        if r["rahu_h"] is None or r["lagna_lord_h"] is None:
            return None
        if not ashtottari_applicable(r["rahu_h"], r["lagna_lord_h"]):
            return None
        return ash(r)

    def yog(r):
        p = yogini_active_at(r["moon_nak"], r["bjd"], r["ejd"])
        return p.presiding_planet if p else None

    results = [
        _test_dasha(rows, ash, _ASH_SHARE, "Ashtottari MD (all charts)"),
        _test_dasha([r for r in rows if ash_applicable(r) is not None],
                    ash, _ASH_SHARE, "Ashtottari MD (applicable: Rahu kendra/trine)"),
        _test_dasha(rows, yog, _YOG_SHARE, "Yogini MD (presiding planet)"),
    ]
    return results


# --------------------------------------------------------------------------- #
# Significator battery — does a BETTER death significator exist than the        #
# textbook Lagna maraka? Tested against the strong Vimshottari MD-at-death.     #
# --------------------------------------------------------------------------- #

def _lord_from(sign: int, house: int) -> str:
    """Ruler of `house` counted (whole-sign) from any sign — Lagna/Moon/Sun/Karakāṁśa."""
    return SIGN_RULERS[((sign - 1 + house - 1) % 12) + 1]


def _d9_sign(lon: float) -> int:
    return int(compute_divisional_longitude(lon % 360.0, 9) // 30) + 1


def _sig_rows(con) -> list[dict]:
    hc = ", ".join(f"c.{g.lower()}_house AS {g.lower()}_h" for g in _MARAKA_GRAHAS)
    lc = ", ".join(f"c.{g.lower()}_lon AS {g.lower()}_lon" for g in _MARAKA_GRAHAS)
    rows = con.execute(
        f"""SELECT e.person_id, e.md_lord_at_event AS md, c.asc_sign, c.asc_lon, {hc}, {lc},
                   k.planet AS ak
            FROM events_with_dasha e JOIN charts c USING(person_id)
            LEFT JOIN jaimini_karakas k ON k.person_id=e.person_id
                                       AND k.karaka='AK_Atmakaraka'
            WHERE e.event_class='death_cause_unspecified'
              AND e.md_lord_at_event IS NOT NULL AND c.asc_sign IS NOT NULL"""
    ).fetchall()
    nc = len(_MARAKA_GRAHAS)
    out = []
    for r in rows:
        pid, md, asc, asclon = r[0], r[1], int(r[2]), float(r[3])
        houses = r[4:4 + nc]; lons = r[4 + nc:4 + 2 * nc]; ak = r[-1]
        gh = {g: (int(h) if h is not None else 0) for g, h in zip(_MARAKA_GRAHAS, houses)}
        lo = {g: l for g, l in zip(_MARAKA_GRAHAS, lons)}
        out.append({"pid": pid, "md": md, "asc": asc, "asclon": asclon,
                    "gh": gh, "lo": lo, "ak": ak})
    return out


def _sun_sign(r: dict) -> int:
    return ((r["asc"] - 1) + (r["gh"]["Sun"] - 1)) % 12 + 1


def _karakamsa_sign(r: dict) -> int | None:
    ak, lo = r["ak"], r["lo"]
    return _d9_sign(lo[ak]) if ak and lo.get(ak) is not None else None


_SIG_BATTERY: dict[str, Callable[[dict], set[str]]] = {
    "maraka from Lagna (baseline)": lambda r: _maraka_set(r["asc"], r["gh"], "full"),
    "maraka from Sun": lambda r: {_lord_from(_sun_sign(r), 2), _lord_from(_sun_sign(r), 7), "Saturn"},
    "maraka from Moon": lambda r: (
        {_lord_from(((r["asc"] - 1) + (r["gh"]["Moon"] - 1)) % 12 + 1, 2),
         _lord_from(((r["asc"] - 1) + (r["gh"]["Moon"] - 1)) % 12 + 1, 7), "Saturn"}),
    "maraka from Karakamsa (2&7+Sat)": lambda r: (
        {_lord_from(_karakamsa_sign(r), 2), _lord_from(_karakamsa_sign(r), 7), "Saturn"}
        if _karakamsa_sign(r) else set()),
    "2nd-from-Karakamsa lord": lambda r: (
        {_lord_from(_karakamsa_sign(r), 2)} if _karakamsa_sign(r) else set()),
    "8th-from-Karakamsa lord": lambda r: (
        {_lord_from(_karakamsa_sign(r), 8)} if _karakamsa_sign(r) else set()),
    "Atmakaraka": lambda r: {r["ak"]} if r["ak"] else set(),
    "8th lord (Lagna)": lambda r: {_house_lord(r["asc"], 8)},
}


def _test_significator(rows: list[dict], sigfn: Callable[[dict], set[str]],
                       name: str) -> DashaResult:
    """Is the Vimshottari MD-at-death this significator, vs its dasha-length share?"""
    obs = n = 0
    exp = 0.0
    for r in rows:
        S = sigfn(r)
        if not S:
            continue
        n += 1
        obs += r["md"] in S
        exp += sum(LORD_SHARE.get(p, 0.0) for p in S)
    er = exp / n if n else 0.0
    orr = obs / n if n else 0.0
    se = math.sqrt(n * er * (1 - er)) if n and 0 < er < 1 else 0.0
    z = (obs - exp) / se if se else 0.0
    return DashaResult(name, n, round(orr, 4), round(er, 4),
                       round(orr / er, 3) if er else 0.0, round(z, 2),
                       round(2.0 * _norm_sf(abs(z)), 8))


def probe_significators(con=None) -> list[DashaResult]:
    own = con is None
    con = con or open_catalog()
    try:
        rows = _sig_rows(con)
    finally:
        if own:
            con.close()
    out = [_test_significator(rows, fn, name) for name, fn in _SIG_BATTERY.items()]
    out.sort(key=lambda r: r.lift, reverse=True)
    return out


def main() -> int:
    print("\n=== Doctrine-mining battery (death corpus) — gate: lift>1 & p<0.01 ===")
    print("\n-- Alternate dashas: is the active lord a maraka? --")
    print(f"{'technique':<46} {'lift':>6} {'p':>11}  {'n':>6}")
    for r in run():
        flag = "  <==PASS" if (r.lift > 1 and r.p_value < 0.01) else ""
        print(f"{r.name:<46} {r.lift:>6} {r.p_value:>11.3g}  {r.n:>6}{flag}")
    print("\n-- Significators vs Vimshottari MD (which death-lord is strongest?) --")
    print(f"{'significator':<46} {'lift':>6} {'p':>11}  {'n':>6}")
    for r in probe_significators():
        flag = "  <==PASS" if (r.lift > 1 and r.p_value < 0.01) else ""
        print(f"{r.name:<46} {r.lift:>6} {r.p_value:>11.3g}  {r.n:>6}{flag}")
    print("\nNote: stronger INDIVIDUAL significators (Karakāṁśa/Sun maraka > Lagna maraka)")
    print("do NOT raise held-out composite capture@10% past ~0.22 — the signal is")
    print("correlated and has hit a ceiling. See docs/death_timing.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
