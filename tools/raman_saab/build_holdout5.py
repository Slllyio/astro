"""Build and SEAL hold-out 5 (docs/raman_saab/FIDELITY_FIXES_PREREG.md, Addendum 31).

Conclusions: the hold-out 2 extractions of the HTJAH charts that hold-out 2 rejected
(`r2_htjah1a.json`, `r2_htjah2_merged.json`), used as extracted. Positions: two independent
transcriptions of the Rasi diagrams from page images (`r5_htjah_scan_positions_a/b.json`); a
chart is used only if both agree on all nine grahas and the Lagna. Where birth data is printed and
the cast puts all nine grahas and the Lagna in the printed signs, the cast is used (degrees);
otherwise the printed signs are. Dedupe against the goldens, hold-outs 1-3 and hold-out 4's
position extraction (never the sealed hold-out 4 fixture). This script never prints a verdict.

Usage:
    python -m tools.raman_saab.build_holdout5 --v0-out PATH [--out FIXTURE]
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict

from tools.raman_saab.build_holdout import _EARLIER, _GRAHAS, _birth, _sign_no

X = "docs/raman_saab/holdout_extractions/"
OUT = "tests/fixtures/raman_holdout5_sealed.jsonl"
CONCL = {"I": (X + "r2_htjah1a.json", "HTJAH-I"), "II": (X + "r2_htjah2_merged.json", "HTJAH-II")}
READERS = (X + "r5_htjah_scan_positions_a.json", X + "r5_htjah_scan_positions_b.json")
H4_POSITIONS = X + "r4_3hc_scan_positions_a.json"
_STAMP = "2026-10-24"
#: birth-line facts the hold-out 2 extraction left out or could not encode, as both readers
#: transcribed them from the page image (time zones: G.M.T. 0, E.S.T. -5, Indian War Time +6.5)
BIRTH_FIX = {
    ("I", 86): {"date": "1901-09-26", "time": "00:20", "time_basis": "LMT", "lat_deg": 10, "lat_min": 25,
                "lat_dir": "N", "lon_deg": 88, "lon_min": 15, "lon_dir": "E"},
    ("II", 70): {"tz": 0.0}, ("II", 76): {"tz": -5.0}, ("II", 149): {"tz": 6.5},
}


def _positions(rasi: dict | None) -> dict | None:
    if not rasi:
        return None
    pos = {}
    for sign, items in rasi.items():
        for g in items:
            g = {"Merc.": "Mercury", "Kethu": "Ketu"}.get(g, g)
            if g in pos:
                return None
            pos[g] = _sign_no(sign)
    return pos if all(g in pos for g in _GRAHAS + ("Lagna",)) else None


def _signature(pos: dict) -> tuple:
    return (pos["Lagna"],) + tuple(pos[g] for g in _GRAHAS)


def _cast_birth(key, c: dict) -> dict | None:
    fix = BIRTH_FIX.get(key, {})
    b = dict(c.get("birth") or {})
    b.update({k: v for k, v in fix.items() if k != "tz"})
    if "tz" in fix:
        b["time_basis"] = "IST"           # placeholder so _birth parses; tz replaced below
    birth, _ = _birth(b)
    if birth is not None and "tz" in fix:
        birth["tz"] = fix["tz"]
    return birth


def main(v0_out: str, out_path: str = OUT) -> None:
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    a, b = ({(c["volume"], c["chart_no"]): c for c in json.load(open(p, encoding="utf-8"))} for p in READERS)
    seen_dates, seen_signs = set(), set()
    for fx in _EARLIER:
        if fx == out_path:
            continue
        for line in open(fx, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                r = json.loads(line)
                if r.get("birth") and r["birth"].get("dt"):
                    seen_dates.add(r["birth"]["dt"][:10])
                if r.get("stated_positions") and r.get("lagna_sign"):
                    seen_signs.add((r["lagna_sign"],) + tuple(
                        int(tg._materialise_lon(r["stated_positions"][g]) // 30) + 1
                        for g in _GRAHAS if g in r["stated_positions"]))
    for c in json.load(open(H4_POSITIONS, encoding="utf-8")):
        p = _positions(c.get("rasi"))
        if p:
            seen_signs.add(_signature(p))
    report, records = defaultdict(list), []
    for vol, (path, book) in CONCL.items():
        for c in json.load(open(path, encoding="utf-8")):
            key = (vol, c.get("chart_no"))
            if key not in a:
                continue
            tag = f"{book}.chart_{key[1]}"
            pa, pb = _positions(a[key]["rasi"]), _positions(b.get(key, {}).get("rasi"))
            if pa is None or pb is None:
                report["diagram incomplete or missing"].append(tag); continue
            if pa != pb:
                report["readers disagree"].append(f"{tag} {[g for g in pa if pa[g] != pb.get(g)]}"); continue
            if not c.get("conclusions"):
                report["no conclusions"].append(tag); continue
            if _signature(pa) in seen_signs:
                report["printed signs equal an earlier chart"].append(tag); continue
            birth, stated, lagna = _cast_birth(key, c), {}, pa["Lagna"]
            if birth is not None and birth["dt"][:10] in seen_dates:
                report["birth date equals an earlier chart"].append(tag); continue
            if birth is not None:
                chart = tg.build_chart({"id": tag, "birth": birth, "stated_positions": {}})
                miss = [g for g in _GRAHAS if int(chart.planets[g].lon // 30) + 1 != pa[g]]
                if chart.asc_sign != pa["Lagna"]:
                    miss.append("Lagna")
                if miss:
                    report["cast disagrees with printed signs; printed signs used"].append(f"{tag} {miss}")
                    birth = None
                else:
                    report["cast agrees with all printed signs; cast used"].append(tag)
            else:
                report["no usable birth data; printed signs used"].append(tag)
            if birth is None:
                stated = {g: {"lon": round((pa[g] - 1) * 30 + 15.0, 4), "bhava": ((pa[g] - lagna) % 12) + 1,
                              "position_source": "holdout_extraction"} for g in _GRAHAS}
            verdicts = defaultdict(set)
            for k in c["conclusions"]:
                verdicts[(k["house"], k["signification"])].add(k["verdict"])
            by_house: dict[str, list] = defaultdict(list)
            used = set()
            for k in c["conclusions"]:
                hs = (k["house"], k["signification"])
                if hs in used:
                    continue
                used.add(hs)
                if len(verdicts[hs]) > 1:
                    report["contested conclusion dropped"].append(f"{tag} {hs}"); continue
                by_house[k["house"]].append(k)
            n = max((len(v) for v in by_house.values()), default=0)
            for i in range(n):
                ev = {h: {"signification": ks[i]["signification"], "verdict": ks[i]["verdict"],
                          "verdict_prose": ks[i]["quote"], "verdict_review": "HOLDOUT",
                          "review_note": f"Engine-blind extraction {_STAMP} ({book}:{ks[i]['line']}). {ks[i].get('why', '')}"}
                      for h, ks in by_house.items() if i < len(ks)}
                records.append({"id": tag + (f"#{i+1}" if i else ""), "book": book,
                                "name": c.get("name") or f"{book} Chart {key[1]}", "case_type": "holdout",
                                "birth": birth, "lagna_sign": lagna, "stated_positions": stated,
                                "expected_verdicts": ev, "expected_longevity": None, "track_eligibility": ["B"],
                                "confidence": 0.5,
                                "citations": [f"{book}:{c.get('first_line')}-{c.get('last_line')}",
                                              f"page image p.{a[key]['page']}"]})
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# SEALED HOLD-OUT 5 (Addendum 31, docs/raman_saab/FIDELITY_FIXES_PREREG.md). Scored ONCE,\n")
        f.write("# together with hold-out 4. Never tune against it. Built by tools/raman_saab/build_holdout5.py\n")
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    v0 = {}
    for r in records:
        chart = tg.build_chart(r)
        for h, e in r["expected_verdicts"].items():
            v0[f"{r['id']} {h}/{e['signification']}"] = tg._signification_verdict(chart, int(h[1:]), e["signification"])
    blob = json.dumps(v0, sort_keys=True).encode()
    open(v0_out, "wb").write(blob)
    rows = sum(len(r["expected_verdicts"]) for r in records)
    lab = defaultdict(int)
    for r in records:
        for e in r["expected_verdicts"].values():
            lab[e["verdict"]] += 1
    natives = len({r["id"].split("#")[0] for r in records})
    print(f"natives: {natives}  records: {len(records)}  scored rows: {rows}  labels: {dict(lab)}")
    for k, v in report.items():
        print(f"[{k}] {len(v)}: {v}")
    print("fixture sha256:", hashlib.sha256(open(out_path, "rb").read()).hexdigest())
    print("V0 verdict file sha256:", hashlib.sha256(blob).hexdigest())


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[args.index("--v0-out") + 1], args[args.index("--out") + 1] if "--out" in args else OUT)
