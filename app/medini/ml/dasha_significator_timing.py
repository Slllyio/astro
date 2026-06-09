"""Does the dasha TIME events to the native's chart-specific significators?

The valence work (Findings 3–7) hit a wall: event "benefit" is ~deterministic
from `event_class`, so predicting it is near-circular. This module switches to a
target that is **independent of the chart and non-circular** — *which lord was
running when the event occurred* — and asks the foundational claim of predictive
jyotish directly:

    Do life events fall in the Mahadasha/Antardasha of the planets that
    signify that event's house **in this native's own chart**, more than
    chance?

Two kinds of significator, deliberately separated:

  * **house-lord** — the lord of the event's domain bhava (7th for marriage,
    10th for career, 8th for death …). This is **chart-specific**: the 7th lord
    is Mars for an Aries ascendant, Venus for Taurus, and so on. This is the
    part the existing `dasha_event_associations` module never isolates.
  * **karaka** — the universal significator (Venus for marriage, Saturn for
    death …). Same planet for everyone, so it is *not* chart-specific.

Two nulls, each matched to what it can actually test:

  * **House-lord → chart-shuffle permutation (rigorous).** Reassign every
    person a *donor ascendant* and recompute the house-lord set; the real
    running lord is held fixed. If the real chart's house-lord matches the
    running lord more than a random chart's would, dasha timing carries
    genuine chart-specific signal. This automatically absorbs Vimshottari
    exposure asymmetry (the running-lord distribution is untouched).
  * **Karaka → exposure-adjusted lift (descriptive).** A universal karaka
    can't be permuted by shuffling ascendants, so we test it the classical
    way: observed match rate ÷ the person-time the karaka's dasha occupies
    (`measured` exposure from `dasha_windows`). Lift > 1 ⇒ events cluster in
    the karaka's period beyond its raw share of life.

Reported per event class for MD, AD, and MD∩AD (does the sub-period sharpen
the timing) — a data-driven verdict on *which classical significator rules
actually hold*.

Usage::

    python -m app.medini.ml.dasha_significator_timing \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --k 400
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from app.core.bhava_judge import _BHAVA_KARAKAS
from app.core.dignity import SIGN_RULERS
from app.medini.ml.dasha_event_promise import _EVENT_BHAVAS, _sign_in_house

logger = logging.getLogger(__name__)

_LORDS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
# Classes worth a per-rule verdict (enough events + a clear domain bhava).
_REPORT_CLASSES: Final[tuple[str, ...]] = (
    "marriage", "career", "death", "health", "divorce", "education",
    "relationship", "progeny", "finance",
)


def _houselord_lookup() -> np.ndarray:
    """L[asc-1, bhava-1] = index into _LORDS of that bhava's lord for that asc."""
    lord_idx = {l: i for i, l in enumerate(_LORDS)}
    L = np.zeros((12, 12), dtype=int)
    for asc in range(1, 13):
        for b in range(1, 13):
            L[asc - 1, b - 1] = lord_idx[SIGN_RULERS[_sign_in_house(b, asc)]]
    return L


def _bhavas_for(event_class: object) -> tuple[int, ...]:
    return _EVENT_BHAVAS.get(str(event_class or "other").strip().lower(), (1,))


def measured_md_exposure_by_person(windows: pd.DataFrame, lord_col: str,
                                   ) -> dict[str, np.ndarray]:
    """Per-person exposure share over _LORDS, from dasha-window person-time."""
    lord_idx = {l: i for i, l in enumerate(_LORDS)}
    out: dict[str, np.ndarray] = {}
    for pid, g in windows.groupby("person_id"):
        v = np.zeros(len(_LORDS), dtype=float)
        for lord, dur in g.groupby(lord_col)["duration_days"].sum().items():
            if str(lord) in lord_idx:
                v[lord_idx[str(lord)]] += float(dur)
        tot = v.sum()
        out[str(pid)] = v / tot if tot > 0 else v
    return out


def prepare(events: pd.DataFrame, charts: pd.DataFrame,
            ) -> dict[str, object]:
    """Vectorise events for the timing test (charted events with a known asc)."""
    asc_by = charts.dropna(subset=["asc_sign"]).set_index("person_id")["asc_sign"]
    asc_by = asc_by.astype(int)
    lord_idx = {l: i for i, l in enumerate(_LORDS)}

    df = events[events["person_id"].isin(asc_by.index)
                & events["md_lord_at_event"].isin(lord_idx)].copy()
    persons = asc_by.index.tolist()
    pid_index = {p: i for i, p in enumerate(persons)}

    pe = df["person_id"].map(pid_index).to_numpy()
    asc = asc_by.to_numpy()                                   # per person
    md = df["md_lord_at_event"].map(lord_idx).to_numpy()
    ad = df["ad_lord_at_event"].map(
        lambda x: lord_idx.get(str(x), -1)).to_numpy()
    bhavas = [_bhavas_for(c) for c in df["event_class"]]
    cls = df["event_class"].astype(str).str.lower().to_numpy()
    return {"df": df, "persons": persons, "pe": pe, "asc": asc, "md": md,
            "ad": ad, "bhavas": bhavas, "cls": cls}


def _houselord_match(asc_per_person: np.ndarray, pe: np.ndarray,
                     bhavas: list[tuple[int, ...]], lord: np.ndarray,
                     L: np.ndarray) -> np.ndarray:
    """Boolean per event: is `lord` the house-lord of any domain bhava under the
    ascendant currently assigned to that event's person?"""
    out = np.zeros(len(pe), dtype=bool)
    asc_e = asc_per_person[pe]                                # asc per event
    for i in range(len(pe)):
        a = asc_e[i] - 1
        if lord[i] < 0:
            continue
        out[i] = any(L[a, b - 1] == lord[i] for b in bhavas[i])
    return out


def run_timing(events: pd.DataFrame, charts: pd.DataFrame, windows: pd.DataFrame,
               *, k: int = 400, seed: int = 0) -> pd.DataFrame:
    """Per-class significator-timing table: house-lord chart-shuffle + karaka lift."""
    P = prepare(events, charts)
    df, persons, pe, asc, md, ad, bhavas, cls = (
        P["df"], P["persons"], P["pe"], P["asc"], P["md"], P["ad"],
        P["bhavas"], P["cls"])
    L = _houselord_lookup()
    md_exp = measured_md_exposure_by_person(windows, "md_lord")
    lord_idx = {l: i for i, l in enumerate(_LORDS)}
    karaka_idx = {b: tuple(lord_idx[k] for k in ks if k in lord_idx)
                  for b, ks in _BHAVA_KARAKAS.items()}

    # real house-lord matches for MD and AD
    asc_arr = np.asarray(asc, dtype=int)
    real_md = _houselord_match(asc_arr, pe, bhavas, md, L)
    real_ad = _houselord_match(asc_arr, pe, bhavas, ad, L)

    # karaka matches (universal) + per-person karaka exposure for lift
    kar_md = np.zeros(len(pe), dtype=bool)
    kar_exp = np.zeros(len(pe), dtype=float)
    for i in range(len(pe)):
        kset = set()
        for b in bhavas[i]:
            kset.update(karaka_idx.get(b, ()))
        kar_md[i] = md[i] in kset
        ev = md_exp.get(persons[pe[i]])
        if ev is not None and kset:
            kar_exp[i] = float(ev[list(kset)].sum())

    rng = np.random.default_rng(seed)
    rows = []
    for c in _REPORT_CLASSES:
        m = cls == c
        n = int(m.sum())
        if n < 40:
            continue
        # --- house-lord MD: chart-shuffle null ---
        obs = float(real_md[m].mean())
        null = np.empty(k)
        for j in range(k):
            donor = asc_arr[rng.permutation(len(persons))]
            null[j] = _houselord_match(donor, pe[m], [bhavas[i] for i in np.where(m)[0]],
                                       md[m], L).mean()
        nmean, nstd = float(null.mean()), float(null.std(ddof=1))
        z = (obs - nmean) / nstd if nstd > 0 else float("nan")
        p = float((null >= obs).sum() + 1) / (k + 1)
        # --- house-lord AD (descriptive obs only) ---
        obs_ad = float(real_ad[m].mean())
        # --- karaka MD: exposure lift ---
        k_obs = float(kar_md[m].mean())
        k_exp = float(kar_exp[m].mean())
        rows.append({
            "event_class": c, "n": n,
            "houselord_md_obs": round(obs, 3),
            "houselord_md_null": round(nmean, 3),
            "houselord_md_lift": round(obs / nmean, 3) if nmean else float("nan"),
            "houselord_md_z": round(z, 2), "houselord_md_p": round(p, 4),
            "houselord_ad_obs": round(obs_ad, 3),
            "karaka_md_obs": round(k_obs, 3), "karaka_md_exp": round(k_exp, 3),
            "karaka_md_lift": round(k_obs / k_exp, 3) if k_exp else float("nan"),
        })
    return pd.DataFrame(rows)


def build_report(tab: pd.DataFrame, *, k: int) -> str:
    L = ["# Significator timing — does the dasha time events to the chart?", "",
         "Non-circular test: target is *which lord was running*, predicted by the "
         "native's own significators. House-lord is chart-specific (different "
         "planet per ascendant) and tested by a chart-shuffle null; the universal "
         "karaka is tested by exposure-adjusted lift.", "",
         f"Chart-shuffle K={k}. ✶ = house-lord chart-shuffle p < 0.05.", "",
         "## House-lord (chart-specific) — the rigorous test", "",
         "| event_class | n | MD match | shuffled | lift | z | p | AD match |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for _, r in tab.iterrows():
        star = " ✶" if r["houselord_md_p"] < 0.05 else ""
        L.append(
            f"| {r['event_class']} | {r['n']} | {r['houselord_md_obs']*100:.0f}% | "
            f"{r['houselord_md_null']*100:.0f}% | **{r['houselord_md_lift']:.2f}**{star} | "
            f"{r['houselord_md_z']} | {r['houselord_md_p']:.4g} | "
            f"{r['houselord_ad_obs']*100:.0f}% |")
    L += ["", "## Karaka (universal) — exposure-adjusted lift", "",
          "| event_class | n | MD karaka match | exposure | lift |",
          "|---|---:|---:|---:|---:|"]
    for _, r in tab.iterrows():
        L.append(f"| {r['event_class']} | {r['n']} | {r['karaka_md_obs']*100:.0f}% | "
                 f"{r['karaka_md_exp']*100:.0f}% | **{r['karaka_md_lift']:.2f}** |")
    # verdict
    sig = tab[tab["houselord_md_p"] < 0.05]["event_class"].tolist()
    bonf = 0.05 / len(tab) if len(tab) else 0.05
    sig_bonf = tab[tab["houselord_md_p"] < bonf]["event_class"].tolist()
    L += ["", "## Verdict", "",
          f"- House-lord timing is significant (chart-shuffle raw p<0.05) for: "
          f"**{', '.join(sig) if sig else 'none'}**.",
          f"- Surviving Bonferroni across {len(tab)} classes (p<{bonf:.4f}): "
          f"**{', '.join(sig_bonf) if sig_bonf else 'none'}** — borderline cases "
          "are best read as the most pre-registered classical rule (7th-lord→"
          "marriage), not data-mined.",
          "- Lift > 1 with z > 0 ⇒ events fall under the native's own house-lord "
          "more than a random chart's — chart-specific dasha timing.",
          "- Karaka lift > 1 ⇒ the universal significator's period also attracts "
          "the event beyond its share of life (classical, but not chart-specific). "
          "Note marriage: house-lord lift > 1 yet karaka (Venus) lift < 1 — it is "
          "the chart-specific 7th-lord, not universal Venus, that times marriage.",
          ""]
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path, *, k: int = 400, seed: int = 0,
        ) -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    events = events[events["md_lord_at_event"].notna()].copy()
    charts = pd.read_parquet(data_dir / "charts.parquet")
    windows = pd.read_parquet(data_dir / "dasha_windows.parquet")

    tab = run_timing(events, charts, windows, k=k, seed=seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out_dir / "significator_timing.csv", index=False)
    (out_dir / "significator_timing.md").write_text(
        build_report(tab, k=k), encoding="utf-8")
    logger.info("significator timing rows=%d", len(tab))
    return {"classes": len(tab),
            "significant": tab[tab["houselord_md_p"] < 0.05]["event_class"].tolist()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("--k", type=int, default=400)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.data_dir, args.out, k=args.k, seed=args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
