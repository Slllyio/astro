"""Addendum 33: score V0, R5, C1, C4 (and passing combinations) ONCE on hold-outs 4+5, with the
no-fit baselines B3 and always-favourable, plus pool figures. R5 is a patch: run this script once
with the patch applied (`--r5`) and once without; each run writes its own JSON.

Usage:
    python -m tools.raman_saab.score_batch33 OUT.json VARIANT_SET [VARIANT_SET ...] [--r5]
    VARIANT_SET is a '+'-joined list, e.g. V0, C1, C4, C1+C4 (V0 = no switch).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict

H4 = "tests/fixtures/raman_holdout4_sealed.jsonl"
H5 = "tests/fixtures/raman_holdout5_sealed.jsonl"
SEALED_V0 = {"H4": ("docs/raman_saab/holdout4_v0_verdicts_sealed.json",
                    "223b8ae34d3f392eb452be2a5e7a4a3a66951dabb2d385bd0f4416842cc4d6d9"),
             "H5": ("docs/raman_saab/holdout5_v0_verdicts_sealed.json",
                    "5a1c55acf5cd1abfade02ab00c00ca9524701b757e753f7db62aabc9b6791a74")}
CLASSES = ("favourable", "mixed", "afflicted")


def _load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]


def _b3(nb, nm):
    return "favourable" if nb >= nm else "afflicted"


def _metrics(rows, key, dist):
    ex = sum(r[key] == r["gold"] for r in rows)
    w1 = sum(dist(r[key], r["gold"]) <= 1 for r in rows)
    re_ = sum(dist(r[key], r["gold"]) >= 2 for r in rows)
    rec = [sum(r[key] == c for r in rows if r["gold"] == c) / n
           for c in CLASSES if (n := sum(r["gold"] == c for r in rows))]
    books = defaultdict(int)
    for r in rows:
        books[r["book"]] += dist(r[key], r["gold"]) >= 2
    return {"n": len(rows), "exact": ex, "within1": w1, "real": re_,
            "macro_recall": round(sum(rec) / len(rec), 3), "real_by_book": dict(books)}


def main(out: str, sets: list[str], r5: bool) -> None:
    sys.path.insert(0, ".")
    from app.raman_saab.judges import house_template as ht
    from tests.raman_saab import test_goldens as tg
    from tools.raman_saab import fidelity_variants as fv
    res = {"r5_patch_applied": r5, "sealed_v0_ok": {}, "holdout": {}, "pool": {}, "rows": {}}
    for k, (p, sha) in SEALED_V0.items():
        res["sealed_v0_ok"][k] = hashlib.sha256(open(p, "rb").read()).hexdigest() == sha
    recs = [("H4", r) for r in _load(H4)] + [("H5", r) for r in _load(H5)]
    for vs in sets:
        variants = set() if vs == "V0" else set(vs.split("+"))
        label = ("R5+" if r5 else "") + vs
        fv.apply(variants)
        rows = []
        try:
            for hs, r in recs:
                ch = tg.build_chart(r)
                for h, e in r["expected_verdicts"].items():
                    pf = ht.judge_house(ch, int(h[1:]))
                    sv = next((s for s in pf.significations if s.signification == e["signification"]), None)
                    nb = len(sv.ledger.fired_benefic) if sv else 0
                    nm = len(sv.ledger.fired_malefic) if sv else 0
                    rows.append({"key": f"{r['id']} {h}/{e['signification']}", "set": hs, "book": r["book"],
                                 "gold": e["verdict"], "got": tg._signification_verdict(ch, int(h[1:]), e["signification"]),
                                 "B3": _b3(nb, nm), "AF": "favourable"})
        finally:
            fv.apply(set())
        pool = fv.run(variants)
        pd = [{"gold": g, "got": v, "book": b} for b, g, v in pool.values()]
        res["pool"][label] = _metrics(pd, "got", tg._ordinal_distance)
        res["rows"][label] = {r["key"]: r["got"] for r in rows}
        res["holdout"][label] = {}
        for part, sel in (("H4", "H4"), ("H5", "H5"), ("H4+H5", None)):
            rr = [r for r in rows if sel is None or r["set"] == sel]
            res["holdout"][label][part] = {k: _metrics(rr, k, tg._ordinal_distance) for k in ("got", "B3", "AF")}
    json.dump(res, open(out, "w"), indent=1)
    print("written", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    r5 = "--r5" in a
    a = [x for x in a if x != "--r5"]
    main(a[0], a[1:], r5)
