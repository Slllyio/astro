"""Harshness diagnosis: replay the judge step by step and count the mechanisms that make a
matter afflicted, on Raman's confirmed conclusions and on random charts.

Diagnostic only; it changes no verdict. Record: docs/raman_saab/HARSHNESS_DIAGNOSIS_2026-10-30.md.

Usage:
    python -m tools.raman_saab.harshness_mechanisms --population 1000
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import random
from collections import Counter, defaultdict

from app.raman_saab import house_audit as ha
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.conditions import NATURAL_MALEFICS, EvalContext
from app.raman_saab.doctrine.significations import significations_of
from app.raman_saab.doctrine.yogas import detect_yogas, raja_yoga_vital
from app.raman_saab.judges import house_template as ht
from app.raman_saab.primitives.sphutas import beeja_kshetra

def trace(chart, house, sig, ctx):
    lagna = ht._build_frame_ledger(chart, sig, "lagna", ctx)
    moon = ht._build_frame_ledger(chart, sig, "moon", ctx)
    ls, ms = ht._total_shadbala(lagna.lord, chart), ht._total_shadbala(moon.lord, chart)
    lead = moon if (ls is not None and ms is not None and ms > ls) else lagna
    steps = []
    rasi,_ = ht._decide_clauses(dataclasses.replace(lead, navamsa_status="neutral"))
    steps.append(("rasi clauses (no D9)", rasi))
    v,_ = ht._decide_clauses(lead); steps.append(("clauses with D9", v))
    v,_ = ht._decide(lead); steps.append(("D9 one-step cap", v))
    v,_ = ht._decisive_affliction(v, lead, sig); steps.append(("decisive_affliction", v))
    v,_ = ht._catastrophic_severity_gate(sig, v, lead); steps.append(("catastrophic", v))
    fy = ctx.get_or_compute("fired_yogas", lambda: detect_yogas(chart))
    vital = frozenset(y.id for y in fy if y.kind == "raja" and raja_yoga_vital(chart, y.id))
    v,_,_ = ht._yoga_modulate(v, lead, sig, fy, vital); steps.append(("yoga", v))
    v,_,_ = ht._dhana_floor(v, lead, sig, fy); steps.append(("dhana_floor", v))
    v,bl,_ = ht._blemishless_venus_floor(chart, sig, v, lead); steps.append(("venus_floor", v))
    v,_ = ht._saptamsa_gate(chart, sig, v, lead, ctx); steps.append(("saptamsa", v))
    v,_,lead = ht._fertility_gate(chart, sig, v, lead, ctx); steps.append(("fertility", v))
    v,_ = ht._longevity_span(chart, sig, v, ctx); steps.append(("longevity_span", v))
    v,bmd = ht._marital_bond_gate(chart, sig, v, blem_lifted=bl); steps.append(("marital_bond", v))
    v,_ = ht._malefic_occupancy_gate(chart, sig, v, lead); steps.append(("malefic_occupancy", v))
    v,_ = ht._marginal_karaka_gate(chart, sig, v, lead, bond_demoted=bool(bmd)); steps.append(("marginal_karaka", v))
    v,_ = ht._yogakaraka_lagna_gate(chart, sig, v); steps.append(("yogakaraka_lagna", v))
    v,_ = ht._powerful_dhana_kendra_floor(chart, sig, v, lead); steps.append(("dhana_kendra", v))
    v,_ = ht._event_timing(chart, sig, v, lead, ctx); steps.append(("event_timing", v))
    return steps

def mechs(chart, house, sv, ctx):
    """Which mechanisms touched this matter's verdict."""
    L = sv.ledger; out = set()
    steps = trace(chart, house, next(s for s in significations_of(house) if s.key == sv.signification), ctx)
    names = [n for n, v in steps]; vals = [v for n, v in steps]
    def moved(step):
        i = names.index(step); return vals[i] != vals[i-1]
    if sv.verdict == "afflicted":
        if moved("fertility") and "beeja_kshetra" in dict(sv.metadata) and dict(sv.metadata)["beeja_kshetra"] == "weak":
            out.add("fertility_both_weak")
        if moved("fertility") and dict(sv.metadata).get("beeja_kshetra") == "one_weak_denied":
            out.add("fertility_one_weak")
        if moved("decisive_affliction"):
            ids = {f.rule.id for f in L.fired_malefic}
            if "H7.C.82" in ids:
                aff = [m for m in NATURAL_MALEFICS if (chart.planets[m].rasi_house == 7 or drishti.aspects_house(m, 7, chart))]
                out.add("H7.C.82_nodes_only" if set(aff) <= {"Rahu", "Ketu"} else "H7.C.82_other")
            else: out.add("decisive_other")
        cl, _ = ha.decide_clause(L)
        if cl.startswith("clause 6") and "active maraka" in cl and not L.fired_malefic:
            out.add("maraka_only_clause6")
        if moved("clauses with D9"): out.add("navamsa_push")
    return out

def golden():
    recs = {}
    for l in ha.GOLDENS_PATH.read_text().splitlines():
        if l.strip() and not l.startswith('#'):
            r = json.loads(l); recs[r['id']] = r
    tab = defaultdict(Counter)
    for rid, h, rv, _, _ in ha.precedent_index():
        rec = recs[rid]; ch = ha._golden_chart(rec); ctx = EvalContext(ch)
        keys = [e["signification"] for k, e in rec["expected_verdicts"].items() if int(k[1:]) == h]
        pf = ht.judge_house(ch, h)
        for sv in pf.significations:
            if sv.signification not in keys: continue
            for m in mechs(ch, h, sv, ctx): tab[m][rv] += 1
    return tab

def population(n=1000, seed=20261030):
    rnd = random.Random(seed)
    cities = [(26.45, 80.33), (28.61, 77.21), (19.08, 72.88), (12.97, 77.59), (22.57, 88.36), (13.08, 80.27)]
    head = Counter(); rule_worst = Counter(); m = Counter(); nm = 0; nch = 0
    for i in range(n):
        lat, lon = rnd.choice(cities)
        b = BirthData("p", rnd.randint(1950, 2005), rnd.randint(1, 12), rnd.randint(1, 28), rnd.randint(0, 23), rnd.randint(0, 59), 5.5, lat, lon)
        ch = cast_chart(b, ayanamsa="raman"); ctx = EvalContext(ch); nch += 1
        bk = beeja_kshetra(ch); m["chart: beeja and kshetra both weak"] += (not bk.beeja_strong and not bk.kshetra_strong)
        for h in range(1, 13):
            pf = ht.judge_house(ch, h); head[(h, pf.rollup)] += 1
            vs = [sv.verdict for sv in pf.significations]
            if pf.rollup == "afflicted" and vs.count("favourable") > len(vs) / 2: rule_worst[h] += 1
            for sv in pf.significations:
                nm += 1
                for x in mechs(ch, h, sv, ctx): m[x] += 1
    return nch, head, rule_worst, m, nm

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--population", type=int, default=1000)
    a = ap.parse_args(argv)
    g = golden()
    print("Raman's verdict where a mechanism decided an afflicted reading:")
    for k, c in sorted(g.items()):
        print(" ", k, dict(c))
    nch, head, rw, m, nm = population(a.population)
    print(f"Random charts: {nch} ({nm} matters)")
    for h in range(1, 13):
        print(f"  H{h}: headline afflicted {head[(h, 'afflicted')] / nch:.0%}, favourable "
              f"{head[(h, 'favourable')] / nch:.0%}, mixed {head[(h, 'mixed')] / nch:.0%}; "
              f"afflicted though most matters favourable {rw[h] / nch:.0%}")
    for k, v in sorted(m.items()):
        print(" ", k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
