"""Track-B VOCATION & EMINENCE validation — the non-death outcome axis.

Tests the engine's house / kāraka / **yoga** signals against a real, independent
biographical outcome (Astro-Databank vocation + eminence), exactly per
``docs/raman_saab/VOCATION_PREREG.md`` (committed before this ran).

Pipeline:
1. Cast every person in ``vocation_corpus.parquet`` — Lahiri sidereal planet
   longitudes, sidereal ascendant → whole-sign houses (Vedic frame), plus a
   tropical Placidus cusp set for the Gauquelin mundane position (ayanāṁśa-
   invariant). Lean direct-Swiss-Ephemeris (Moshier), ~0.1 ms/chart.
2. Extract the pre-registered feature indicators per person.
3. Run the 19-test battery under the PRIMARY null — **birth-decade-stratified
   label permutation** — with an exact hypergeometric (finite-population)
   z/RR; no Monte-Carlo on the test itself.
4. Validity: null-calibration (shuffled labels → z ~ N(0,1)) and planted-effect
   recovery (construct a G1-sized RR=1.20 label, confirm it is recovered).

CLI:
    python -m app.medini.ml.raman_saab.vocation_validate \
        --corpus data/holos/vocation_corpus.parquet \
        --out data/ml_runs/raman_saab/vocation_validation.json
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from app.core.chart_model import Chart
from app.core.dignity import (
    SIGN_RULERS, is_exalted, is_moolatrikona, is_own_sign,
)
from app.core.drishti_argala import aspects_from_planet
from app.core import yoga_library as YL

logger = logging.getLogger(__name__)

_BODIES = [
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN), ("Rahu", swe.MEAN_NODE),
]
_SFLAG = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
_TFLAG = swe.FLG_MOSEPH
_KENDRAS = frozenset({1, 4, 7, 10})

# Pre-registered kāraka → vocation map (VOCATION_PREREG.md §Family 1).
_KARAKA_MAP: dict[str, str] = {
    "voc_sports": "Mars", "voc_military": "Mars", "voc_medical": "Mars",
    "voc_writers": "Mercury", "voc_science": "Mercury", "voc_business": "Mercury",
    "voc_education": "Jupiter", "voc_law": "Jupiter", "voc_religion": "Jupiter",
    "voc_entertainment": "Venus", "voc_art": "Venus",
    "voc_politics": "Sun",
}


# ── casting + features ────────────────────────────────────────────────

def _house_of_lon(lon: float, cusps: tuple[float, ...]) -> int:
    """Mundane (Placidus) house 1..12 of an ecliptic longitude given the 12
    house-cusp longitudes (cusps[0] = house-1 cusp = ascendant)."""
    for i in range(12):
        a = cusps[i] % 360.0
        b = cusps[(i + 1) % 12] % 360.0
        span = (b - a) % 360.0
        off = (lon - a) % 360.0
        if off < span:
            return i + 1
    return 12


def _cast(r) -> dict | None:
    try:
        ut = int(r.birth_hour) + int(r.birth_min) / 60.0 - float(r.tz_offset)
        jd = swe.julday(int(r.birth_year), int(r.birth_month), int(r.birth_day),
                        ut, swe.GREG_CAL)
        slons: dict[str, float] = {}
        for nm, b in _BODIES:
            xx, _ = swe.calc_ut(jd, b, _SFLAG)
            slons[nm] = xx[0] % 360.0
        slons["Ketu"] = (slons["Rahu"] + 180.0) % 360.0
        ayan = swe.get_ayanamsa_ut(jd)
        tcusps, tascmc = swe.houses(jd, float(r.lat), float(r.lon), b"P")
        asc_sid = (tascmc[0] - ayan) % 360.0
        xm, _ = swe.calc_ut(jd, swe.MARS, _TFLAG)
        mars_trop = xm[0] % 360.0
        return {"slons": slons, "asc_sid": asc_sid,
                "tcusps": tuple(tcusps), "mars_trop": mars_trop}
    except Exception:  # noqa: BLE001 — a handful of extreme-latitude Placidus fails
        return None


def _karaka_strong(k: str, sign: dict[str, int], house: dict[str, int],
                   lon: dict[str, float], tenth_sign: int, tenth_lord: str) -> bool:
    """Pre-registered KĀRAKA_STRONG(K): dignity | kendra | 10th-link."""
    s, h = sign[k], house[k]
    if is_exalted(k, s) or is_own_sign(k, s) or is_moolatrikona(k, lon[k]):
        return True
    if h in _KENDRAS:
        return True
    if h == 10 or 10 in aspects_from_planet(k, h):        # occupies / aspects 10th
        return True
    if sign[k] == sign[tenth_lord]:                        # conjunct 10th lord
        return True
    return False


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cast every person and emit the pre-registered feature + label frame."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    grahas = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    pmp = (YL.detect_ruchaka, YL.detect_bhadra, YL.detect_hamsa,
           YL.detect_malavya, YL.detect_sasa)
    raja = (YL.detect_raja_yoga, YL.detect_neecha_bhanga_raja,
            YL.detect_dharma_karma_adhipati)
    rows: list[dict] = []
    for r in df.itertuples():
        c = _cast(r)
        if c is None:
            continue
        lon = c["slons"]
        sign = {p: int(lon[p] // 30) + 1 for p in grahas}
        lagna = int(c["asc_sid"] // 30) + 1
        house = {p: ((sign[p] - lagna) % 12) + 1 for p in grahas}
        tenth_sign = ((lagna - 1 + 9) % 12) + 1
        tenth_lord = SIGN_RULERS[tenth_sign]

        chart = Chart(planet_signs=sign, planet_houses=house, planet_lons=lon,
                      asc_sign=lagna, asc_lon=c["asc_sid"])

        pmp_on = any(d(chart).active for d in pmp)
        raja_on = any(d(chart).active for d in raja)
        tl_s, tl_h = sign[tenth_lord], house[tenth_lord]
        tenth_lord_strong = bool(
            is_exalted(tenth_lord, tl_s) or is_own_sign(tenth_lord, tl_s)
            or is_moolatrikona(tenth_lord, lon[tenth_lord]) or tl_h in _KENDRAS
        )
        mars_house_mundane = _house_of_lon(c["mars_trop"], c["tcusps"])

        row = {
            "decade": (int(r.birth_year) // 10) * 10,
            "eminent": int(r.eminent),
            "voc_sports": int(r.voc_sports), "voc_military": int(r.voc_military),
            # kāraka-strength feature per graha (computed once, reused per vocation)
            "k_Mars": int(_karaka_strong("Mars", sign, house, lon, tenth_sign, tenth_lord)),
            "k_Mercury": int(_karaka_strong("Mercury", sign, house, lon, tenth_sign, tenth_lord)),
            "k_Jupiter": int(_karaka_strong("Jupiter", sign, house, lon, tenth_sign, tenth_lord)),
            "k_Venus": int(_karaka_strong("Venus", sign, house, lon, tenth_sign, tenth_lord)),
            "k_Sun": int(_karaka_strong("Sun", sign, house, lon, tenth_sign, tenth_lord)),
            "pmp": int(pmp_on), "raja": int(raja_on),
            "tenth_lord_strong": int(tenth_lord_strong),
            "mars_plus_zone": int(mars_house_mundane in (12, 9)),
        }
        row["eminence_union"] = int(pmp_on or raja_on or tenth_lord_strong)
        # copy through the remaining vocation-group labels
        for col in _KARAKA_MAP:
            row[col] = int(getattr(r, col))
        rows.append(row)
    return pd.DataFrame(rows)


# ── stratified-permutation test (exact, hypergeometric) ───────────────

def _pool_small_strata(decade: np.ndarray, min_n: int = 20) -> np.ndarray:
    """Merge decades with < min_n rows into the nearest larger decade."""
    out = decade.copy()
    vals, counts = np.unique(out, return_counts=True)
    small = set(vals[counts < min_n])
    big = sorted(v for v in vals if v not in small)
    if not big:
        return np.zeros_like(out)
    for v in small:
        nearest = min(big, key=lambda b: abs(b - v))
        out[out == v] = nearest
    return out


def strat_test(feature: np.ndarray, label: np.ndarray, decade: np.ndarray) -> dict:
    """Birth-decade-stratified label-permutation test. Within each stratum the
    label is a random size-``n_L`` subset, so the feature-hit count among the
    labelled is hypergeometric: E = n_L·K/n, Var = n_L·(K/n)·(1−K/n)·(n−n_L)/(n−1).
    O, E, Var summed over strata → exact one-sided z, RR."""
    strata = _pool_small_strata(decade)
    O = E = V = 0.0
    for s in np.unique(strata):
        m = strata == s
        n = int(m.sum())
        if n < 2:
            continue
        K = float(feature[m].sum())
        nL = float(label[m].sum())
        if nL == 0 or K == 0:
            continue
        p = K / n
        O += float((feature[m] * label[m]).sum())
        E += nL * p
        V += nL * p * (1.0 - p) * (n - nL) / (n - 1)
    if E <= 0 or V <= 0:
        return {"observed": O, "expected": E, "rr": None, "z": None, "p_one_sided": None}
    z = (O - E) / math.sqrt(V)
    p_one = 0.5 * math.erfc(z / math.sqrt(2.0))       # P(Z >= z)
    return {"observed": O, "expected": round(E, 2), "rr": round(O / E, 4),
            "z": round(z, 3), "p_one_sided": p_one, "expected_ge_10": E >= 10}


# ── validity checks ───────────────────────────────────────────────────

def null_calibration(feat: np.ndarray, decade: np.ndarray, n_L: int,
                     reps: int = 300, seed: int = 7) -> dict:
    """Shuffle a random size-n_L label many times; the stratified z should be
    ~N(0,1) if the test is calibrated."""
    rng = np.random.default_rng(seed)
    n = len(feat)
    zs = []
    for _ in range(reps):
        lab = np.zeros(n, dtype=int)
        lab[rng.choice(n, size=n_L, replace=False)] = 1
        r = strat_test(feat, lab, decade)
        if r["z"] is not None:
            zs.append(r["z"])
    zs = np.array(zs)
    return {"reps": len(zs), "z_mean": round(float(zs.mean()), 3),
            "z_sd": round(float(zs.std()), 3)}


def planted_recovery(feat: np.ndarray, decade: np.ndarray, n_L: int,
                     target_rr: float = 1.20, seed: int = 11) -> dict:
    """Construct a size-n_L synthetic label whose feature-positive fraction is
    exactly ``target_rr`` × the population base rate, then confirm the
    stratified test recovers RR ≈ target_rr at significance. This proves the
    null is not blind to a G1-sized (RR≥1.20) effect at the eminence label size."""
    rng = np.random.default_rng(seed)
    base = float(feat.mean())
    pos = np.flatnonzero(feat == 1)
    neg = np.flatnonzero(feat == 0)
    n_pos = min(len(pos), int(round(target_rr * base * n_L)))
    n_neg = max(0, n_L - n_pos)
    idx = np.concatenate([
        rng.choice(pos, size=n_pos, replace=False),
        rng.choice(neg, size=min(len(neg), n_neg), replace=False),
    ])
    lab = np.zeros(len(feat), dtype=int)
    lab[idx] = 1
    r = strat_test(feat, lab, decade)
    return {"target_rr": target_rr, "base_rate": round(base, 4),
            "n_label": int(lab.sum()), "rr": r["rr"], "z": r["z"],
            "p_one_sided": r["p_one_sided"]}


# ── battery ───────────────────────────────────────────────────────────

def run_battery(feats: pd.DataFrame) -> dict:
    decade = feats["decade"].to_numpy()
    K_TOTAL = 12 + 4 + 3
    alpha = 0.05 / K_TOTAL

    def verdict(r: dict) -> str:
        if r["rr"] is None or not r.get("expected_ge_10", False):
            return "underpowered"
        if r["rr"] >= 1.20 and r["p_one_sided"] < alpha:
            return "SUPPORTED"
        return "refuted"

    f1 = []
    for col, karaka in _KARAKA_MAP.items():
        r = strat_test(feats[f"k_{karaka}"].to_numpy(), feats[col].to_numpy(), decade)
        r.update({"vocation": col, "karaka": karaka, "n_group": int(feats[col].sum()),
                  "verdict": verdict(r)})
        f1.append(r)

    f2 = []
    emi = feats["eminent"].to_numpy()
    for sig in ("pmp", "raja", "tenth_lord_strong", "eminence_union"):
        r = strat_test(feats[sig].to_numpy(), emi, decade)
        r.update({"signal": sig, "n_eminent": int(emi.sum()), "verdict": verdict(r)})
        f2.append(r)

    f3 = []
    mars_pz = feats["mars_plus_zone"].to_numpy()
    pops = {
        "eminent_sports": (emi == 1) & (feats["voc_sports"].to_numpy() == 1),
        "eminent_military": (emi == 1) & (feats["voc_military"].to_numpy() == 1),
        "eminent_sports_or_military": (emi == 1) & (
            (feats["voc_sports"].to_numpy() == 1) | (feats["voc_military"].to_numpy() == 1)),
    }
    for name, mask in pops.items():
        r = strat_test(mars_pz, mask.astype(int), decade)
        r.update({"population": name, "n_pop": int(mask.sum()), "verdict": verdict(r)})
        f3.append(r)

    # validity: null-calibration on a mid-size label; planted recovery at the
    # realistic small-label (eminence) prevalence where RR maps cleanly.
    nL_mid = int(feats["voc_entertainment"].sum())
    nL_small = int(feats["eminent"].sum())
    validity = {
        "null_calibration": null_calibration(feats["k_Venus"].to_numpy(), decade, nL_mid),
        "planted_rr120": planted_recovery(feats["k_Mars"].to_numpy(), decade, nL_small),
    }

    return {
        "n_persons": int(len(feats)),
        "k_tests": K_TOTAL, "bonferroni_alpha": alpha,
        "g1_threshold_rr": 1.20,
        "mars_plus_zone_base_rate": round(float(mars_pz.mean()), 4),
        "family1_karaka_vocation": f1,
        "family2_eminence_yogas": f2,
        "family3_gauquelin_mars": f3,
        "validity": validity,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", type=Path, default=Path("data/holos/vocation_corpus.parquet"))
    p.add_argument("--out", type=Path,
                   default=Path("data/ml_runs/raman_saab/vocation_validation.json"))
    p.add_argument("--limit", type=int, default=0, help="cast only first N (debug)")
    p.add_argument("--refresh", action="store_true", help="recast even if cache exists")
    args = p.parse_args()

    cache = args.out.with_name("vocation_features.parquet")
    if cache.exists() and not args.limit and not args.refresh:
        feats = pd.read_parquet(cache)
        logger.info("loaded cached features (%d) from %s", len(feats), cache)
    else:
        df = pd.read_parquet(args.corpus)
        if args.limit:
            df = df.head(args.limit)
        logger.info("casting %d charts …", len(df))
        feats = extract_features(df)
        if not args.limit:
            cache.parent.mkdir(parents=True, exist_ok=True)
            feats.to_parquet(cache, index=False)
    logger.info("cast %d charts; running battery", len(feats))
    out = run_battery(feats)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1))

    print(f"\nN={out['n_persons']}  α_Bonf={out['bonferroni_alpha']:.5f}  "
          f"Mars plus-zone base={out['mars_plus_zone_base_rate']}")
    print("\n-- F1 kāraka→vocation --")
    for r in out["family1_karaka_vocation"]:
        print(f"  {r['vocation']:20s} {r['karaka']:8s} n={r['n_group']:6d} "
              f"RR={r['rr']} z={r['z']} p={r['p_one_sided']:.3g} [{r['verdict']}]")
    print("-- F2 eminence→yogas --")
    for r in out["family2_eminence_yogas"]:
        print(f"  {r['signal']:20s} n={r['n_eminent']:6d} RR={r['rr']} z={r['z']} "
              f"p={r['p_one_sided']:.3g} [{r['verdict']}]")
    print("-- F3 Gauquelin Mars --")
    for r in out["family3_gauquelin_mars"]:
        print(f"  {r['population']:26s} n={r['n_pop']:5d} RR={r['rr']} z={r['z']} "
              f"p={r['p_one_sided']:.3g} [{r['verdict']}]")
    v = out["validity"]
    print(f"\nvalidity: null z~N({v['null_calibration']['z_mean']},"
          f"{v['null_calibration']['z_sd']}); planted RR1.20 -> RR={v['planted_rr120']['rr']} "
          f"z={v['planted_rr120']['z']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
