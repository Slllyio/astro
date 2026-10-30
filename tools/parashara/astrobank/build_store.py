"""Parashara feature store for the astrobank real-outcome validation (PARASHARA_PREREG.md).

Casts every chart in the Raman store's population (`store_population.parquet` — same 22,315 people)
ONCE with the PARASHARA engine (Lahiri), runs `synthesize(read(...))`, and persists only what the
pre-registered tests read:

  verdicts          person_id, house, verdict               (one verdict per house)
  ayurdaya          person_id, total_years                  (nisargayu_full)
  sig_windows       person_id, house, level, quality, jd_start, jd_end   (H7 only — the timing tests)
  maraka_windows    person_id, level, both, jd_start, jd_end

Window dates: age (years after birth) -> JD from birth-date NOON, the same birth_jd convention the
timing test uses. The engine-independent tables are read from `--raman-root`, never rebuilt.

Usage:
    py -3.12 -m tools.parashara.astrobank.build_store --raman-root E:/astro/data/astro_databank/derived/raman --out E:/astro/data/astro_databank/derived/parashara
    py -3.12 -m tools.parashara.astrobank.build_store ... --bench 200
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

_YEAR = 365.2425
_TABLES = ("verdicts", "ayurdaya", "sig_windows", "maraka_windows")
_TIMING_HOUSES = (7,)
_CHUNK = 500


def init_worker() -> None:
    import swisseph as swe
    swe.set_ephe_path(None)


def process_person(row: dict[str, Any]) -> dict[str, list[dict]] | None:
    try:
        return _process(row)
    except Exception:  # noqa: BLE001 - per-row failure -> None (counted, never fatal)
        return None


def _process(row: dict[str, Any]) -> dict[str, list[dict]]:
    import swisseph as swe
    from app.parashara.chart.cast import cast
    from app.parashara.reading import read
    from app.parashara.synthesis import synthesize
    from app.parashara.synthesis.activation import active_windows, influences
    from app.parashara.synthesis.chart_facts import planet_signs

    pid = row["person_id"]
    y, mo, d = (int(x) for x in row["birth_date"].split("-"))
    t = row["birth_time"]
    reading = read(cast(year=y, month=mo, day=d, hour=int(t[:2]), minute=int(t[3:5]),
                        tz_offset=float(row["tz_offset"]), latitude=float(row["latitude"]),
                        longitude=float(row["longitude"])))
    report = synthesize(reading)
    birth_jd = swe.julday(y, mo, d, 12.0, swe.GREG_CAL)

    def jd(age: float) -> float:
        return birth_jd + age * _YEAR

    verdicts = [{"person_id": pid, "house": h, "verdict": j.verdict}
                for h, j in report.houses.items()]
    ayur = [{"person_id": pid, "total_years": float(reading.nisargayu_full.total_years)}]

    chart = reading.chart
    signs = planet_signs(chart)
    vim = next(dr for dr in reading.dashas if dr.system == "vimshottari")
    sig: list[dict] = []
    for h in _TIMING_HOUSES:
        for w in active_windows(reading, (h,)):
            sig.append({"person_id": pid, "house": h, "level": "AD", "quality": w.quality,
                        "jd_start": jd(w.start_age), "jd_end": jd(w.end_age)})
        for p in vim.timeline:
            if p.end_year > 0 and influences(chart, p.lord, h, signs=signs):
                sig.append({"person_id": pid, "house": h, "level": "MD", "quality": "",
                            "jd_start": jd(max(0.0, p.start_year)), "jd_end": jd(p.end_year)})

    marakas = {m.planet for m in reading.maraka_planets}
    mar: list[dict] = []
    for maha, bhuktis in vim.bhuktis:
        for b in bhuktis:
            if b.end_year <= 0 or not (maha in marakas or b.lord in marakas):
                continue
            mar.append({"person_id": pid, "level": "AD",
                        "both": bool(maha in marakas and b.lord in marakas),
                        "jd_start": jd(max(0.0, b.start_year)), "jd_end": jd(b.end_year)})
    for p in vim.timeline:
        if p.end_year > 0 and p.lord in marakas:
            mar.append({"person_id": pid, "level": "MD", "both": True,
                        "jd_start": jd(max(0.0, p.start_year)), "jd_end": jd(p.end_year)})
    return {"verdicts": verdicts, "ayurdaya": ayur, "sig_windows": sig, "maraka_windows": mar}


def process_natal(row: dict[str, Any]) -> dict[str, Any] | None:
    """Natal facts for the double-transit test (DOUBLE_TRANSIT_PREREG.md): the 7th/8th house signs
    and their lords' signs (Parashara cast, Lahiri). Separate table so earlier results stay
    reproducible."""
    try:
        from app.parashara.chart.cast import cast
        from app.parashara.primitives.relationships import SIGN_LORDS
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        ch = cast(year=y, month=mo, day=d, hour=int(t[:2]), minute=int(t[3:5]),
                  tz_offset=float(row["tz_offset"]), latitude=float(row["latitude"]),
                  longitude=float(row["longitude"]))
        sign = {p: int(lon % 360.0 // 30) + 1 for p, lon in ch.longitudes.items()}
        out: dict[str, Any] = {"person_id": row["person_id"], "asc_sign": ch.asc_sign}
        for h in (7, 8):
            hs = ((ch.asc_sign - 1 + h - 1) % 12) + 1
            out[f"h{h}_sign"] = hs
            out[f"h{h}_lord_sign"] = sign[SIGN_LORDS[hs]]
        return out
    except Exception:  # noqa: BLE001
        return None


def run_natal(raman_root: Path, out: Path, workers: int, extension: bool = False) -> int:
    pop = pd.read_parquet(raman_root / "store_population.parquet")
    master = pd.read_parquet(raman_root / "person_master.parquet")
    people = _extension_people(raman_root) if extension else set(pop.person_id)
    rows = master[master.person_id.isin(people)][
        ["person_id", "birth_date", "birth_time", "tz_offset", "latitude", "longitude"]
    ].to_dict("records")
    (out / "parts").mkdir(parents=True, exist_ok=True)
    _guard_population(out / "parts", rows, extension=extension)
    with mp.Pool(processes=workers, initializer=init_worker) as pool:
        res = pool.map(process_natal, rows, chunksize=200)
    ok = [r for r in res if r is not None]
    pd.DataFrame(ok).to_parquet(out / "natal.parquet", compression="zstd", index=False)
    print(f"[natal] {len(ok)}/{len(rows)} charts -> natal.parquet")
    return 0


def _engine_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              cwd=".").stdout.strip()[:12]
    except Exception:  # noqa: BLE001
        return "unknown"


def _extension_people(raman_root: Path) -> set[str]:
    """DOUBLE_TRANSIT_PREREG_AMENDMENT_1: people (tiers A/B/C) with a DAY-precision marriage,
    divorce or own-death event who are NOT in the original store population."""
    import re
    ev = pd.read_parquet(raman_root / "person_events.parquet")
    ev = ev[ev.date_precision == "day"]
    low = (ev.event_root + " " + ev.event_subtype.fillna("")).str.lower()
    target = (low.str.contains("marriage|divorce", regex=True)
              | (low.str.match(r"^death") & ~low.str.contains("death of")))
    master = pd.read_parquet(raman_root / "person_master.parquet")
    tiered = set(master[master.quality_tier.isin(["A", "B", "C"])].person_id)
    pop = set(pd.read_parquet(raman_root / "store_population.parquet").person_id)
    _ = re  # pattern logic mirrors transit_tests.TESTS
    return (set(ev[target].person_id) & tiered) - pop


def _guard_population(parts: Path, rows: list[dict], *, extension: bool) -> None:
    """Chunk `.done` markers are positional: resuming into an --out built for a DIFFERENT
    population would silently skip chunks and then overwrite the store. Refuse instead."""
    import hashlib
    sha = hashlib.sha256("\n".join(sorted(r["person_id"] for r in rows)).encode()).hexdigest()
    marker = parts / "population_sha.txt"
    # an unmarked store predates this guard and is the primary population: only a
    # non-extension run may adopt it
    legacy = extension and not marker.exists() and (any(parts.glob("*.done")) or (parts.parent / "natal.parquet").exists())
    if legacy or (marker.exists() and marker.read_text(encoding="utf-8").strip() != sha):
        raise SystemExit(f"[store] {parts.parent} was built for a different (or unrecorded) "
                         f"population; use a fresh --out (refusing to resume/overwrite)")
    marker.write_text(sha, encoding="utf-8")


def run(raman_root: Path, out: Path, workers: int, bench: int | None,
        extension: bool = False) -> int:
    pop = pd.read_parquet(raman_root / "store_population.parquet")
    master = pd.read_parquet(raman_root / "person_master.parquet")
    people = _extension_people(raman_root) if extension else set(pop.person_id)
    sel = master[master.person_id.isin(people)]
    rows = sel[["person_id", "birth_date", "birth_time", "tz_offset",
                "latitude", "longitude"]].to_dict("records")
    label = "AMENDMENT_1 extension" if extension else "Raman store's population"
    print(f"[store] population: {len(rows)} charts ({label}, cast with Parashara)")

    if bench:
        init_worker()
        t0 = time.perf_counter()
        ok = sum(1 for r in rows[:bench] if process_person(r) is not None)
        per = (time.perf_counter() - t0) / max(1, min(bench, len(rows)))
        print(f"[bench] {ok}/{min(bench, len(rows))} ok  {per*1000:.0f} ms/chart  "
              f"-> full run ~{per*len(rows)/max(1, workers)/60:.1f} min on {workers} workers")
        return 0

    parts = out / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    _guard_population(parts, rows, extension=extension)
    chunks = [rows[i:i + _CHUNK] for i in range(0, len(rows), _CHUNK)]
    failures, t0 = 0, time.perf_counter()
    with mp.Pool(processes=workers, initializer=init_worker) as pool:
        for ci, chunk in enumerate(chunks):
            marker = parts / f"part_{ci:05d}.done"
            if marker.exists():
                continue
            results = pool.map(process_person, chunk)
            failures += sum(1 for r in results if r is None)
            tables: dict[str, list[dict]] = defaultdict(list)
            for r in results:
                if r is not None:
                    for name in _TABLES:
                        tables[name].extend(r[name])
            for name in _TABLES:
                if tables[name]:
                    pd.DataFrame(tables[name]).to_parquet(parts / f"{name}_{ci:05d}.parquet",
                                                          compression="zstd", index=False)
            marker.write_text("ok", encoding="utf-8")
            print(f"[store] chunk {ci+1}/{len(chunks)}  ({(time.perf_counter()-t0)/60:.1f} min)")
    for name in _TABLES:
        files = sorted(parts.glob(f"{name}_*.parquet"))
        if files:
            pd.concat([pd.read_parquet(f) for f in files], ignore_index=True).to_parquet(
                out / f"{name}.parquet", compression="zstd", index=False)
    manifest = {"n_selected": len(rows), "n_failures": failures, "engine_sha": _engine_sha(),
                "engine": "parashara (Lahiri)", "built": time.strftime("%Y-%m-%d %H:%M")}
    (out / "charts_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[store] DONE  failures={failures} ({failures/max(1, len(rows)):.2%})")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--raman-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=max(1, (mp.cpu_count() or 4) - 2))
    ap.add_argument("--bench", type=int, default=None)
    ap.add_argument("--natal-only", action="store_true",
                    help="write only natal.parquet (double-transit test inputs)")
    ap.add_argument("--extension", action="store_true",
                    help="cast DOUBLE_TRANSIT_PREREG_AMENDMENT_1's extension people (outside the "
                         "store population); requires a fresh --out")
    a = ap.parse_args(argv)
    if a.natal_only:
        return run_natal(a.raman_root, a.out, a.workers, extension=a.extension)
    return run(a.raman_root, a.out, a.workers, a.bench, extension=a.extension)


if __name__ == "__main__":
    raise SystemExit(main())
