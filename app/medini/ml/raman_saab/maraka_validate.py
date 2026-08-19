"""House-based maraka validation on the timed-birth (Rodden AA/A/B) corpus.

This is the test the Wikidata run could not do: with real birth times the
lagna is known, so the lord sets are **chart-dependent** — each person has
their own maraka lords (2nd & 7th lords from lagna), 8th lord, etc.

Statistics are identical to ``population_validate``: the death-moment lord
membership is Bernoulli per person, the count is Poisson-binomial, and the
PRIMARY null is the permutation / shuffled-age null (each person's own
timeline evaluated at ages drawn from the corpus's empirical age-at-death
distribution) — controlling the dasha-length endpoint bias and the age
confound. The per-person lord set S_i rides along unchanged under the null,
so chart-dependence costs nothing statistically.

Also runs, as a **cross-corpus replication probe** of run 1, the fixed-lord
Saturn/malefic rules on this independent corpus.

Natal 8th-house longevity tests (Saturn/Mars/Rahu/Ketu/Jupiter in 8H vs age
at death) are cohort-restricted to births ≤ 1900: anyone born later could
still have been alive at scrape time, so late cohorts contain only
young-deaths (right-truncation) and would fake a "died younger" signal.

Usage:
    python -m app.medini.ml.raman_saab.maraka_validate \
        --corpus app/medini/data/raman_saab/adb_timed_death_corpus.parquet \
        --out data/ml_runs/raman_saab
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe
from scipy.stats import norm

from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab import population_validate as PV
from app.medini.ml.raman_saab.kundali import Kundali, cast_kundali
from app.medini.ml.raman_saab.rules import CANDIDATE_RULES, MARAKA_RULES

logger = logging.getLogger(__name__)

_SEED = 20260702
_PERM_SAMPLES = 1000

# Kundali -> lord set resolvers for the ChartRules.
_RESOLVERS = {
    "maraka_lords": lambda k: set(k.maraka_lords),
    "lord_8": lambda k: {k.lord_8},
    "maraka_and_8": lambda k: set(k.maraka_lords) | {k.lord_8},
    # Empty set when Saturn holds no maraka lordship -> that person can never
    # score a hit AND has null prob 0; they drop out of both O and E, which is
    # exactly the intended "restricted to charts where Saturn is maraka".
    "saturn_if_maraka": lambda k: ({"Saturn"} if "Saturn" in k.maraka_lords
                                   else set()),
}


def _death_jd(dod: str) -> float:
    y, m, d = (int(x) for x in dod.split("-"))
    return swe.julday(y, m, d, 12.0, swe.GREG_CAL)


def _load_people(corpus: Path) -> tuple[list[PV.PersonTimeline], list[Kundali],
                                        pd.DataFrame]:
    df = pd.read_parquet(corpus)
    timelines: list[PV.PersonTimeline] = []
    kundalis: list[Kundali] = []
    kept_rows = []
    for _, row in df.iterrows():
        try:
            y, m, d = (int(x) for x in str(row["dob"]).split("-"))
            hh, mm = (int(x) for x in str(row["tob"]).split(":")[:2])
        except (ValueError, AttributeError):
            continue
        k = cast_kundali(y, m, d, hh, mm, float(row["tz_offset"]),
                         float(row["lat"]), float(row["lon"]))
        if k is None:
            continue
        death_jd = _death_jd(str(row["dod"]))
        if death_jd - k.birth_jd <= 365 or death_jd - k.birth_jd > 120 * 366:
            continue
        mds = D.md_intervals(k.moon_longitude, k.birth_jd)
        md_start = np.array([iv.start_jd for iv in mds])
        md_lord = np.array([PV._LORD_IDX[iv.lord] for iv in mds], dtype=np.int8)
        ad_start, ad_lord, ad_pmd = [], [], []
        for md in mds:
            for ad in D.ad_intervals_in_md(md):
                ad_start.append(ad.start_jd)
                ad_lord.append(PV._LORD_IDX[ad.lord])
                ad_pmd.append(PV._LORD_IDX[md.lord])
        timelines.append(PV.PersonTimeline(
            k.birth_jd, death_jd, md_start, md_lord,
            np.array(ad_start), np.array(ad_lord, dtype=np.int8),
            np.array(ad_pmd, dtype=np.int8)))
        kundalis.append(k)
        kept_rows.append(row)
    kept = pd.DataFrame(kept_rows).reset_index(drop=True)
    logger.info("cast %d/%d timed charts", len(kundalis), len(df))
    return timelines, kundalis, kept


def _person_masks(kundalis: list[Kundali], resolver: str) -> np.ndarray:
    """(n, 9) bool matrix: person i's rule lord-set membership per lord."""
    fn = _RESOLVERS[resolver]
    masks = np.zeros((len(kundalis), PV._N), dtype=bool)
    for i, k in enumerate(kundalis):
        for L in fn(k):
            masks[i, PV._LORD_IDX[L]] = True
    return masks


def evaluate_chart_rules(
    timelines: list[PV.PersonTimeline], kundalis: list[Kundali],
    sample_ages_days: np.ndarray,
) -> list[dict]:
    n = len(timelines)
    obs_md = np.array([PV._lord_at(np.array([t.death_jd]), t.md_start, t.md_lord)[0]
                       for t in timelines])
    obs_ad = np.array([PV._lord_at(np.array([t.death_jd]), t.ad_start, t.ad_lord)[0]
                       for t in timelines])
    # Per-person permutation samples (shared age draw).
    samples = []  # per person: (2, k) [parent-md lord, ad lord]
    for t in timelines:
        jds = t.birth_jd + sample_ages_days
        pmd_at = PV._lord_at(jds, t.ad_start, t.ad_pmd_lord)
        ad_at = PV._lord_at(jds, t.ad_start, t.ad_lord)
        samples.append(np.stack([pmd_at, ad_at]))

    results: list[dict] = []
    for rule in MARAKA_RULES:
        masks = _person_masks(kundalis, rule.resolver)  # (n, 9)
        n_eligible = int((masks.any(axis=1)).sum())
        for level in rule.levels:
            obs_flags = np.zeros(n, dtype=bool)
            probs = np.zeros(n)
            for i in range(n):
                Smask = masks[i]
                if not Smask.any():
                    continue  # ineligible person: O contribution 0, p_i 0
                md_hit = Smask[obs_md[i]]
                ad_hit = Smask[obs_ad[i]]
                obs_flags[i] = (md_hit if level == "md"
                                else ad_hit if level == "ad"
                                else (md_hit or ad_hit))
                s = samples[i]
                if level == "md":
                    probs[i] = Smask[s[0]].mean()
                elif level == "ad":
                    probs[i] = Smask[s[1]].mean()
                else:
                    probs[i] = (Smask[s[0]] | Smask[s[1]]).mean()
            O = int(obs_flags.sum())
            E = float(probs.sum())
            var = float((probs * (1 - probs)).sum())
            z, p = PV._pb_stats(O, E, var, rule.direction)
            results.append({
                "rule_id": rule.rule_id, "level": level,
                "direction": rule.direction, "null": "permutation",
                "n": n_eligible, "observed": O, "expected": round(E, 2),
                "rr": round(O / E, 4) if E > 0 else None,
                "z": round(z, 3), "p_one_sided": p,
            })
    return results


def natal_8h_longevity(kundalis: list[Kundali], kept: pd.DataFrame,
                       cohort_max_dob: str = "1900-12-31") -> list[dict]:
    """Age-at-death difference for 8H occupancy, right-truncation-safe cohort."""
    dob = pd.to_datetime(kept["dob"], errors="coerce")
    dod = pd.to_datetime(kept["dod"], errors="coerce")
    age = ((dod - dob).dt.days / 365.2425).to_numpy()
    in_cohort = (dob <= pd.Timestamp(cohort_max_dob)).to_numpy()
    rows = []
    for planet in ("Saturn", "Mars", "Rahu", "Ketu", "Jupiter", "Venus"):
        flag = np.array([k.planet_house.get(planet) == 8 for k in kundalis])
        a = age[in_cohort & flag]
        b = age[in_cohort & ~flag]
        if len(a) < 30:
            rows.append({"planet": planet, "n_in_8h": int(len(a)),
                         "note": "underpowered (<30)"})
            continue
        # Welch z, two-sided.
        se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        z = (a.mean() - b.mean()) / se if se > 0 else 0.0
        rows.append({
            "planet": planet, "n_in_8h": int(len(a)), "n_rest": int(len(b)),
            "mean_age_in_8h": round(float(a.mean()), 2),
            "mean_age_rest": round(float(b.mean()), 2),
            "delta_years": round(float(a.mean() - b.mean()), 2),
            "z_two_sided": round(float(z), 3),
            "p_two_sided": float(2 * norm.sf(abs(z))),
        })
    return rows


def run(corpus: Path, out_dir: Path) -> dict:
    timelines, kundalis, kept = _load_people(corpus)
    ages = np.array([t.death_jd - t.birth_jd for t in timelines])
    rng = np.random.default_rng(_SEED)
    sample_ages = rng.choice(ages, size=min(_PERM_SAMPLES, len(ages)),
                             replace=False)

    chart_results = evaluate_chart_rules(timelines, kundalis, sample_ages)
    # Fixed-lord replication of run 1 on this independent corpus.
    fixed_results, lord_rows = PV.evaluate(timelines, sample_ages,
                                           rules=CANDIDATE_RULES)
    natal_rows = natal_8h_longevity(kundalis, kept)

    n_tests = sum(len(r.levels) for r in MARAKA_RULES)
    result = {
        "corpus": str(corpus), "n_persons": len(timelines),
        "corpus_kind": "ADB timed births (Rodden AA/A/B) via Wayback",
        "perm_samples": len(sample_ages),
        "n_chart_rule_tests": n_tests,
        "bonferroni_alpha": 0.01 / n_tests,
        "chart_rule_results": chart_results,
        "fixed_rule_replication": [asdict(r) for r in fixed_results
                                   if r.null == "permutation"],
        "lord_results": lord_rows,
        "natal_8h_longevity": natal_rows,
        "notes": [
            "PRIMARY null = permutation (shuffled age-at-death) — as in run 1.",
            "Chart rules use per-person lord sets from the real lagna "
            "(Rodden AA/A/B birth times, ADB tz offsets incl. LMT).",
            "natal_8h tests restricted to births <= 1900 to avoid "
            "right-truncation (late cohorts contain only young deaths).",
            "Second, independent corpus — provides the G2 replication axis "
            "for run 1's fixed-lord rules.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "maraka_validation.json").write_text(json.dumps(result, indent=2))
    logger.info("wrote %s", out_dir / "maraka_validation.json")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path,
                   default=Path("app/medini/data/raman_saab/adb_timed_death_corpus.parquet"))
    p.add_argument("--out", type=Path, default=Path("data/ml_runs/raman_saab"))
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run(args.corpus, args.out)
    print(f"\nN={result['n_persons']} timed charts   "
          f"Bonferroni α={result['bonferroni_alpha']:.2e}")
    print(f"{'rule':<32}{'lvl':<9}{'n_elig':>7}{'RR':>8}{'z':>8}{'p':>11}")
    for r in result["chart_rule_results"]:
        rr = f"{r['rr']:.3f}" if r["rr"] is not None else "nan"
        print(f"{r['rule_id']:<32}{r['level']:<9}{r['n']:>7}{rr:>8}"
              f"{r['z']:>8.2f}{r['p_one_sided']:>11.2e}")
    print("\nNatal 8H longevity (births <=1900, two-sided):")
    for r in result["natal_8h_longevity"]:
        if "delta_years" in r:
            print(f"  {r['planet']:<9} in 8H: n={r['n_in_8h']:>4}  "
                  f"Δage={r['delta_years']:+.2f}y  z={r['z_two_sided']:+.2f}  "
                  f"p={r['p_two_sided']:.3f}")
        else:
            print(f"  {r['planet']:<9} in 8H: n={r['n_in_8h']} — {r['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
