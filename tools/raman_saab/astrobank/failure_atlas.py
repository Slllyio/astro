"""Stage 8 — the FAILURE ATLAS: per-case, per-feature, per-house statistics of engine vs reality.

For every person x reality-feature: the engine's reading of the matched house-signification
(verdict + degree) beside the reality, classified into a direction-normalized cell taxonomy
(AGREE_STRONG .. DISAGREE_STRONG / ABSTAIN / BACKGROUND). Aggregated into per-feature confusion
tables (case vs labeled-contrast vs background), vacuity-corrected statistics (Youden's J on reads,
degree-level delta, calibration-by-reading), a failure-direction classification per feature, house
rollups, an off-diagonal noise floor, and three diagnostic slices (tier A-vs-B: the birth-time-noise
excuse; birth decade: label drift; sidereal lagna via AstroDatabank's own published ascendants:
which lagnas the over-affliction lives in).

PRIVACY: app_user (non-celebrity) names are blanked in the parquet itself; only celebrity_databank
names can appear in any artifact. AUCs are read from matrix_results.json (never recomputed for the
matched cell) so the atlas cannot disagree with the pre-registered numbers.

Usage:
    py -3.12 -m tools.raman_saab.astrobank.failure_atlas            # build + report
    py -3.12 -m tools.raman_saab.astrobank.failure_atlas --report-out docs/raman_saab/FAILURE_ATLAS.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tools.raman_saab.astrobank._stats import auc_mw
from tools.raman_saab.astrobank.engine_reality_matrix import FEATURES

_OUT = Path("data/astro_databank/derived/raman")
_ATLAS = _OUT / "failure_atlas"
_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio',
          'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# thresholds (the atlas registration — descriptive triage, per METHODOLOGY.md governance)
T_SAT, T_J, T_AUC_WEAK, T_AUC_SUPP, N_MIN = 0.60, 0.05, 0.52, 0.55, 30


def _cell_class(verdict: str, degree: str, expected: str) -> str:
    if verdict in (None, "", "insufficient-evidence") or pd.isna(verdict):
        return "ABSTAIN"
    if verdict == "mixed":
        return "ABSTAIN_MIXED"
    agree = (verdict == expected)
    strong = (degree == "strong")
    if agree:
        return "AGREE_STRONG" if strong else "AGREE_LEAN"
    return "DISAGREE_STRONG" if strong else "DISAGREE_LEAN"


def build() -> tuple[pd.DataFrame, dict]:
    master = pd.read_parquet(_OUT / "person_master.parquet").set_index("person_id")
    pop = pd.read_parquet(_OUT / "store_population.parquet")
    matrix = pd.read_parquet(_OUT / "engine_reality_matrix.parquet")
    verd = pd.read_parquet(_OUT / "verdicts.parquet")
    ev = pd.read_parquet(_OUT / "person_events.parquet")
    mres = json.loads((_OUT / "matrix_results.json").read_text(encoding="utf-8"))["features"]

    pids = matrix.index
    m = master.loc[pids]
    # fame proxy: documentation density
    n_ev = ev[ev.person_id.isin(pids)].groupby("person_id").size()
    n_cat = m.categories_raw.fillna("").apply(lambda c: sum(1 for t in c.split(";") if " : " in t))
    fame = ((n_ev.reindex(pids).fillna(0) - n_ev.mean()) / (n_ev.std() or 1)
            + (n_cat - n_cat.mean()) / (n_cat.std() or 1)
            + m.categories_raw.fillna("").str.contains("Notable :").astype(float))
    # sidereal lagna from AstroDatabank's published tropical Asc (raman ayanamsa ~22.4 deg 1900-70)
    import swisseph as swe
    from app.raman_saab.chart.ayanamsa import sidereal_mode
    asc_tok = m.categories_raw.fillna("").str.extract(r"Asc (\d+) (\w+)")
    with sidereal_mode("raman"):
        ayan = {y: float(swe.get_ayanamsa_ut(swe.julday(y, 6, 15, 12.0, swe.GREG_CAL)))
                for y in range(1700, 2016)}
    lagna_sid, cusp_flag = {}, {}
    for pid, (deg, sign) in asc_tok.iterrows():
        if pd.isna(sign) or sign not in _SIGNS:
            continue
        yr = int(m.loc[pid, "birth_date"][:4])
        trop = _SIGNS.index(sign) * 30 + int(deg)
        sid = (trop - ayan.get(yr, 22.4)) % 360
        lagna_sid[pid] = _SIGNS[int(sid // 30)]
        cusp_flag[pid] = min(sid % 30, 30 - sid % 30) < 1.0

    vkey = verd.set_index(["person_id", "house", "signification"])[["verdict", "degree"]]
    rows = []
    for fid, (_k, _p, h, sig, direction, contrast) in FEATURES.items():
        rc = f"real_{fid}"
        if rc not in matrix.columns:
            continue
        expected = "afflicted" if direction == "afflicted" else "favourable"
        try:
            sub = vkey.xs((h, sig), level=(1, 2)).reindex(pids)
        except KeyError:
            continue
        real = matrix[rc]
        contrast_real = matrix[f"real_{contrast}"] if contrast else None
        for pid in pids:
            r = int(real.loc[pid])
            side = ("positive" if r == 1 else
                    "contrast" if (contrast_real is not None and int(contrast_real.loc[pid]) == 1)
                    else "background")
            v, d = sub.loc[pid, "verdict"], sub.loc[pid, "degree"]
            exp_here = expected if side != "contrast" else (
                "favourable" if expected == "afflicted" else "afflicted")
            rows.append({
                "person_id": pid,
                "name_display": (m.loc[pid, "name_display"]
                                 if m.loc[pid, "population"] == "celebrity_databank" else ""),
                "birth_date": m.loc[pid, "birth_date"], "quality_tier": m.loc[pid, "quality_tier"],
                "birth_decade": int(m.loc[pid, "birth_date"][:4]) // 10 * 10,
                "feature_id": fid, "house": h, "signification": sig, "direction": direction,
                "reality_side": side, "eng_verdict": v if isinstance(v, str) else "",
                "eng_degree": d if isinstance(d, str) else "",
                "cell_class": ("BACKGROUND" if side == "background"
                               else _cell_class(v, d, exp_here)),
                "fame_score": float(fame.loc[pid]),
                "lagna_sidereal": lagna_sid.get(pid, ""), "lagna_cusp": cusp_flag.get(pid, False),
            })
    cases = pd.DataFrame(rows)
    _ATLAS.mkdir(parents=True, exist_ok=True)
    cases.to_parquet(_ATLAS / "failure_atlas_cases.parquet", engine="pyarrow",
                     compression="zstd", index=False)

    # ── per-feature statistics ───────────────────────────────────────────────
    summary: dict[str, dict] = {}
    eng_cols = [c for c in matrix.columns if c.startswith("eng_")]
    for fid, (_k, _p, h, sig, direction, contrast) in FEATURES.items():
        f = cases[cases.feature_id == fid]
        if f.empty:
            continue
        expected = "afflicted" if direction == "afflicted" else "favourable"
        opposite = "favourable" if expected == "afflicted" else "afflicted"
        def dist(side):
            g = f[f.reality_side == side]
            n = len(g)
            if n == 0:
                return {}, 0
            vc = g.eng_verdict.replace("", "insufficient-evidence").value_counts(normalize=True)
            return {v: float(vc.get(v, 0)) for v in
                    ("afflicted", "mixed", "favourable", "insufficient-evidence")}, n
        pc, n_case = dist("positive")
        kc, n_ctr = dist("contrast")
        bg, n_bg = dist("background")
        ref = kc if n_ctr >= N_MIN else bg
        n_ref = n_ctr if n_ctr >= N_MIN else n_bg
        # Youden's J on reads (expected-class excess, vacuity-robust)
        def read_share(d, v):
            tot = d.get("afflicted", 0) + d.get("mixed", 0) + d.get("favourable", 0)
            return d.get(v, 0) / tot if tot else 0.0
        J = read_share(pc, expected) - read_share(ref, expected)
        # degree-level delta on the expected class
        pos = f[f.reality_side == "positive"]
        refside = "contrast" if n_ctr >= N_MIN else "background"
        refg = f[f.reality_side == refside]
        d_strong = (((pos.eng_verdict == expected) & (pos.eng_degree == "strong")).mean()
                    - ((refg.eng_verdict == expected) & (refg.eng_degree == "strong")).mean())
        # calibration: P(positive | reading) among positive+reference
        pool = f[f.reality_side.isin(["positive", refside])]
        q = {}
        for v in ("afflicted", "mixed", "favourable"):
            g = pool[pool.eng_verdict == v]
            q[v] = float((g.reality_side == "positive").mean()) if len(g) >= 20 else None
        prev = float((pool.reality_side == "positive").mean())
        auc = mres.get(fid, {}).get("auc")
        ci = mres.get(fid, {}).get("ci", [None, None])
        # failure classification cascade
        sat = bg.get(expected, 0) >= T_SAT
        sat_opp = bg.get(opposite, 0) >= T_SAT
        if n_case < N_MIN:
            fclass = "UNDER-POWERED"
        elif auc is not None and ci[1] is not None and ci[1] < 0.5:
            fclass = "INVERTED"
        elif auc is not None and auc >= T_AUC_SUPP and ci[0] and ci[0] > 0.5:
            fclass = "SUPPORTED"
        elif auc is not None and auc >= T_AUC_WEAK and ci[0] and ci[0] > 0.5:
            fclass = "WEAK-SIGNAL"
        elif sat and abs(J) < T_J:
            fclass = f"SATURATED-{expected.upper()}"
        elif sat_opp and abs(J) < T_J:
            fclass = f"SATURATED-{opposite.upper()}-AGAINST"
        else:
            fclass = "PURE-NOISE"
        # slices: tier A vs B AUC (the birth-time-noise excuse test)
        ec = f"eng_H{h}_{sig}"
        def slice_auc(tier):
            sm = matrix[matrix.index.isin(m[m.quality_tier == tier].index)]
            cv = sm[sm[f"real_{fid}"] == 1][ec].dropna().to_numpy()
            if contrast:
                kv = sm[sm[f"real_{contrast}"] == 1][ec].dropna().to_numpy()
            else:
                kv = sm[sm[f"real_{fid}"] == 0][ec].dropna().to_numpy()
            return (auc_mw(cv, kv, direction)["auc"]
                    if len(cv) >= 20 and len(kv) >= 20 else None)
        summary[fid] = {
            "house": h, "signification": sig, "direction": direction,
            "n_case": n_case, "n_contrast": n_ctr, "n_background": n_bg, "ref": refside,
            "case_dist": pc, "ref_dist": ref, "background_dist": bg,
            "J_expected_excess": round(J, 4), "delta_strong": round(float(d_strong), 4),
            "calibration_q": q, "prevalence": round(prev, 4),
            "auc": auc, "auc_ci": ci, "failure_class": fclass,
            "auc_tierA": slice_auc("A"), "auc_tierB": slice_auc("B"),
        }

    # off-diagonal noise floor (from the matrix, |AUC-0.5| of every unmatched cell)
    floor_vals = []
    for fid, (_k, _p, h, sig, direction, contrast) in FEATURES.items():
        rc = f"real_{fid}"
        if rc not in matrix.columns:
            continue
        posm = matrix[matrix[rc] == 1]
        negm = (matrix[matrix[f"real_{contrast}"] == 1] if contrast else matrix[matrix[rc] == 0])
        for c in eng_cols:
            if c == f"eng_H{h}_{sig}":
                continue
            cv, kv = posm[c].dropna().to_numpy(), negm[c].dropna().to_numpy()
            if len(cv) >= 25 and len(kv) >= 25:
                floor_vals.append(abs(auc_mw(cv, kv, direction)["auc"] - 0.5))
    floor = {"p50": float(np.median(floor_vals)), "p95": float(np.percentile(floor_vals, 95)),
             "n_cells": len(floor_vals)}

    # per-house rollup
    houses: dict[int, dict] = {}
    for h in range(1, 13):
        feats = {fid: s for fid, s in summary.items() if s["house"] == h}
        bg_aff = [s["background_dist"].get("afflicted", 0) for s in feats.values()
                  if s["direction"] == "afflicted"]
        houses[h] = {
            "features": list(feats), "n_features": len(feats),
            "mean_abs_auc_dev": (float(np.mean([abs((s["auc"] or 0.5) - 0.5)
                                 for s in feats.values()])) if feats else None),
            "over_affliction_index": float(np.mean(bg_aff)) if bg_aff else None,
            "classes": sorted({s["failure_class"] for s in feats.values()}),
        }

    out = {"summary": summary, "houses": houses, "noise_floor": floor,
           "n_cases_rows": len(cases)}
    (_ATLAS / "atlas_results.json").write_text(json.dumps(out, indent=2, default=str),
                                               encoding="utf-8")

    # per-feature CSVs + interesting cases
    for fid in summary:
        f = cases[(cases.feature_id == fid) & (cases.reality_side != "background")]
        bgs = cases[(cases.feature_id == fid) & (cases.reality_side == "background")].sample(
            n=min(200, (cases.feature_id == fid).sum()), random_state=7)
        pd.concat([f, bgs]).sort_values("fame_score", ascending=False)[
            ["name_display", "birth_date", "quality_tier", "reality_side", "eng_verdict",
             "eng_degree", "cell_class", "fame_score", "lagna_sidereal"]].to_csv(
            _ATLAS / f"atlas_{fid}.csv", index=False, encoding="utf-8")
    interesting = cases[(cases.reality_side == "positive")
                        & cases.cell_class.isin(["AGREE_STRONG", "DISAGREE_STRONG"])]
    interesting.sort_values(["feature_id", "fame_score"], ascending=[True, False]).to_csv(
        _ATLAS / "interesting_cases.csv", index=False, encoding="utf-8")
    print(f"[atlas] cases={len(cases)}  features={len(summary)}  "
          f"noise-floor p95={floor['p95']:.3f} ({floor['n_cells']} cells)")
    return cases, out


def report(cases: pd.DataFrame, out: dict, path: Path, k_examples: int = 3,
           person_cap: int = 2) -> None:
    summary, houses, floor = out["summary"], out["houses"], out["noise_floor"]
    L: list[str] = []
    L.append("# The Failure Atlas — where the engine's readings meet real lives\n")
    L.append("> Per-case, per-house, per-feature statistics of the raman_saab engine against the "
             "AstroDatabank reality corpus (16,450 tier-A/B charts). Descriptive companion to "
             "[REAL_OUTCOME_GENERALIZATION.md](REAL_OUTCOME_GENERALIZATION.md) (THAT it fails) and "
             "[WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md](WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md) "
             "(WHY). Nothing here is a discovery claim; matched AUCs are the pre-registered "
             "Stage-7 numbers, never recomputed.\n")
    L.append("> All named individuals are public figures from the public AstroDatabank corpus; "
             "every stated life fact is that database's own published category label. No private "
             "(app_user) records appear in any name-bearing artifact.\n")

    L.append("\n## 1. The atlas at a glance\n")
    L.append("| feature | house·sig | n | AUC | J (expected-class excess) | Δstrong | "
             "background@expected | failure class |")
    L.append("|---|---|---|---|---|---|---|---|")
    for fid, s in sorted(summary.items(), key=lambda kv: (kv[1]["house"], kv[0])):
        exp = "afflicted" if s["direction"] == "afflicted" else "favourable"
        L.append(f"| {fid} | H{s['house']}·{s['signification']} | {s['n_case']} | "
                 f"{s['auc']:.3f} | {s['J_expected_excess']:+.3f} | {s['delta_strong']:+.3f} | "
                 f"{s['background_dist'].get(exp, 0):.0%} | {s['failure_class']} |"
                 if s["auc"] else
                 f"| {fid} | H{s['house']}·{s['signification']} | {s['n_case']} | — | "
                 f"{s['J_expected_excess']:+.3f} | {s['delta_strong']:+.3f} | "
                 f"{s['background_dist'].get(exp, 0):.0%} | {s['failure_class']} |")
    L.append(f"\nOff-diagonal noise floor (|AUC−.5| across {floor['n_cells']} unmatched cells): "
             f"median {floor['p50']:.3f}, p95 {floor['p95']:.3f}. A matched effect below the p95 "
             f"is indistinguishable from the field's own noise.\n")

    L.append("\n## 2. House heat table\n")
    L.append("| house | features tested | mean |AUC−.5| | over-affliction index | classes |")
    L.append("|---|---|---|---|---|")
    for h in range(1, 13):
        hh = houses[str(h)] if str(h) in houses else houses.get(h, {})
        if not hh or not hh.get("n_features"):
            L.append(f"| H{h} | — untested (no pre-registered reality feature) | | | |")
            continue
        oai = hh["over_affliction_index"]
        L.append(f"| H{h} | {', '.join(hh['features'])} | {hh['mean_abs_auc_dev']:.3f} | "
                 f"{oai:.0%} | {', '.join(hh['classes'])} |" if oai is not None else
                 f"| H{h} | {', '.join(hh['features'])} | {hh['mean_abs_auc_dev']:.3f} | — | "
                 f"{', '.join(hh['classes'])} |")

    L.append("\n## 3. Feature blocks — confusion, calibration, and named cases\n")
    appearances: dict[str, int] = {}
    for fid, s in sorted(summary.items(), key=lambda kv: (kv[1]["house"], kv[0])):
        L.append(f"\n### H{s['house']} · {s['signification']} ← `{fid}` "
                 f"(direction: {s['direction']}-expected) — **{s['failure_class']}**\n")
        L.append(f"| group | n | afflicted | mixed | favourable | abstain |")
        L.append("|---|---|---|---|---|---|")
        for label, dist, n in (("cases", s["case_dist"], s["n_case"]),
                               (f"reference ({s['ref']})", s["ref_dist"],
                                s["n_contrast"] if s["ref"] == "contrast" else s["n_background"]),
                               ("background", s["background_dist"], s["n_background"])):
            if dist:
                L.append(f"| {label} | {n} | {dist.get('afflicted',0):.0%} | "
                         f"{dist.get('mixed',0):.0%} | {dist.get('favourable',0):.0%} | "
                         f"{dist.get('insufficient-evidence',0):.0%} |")
        q = s["calibration_q"]
        qtxt = ", ".join(f"{v}→{q[v]:.1%}" for v in ("afflicted", "mixed", "favourable")
                         if q.get(v) is not None)
        ta = f"{s['auc_tierA']:.3f}" if s['auc_tierA'] else "—"
        tb = f"{s['auc_tierB']:.3f}" if s['auc_tierB'] else "—"
        L.append(f"\nCalibration P(case|reading): {qtxt or 'n too small'} "
                 f"(prevalence {s['prevalence']:.1%}). "
                 f"Tier-A AUC {ta} vs tier-B {tb} (the birth-time-noise test).\n")
        # named examples: top-fame DISAGREE_STRONG x2 + AGREE_STRONG x1, celebrity only, cap 2
        f = cases[(cases.feature_id == fid) & (cases.reality_side == "positive")
                  & (cases.name_display != "")]
        ex = []
        for cls, kk in (("DISAGREE_STRONG", k_examples - 1), ("AGREE_STRONG", 1)):
            pool = f[f.cell_class == cls].sort_values("fame_score", ascending=False)
            taken = 0
            for r in pool.itertuples():
                if taken >= kk:
                    break
                if appearances.get(r.person_id, 0) >= person_cap:
                    continue
                appearances[r.person_id] = appearances.get(r.person_id, 0) + 1
                ex.append(f"- **{r.name_display}** (b. {r.birth_date}, tier {r.quality_tier}) — "
                          f"engine read H{s['house']} {s['signification']} "
                          f"**{r.eng_verdict}-{r.eng_degree}**; reality: {fid}. [{cls}]")
                taken += 1
        if ex:
            L.append("Example cases:\n" + "\n".join(ex) + "\n")

    L.append("\n## 4. Caveats\n")
    L.append("- Reality labels are AstroDatabank's own category tags (coarse, era-dependent); "
             "the corpus is celebrity-selected.\n- The tier-A-vs-B columns test the "
             "birth-time-noise excuse: if time error blurred a real signal, minute-precision "
             "tier-A must out-perform tier-B.\n- Lagna slice uses AstroDatabank's published "
             "ascendants (tropical→sidereal, cusp rows flagged) — see atlas_results.json.\n"
             "- Governance: per METHODOLOGY.md, nothing here tunes the engine.\n")
    path.write_text("\n".join(L), encoding="utf-8")
    print(f"[atlas] report -> {path}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-out", type=Path,
                    default=_ATLAS / "FAILURE_ATLAS.md")
    a = ap.parse_args(argv)
    cases, out = build()
    report(cases, out, a.report_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
