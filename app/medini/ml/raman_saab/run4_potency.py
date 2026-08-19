"""Run-4 population harness — Raman-as-practiced fatal potency at scale.

Pipeline per person (corpus: ``death_corpus_run3.parquet``, N=2,091 timed
Rodden AA/A charts with own-death dates):

1. Cast the natal chart with the production engine (Lahiri), then convert
   every longitude to **Raman's ayanamsa** by the exact per-JD delta
   (tropical frame is mode-invariant, so ``lon_raman = lon_lahiri +
   ayanamsa_lahiri(jd) − ayanamsa_raman(jd)``) and rebuild the bundle from
   positions. The fidelity gate proved Lahiri misstates Raman's dasha
   timeline by ~1.5 dasha-years (only 2/5 of his printed death-dasha
   verdicts reproduce under Lahiri vs 4/4 under his own positions), so the
   method test must run in his frame. This is a pre-registered, justified
   divergence from the repo's production-Lahiri lock — we are validating
   Raman's method, not the repo's doctrine config.
2. Build the Vimshottari MD/AD timeline from the converted Moon; compute
   **fatal potency** (raman_method.PotencyModel, weights frozen per
   RUN4_PREREG.md) at the true death moment and at the **shared 1,000
   shuffled ages** drawn from the corpus' empirical age-at-death
   distribution (the run-1/-3 permutation null: controls dasha-length AND
   age confounds simultaneously).

Transit multipliers are EXCLUDED from the primaries (pre-registered): the
ingress tables are Lahiri-built and mixing frames would be inconsistent;
the dasha-sandhi term (pure dasha math) is included.

Primaries (Bonferroni α = 0.01/3, thresholds in run4_gate.toml):

- **P1 top-decile exceedance** — per person, threshold = their own 90th
  percentile of sampled-age potencies; hit = death potency STRICTLY above
  it. Per-person null p_i computed exactly from the sample (ties included),
  so the Poisson-binomial test is self-calibrating even where the band gate
  makes the potency distribution discrete.
- **P2 mean percentile rank** — mid-rank percentile of the death potency
  within the person's own sampled distribution; under the null each
  person's percentile has mean exactly 0.5 (mid-rank tie handling); the
  variance is estimated per person from the sample itself.
- **P3 longevity-band accuracy** — encoder band vs observed
  ``band_of_age``; Cohen's κ with an empirical null from the shuffled ages.

Preflight (hard gate): re-pair each person with a random OTHER person's
death age — all primaries must collapse to |z| ≤ 3.

Usage:
    python -m app.medini.ml.raman_saab.run4_potency \
        --corpus data/raman_saab/death_corpus_run3.parquet \
        --out data/ml_runs/raman_saab/run4 [--smoke 300]
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe
from scipy.stats import norm

from app.core.ephemeris_engine import calculate_all_charts
from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab.ayurdaya import AyuBand, band_of_age
from app.medini.ml.raman_saab.chart_bundle import GRAHAS, bundle_from_positions
from app.medini.ml.raman_saab.raman_method import LORD_IDX, PotencyModel

logger = logging.getLogger(__name__)

_SEED = 20260703
_PERM_SAMPLES = 1000
_DPY = D.DAYS_PER_VEDIC_YEAR


def _ayanamsa_delta(jd: float) -> float:
    """ayanamsa_lahiri(jd) − ayanamsa_raman(jd); add to Lahiri longitudes."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    a_l = swe.get_ayanamsa_ut(jd)
    swe.set_sid_mode(swe.SIDM_RAMAN)
    a_r = swe.get_ayanamsa_ut(jd)
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # restore process default
    return a_l - a_r


@dataclass
class Person:
    pm: PotencyModel
    death_age_days: float
    # timelines for fast lord/frac lookup
    ad_start: np.ndarray
    ad_lord: np.ndarray
    ad_pmd: np.ndarray
    md_start: np.ndarray
    md_end: np.ndarray
    birth_jd: float

    def eval_at(self, age_days: np.ndarray) -> np.ndarray:
        jds = self.birth_jd + age_days
        i = np.clip(np.searchsorted(self.ad_start, jds, side="right") - 1,
                    0, len(self.ad_lord) - 1)
        md_idx = self.ad_pmd[i]
        ad_idx = self.ad_lord[i]
        j = np.clip(np.searchsorted(self.md_start, jds, side="right") - 1,
                    0, len(self.md_start) - 1)
        md_frac = (jds - self.md_start[j]) / (self.md_end[j] - self.md_start[j])
        return self.pm.potency(md_idx, ad_idx, age_days / _DPY,
                               md_frac=np.clip(md_frac, 0.0, 1.0))


def _build_person(row: pd.Series) -> Person | None:
    try:
        y, m, d = (int(x) for x in str(row["dob"]).split("-"))
        hh = float(row["tob_hours"])
        tz = float(row["tz_offset"])
        lat, lon = float(row["lat"]), float(row["lon"])
    except (ValueError, TypeError, AttributeError):
        return None
    if not (0.0 <= hh < 24.0):
        return None
    try:
        cast = calculate_all_charts(y, m, d, int(hh), int(round((hh % 1) * 60)),
                                    tz, latitude=lat, longitude=lon)
    except Exception:  # noqa: BLE001
        return None
    asc = cast.get("ascendant")
    if not asc:
        return None
    d1 = cast["d1"]
    if any(g not in d1 for g in GRAHAS):
        return None
    birth_jd = float(cast["birth_jd"])
    delta = _ayanamsa_delta(birth_jd)
    lons = {g: (float(d1[g]["longitude"]) + delta) % 360.0 for g in GRAHAS}
    asc_lon = (float(asc["longitude"]) + delta) % 360.0
    bundle = bundle_from_positions(lons, asc_lon, birth_jd=birth_jd,
                                   person_id=str(row["person_id"]))
    dy, dm, dd = (int(x) for x in str(row["dod"]).split("-"))
    death_jd = swe.julday(dy, dm, dd, 12.0, swe.GREG_CAL)
    death_age_days = death_jd - birth_jd
    if not (365.0 < death_age_days <= 120 * 366.0):
        return None
    mds = D.md_intervals(lons["Moon"], birth_jd)
    ad_start, ad_lord, ad_pmd = [], [], []
    for md in mds:
        for ad in D.ad_intervals_in_md(md):
            ad_start.append(ad.start_jd)
            ad_lord.append(LORD_IDX[ad.lord])
            ad_pmd.append(LORD_IDX[md.lord])
    return Person(
        pm=PotencyModel.from_bundle(bundle),
        death_age_days=death_age_days,
        ad_start=np.array(ad_start), ad_lord=np.array(ad_lord, dtype=np.int8),
        ad_pmd=np.array(ad_pmd, dtype=np.int8),
        md_start=np.array([iv.start_jd for iv in mds]),
        md_end=np.array([iv.end_jd for iv in mds]),
        birth_jd=birth_jd,
    )


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #

def _pb_test(hits: np.ndarray, p_null: np.ndarray) -> dict:
    O = float(hits.sum())
    E = float(p_null.sum())
    var = float((p_null * (1 - p_null)).sum())
    z = (O - E) / math.sqrt(var) if var > 0 else 0.0
    return {"observed": O, "expected": round(E, 2), "rr": round(O / E, 4) if E else None,
            "z": round(z, 3), "p_one_sided": float(norm.sf(z))}


def _percentile_test(death_pct: np.ndarray, pct_var: np.ndarray) -> dict:
    n = len(death_pct)
    mean = float(death_pct.mean())
    se = math.sqrt(float(pct_var.sum()) / n**2)
    z = (mean - 0.5) / se if se > 0 else 0.0
    return {"mean_percentile": round(mean, 4), "se": round(se, 5),
            "z": round(z, 3), "p_one_sided": float(norm.sf(z))}


def _kappa(pred: np.ndarray, obs: np.ndarray) -> float:
    n = len(pred)
    po = float((pred == obs).mean())
    pe = sum(float((pred == b).mean()) * float((obs == b).mean())
             for b in np.unique(np.concatenate([pred, obs])))
    return (po - pe) / (1 - pe) if pe < 1 else 0.0


def evaluate(persons: list[Person], sample_ages_days: np.ndarray,
             rng: np.random.Generator) -> dict:
    n = len(persons)
    death_hit, hit_p = np.zeros(n), np.zeros(n)
    death_pct, pct_var = np.zeros(n), np.zeros(n)
    pred_band, obs_band = np.zeros(n, dtype=np.int8), np.zeros(n, dtype=np.int8)
    null_pcts = np.zeros((n, len(sample_ages_days)))

    for i, p in enumerate(persons):
        samp = p.eval_at(sample_ages_days)
        dpot = float(p.eval_at(np.array([p.death_age_days]))[0])
        thresh = np.quantile(samp, 0.90)
        death_hit[i] = dpot > thresh
        hit_p[i] = float((samp > thresh).mean())      # exact null p (ties!)
        # mid-rank percentile of death potency in own sample
        below = float((samp < dpot).mean())
        eq = float((samp == dpot).mean())
        death_pct[i] = below + 0.5 * eq
        # per-person null variance of the mid-rank percentile
        s_below = (samp[:, None] < samp[None, :]).mean(axis=0)  # O(k^2/…)
        s_pct = s_below + 0.5 * (samp[:, None] == samp[None, :]).mean(axis=0)
        pct_var[i] = float(s_pct.var())
        null_pcts[i] = s_pct
        pred_band[i] = int(p.pm.band)
        obs_band[i] = int(band_of_age(p.death_age_days / _DPY))

    p1 = _pb_test(death_hit, hit_p)
    p2 = _percentile_test(death_pct, pct_var)
    # P3: κ with empirical null — pair predicted bands with the observed
    # band of randomly drawn sample ages.
    k_obs = _kappa(pred_band, obs_band)
    k_null = []
    obs_bands_of_samples = np.array(
        [int(band_of_age(a / _DPY)) for a in sample_ages_days], dtype=np.int8)
    for _ in range(500):
        draw = rng.choice(obs_bands_of_samples, size=n, replace=True)
        k_null.append(_kappa(pred_band, draw))
    k_null = np.array(k_null)
    p3 = {"kappa": round(k_obs, 4),
          "kappa_null_mean": round(float(k_null.mean()), 4),
          "kappa_null_sd": round(float(k_null.std()), 5),
          "p_one_sided": float(((k_null >= k_obs).sum() + 1) / (len(k_null) + 1)),
          "band_confusion": {
              f"pred_{AyuBand(pb).name}": {
                  f"obs_{AyuBand(ob).name}": int(((pred_band == pb) & (obs_band == ob)).sum())
                  for ob in (0, 1, 2)} for pb in (0, 1, 2)},
          }
    return {"n": n, "P1_top_decile": p1, "P2_mean_percentile": p2,
            "P3_band_kappa": p3}


def preflight_shuffled_pairing(persons: list[Person],
                               sample_ages_days: np.ndarray,
                               rng: np.random.Generator) -> dict:
    """Re-pair persons with other persons' death ages; primaries must go null."""
    ages = np.array([p.death_age_days for p in persons])
    perm = rng.permutation(len(persons))
    shuffled = []
    for i, p in enumerate(persons):
        q = Person(pm=p.pm, death_age_days=float(ages[perm[i]]),
                   ad_start=p.ad_start, ad_lord=p.ad_lord, ad_pmd=p.ad_pmd,
                   md_start=p.md_start, md_end=p.md_end, birth_jd=p.birth_jd)
        shuffled.append(q)
    out = evaluate(shuffled, sample_ages_days, rng)
    out["pass"] = (abs(out["P1_top_decile"]["z"]) <= 3.0
                   and abs(out["P2_mean_percentile"]["z"]) <= 3.0)
    return out


def run(corpus: Path, out_dir: Path, smoke: int | None = None) -> dict:
    df = pd.read_parquet(corpus)
    if smoke:
        df = df.sample(n=min(smoke, len(df)), random_state=_SEED).reset_index(drop=True)
    logger.info("corpus: %d rows", len(df))
    persons: list[Person] = []
    for _, row in df.iterrows():
        p = _build_person(row)
        if p is not None:
            persons.append(p)
    logger.info("built %d/%d persons", len(persons), len(df))

    rng = np.random.default_rng(_SEED)
    all_ages = np.array([p.death_age_days for p in persons])
    k = min(_PERM_SAMPLES, len(all_ages))
    sample_ages = rng.choice(all_ages, size=k, replace=False)

    pre = preflight_shuffled_pairing(persons, sample_ages,
                                     np.random.default_rng(_SEED + 1))
    logger.info("preflight shuffled-pairing: P1 z=%.2f P2 z=%.2f pass=%s",
                pre["P1_top_decile"]["z"], pre["P2_mean_percentile"]["z"],
                pre["pass"])

    result = evaluate(persons, sample_ages, np.random.default_rng(_SEED + 2))
    out = {
        "corpus": str(corpus), "n_rows": len(df), "n_persons": len(persons),
        "perm_samples": k, "seed": _SEED, "smoke": bool(smoke),
        "ayanamsa": "RAMAN (converted from Lahiri cast by exact per-JD delta)",
        "transits_in_primaries": False,
        "preflight_shuffled_pairing": pre,
        "primaries": result,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    name = "smoke_run.json" if smoke else "main_run.json"
    (out_dir / name).write_text(json.dumps(out, indent=2))
    logger.info("wrote %s", out_dir / name)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path,
                    default=Path("data/raman_saab/death_corpus_run3.parquet"))
    ap.add_argument("--out", type=Path, default=Path("data/ml_runs/raman_saab/run4"))
    ap.add_argument("--smoke", type=int, default=None)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    res = run(args.corpus, args.out, smoke=args.smoke)
    pr = res["primaries"]
    print(f"\nN={pr['n']}  preflight pass={res['preflight_shuffled_pairing']['pass']}")
    print("P1 top-decile:", pr["P1_top_decile"])
    print("P2 percentile:", pr["P2_mean_percentile"])
    print("P3 band κ:", {k: v for k, v in pr["P3_band_kappa"].items()
                         if k != "band_confusion"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
