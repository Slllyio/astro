"""Verse-level dictum timing — testing the classics exactly as the texts state them.

Findings 11–13 abstracted the classics into "significator families" and a 0–6
confluence count. That blended two *different* doctrines and never tested the
mechanism BPHS actually uses. The verse-level research pass
(`dictum_catalog_v2.md`) lets us encode specific rules and test them within each
life, exposure-controlled. This module implements the highest-value, genuinely
novel ones:

T1. **The AD-counted-from-the-MD-lord frame (PD 20.29; BPHS 52–60 passim).**
    Parashara's core timing rule is *positional from the dāyeśa*: the bhukti lord
    in the 6th/8th/12th **from the dasha lord** gives sorrow; in kendra/trikona/11
    it gives the auspicious results of that house. We never tested this frame.
    Direction-aware: auspicious events (marriage/career/education) should favour
    the benefic positions; death should favour the malefic (6/8/12) positions.

T2. **The 7th-lord school adjudication (the headline scholarly finding).**
    In **Phaladeepika 10.13 / Jataka Parijata 14.29** the 7th-lord's dasha *gives
    marriage*. In **BPHS 48.5–8 / 44.2–5** the 7th-lord is a **maraka** — its
    dasha brings "distress to wife and possible death of the native." These are
    empirically decidable: does the 7L MD/AD elevate **marriage**, **death**,
    both, or neither, relative to each native's own exposure? Whichever lifts
    tells us which school this corpus supports.

T3. **The two marriage streams, separated.** Phaladeepika-stream (7L ∪ Venus ∪
    occupant/aspector of 7H ∪ rāśi/navāṁśa-dispositor of 7L as MD or AD) vs
    BPHS-stream (a natural-benefic AD, well-dignified, in a benefic position from
    both Lagna and the MD lord). Each tested separately so a real signal in one
    is not diluted by the other (Finding 13's dilution lesson).

Statistic — **within-person exposure-controlled lift** (Poisson–binomial):
for each native, a condition's *exposure* = the duration-weighted fraction of
their in-age-band life where the condition holds; the event is a *hit* if its own
period satisfies the condition. Under the null "events fall proportional to
duration," the event is a hit with probability = exposure. Aggregating over
natives, H = Σ hit, E = Σ exposure, V = Σ exposure(1−exposure); z = (H−E)/√V,
lift = H/E. Each native is its own control, so age/era confounds cancel and a
large significator set cannot manufacture lift (its big exposure is the baseline).

Usage::

    python -m app.medini.ml.dasha_verse_timing \\
        --data-dir /tmp/la_run --out data/ml_runs/lunarastro_dignity
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Callable, Final

import numpy as np
import pandas as pd
from scipy.stats import norm

from app.core.dignity import SIGN_RULERS, dignity_state
from app.core.drishti_argala import planets_aspecting_bhava
from app.medini.ml.dasha_event_promise import _sign_in_house

logger = logging.getLogger(__name__)
_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_GOOD_DIGNITY: Final[frozenset[str]] = frozenset({"exalted", "own", "friendly"})
# house-from-dāyeśa classification (PD 20.29 + BPHS 52–60).
_GOOD_FROM_MD: Final[frozenset[int]] = frozenset({1, 4, 5, 7, 9, 10, 11})  # kendra/trikona/11
_BAD_FROM_MD: Final[frozenset[int]] = frozenset({6, 8, 12})                # dusthana
# domain → (auspicious?, age band). death is the one inauspicious domain.
DOMAINS: Final[dict[str, tuple[bool, tuple[int, int]]]] = {
    "marriage": (True, (16, 55)),
    "career": (True, (18, 72)),
    "education": (True, (8, 40)),
    "death": (False, (30, 105)),
}


def _house_from(a_house: int, ref_house: int) -> int:
    """House number of a planet counted *from* a reference planet's house (1..12)."""
    return ((a_house - ref_house) % 12) + 1


def _person_facts(crow: pd.Series, d9row: pd.Series | None) -> dict:
    asc = int(crow["asc_sign"])
    houses = {g: int(crow[f"{g.lower()}_house"]) for g in _GRAHAS
              if pd.notna(crow.get(f"{g.lower()}_house"))}
    signs = {g: int(crow[f"{g.lower()}_sign"]) for g in _GRAHAS
             if pd.notna(crow.get(f"{g.lower()}_sign"))}
    d9 = ({g: int(d9row[f"{g.lower()}_d9_sign"]) for g in _GRAHAS
           if d9row is not None and pd.notna(d9row.get(f"{g.lower()}_d9_sign"))}
          if d9row is not None else {})

    # functional lords of key houses.
    lord = {h: SIGN_RULERS[_sign_in_house(h, asc)] for h in (7, 10, 8, 2, 5, 4)}

    # good (well-dignified) natural benefics, by natal sign.
    good = set()
    for g in _GRAHAS:
        if g in signs:
            try:
                if dignity_state(g, signs[g]) in _GOOD_DIGNITY:
                    good.add(g)
            except (KeyError, ValueError):
                pass

    # Phaladeepika-stream marriage significators (7L ∪ Venus ∪ occ/asp 7H ∪
    # rāśi/navāṁśa dispositor of 7L).
    l7 = lord[7]
    phala = {l7, "Venus"}
    phala |= {p for p, h in houses.items() if h == 7}                 # occupants
    phala |= set(planets_aspecting_bhava(7, houses))                  # aspectors
    if l7 in signs:
        phala.add(SIGN_RULERS[signs[l7]])                            # rāśi-dispositor
    if l7 in d9:
        phala.add(SIGN_RULERS[d9[l7]])                               # navāṁśa-dispositor
    phala = {p for p in phala if p in _GRAHAS}

    return {"houses": houses, "signs": signs, "good": good, "lord": lord,
            "phala": phala}


# ── condition predicates: f(md, ad, facts) → bool ───────────────────────────
def _ad_from_md(md: str, ad: str, f: dict) -> int | None:
    h = f["houses"]
    if md in h and ad in h:
        return _house_from(h[ad], h[md])
    return None


def cond_pos_benefic(md: str, ad: str, f: dict) -> bool:
    """PD 20.29: AD lord in kendra/trikona/11 from the MD lord."""
    p = _ad_from_md(md, ad, f)
    return p is not None and p in _GOOD_FROM_MD


def cond_pos_malefic(md: str, ad: str, f: dict) -> bool:
    """PD 20.29: AD lord in 6/8/12 from the MD lord → sorrow."""
    p = _ad_from_md(md, ad, f)
    return p is not None and p in _BAD_FROM_MD


def cond_7L(md: str, ad: str, f: dict) -> bool:
    """7th-lord runs as MD or AD (Phaladeepika marriage / BPHS maraka)."""
    l7 = f["lord"][7]
    return md == l7 or ad == l7


def cond_phala_stream(md: str, ad: str, f: dict) -> bool:
    """Phaladeepika-stream marriage significator as MD or AD."""
    return md in f["phala"] or ad in f["phala"]


def cond_bphs_stream(md: str, ad: str, f: dict) -> bool:
    """BPHS-stream: a well-dignified natural-benefic AD, benefic from both
    Lagna (kendra/trikona) and the MD lord (PD 20.29 + the 52–60 conditions)."""
    if ad not in _BENEFICS or ad not in f["good"]:
        return False
    ah = f["houses"].get(ad)
    if ah is None or ah not in {1, 4, 5, 7, 9, 10}:        # kendra/trikona from Lagna
        return False
    return cond_pos_benefic(md, ad, f)


# domain → {condition_name: predicate}. Directionality handled in reporting.
CONDITIONS: Final[dict[str, dict[str, Callable]]] = {
    "marriage": {"AD_benefic_from_MD": cond_pos_benefic,
                 "AD_malefic_from_MD": cond_pos_malefic,
                 "7L_period": cond_7L,
                 "Phaladeepika_stream": cond_phala_stream,
                 "BPHS_benefic_AD_stream": cond_bphs_stream},
    "career": {"AD_benefic_from_MD": cond_pos_benefic,
               "AD_malefic_from_MD": cond_pos_malefic,
               "BPHS_benefic_AD_stream": cond_bphs_stream},
    "education": {"AD_benefic_from_MD": cond_pos_benefic,
                  "AD_malefic_from_MD": cond_pos_malefic},
    "death": {"AD_benefic_from_MD": cond_pos_benefic,
              "AD_malefic_from_MD": cond_pos_malefic,
              "7L_period": cond_7L},
}


def _first_events(events: pd.DataFrame, domain: str) -> pd.DataFrame:
    ev = events[events["event_class"].astype(str).str.lower() == domain].copy()
    ev = ev.dropna(subset=["md_seq", "ad_seq"])
    return ev.sort_values("event_jd").groupby("person_id").head(1)


def within_person_lift(windows: pd.DataFrame, charts: pd.DataFrame,
                       d9: pd.DataFrame | None, events: pd.DataFrame,
                       domain: str) -> dict:
    auspicious, (lo, hi) = DOMAINS[domain]
    conds = CONDITIONS[domain]
    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    d9idx = d9.drop_duplicates("person_id").set_index("person_id") if d9 is not None else None
    birth = cidx["birth_jd_used"]
    ev_first = _first_events(events, domain).set_index("person_id")

    acc = {c: {"H": 0.0, "E": 0.0, "V": 0.0, "n": 0} for c in conds}
    n_persons = n_dropped = 0

    for pid, wg in windows.groupby("person_id"):
        if pid not in cidx.index or pid not in ev_first.index or pd.isna(birth.get(pid)):
            continue
        b = float(birth[pid])
        f = _person_facts(cidx.loc[pid],
                          d9idx.loc[pid] if (d9idx is not None and pid in d9idx.index) else None)
        mid_age = (((wg["start_jd"] + wg["end_jd"]) / 2) - b) / 365.25
        band = wg[(mid_age >= lo) & (mid_age <= hi)]
        if band.empty or band["duration_days"].sum() <= 0:
            continue
        evrow = ev_first.loc[pid]
        eseq = (int(evrow["md_seq"]), int(evrow["ad_seq"]))
        ew = band[(band["md_seq"] == eseq[0]) & (band["ad_seq"] == eseq[1])]
        if ew.empty:                          # event period falls outside the age band
            n_dropped += 1
            continue
        n_persons += 1
        tot = float(band["duration_days"].sum())
        for cname, pred in conds.items():
            flags = band.apply(lambda r: pred(str(r["md_lord"]), str(r["ad_lord"]), f), axis=1)
            expo = float(band.loc[flags, "duration_days"].sum() / tot)
            hit = bool(pred(str(ew.iloc[0]["md_lord"]), str(ew.iloc[0]["ad_lord"]), f))
            a = acc[cname]
            a["H"] += hit
            a["E"] += expo
            a["V"] += expo * (1.0 - expo)
            a["n"] += 1

    out = {"domain": domain, "auspicious": auspicious, "n_persons": n_persons,
           "n_dropped_out_of_band": n_dropped, "conditions": {}, "_raw": acc}
    for cname, a in acc.items():
        if a["n"] == 0 or a["V"] <= 0:
            continue
        z = (a["H"] - a["E"]) / np.sqrt(a["V"])
        out["conditions"][cname] = {
            "n": a["n"], "hit_rate": round(a["H"] / a["n"], 4),
            "expected": round(a["E"] / a["n"], 4),
            "lift": round(a["H"] / a["E"], 3) if a["E"] else None,
            "z": round(float(z), 2),
            "p": round(float(2 * norm.sf(abs(z))), 4)}
    return out


def _stat(a: dict) -> dict:
    z = (a["H"] - a["E"]) / np.sqrt(a["V"])
    return {"n": a["n"], "hit_rate": round(a["H"] / a["n"], 4),
            "expected": round(a["E"] / a["n"], 4),
            "lift": round(a["H"] / a["E"], 3) if a["E"] else None,
            "z": round(float(z), 2), "p": round(float(2 * norm.sf(abs(z))), 4)}


def pooled_tests(results: list[dict]) -> dict:
    """Power-boosting meta-tests that pool raw Poisson–binomial accumulators
    across domains. Pooling H/E/V is exact for the same condition; a native with
    events in several domains contributes once per domain (different events)."""
    by_dom = {r["domain"]: r["_raw"] for r in results}
    pools: dict[str, list[str]] = {
        # PD 20.29 frame: does a benefic position from the MD lord lift the three
        # auspicious domains jointly?
        "AD_benefic_from_MD ∣ auspicious (marriage+career+education)":
            ["marriage", "career", "education"],
        # the BPHS well-dignified-benefic-AD stream across its two big domains.
        "BPHS_benefic_AD_stream ∣ marriage+career": ["marriage", "career"],
    }
    cond_of = {"AD_benefic_from_MD ∣ auspicious (marriage+career+education)":
               "AD_benefic_from_MD",
               "BPHS_benefic_AD_stream ∣ marriage+career": "BPHS_benefic_AD_stream"}
    out = {}
    for label, doms in pools.items():
        cname = cond_of[label]
        agg = {"H": 0.0, "E": 0.0, "V": 0.0, "n": 0}
        for d in doms:
            a = by_dom[d][cname]
            for k in agg:
                agg[k] += a[k]
        if agg["V"] > 0:
            out[label] = _stat(agg)
    return out


def build_report(results: list[dict], pooled: dict) -> str:
    L = ["# Verse-level dictum timing — the classics tested as written", "",
         "Within-person, exposure-controlled lift. For each native a condition's "
         "**expected** = the duration-weighted share of their in-age-band life where "
         "the condition holds; **hit-rate** = share of natives whose actual event "
         "period satisfied it. **lift = hit/expected** (1.0 = no skill beyond "
         "chance); z from the Poisson–binomial null (events ∝ duration). Each "
         "native is its own control.", ""]
    for res in results:
        dom = res["domain"]
        dirn = "auspicious — expect benefic positions to lift" if res["auspicious"] \
            else "inauspicious — expect malefic (6/8/12) positions to lift"
        L += [f"## {dom}  ({dirn})", "",
              f"n={res['n_persons']} natives (dropped {res['n_dropped_out_of_band']} "
              "whose event fell outside the age band).", "",
              "| condition | n | hit-rate | expected | lift | z | p |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for cname, c in res["conditions"].items():
            star = " ✦" if c["p"] < 0.05 else ""
            L.append(f"| {cname}{star} | {c['n']} | {c['hit_rate']*100:.1f}% | "
                     f"{c['expected']*100:.1f}% | **{c['lift']}** | {c['z']} | {c['p']:.3g} |")
        L.append("")
    if pooled:
        L += ["## Pooled meta-tests (power-boosting)", "",
              "| pooled condition | n | hit-rate | expected | lift | z | p |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for label, c in pooled.items():
            star = " ✦" if c["p"] < 0.05 else ""
            L.append(f"| {label}{star} | {c['n']} | {c['hit_rate']*100:.1f}% | "
                     f"{c['expected']*100:.1f}% | **{c['lift']}** | {c['z']} | {c['p']:.3g} |")
        L.append("")
    L += ["## Reading", "",
          "- **lift > 1, p < 0.05** ⇒ events concentrate in the rule's periods "
          "beyond each native's own exposure — the verse carries real timing skill.",
          "- **lift ≈ 1** ⇒ the rule names periods the event already occupies by "
          "duration alone — no skill (the Finding 11–13 pattern).",
          "- **T2 adjudication**: compare `7L_period` lift for *marriage* vs *death*. "
          "Phaladeepika predicts a marriage lift; BPHS's maraka doctrine predicts a "
          "death lift. The data picks the school.",
          "- **T1**: for auspicious domains `AD_benefic_from_MD` should lift and "
          "`AD_malefic_from_MD` should sit below 1; for death the reverse — the "
          "first direct test of Parashara's from-the-dāyeśa frame.", ""]
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path) -> list[dict]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    windows = pd.read_parquet(data_dir / "dasha_windows.parquet")
    d9 = pd.read_parquet(data_dir / "charts_d9.parquet") \
        if (data_dir / "charts_d9.parquet").exists() else None

    results = []
    for dom in DOMAINS:
        res = within_person_lift(windows, charts, d9, events, dom)
        results.append(res)
        logger.info("%s: n=%d  %s", dom, res["n_persons"],
                    {c: v["lift"] for c, v in res["conditions"].items()})

    pooled = pooled_tests(results)
    logger.info("pooled: %s", {k: (v["lift"], v["p"]) for k, v in pooled.items()})

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "verse_timing.md").write_text(
        build_report(results, pooled), encoding="utf-8")
    for r in results:                                    # drop bulky raw accumulators
        r.pop("_raw", None)
    (out_dir / "verse_timing.json").write_text(
        json.dumps({"per_domain": results, "pooled": pooled}, indent=2),
        encoding="utf-8")
    rows = [{"domain": r["domain"], "condition": c, **v}
            for r in results for c, v in r["conditions"].items()]
    pd.DataFrame(rows).to_csv(out_dir / "verse_timing.csv", index=False)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=Path("/tmp/la_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    res = run(args.data_dir, args.out)
    for r in res:
        print(r["domain"], {c: (v["lift"], v["p"]) for c, v in r["conditions"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
