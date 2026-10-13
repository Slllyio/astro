"""Phase 3: risk-set dasha-activation timing, exactly per docs/validation/PHASE3_TIMING_PREREG.md (08058ff6).

For every mapped event (person i, age a, house set H): 10 controls of the same tier and birth decade,
alive and observable at age a, each scored on THEIR OWN chart at age a. Exposure comes from the
map-agnostic activation store (tools/validation/activation_store.py).

  P1  AD level, day-precision events: an (MD, AD) period of tier >= 3 for H (death: t_mk >= 3)
  P2  MD level, other events at mid-year: the MD lord influences H (death: is a primary maraka)
  E = mean over events of [x_case - mean(x_controls)], person-clustered bootstrap CI, SESOI 0.03.

Order enforced in code (sham before real): (1) within-set label permutation sham, (2) placebo dasha,
(3) planted recovery; any sham failure stops the run before the real exposure is compared.

Usage:
    py -3.12 -m tools.validation.riskset_timing --derived E:/astro/data/astro_databank/derived --store E:/astro/data/validation/activation_lahiri_AB.parquet --store-raman E:/astro/data/validation/activation_raman_AB.parquet --out docs/validation/PHASE3_RESULTS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from tools.validation.result import Result, emit
from tools.validation.stats import cluster_bootstrap, mde80

PREREG = "PHASE3_TIMING_PREREG@08058ff6"
SESOI = 0.03
K_CONTROLS = 10
SEED = 20261014
CUTOFF_YEAR = 2024
AGE_MIN, AGE_MAX = 5.0, 95.0
_YEAR = 365.2425
MARAKA = "maraka"
_MONTHS = r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b"

#: (pattern on normalised "root subtype", houses). Ordered: first match wins. Positive list only;
#: anything unmatched is excluded (PHASE3_TIMING_PREREG "Event -> house map").
EVENT_MAP: tuple[tuple[str, tuple[int, ...] | str], ...] = (
    (r"^death of mate", (7,)), (r"^death of father", (9,)), (r"^death of mother", (4,)),
    (r"^death of child", (5,)), (r"^death of sibling", (3,)),
    (r"^death of", ()),                                           # significant person etc: excluded
    (r"^death and came back", ()),
    (r"^death( by|,|$| (disease|unspecified|accident|suicide)$)", MARAKA),   # + legacy rows (audit B1)
    (r"parents divorced", ()),
    (r"\bmarriage\b|divorce|begin significant relationship|end significant relationship", (7,)),
    (r"adopted a child|conception|abortion/ miscarriage", (5,)),
    (r"new job|new career|fired/laid off/quit|retired|\bprize\b|gain social status"
     r"|published/ exhibited/ released|begin major project|^career\b", (10,)),
    (r"acute illness|chronic illness|medical diagnosis|medical procedure|^health negative", (6,)),
    (r"accident \(non-fatal\)|violent trauma|^accidents\b", (6,)),
    (r"trial dates|law suit|^legal\b", (6,)),
    (r"\barrest\b", (12,)),
    (r"^education\b", (4,)),
    (r"inherited money", (8,)),
    (r"gain significant money|lose significant money|^finance\b|^business\b", (2, 11)),
)


def map_event(root: str, subtype: str | None) -> tuple[int, ...] | str | None:
    """House set for an event, MARAKA for own death, or None if excluded/unmapped."""
    text = re.sub(_MONTHS, "", f"{root} {subtype or ''}".lower())
    text = re.sub(r"\s+", " ", text).strip()
    for pat, houses in EVENT_MAP:
        if re.search(pat, text):
            return houses or None
    return None


def family(houses) -> str:
    if houses == MARAKA:
        return "own_death"
    return {(7,): "relationship", (10,): "career", (6,): "health_legal"}.get(tuple(houses), "other")


def _jd(y: int, m: int, d: int) -> float:
    return swe.julday(int(y), max(1, int(m)), max(1, int(d)), 12.0, swe.GREG_CAL)


class Store:
    """person_id -> (starts, ends, tier matrix [t1..t12, t_mk], conj) per variant, age-sorted."""

    def __init__(self, path: Path):
        df = pd.read_parquet(path)
        cols = [*(f"t{h}" for h in range(1, 13)), "t_mk"]
        self.data: dict[str, dict[str, tuple]] = {}
        for (pid, var), g in df.sort_values("start_age").groupby(["person_id", "variant"], sort=False):
            self.data.setdefault(pid, {})[var] = (g.start_age.to_numpy(), g.end_age.to_numpy(),
                                                  g[cols].to_numpy(), g.conj.to_numpy())

    def tier(self, pid: str, age: float, houses, variant: str = "real", conj_only: bool = False) -> int:
        """Max activation tier over the house set at `age` (-1 if no period covers it)."""
        rec = self.data.get(pid, {}).get(variant)
        if rec is None:
            return -1
        s, e, t, c = rec
        i = int(np.searchsorted(s, age, side="right")) - 1
        if i < 0 or age >= e[i]:
            return -1
        cols = [12] if houses == MARAKA else [h - 1 for h in houses]
        best = int(t[i, cols].max())
        if conj_only and best == 4 and not c[i]:
            best = 3
        return best


def exposed(tier: int, level: str) -> bool:
    return tier >= 3 if level == "AD" else tier in (1, 3, 4)


def build_sets(events: pd.DataFrame, master: pd.DataFrame, death_age: dict[str, float],
               in_store: set[str], rng) -> list[dict]:
    """Risk sets: same tier and birth decade, observable and alive at age a, != case."""
    pool = master[master.person_id.isin(in_store)]
    groups = {k: (g.person_id.to_numpy(), g.birth_year.to_numpy(),
                  np.array([death_age.get(p, np.inf) for p in g.person_id]))
              for k, g in pool.groupby(["quality_tier", "decade"])}
    sets = []
    for ev in events.itertuples():
        ids, by, da = groups.get((ev.quality_tier, ev.decade), (np.array([]),) * 3)
        ok = (ids != ev.person_id) & (by + ev.age <= CUTOFF_YEAR) & (da > ev.age)
        cand = ids[ok]
        if len(cand) < K_CONTROLS:
            continue
        sets.append(dict(case=ev.person_id, age=ev.age, houses=ev.houses, level=ev.level,
                         family=family(ev.houses), rodden=ev.rodden, event_jd=ev.event_jd,
                         controls=rng.choice(cand, K_CONTROLS, replace=False)))
    return sets


def score(sets: list[dict], store: Store, *, variant: str = "real", conj_only: bool = False,
          tier_fn=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(x_case, x_controls[n,K], tiers[n,K+1]) for every set."""
    xc, xk, tt = [], [], []
    for s in sets:
        members = [s["case"], *s["controls"]]
        tiers = [store.tier(p, s["age"], s["houses"], variant, conj_only) for p in members]
        if tier_fn is not None:
            tiers = tier_fn(s, members, tiers)
        x = [exposed(t, s["level"]) for t in tiers]
        xc.append(x[0]); xk.append(x[1:]); tt.append(tiers)
    return np.array(xc, float), np.array(xk, float), np.array(tt, int)


def excess(xc: np.ndarray, xk: np.ndarray, pids, rng) -> dict:
    d = xc - xk.mean(1)
    p = float(xk.mean())
    se0 = float(np.sqrt(p * (1 - p) * (1 + 1 / K_CONTROLS) / max(1, len(d))))
    lo, hi = cluster_bootstrap(d, np.asarray(pids), rng=rng)
    se = (hi - lo) / 3.919928
    return {"E": float(d.mean()), "ci": (lo, hi), "se": se, "se0": se0, "coverage": p,
            "n": int(len(d)), "n_people": int(len(set(pids))),
            "p": float(2 * (1 - __import__("scipy.stats").stats.norm.cdf(abs(d.mean()) / se))) if se > 0 else 1.0}


def clr_or(xc: np.ndarray, xk: np.ndarray) -> float | None:
    """Conditional-logistic OR (risk sets as strata) for a binary exposure."""
    from statsmodels.discrete.conditional_models import ConditionalLogit
    n, k = xk.shape
    y = np.r_[np.ones(n), np.zeros(n * k)]
    x = np.r_[xc, xk.ravel()]
    g = np.r_[np.arange(n), np.repeat(np.arange(n), k)]
    keep = np.isin(g, [i for i in range(n) if 0 < xc[i] + xk[i].sum() < k + 1])
    if keep.sum() == 0:
        return None
    try:
        res = ConditionalLogit(y[keep], x[keep][:, None], groups=g[keep]).fit(disp=0)
        return float(np.exp(res.params[0]))
    except Exception:  # noqa: BLE001 - reported as unavailable, never fatal
        return None


def clr_slope(tt: np.ndarray) -> tuple[float, float] | None:
    """S1: CLR log-odds slope per activation tier (0..4; uncovered ages dropped)."""
    from statsmodels.discrete.conditional_models import ConditionalLogit
    n, m = tt.shape
    y = np.tile(np.r_[1.0, np.zeros(m - 1)], n)
    x = tt.ravel().astype(float)
    g = np.repeat(np.arange(n), m)
    keep = x >= 0
    try:
        res = ConditionalLogit(y[keep], x[keep][:, None], groups=g[keep]).fit(disp=0)
        return float(res.params[0]), float(res.pvalues[0])
    except Exception:  # noqa: BLE001
        return None


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=ps.get)
    out, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * ps[k]))
        out[k] = run
    return out


def load_events(derived: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    R = derived / "raman"
    master = pd.read_parquet(R / "person_master.parquet")
    master = master[master.birth_date.str.match(r"^\d{4}-\d\d-\d\d$")].copy()
    master["birth_year"] = master.birth_date.str[:4].astype(int)
    master["decade"] = master.birth_year // 10 * 10
    master["birth_jd"] = [_jd(int(b[:4]), int(b[5:7]), int(b[8:10])) for b in master.birth_date]
    ev = pd.read_parquet(R / "person_events.parquet").merge(
        master[["person_id", "quality_tier", "decade", "birth_jd", "rodden_rating"]], on="person_id")
    ev = ev[ev.quality_tier.isin(["A", "B"])]
    ev["houses"] = [map_event(r, s) for r, s in zip(ev.event_root, ev.event_subtype)]
    ev = ev[ev.houses.notna()].copy()
    day = ev.date_precision == "day"
    ev["event_jd"] = np.where(day, [_jd(y, m, d) for y, m, d in zip(ev.event_year, ev.event_month, ev.event_day)],
                              [_jd(y, 7, 2) for y in ev.event_year])
    # own death: one event per person, the day-precision row preferred (audit B1, NB7)
    is_death = ev.houses.astype(str) == MARAKA
    deaths = ev[is_death].assign(_rank=(~day[is_death]).astype(int)).sort_values(["person_id", "_rank", "event_jd"])
    deaths = deaths.drop_duplicates("person_id").drop(columns="_rank")
    death_age = {r.person_id: (r.event_jd - r.birth_jd) / _YEAR for r in deaths.itertuples()}
    ev = pd.concat([ev[~is_death], deaths])
    n0 = len(ev)
    ev = ev.assign(_h=ev.houses.astype(str)).drop_duplicates(["person_id", "event_jd", "_h"]).drop(columns="_h")
    print(f"[phase3] dedup person x date x house: {n0} -> {len(ev)} events (audit B2)")
    day = ev.date_precision == "day"
    ev["age"] = (ev.event_jd - ev.birth_jd) / _YEAR
    ev["level"] = np.where(day, "AD", "MD")
    ev["rodden"] = ev.rodden_rating
    ev = ev[(ev.age >= AGE_MIN) & (ev.age <= AGE_MAX)]
    return ev, master, death_age


def double_transit_fn(derived: Path, sets: list[dict], workers: int):
    """S3: AND the P1 tier with 'transiting Jupiter and Saturn both bear on H or its lord'."""
    import multiprocessing as mp
    from tools.parashara.astrobank.transit_tests import _dt
    from tools.validation.reliability import install_ayanamsa_patch
    pids = sorted({p for s in sets for p in (s["case"], *s["controls"])})
    master = pd.read_parquet(derived / "raman" / "person_master.parquet").set_index("person_id")
    rows = [dict(master.loc[p, ["birth_date", "birth_time", "tz_offset", "latitude", "longitude"]], person_id=p)
            for p in pids]
    with mp.Pool(workers, initializer=install_ayanamsa_patch) as pool:
        natal = {r["person_id"]: r for r in pool.map(_natal_signs, rows, chunksize=200) if r}
    from app.parashara.primitives.relationships import SIGN_LORDS
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    def fn(s, members, tiers):
        out = []
        for p, t in zip(members, tiers):
            n = natal.get(p)
            if n is None or t < 3:
                out.append(min(t, 2) if t >= 0 else t)
                continue
            jd = n["birth_jd"] + s["age"] * _YEAR
            hit = False
            # death: DT on the 8th, per DOUBLE_TRANSIT_PREREG (the maraka leg is the dasha tier)
            for h in ((8,) if s["houses"] == MARAKA else s["houses"]):
                hs = (n["asc"] - 1 + h - 1) % 12 + 1
                hit |= _dt(jd, (hs, n["signs"][SIGN_LORDS[hs]]))
            out.append(t if hit else 2)
        return out
    return fn


def _natal_signs(row: dict) -> dict | None:
    try:
        from app.parashara.chart.cast import cast
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        ch = cast(year=y, month=mo, day=d, hour=int(t[:2]), minute=int(t[3:5]), tz_offset=float(row["tz_offset"]),
                  latitude=float(row["latitude"]), longitude=float(row["longitude"]))
        return {"person_id": row["person_id"], "asc": ch.asc_sign, "birth_jd": _jd(y, mo, d),
                "signs": {p: int(lon % 360 // 30) + 1 for p, lon in ch.longitudes.items()}}
    except Exception:  # noqa: BLE001
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--store", type=Path, required=True)
    ap.add_argument("--store-raman", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, default=Path("E:/astro/data/validation/phase3_results.json"))
    ap.add_argument("--sink", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(SEED)
    ev, master, death_age = load_events(a.derived)
    store = Store(a.store)
    n_ev = len(ev)
    ev = ev[ev.person_id.isin(store.data)]
    print(f"[phase3] cases in store: {len(ev)}/{n_ev} (audit NB5)")
    sets = build_sets(ev, master, death_age, set(store.data), rng)
    out: dict = {"n_mapped_events": int(len(ev)), "n_sets": len(sets)}
    by_level = {lvl: [s for s in sets if s["level"] == lvl] for lvl in ("AD", "MD")}
    pids = {lvl: [s["case"] for s in ss] for lvl, ss in by_level.items()}

    # ---- 1. sham first: case label permuted within each risk set ---------------------------------
    sham_ok = True
    for lvl, ss in by_level.items():
        xc, xk, _ = score(ss, store)
        allx = np.c_[xc, xk]
        j = rng.integers(0, K_CONTROLS + 1, len(ss))
        sc = allx[np.arange(len(ss)), j]
        sk = np.array([np.delete(row, jj) for row, jj in zip(allx, j)])
        sh = excess(sc, sk, pids[lvl], rng)
        out[f"sham_{lvl}"] = sh
        sham_ok &= sh["ci"][0] <= 0 <= sh["ci"][1]
        # planted recovery: case exposure resampled at mean(controls) + SESOI
        pc = (rng.random(len(ss)) < np.clip(xk.mean(1) + SESOI, 0, 1)).astype(float)
        pl = excess(pc, xk, pids[lvl], rng)
        out[f"planted_{lvl}"] = pl | {"recovered": bool(pl["ci"][0] <= SESOI <= pl["ci"][1])}
    out["sham_ok"] = bool(sham_ok)
    planted_ok = all(out[f"planted_{lv}"]["recovered"] for lv in by_level)
    out["planted_ok"] = planted_ok
    if not sham_ok or not planted_ok:
        a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        raise SystemExit("[phase3] CONTROL FAILED (sham or planted) -- real exposure NOT compared")

    # ---- 2. placebo dasha, then real ----------------------------------------------------------
    results = {}
    for lvl, tag in (("AD", "P1"), ("MD", "P2")):
        ss = by_level[lvl]
        out[f"placebo_{tag}"] = excess(*score(ss, store, variant="placebo")[:2], pids[lvl], rng)
        xc, xk, tt = score(ss, store)
        r = excess(xc, xk, pids[lvl], rng) | {"clr_or": clr_or(xc, xk)}
        results[tag] = r
        out[tag] = r
        if lvl == "AD":
            s1 = clr_slope(tt)
            out["S1_slope"], out["S1_p"] = s1 if s1 else (None, None)
            out["S1_slope_conj_only"] = clr_slope(score(ss, store, conj_only=True)[2])
            fam = {}
            for f in sorted({s["family"] for s in ss}):
                idx = [i for i, s in enumerate(ss) if s["family"] == f]
                if len(idx) >= 30:
                    fam[f] = excess(xc[idx], xk[idx], [pids[lvl][i] for i in idx], rng)
            out["P1_by_family"] = fam
            for rr in ("AA", "A"):
                idx = [i for i, s in enumerate(ss) if s["rodden"] == rr]
                if idx:
                    out[f"P1_rodden_{rr}"] = excess(xc[idx], xk[idx], [pids[lvl][i] for i in idx], rng)
        # S2 specificity: target minus mean of non-target house instruments, same sets
        non = []
        for s in ss:
            tgt = set() if s["houses"] == MARAKA else set(s["houses"])   # death: vs all 12 houses
            non.append([h for h in range(1, 13) if h not in tgt])
        alt = []
        for h_off in range(12):
            alt_sets = [dict(s, houses=(nn[h_off],)) if h_off < len(nn) else None for s, nn in zip(ss, non)]
            idx = [i for i, x in enumerate(alt_sets) if x is not None]
            axc, axk, _ = score([alt_sets[i] for i in idx], store)
            d = np.full(len(ss), np.nan)
            d[idx] = axc - axk.mean(1)
            alt.append(d)
        spec = (xc - xk.mean(1)) - np.nanmean(np.vstack(alt), 0)
        lo, hi = cluster_bootstrap(spec, np.asarray(pids[lvl]), rng=rng)
        se2 = (hi - lo) / 3.919928
        from scipy.stats import norm
        out[f"S2_{tag}"] = {"E": float(spec.mean()), "ci": (lo, hi),
                            "p": float(2 * (1 - norm.cdf(abs(spec.mean()) / se2))) if se2 > 0 else 1.0}
        # Raman-ayanamsa sensitivity (same risk sets)
    raman = Store(a.store_raman)
    for lvl, tag in (("AD", "P1"), ("MD", "P2")):
        out[f"{tag}_raman_ayanamsa"] = excess(*score(by_level[lvl], raman)[:2], pids[lvl], rng)
    del raman
    # S3 double transit on P1 sets
    s3 = score(by_level["AD"], store, tier_fn=double_transit_fn(a.derived, by_level["AD"], a.workers))
    out["S3_double_transit"] = excess(s3[0], s3[1], pids["AD"], rng)

    # ---- 3. verdicts + Holm -------------------------------------------------------------------
    adj = holm({k: results[k]["p"] for k in results})
    for tag, r in results.items():
        res = Result(test_id=f"phase3:{tag}", prereg_id=PREREG, engine="parashara", statistic="hit_diff",
                     unit="event", effect=r["E"], se=r["se"], se0=r["se0"], sesoi=SESOI, n_cases=r["n"],
                     n_clusters=r["n_people"], sham_ok=sham_ok, n_controls=r["n"] * K_CONTROLS,
                     ci95_override=r["ci"], planted_recovered=out[f"planted_{'AD' if tag == 'P1' else 'MD'}"]["recovered"],
                     config={"holm_p": adj[tag], "coverage": r["coverage"], "clr_or": r["clr_or"]})
        r["verdict"] = res.verdict if adj[tag] < 0.05 or res.verdict != "SIGNAL" else "UNDERPOWERED (Holm)"
        r["holm_p"], r["mde80"], r["p_tost"] = adj[tag], mde80(r["se0"]), res.p_tost
        if a.sink:
            tmp = a.sink.with_suffix(".tmp")
            rec = emit(res, tmp)
            tmp.unlink()
            rec["verdict"] = r["verdict"]                 # Holm override applied (audit NB2)
            a.sink.parent.mkdir(parents=True, exist_ok=True)
            with a.sink.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")
    # secondaries: p-values + Holm within the three (audit NB3)
    sec = {"S1": out.get("S1_p"), "S2": out["S2_P1"].get("p"), "S3": out["S3_double_transit"]["p"]}
    out["secondary_holm"] = holm({k: v for k, v in sec.items() if v is not None})
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    a.out.write_text(markdown(out), encoding="utf-8")
    print(json.dumps({k: (v.get("E"), v.get("ci"), v.get("verdict")) for k, v in out.items()
                      if isinstance(v, dict) and "E" in v}, indent=1, default=str))
    return 0


def _row(name: str, r: dict) -> str:
    lo, hi = r["ci"]
    extra = f" | {r['n']} | {r.get('coverage', float('nan')):.2f}" if "n" in r else " | | "
    return f"| {name} | {r['E']:+.4f} | {lo:+.4f}..{hi:+.4f}{extra} |"


def markdown(o: dict) -> str:
    L = ["# Phase 3 results: risk-set dasha-activation timing", "",
         f"Per `docs/validation/PHASE3_TIMING_PREREG.md` ({PREREG}). Generated by `tools/validation/riskset_timing.py`.",
         f"Mapped events (A+B): {o['n_mapped_events']}; risk sets built: {o['n_sets']}. "
         f"Shams passed: **{o['sham_ok']}**.", "",
         "E = case exposure − mean of 10 matched controls' exposure (0 = no timing effect). SESOI 0.03.", "",
         "## Primaries", "", "| test | E | 95% CI | n | control coverage | CLR OR | MDE80 | Holm p | p_TOST | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for t in ("P1", "P2"):
        r = o[t]
        L.append(f"| {t} ({'AD level, day-dated' if t == 'P1' else 'MD level, year-dated'}) | {r['E']:+.4f} "
                 f"| {r['ci'][0]:+.4f}..{r['ci'][1]:+.4f} | {r['n']} | {r['coverage']:.2f} | "
                 f"{(r['clr_or'] or float('nan')):.3f} | {r['mde80']:.3f} | {r['holm_p']:.3f} | {r['p_tost']:.3f} | **{r['verdict']}** |")
    L += ["", "## Controls (computed before the real exposure)", "", "| arm | E | 95% CI | n | coverage |", "|---|---|---|---|---|"]
    for k in ("sham_AD", "sham_MD", "planted_AD", "planted_MD", "placebo_P1", "placebo_P2"):
        L.append(_row(k + (f" (recovered: {o[k]['recovered']})" if "recovered" in o[k] else ""), o[k]))
    L += ["", "## Secondaries and sensitivity arms (descriptive unless a primary is SIGNAL)", "",
          "| arm | E | 95% CI | n | coverage |", "|---|---|---|---|---|"]
    for k in ("S2_P1", "S2_P2", "S3_double_transit", "P1_raman_ayanamsa", "P2_raman_ayanamsa",
              "P1_rodden_AA", "P1_rodden_A"):
        if k in o:
            L.append(_row(k, o[k]))
    for f, r in o.get("P1_by_family", {}).items():
        L.append(_row(f"P1 family: {f}", r))
    L += ["", f"S1 dose-response (CLR log-odds per tier 0–4): {o.get('S1_slope')} (p {o.get('S1_p')}) · "
          f"conj-only: {o.get('S1_slope_conj_only')}",
          f"Secondary Holm-adjusted p (S1-S3): {o.get('secondary_holm')}",
          "S3 uses the 8th as the transit target for own death, per "
          "`tools/parashara/astrobank/DOUBLE_TRANSIT_PREREG.md` (cited by the Phase 3 prereg).",
          "Shams: the within-set permutation sham checks arithmetic only (its expectation is 0 by "
          "construction); the PLACEBO dasha is the informative control.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
