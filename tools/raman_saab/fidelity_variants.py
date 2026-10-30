"""Pre-registered fidelity-fix variants R1, R3b, R4, G1, N1, G2 (docs/raman_saab/FIDELITY_FIXES_PREREG.md).

Measurement only: every variant is applied by rebinding judge functions at run time, so the
shipped engine is untouched until a variant passes the pre-registered decision rule.

Usage:
    python -m tools.raman_saab.fidelity_variants V0 R1 R3b R4 [--json out.json]
    python -m tools.raman_saab.fidelity_variants --gate1
"""
from __future__ import annotations

import dataclasses
import json
import sys
from typing import Optional

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.judges import house_template as ht
from app.raman_saab.primitives import sphutas
from app.raman_saab.primitives.bhangas import neecha_bhanga
from app.raman_saab.primitives.dignity import dignity

NATURAL_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
FIRM_BENEFICS = frozenset({"Jupiter", "Venus"})


def _contacts(planet: str, chart: RamanChart) -> tuple[bool, bool]:
    p = chart.planets[planet]
    mal = ben = False
    for other, q in chart.planets.items():
        if other == planet:
            continue
        if q.sign == p.sign or drishti.aspects_planet(other, planet, chart):
            mal = mal or other in NATURAL_MALEFICS
            ben = ben or other in FIRM_BENEFICS
    return mal, ben


def raman_condition(planet: str, chart: RamanChart, matter_sign: int) -> Optional[bool]:
    """R1: True strong / False weak / None = no Raman-grammar reading (caller falls back)."""
    p = chart.planets.get(planet)
    if p is None:
        return None
    if planet not in ("Rahu", "Ketu"):
        if dignity(planet, chart) == "debil" and not neecha_bhanga(planet, chart):
            return False
        if planet != "Sun" and p.combust_fraction > 0.0:
            return False
    weak = strong = False
    if ((p.sign - matter_sign) % 12) + 1 in (6, 8, 12):
        weak = True
    mal, ben = _contacts(planet, chart)
    if mal and not ben:
        weak = True
    if ben and not mal:
        strong = True
    if planet not in ("Rahu", "Ketu") and dignity(planet, chart) in ("exalt", "own", "moolatrikona"):
        strong = True
    if weak and not strong:
        return False
    if strong and not weak:
        return True
    return None


def _frame_sign(chart: RamanChart, frame: str, sig) -> int:
    if frame == "moon" and "Moon" in chart.planets:
        return chart.planets["Moon"].sign
    if frame == "karaka" and sig.alternate_frame_core in chart.planets:
        return chart.planets[sig.alternate_frame_core].sign
    return chart.asc_sign


_ORIG_LEDGER = ht._build_frame_ledger
_ORIG_DECIDE = ht._decide


def _r1_ledger(chart, sig, frame, ctx=None):
    L = _ORIG_LEDGER(chart, sig, frame, ctx)
    matter_sign = ((_frame_sign(chart, frame, sig) - 1 + sig.house - 1) % 12) + 1
    lc = raman_condition(L.lord, chart, matter_sign)
    kc = raman_condition(L.karaka, chart, matter_sign)
    ls = L.lord_strong if lc is None else lc
    ks = ls if L.lord_karaka_identical else (L.karaka_strong if kc is None else kc)
    return dataclasses.replace(L, lord_strong=ls, karaka_strong=ks)


def _preponderance(L) -> Optional[str]:
    b = len({f.rule.id for f in L.fired_benefic})
    m = len({f.rule.id for f in L.fired_malefic})
    return "favourable" if b > m else "afflicted" if m > b else None


def _make_tiebreak(cast: bool, stated: bool):
    def _decide(L):
        v, shifted = _ORIG_DECIDE(L)
        if v != "mixed":
            return v, shifted
        sparse = L.lord_strong is None and L.karaka_strong is None
        if (sparse and stated) or (not sparse and cast):
            p = _preponderance(L)
            if p is not None:
                return p, True
        return v, shifted
    return _decide


def apply(variants: set[str]) -> None:
    ht._build_frame_ledger = _r1_ledger if "R1" in variants else _ORIG_LEDGER
    cast, stated = "R3b" in variants, "R4" in variants
    ht._decide = _make_tiebreak(cast, stated) if (cast or stated) else _ORIG_DECIDE
    from app.raman_saab.doctrine.rule_sets.house_07_kalatra import combinations as h7c
    ht.G1_FERTILITY_ONE_STEP = "G1" in variants          # Addendum 16
    h7c.NODE_AXIS_AS_ONE = "N1" in variants              # Addendum 16
    sphutas.G2_PRINTED_SPHUTA_TEST = "G2" in variants     # Addendum 18


def run(variants: set[str]) -> dict[str, tuple[str, str, Optional[str]]]:
    from tests.raman_saab import test_goldens as tg
    apply(variants)
    rows = {}
    try:
        for rec in tg._TRACK_B_RATCHET:
            chart = tg.build_chart(rec)
            for house, e in tg.confirmed_verdicts(rec):
                got = tg._signification_verdict(chart, house, e["signification"])
                rows[f"{rec['id']} H{house}/{e['signification']}"] = (rec["book"], e["verdict"], got)
    finally:
        apply(set())
    return rows


def score(rows) -> dict[str, tuple[int, int, int, int]]:
    from tests.raman_saab import test_goldens as tg
    out = {}
    for bk in ("ALL", "HTJAH-I", "HTJAH-II", "NH"):
        R = [v for v in rows.values() if bk == "ALL" or v[0] == bk]
        d = [tg._ordinal_distance(g, x) for _, x, g in R]
        out[bk] = (sum(z == 0 for z in d), sum(z <= 1 for z in d), sum(z >= 2 for z in d), len(R))
    return out


def passes(base, var) -> bool:
    """The pre-registered decision rule."""
    for bk in ("ALL", "HTJAH-I", "HTJAH-II", "NH"):
        if var[bk][2] > base[bk][2]:
            return False
    if var["ALL"][1] < base["ALL"][1]:
        return False
    return var["ALL"][0] > base["ALL"][0] or var["ALL"][2] < base["ALL"][2]


def gate1(words_path: str = "/tmp/claude-0/re/words.json") -> None:
    """R1 gate 1: agreement with Raman's strong/weak words, R1 vs current pillar (cast rows)."""
    from tests.raman_saab import test_goldens as tg
    from app.raman_saab.doctrine.significations import significations_of
    W = {w["key"]: w for w in json.load(open(words_path))}
    recs = {r["id"]: r for r in tg._TRACK_B_RATCHET}
    tallies = {"lord": [0, 0, 0], "karaka": [0, 0, 0]}  # [n, current agrees, R1 agrees]
    for key, w in W.items():
        if w["cast"] != "birth":
            continue
        rid, hs = key.split(" ")
        house = int(hs.split("/")[0][1:]); sk = hs.split("/")[1]
        chart = tg.build_chart(recs[rid])
        sig = next(s for s in significations_of(house) if s.key == sk)
        pf = ht.judge_house(chart, house)
        sv = next(s for s in pf.significations if s.signification == sk)
        L = sv.ledger
        matter_sign = ((_frame_sign(chart, L.frame, sig) - 1 + house - 1) % 12) + 1
        for role, planet, cur in (("lord", L.lord, L.lord_strong), ("karaka", L.karaka, L.karaka_strong)):
            word = w[f"{role}_word"]
            if word not in ("strong", "weak"):
                continue
            rc = raman_condition(planet, chart, matter_sign)
            r1 = cur if rc is None else rc
            truth = word == "strong"
            t = tallies[role]
            t[0] += 1; t[1] += (cur is truth); t[2] += (r1 is truth)
    for role, (n, c, r) in tallies.items():
        print(f"gate1 {role}: n={n} current={c} R1={r}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--gate1" in args:
        gate1(); sys.exit(0)
    out = None
    if "--json" in args:
        out = args[args.index("--json") + 1]; args = [a for a in args if a not in ("--json", out)]
    res = {}
    for v in args:
        vs = set() if v == "V0" else set(v.split("+"))
        rows = run(vs); res[v] = rows
        print(v, score(rows), flush=True)
    if out:
        json.dump(res, open(out, "w"), indent=0)
