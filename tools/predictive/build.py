"""Build and cache every feature table for the learned predictive test.

    python -m tools.predictive.build --derived <derived> --stores <validation dir> --out <cache dir>

Writes (cache dir): people.parquet, base_A.parquet, G_A.parquet, T_A.parquet, targets_A.parquet,
sets_B.parquet (case-crossover rows with all timing features). No outcome is compared with any
feature here. Tier C is never loaded (features.load_people drops it).
"""
from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from tools.predictive import features as F

K_CONTROLS = 10
CUTOFF_JD = 2460676.5          # 2025-01-01 00:00 UT: dates must fall on or before 2024-12-31
DOY_WINDOW = 15


def load_events(derived: Path, people: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Phase 3 loader (frozen map), day precision, own death excluded, dev people only."""
    from tools.validation.riskset_timing import MARAKA, load_events as p3
    ev, _master, death_age = p3(derived)
    ev = ev[ev.person_id.isin(people.index) & (ev.level == "AD")]
    ev = ev[ev.houses.astype(str) != MARAKA].copy()
    ev["etype"] = ev.houses.astype(str)
    return ev, death_age


def control_sets(ev: pd.DataFrame, people: pd.DataFrame, death_age: dict, rng) -> pd.DataFrame:
    """Case + K_CONTROLS same-person dates per event (prereg Task B)."""
    import swisseph as swe
    ages_by_type = {t: g[["person_id", "age"]].to_numpy() for t, g in ev.groupby("etype")}
    own = {(p, t): g.event_jd.to_numpy() for (p, t), g in ev.groupby(["person_id", "etype"])}
    rows, dropped = [], 0
    for set_id, e in enumerate(ev.itertuples()):
        bj = people.at[e.person_id, "jd_ut"]
        pool = ages_by_type[e.etype]
        pool = pool[pool[:, 0] != e.person_id, 1].astype(float)
        case_doy = pd.Timestamp(*swe.revjul(e.event_jd, swe.GREG_CAL)[:3]).dayofyear
        max_age = min(death_age.get(e.person_id, np.inf), (CUTOFF_JD - bj) / F.YEAR)
        same = own[(e.person_id, e.etype)]
        got = []
        for _ in range(400):
            if len(got) == K_CONTROLS or len(pool) == 0:
                break
            a = float(rng.choice(pool))
            y = int(swe.revjul(bj + a * F.YEAR, swe.GREG_CAL)[0])
            doy = case_doy + int(rng.integers(-DOY_WINDOW, DOY_WINDOW + 1))
            jd = swe.julday(y, 1, 1, 12.0) + (doy - 1)
            age = (jd - bj) / F.YEAR
            if age < 5 or age >= max_age or np.min(np.abs(same - jd)) <= 365:
                continue
            if any(abs(jd - g) < 1 for g in got):
                continue
            got.append(jd)
        if len(got) < K_CONTROLS:
            dropped += 1
            continue
        rows.append(dict(set_id=set_id, person_id=e.person_id, etype=e.etype, jd=e.event_jd, case=1))
        rows += [dict(set_id=set_id, person_id=e.person_id, etype=e.etype, jd=j, case=0) for j in got]
    print(f"[sets] {len(ev)} events, {dropped} dropped (fewer than {K_CONTROLS} eligible control dates)")
    return pd.DataFrame(rows)


def timing_features(rows: pd.DataFrame, people: pd.DataFrame, pos: dict, sig: dict,
                    store_par: F.StoreLookup | None, store_ram: F.StoreLookup | None) -> pd.DataFrame:
    import swisseph as swe
    out = []
    for r in rows.itertuples():
        bj = people.at[r.person_id, "jd_ut"]
        age = (r.jd - bj) / F.YEAR
        y, m, d, _ = swe.revjul(r.jd, swe.GREG_CAL)
        doy = pd.Timestamp(y, m, d).dayofyear
        x = {"bt_age": age, "bt_year": y, "bt_doy_sin": np.sin(2 * np.pi * doy / 365.25),
             "bt_doy_cos": np.cos(2 * np.pi * doy / 365.25)}
        x.update(F.transit_G_row(pos[r.person_id], bj, r.jd))
        x.update(F.kp_dasa_row(sig.get(r.person_id), r.jd))
        if store_par is not None:
            x.update(store_par.row(r.person_id, age, "s_par_"))
        if store_ram is not None:
            x.update(store_ram.row(r.person_id, age, "s_ram_"))
        out.append(x)
    return pd.DataFrame(out, index=rows.index)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--stores", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    p = F.load_people(a.derived)
    print(f"[people] {len(p)} development people (tiers A+B)")
    p.drop(columns=["tags", "categories_raw", "name_display", "name_norm"]).to_parquet(a.out / "people.parquet")
    F.baseline_natal(p).to_parquet(a.out / "base_A.parquet")
    F.targets(p).to_parquet(a.out / "targets_A.parquet")
    G, pos = F.natal_G(p)
    G.to_parquet(a.out / "G_A.parquet")
    print(f"[G] {G.shape} {time.time() - t0:.0f}s")
    kp, sig = F.kp_natal(p)
    T = pd.concat([F.raman_rules(a.derived, p.index), F.parashara_verdicts(a.derived, p.index), kp], axis=1)
    T = T.fillna(0).astype(np.int8)
    T.to_parquet(a.out / "T_A.parquet")
    print(f"[T] {T.shape} {time.time() - t0:.0f}s")
    with open(a.out / "natal_pos.pkl", "wb") as f:
        pickle.dump(pos, f)

    ev, death_age = load_events(a.derived, p)
    rng = np.random.default_rng(F.SEED)
    rows = control_sets(ev, p, death_age, rng)
    sp = F.StoreLookup.load(a.stores / "activation_lahiri_AB.parquet", rows.person_id.unique())
    sr = F.StoreLookup.load(a.stores / "raman_activation_raman_AB.parquet", rows.person_id.unique())
    X = timing_features(rows, p, pos, sig, sp, sr)
    B = pd.concat([rows, X], axis=1)
    B.to_parquet(a.out / "sets_B.parquet")
    print(f"[B] {B.shape}, {B.set_id.nunique()} sets {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
