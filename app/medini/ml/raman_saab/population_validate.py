"""Population validation of the Raman death-timing (dasha) rules.

For each person (birth date, death date, birthplace) we compute the Vimshottari
Mahadasha / Antardasha lord active **at death**, and test whether a rule's lord
set S is enriched at death relative to a null.

## Two nulls (the second is the honest one)

1. **Exposure null (DESCRIPTIVE ONLY — length-biased):** P(death-lord ∈ S) =
   fraction of the lived lifespan spent under S. This has an *endpoint
   length-bias*: the death dasha is only partially lived (death interrupts it),
   so it contributes less to exposure than its full length while still scoring a
   full "observed" hit — inflating RR for long dashas (Venus 20y, Saturn 19y,
   Jupiter 16y) regardless of doctrine. Reported but NOT used for verdicts.

2. **Permutation / shuffled-age null (PRIMARY):** evaluate each person's own
   dasha timeline at ages drawn from the population's empirical age-at-death
   distribution. This preserves (a) each chart's dasha-length structure and
   (b) the age-at-death distribution, breaking only the specific pairing of a
   chart with its true death age. It therefore controls the length-bias AND the
   age confound simultaneously — it is the population form of the repo's own
   ``stage_d_preflight.check_shuffled_times_collapse``. A rule is real only if
   it enriches beyond THIS null.

Under either null the per-person indicator is Bernoulli(p_i), so the count O is
Poisson-binomial → O ≈ Normal(Σp_i, Σp_i(1−p_i)), giving exact z and one-sided
p with no Monte Carlo on the test itself (the null p_i come from a fixed-seed
age sample).

Limitations (docs/death_timing_findings.md §6): birth times unknown (assumed
hour + sensitivity sweep); single corpus (Wikidata) so max ratchet status is
`provisional`; house/lord maraka rules untestable without an ascendant.

Usage:
    python -m app.medini.ml.raman_saab.population_validate \
        --corpus app/medini/data/raman_saab/death_corpus.parquet \
        --out data/ml_runs/raman_saab
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe
from scipy.stats import norm

from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab.rules import CANDIDATE_RULES, Rule

logger = logging.getLogger(__name__)

# Fixed lord ordering for int-coding.
LORDS: tuple[str, ...] = D.ALL_LORDS
_LORD_IDX: dict[str, int] = {L: i for i, L in enumerate(LORDS)}
_N = len(LORDS)

_PERM_SAMPLES = 1000  # ages sampled from the empirical distribution for the null
_SEED = 20260702


@dataclass
class PersonTimeline:
    birth_jd: float
    death_jd: float
    md_start: np.ndarray   # sorted interval starts (float)
    md_lord: np.ndarray    # int-coded lord per md interval
    ad_start: np.ndarray
    ad_lord: np.ndarray
    ad_pmd_lord: np.ndarray  # parent MD lord per AD interval (for md_or_ad)


def _death_jd(dod: str) -> float:
    y, m, d = (int(x) for x in dod.split("-"))
    return swe.julday(y, m, d, 12.0, swe.GREG_CAL)


def _timeline(row: pd.Series, hour: float) -> PersonTimeline | None:
    try:
        y, m, d = (int(x) for x in str(row["dob"]).split("-"))
    except (ValueError, AttributeError):
        return None
    moon_lon, birth_jd = D.moon_longitude(y, m, d, hour, float(row["lon"]))
    death_jd = _death_jd(str(row["dod"]))
    if death_jd - birth_jd <= 0:
        return None
    mds = D.md_intervals(moon_lon, birth_jd)
    md_start = np.array([iv.start_jd for iv in mds], dtype=np.float64)
    md_lord = np.array([_LORD_IDX[iv.lord] for iv in mds], dtype=np.int8)
    ad_start_l, ad_lord_l, ad_pmd_l = [], [], []
    for md in mds:
        for ad in D.ad_intervals_in_md(md):
            ad_start_l.append(ad.start_jd)
            ad_lord_l.append(_LORD_IDX[ad.lord])
            ad_pmd_l.append(_LORD_IDX[md.lord])
    return PersonTimeline(
        birth_jd, death_jd,
        md_start, md_lord,
        np.array(ad_start_l, dtype=np.float64),
        np.array(ad_lord_l, dtype=np.int8),
        np.array(ad_pmd_l, dtype=np.int8),
    )


def _lord_at(jds: np.ndarray, starts: np.ndarray, lords: np.ndarray) -> np.ndarray:
    """Vectorised: lord index active at each jd (searchsorted on interval starts)."""
    idx = np.searchsorted(starts, jds, side="right") - 1
    idx = np.clip(idx, 0, len(lords) - 1)
    return lords[idx]


def _exposure_probs(tl: PersonTimeline) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (md_exp[N], ad_exp[N], and per-AD lived weights for md_or_ad).

    md_or_ad handled by caller via ad-level joint; here we return the AD lived
    weights plus ad_lord/ad_pmd already on the timeline.
    """
    span = tl.death_jd - tl.birth_jd
    # AD interval ends = next start, last ends at +inf effectively (clip to death)
    ad_end = np.empty_like(tl.ad_start)
    ad_end[:-1] = tl.ad_start[1:]
    ad_end[-1] = tl.ad_start[-1] + 1e9
    lo = np.maximum(tl.ad_start, tl.birth_jd)
    hi = np.minimum(ad_end, tl.death_jd)
    w = np.clip(hi - lo, 0, None) / span  # lived fraction per AD interval
    ad_exp = np.bincount(tl.ad_lord, weights=w, minlength=_N)
    # MD exposure = aggregate AD weights by parent md lord
    md_exp = np.bincount(tl.ad_pmd_lord, weights=w, minlength=_N)
    return md_exp, ad_exp, w


def _perm_probs(tl: PersonTimeline, sample_ages_days: np.ndarray
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Null probs from evaluating this timeline at population death-ages.

    Returns (p_md[N], p_ad[N], p_pmd_and_ad_joint) where the joint is captured
    by returning md-lord and ad-lord samples for md_or_ad union handling.
    """
    jds = tl.birth_jd + sample_ages_days
    md_at = _lord_at(jds, tl.md_start, tl.md_lord)
    ad_at = _lord_at(jds, tl.ad_start, tl.ad_lord)
    pmd_at = _lord_at(jds, tl.ad_start, tl.ad_pmd_lord)  # md lord via ad timeline
    k = len(jds)
    p_md = np.bincount(md_at, minlength=_N) / k
    p_ad = np.bincount(ad_at, minlength=_N) / k
    # store per-sample md/ad for union prob per rule (small: k ints)
    return p_md, p_ad, np.stack([pmd_at, ad_at])


@dataclass
class RuleResult:
    rule_id: str
    level: str
    direction: str
    null: str
    n: int
    observed: int
    expected: float
    rr: float
    z: float
    p_one_sided: float


def _pb_stats(O: float, E: float, var: float, direction: str) -> tuple[float, float]:
    if var <= 0:
        return 0.0, 0.5
    z = (O - E) / math.sqrt(var)
    p = float(norm.sf(z)) if direction == "enrich" else float(norm.cdf(z))
    return z, p


def evaluate(
    timelines: list[PersonTimeline], sample_ages_days: np.ndarray,
    rules: tuple[Rule, ...] = CANDIDATE_RULES,
) -> tuple[list[RuleResult], list[dict]]:
    n = len(timelines)
    # Observed death lords.
    obs_md = np.array([_lord_at(np.array([t.death_jd]), t.md_start, t.md_lord)[0]
                       for t in timelines])
    obs_ad = np.array([_lord_at(np.array([t.death_jd]), t.ad_start, t.ad_lord)[0]
                       for t in timelines])

    # Per-person null prob vectors under both nulls.
    exp_md = np.zeros((n, _N)); exp_ad = np.zeros((n, _N))
    exp_w = []  # list of (ad_lord, ad_pmd, w) via timeline for union
    perm_md = np.zeros((n, _N)); perm_ad = np.zeros((n, _N))
    perm_samples = []  # per person np.array shape (2, k): [pmd, ad]
    for i, t in enumerate(timelines):
        em, ea, w = _exposure_probs(t)
        exp_md[i] = em; exp_ad[i] = ea; exp_w.append(w)
        pm, pa, samp = _perm_probs(t, sample_ages_days)
        perm_md[i] = pm; perm_ad[i] = pa; perm_samples.append(samp)

    results: list[RuleResult] = []
    for rule in rules:
        S = np.array([_LORD_IDX[L] for L in rule.lords])
        Smask = np.zeros(_N, dtype=bool); Smask[S] = True
        for level in rule.levels:
            for null_name in ("permutation", "exposure"):
                # observed
                if level == "md":
                    obs = int(Smask[obs_md].sum())
                elif level == "ad":
                    obs = int(Smask[obs_ad].sum())
                else:  # md_or_ad
                    obs = int((Smask[obs_md] | Smask[obs_ad]).sum())
                # expected p_i per person
                if null_name == "exposure":
                    if level == "md":
                        p = exp_md[:, S].sum(axis=1)
                    elif level == "ad":
                        p = exp_ad[:, S].sum(axis=1)
                    else:
                        p = np.array([
                            w[(np.isin(timelines[i].ad_pmd_lord, S)
                               | np.isin(timelines[i].ad_lord, S))].sum()
                            for i, w in enumerate(exp_w)])
                else:  # permutation
                    if level == "md":
                        p = perm_md[:, S].sum(axis=1)
                    elif level == "ad":
                        p = perm_ad[:, S].sum(axis=1)
                    else:
                        p = np.array([
                            (Smask[s[0]] | Smask[s[1]]).mean()
                            for s in perm_samples])
                E = float(p.sum())
                var = float((p * (1 - p)).sum())
                z, pval = _pb_stats(obs, E, var, rule.direction)
                rr = obs / E if E > 0 else float("nan")
                results.append(RuleResult(
                    rule_id=rule.rule_id, level=level, direction=rule.direction,
                    null=null_name, n=n, observed=obs, expected=round(E, 2),
                    rr=round(rr, 4), z=round(z, 3), p_one_sided=pval))

    # Per-lord table (permutation null, both levels).
    lord_rows: list[dict] = []
    for level, obsarr, permarr in (("md", obs_md, perm_md), ("ad", obs_ad, perm_ad)):
        for L in LORDS:
            li = _LORD_IDX[L]
            obs = int((obsarr == li).sum())
            p = permarr[:, li]
            E = float(p.sum()); var = float((p * (1 - p)).sum())
            z, _ = _pb_stats(obs, E, var, "enrich")
            lord_rows.append({"lord": L, "level": level, "null": "permutation",
                              "observed": obs, "expected": round(E, 2),
                              "rr": round(obs / E, 4) if E > 0 else None,
                              "z": round(z, 3)})
    return results, lord_rows


def _build(df: pd.DataFrame, hour: float) -> list[PersonTimeline]:
    out = []
    for _, row in df.iterrows():
        t = _timeline(row, hour)
        if t is not None:
            out.append(t)
    return out


def run(corpus: Path, out_dir: Path, hour: float = 12.0,
        sweep_hours: tuple[float, ...] = (0.0, 6.0, 12.0, 18.0),
        min_age: float = 1.0) -> dict:
    df = pd.read_parquet(corpus)
    age = (pd.to_datetime(df["dod"]) - pd.to_datetime(df["dob"])).dt.days / 365.2425
    df = df[(age >= min_age) & (age <= 120)].reset_index(drop=True)
    age = age[(age >= min_age) & (age <= 120)].reset_index(drop=True)
    logger.info("corpus: %d persons", len(df))

    rng = np.random.default_rng(_SEED)
    ages_days = ((pd.to_datetime(df["dod"]) - pd.to_datetime(df["dob"])).dt.days
                 ).to_numpy(dtype=np.float64)
    sample_ages = rng.choice(ages_days, size=min(_PERM_SAMPLES, len(ages_days)),
                             replace=False)

    timelines = _build(df, hour)
    rule_results, lord_rows = evaluate(timelines, sample_ages)

    # Birth-time sensitivity (permutation null, headline rows only).
    sweep: dict[str, list] = {}
    for h in sweep_hours:
        tl_h = timelines if h == hour else _build(df, h)
        rr_h, _ = evaluate(tl_h, sample_ages)
        for r in rr_h:
            if r.null != "permutation":
                continue
            sweep.setdefault(f"{r.rule_id}|{r.level}", []).append(
                {"hour": h, "rr": r.rr, "z": r.z, "p": r.p_one_sided})

    # Age-stratified confound check (55-85), permutation null.
    band = df[(age >= 55) & (age <= 85)].reset_index(drop=True)
    tl_band = _build(band, hour)
    band_results, _ = evaluate(tl_band, sample_ages)

    n_tests = sum(len(r.levels) for r in CANDIDATE_RULES)
    result = {
        "corpus": str(corpus), "n_persons": len(timelines),
        "primary_hour_local": hour, "perm_samples": len(sample_ages),
        "n_rule_tests": n_tests, "bonferroni_alpha": 0.01 / n_tests,
        "rule_results": [asdict(r) for r in rule_results],
        "lord_results": lord_rows,
        "birth_time_sensitivity": sweep,
        "age_stratified_55_85": {
            "n_persons": len(tl_band),
            "rule_results": [asdict(r) for r in band_results
                             if r.null == "permutation"],
        },
        "notes": [
            "PRIMARY null = permutation (shuffled age-at-death); controls the "
            "dasha-length endpoint bias AND the age confound.",
            "Exposure null is descriptive only and length-biased — do not use "
            "for verdicts.",
            "Single corpus (Wikidata) -> max ratchet status 'provisional'.",
            "Birth times unknown; house/lord maraka rules not tested.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "population_validation.json").write_text(json.dumps(result, indent=2))
    logger.info("wrote %s", out_dir / "population_validation.json")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path,
                   default=Path("app/medini/data/raman_saab/death_corpus.parquet"))
    p.add_argument("--out", type=Path, default=Path("data/ml_runs/raman_saab"))
    p.add_argument("--hour", type=float, default=12.0)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = run(args.corpus, args.out, hour=args.hour)
    print(f"\nN={result['n_persons']}  Bonferroni α={result['bonferroni_alpha']:.2e}")
    print(f"{'rule':<34}{'lvl':<9}{'null':<12}{'RR':>7}{'z':>8}{'p':>11}")
    for r in result["rule_results"]:
        if r["null"] != "permutation":
            continue
        print(f"{r['rule_id']:<34}{r['level']:<9}{r['null']:<12}"
              f"{r['rr']:>7.3f}{r['z']:>8.2f}{r['p_one_sided']:>11.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
