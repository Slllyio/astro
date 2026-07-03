"""The Triple Lock — joint validation of Raman's conjunctional death claim.

The doctrine under test (RUN3_PREREG.md §1): *death occurs when (1) a maraka
dasha runs (MD or AD lord among the lords of the 2nd/7th from lagna), (2) a
Saturn/Jupiter gochara trigger is live (T1 sade sati | T2 Saturn in natal 8H |
T3 double transit on 8H), and (3) the age lies in the chart's promised
ayurdaya band.* Run 1 (Wikidata) refuted the house-independent marginals;
run 2 (ADB Wayback) refuted the house-based maraka marginals; run 3 tests the
CONJUNCTION — the form practitioners actually claim — plus the two legs never
tested (gochara, ayurdaya).

## Statistics

Identical machinery to runs 1–2: per person the death-moment indicator is
Bernoulli under the PRIMARY permutation / shuffled-age null (one fixed-seed
sample of ages from the corpus's empirical age-at-death distribution, shared
by every person and every leg). Because all three legs are evaluated at the
SAME sampled ages, the joint null probability ``p_i = (a1 & a2 & a3).mean()``
carries the full between-leg dependence for free. Counts are
Poisson-binomial → exact z / one-sided p (``population_validate._pb_stats``).
The exposure null is not computed (run 1 proved it length-biased).

Primary tests (4, Bonferroni α = 0.01/4; thresholds in run3_gate.toml):
    leg1_maraka (md_or_ad)   RR ≥ 1.20
    leg2_gochara (T1|T2|T3)  RR ≥ 1.20
    leg3_ayurdaya (band)     RR ≥ 1.20
    triple_lock (1∧2∧3)      RR ≥ 1.50   (the conjunctional claim is strong)

Pre-listed secondary rows (descriptive; cannot promote/refute): leg1 md-only /
ad-only, T1/T2/T3 singles, T4-aggravated joint, the three pairwise
conjunctions, and the ayurdaya confusion matrix + Cohen's κ.

Preflight hard gate: re-pairing persons with shuffled death ages must collapse
every RR to ≈ 1 (the population form of stage_d's shuffled-times check).

Usage:
    python -m app.medini.ml.raman_saab.triple_lock \
        --corpus data/raman_saab/death_corpus_run3.parquet \
        --out data/ml_runs/raman_saab/run3
"""
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab import gochara_death as G
from app.medini.ml.raman_saab import population_validate as PV
from app.medini.ml.raman_saab.ayurdaya import (
    AyuBand, band_of_age, compute_ayurdaya,
)
from app.medini.ml.raman_saab.kundali import Kundali, cast_kundali, _nth_sign
from app.medini.ml.raman_saab.transit_table import get_table

logger = logging.getLogger(__name__)

_SEED = 20260703
_PERM_SAMPLES = 1000
_DAYS_PER_YEAR = D.DAYS_PER_VEDIC_YEAR


@dataclass
class PersonContext:
    """Everything the Triple-Lock indicators need for one person."""
    person_id: str
    birth_jd: float
    death_jd: float
    # dasha timeline (searchsorted arrays, as in population_validate)
    ad_start: np.ndarray
    ad_lord: np.ndarray
    ad_pmd_lord: np.ndarray
    # chart-derived
    asc_sign: int
    moon_sign: int
    maraka_mask: np.ndarray      # (9,) bool over PV lord indexing
    ayu_band: int                # AyuBand value
    rodden: str
    lat: float


# ── person construction ─────────────────────────────────────────────────────

def _build_person(row: pd.Series, *, jitter_minutes: float = 0.0,
                  fixed_hour: float | None = None) -> PersonContext | None:
    try:
        y, m, d = (int(x) for x in str(row["dob"]).split("-"))
        hh, mm = (int(x) for x in str(row["tob"]).split(":")[:2])
    except (ValueError, AttributeError):
        return None
    if fixed_hour is not None:
        hh, mm = int(fixed_hour), int(round((fixed_hour % 1) * 60))
    if jitter_minutes:
        total = hh * 60 + mm + jitter_minutes
        total = max(0.0, min(24 * 60 - 1, total))
        hh, mm = int(total // 60), int(total % 60)
    k = cast_kundali(y, m, d, hh, mm, float(row["tz_offset"]),
                     float(row["lat"]), float(row["lon"]))
    if k is None:
        return None
    death_jd = swe.julday(*(int(x) for x in str(row["dod"]).split("-")),
                          12.0, swe.GREG_CAL)
    if not (365.0 < death_jd - k.birth_jd <= 120 * 366.0):
        return None
    try:
        ayu = compute_ayurdaya(k, float(row["lat"]), float(row["lon"]))
    except RuntimeError:
        return None  # sunrise failure (counted by caller via None)
    mds = D.md_intervals(k.moon_longitude, k.birth_jd)
    ad_start, ad_lord, ad_pmd = [], [], []
    for md in mds:
        for ad in D.ad_intervals_in_md(md):
            ad_start.append(ad.start_jd)
            ad_lord.append(PV._LORD_IDX[ad.lord])
            ad_pmd.append(PV._LORD_IDX[md.lord])
    maraka_mask = np.zeros(PV._N, dtype=bool)
    for L in k.maraka_lords:
        maraka_mask[PV._LORD_IDX[L]] = True
    return PersonContext(
        person_id=str(row.get("person_id", "")),
        birth_jd=k.birth_jd, death_jd=death_jd,
        ad_start=np.array(ad_start),
        ad_lord=np.array(ad_lord, dtype=np.int8),
        ad_pmd_lord=np.array(ad_pmd, dtype=np.int8),
        asc_sign=k.lagna_sign,
        moon_sign=_nth_sign(k.lagna_sign, k.planet_house["Moon"]),
        maraka_mask=maraka_mask,
        ayu_band=int(ayu.band),
        rodden=str(row.get("rodden", "")),
        lat=float(row["lat"]),
    )


# ── per-person indicator vectors at arbitrary JDs ────────────────────────────

def _indicators_at(p: PersonContext, jds: np.ndarray,
                   sat_signs: np.ndarray, jup_signs: np.ndarray,
                   ) -> dict[str, np.ndarray]:
    """Boolean vectors for every primary/secondary condition at ``jds``.

    ``sat_signs``/``jup_signs`` are the transit signs at ``jds`` (from the
    ingress tables) — passed in so callers batch the lookups.
    """
    md_at = PV._lord_at(jds, p.ad_start, p.ad_pmd_lord)
    ad_at = PV._lord_at(jds, p.ad_start, p.ad_lord)
    l1_md = p.maraka_mask[md_at]
    l1_ad = p.maraka_mask[ad_at]
    l1 = l1_md | l1_ad
    t1 = G.t1_sade_sati(sat_signs, p.moon_sign)
    t2 = G.t2_saturn_in_8h(sat_signs, p.asc_sign)
    t3 = G.t3_double_transit_8h(sat_signs, jup_signs, p.asc_sign)
    t4 = G.t4_no_protective_jupiter(jup_signs, p.moon_sign)
    l2 = t1 | t2 | t3
    ages = (jds - p.birth_jd) / _DAYS_PER_YEAR
    l3 = np.array([int(band_of_age(a)) for a in ages]) == p.ayu_band
    return {
        "leg1_maraka": l1, "leg1_md": l1_md, "leg1_ad": l1_ad,
        "leg2_gochara": l2, "t1_sade_sati": t1, "t2_saturn_8h": t2,
        "t3_double_transit_8h": t3,
        "leg3_ayurdaya": l3,
        "triple_lock": l1 & l2 & l3,
        "triple_plus_t4": l1 & l2 & l3 & t4,
        "leg1_and_leg2": l1 & l2,
        "leg1_and_leg3": l1 & l3,
        "leg2_and_leg3": l2 & l3,
    }


_PRIMARY: tuple[str, ...] = ("leg1_maraka", "leg2_gochara", "leg3_ayurdaya",
                             "triple_lock")
_SECONDARY: tuple[str, ...] = ("leg1_md", "leg1_ad", "t1_sade_sati",
                               "t2_saturn_8h", "t3_double_transit_8h",
                               "triple_plus_t4", "leg1_and_leg2",
                               "leg1_and_leg3", "leg2_and_leg3")


def evaluate(people: list[PersonContext], sample_ages_days: np.ndarray,
             *, death_ages_override: np.ndarray | None = None) -> dict:
    """Observed-vs-null evaluation for every test.

    ``death_ages_override`` (same length as people) replaces each person's
    true death age — used by the preflight shuffled-pairing collapse check.
    """
    sat_t, jup_t = get_table("Saturn"), get_table("Jupiter")
    tests = _PRIMARY + _SECONDARY
    obs = {t: 0 for t in tests}
    E = {t: 0.0 for t in tests}
    var = {t: 0.0 for t in tests}
    band_pred, band_obs = [], []
    for i, p in enumerate(people):
        # null sample
        jds = p.birth_jd + sample_ages_days
        ind = _indicators_at(p, jds, sat_t.sign_at(jds), jup_t.sign_at(jds))
        # observed moment
        if death_ages_override is not None:
            djd = np.array([p.birth_jd + death_ages_override[i]])
        else:
            djd = np.array([p.death_jd])
        oind = _indicators_at(p, djd, sat_t.sign_at(djd), jup_t.sign_at(djd))
        for t in tests:
            pi = float(ind[t].mean())
            E[t] += pi
            var[t] += pi * (1.0 - pi)
            obs[t] += int(oind[t][0])
        band_pred.append(p.ayu_band)
        band_obs.append(int(band_of_age(
            float((djd[0] - p.birth_jd) / _DAYS_PER_YEAR))))

    rows = []
    for t in tests:
        z, p_up = PV._pb_stats(obs[t], E[t], var[t], "enrich")
        rows.append({
            "test": t, "tier": "primary" if t in _PRIMARY else "secondary",
            "null": "permutation", "n": len(people),
            "observed": obs[t], "expected": round(E[t], 2),
            "var": round(var[t], 2),
            "rr": round(obs[t] / E[t], 4) if E[t] > 0 else None,
            "z": round(z, 3), "p_one_sided": p_up,
        })

    # Ayurdaya confusion matrix + Cohen's kappa (secondary).
    cm = np.zeros((3, 3), dtype=int)
    for pr, ob in zip(band_pred, band_obs):
        cm[pr, ob] += 1
    n = cm.sum()
    po = np.trace(cm) / n if n else 0.0
    pe = float((cm.sum(axis=1) * cm.sum(axis=0)).sum()) / (n * n) if n else 0.0
    kappa = (po - pe) / (1 - pe) if pe < 1 else 0.0
    confusion = {
        "matrix_pred_x_obs": cm.tolist(),
        "bands": [b.name for b in AyuBand],
        "accuracy": round(po, 4), "chance_pe": round(pe, 4),
        "cohens_kappa": round(kappa, 4),
    }
    return {"rows": rows, "ayurdaya_confusion": confusion}


# ── pipeline ────────────────────────────────────────────────────────────────

def _build_people(df: pd.DataFrame, **kw) -> tuple[list[PersonContext], dict]:
    people, dropped = [], 0
    for _, row in df.iterrows():
        p = _build_person(row, **kw)
        if p is None:
            dropped += 1
        else:
            people.append(p)
    return people, {"cast": len(people), "dropped": dropped}


def _primary_summary(result: dict) -> dict[str, dict]:
    return {r["test"]: {"rr": r["rr"], "z": r["z"], "p": r["p_one_sided"]}
            for r in result["rows"] if r["tier"] == "primary"}


def run(corpus: Path, out_dir: Path, *, robustness: bool = True,
        smoke_n: int | None = None) -> dict:
    df = pd.read_parquet(corpus)
    if smoke_n:
        df = df.sample(n=min(smoke_n, len(df)), random_state=_SEED)
    people, build_stats = _build_people(df)
    logger.info("built %d person contexts (%d dropped)",
                len(people), build_stats["dropped"])

    ages = np.array([p.death_jd - p.birth_jd for p in people])
    rng = np.random.default_rng(_SEED)
    sample_ages = rng.choice(ages, size=min(_PERM_SAMPLES, len(ages)),
                             replace=False)

    # ── PREFLIGHT (hard gate): shuffled person<->death-age pairing must
    # collapse every RR to ~1.
    shuffled = rng.permutation(ages)
    pre = evaluate(people, sample_ages, death_ages_override=shuffled)
    # Collapse criterion: under the shuffled pairing each primary count is a
    # draw from its own Poisson-binomial null, so RR fluctuates with
    # sd = sqrt(var)/E (~0.09 for the joint test at full N). A fixed RR band
    # would false-alarm on correct nulls; the right check is |z| <= 3.
    pre_bad = [r for r in pre["rows"]
               if r["tier"] == "primary" and abs(r["z"]) > 3.0]
    preflight = {"primary": _primary_summary(pre),
                 "pass": not pre_bad}
    if pre_bad:
        logger.error("PREFLIGHT FAIL: %s", pre_bad)

    # ── main evaluation
    main_res = evaluate(people, sample_ages)

    result = {
        "corpus": str(corpus), "n_persons": len(people),
        "build_stats": build_stats,
        "perm_samples": int(len(sample_ages)),
        "seed": _SEED,
        "n_primary_tests": len(_PRIMARY),
        "bonferroni_alpha": 0.01 / len(_PRIMARY),
        "preflight_shuffled_pairing": preflight,
        "results": main_res["rows"],
        "ayurdaya_confusion": main_res["ayurdaya_confusion"],
        "robustness": {},
        "notes": [
            "PRIMARY null = permutation (shuffled age-at-death), shared "
            "sample across persons and legs; joint p_i from the same draws.",
            "Thresholds per run3_gate.toml: legs RR>=1.20, joint RR>=1.50.",
            "Single corpus -> ratchet ceiling 'provisional'.",
        ],
    }

    if robustness and preflight["pass"]:
        rob: dict = {}
        # Birth-time jitter ±15 min (Rodden A precision), 2 fixed seeds.
        for jseed in (1, 2):
            jrng = np.random.default_rng(_SEED + jseed)
            jit = jrng.uniform(-15.0, 15.0, size=len(df))
            jdf = df.reset_index(drop=True)
            jpeople = []
            flips = 0
            for i, (_, row) in enumerate(jdf.iterrows()):
                p = _build_person(row, jitter_minutes=float(jit[i]))
                if p is not None:
                    jpeople.append(p)
            base_by_id = {p.person_id: p for p in people}
            for p in jpeople:
                b = base_by_id.get(p.person_id)
                if b and (b.asc_sign != p.asc_sign
                          or b.ayu_band != p.ayu_band
                          or not np.array_equal(b.maraka_mask, p.maraka_mask)):
                    flips += 1
            jres = evaluate(jpeople, sample_ages)
            rob[f"jitter15_seed{jseed}"] = {
                "n": len(jpeople),
                "flip_fraction": round(flips / max(1, len(jpeople)), 4),
                "primary": _primary_summary(jres),
            }
        # Degenerate fixed-hour sweep (bridges run 1's no-time regime).
        for h in (0.0, 6.0, 12.0, 18.0):
            hpeople, _ = _build_people(df, fixed_hour=h)
            hres = evaluate(hpeople, sample_ages)
            rob[f"fixed_hour_{int(h):02d}"] = {
                "n": len(hpeople), "primary": _primary_summary(hres)}
        # Strata.
        for name, mask in (
            ("rodden_AA", df["rodden"] == "AA"),
            ("rodden_A", df["rodden"] == "A"),
            ("north_hemisphere", df["lat"] > 0),
            ("south_hemisphere", df["lat"] <= 0),
        ):
            sub = df[mask]
            if len(sub) < 100:
                rob[f"stratum_{name}"] = {"n": int(len(sub)),
                                          "note": "under 100; skipped"}
                continue
            speople, _ = _build_people(sub)
            sres = evaluate(speople, sample_ages)
            rob[f"stratum_{name}"] = {"n": len(speople),
                                      "primary": _primary_summary(sres)}
        result["robustness"] = rob

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "triple_lock_validation.json").write_text(
        json.dumps(result, indent=2))
    logger.info("wrote %s", out_dir / "triple_lock_validation.json")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path,
                   default=Path("data/raman_saab/death_corpus_run3.parquet"))
    p.add_argument("--out", type=Path,
                   default=Path("data/ml_runs/raman_saab/run3"))
    p.add_argument("--smoke", type=int, default=None,
                   help="random subsample for a smoke run")
    p.add_argument("--no-robustness", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run(args.corpus, args.out, robustness=not args.no_robustness,
                 smoke_n=args.smoke)
    print(f"\nN={result['n_persons']}  preflight pass="
          f"{result['preflight_shuffled_pairing']['pass']}  "
          f"alpha={result['bonferroni_alpha']:.4f}")
    print(f"{'test':<24}{'tier':<11}{'RR':>8}{'z':>8}{'p':>12}")
    for r in result["results"]:
        rr = f"{r['rr']:.3f}" if r["rr"] is not None else "nan"
        print(f"{r['test']:<24}{r['tier']:<11}{rr:>8}{r['z']:>8.2f}"
              f"{r['p_one_sided']:>12.2e}")
    cm = result["ayurdaya_confusion"]
    print(f"\nayurdaya: accuracy={cm['accuracy']}  kappa={cm['cohens_kappa']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
