"""Tally judge T1 (docs/raman_saab/TALLY_JUDGE_PREREG_2026-10-31.md).

Adds up, from the chart alone, the factor types Raman checks for a matter (lord, occupants,
aspects, hemming, 6/8/12 lords, karaka, Navamsa, routed yogas) in three frames (Lagna, Moon,
karaka), each instance +1 or -1, then maps the sum to a verdict with a three-number ordinal
model. Never reads hold-outs 4 or 5 unless `final` is given (user's say-so required).

Usage: python -m tools.raman_saab.tally_judge dev | freeze | final
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

from scipy.optimize import minimize

DIR = Path("docs/raman_saab/tally_judge")
PARAMS = DIR / "t1_frozen.json"
DEV_SETS = {"H1": "tests/fixtures/raman_holdout_sealed.jsonl",
            "H2": "tests/fixtures/raman_holdout2_sealed.jsonl",
            "H3": "tests/fixtures/raman_holdout3_sealed.jsonl"}
FINAL_SETS = {"H4": "tests/fixtures/raman_holdout4_sealed.jsonl",
              "H5": "tests/fixtures/raman_holdout5_sealed.jsonl"}
CLASSES = ("afflicted", "mixed", "favourable")
BENEFICS = ("Jupiter", "Venus", "Mercury")
MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
GOOD_DIGNITY = {"exalt", "moolatrikona", "own"}
BAD_DIGNITY = {"debil", "enemy"}


def _sign_of_house(frame_sign: int, n: int) -> int:
    return (frame_sign + n - 2) % 12 + 1


def _lagna_house(chart, sign: int) -> int:
    return (sign - chart.asc_sign) % 12 + 1


def _house_from(chart, frame_sign: int, planet: str) -> int:
    return (chart.planets[planet].sign - frame_sign) % 12 + 1


def _associations(chart, planet, drishti):
    """+1 per benefic joining/aspecting, -1 per malefic, -1 if combust."""
    p = chart.planets[planet]
    s = 0
    for q in chart.planets:
        if q == planet:
            continue
        touches = chart.planets[q].sign == p.sign or drishti.aspects_planet(q, planet, chart)
        if touches:
            s += 1 if q in BENEFICS else -1 if q in MALEFICS else 0
    if p.combust_fraction > 0:
        s -= 1
    return s


def _dignity_score(chart, planet, dignity):
    if planet in ("Rahu", "Ketu"):
        return 0
    d = dignity(planet, chart)
    return 1 if d in GOOD_DIGNITY else -1 if d in BAD_DIGNITY else 0


def _navamsa_score(chart, planet, rel, SIGN_LORDS):
    if planet in ("Rahu", "Ketu") or planet not in chart.planets:
        return 0
    nav = chart.planets[planet].navamsa_sign
    if nav == rel.EXALTATION[planet][0] or SIGN_LORDS[nav] == planet:
        return 1
    if nav == rel.DEBILITATION[planet][0]:
        return -1
    return 0


def factors(chart, house: int, sig: str, karaka: str) -> dict[str, int]:
    from app.raman_saab.chart.constants import SIGN_LORDS
    from app.raman_saab.doctrine import drishti, hemming
    from app.raman_saab.doctrine.yoga_routes import YOGA_ROUTES, routes_to
    from app.raman_saab.doctrine.yogas import YOGAS, detect_yogas
    from app.raman_saab.primitives import relationships as rel
    from app.raman_saab.primitives.dignity import dignity

    f = {k: 0 for k in ("lord_place", "lord_dignity", "lord_assoc", "occupants", "aspects",
                        "hemming", "dusthana_lords", "karaka", "navamsa", "yogas")}
    frames = [chart.asc_sign]
    if "Moon" in chart.planets:
        frames.append(chart.planets["Moon"].sign)
    if karaka in chart.planets:
        frames.append(chart.planets[karaka].sign)
    lagna_lord = None
    for fs in frames:
        tsign = _sign_of_house(fs, house)
        th = _lagna_house(chart, tsign)
        lord = SIGN_LORDS[tsign]
        if fs == chart.asc_sign:
            lagna_lord = lord
        if lord in chart.planets:
            d = _house_from(chart, fs, lord)
            f["lord_place"] += 1 if d in (1, 4, 7, 10, 5, 9) else -1 if d in (6, 8, 12) else 0
            f["lord_dignity"] += _dignity_score(chart, lord, dignity)
            f["lord_assoc"] += _associations(chart, lord, drishti)
            if drishti.aspects_house(lord, th, chart) and chart.planets[lord].rasi_house != th:
                f["aspects"] += 1
        for q, p in chart.planets.items():
            if q == lord:
                continue
            if p.rasi_house == th:
                f["occupants"] += 1 if q in BENEFICS else -1 if q in MALEFICS else 0
            elif drishti.aspects_house(q, th, chart):
                f["aspects"] += 1 if q in BENEFICS else -1 if q in MALEFICS else 0
        if hemming.hemmed_house(chart, th, "malefic"):
            f["hemming"] -= 1
        if hemming.hemmed_house(chart, th, "benefic"):
            f["hemming"] += 1
        for dn in (6, 8, 12):
            dl = SIGN_LORDS[_sign_of_house(fs, dn)]
            if dl != lord and dl in chart.planets and chart.planets[dl].rasi_house == th:
                f["dusthana_lords"] -= 1
    if karaka in chart.planets:
        f["karaka"] += _dignity_score(chart, karaka, dignity)
        if chart.planets[karaka].rasi_house in (6, 8, 12):
            f["karaka"] -= 1
        f["karaka"] += _associations(chart, karaka, drishti)
        f["navamsa"] += _navamsa_score(chart, karaka, rel, SIGN_LORDS)
    if lagna_lord and lagna_lord != karaka:
        f["navamsa"] += _navamsa_score(chart, lagna_lord, rel, SIGN_LORDS)
    kinds = {y.id: y.kind for y in YOGAS}
    progeny_curses = {yid for yid, route in YOGA_ROUTES.items() if route == ((5, frozenset({"children"})),)}
    for y in detect_yogas(chart):
        if routes_to(y.id, house, sig):
            f["yogas"] += -1 if (kinds.get(y.id) == "arishta" or y.id in progeny_curses) else 1
    return f


def _load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]


def rows_for(recs, confirmed_only):
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    import app.raman_saab.judges.house_template as ht
    out = []
    for r in recs:
        ch = tg.build_chart(r)
        pfs = {}
        for h, e in r["expected_verdicts"].items():
            if confirmed_only and not tg._is_confirmed(e):
                continue
            hn = int(h[1:])
            pf = pfs.setdefault(hn, ht.judge_house(ch, hn))
            sv = next((s for s in pf.significations if s.signification == e["signification"]), None)
            karaka = sv.karaka if sv else ""
            fx = factors(ch, hn, e["signification"], karaka)
            out.append({"key": f"{r['id']} {h}/{e['signification']}", "chart": r["id"], "gold": e["verdict"],
                        "E": sv.verdict if sv else None,
                        "nb": len(sv.ledger.fired_benefic) if sv else 0,
                        "nm": len(sv.ledger.fired_malefic) if sv else 0,
                        "f": fx, "S": sum(fx.values())})
    return out


def _probs(t, s):
    a, c1, d = t
    c2 = c1 + math.exp(d)
    sig = lambda z: 1 / (1 + math.exp(-z))
    pa = 1 - sig(a * s - c1); pf = sig(a * s - c2)
    return (pa, max(1e-9, 1 - pa - pf), pf)


def fit(rows):
    y = [CLASSES.index(r["gold"]) for r in rows]
    nll = lambda t: sum(-math.log(max(1e-12, _probs(t, r["S"])[k])) for r, k in zip(rows, y))
    best = min((minimize(nll, s0, method="Nelder-Mead", options={"maxiter": 20000})
                for s0 in ([0.2, 0.0, 0.0], [0.5, -1.0, 0.5], [0.1, 1.0, -0.5])), key=lambda r: r.fun)
    return list(best.x)


def _dist(a, b):
    o = {"favourable": 0, "mixed": 1, "afflicted": 2}
    return 0 if a == b else (abs(o[a] - o[b]) if a in o and b in o else 2)


def score(rows, preds, probs=None, freq=None):
    n = len(rows)
    rec = [sum(p == c for p, r in zip(preds, rows) if r["gold"] == c) / max(1, sum(r["gold"] == c for r in rows))
           for c in CLASSES if any(r["gold"] == c for r in rows)]
    out = {"n": n, "exact": sum(p == r["gold"] for p, r in zip(preds, rows)),
           "within1": sum(_dist(p, r["gold"]) <= 1 for p, r in zip(preds, rows)),
           "real": sum(_dist(p, r["gold"]) >= 2 for p, r in zip(preds, rows)),
           "macro_recall": round(sum(rec) / len(rec), 3)}
    if probs is not None:
        out["logloss"] = round(sum(-math.log(max(1e-12, p[CLASSES.index(r["gold"])])) for p, r in zip(probs, rows)) / n, 4)
    if freq is not None:
        out["freq_logloss"] = round(sum(-math.log(freq[r["gold"]]) for r in rows) / n, 4)
    return out


def b3(r):
    return "favourable" if r["nb"] >= r["nm"] else "afflicted"


def report(name, rows, t, freq):
    pp = [_probs(t, r["S"]) for r in rows]
    pred = [CLASSES[max(range(3), key=lambda k: p[k])] for p in pp]
    res = {"T1": score(rows, pred, pp, freq), "B3": score(rows, [b3(r) for r in rows]),
           "E": score(rows, [r["E"] for r in rows]),
           "T1_says": {c: pred.count(c) for c in CLASSES}}
    print(name, json.dumps(res))
    return res, pred


def _freq(rows):
    return {c: sum(r["gold"] == c for r in rows) / len(rows) for c in CLASSES}


def main(cmd):
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    DIR.mkdir(parents=True, exist_ok=True)
    pool = rows_for(tg._TRACK_B_RATCHET, True)
    dev = [r for p in DEV_SETS.values() for r in rows_for(_load(p), False)]
    if cmd == "dev":
        t = fit(pool)
        print("theta (pool)", [round(x, 4) for x in t])
        freq = _freq(pool)
        report("pool (in-sample)", pool, t, freq)
        res, _ = report("H1-3 (dev check)", dev, t, freq)
        json.dump({"theta_pool": t, "dev": res}, open(DIR / "t1_dev.json", "w"), indent=1)
    elif cmd == "freeze":
        allr = pool + dev
        t = fit(allr)
        verdicts = {r["key"]: CLASSES[max(range(3), key=lambda k: _probs(t, r["S"])[k])] for r in allr}
        sha = hashlib.sha256(json.dumps(verdicts, sort_keys=True).encode()).hexdigest()
        json.dump({"theta": t, "freq": _freq(allr), "sha_dev_verdicts": sha}, open(PARAMS, "w"), indent=1)
        print("frozen", t, sha)
    elif cmd == "final":
        fz = json.load(open(PARAMS))
        rows = [r for p in FINAL_SETS.values() for r in rows_for(_load(p), False)]
        report("H4+H5 (final, one time)", rows, fz["theta"], fz["freq"])


if __name__ == "__main__":
    main(sys.argv[1])
