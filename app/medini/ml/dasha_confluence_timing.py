"""Confluence timing — astrology judged the way a jyotishi actually predicts.

Finding 11 tested single factors (too strict → null); Finding 12 tested "ANY one
of a disjunctive set fires" (too permissive → hit-rate = chance). Neither is
practice. A real astrologer predicts the event in the period where **many
independent significators converge**, and grades confidence by **how many agree**.

So we score every Mahadasha–Antardasha period of a life by its **confluence** —
the number of independent classical condition-families that activate the domain —
and ask whether real events concentrate in the high-confluence periods.

Confluence families (each a distinct line of evidence; sum ∈ 0..6):
  F1  MD lord is a primary significator of the domain (house-lord / occupant /
      aspector / karaka of the domain house).
  F2  AD lord is a primary significator.
  F3  Navamsa (D9) corroboration — MD/AD lord is the navamsa dispositor of the
      house-lord, or is vargottama.
  F4  Universal karaka of the domain runs as MD or AD.
  F5  An activating lord is well-dignified (exalted/own/moolatrikona/friendly)
      and **not combust** — strength to deliver.
  F6  Sambandha — MD & AD lords are mutually related (naisargika friends, OR
      conjunct, OR in mutual aspect) and at least one activates the domain.

Degree-based factors (combustion, exact conjunction, moolatrikona) use recomputed
longitudes (`charts_lon.parquet`); everything degrades gracefully to whole-sign.

Two verdicts, both within-life so the chart is its own control:
  A  Dose-response — does the event rate per person-year rise with confluence,
     within a plausible age band (so it adds beyond "the period at the right age")?
  B  Within-person peak — does the actual event fall in a higher-confluence period
     than a duration-weighted random period of the same life? (percentile vs 0.5).

If both are flat, the convergence method itself carries no signal — a fair,
decisive null. If they rise, cross-inference has real graded skill.

Usage::

    python -m app.medini.ml.dasha_confluence_timing \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --k 2000
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from scipy.stats import chi2, spearmanr

from app.core.bhava_judge import _BHAVA_KARAKAS
from app.core.dignity import (
    SIGN_RULERS, dignity_state, is_moolatrikona, naisargika_relation,
)
from app.core.drishti_argala import aspects_from_planet
from app.medini.ml.dasha_classical_dictums import DICTUMS, _significator_set
from app.medini.ml.dasha_event_promise import _sign_in_house

logger = logging.getLogger(__name__)
_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
# combustion orbs (degrees from Sun), classical.
_COMBUST_ORB: Final[dict[str, float]] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0,
    "Venus": 10.0, "Saturn": 15.0,
}
_GOOD_DIGNITY: Final[frozenset[str]] = frozenset({"exalted", "own", "friendly"})
# domain → (event_class, primary house, age band for "candidate periods").
DOMAINS: Final[dict[str, tuple[int, tuple[int, int]]]] = {
    "marriage": (7, (16, 55)),
    "career": (10, (18, 72)),
    "death": (8, (30, 105)),
}


def _ang_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _safe_dignity(p: str, sign: int) -> str:
    try:
        return dignity_state(p, sign)
    except (KeyError, ValueError):
        return "unknown"


def _person_facts(crow: pd.Series, d9row, lonrow, domain: str) -> dict:
    cfg = DICTUMS[domain]
    asc = int(crow["asc_sign"])
    houses = {g: int(crow[f"{g.lower()}_house"]) for g in _GRAHAS
              if pd.notna(crow.get(f"{g.lower()}_house"))}
    signs = {g: int(crow[f"{g.lower()}_sign"]) for g in _GRAHAS
             if pd.notna(crow.get(f"{g.lower()}_sign"))}
    lons = ({g: float(lonrow[f"{g.lower()}_lon"]) for g in _GRAHAS}
            if lonrow is not None else {})

    # F1/F2 primary significators (no D9 here): reuse the dictum union sans d9.
    prim_cfg = {**cfg, "d9_disp": []}
    prim = _significator_set(crow, None, prim_cfg)

    # F3 D9 dispositors of the house-lord(s) + vargottama planets.
    d9_set: set[str] = set()
    if d9row is not None:
        for h in cfg["d9_disp"] or cfg["houses"][:1]:
            lord = SIGN_RULERS[_sign_in_house(h, asc)]
            d9s = d9row.get(f"{lord.lower()}_d9_sign")
            if pd.notna(d9s):
                d9_set.add(SIGN_RULERS[int(d9s)])
        d9_set |= {g for g in _GRAHAS                       # vargottama
                   if g in signs and pd.notna(d9row.get(f"{g.lower()}_d9_sign"))
                   and int(d9row[f"{g.lower()}_d9_sign"]) == signs[g]}

    # F4 karakas.
    karaka = set(cfg.get("extra", []))
    for h in cfg["karaka_houses"]:
        karaka.update(_BHAVA_KARAKAS.get(h, ()))

    # combustion + good dignity.
    combust = set()
    if lons:
        sun = lons.get("Sun")
        for g, orb in _COMBUST_ORB.items():
            if g in lons and sun is not None and _ang_sep(lons[g], sun) < orb:
                combust.add(g)
    good = set()
    for g in _GRAHAS:
        if g not in signs:
            continue
        dg = _safe_dignity(g, signs[g])
        mt = bool(lons) and g in lons and is_moolatrikona(g, lons[g])
        if (dg in _GOOD_DIGNITY or mt) and g not in combust:
            good.add(g)

    return {"houses": houses, "signs": signs, "lons": lons, "prim": prim,
            "d9": d9_set, "karaka": karaka, "combust": combust, "good": good}


def _sambandha(md: str, ad: str, f: dict) -> bool:
    if md == ad:
        return False
    # naisargika friendship (either direction)
    try:
        if "friend" in (naisargika_relation(md, ad), naisargika_relation(ad, md)):
            return True
    except (KeyError, ValueError):
        pass
    h = f["houses"]
    s = f["signs"]
    lons = f["lons"]
    # conjunction: same sign (tighten to <13° if longitudes present)
    if md in s and ad in s and s[md] == s[ad]:
        if not lons or (md in lons and ad in lons and _ang_sep(lons[md], lons[ad]) < 13):
            return True
    # mutual whole-sign aspect
    if md in h and ad in h:
        if (h[ad] in aspects_from_planet(md, h[md])
                and h[md] in aspects_from_planet(ad, h[ad])):
            return True
    return False


def _confluence(md: str, ad: str, f: dict) -> int:
    f1 = md in f["prim"]
    f2 = ad in f["prim"]
    f3 = md in f["d9"] or ad in f["d9"]
    f4 = md in f["karaka"] or ad in f["karaka"]
    activators = [l for l in (md, ad) if l in f["prim"]]
    f5 = any(a in f["good"] for a in activators)
    f6 = (f1 or f2) and _sambandha(md, ad, f)
    return int(f1) + int(f2) + int(f3) + int(f4) + int(f5) + int(f6)


def build_period_table(windows: pd.DataFrame, charts: pd.DataFrame,
                       d9: pd.DataFrame | None, lon: pd.DataFrame | None,
                       events: pd.DataFrame, domain: str) -> pd.DataFrame:
    cls, _, (lo, hi) = domain, *DOMAINS[domain]
    ev = events[events["event_class"].astype(str).str.lower() == domain]
    ev_count = ev.groupby(["person_id", "md_seq", "ad_seq"]).size()
    first_ev = (ev.sort_values("event_jd").groupby("person_id").head(1)
                .set_index("person_id")[["md_seq", "ad_seq"]])

    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    d9idx = d9.drop_duplicates("person_id").set_index("person_id") if d9 is not None else None
    lonidx = lon.drop_duplicates("person_id").set_index("person_id") if lon is not None else None
    birth = cidx["birth_jd_used"]

    rows = []
    for pid, wg in windows.groupby("person_id"):
        if pid not in cidx.index or pd.isna(birth.get(pid)):
            continue
        f = _person_facts(cidx.loc[pid],
                          d9idx.loc[pid] if (d9idx is not None and pid in d9idx.index) else None,
                          lonidx.loc[pid] if (lonidx is not None and pid in lonidx.index) else None,
                          domain)
        b = float(birth[pid])
        fe = (int(first_ev.loc[pid, "md_seq"]), int(first_ev.loc[pid, "ad_seq"])) \
            if pid in first_ev.index else None
        for w in wg.itertuples():
            age = (((w.start_jd + w.end_jd) / 2) - b) / 365.25
            rows.append({
                "person_id": pid, "md_seq": w.md_seq, "ad_seq": w.ad_seq,
                "conf": _confluence(str(w.md_lord), str(w.ad_lord), f),
                "dur": float(w.duration_days), "age": age,
                "n_event": int(ev_count.get((pid, w.md_seq, w.ad_seq), 0)),
                "is_first_event": fe is not None and (w.md_seq, w.ad_seq) == fe,
                "in_band": lo <= age <= hi,
            })
    return pd.DataFrame(rows)


def dose_response(tab: pd.DataFrame) -> dict:
    """Event rate per 1000 person-years by confluence level, within age band."""
    a = tab[tab["in_band"]].copy()
    if a.empty:
        return {}
    levels = sorted(a["conf"].unique())
    py_tot = a["dur"].sum() / 365.25
    ev_tot = a["n_event"].sum()
    rows, obs, exp = [], [], []
    for k in levels:
        g = a[a["conf"] == k]
        py = g["dur"].sum() / 365.25
        n = int(g["n_event"].sum())
        rows.append({"conf": int(k), "n_windows": len(g),
                     "person_years": round(py, 1), "events": n,
                     "rate_per_1k_yr": round(n / py * 1000, 2) if py else None})
        obs.append(n)
        exp.append(ev_tot * py / py_tot if py_tot else 0)
    obs, exp = np.array(obs, float), np.array(exp, float)
    mask = exp > 0
    chi = float(((obs[mask] - exp[mask]) ** 2 / exp[mask]).sum())
    p = float(chi2.sf(chi, df=mask.sum() - 1)) if mask.sum() > 1 else 1.0
    rates = [r["rate_per_1k_yr"] for r in rows if r["rate_per_1k_yr"] is not None]
    rho = float(spearmanr(levels[:len(rates)], rates).statistic) if len(rates) > 2 else float("nan")
    return {"curve": rows, "chi2": round(chi, 2), "chi2_p": p,
            "trend_rho": round(rho, 3), "overall_rate": round(ev_tot / py_tot * 1000, 2)}


def peak_test(tab: pd.DataFrame, *, k: int = 2000, seed: int = 0) -> dict:
    """Within-person duration-weighted percentile of the event window's conf."""
    a = tab[tab["in_band"]].copy()
    pcts, weights_by_person = [], []
    for pid, g in a.groupby("person_id"):
        ev = g[g["is_first_event"]]
        if ev.empty:
            continue
        c0 = float(ev["conf"].iloc[0])
        tot = g["dur"].sum()
        if tot <= 0:
            continue
        below = g.loc[g["conf"] < c0, "dur"].sum()
        equal = g.loc[g["conf"] == c0, "dur"].sum()
        pcts.append((below + 0.5 * equal) / tot)
        weights_by_person.append((g["conf"].to_numpy(), g["dur"].to_numpy() / tot))
    if not pcts:
        return {}
    obs = float(np.mean(pcts))
    rng = np.random.default_rng(seed)
    null = np.empty(k)
    for j in range(k):
        s = 0.0
        for confs, w in weights_by_person:
            c0 = rng.choice(confs, p=w)              # duration-weighted draw
            below = w[confs < c0].sum()
            equal = w[confs == c0].sum()
            s += below + 0.5 * equal
        null[j] = s / len(weights_by_person)
    nstd = float(null.std(ddof=1))
    return {"n_persons": len(pcts), "mean_percentile": round(obs, 4),
            "null_mean": round(float(null.mean()), 4), "null_std": round(nstd, 4),
            "z": round((obs - 0.5) / nstd, 2) if nstd else None,
            "p": round(float((null >= obs).sum() + 1) / (k + 1), 4)}


def build_report(results: dict, *, k: int) -> str:
    L = ["# Confluence timing — does cross-inference of many dictums concentrate events?",
         "", "Each Mahadasha–Antardasha period scored 0–6 by how many independent "
         "significator families converge on the domain. Tested within each life "
         f"(its own control). Peak-test permutation K={k}.", ""]
    for dom, res in results.items():
        dr, pk = res["dose"], res["peak"]
        L += [f"## {dom}", ""]
        if dr:
            L += [f"Dose-response (events per 1000 person-yrs, in age band; overall "
                  f"{dr['overall_rate']}):", "",
                  "| confluence | windows | person-yrs | events | rate |",
                  "|---:|---:|---:|---:|---:|"]
            for r in dr["curve"]:
                L.append(f"| {r['conf']} | {r['n_windows']} | {r['person_years']} | "
                         f"{r['events']} | **{r['rate_per_1k_yr']}** |")
            L.append(f"\nTrend ρ(conf,rate) = **{dr['trend_rho']}**; "
                     f"χ²={dr['chi2']} (p={dr['chi2_p']:.3g}).")
        if pk:
            verdict = ("events fall in **higher**-confluence periods than chance"
                       if pk["z"] and pk["z"] >= 2 else
                       "**no** concentration beyond chance" if pk["z"] is not None
                       and pk["z"] < 1 else "weak/ambiguous concentration")
            L += ["", f"Within-person peak: mean event-window percentile "
                  f"**{pk['mean_percentile']}** (null 0.50), z=**{pk['z']}**, "
                  f"p={pk['p']:.3g} → {verdict}. (n={pk['n_persons']})", ""]
    L += ["## Reading", "",
          "- A rising rate(conf) curve + percentile ≫ 0.50 ⇒ convergence of "
          "dictums genuinely concentrates events: cross-inference has graded skill.",
          "- A flat curve + percentile ≈ 0.50 ⇒ even the astrologer's actual "
          "method — stacking many agreeing indications — carries no timing signal "
          "beyond chance on this corpus.", ""]
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path, *, k: int = 2000, seed: int = 0) -> dict:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    windows = pd.read_parquet(data_dir / "dasha_windows.parquet")
    d9 = pd.read_parquet(data_dir / "charts_d9.parquet") if (data_dir / "charts_d9.parquet").exists() else None
    lon = pd.read_parquet(data_dir / "charts_lon.parquet") if (data_dir / "charts_lon.parquet").exists() else None

    results, curves = {}, []
    for dom in DOMAINS:
        tab = build_period_table(windows, charts, d9, lon, events, dom)
        dose = dose_response(tab)
        peak = peak_test(tab, k=k, seed=seed)
        results[dom] = {"dose": dose, "peak": peak}
        for r in dose.get("curve", []):
            curves.append({"domain": dom, **r})
        logger.info("%s: trend_rho=%s peak_z=%s peak_p=%s", dom,
                    dose.get("trend_rho"), peak.get("z"), peak.get("p"))

    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(curves).to_csv(out_dir / "confluence_dose_response.csv", index=False)
    (out_dir / "confluence_timing.md").write_text(
        build_report(results, k=k), encoding="utf-8")
    (out_dir / "confluence_timing.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("--k", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    res = run(args.data_dir, args.out, k=args.k, seed=args.seed)
    print({d: {"trend_rho": r["dose"].get("trend_rho"),
               "peak_z": r["peak"].get("z"), "peak_p": r["peak"].get("p")}
           for d, r in res.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
