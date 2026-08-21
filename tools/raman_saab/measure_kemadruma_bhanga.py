"""What each reading of 3HC:2187-2188 would cost (DOCTRINE_BACKLOG "Kemadruma bhanga
attribution").

No production code is edited: each candidate reading is a monkeypatched stand-in for
`bhangas.kemadruma_bhanga`, so the sweep can be re-run against any future version of the
real function to check the conclusions still hold.

The reason to sweep rather than argue: three of the five readings turn out to change nothing
at all, and one of those three (dropping the conjunction branch) is redundant by
construction rather than by luck. That is not visible from the text.

Usage:
    python -m tools.raman_saab.measure_kemadruma_bhanga
"""
from __future__ import annotations

import pathlib
import sys
from collections import Counter

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tests"))

from raman_saab import test_goldens as G  # noqa: E402

from app.raman_saab.primitives import bhangas as B  # noqa: E402
from app.raman_saab.doctrine import drishti  # noqa: E402
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS  # noqa: E402

_KENDRA = B._KENDRA


def make(a: bool, b: bool, c: bool, ext: bool):
    def fn(chart) -> bool:
        if "Moon" not in chart.planets:
            return False
        moon_h = chart.planets["Moon"].rasi_house
        if a and moon_h in _KENDRA:
            return True
        for name, pl in chart.planets.items():
            if name in ("Moon", "Rahu", "Ketu"):
                continue
            if a and pl.rasi_house in _KENDRA:
                return True
            if b and B._in_kendra_from(name, moon_h, chart):
                return True
            if c and pl.rasi_house == moon_h:
                return True
        if ext:
            for name in NATURAL_BENEFICS:
                if name != "Moon" and drishti.aspects_planet(name, "Moon", chart):
                    return True
        return False
    return fn


CHARTS = []
seen = set()
for rec in G._GOLDENS:
    k = G._id(rec)
    if k in seen:
        continue
    seen.add(k)
    CHARTS.append((k, G.build_chart(rec)))

GOLDEN = {}
for rec in G._TRACK_B_RATCHET:
    for house, entry in G.confirmed_verdicts(rec):
        GOLDEN[f"{G._id(rec)} H{house}/{entry['signification']}"] = entry["verdict"]

import app.raman_saab.judges.house_template as HT  # noqa: E402

_orig = B.kemadruma_bhanga


def install(fn):
    B.kemadruma_bhanga = fn
    # rebind every module that imported the symbol by value
    for mod in list(sys.modules.values()):
        if mod and getattr(mod, "__name__", "").startswith("app.raman_saab"):
            if getattr(mod, "kemadruma_bhanga", None) is not None:
                mod.kemadruma_bhanga = fn


def pinned():
    out = {}
    for rec in G._TRACK_B_RATCHET:
        chart = G.build_chart(rec)
        for house, entry in G.confirmed_verdicts(rec):
            out[f"{G._id(rec)} H{house}/{entry['signification']}"] = \
                G._signification_verdict(chart, house, entry["signification"])
    return out


def everything():
    out = {}
    for key, chart in CHARTS:
        for h in range(1, 13):
            for sv in HT.judge_house(chart, h).significations:
                out[f"{key}|H{h}|{sv.signification}"] = sv.verdict
    return out


def bhanga_rate(fn):
    return sum(1 for _k, c in CHARTS if B.kemadruma(c) and fn(c)), \
        sum(1 for _k, c in CHARTS if B.kemadruma(c))


READINGS = [
    ("R1 shipped: (a)(b)(c)+extended", True, True, True, True),
    ("R2 drop (c) conjunction", True, True, False, True),
    ("R3 drop extended drishti", True, True, True, False),
    ("R4 keep only what Raman works", True, True, False, False),
    ("R5 maximal dismissal: no bhanga", False, False, False, False),
]

install(make(True, True, True, True))
base_pin, base_all = pinned(), everything()
be, btot, _ = G.track_b_scoreboard()
bw, _t, breal = G.track_b_ordinal_scoreboard()
print(f"charts={len(CHARTS)}  significations={len(base_all)}")
hdr = f"{'reading':38} {'bhanga fires':>13} {'exact':>10} {'within-1':>10} {'real':>5} {'moved':>7}"
print(hdr)
print("-" * len(hdr))
notes = []
for name, a, b, c, ext in READINGS:
    fn = make(a, b, c, ext)
    install(fn)
    fires, formed = bhanga_rate(fn)
    e, tot, _ = G.track_b_scoreboard()
    w1, _tt, real = G.track_b_ordinal_scoreboard()
    allv, pin = everything(), pinned()
    moved = sum(1 for k in base_all if base_all[k] != allv[k])
    print(f"{name:38} {fires:6}/{formed:<6} {e:4}/{tot:<5} {w1:4}/{tot:<5} "
          f"{len(real):5} {moved:7}")
    pm = [(k, base_pin[k], pin[k], GOLDEN[k]) for k in GOLDEN if base_pin[k] != pin[k]]
    kinds = Counter(f"{base_all[k]} -> {allv[k]}" for k in base_all if base_all[k] != allv[k])
    notes.append((name, pm, kinds))
install(_orig)

for name, pm, kinds in notes:
    if not pm and not kinds:
        continue
    print(f"\n=== {name} ===")
    for k, v in kinds.most_common():
        print(f"    {v:5} x  {k}")
    for k, was, now, gold in pm:
        mark = "FIXED " if now == gold else "BROKE " if was == gold else "moved "
        print(f"    {mark}{k}: {was} -> {now}   (Raman: {gold})")
