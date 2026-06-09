"""Does the D9 (Navamsa) refine the marriage-timing significator?

Finding 9 pinned the signal to the **D1 7th-lord Mahadasha** (lift 1.15). The
Navamsa is the classical marriage varga, so the question is whether D9-derived
significators time marriage as well as, or better than, the plain D1 7th-lord.

Without the D9 ascendant (birth lat/long were not persisted) we use the two
strongest **planet-based** D9 significators, both fully recoverable:

  * **venus_d9_disp** — the lord of the sign Venus occupies in Navamsa (the
    karaka's deeper dispositor).
  * **d1_7L_d9_disp** — the lord of the Navamsa sign the D1 7th-lord falls in
    (where the 7th-lord's strength "matures").
  * **d1_7th_lord** — the D1 baseline, recomputed here for a like-for-like
    comparison (should reproduce ~1.15).
  * **d1_7L_or_venus_d9** — does either firing widen the catch?

Each significator is a single planet per native; we test whether the running
MD lord equals it among marriages, against a **shuffle null** (reassign the
significator planet across natives; the running lord stays fixed, so Vimshottari
exposure and each planet's marginal significator-frequency are both absorbed).
K is large for a tight p on the headline.

Usage::

    python -m app.medini.ml.dasha_marriage_d9 \\
        --data-dir app/medini/data/lunarastro_run \\
        --out data/ml_runs/lunarastro_dignity --k 5000
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Callable, Final

import numpy as np
import pandas as pd

from app.core.dignity import SIGN_RULERS
from app.medini.ml.dasha_significator_timing import _LORDS
from app.medini.ml.dasha_event_promise import _sign_in_house

logger = logging.getLogger(__name__)
_LORD_IDX: Final[dict[str, int]] = {l: i for i, l in enumerate(_LORDS)}


def _idx(planet: str | None) -> int:
    return _LORD_IDX.get(str(planet), -1)


def _sig_d1_7th_lord(row: pd.Series) -> int:
    return _idx(SIGN_RULERS[_sign_in_house(7, int(row["asc_sign"]))])


def _sig_venus_d9_disp(row: pd.Series) -> int:
    return _idx(SIGN_RULERS[int(row["venus_d9_sign"])])


def _sig_d1_7L_d9_disp(row: pd.Series) -> int:
    p7 = SIGN_RULERS[_sign_in_house(7, int(row["asc_sign"]))]   # D1 7th-lord
    d9_sign = row.get(f"{p7.lower()}_d9_sign")
    if pd.isna(d9_sign):
        return -1
    return _idx(SIGN_RULERS[int(d9_sign)])


_SIGNIFICATORS: Final[dict[str, Callable[[pd.Series], int]]] = {
    "d1_7th_lord": _sig_d1_7th_lord,
    "venus_d9_disp": _sig_venus_d9_disp,
    "d1_7L_d9_disp": _sig_d1_7L_d9_disp,
}


def _perm(obs: float, sig_per_person: np.ndarray, pe: np.ndarray, md: np.ndarray,
          *, k: int, seed: int, second: np.ndarray | None = None) -> dict:
    """Shuffle the significator planet across natives; match = md == sig."""
    rng = np.random.default_rng(seed)
    n = len(sig_per_person)
    null = np.empty(k)
    for j in range(k):
        perm = rng.permutation(n)
        s = sig_per_person[perm]
        match = (md == s[pe])
        if second is not None:
            match |= (md == second[perm][pe])
        null[j] = match.mean()
    nmean, nstd = float(null.mean()), float(null.std(ddof=1))
    return {"obs": round(obs, 4), "null": round(nmean, 4),
            "lift": round(obs / nmean, 3) if nmean else float("nan"),
            "z": round((obs - nmean) / nstd, 2) if nstd else float("nan"),
            "p": round(float((null >= obs).sum() + 1) / (k + 1), 5)}


def run_d9(events: pd.DataFrame, charts: pd.DataFrame, d9: pd.DataFrame, *,
           k: int = 5000, seed: int = 0) -> pd.DataFrame:
    merged = charts.merge(d9, on="person_id", how="inner").dropna(subset=["asc_sign"])
    persons = merged["person_id"].tolist()
    pid_index = {p: i for i, p in enumerate(persons)}

    mar = events[(events["event_class"].astype(str).str.lower() == "marriage")
                 & events["person_id"].isin(pid_index)
                 & events["md_lord_at_event"].isin(_LORD_IDX)].copy()
    pe = mar["person_id"].map(pid_index).to_numpy()
    md = mar["md_lord_at_event"].map(_LORD_IDX).to_numpy()

    sig_arrays = {name: merged.apply(fn, axis=1).to_numpy()
                  for name, fn in _SIGNIFICATORS.items()}
    rows = []
    for name, sig in sig_arrays.items():
        obs = float((md == sig[pe]).mean())
        r = _perm(obs, sig, pe, md, k=k, seed=seed)
        rows.append({"significator": name, "n_marriages": len(pe), **r})
    # combined: D1 7th-lord OR Venus-D9-dispositor
    s1, s2 = sig_arrays["d1_7th_lord"], sig_arrays["venus_d9_disp"]
    obs = float(((md == s1[pe]) | (md == s2[pe])).mean())
    rows.append({"significator": "d1_7L_or_venus_d9", "n_marriages": len(pe),
                 **_perm(obs, s1, pe, md, k=k, seed=seed, second=s2)})
    return pd.DataFrame(rows)


def build_report(tab: pd.DataFrame, *, k: int) -> str:
    L = [f"# Marriage timing — does the Navamsa (D9) refine the significator? (K={k})",
         "", "Each significator is one planet per native; tested as MD-lord match "
         "among marriages vs a shuffle null. ✶ = p < 0.05.", "",
         "| significator | n | MD match | null | lift | z | p |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for _, r in tab.iterrows():
        star = " ✶" if r["p"] < 0.05 else ""
        L.append(f"| {r['significator']} | {r['n_marriages']} | "
                 f"{r['obs']*100:.1f}% | {r['null']*100:.1f}% | "
                 f"**{r['lift']:.2f}**{star} | {r['z']} | {r['p']:.4g} |")
    d1 = tab[tab.significator == "d1_7th_lord"].iloc[0]
    best_d9 = tab[tab.significator.isin(["venus_d9_disp", "d1_7L_d9_disp"])] \
        .sort_values("lift", ascending=False).iloc[0]
    L += ["", "## Reading", "",
          f"- D1 7th-lord lift {d1['lift']:.2f} (z={d1['z']}, p={d1['p']:.3g}) — "
          "the established baseline.",
          f"- Best D9 significator: **{best_d9['significator']}** lift "
          f"{best_d9['lift']:.2f} (z={best_d9['z']}, p={best_d9['p']:.3g}). "
          + ("D9 *adds* timing resolution beyond D1."
             if best_d9["lift"] > d1["lift"] and best_d9["p"] < 0.05 else
             "D9 does **not** beat the plain D1 7th-lord here — on this corpus the "
             "Navamsa dispositors do not sharpen marriage timing."),
          "- The shuffle null absorbs each planet's marginal significator-frequency "
          "and Vimshottari exposure, so lift > 1 is a genuine chart→timing match.",
          ""]
    return "\n".join(L)


def run(data_dir: Path, out_dir: Path, *, k: int = 5000, seed: int = 0,
        d9_path: Path | None = None) -> dict[str, object]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    events = events[events["md_lord_at_event"].notna()].copy()
    charts = pd.read_parquet(data_dir / "charts.parquet")
    d9 = pd.read_parquet(d9_path or (data_dir / "charts_d9.parquet"))

    tab = run_d9(events, charts, d9, k=k, seed=seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out_dir / "marriage_d9.csv", index=False)
    (out_dir / "marriage_d9.md").write_text(build_report(tab, k=k), encoding="utf-8")
    logger.info("marriage D9: %s", tab.to_dict(orient="records"))
    return {"rows": len(tab)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path,
                        default=Path("app/medini/data/lunarastro_run"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/ml_runs/lunarastro_dignity"))
    parser.add_argument("--d9", type=Path, default=None)
    parser.add_argument("--k", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s | %(message)s")
    print(run(args.data_dir, args.out, k=args.k, seed=args.seed, d9_path=args.d9))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
