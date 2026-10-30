"""Phase 3R instrument store: activation tiers from the RAMAN ENGINE's own code (PHASE3R_RAMAN_TIMING_PREREG).

Same schema as tools/validation/activation_store.py, so riskset_timing.py runs on it unchanged:
  person_id, variant, md, ad, start_age, end_age, t1..t12, t_mk, conj
Per (MD, AD) period and house H, exactly as vimshottari.active_houses + detailed_report.graded_buckets:
  timers = timer_set(H) | timer_set(aux) for aux in _EVENT_AUX_HOUSES[H]
  tier   = bhukti_tier(md in timers, ad in timers, lords_associated(md, ad))
  t_mk   = the same over maraka_set(chart).primary  (or .all() with --maraka all)
Engine code is only CALLED. Placebo = the engine's own dasha construction seeded one nakshatra
ahead (Moon + 13deg20', same elapsed fraction).

Usage:
    py -3.12 -m tools.validation.raman_activation_store --derived E:/astro/data/astro_databank/derived --tiers A,B --ayanamsa raman --out E:/astro/data/validation/raman_activation_raman_AB.parquet
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from tools.validation.activation_store import COLUMNS

_YEAR = 365.2425
_TIER = {"par excellence": 4, "ordinary": 3, "limited": 2, "feeble": 1, None: 0}
NAK = 360.0 / 27.0


def timeline(chart, moon_shift: float = 0.0):
    """The engine's mahadasha_timeline, optionally with the Moon shifted (placebo). shift 0 == engine."""
    from app.raman_saab.primitives import vimshottari as vd
    if moon_shift == 0.0:
        return vd.mahadasha_timeline(chart)
    md = vd.calculate_vimshottari_mahadasha((chart.planets["Moon"].lon + moon_shift) % 360.0, chart.jd_ut)
    start = chart.jd_ut - md["time_elapsed_years"] * vd.DAYS_PER_VEDIC_YEAR
    out, cursor, acc, i = [], start, 0.0, 0
    seq = vd._sequence_from(md["mahadasha_lord"])
    while acc < 140.0:
        lord = seq[i % 9]
        yrs = vd._LORD_YEARS[lord]
        end = cursor + yrs * vd.DAYS_PER_VEDIC_YEAR
        out.append(vd.DashaPeriod(lord, None, cursor, end))
        cursor, acc, i = end, acc + yrs, i + 1
    return out


def periods(chart, birth_jd: float, maraka: str, moon_shift: float = 0.0) -> list[tuple]:
    from app.raman_saab.primitives import vimshottari as vd
    timers = []
    for h in range(1, 13):
        t = set(vd.timer_set(chart, h))
        for aux in vd._EVENT_AUX_HOUSES.get(h, ()):
            t |= vd.timer_set(chart, aux)
        timers.append(t)
    ms = vd.maraka_set(chart)
    mk = ms.primary if maraka == "primary" else ms.all()
    out = []
    for md in timeline(chart, moon_shift):
        for bh in vd.bhuktis(md):
            if bh.end_jd <= birth_jd:
                continue
            assoc = vd.lords_associated(chart, bh.maha, bh.antar)
            conj = chart.planets[bh.maha].rasi_house == chart.planets[bh.antar].rasi_house
            tiers = [_TIER[vd.bhukti_tier(bh.maha in t, bh.antar in t, assoc)] for t in timers]
            out.append((bh.maha, bh.antar, max(0.0, (bh.start_jd - birth_jd) / _YEAR),
                        (bh.end_jd - birth_jd) / _YEAR, *tiers,
                        _TIER[vd.bhukti_tier(bh.maha in mk, bh.antar in mk, assoc)], conj))
    return out


def process(task: tuple[dict[str, Any], str, str]) -> list[tuple] | None:
    row, ayanamsa, maraka = task
    try:
        import swisseph as swe
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.chart.model import BirthData
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        chart = cast_chart(BirthData(name=row["person_id"], year=y, month=mo, day=d, hour=int(t[:2]),
                                     minute=int(t[3:5]), tz_offset=float(row["tz_offset"]),
                                     latitude=float(row["latitude"]), longitude=float(row["longitude"])),
                           ayanamsa=ayanamsa)
        bjd = swe.julday(y, mo, d, 12.0, swe.GREG_CAL)       # same age anchor as riskset_timing
        pid = row["person_id"]
        return ([(pid, "real", *p) for p in periods(chart, bjd, maraka)]
                + [(pid, "placebo", *p) for p in periods(chart, bjd, maraka, moon_shift=NAK)])
    except Exception:  # noqa: BLE001 - per-row failure counted, never fatal
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--tiers", default="A,B")
    ap.add_argument("--ayanamsa", choices=("raman", "lahiri"), default="raman")
    ap.add_argument("--maraka", choices=("primary", "all"), default="primary")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    from tools.raman_saab.astrobank._worker import init_worker
    master = pd.read_parquet(a.derived / "raman" / "person_master.parquet")
    sel = master[master.quality_tier.isin(a.tiers.split(","))
                 & master.birth_time.str.match(r"^\d\d:\d\d") & master.birth_date.str.match(r"^\d{4}-\d\d-\d\d$")]
    rows = sel[["person_id", "birth_date", "birth_time", "tz_offset", "latitude", "longitude"]] \
        .dropna().to_dict("records")[: a.limit]
    t0, recs, fails = time.perf_counter(), [], 0
    with mp.Pool(a.workers, initializer=init_worker) as pool:
        for i, r in enumerate(pool.imap_unordered(process, [(x, a.ayanamsa, a.maraka) for x in rows], chunksize=40)):
            if r is None:
                fails += 1
            else:
                recs.extend(r)
            if i % 5000 == 0:
                print(f"[raman-activation] {i}/{len(rows)} ({(time.perf_counter()-t0)/60:.1f} min)")
    df = pd.DataFrame.from_records(recs, columns=COLUMNS)
    tcols = [*(f"t{h}" for h in range(1, 13)), "t_mk"]
    df[tcols] = df[tcols].astype(np.int8)
    df[["start_age", "end_age"]] = df[["start_age", "end_age"]].astype(np.float32)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(a.out, compression="zstd", index=False)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:12]
    a.out.with_suffix(".manifest.json").write_text(json.dumps({
        "engine": "raman_saab", "n_selected": len(rows), "n_failures": fails, "ayanamsa": a.ayanamsa,
        "maraka": a.maraka, "engine_sha": sha, "built": time.strftime("%Y-%m-%d %H:%M")}, indent=2), encoding="utf-8")
    print(f"[raman-activation] DONE {len(rows)-fails}/{len(rows)} people, {len(df)} rows -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
