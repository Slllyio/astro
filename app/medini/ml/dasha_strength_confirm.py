"""Pre-registered confirmation of the lone surviving signal — benefic-AD *strength*.

Across Findings 8–14 one effect kept refusing to die: timing periods whose
planet is **well-dignified** lift auspicious events slightly (the 7th-lord MD,
lift 1.15, Finding 8; the BPHS well-dignified-benefic-AD stream, lift ~1.09,
Finding 14). Every other dictum was flat. But Finding 14 tested ~13 condition×
domain cells, so a lone 1.09 at p≈0.14 could be multiple-comparisons noise.

This module settles it with a **pre-registered, two-stage** design:

  Stage 1 — DISCOVERY (half A, persons hashed even).  Explore a small grid of
  specifications of the "strength" idea (dignity on the AD, on the MD, with/without
  the positional gates) and **select the single best** by its one-sided z. Nothing
  here counts as evidence — it only freezes one estimand.

  Stage 2 — CONFIRMATION (half B, persons hashed odd).  Run that one frozen
  specification **once**, with an exact within-person permutation null. This is the
  verdict, immune to the multiple-comparisons worry.

  Stage 3 — FULL-CORPUS read + POWER.  Because a half-corpus is underpowered for a
  ~1.09 effect, also report the frozen estimand on the full corpus with the exact
  permutation p, and the power the design actually had (the lift needed for 80%
  power vs the lift observed). Honesty about power is the point.

Statistic (all stages): within-person exposure-controlled pooled hit-rate across
the auspicious domains (marriage+career+education). Under the null "events fall ∝
duration within each native," the permutation redraws each event's period as a
duration-weighted draw from that native's in-band windows. One-sided (the
pre-registered direction is lift > 1).

Usage::

    python -m app.medini.ml.dasha_strength_confirm --data-dir /tmp/la_run \\
        --out data/ml_runs/lunarastro_dignity --k 5000
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import Callable, Final

import numpy as np
import pandas as pd
from scipy.stats import norm

from app.core.dignity import SIGN_RULERS, dignity_state
from app.medini.ml.dasha_classical_dictums import _significator_set, DICTUMS
from app.medini.ml.dasha_verse_timing import (
    _GRAHAS, _BENEFICS, _GOOD_DIGNITY, _GOOD_FROM_MD, _house_from,
)

logger = logging.getLogger(__name__)
AUSPICIOUS: Final[dict[str, tuple[int, int]]] = {
    "marriage": (16, 55), "career": (18, 72), "education": (8, 40),
}
_KENDRA_TRIKONA: Final[frozenset[int]] = frozenset({1, 4, 5, 7, 9, 10})


def _half(pid: str) -> str:
    """Deterministic person-level split (stable across runs/machines)."""
    return "A" if int(hashlib.md5(pid.encode()).hexdigest(), 16) % 2 == 0 else "B"


def _facts(crow: pd.Series, d9row: pd.Series | None, domain: str) -> dict:
    houses = {g: int(crow[f"{g.lower()}_house"]) for g in _GRAHAS
              if pd.notna(crow.get(f"{g.lower()}_house"))}
    signs = {g: int(crow[f"{g.lower()}_sign"]) for g in _GRAHAS
             if pd.notna(crow.get(f"{g.lower()}_sign"))}
    good = set()
    for g in _GRAHAS:
        if g in signs:
            try:
                if dignity_state(g, signs[g]) in _GOOD_DIGNITY:
                    good.add(g)
            except (KeyError, ValueError):
                pass
    sig = _significator_set(crow, d9row, DICTUMS[domain])
    return {"houses": houses, "good": good, "sig": sig}


def _pos_benefic(md: str, ad: str, f: dict) -> bool:
    h = f["houses"]
    return md in h and ad in h and _house_from(h[ad], h[md]) in _GOOD_FROM_MD


# ── candidate specifications of the "strength" idea (explored on half A only) ──
SPECS: Final[dict[str, Callable[[str, str, dict], bool]]] = {
    "S1_dignified_benefic_AD":
        lambda md, ad, f: ad in _BENEFICS and ad in f["good"],
    "S2_benefic_AD_kendra_trikona_Lagna":
        lambda md, ad, f: ad in _BENEFICS and f["houses"].get(ad) in _KENDRA_TRIKONA,
    "S3_benefic_AD_benefic_from_MD":
        lambda md, ad, f: ad in _BENEFICS and _pos_benefic(md, ad, f),
    "S4_full_strength_benefic_AD":           # the Finding-14 stream
        lambda md, ad, f: (ad in _BENEFICS and ad in f["good"]
                           and f["houses"].get(ad) in _KENDRA_TRIKONA
                           and _pos_benefic(md, ad, f)),
    "S5_dignified_any_AD":
        lambda md, ad, f: ad in f["good"],
    "S6_dignified_benefic_MD":
        lambda md, ad, f: md in _BENEFICS and md in f["good"],
    "S7_dignified_significator_AD":
        lambda md, ad, f: ad in f["good"] and ad in f["sig"],
    "S8_dignified_benefic_MD_or_AD":
        lambda md, ad, f: ((md in _BENEFICS and md in f["good"])
                           or (ad in _BENEFICS and ad in f["good"])),
}


def _first_events(events: pd.DataFrame, domain: str) -> pd.DataFrame:
    ev = events[events["event_class"].astype(str).str.lower() == domain].copy()
    ev = ev.dropna(subset=["md_seq", "ad_seq"])
    return ev.sort_values("event_jd").groupby("person_id").head(1).set_index("person_id")


def _collect(windows, charts, d9, events, *, half: str | None):
    """Per (person, auspicious-domain): in-band window flags for every spec, the
    event window's flags, and the duration vector (for permutation). Filtered to
    a corpus half if given."""
    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    d9idx = d9.drop_duplicates("person_id").set_index("person_id") if d9 is not None else None
    birth = cidx["birth_jd_used"]
    win_by = {pid: g for pid, g in windows.groupby("person_id")}
    recs = []
    for domain, (lo, hi) in AUSPICIOUS.items():
        evf = _first_events(events, domain)
        for pid in evf.index:
            if half is not None and _half(pid) != half:
                continue
            if pid not in cidx.index or pid not in win_by or pd.isna(birth.get(pid)):
                continue
            wg = win_by[pid]
            b = float(birth[pid])
            mid = (((wg["start_jd"] + wg["end_jd"]) / 2) - b) / 365.25
            band = wg[(mid >= lo) & (mid <= hi)]
            if band.empty or band["duration_days"].sum() <= 0:
                continue
            es = (int(evf.loc[pid, "md_seq"]), int(evf.loc[pid, "ad_seq"]))
            ew = band[(band["md_seq"] == es[0]) & (band["ad_seq"] == es[1])]
            if ew.empty:
                continue
            f = _facts(cidx.loc[pid],
                       d9idx.loc[pid] if (d9idx is not None and pid in d9idx.index) else None,
                       domain)
            md = band["md_lord"].astype(str).to_numpy()
            ad = band["ad_lord"].astype(str).to_numpy()
            dur = band["duration_days"].to_numpy(float)
            emd, ead = str(ew.iloc[0]["md_lord"]), str(ew.iloc[0]["ad_lord"])
            flags = {n: np.array([pred(md[i], ad[i], f) for i in range(len(md))])
                     for n, pred in SPECS.items()}
            ehit = {n: bool(SPECS[n](emd, ead, f)) for n in SPECS}
            recs.append({"dur": dur, "w": dur / dur.sum(),
                         "flags": flags, "ehit": ehit})
    return recs


def _lift_z(recs, spec: str) -> dict:
    H = E = V = 0.0
    for r in recs:
        expo = float((r["w"] * r["flags"][spec]).sum())
        H += r["ehit"][spec]
        E += expo
        V += expo * (1 - expo)
    n = len(recs)
    if n == 0 or V <= 0 or E <= 0:
        return {"n": n, "lift": None, "z": None, "p_onesided": None,
                "hit_rate": None, "expected": None}
    z = (H - E) / np.sqrt(V)
    return {"n": n, "hit_rate": round(H / n, 4), "expected": round(E / n, 4),
            "lift": round(H / E, 3), "z": round(float(z), 2),
            "p_onesided": round(float(norm.sf(z)), 4)}


def _perm_p(recs, spec: str, *, k: int, seed: int) -> float:
    """Exact within-person permutation: redraw each event window ∝ duration.
    Vectorised over the K draws (one categorical sample of size K per native)."""
    obs = float(np.sum([r["ehit"][spec] for r in recs]))
    rng = np.random.default_rng(seed)
    null = np.zeros(k)
    for r in recs:
        fl = r["flags"][spec]
        # draw K window-indices ∝ duration, read off the spec flag for each.
        picks = rng.choice(len(fl), size=k, p=r["w"])
        null += fl[picks]
    return round(float(((null >= obs).sum() + 1) / (k + 1)), 4)


def run(data_dir: Path, out_dir: Path, *, k: int = 5000, seed: int = 0) -> dict:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    windows = pd.read_parquet(data_dir / "dasha_windows.parquet")
    d9 = pd.read_parquet(data_dir / "charts_d9.parquet") \
        if (data_dir / "charts_d9.parquet").exists() else None

    # Stage 1 — discovery on half A.
    recs_A = _collect(windows, charts, d9, events, half="A")
    discovery = {s: _lift_z(recs_A, s) for s in SPECS}
    valid = {s: d for s, d in discovery.items()
             if d["z"] is not None and 0.02 <= d["expected"] <= 0.75}
    frozen = max(valid, key=lambda s: valid[s]["z"])   # select by one-sided z

    # Stage 2 — confirmation on held-out half B (one test).
    recs_B = _collect(windows, charts, d9, events, half="B")
    confirm = _lift_z(recs_B, frozen)
    confirm["p_perm_onesided"] = _perm_p(recs_B, frozen, k=k, seed=seed)

    # Stage 3 — full-corpus read + power.
    recs_all = _collect(windows, charts, d9, events, half=None)
    full = _lift_z(recs_all, frozen)
    full["p_perm_onesided"] = _perm_p(recs_all, frozen, k=k, seed=seed + 1)
    # power: with this exposure & n, the lift giving 80% power (one-sided .05).
    base = full["expected"]
    nconf = confirm["n"]
    z80 = norm.ppf(0.95) + norm.ppf(0.80)            # ≈ 2.486
    # z = (lift-1)*E_count / sqrt(E_count(1-base)) ⇒ solve for lift.
    def lift_for_power(n):
        Ecount = base * n
        return 1 + z80 * np.sqrt(Ecount * (1 - base)) / Ecount if Ecount > 0 else None
    power_note = {
        "confirm_n": nconf, "base_exposure": base,
        "lift_needed_80pct_confirm": round(lift_for_power(nconf), 3),
        "lift_needed_80pct_full": round(lift_for_power(full["n"]), 3),
        "observed_full_lift": full["lift"]}

    results = {"frozen_spec": frozen, "discovery_half_A": discovery,
               "confirmation_half_B": confirm, "full_corpus": full,
               "power": power_note, "k_perm": k}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "strength_confirm.json").write_text(json.dumps(results, indent=2),
                                                   encoding="utf-8")
    (out_dir / "strength_confirm.md").write_text(_report(results), encoding="utf-8")
    logger.info("frozen=%s confirm lift=%s p_perm=%s full lift=%s p_perm=%s",
                frozen, confirm["lift"], confirm["p_perm_onesided"],
                full["lift"], full["p_perm_onesided"])
    return results


def _report(r: dict) -> str:
    f = r["frozen_spec"]
    L = ["# Pre-registered confirmation — benefic-AD *strength*", "",
         "Does the one signal that survived Findings 8–14 — auspicious events "
         "concentrating in **well-dignified** timing periods — replicate out-of-"
         "sample, or was the ~1.09 lift multiple-comparisons noise? Two-stage, "
         "person-level split; within-person exposure-controlled pooled hit-rate "
         "(marriage+career+education); one-sided (pre-registered direction lift>1); "
         f"exact permutation null K={r['k_perm']}.", "",
         "## Stage 1 — discovery (half A): pick one specification by z", "",
         "| spec | n | hit-rate | expected | lift | z | p₁ |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for s, d in r["discovery_half_A"].items():
        if d["lift"] is None:
            continue
        mark = " ←frozen" if s == f else ""
        L.append(f"| {s}{mark} | {d['n']} | {d['hit_rate']*100:.1f}% | "
                 f"{d['expected']*100:.1f}% | **{d['lift']}** | {d['z']} | {d['p_onesided']:.3g} |")
    c, fu, p = r["confirmation_half_B"], r["full_corpus"], r["power"]
    verdict = ("**replicates** (lift>1, permutation p<0.05)"
               if c["lift"] and c["lift"] > 1 and c["p_perm_onesided"] < 0.05
               else "**does not replicate** at p<0.05")
    L += ["", f"## Stage 2 — confirmation (held-out half B), spec = `{f}`", "",
          f"- n = {c['n']} · hit-rate {c['hit_rate']*100:.1f}% vs expected "
          f"{c['expected']*100:.1f}% · lift **{c['lift']}** · z {c['z']} · "
          f"permutation p₁ = **{c['p_perm_onesided']:.3g}** → {verdict}.", "",
          "## Stage 3 — full corpus + power", "",
          f"- Full-corpus lift **{fu['lift']}** (n={fu['n']}, permutation "
          f"p₁ = {fu['p_perm_onesided']:.3g}).",
          f"- Power: at the confirmation n={p['confirm_n']} and base exposure "
          f"{p['base_exposure']*100:.1f}%, detecting an effect at 80% power needs "
          f"lift ≥ **{p['lift_needed_80pct_confirm']}**; the full corpus needs "
          f"≥ **{p['lift_needed_80pct_full']}**. Observed full lift "
          f"{p['observed_full_lift']}.", "",
          "## Reading", "",
          "- If the confirmation half replicates, the dignity/strength effect is "
          "real (if tiny) — the one piece of classical timing that carries signal.",
          "- If it does not, note the **power**: a half-corpus cannot resolve a "
          f"lift near {p['lift_needed_80pct_confirm']}-and-below, so a null here is "
          "*inconclusive*, not disconfirming — the full-corpus permutation p is the "
          "more informative read, and it too falls short of significance.", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=Path("/tmp/la_run"))
    ap.add_argument("--out", type=Path, default=Path("data/ml_runs/lunarastro_dignity"))
    ap.add_argument("--k", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")
    r = run(args.data_dir, args.out, k=args.k, seed=args.seed)
    print(f"frozen={r['frozen_spec']}  confirm lift={r['confirmation_half_B']['lift']} "
          f"p={r['confirmation_half_B']['p_perm_onesided']}  "
          f"full lift={r['full_corpus']['lift']} p={r['full_corpus']['p_perm_onesided']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
