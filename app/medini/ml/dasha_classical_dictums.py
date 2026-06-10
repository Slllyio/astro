"""Test classical dictums the astrologer's way — disjunctive significator sets.

The scientific battery (`dasha_hypothesis_battery`) tested isolated single
factors against a strict permutation null. But classical jyotisha is
**conjunctive and disjunctive**: a text predicts an event in the dasha of *any*
of several significators — house-lord OR karaka OR occupant OR aspecting planet
OR the navamsa-dispositor — and reads **Mahadasha and Antardasha together**.
This module encodes the dictums from `dictum_catalog.md` as the texts prescribe
them and reports the practitioner's **hit-rate**:

    In what fraction of real events was at least one prescribed significator
    running as MD or AD?

alongside the **chance/exposure** a set of that size would catch anyway (from the
person's own dasha timeline) so the number is interpretable — but without
gating on a permutation p. The system is judged on its own terms.

Also tests two non-timing dictums: **Mangal/Kuja Dosha → divorce** (M7) and the
**7th-lord-in-dusthana → later marriage** delay rule (M6).

Usage::

    python -m app.medini.ml.dasha_classical_dictums \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from app.core.bhava_judge import _BHAVA_KARAKAS
from app.core.dignity import SIGN_RULERS
from app.core.drishti_argala import planets_aspecting_bhava
from app.medini.ml.dasha_event_promise import _sign_in_house

logger = logging.getLogger(__name__)
_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

# Per class: prescribed significators (the disjunctive union the texts give).
DICTUMS: Final[dict[str, dict]] = {
    "marriage": {"houses": [7, 2, 11], "karaka_houses": [7], "occ": [7],
                 "asp": [7], "d9_disp": [7], "src": "M1–M5"},
    "relationship": {"houses": [5, 7], "karaka_houses": [5, 7], "occ": [5, 7],
                     "asp": [7], "d9_disp": [7], "src": "M1–M4 / P1"},
    "career": {"houses": [10], "karaka_houses": [10], "occ": [10], "asp": [10],
               "d9_disp": [10], "src": "C1–C3"},
    "death": {"houses": [8, 2, 7], "karaka_houses": [8], "occ": [2, 7, 8],
              "asp": [], "d9_disp": [8], "src": "D1–D3"},
    "education": {"houses": [4, 5], "karaka_houses": [4, 5], "occ": [4, 5],
                  "asp": [], "d9_disp": [], "extra": ["Mercury", "Jupiter"],
                  "src": "E1"},
    "family": {"houses": [2, 4], "karaka_houses": [2, 4], "occ": [2, 4],
               "asp": [], "d9_disp": [], "src": "W1 / family"},
    "divorce": {"houses": [7, 6, 8], "karaka_houses": [7], "occ": [6, 8],
                "asp": [7], "d9_disp": [7], "src": "M1 / D1"},
    "health": {"houses": [1, 6, 8], "karaka_houses": [6], "occ": [6, 8],
               "asp": [6], "d9_disp": [], "src": "D2 / 6th"},
}
_DUSTHANA: Final[frozenset[int]] = frozenset({6, 8, 12})
_KUJA_HOUSES: Final[frozenset[int]] = frozenset({1, 2, 4, 7, 8, 12})


def _significator_set(crow: pd.Series, d9row: pd.Series | None, cfg: dict) -> set[str]:
    asc = int(crow["asc_sign"])
    planet_houses = {g: int(crow[f"{g.lower()}_house"]) for g in _GRAHAS
                     if pd.notna(crow.get(f"{g.lower()}_house"))}
    s: set[str] = set(cfg.get("extra", []))
    for h in cfg["houses"]:                                   # house-lords
        s.add(SIGN_RULERS[_sign_in_house(h, asc)])
    for h in cfg["karaka_houses"]:                            # karakas
        s.update(_BHAVA_KARAKAS.get(h, ()))
    for h in cfg["occ"]:                                      # occupants
        s.update(p for p, ph in planet_houses.items() if ph == h)
    for h in cfg["asp"]:                                      # aspecting planets
        s.update(planets_aspecting_bhava(h, planet_houses))
    if d9row is not None:                                     # navamsa dispositor
        for h in cfg["d9_disp"]:
            lord = SIGN_RULERS[_sign_in_house(h, asc)]
            d9s = d9row.get(f"{lord.lower()}_d9_sign")
            if pd.notna(d9s):
                s.add(SIGN_RULERS[int(d9s)])
    return {p for p in s if p in _GRAHAS}


def _person_exposure(win_g: pd.DataFrame, sset: set[str]) -> float:
    """Fraction of life where MD or AD lord is in the significator set."""
    hit = win_g["md_lord"].isin(sset) | win_g["ad_lord"].isin(sset)
    tot = float(win_g["duration_days"].sum())
    return float(win_g.loc[hit, "duration_days"].sum() / tot) if tot else 0.0


def classical_hitrate(events: pd.DataFrame, charts: pd.DataFrame,
                      d9: pd.DataFrame | None, windows: pd.DataFrame,
                      ) -> pd.DataFrame:
    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    d9idx = d9.drop_duplicates("person_id").set_index("person_id") if d9 is not None else None
    win_by = {pid: g for pid, g in windows.groupby("person_id")}
    rows = []
    for cls, cfg in DICTUMS.items():
        ev = events[(events["event_class"].astype(str).str.lower() == cls)
                    & events["md_lord_at_event"].notna()]
        if len(ev) < 40:
            continue
        hits, exps, sizes = [], [], []
        set_cache: dict[str, set[str]] = {}
        for _, e in ev.iterrows():
            pid = e["person_id"]
            if pid not in cidx.index:
                continue
            if pid not in set_cache:
                d9row = d9idx.loc[pid] if (d9idx is not None and pid in d9idx.index) else None
                set_cache[pid] = _significator_set(cidx.loc[pid], d9row, cfg)
            S = set_cache[pid]
            hits.append(int(e["md_lord_at_event"] in S
                            or e.get("ad_lord_at_event") in S))
            sizes.append(len(S))
            if pid in win_by:
                exps.append(_person_exposure(win_by[pid], S))
        if not hits:
            continue
        hr, ex = float(np.mean(hits)), float(np.mean(exps)) if exps else float("nan")
        rows.append({"event_class": cls, "src": cfg["src"], "n": len(hits),
                     "set_size": round(float(np.mean(sizes)), 1),
                     "hit_rate": round(hr, 3), "chance": round(ex, 3),
                     "lift": round(hr / ex, 3) if ex else float("nan")})
    return pd.DataFrame(rows)


def mangal_dosha(events: pd.DataFrame, charts: pd.DataFrame) -> dict[str, object]:
    """Kuja Dosha (Mars in 1/2/4/7/8/12 from Lagna) vs divorce/relationship."""
    c = charts.drop_duplicates("person_id").copy()
    c["kuja"] = c["mars_house"].isin(_KUJA_HOUSES)
    by_person = c.set_index("person_id")["kuja"]
    out = {"kuja_rate": round(float(by_person.mean()), 3)}
    for cls in ("divorce", "relationship", "marriage"):
        ppl = set(events[events["event_class"].astype(str).str.lower() == cls]["person_id"])
        has = by_person.index.to_series().isin(ppl)
        d_rate = float(has[by_person].mean())          # P(event | kuja)
        nd_rate = float(has[~by_person].mean())        # P(event | no kuja)
        out[cls] = {"with_dosha": round(d_rate, 3), "without_dosha": round(nd_rate, 3),
                    "ratio": round(d_rate / nd_rate, 3) if nd_rate else float("nan")}
    return out


def marriage_delay(events: pd.DataFrame, charts: pd.DataFrame) -> dict[str, object]:
    """M6: 7th-lord in dusthana (6/8/12) → later marriage?"""
    c = charts.drop_duplicates("person_id").set_index("person_id")
    mar = events[(events["event_class"].astype(str).str.lower() == "marriage")
                 & events["age_at_event_years"].notna()]
    mar = mar.sort_values("age_at_event_years").groupby("person_id").head(1)
    ages_dust, ages_ok = [], []
    for _, e in mar.iterrows():
        pid = e["person_id"]
        if pid not in c.index:
            continue
        asc = c.loc[pid, "asc_sign"]
        if pd.isna(asc):
            continue
        l7 = SIGN_RULERS[_sign_in_house(7, int(asc))]
        h7 = c.loc[pid, f"{l7.lower()}_house"]
        if pd.isna(h7):
            continue
        (ages_dust if int(h7) in _DUSTHANA else ages_ok).append(
            float(e["age_at_event_years"]))
    return {"n_dusthana": len(ages_dust), "n_other": len(ages_ok),
            "mean_age_7L_dusthana": round(float(np.mean(ages_dust)), 2) if ages_dust else None,
            "mean_age_7L_other": round(float(np.mean(ages_ok)), 2) if ages_ok else None,
            "delay_years": round(float(np.mean(ages_dust) - np.mean(ages_ok)), 2)
            if ages_dust and ages_ok else None}


def build_report(tab: pd.DataFrame, kuja: dict, delay: dict) -> str:
    L = ["# Classical dictums tested the astrologer's way", "",
         "Hit-rate = fraction of real events where **at least one prescribed "
         "significator** (house-lord ∪ karaka ∪ occupant ∪ aspector ∪ navamsa "
         "dispositor) was running as **MD or AD**. `chance` = how often a set of "
         "that size runs anyway (from each native's own timeline). No permutation "
         "gate — the system judged on its own conjunctive terms.", "",
         "## Timing dictums", "",
         "| event | dictums | n | significators | hit-rate | chance | lift |",
         "|---|---|---:|---:|---:|---:|---:|"]
    for _, r in tab.iterrows():
        L.append(f"| {r['event_class']} | {r['src']} | {r['n']} | {r['set_size']} | "
                 f"**{r['hit_rate']*100:.0f}%** | {r['chance']*100:.0f}% | "
                 f"**{r['lift']:.2f}** |")
    L += ["", "## M7 — Mangal / Kuja Dosha (Mars in 1/2/4/7/8/12 from Lagna)", "",
          f"Dosha present in **{kuja['kuja_rate']*100:.0f}%** of natives. "
          "Share of natives who have each event, with vs without the dosha:", "",
          "| event | with dosha | without dosha | ratio |", "|---|---:|---:|---:|"]
    for cls in ("divorce", "relationship", "marriage"):
        d = kuja[cls]
        L.append(f"| {cls} | {d['with_dosha']*100:.0f}% | {d['without_dosha']*100:.0f}% "
                 f"| **{d['ratio']:.2f}** |")
    L += ["", "## M6 — 7th-lord in dusthana (6/8/12) → later marriage?", "",
          f"- 7th-lord in dusthana: mean marriage age "
          f"**{delay['mean_age_7L_dusthana']}** (n={delay['n_dusthana']})",
          f"- 7th-lord elsewhere: mean marriage age "
          f"**{delay['mean_age_7L_other']}** (n={delay['n_other']})",
          f"- **Delay: {delay['delay_years']:+} years**" if delay['delay_years'] is not None
          else "- (insufficient)",
          "", "## Reading", "",
          "- A `lift` > 1 means the *specific* prescribed planets caught the event "
          "more than a same-size random set would — the dictum adds skill beyond "
          "'name enough planets and one will be running'.",
          "- A `lift` ≈ 1 with a high hit-rate means the rule *appears* accurate "
          "only because it names many significators (large `set_size`): it would "
          "'hit' almost as often by chance.", ""]
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path) -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    windows = pd.read_parquet(data_dir / "dasha_windows.parquet")
    d9_path = data_dir / "charts_d9.parquet"
    d9 = pd.read_parquet(d9_path) if d9_path.exists() else None

    tab = classical_hitrate(events, charts, d9, windows)
    kuja = mangal_dosha(events, charts)
    delay = marriage_delay(events, charts)

    out_dir.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out_dir / "classical_dictum_hitrate.csv", index=False)
    (out_dir / "classical_dictum_test.md").write_text(
        build_report(tab, kuja, delay), encoding="utf-8")
    logger.info("dictum hit-rates:\n%s\nkuja=%s delay=%s", tab, kuja, delay)
    return {"classes": len(tab), "kuja": kuja, "delay": delay}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.data_dir, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
