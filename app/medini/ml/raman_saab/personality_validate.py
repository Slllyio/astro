"""Track-B PERSONALITY (native-profile) validation — the personality axis.

Tests the engine's served "Who you are" personality signal against real,
birth-time-accurate biography, exactly per
``docs/raman_saab/PERSONALITY_PREREG.md`` (committed before this ran).

The predictor is the **served native_profile signal**: cast each person with the
production ``chart_bundle.build_bundle`` (Lahiri sidereal, whole-sign houses),
compute per-graha dignity/combust/composite via the reading's own
``proforma._planet_strength(wrapper, avasthas=None)``, then apply the frozen
``_planet_lexicon.well_placed`` rule → a binary ``PLANET_WELL_PLACED(P)`` per
governing graha P ∈ {Sun, Moon, Mars, Mercury, Jupiter, Venus}.

The statistics are reused **verbatim** from the vocation harness (same analytic
birth-decade-stratified hypergeometric permutation null, same power checks, same
G1 + Bonferroni gate), so this is only a swap of predictor + labels.

  Family 1 — Venus well-placed → marriage intact (the flagship new test).
  Family 3 — personality predictor → vocation (construct-validity re-test).

CLI:
    python -m app.medini.ml.raman_saab.personality_validate \
        --marriage data/vedastro/marriage_corpus.parquet \
        --vocation data/holos/vocation_corpus.parquet \
        --out data/ml_runs/raman_saab/personality_validation.json
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as _st

from app.core.dignity import dignity_state
from app.core.shadbala import dig_bala
from app.medini.ml.raman_saab.chart_bundle import build_bundle
from app.reading._planet_lexicon import well_placed
# reuse the vocation harness's statistics VERBATIM (identical null + power gate)
from app.medini.ml.raman_saab.vocation_validate import (
    _pool_small_strata,          # noqa: F401  (re-exported for tests)
    null_calibration,
    planted_recovery,
    strat_test,
)

logger = logging.getLogger(__name__)

# The 6 governing grahas behind the 8 native_profile styles (Sun→leadership+
# decision, Moon→emotional, Mars→risk, Mercury→communication+learning,
# Jupiter→financial, Venus→relationship).
_GOV = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus")

# Pre-registered personality-predictor → vocation map (PERSONALITY_PREREG §F3).
_VOC_MAP: dict[str, str] = {
    "voc_sports": "Mars", "voc_military": "Mars", "voc_medical": "Mars",
    "voc_writers": "Mercury", "voc_science": "Mercury", "voc_business": "Mercury",
    "voc_education": "Jupiter", "voc_law": "Jupiter", "voc_religion": "Jupiter",
    "voc_entertainment": "Venus", "voc_art": "Venus",
    "voc_politics": "Sun",
}

_YEAR_MIN, _YEAR_MAX = 1400, 2010

# Composite 0–1 component weights — copied VERBATIM from
# app.reading.proforma (_DIGNITY_SCORE + the _planet_strength composite formula)
# so this population feature is byte-identical to the served native_profile
# strength with avasthas=None (the avasthā 5th component is off the bundle).
_DIGNITY_SCORE = {
    "exalted": 1.0, "moolatrikona": 0.95, "own": 0.85, "friendly": 0.68,
    "neutral": 0.5, "inimical": 0.32, "debilitated": 0.1, "enemy": 0.32,
}


def _dignity_composite_combust(bundle, graha: str):
    """Reproduce proforma._planet_strength(avasthas=None) for one graha:
    returns (dignity_str|None, composite_0_100|None, combust_bool)."""
    signs = bundle.chart.planet_signs
    if graha not in signs:
        return None, None, False
    house = bundle.kundali.planet_house.get(graha)
    try:
        dig = dignity_state(graha, int(signs[graha]))
    except Exception:  # noqa: BLE001
        dig = None
    vim = bundle.strength.get(graha)
    shad = bundle.shadbala_ratio.get(graha)
    comp: list[float] = []
    if dig:
        d = _DIGNITY_SCORE.get(str(dig).lower())
        if d is not None:
            comp.append(d)
    if shad is not None:
        comp.append(min(1.0, float(shad) / 1.2))
    if vim is not None:
        comp.append(float(vim))
    if house:
        try:
            comp.append(min(1.0, dig_bala(graha, int(house)) / 60.0))
        except Exception:  # noqa: BLE001
            pass
    composite = round(sum(comp) / len(comp) * 100) if comp else None
    return dig, composite, bool(bundle.combust.get(graha, False))


# ── feature extraction (the served native_profile signal) ─────────────

def _well_flags(r) -> dict[str, int] | None:
    """Cast one person and return the frozen native_profile condition per
    governing graha: PLANET_WELL_PLACED(P) ∈ {0,1} + the continuous composite.
    None on a cast failure (extreme latitude, bad row)."""
    try:
        yr = int(r.birth_year)
        if not (_YEAR_MIN <= yr <= _YEAR_MAX):
            return None
        bundle = build_bundle(
            yr, int(r.birth_month), int(r.birth_day),
            int(r.birth_hour), int(r.birth_min), float(r.tz_offset),
            float(r.lat), float(r.lon),
        )
        if bundle is None:
            return None
        out: dict[str, int] = {"decade": (yr // 10) * 10}
        ok = False
        for p in _GOV:
            dig, composite, combust = _dignity_composite_combust(bundle, p)
            if dig is None and composite is None and not combust:
                out[f"well_{p}"] = 0
                out[f"strain_{p}"] = 0
                out[f"comp_{p}"] = np.nan
                continue
            w = well_placed(dig, composite, combust)
            out[f"well_{p}"] = 1 if w is True else 0
            out[f"strain_{p}"] = 1 if w is False else 0
            out[f"comp_{p}"] = float(composite) if composite is not None else np.nan
            ok = True
        return out if ok else None
    except Exception:  # noqa: BLE001
        return None


def extract_marriage(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in df.itertuples():
        f = _well_flags(r)
        if f is None:
            continue
        f["intact"] = int(1 - int(r.marriage_dissolution))
        f["dissolved"] = int(r.marriage_dissolution)
        rows.append(f)
    return pd.DataFrame(rows)


def extract_vocation(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in df.itertuples():
        f = _well_flags(r)
        if f is None:
            continue
        f["eminent"] = int(r.eminent)
        for col in _VOC_MAP:
            f[col] = int(getattr(r, col))
        rows.append(f)
    return pd.DataFrame(rows)


# ── continuous arm (Venus composite: intact vs dissolved) ─────────────

def _continuous_arm(feats: pd.DataFrame, seed: int = 23, reps: int = 2000) -> dict:
    """Welch two-sample z + Mann-Whitney on Venus composite between the intact
    and dissolved groups, with a within-decade shuffled-label permutation null
    on the mean difference (per maraka_validate.natal_8h_longevity)."""
    d = feats.dropna(subset=["comp_Venus"]).copy()
    intact = d.loc[d["intact"] == 1, "comp_Venus"].to_numpy()
    dissolved = d.loc[d["dissolved"] == 1, "comp_Venus"].to_numpy()
    if len(intact) < 30 or len(dissolved) < 30:
        return {"note": "insufficient n", "n_intact": len(intact),
                "n_dissolved": len(dissolved)}
    welch = _st.ttest_ind(intact, dissolved, equal_var=False)
    mw = _st.mannwhitneyu(intact, dissolved, alternative="two-sided")
    obs_diff = float(intact.mean() - dissolved.mean())
    # within-decade permutation null of the mean difference
    rng = np.random.default_rng(seed)
    comp = d["comp_Venus"].to_numpy()
    lab = d["intact"].to_numpy()
    dec = _pool_small_strata(d["decade"].to_numpy())
    perm = np.empty(reps)
    for i in range(reps):
        pl = lab.copy()
        for s in np.unique(dec):
            m = dec == s
            pl[m] = rng.permutation(pl[m])
        a = comp[pl == 1]
        b = comp[pl == 0]
        perm[i] = a.mean() - b.mean()
    p_perm = float((np.abs(perm) >= abs(obs_diff)).mean())
    return {
        "n_intact": int(len(intact)), "n_dissolved": int(len(dissolved)),
        "mean_intact": round(float(intact.mean()), 3),
        "mean_dissolved": round(float(dissolved.mean()), 3),
        "mean_diff": round(obs_diff, 3),
        "welch_t": round(float(welch.statistic), 3),
        "welch_p": float(welch.pvalue),
        "mannwhitney_p": float(mw.pvalue),
        "perm_null_p_two_sided": p_perm,
        "cohens_d": round(obs_diff / np.sqrt(
            (intact.var(ddof=1) + dissolved.var(ddof=1)) / 2.0), 4),
    }


# ── battery ───────────────────────────────────────────────────────────

def run_battery(mar: pd.DataFrame, voc: pd.DataFrame) -> dict:
    K_TOTAL = 1 + 12                                  # F1 (1) + F3 (12)
    alpha = 0.05 / K_TOTAL

    def verdict(r: dict) -> str:
        if r["rr"] is None or not r.get("expected_ge_10", False):
            return "underpowered"
        if r["rr"] >= 1.20 and r["p_one_sided"] < alpha:
            return "SUPPORTED"
        return "refuted"

    # ---- Family 1: Venus well-placed → marriage intact (flagship, K-counted).
    dec_m = mar["decade"].to_numpy()
    f1_main = strat_test(mar["well_Venus"].to_numpy(), mar["intact"].to_numpy(), dec_m)
    f1_main.update({"test": "venus_well_placed->intact",
                    "n_label": int(mar["intact"].sum()), "verdict": verdict(f1_main)})
    # reported alongside (NOT Bonferroni-counted)
    f1_mirror = strat_test(mar["strain_Venus"].to_numpy(),
                           mar["dissolved"].to_numpy(), dec_m)
    f1_mirror.update({"test": "venus_under_strain->dissolved",
                      "n_label": int(mar["dissolved"].sum())})
    f1_cont = _continuous_arm(mar)

    # ---- Family 3: personality predictor → vocation (construct validity, K-counted).
    dec_v = voc["decade"].to_numpy()
    f3 = []
    for col, graha in _VOC_MAP.items():
        r = strat_test(voc[f"well_{graha}"].to_numpy(), voc[col].to_numpy(), dec_v)
        r.update({"vocation": col, "graha": graha, "n_group": int(voc[col].sum()),
                  "verdict": verdict(r)})
        f3.append(r)
    # eminence — descriptive extra (NOT Bonferroni-counted)
    emi = strat_test(voc["well_Sun"].to_numpy(), voc["eminent"].to_numpy(), dec_v)
    emi.update({"test": "sun_well_placed->eminent", "n_label": int(voc["eminent"].sum())})

    # ---- validity: powered-not-blind proof (on the marriage frame, F1 label size).
    nL = int(mar["intact"].sum())
    validity = {
        "null_calibration": null_calibration(mar["well_Venus"].to_numpy(), dec_m, nL),
        "planted_rr120": planted_recovery(mar["well_Venus"].to_numpy(), dec_m,
                                          int(mar["dissolved"].sum())),
    }

    return {
        "n_marriage": int(len(mar)), "n_vocation": int(len(voc)),
        "k_tests": K_TOTAL, "bonferroni_alpha": alpha, "g1_threshold_rr": 1.20,
        "venus_well_placed_base_rate": round(float(mar["well_Venus"].mean()), 4),
        "family1_relationship": {"main": f1_main, "mirror": f1_mirror,
                                 "continuous": f1_cont},
        "family3_vocation": f3,
        "eminence_descriptive": emi,
        "validity": validity,
        "dropped": {
            "F2_life_valence": "lapaas source unreachable this session",
            "F4_psychometric": "no Big-Five/MBTI + birth-time dataset available",
        },
    }


def _load_or_cast(corpus: Path, cache: Path, extractor, limit: int,
                  refresh: bool) -> pd.DataFrame:
    if cache.exists() and not limit and not refresh:
        logger.info("loaded cached features (%d) from %s",
                    len(pd.read_parquet(cache)), cache)
        return pd.read_parquet(cache)
    df = pd.read_parquet(corpus)
    if limit:
        df = df.head(limit)
    logger.info("casting %d charts from %s …", len(df), corpus)
    feats = extractor(df)
    if not limit:
        cache.parent.mkdir(parents=True, exist_ok=True)
        feats.to_parquet(cache, index=False)
    return feats


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--marriage", type=Path,
                   default=Path("data/vedastro/marriage_corpus.parquet"))
    p.add_argument("--vocation", type=Path,
                   default=Path("data/holos/vocation_corpus.parquet"))
    p.add_argument("--out", type=Path,
                   default=Path("data/ml_runs/raman_saab/personality_validation.json"))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--refresh", action="store_true")
    args = p.parse_args()

    mar = _load_or_cast(args.marriage,
                        args.out.with_name("personality_marriage_features.parquet"),
                        extract_marriage, args.limit, args.refresh)
    voc = _load_or_cast(args.vocation,
                        args.out.with_name("personality_vocation_features.parquet"),
                        extract_vocation, args.limit, args.refresh)
    logger.info("cast marriage=%d vocation=%d; running battery", len(mar), len(voc))
    out = run_battery(mar, voc)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1))

    print(f"\nN_marriage={out['n_marriage']}  N_vocation={out['n_vocation']}  "
          f"α_Bonf={out['bonferroni_alpha']:.5f}  "
          f"Venus-well base={out['venus_well_placed_base_rate']}")
    m = out["family1_relationship"]["main"]
    print(f"\n-- F1 relationship (flagship) --")
    print(f"  Venus well-placed -> intact   n={m['n_label']} RR={m['rr']} "
          f"z={m['z']} p={m['p_one_sided']:.3g} [{m['verdict']}]")
    c = out["family1_relationship"]["continuous"]
    if "mean_diff" in c:
        print(f"  Venus composite intact={c['mean_intact']} dissolved={c['mean_dissolved']} "
              f"Δ={c['mean_diff']} d={c['cohens_d']} perm_p={c['perm_null_p_two_sided']:.3g}")
    print("-- F3 personality->vocation (construct validity) --")
    for r in out["family3_vocation"]:
        print(f"  {r['vocation']:20s} {r['graha']:8s} n={r['n_group']:6d} "
              f"RR={r['rr']} z={r['z']} p={r['p_one_sided']:.3g} [{r['verdict']}]")
    v = out["validity"]
    print(f"\nvalidity: null z~N({v['null_calibration']['z_mean']},"
          f"{v['null_calibration']['z_sd']}); planted RR1.20 -> RR="
          f"{v['planted_rr120']['rr']} z={v['planted_rr120']['z']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
