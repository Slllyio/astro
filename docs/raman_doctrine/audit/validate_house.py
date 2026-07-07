"""Held-out audit harness for the house strength point-scheme (imports LIVE scheme).

Usage:
  PYTHONPATH=. python3 docs/raman_doctrine/audit/validate_house.py \
      docs/raman_doctrine/audit/corpora/*.json [-v]

Each corpus row encodes a Raman worked-chart factor as the assessor sees it (feature
tokens) with his verdict on the 9-grade scale; ``delta_of`` maps every token to the
LIVE scheme weight, so the harness re-runs the live ``_combine`` and reports how far
each prediction lands from Raman (within-one is the target). Holdout = chart_no % 3.
Multiple corpora are pooled; per-corpus and combined stats are printed.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from app.medini.doctrine.domains.house_judgment import (
    _DIGNITY_W, _W, Finding, VERDICT_SCALE, _combine, _verdict_label,
)

IDX = {lab: i for i, lab in enumerate(VERDICT_SCALE)}


def delta_of(feat: dict) -> float:
    t = feat["type"]
    if t == "placement":
        return {"dusthana": _W["dusthana"], "kendra_trikona": _W["kendra_trikona"]}[feat["where"]]
    if t == "vargottama":
        return _W["vargottama"]
    if t == "neechabhanga":
        return _W["neechabhanga"]
    if t == "dignity":
        return _DIGNITY_W[feat["state"]]
    if t == "aspect":
        return _W["aspect"] if feat["benefic"] else -_W["aspect"]
    if t == "bhava_aspect":
        # Phase 2.3: an exalted planet aspecting the bhava is credited like an
        # exalted companion (conjunct_exalted), scaled to the bhava-aspect weight.
        if feat.get("exalted"):
            return _W["conjunct_exalted"] * _W["bhava_aspect_mul"]
        base = _W["aspect"] if feat["benefic"] else -_W["aspect"]
        return base * _W["bhava_aspect_mul"]
    if t == "occupant":
        # Phase 2.1: an occupant's dignity colours the bhava. Mirror _assess_bhava:
        # exalted replaces the ±0.7 nature; own/debil/neechabhanga add to it.
        dg = feat.get("dignity")
        if dg == "exalted":
            return _W["conjunct_exalted"]
        base = _W["conjunct"] if feat["benefic"] else -_W["conjunct"]
        if dg == "own":
            return base + _DIGNITY_W["own"]
        if dg == "debilitated":
            return base + _DIGNITY_W["debilitated"]
        if dg == "neechabhanga":
            return base + _W["neechabhanga"]
        return base
    if t == "conjunct":
        if feat.get("exalted"):
            return _W["conjunct_exalted"]
        return _W["conjunct"] if feat["benefic"] else -_W["conjunct"]
    if t == "kartari":
        return _W["kartari_subha"] if feat["kind"] == "subha" else _W["kartari_papa"]
    raise ValueError(f"unknown feature type {t!r}")


def predict(row: dict) -> tuple[str, float]:
    findings = [Finding(f.get("why", f["type"]), round(delta_of(f), 3),
                        f.get("frame", "Rasi"), f["type"]) for f in row["findings"]]
    score, _r, _n = _combine(findings, additive=row["additive"])
    return _verdict_label(score), score


def stats(name, ds):
    n = len(ds)
    if not n:
        return
    exact = sum(1 for x in ds if x == 0)
    w1 = sum(1 for x in ds if abs(x) <= 1)
    over = sum(1 for x in ds if x > 1)
    under = sum(1 for x in ds if x < -1)
    print(f"{name:<10} n={n:<3} exact={exact:<3}({exact/n:.0%})  within1={w1:<3}({w1/n:.0%})  "
          f"over>1={over}  under>1={under}  mean={sum(ds)/n:+.2f}")


def main():
    pooled = {"OVERALL": [], "TRAIN": [], "HOLDOUT": []}
    verbose = "-v" in sys.argv
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    for path in paths:
        corpus = json.loads(Path(path).read_text())
        rows = corpus["rows"]
        local = []
        for row in rows:
            pred, score = predict(row)
            d = IDX[pred] - IDX[row["expected"]]
            split = "HOLDOUT" if row["chart"] % 3 == 0 else "TRAIN"
            pooled["OVERALL"].append(d); pooled[split].append(d); local.append(d)
            if verbose and abs(d) > 1:
                print(f"  {corpus.get('house','?')}/{row['chart']} {row['role']:<7} "
                      f"{row['subject'][:20]:<20} pred={pred:<14} raman={row['expected']:<14} {d:+d}")
        stats(f"h{corpus.get('house','?')}", local)
    print("-" * 72)
    for k in ("OVERALL", "TRAIN", "HOLDOUT"):
        stats(k, pooled[k])


if __name__ == "__main__":
    main()
