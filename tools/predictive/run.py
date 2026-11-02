"""Runner for Phases 1 and 2 of the learned predictive test (docs/predictive/PREDICTIVE_PREREG_2026-11-02.md).

    python -m tools.predictive.run <stage> --cache <cache dir> --out <results dir> [--derived ...] [--gauq ...]

Stages: gauquelin, plants_A, plants_B, phase2_B, phase2_A. Every null run is appended to
<out>/<stage>_runs.jsonl as it finishes, so a stopped job resumes where it left off.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe
from sklearn.metrics import roc_auc_score

from tools.predictive import evaluate as E
from tools.predictive import features as F

AREA_OF_ETYPE = {"(7,)": "marriage", "(10,)": "career", "(6,)": "health", "(5,)": "children",
                 "(4,)": "parents", "(9,)": "parents"}


# ----------------------------------------------------------------------------- helpers

def _runs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def _append(path: Path, rec: dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")


def _todo(path: Path, n: int, a) -> list[int]:
    done = {r["run"] for r in _runs(path)}
    return [i for i in range(n) if i not in done and i % a.nshards == a.shard]


def random_time_jd(people: pd.DataFrame, rng) -> np.ndarray:
    """Null N1: a uniform random clock time on the real local birth date."""
    day0 = np.array([swe.julday(y, m, d, 0.0 - tz, swe.GREG_CAL)
                     for y, m, d, tz in zip(people.year, people.month, people.day, people.tz_offset)])
    return day0 + rng.random(len(people))


def n2_perm(people: pd.DataFrame, rng) -> tuple[np.ndarray, float]:
    """Null N2: permutation of rows within (birth year, half-month, latitude band) strata."""
    perm = np.arange(len(people))
    keys = people.year.astype(str) + "|" + people.half_month.astype(str) + "|" + people.lat_band
    alone = 0
    for _, idx in pd.Series(np.arange(len(people))).groupby(keys.to_numpy()):
        ix = idx.to_numpy()
        if len(ix) == 1:
            alone += 1
        perm[ix] = rng.permutation(ix)
    return perm, alone / len(people)


# ----------------------------------------------------------------------------- Task A machinery

class TaskA:
    def __init__(self, base: pd.DataFrame, Y: pd.DataFrame, areas: dict[str, str], tiers: np.ndarray):
        self.base = base.to_numpy(float)
        self.Y = Y
        self.areas = areas
        self.tiers = tiers
        self.cache = {}
        for t in Y.columns:
            ok = (Y[t] >= 0).to_numpy()
            y = Y[t].to_numpy()[ok]
            folds = E.folds_A(y)
            pb = E.oof(self.base[ok], y, folds)
            self.cache[t] = (ok, y, folds, pb, roc_auc_score(y, pb))

    def stats(self, astro: np.ndarray, fams: dict[str, np.ndarray], keep_oof: bool = False) -> dict:
        out = {"targets": {}}
        oofs = {}
        for t, (ok, y, folds, pb, ab) in self.cache.items():
            X = np.hstack([self.base[ok], astro[ok]])
            pf = E.oof(X, y, folds)
            rec = {"auc_base": ab, "auc_full": roc_auc_score(y, pf), "fam": {}}
            for f, cols in fams.items():
                Xf = np.hstack([self.base[ok], astro[ok][:, cols]])
                rec["fam"][f] = roc_auc_score(y, E.oof(Xf, y, folds))
            tier = self.tiers[ok]
            for tv in ("A", "B"):
                m = tier == tv
                if y[m].min() != y[m].max():
                    rec[f"d_full_tier{tv}"] = roc_auc_score(y[m], pf[m]) - roc_auc_score(y[m], pb[m])
            out["targets"][t] = rec
            if keep_oof:
                oofs[t] = pf
        return summarise_A(out, self.areas), oofs


def summarise_A(out: dict, areas: dict[str, str]) -> dict:
    T = out["targets"]
    fams = next(iter(T.values()))["fam"].keys()

    def block(names):
        d_full = float(np.mean([T[t]["auc_full"] - T[t]["auc_base"] for t in names]))
        d_fam = {f: float(np.mean([T[t]["fam"][f] - T[t]["auc_base"] for t in names])) for f in fams}
        best = max(d_fam, key=d_fam.get)
        return {"d_full": d_full, "scan": d_fam[best], "scan_family": best, "d_fam": d_fam}

    out["pooled"] = block(list(T))
    out["areas"] = {a: block([t for t in T if areas[t] == a]) for a in sorted(set(areas.values()))}
    return out


# ----------------------------------------------------------------------------- Task B machinery

class TaskB:
    def __init__(self, B: pd.DataFrame, tiers: dict[str, str]):
        self.B = B.reset_index(drop=True)
        self.etype_code = pd.factorize(self.B.etype)[0]
        self.base_cols = ["bt_age", "bt_year", "bt_doy_sin", "bt_doy_cos"]
        self.astro_cols = [c for c in self.B.columns if c[:2] in ("x_", "k_", "s_")]
        self.fams = F.timing_families(self.astro_cols)
        self.groups = self.B.person_id.to_numpy()
        self.folds = E.folds_B(self.groups)
        self.set_ids = np.sort(self.B.set_id.unique())
        first = self.B.drop_duplicates("set_id").set_index("set_id").sort_index()
        self.set_area = first.etype.map(AREA_OF_ETYPE).fillna("other").to_numpy()
        self.set_tier = first.person_id.map(tiers).to_numpy()
        self.set_person = first.person_id.to_numpy()

    def X(self, cols, astro: pd.DataFrame | None = None):
        src = self.B if astro is None else astro
        base = np.column_stack([self.B[self.base_cols].to_numpy(float), self.etype_code])
        return base if not cols else np.hstack([base, src[cols].to_numpy(float)])

    def stats(self, case: np.ndarray, astro: pd.DataFrame | None = None) -> dict:
        sid = self.B.set_id.to_numpy()
        cb = E.concordance(E.oof(self.X([]), case, self.folds), case, sid)
        cf = E.concordance(E.oof(self.X(self.astro_cols, astro), case, self.folds), case, sid)
        fam = {f: E.concordance(E.oof(self.X(c, astro), case, self.folds), case, sid) for f, c in self.fams.items()}

        def block(m):
            d_fam = {f: float(np.mean(v[m] - cb[m])) for f, v in fam.items()}
            best = max(d_fam, key=d_fam.get)
            return {"n_sets": int(m.sum()), "conc_base": float(cb[m].mean()), "conc_full": float(cf[m].mean()),
                    "d_full": float(np.mean(cf[m] - cb[m])), "scan": d_fam[best], "scan_family": best,
                    "d_fam": d_fam}

        allm = np.ones(len(cb), bool)
        out = {"pooled": block(allm),
               "areas": {a: block(self.set_area == a) for a in sorted(set(self.set_area))},
               "tiers": {t: block(self.set_tier == t) for t in ("A", "B")}}
        out["_per_set"] = (cf - cb).tolist()
        return out


def permute_within_sets(B: pd.DataFrame, rng, weight: np.ndarray | None = None) -> np.ndarray:
    case = np.zeros(len(B), int)
    for _, ix in B.groupby("set_id").indices.items():
        w = None if weight is None else weight[ix] / weight[ix].sum()
        case[rng.choice(ix, p=w)] = 1
    return case


# ----------------------------------------------------------------------------- stages

def p_value(obs: float, null: list[float]) -> float:
    return (1 + sum(v >= obs for v in null)) / (1 + len(null))


def stage_gauquelin(a) -> dict:
    from app.empirical.tournament.holdout import assign_holdout
    g = pd.read_parquet(a.gauq)
    hold = assign_holdout(g.person_id, salt="gauquelin-screening-v1")
    ovl = set(pd.read_csv(a.overlap).person_id_gauq)
    g = g[~g.person_id.isin(hold) & ~g.person_id.isin(ovl) & ~g.needs_geocoding
          & g.birth_date.str.match(r"^\d{4}-\d\d-\d\d$") & g.tz_offset_hours.notna()
          & g.latitude.notna() & g.longitude.notna()].copy()
    ymd = g.birth_date.str.split("-", expand=True).astype(int)
    g["year"], g["month"], g["day"] = ymd[0], ymd[1], ymd[2]
    g["tz_offset"] = g.tz_offset_hours
    g["jd_ut"] = [swe.julday(y, m, d, h + mi / 60 + s / 3600 - tz, swe.GREG_CAL) for y, m, d, h, mi, s, tz in
                  zip(g.year, g.month, g.day, g.hour_local_std, g.minute, g.second.fillna(0), g.tz_offset)]
    g["doy"] = pd.to_datetime(g.birth_date).dt.dayofyear
    g = g.set_index("person_id", drop=False)
    y = (g.profession == "sports_champion").astype(int).to_numpy()
    ang = 2 * np.pi * g.doy.to_numpy() / 365.25
    base = np.column_stack([g.year, np.sin(ang), np.cos(ang), g.latitude, g.longitude]).astype(float)
    folds = E.folds_A(y)
    pb = E.oof(base, y, folds)
    ab = roc_auc_score(y, pb)

    def stat(G: pd.DataFrame) -> dict:
        fams = {k: [G.columns.get_loc(c) for c in v] for k, v in F.natal_families(G.columns).items()}
        A = G.to_numpy(float)
        full = roc_auc_score(y, E.oof(np.hstack([base, A]), y, folds)) - ab
        fd = {f: roc_auc_score(y, E.oof(np.hstack([base, A[:, c]]), y, folds)) - ab for f, c in fams.items()}
        best = max(fd, key=fd.get)
        return {"d_full": full, "scan": fd[best], "scan_family": best, "d_fam": fd}

    runs_path = a.out / "gauquelin_runs.jsonl"
    rng = np.random.default_rng(E.SEED + 1)
    done = _runs(runs_path)
    for i in range(len(done), a.n1 if a.n1 else 50):
        rng_i = np.random.default_rng([E.SEED, 1, i])
        r = stat(F.natal_G(g, random_time_jd(g, rng_i))[0])
        _append(runs_path, {"run": i, **r})
        print(f"[gauquelin] N1 run {i}: full {r['d_full']:+.4f} scan {r['scan']:+.4f}", flush=True)
    if a.runs_only:
        return {}
    obs = stat(F.natal_G(g)[0])
    null = _runs(runs_path)
    res = {"n": int(len(y)), "n_sports": int(y.sum()), "auc_base": ab, "observed": obs,
           "p_full": p_value(obs["d_full"], [r["d_full"] for r in null]),
           "p_scan": p_value(obs["scan"], [r["scan"] for r in null]),
           "null_mean_full": float(np.mean([r["d_full"] for r in null])),
           "null_mean_scan": float(np.mean([r["scan"] for r in null])), "n_null": len(null)}
    res["pass"] = bool(min(res["p_full"], res["p_scan"]) < 0.05)
    return res


def _load_A(cache: Path):
    p = pd.read_parquet(cache / "people.parquet")
    base = pd.read_parquet(cache / "base_A.parquet").loc[p.index]
    G = pd.read_parquet(cache / "G_A.parquet").loc[p.index]
    T = pd.read_parquet(cache / "T_A.parquet").loc[p.index]
    return p, base, G, T


def stage_plants_A(a) -> dict:
    p, base, G, _T = _load_A(a.cache)
    rng = np.random.default_rng([E.SEED, 2])
    conds = {"moon_nakshatra": G.g_Moon_nak.isin([0, 9, 18]).to_numpy(),
             "mars_venus_same_sign": (G.g_Mars_sign == G.g_Venus_sign).to_numpy()}
    astro = G.to_numpy(float)
    fams = {k: [G.columns.get_loc(c) for c in v] for k, v in F.natal_families(G.columns).items()}
    res = {}
    for name, c in conds.items():
        p0 = 0.10 / (1 + c.mean())                          # overall prevalence 10%, risk ratio 2.0
        labels = [(rng.random(len(c)) < p0 * (1 + c)).astype(int) for _ in range(5)]
        nulls_lab = [(rng.random(len(c)) < 0.10).astype(int) for _ in range(5)] if name == "moon_nakshatra" else []
        tA = TaskA(base, pd.DataFrame({"plant": labels[0]}, index=p.index), {"plant": "plant"},
                   p.quality_tier.to_numpy())
        runs_path = a.out / f"plants_A_{name}_runs.jsonl"
        for i in _todo(runs_path, 20, a):
            perm, _ = n2_perm(p, np.random.default_rng([E.SEED, 3, i]))
            s, _ = tA.stats(astro[perm], fams)
            _append(runs_path, {"run": i, "d_full": s["pooled"]["d_full"], "scan": s["pooled"]["scan"]})
            print(f"[plants_A {name}] null {i}", flush=True)
        if a.runs_only:
            continue
        null = _runs(runs_path)
        reps = []
        for k, lab in enumerate(labels + nulls_lab):
            tk = TaskA(base, pd.DataFrame({"plant": lab}, index=p.index), {"plant": "plant"},
                       p.quality_tier.to_numpy())
            s, _ = tk.stats(astro, fams)
            pf = p_value(s["pooled"]["d_full"], [r["d_full"] for r in null])
            ps = p_value(s["pooled"]["scan"], [r["scan"] for r in null])
            reps.append({"replicate": k, "kind": "plant" if k < 5 else "all_null",
                         "d_full": s["pooled"]["d_full"], "scan": s["pooled"]["scan"],
                         "scan_family": s["pooled"]["scan_family"], "p_full": pf, "p_scan": ps,
                         "detected": bool(min(pf, ps) < 0.05)})
            print(f"[plants_A {name}] rep {k}: {reps[-1]}", flush=True)
        res[name] = {"replicates": reps,
                     "detected": sum(r["detected"] for r in reps if r["kind"] == "plant"),
                     "all_null_detected": sum(r["detected"] for r in reps if r["kind"] == "all_null")}
    return res


def _load_B(cache: Path):
    p = pd.read_parquet(cache / "people.parquet")
    B = pd.read_parquet(cache / "sets_B.parquet")
    return p, B, TaskB(B, dict(zip(p.index, p.quality_tier)))


def stage_plants_B(a) -> dict:
    _p, B, tB = _load_B(a.cache)
    w = np.where(tB.B.x_Jupiter_from_moon.isin([1, 5, 9]), 3.0, 1.0)
    res = []
    for k in range(8):                                   # 0-4 plants, 5-7 all-null checks
        kind = "plant" if k < 5 else "all_null"
        lab = permute_within_sets(tB.B, np.random.default_rng([E.SEED, 4, k]), w if kind == "plant" else None)
        obs = tB.stats(lab)["pooled"]
        null = []
        for i in range(20):
            nl = permute_within_sets(tB.B, np.random.default_rng([E.SEED, 5, k, i]))
            s = tB.stats(nl)["pooled"]
            null.append(s)
        pf = p_value(obs["d_full"], [n["d_full"] for n in null])
        ps = p_value(obs["scan"], [n["scan"] for n in null])
        res.append({"replicate": k, "kind": kind, "d_full": obs["d_full"], "scan": obs["scan"],
                    "scan_family": obs["scan_family"], "p_full": pf, "p_scan": ps,
                    "detected": bool(min(pf, ps) < 0.05)})
        print(f"[plants_B] {res[-1]}", flush=True)
    return {"replicates": res, "detected": sum(r["detected"] for r in res if r["kind"] == "plant"),
            "all_null_detected": sum(r["detected"] for r in res if r["kind"] == "all_null")}


def _summ_null(obs: dict, null: list[dict], sesoi: float, key_list) -> dict:
    out = {}
    for key in key_list:
        nv = [n[key] for n in null]
        out[key] = {"observed": obs[key], "null_mean": float(np.mean(nv)), "null_sd": float(np.std(nv)),
                    "p": p_value(obs[key], nv), "mde80": float(2.8 * np.std(nv)),
                    "excess": obs[key] - float(np.mean(nv))}
    return out


def stage_phase2_B(a) -> dict:
    p, B, tB = _load_B(a.cache)
    case = tB.B.case.to_numpy()
    runs_path = a.out / "phase2_B_N3_runs.jsonl"
    for i in _todo(runs_path, 100, a):
        s = tB.stats(permute_within_sets(tB.B, np.random.default_rng([E.SEED, 7, i])))
        s.pop("_per_set")
        _append(runs_path, {"run": i, **s})
        print(f"[phase2_B] N3 run {i}: full {s['pooled']['d_full']:+.4f}", flush=True)
    if a.runs_only:
        return {}
    obs = tB.stats(case)
    per_set = np.array(obs.pop("_per_set"))
    lo, hi = E.boot_ci(per_set, tB.set_person, np.random.default_rng([E.SEED, 6]))
    null = _runs(runs_path)
    res = {"observed": obs, "ci95_d_full": [lo, hi], "n_null": len(null),
           "pooled": _summ_null(obs["pooled"], [n["pooled"] for n in null], 0.03, ("d_full", "scan")),
           "areas": {ar: _summ_null(obs["areas"][ar], [n["areas"][ar] for n in null], 0.03, ("d_full", "scan"))
                     for ar in obs["areas"]},
           "tiers": {t: _summ_null(obs["tiers"][t], [n["tiers"][t] for n in null], 0.03, ("d_full", "scan"))
                     for t in obs["tiers"]}}
    return res


def stage_phase2_A(a) -> dict:
    p, base, G, T = _load_A(a.cache)
    Y = pd.read_parquet(a.cache / "targets_A.parquet").loc[p.index]
    astro_df = pd.concat([G, T], axis=1)
    cols = list(astro_df.columns)
    fams = {k: [cols.index(c) for c in v] for k, v in F.natal_families(cols).items()}
    tA = TaskA(base, Y, F.AREA_OF_TARGET, p.quality_tier.to_numpy())
    runs_path = a.out / "phase2_A_N2_runs.jsonl"
    A = astro_df.to_numpy(float)
    for i in _todo(runs_path, 40, a):
        perm, alone = n2_perm(p, np.random.default_rng([E.SEED, 9, i]))
        s, _ = tA.stats(A[perm], fams)
        _append(runs_path, {"run": i, "alone_share": alone, "pooled": s["pooled"], "areas": s["areas"],
                            "targets": {t: v["auc_full"] - v["auc_base"] for t, v in s["targets"].items()}})
        print(f"[phase2_A] N2 run {i}: full {s['pooled']['d_full']:+.4f} scan {s['pooled']['scan']:+.4f}", flush=True)
    if a.runs_only:
        return {}
    obs, oofs = tA.stats(astro_df.to_numpy(float), fams, keep_oof=True)
    rng = np.random.default_rng([E.SEED, 8])
    for t, pf in oofs.items():
        ok, y, _f, pb, _ab = tA.cache[t]
        obs["targets"][t]["ci95_d_full"] = E.auc_boot_ci(y, pf, pb, rng, reps=500)
        obs["targets"][t]["n_pos"], obs["targets"][t]["n"] = int(y.sum()), int(len(y))
    (a.out / "phase2_A_observed.json").write_text(json.dumps(obs, indent=1))
    null = _runs(runs_path)
    res = {"observed": obs, "n_null": len(null), "alone_share": null[0]["alone_share"] if null else None,
           "pooled": _summ_null(obs["pooled"], [n["pooled"] for n in null], 0.02, ("d_full", "scan")),
           "areas": {ar: _summ_null(obs["areas"][ar], [n["areas"][ar] for n in null], 0.02, ("d_full", "scan"))
                     for ar in obs["areas"]}}
    return res


def stage_n1_B(a) -> dict:
    """Null N1 for Task B (secondary): same-day random birth times; store activation tiers kept."""
    from tools.predictive.build import timing_features
    p, B, tB = _load_B(a.cache)
    obs = json.loads((a.out / "phase2_B_results.json").read_text())["observed"]
    case = tB.B.case.to_numpy()
    sub = p.loc[tB.B.person_id.unique()]
    store_cols = [c for c in tB.B.columns if c.startswith("s_")]
    runs_path = a.out / "phase2_B_N1_runs.jsonl"
    for i in _todo(runs_path, 20, a):
        jd = random_time_jd(sub, np.random.default_rng([E.SEED, 10, i]))
        _G, pos = F.natal_G(sub, jd)
        _k, sig = F.kp_natal(sub, jd)
        rows = tB.B[["set_id", "person_id", "etype", "jd", "case"]]
        X = timing_features(rows, sub.assign(jd_ut=jd), pos, sig, None, None)
        X[store_cols] = tB.B[store_cols].to_numpy()
        s = tB.stats(case, X)
        s.pop("_per_set")
        _append(runs_path, {"run": i, **s})
        print(f"[n1_B] run {i}: full {s['pooled']['d_full']:+.4f}", flush=True)
    null = _runs(runs_path)
    return {"n_null": len(null), "pooled": _summ_null(obs["pooled"], [n["pooled"] for n in null], 0.03, ("d_full", "scan")),
            "areas": {ar: _summ_null(obs["areas"][ar], [n["areas"][ar] for n in null], 0.03, ("d_full", "scan"))
                      for ar in obs["areas"]}}


def stage_n1_A(a) -> dict:
    """Null N1 for Task A (secondary): G and KP recomputed at same-day random times; Raman/Parashara kept."""
    p, base, G, T = _load_A(a.cache)
    Y = pd.read_parquet(a.cache / "targets_A.parquet").loc[p.index]
    obs = json.loads((a.out / "phase2_A_observed.json").read_text())
    keep = [c for c in T.columns if not c.startswith("t_kp_")]
    tA = TaskA(base, Y, F.AREA_OF_TARGET, p.quality_tier.to_numpy())
    runs_path = a.out / "phase2_A_N1_runs.jsonl"
    for i in _todo(runs_path, 20, a):
        jd = random_time_jd(p, np.random.default_rng([E.SEED, 11, i]))
        Gr, _ = F.natal_G(p, jd)
        kp, _ = F.kp_natal(p, jd)
        astro_df = pd.concat([Gr, T[keep], kp.reindex(columns=[c for c in T.columns if c.startswith("t_kp_")],
                                                         fill_value=0)], axis=1)[list(G.columns) + list(T.columns)]
        cols = list(astro_df.columns)
        fams = {k: [cols.index(c) for c in v] for k, v in F.natal_families(cols).items()}
        s, _ = tA.stats(astro_df.fillna(0).to_numpy(float), fams)
        _append(runs_path, {"run": i, "pooled": s["pooled"], "areas": s["areas"]})
        print(f"[n1_A] run {i}: full {s['pooled']['d_full']:+.4f}", flush=True)
    null = _runs(runs_path)
    return {"n_null": len(null), "pooled": _summ_null(obs["pooled"], [n["pooled"] for n in null], 0.02, ("d_full", "scan")),
            "areas": {ar: _summ_null(obs["areas"][ar], [n["areas"][ar] for n in null], 0.02, ("d_full", "scan"))
                      for ar in obs["areas"]}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--gauq", type=Path)
    ap.add_argument("--overlap", type=Path)
    ap.add_argument("--n1", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--runs-only", action="store_true")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    fn = {"gauquelin": stage_gauquelin, "plants_A": stage_plants_A, "plants_B": stage_plants_B,
          "phase2_B": stage_phase2_B, "phase2_A": stage_phase2_A,
          "n1_B": stage_n1_B, "n1_A": stage_n1_A}[a.stage]
    res = fn(a)
    if a.runs_only:
        return 0
    res["seconds"] = round(time.time() - t0)
    (a.out / f"{a.stage}_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if k not in ("observed", "replicates")}, indent=1, default=float)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
