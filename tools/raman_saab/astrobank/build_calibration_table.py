"""Stage 9 — build the population-calibration table from the astrobank background distributions.

The Failure Atlas proved the engine's verdicts are DEGENERATE AS STATEMENTS on ordinary charts
(e.g. 76% of all charts read H5-children afflicted): a reading carries no population context. This
tool emits the committed `calibration_table.json` — for every (house, signification), the empirical
distribution of the 7-level verdict-degree score over the 16,450-chart tier-A/B population, plus
the atlas failure-class — consumed by the report-only `judges/calibrated_reading.py` overlay.

GOVERNANCE (METHODOLOGY.md): this does NOT tune the engine — no constant, threshold, or rule
changes; the verdict path and golden ratchet are untouched. The overlay only CONTEXTUALIZES
unchanged Raman verdicts against the population (the monitoring axis made visible), and its content
is provenance-tagged EMPIRICAL_ASTRODATABANK (explicitly not-Raman).

The table is an aggregate over a gitignored corpus (population shares only — no personal data) and
is safe to commit. Usage: py -3.12 -m tools.raman_saab.astrobank.build_calibration_table
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_OUT = Path("data/astro_databank/derived/raman")
# NOTE: not under any `data/` path — the blanket data/ gitignore rule would swallow it,
# and this table must be committed (the calibrated_reading overlay depends on it).
_TABLE = Path("app/raman_saab/doctrine/calibration_table.json")

#: the 7-level score ladder (verdict x degree), matching engine_reality_matrix._DEG/_ORD
_LEVELS = [
    ("afflicted", "strong"), ("afflicted", "moderate"), ("afflicted", "mild"),
    ("mixed", None),
    ("favourable", "mild"), ("favourable", "moderate"), ("favourable", "strong"),
]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    verd = pd.read_parquet(_OUT / "verdicts.parquet")
    pop = pd.read_parquet(_OUT / "store_population.parquet")
    master = pd.read_parquet(_OUT / "person_master.parquet").set_index("person_id")
    tier = set(master[master.quality_tier.isin(["A", "B"])].index) & set(pop.person_id)
    v = verd[verd.person_id.isin(tier)]
    atlas = json.loads((_OUT / "failure_atlas" / "atlas_results.json").read_text(encoding="utf-8"))
    fclass_by_sig = {}
    for fid, s in atlas["summary"].items():
        key = f"H{s['house']}_{s['signification']}"
        # a signification can carry several features; keep the most severe class label list
        fclass_by_sig.setdefault(key, []).append(f"{fid}:{s['failure_class']}")

    table: dict[str, dict] = {}
    for (h, sig), g in v.groupby(["house", "signification"]):
        n = len(g)
        shares = []
        for verdict, degree in _LEVELS:
            if degree is None:
                cnt = int(((g.verdict == verdict)).sum())
            else:
                cnt = int(((g.verdict == verdict) & (g.degree == degree)).sum())
            shares.append(round(cnt / n, 5))
        abstain = round(float((g.verdict == "insufficient-evidence").mean()), 5)
        key = f"H{h}_{sig}"
        table[key] = {
            "house": int(h), "signification": sig, "n": int(n),
            "levels": [f"{v_}{'-' + d if d else ''}" for v_, d in _LEVELS],
            "shares": shares, "abstain": abstain,
            "atlas_failure_classes": fclass_by_sig.get(key, []),
        }
    out = {
        "_provenance": "EMPIRICAL_ASTRODATABANK — population distribution of engine readings over "
                       "16,450 tier-A/B AstroDatabank charts (failure-atlas Stage 9). NOT Raman "
                       "doctrine. Consumed only by the report-only calibrated_reading overlay; "
                       "never by the verdict path (METHODOLOGY.md governance).",
        "population_n": len(tier),
        "inverted_channels": ["H3_courage", "H12_incarceration"],
        "table": table,
    }
    _TABLE.parent.mkdir(parents=True, exist_ok=True)
    _TABLE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"[calibration] wrote {_TABLE} — {len(table)} significations, n={len(tier)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
