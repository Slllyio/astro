"""Measure the directional-parivartana arms (DOCTRINE_BACKLOG "Directional parivartana").

Both arms ship OFF. This sweeps every combination on BOTH ratchet axes AND on the blast
radius — every signification the engine judges across the golden charts — because the
ratchet alone cannot distinguish "changes nothing" from "changes a lot, scoring the same".
Arm A turned out to be the first; arm B the second.

Rebinding the module flags is exactly how `tune_thresholds.py` drives the CONTRA_PILLAR_*
knobs; the flags are documented as read-LIVE for this reason.

Usage:
    python -m tools.raman_saab.measure_directional_parivartana
"""
from __future__ import annotations

import pathlib
import sys
from collections import Counter

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tests"))

from raman_saab import test_goldens as G  # noqa: E402

from app.raman_saab.judges import house_template as HT  # noqa: E402

CHARTS = []
seen: set[str] = set()
for rec in G._GOLDENS:
    k = G._id(rec)
    if k in seen:
        continue
    seen.add(k)
    CHARTS.append((k, G.build_chart(rec)))

GOLDEN: dict[str, str] = {}
for rec in G._TRACK_B_RATCHET:
    for house, entry in G.confirmed_verdicts(rec):
        GOLDEN[f"{G._id(rec)} H{house}/{entry['signification']}"] = entry["verdict"]


def pinned() -> dict[str, str]:
    out = {}
    for rec in G._TRACK_B_RATCHET:
        chart = G.build_chart(rec)
        for house, entry in G.confirmed_verdicts(rec):
            out[f"{G._id(rec)} H{house}/{entry['signification']}"] = \
                G._signification_verdict(chart, house, entry["signification"])
    return out


def everything() -> dict[str, str]:
    out = {}
    for key, chart in CHARTS:
        for h in range(1, 13):
            for sv in HT.judge_house(chart, h).significations:
                out[f"{key}|H{h}|{sv.signification}"] = sv.verdict
    return out


def set_flags(a: bool, b: bool, test: str) -> None:
    HT.PARIVARTANA_DIRECTIONAL, HT.PARIVARTANA_TRANSMITS = a, b
    HT.PARIVARTANA_PARTNER_TEST = test


set_flags(False, False, "either")
base_pin, base_all = pinned(), everything()
b_exact, b_tot, _ = G.track_b_scoreboard()
b_w1, _wt, b_real = G.track_b_ordinal_scoreboard()
print(f"baseline           exact={b_exact}/{b_tot}  within-1={b_w1}/{b_tot}  "
      f"real-errors={len(b_real)}  (of {len(base_all)} significations judged"
      f" across {len(CHARTS)} charts)\n")

hdr = f"{'variant':38} {'exact':>9} {'within-1':>9} {'real':>5} {'moved':>7} {'%':>6}"
print(hdr)
print("-" * len(hdr))
details = []
for arm, a, b in (("A withhold", True, False), ("B transmit", False, True),
                  ("A+B", True, True)):
    for test in ("condition", "dusthana", "either"):
        set_flags(a, b, test)
        e, tot, _ = G.track_b_scoreboard()
        w1, _t, real = G.track_b_ordinal_scoreboard()
        allv, pin = everything(), pinned()
        moved = sum(1 for k in base_all if base_all[k] != allv[k])
        name = f"{arm} / partner={test}"
        print(f"{name:38} {e:4}/{tot:<4} {w1:4}/{tot:<4} {len(real):5} "
              f"{moved:7} {100.0*moved/len(base_all):5.2f}%")
        pin_moved = [(k, base_pin[k], pin[k], GOLDEN[k])
                     for k in GOLDEN if base_pin[k] != pin[k]]
        kinds = Counter(f"{base_all[k]} -> {allv[k]}" for k in base_all
                        if base_all[k] != allv[k])
        details.append((name, pin_moved, kinds))
set_flags(False, False, "either")

for name, pin_moved, kinds in details:
    if not pin_moved and not kinds:
        continue
    print(f"\n=== {name} ===")
    for k, v in kinds.most_common():
        print(f"    {v:5} x  {k}")
    for k, was, now, gold in pin_moved:
        mark = "FIXED " if now == gold else "BROKE " if was == gold else "moved "
        print(f"    {mark}{k}: {was} -> {now}   (Raman: {gold})")
