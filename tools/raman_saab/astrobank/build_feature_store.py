"""Stage 2 — the verdict feature store: cast every selected chart ONCE, persist everything.

Population: every labeled cohort member (all tiers, for sensitivity) UNION a stratified
corpus-control sample (celebrity tier A/B, stratified by birth-decade x latitude band). Chunked
(500 pids/part), resumable (existing parts skipped), multiprocessing with the raman worker.
Engine git sha stamped in the manifest — a later engine change invalidates the store loudly.

Usage:
    py -3.12 -m tools.raman_saab.astrobank.build_feature_store --bench 100   # cost model first
    py -3.12 -m tools.raman_saab.astrobank.build_feature_store [--workers N] [--control 8000]
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

import pandas as pd

from tools.raman_saab.astrobank._worker import init_worker, process_person

_OUT = Path("data/astro_databank/derived/raman")
_PARTS = _OUT / "charts_parts"
_TABLES = ("verdicts", "house_rollups", "ayurdaya", "dasha_timeline",
           "significator_windows", "maraka_windows")
_CHUNK = 500


def _engine_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, cwd=".").stdout.strip()[:12]
    except Exception:  # noqa: BLE001
        return "unknown"


def _population(control_n: int, seed: int = 20260724) -> pd.DataFrame:
    master = pd.read_parquet(_OUT / "person_master.parquet")
    labels = pd.read_parquet(_OUT / "labels.parquet")
    celeb = master[master.population == "celebrity_databank"].set_index("person_id")

    cohort_pids = set(labels.person_id) & set(celeb.index)
    pool = celeb[(~celeb.index.isin(cohort_pids)) & celeb.quality_tier.isin(["A", "B"])].copy()
    # stratified control: birth-decade x latitude band, proportional sample
    pool["decade"] = pool.birth_date.str[:3]
    pool["latband"] = pd.cut(pool.latitude, bins=[-90, 20, 45, 90], labels=["low", "mid", "high"])
    frac = min(1.0, control_n / max(1, len(pool)))
    control = (pool.groupby(["decade", "latband"], observed=True, group_keys=False)
               .apply(lambda g: g.sample(frac=frac, random_state=seed)))
    sel = celeb.loc[sorted(cohort_pids | set(control.index))].reset_index()
    sel["is_control"] = ~sel.person_id.isin(cohort_pids)
    return sel


def _rows_for_worker(df: pd.DataFrame) -> list[dict]:
    return df[["person_id", "birth_date", "birth_time", "tz_offset",
               "latitude", "longitude"]].to_dict("records")


def run(workers: int, control_n: int, bench: int | None) -> int:
    sel = _population(control_n)
    print(f"[store] population: {len(sel)} charts "
          f"({(~sel.is_control).sum()} cohort + {sel.is_control.sum()} control)")

    if bench:
        rows = _rows_for_worker(sel.head(bench))
        init_worker()
        t0 = time.perf_counter()
        ok = sum(1 for r in rows if process_person(r) is not None)
        dt = time.perf_counter() - t0
        per = dt / max(1, len(rows))
        est = per * len(sel) / max(1, workers) / 60
        print(f"[bench] {ok}/{len(rows)} ok  {per*1000:.0f} ms/person single-core  "
              f"-> full run ≈ {est:.0f} min on {workers} workers")
        return 0

    _PARTS.mkdir(parents=True, exist_ok=True)
    all_rows = _rows_for_worker(sel)
    chunks = [all_rows[i:i + _CHUNK] for i in range(0, len(all_rows), _CHUNK)]
    failures = 0
    t0 = time.perf_counter()
    with mp.Pool(processes=workers, initializer=init_worker) as pool:
        for ci, chunk in enumerate(chunks):
            marker = _PARTS / f"part_{ci:05d}.done"
            if marker.exists():
                continue
            results = pool.map(process_person, chunk)
            failures += sum(1 for r in results if r is None)
            tables: dict[str, list[dict]] = defaultdict(list)
            for r in results:
                if r is None:
                    continue
                for name in _TABLES:
                    tables[name].extend(r[name])
            for name in _TABLES:
                if tables[name]:
                    pd.DataFrame(tables[name]).to_parquet(
                        _PARTS / f"{name}_{ci:05d}.parquet", engine="pyarrow",
                        compression="zstd", index=False)
            marker.write_text("ok", encoding="utf-8")
            done = sum(1 for c in range(ci + 1) if (_PARTS / f"part_{c:05d}.done").exists())
            el = (time.perf_counter() - t0) / 60
            print(f"[store] chunk {ci+1}/{len(chunks)} done  ({done*_CHUNK} people, {el:.1f} min)")

    # compact parts into the six tables
    for name in _TABLES:
        parts = sorted(_PARTS.glob(f"{name}_*.parquet"))
        if parts:
            pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True).to_parquet(
                _OUT / f"{name}.parquet", engine="pyarrow", compression="zstd", index=False)
    sel[["person_id", "is_control", "quality_tier"]].to_parquet(
        _OUT / "store_population.parquet", engine="pyarrow", compression="zstd", index=False)
    manifest = {
        "n_selected": len(sel), "n_failures": failures, "chunks": len(chunks),
        "engine_sha": _engine_sha(),
        "person_master_rows": int(pd.read_parquet(_OUT / 'person_master.parquet').shape[0]),
        "built": time.strftime("%Y-%m-%d %H:%M"),
    }
    (_OUT / "charts_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[store] DONE  failures={failures} ({failures/max(1,len(sel)):.2%})  manifest written")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, (mp.cpu_count() or 4) - 2))
    ap.add_argument("--control", type=int, default=8000)
    ap.add_argument("--bench", type=int, default=None)
    a = ap.parse_args(argv)
    return run(a.workers, a.control, a.bench)


if __name__ == "__main__":
    raise SystemExit(main())
