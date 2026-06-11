"""BPHS 18.22–34 fixed-age marriage yogas — the age tables tested directly.

Parashara's own marriage timing is largely a table of configurations → specific
ages ("Venus in 7th from Moon + Saturn in 7th from Venus → marriage at 18").
These need no dasha machinery at all and are directly falsifiable: among natives
matching a configuration, is the observed first-marriage age closer to the
predicted age(s) than chance (ages drawn from the corpus marriage-age
distribution)?

Encodable configurations (whole-sign; 18.31/18.32 need the navamsa lagna we
lack and are skipped; the child-age verses 18.22–18.29 are kept deliberately —
if the corpus is modern, their failure is itself the finding that the tables are
artifacts of their era, not timeless laws).

Usage::

    python -m app.medini.ml.bphs_fixed_age --data-dir /tmp/la_run \\
        --out data/ml_runs/lunarastro_dignity --k 2000
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Callable, Final

import numpy as np
import pandas as pd

from app.core.dignity import SIGN_RULERS, dignity_state
from app.medini.ml.dasha_event_promise import _sign_in_house

logger = logging.getLogger(__name__)
_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_BENEFIC_SIGNS: Final[frozenset[int]] = frozenset({2, 3, 4, 6, 7, 9, 12})  # signs of Ven/Mer/Moon/Jup
_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})


def _f(crow: pd.Series) -> dict | None:
    if pd.isna(crow.get("asc_sign")):
        return None
    asc = int(crow["asc_sign"])
    sign = {g: int(crow[f"{g.lower()}_sign"]) for g in _GRAHAS
            if pd.notna(crow.get(f"{g.lower()}_sign"))}
    house = {g: int(crow[f"{g.lower()}_house"]) for g in _GRAHAS
             if pd.notna(crow.get(f"{g.lower()}_house"))}
    if len(sign) < 9:
        return None
    lord = {h: SIGN_RULERS[_sign_in_house(h, asc)] for h in (1, 2, 7, 8, 11)}
    return {"asc": asc, "sign": sign, "house": house, "lord": lord}


def _seventh_from(sign: int) -> int:
    return ((sign + 5) % 12) + 1


def _yuti(f, a: str, b: str) -> bool:
    return a != b and f["sign"].get(a) == f["sign"].get(b)


def _venus_dignified(f) -> bool:
    try:
        return dignity_state("Venus", f["sign"]["Venus"]) in {"exalted", "own"}
    except (KeyError, ValueError):
        return False


# verse → (predicate, predicted ages)
YOGAS: Final[dict[str, tuple[Callable[[dict], bool], tuple[int, ...]]]] = {
    "18.22 7L in benefic sign/9H + Venus exalt-own → 5,9": (
        lambda f: ((f["sign"].get(f["lord"][7]) in _BENEFIC_SIGNS
                    or f["house"].get(f["lord"][7]) == 9) and _venus_dignified(f)),
        (5, 9)),
    "18.23 Sun in 7H + dispositor yuti Venus → 7,11": (
        lambda f: (f["house"].get("Sun") == 7
                   and _yuti(f, SIGN_RULERS[f["sign"]["Sun"]], "Venus")),
        (7, 11)),
    "18.24 Venus in 2H + 7L in 11H → 10,16": (
        lambda f: (f["house"].get("Venus") == 2
                   and f["house"].get(f["lord"][7]) == 11),
        (10, 16)),
    "18.25 Venus kendra + 1L in Cap/Aqu → 11": (
        lambda f: (f["house"].get("Venus") in _KENDRA
                   and f["sign"].get(f["lord"][1]) in (10, 11)),
        (11,)),
    "18.26 Venus kendra + Saturn 7th-from-Venus → 12,19": (
        lambda f: (f["house"].get("Venus") in _KENDRA
                   and f["sign"].get("Saturn") == _seventh_from(f["sign"]["Venus"])),
        (12, 19)),
    "18.27 Venus 7th-from-Moon + Saturn 7th-from-Venus → 18": (
        lambda f: (f["sign"].get("Venus") == _seventh_from(f["sign"]["Moon"])
                   and f["sign"].get("Saturn") == _seventh_from(f["sign"]["Venus"])),
        (18,)),
    "18.28 2L in 11H + 1L in 10H → 15": (
        lambda f: (f["house"].get(f["lord"][2]) == 11
                   and f["house"].get(f["lord"][1]) == 10),
        (15,)),
    "18.29 2L–11L exchange → 13": (
        lambda f: (f["lord"][2] != f["lord"][11]
                   and f["house"].get(f["lord"][2]) == 11
                   and f["house"].get(f["lord"][11]) == 2),
        (13,)),
    "18.30 Venus in 2H + dispositor yuti Mars → 22,27": (
        lambda f: (f["house"].get("Venus") == 2
                   and _yuti(f, SIGN_RULERS[f["sign"]["Venus"]], "Mars")),
        (22, 27)),
    "18.33 Venus in 5H + Rahu in 5H/9H → 31,33": (
        lambda f: (f["house"].get("Venus") == 5
                   and f["house"].get("Rahu") in (5, 9)),
        (31, 33)),
    "18.34 Venus in 1H + 7L in 7H → 27,30": (
        lambda f: (f["house"].get("Venus") == 1
                   and f["house"].get(f["lord"][7]) == 7),
        (27, 30)),
}


def _err(age: float, preds: tuple[int, ...]) -> float:
    return min(abs(age - p) for p in preds)


def run(data_dir: Path, out_dir: Path, *, k: int = 2000, seed: int = 0) -> dict:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    mar = events[(events["event_class"].astype(str).str.lower() == "marriage")
                 & events["age_at_event_years"].notna()]
    mar = mar.sort_values("age_at_event_years").groupby("person_id").head(1)
    ages_by_pid = mar.set_index("person_id")["age_at_event_years"].astype(float)
    pool = ages_by_pid.to_numpy()

    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    facts = {pid: _f(cidx.loc[pid]) for pid in ages_by_pid.index if pid in cidx.index}
    facts = {p: f for p, f in facts.items() if f is not None}

    rng = np.random.default_rng(seed)
    rows, pooled_obs, pooled_null = [], [], []
    for name, (pred, preds) in YOGAS.items():
        matched = [p for p, f in facts.items() if pred(f)]
        if len(matched) < 8:
            rows.append({"yoga": name, "n": len(matched), "note": "too few matches"})
            continue
        obs = np.array([_err(float(ages_by_pid[p]), preds) for p in matched])
        null = np.array([
            np.mean([_err(a, preds) for a in rng.choice(pool, size=len(matched))])
            for _ in range(k)])
        o = float(obs.mean())
        pv = float(((null <= o).sum() + 1) / (k + 1))
        rows.append({"yoga": name, "n": len(matched),
                     "mean_abs_err_yrs": round(o, 2),
                     "null_mean_err_yrs": round(float(null.mean()), 2),
                     "p_better_than_chance": round(pv, 4),
                     "mean_obs_age": round(float(np.mean([ages_by_pid[p] for p in matched])), 1),
                     "predicted_ages": list(preds)})
        pooled_obs.append(o - float(null.mean()))
        pooled_null.append(float(null.std()))

    results = {"n_married_with_charts": len(facts), "k": k, "yogas": rows,
               "corpus_mean_marriage_age": round(float(pool.mean()), 1)}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "bphs_fixed_age.json").write_text(json.dumps(results, indent=2),
                                                 encoding="utf-8")
    (out_dir / "bphs_fixed_age.md").write_text(_report(results), encoding="utf-8")
    logger.info("fixed-age yogas: %d encoded, %d with n>=8",
                len(YOGAS), sum(1 for r in rows if "mean_abs_err_yrs" in r))
    return results


def _report(r: dict) -> str:
    L = ["# BPHS 18.22–34 fixed-age marriage yogas — tested directly", "",
         f"Among the {r['n_married_with_charts']} married natives with full charts "
         f"(corpus mean first-marriage age {r['corpus_mean_marriage_age']}): for each "
         "configuration, is the observed first-marriage age closer to the verse's "
         "predicted age(s) than ages drawn at random from the corpus distribution? "
         f"(permutation K={r['k']}; p < 0.05 ⇒ the verse beats chance)", "",
         "| yoga (verse → predicted ages) | n | mean |err| (yrs) | chance |err| | p | mean obs. age |",
         "|---|---:|---:|---:|---:|---:|"]
    for row in r["yogas"]:
        if "mean_abs_err_yrs" not in row:
            L.append(f"| {row['yoga']} | {row['n']} | — | — | — | (too few) |")
            continue
        star = " ✦" if row["p_better_than_chance"] < 0.05 else ""
        L.append(f"| {row['yoga']}{star} | {row['n']} | **{row['mean_abs_err_yrs']}** | "
                 f"{row['null_mean_err_yrs']} | {row['p_better_than_chance']:.3g} | "
                 f"{row['mean_obs_age']} |")
    L += ["", "## Reading", "",
          "- mean |err| ≈ chance |err| ⇒ the configuration's natives marry no closer "
          "to the predicted age than anyone else — the table carries no signal.",
          "- The child-age verses (5–16) are expected to fail catastrophically on a "
          "modern corpus: their predicted ages reflect the child-marriage norms of "
          "the text's era — direct evidence the tables encode social custom, not "
          "celestial law.", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=Path("/tmp/la_run"))
    ap.add_argument("--out", type=Path, default=Path("data/ml_runs/lunarastro_dignity"))
    ap.add_argument("--k", type=int, default=2000)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")
    res = run(args.data_dir, args.out, k=args.k)
    for row in res["yogas"]:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
