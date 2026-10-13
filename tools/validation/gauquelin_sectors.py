"""Phase 4.1: Gauquelin Mars-sector positive control (docs/validation/PHASE4_1_GAUQUELIN_PREREG.md).

Mars's diurnal position in Gauquelin's 36 sectors (clockwise from rising), from hour angle H and the
semi-diurnal arc H0 = arccos(-tan(lat) tan(dec)); geometric horizon, no refraction. Expected rates by
Gauquelin's own shuffle: date, clock time and place re-combined from three random subjects of the group.

Usage:
    py -3.12 -m tools.validation.gauquelin_sectors --gauq E:/astro/data/empirical/gauquelin_persons.parquet --overlap E:/astro/data/empirical/gauquelin_dedup_review.csv --out docs/validation/PHASE4_1_RESULTS.md
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from app.empirical.tournament.holdout import assign_holdout

KEY = frozenset({36, 1, 2, 3, 9, 10, 11, 12})
SEED = 20261014
GROUPS = ("sports_champion", "painter", "writer", "actor")


def sector(hour_angle: float, dec: float, lat: float) -> int:
    """Gauquelin sector 1..36. hour_angle in degrees (0 = upper culmination, + westward)."""
    x = -math.tan(math.radians(lat)) * math.tan(math.radians(dec))
    h0 = 180.0 if x <= -1 else 0.0 if x >= 1 else math.degrees(math.acos(x))   # circumpolar / never rises
    h = (hour_angle + 180.0) % 360.0 - 180.0
    n0 = 180.0 - h0
    if -h0 <= h < 0:                 # rising -> upper culmination: 1..9
        base, f = 0, (h + h0) / h0
    elif 0 <= h < h0:                # upper culmination -> setting: 10..18
        base, f = 9, h / h0
    elif h >= h0:                    # setting -> lower culmination: 19..27
        base, f = 18, (h - h0) / n0 if n0 else 0.0
    else:                            # lower culmination -> rising: 28..36
        base, f = 27, (h + 180.0) / n0 if n0 else 0.0
    return base + min(8, int(f * 9)) + 1


def mars_sector(jd_ut: float, lat: float, lon: float) -> int:
    ra, dec = swe.calc_ut(jd_ut, swe.MARS, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0][:2]
    lst = swe.sidtime(jd_ut) * 15.0 + lon
    return sector(lst - ra, dec, lat)


def key_share(dates, hours, tzs, lats, lons) -> float:
    hits = 0
    for (y, m, d), hr, tz, la, lo in zip(dates, hours, tzs, lats, lons):
        hits += mars_sector(swe.julday(y, m, d, hr - tz, swe.GREG_CAL), la, lo) in KEY
    return hits / len(lats)


def expected(dates, hours, tzs, lats, lons, rng, n_shuffles: int) -> float:
    n = len(lats)
    out = []
    for _ in range(n_shuffles):
        i, j, k = rng.permutation(n), rng.permutation(n), rng.permutation(n)
        out.append(key_share([dates[x] for x in i], hours[j], tzs[k], lats[k], lons[k]))
    return float(np.mean(out))


def analyse(g: pd.DataFrame, rng, n_shuffles: int = 100, n_boot: int = 200) -> dict:
    dates = [tuple(int(v) for v in b.split("-")) for b in g.birth_date]
    hours = (g.hour_local_std + g.minute / 60 + g.second / 3600).to_numpy(float)
    tzs, lats, lons = (g.tz_offset_hours.to_numpy(float), g.latitude.to_numpy(float),
                       g.longitude.to_numpy(float))
    obs = key_share(dates, hours, tzs, lats, lons)
    exp = expected(dates, hours, tzs, lats, lons, rng, n_shuffles)
    boots = []
    n = len(g)
    for _ in range(n_boot):
        b = rng.integers(0, n, n)
        bd = [dates[x] for x in b]
        boots.append(key_share(bd, hours[b], tzs[b], lats[b], lons[b])
                     - expected(bd, hours[b], tzs[b], lats[b], lons[b], rng, 20))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": n, "observed": obs, "expected": exp, "excess_pts": 100 * (obs - exp),
            "ci_pts": (100 * lo, 100 * hi)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gauq", type=Path, required=True)
    ap.add_argument("--overlap", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    g = pd.read_parquet(a.gauq)
    hold = assign_holdout(g.person_id, salt="gauquelin-screening-v1")
    ovl = set(pd.read_csv(a.overlap).person_id_gauq)
    g = g[~g.person_id.isin(hold) & ~g.person_id.isin(ovl) & ~g.needs_geocoding
          & g.birth_date.str.match(r"^\d{4}-\d\d-\d\d$")]
    rng = np.random.default_rng(SEED)
    res = {grp: analyse(g[g.profession == grp], rng) for grp in GROUPS}
    L = ["# Phase 4.1 results: Gauquelin Mars-sector positive control", "",
         "Per `docs/validation/PHASE4_1_GAUQUELIN_PREREG.md`. Gauquelin holdout, AstroDatabank overlaps and "
         "un-geocoded rows excluded. Key sectors {36,1,2,3,9,10,11,12}; expected rate from 100 date/time/place shuffles.", "",
         "| group | n | observed key-sector share | expected (shuffle) | excess (pts) | 95% CI (pts) |",
         "|---|---|---|---|---|---|"]
    for grp, r in res.items():
        L.append(f"| {grp} | {r['n']} | {r['observed']:.4f} | {r['expected']:.4f} | {r['excess_pts']:+.2f} "
                 f"| {r['ci_pts'][0]:+.2f}..{r['ci_pts'][1]:+.2f} |")
    sp = res["sports_champion"]
    passed = sp["ci_pts"][0] > 0 and sp["excess_pts"] >= 2.0
    L += ["", f"**Positive control: {'PASS' if passed else 'FAIL'}** (pass bar: sports-champion CI excludes 0 and "
          f"excess >= +2.0 pts; Gauquelin printed about +4.5).", ""]
    a.out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
