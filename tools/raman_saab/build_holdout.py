"""Build and SEAL the R6 hold-out (docs/raman_saab/FIDELITY_FIXES_PREREG.md, "R6").

Input: the engine-blind extractions (one JSON per source range, schema in
docs/raman_saab/HOLDOUT_BRIEF.md). Each chart is cast from its printed birth data and accepted
only if the cast agrees with Raman's printed dasa balance (same planet, years within 1) and with
his printed Lagna where he names one. Charts sharing a birth date with any golden chart are
dropped. Output: tests/fixtures/raman_holdout_sealed.jsonl plus a V0-verdict file whose SHA-256
is printed. This script never prints an engine verdict.

Usage:
    python -m tools.raman_saab.build_holdout EXTRACT.json [EXTRACT.json ...] --v0-out PATH
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict

import swisseph as swe

from app.raman_saab.chart.model import BirthData
from app.raman_saab.rectification.arithmetic import sunrise_jd

SIGNS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
         "sagittarius", "capricorn", "aquarius", "pisces"]
DASA = [("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7), ("Rahu", 18),
        ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)]
ALIASES = {"kethu": "Ketu", "ketu": "Ketu", "venus": "Venus", "sun": "Sun", "moon": "Moon",
           "mars": "Mars", "rahu": "Rahu", "jupiter": "Jupiter", "saturn": "Saturn",
           "mercury": "Mercury", "sukra": "Venus", "guru": "Jupiter", "sani": "Saturn"}
OUT = "tests/fixtures/raman_holdout_sealed.jsonl"
#: extraction file stem prefix -> (record id prefix / book tag, citation tag)
SOURCES = {"3hc": ("3HC", "3HCC"), "r2_nh": ("NH", "NH"), "r2_htjah1": ("HTJAH-I", "HTJAH-I"),
           "r2_htjah2": ("HTJAH-II", "HTJAH-II")}


def _source(stem: str) -> tuple[str, str]:
    for k, v in SOURCES.items():
        if stem.startswith(k):
            return v
    raise ValueError(f"unknown extraction source {stem!r}")


_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _sign_no(name) -> int | None:
    n = (name or "").strip().lower()
    return next((i + 1 for i, s in enumerate(SIGNS) if n.startswith(s[:4])), None)


def _stated(c: dict) -> tuple[dict, int] | None:
    """Stated positions (all nine grahas + Lagna sign) in the golden-fixture format."""
    sp = c.get("stated_positions") or {}
    lag = _sign_no(c.get("lagna_sign_printed") or c.get("lagna_sign_stated"))
    if lag is None or any(g not in sp for g in _GRAHAS):
        return None
    out = {}
    for g in _GRAHAS:
        e = sp[g] or {}
        sg = _sign_no(e.get("sign"))
        if sg is None:
            return None
        deg = e.get("deg")
        deg = float(deg) if isinstance(deg, (int, float)) and 0 <= float(deg) < 30 else 15.0
        out[g] = {"lon": round((sg - 1) * 30 + deg, 4), "bhava": ((sg - lag) % 12) + 1,
                  "position_source": "holdout_extraction"}
    return out, lag


def _deg(d, m, direction) -> float | None:
    if d is None:
        return None
    v = float(d) + (float(m) / 60.0 if m else 0.0)
    return -v if direction in ("S", "W", "s", "w") else v


def _birth(b: dict) -> tuple[dict, str] | tuple[None, str]:
    if not b or not b.get("date"):
        return None, "no date"
    lat = _deg(b.get("lat_deg"), b.get("lat_min"), b.get("lat_dir"))
    lon = _deg(b.get("lon_deg"), b.get("lon_min"), b.get("lon_dir"))
    if lat is None or lon is None:
        return None, "no coordinates"
    if b["date"].startswith("-"):
        return None, "BC date (use printed positions)"
    y, mo, d = (int(x) for x in b["date"].split("-"))
    if y < 1583:
        # Julian-calendar date: the ephemeris cast is Gregorian, so Raman's printed positions decide
        return None, "pre-Gregorian date (use printed positions)"
    basis = (b.get("time_basis") or "").lower().strip()
    if basis == "ghatikas_after_sunrise" and b.get("ghatikas"):
        g = re.match(r"\s*(\d+)(?:[-.](\d+))?", str(b["ghatikas"]))
        if not g:
            return None, "unreadable ghatikas"
        gh = int(g.group(1)) + (int(g.group(2)) / 60.0 if g.group(2) else 0.0)
        tz = lon / 15.0
        sr = sunrise_jd(BirthData("x", y, mo, d, 12, 0, tz, lat, lon), "raman")
        jd = sr + gh / 60.0
        yy, mm, dd, hf = swe.revjul(jd + tz / 24.0, swe.GREG_CAL)
        hh = int(hf); mi = int(round((hf - hh) * 60))
        if mi == 60:
            hh, mi = hh + 1, 0
        return {"dt": f"{yy:04d}-{mm:02d}-{dd:02d}T{hh:02d}:{mi:02d}:00", "tz": round(tz, 4),
                "lat": round(lat, 4), "lon": round(lon, 4)}, "ok"
    if not b.get("time"):
        return None, "no time"
    if basis == "lmt":
        tz = lon / 15.0
    elif basis == "ist":
        tz = 5.5
    elif basis in ("", "none", "null"):
        tz = lon / 15.0     # not printed: Raman's book default is LMT; the dasa-balance check decides
    else:
        return None, f"time basis {basis!r}"
    hh, mi = (int(x) for x in b["time"].split(":")[:2])
    return {"dt": f"{y:04d}-{mo:02d}-{d:02d}T{hh:02d}:{mi:02d}:00", "tz": round(tz, 4),
            "lat": round(lat, 4), "lon": round(lon, 4)}, "ok"


def _balance(moon_lon: float) -> tuple[str, float]:
    span = 360.0 / 27.0
    n = int(moon_lon // span)
    lord, yrs = DASA[n % 9]
    frac = (moon_lon % span) / span
    return lord, (1.0 - frac) * yrs


def _printed_balance(s: str | None) -> tuple[str, float] | None:
    if not s:
        return None
    m = re.match(r"\s*([A-Za-z]+)\D*?(\d+)\s*[-.,]\s*(\d+)(?:\s*[-.,]\s*(\d+))?", s)
    name = re.sub(r"'s$", "", m.group(1).lower()) if m else ""
    if not m or name not in ALIASES:
        return None
    y, mo = int(m.group(2)), int(m.group(3))
    return ALIASES[name], y + mo / 12.0


_PROSE = re.compile(r"balance\s+of\s+(?:the\s+)?([A-Za-z]+?)(?:'s)?\s+dasa\D*?([0-9Oo]+)\s*years?"
                    r"(?:\D{0,12}?([0-9Oo]+)\s*months?)?", re.I)


def _printed_balance_any(s: str | None) -> tuple[str, float] | None:
    """Short form 'Venus 2-1-15' or Raman's prose 'Balance of Venus Dasa at birth: 2 years 1 month'."""
    if s and (m := _PROSE.search(s)):
        name = m.group(1).lower()
        if name in ALIASES:
            num = lambda t: int(t.replace("O", "0").replace("o", "0")) if t else 0
            return ALIASES[name], num(m.group(2)) + num(m.group(3)) / 12.0
    return _printed_balance(s)


def main(paths: list[str], v0_out: str, out_path: str = OUT) -> None:
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    golden_dates = set()
    golden_signs = set()
    for fx in ("tests/fixtures/raman_goldens.jsonl", OUT):
        if fx == out_path:
            continue
        for line in open(fx, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                r = json.loads(line)
                if r.get("birth") and r["birth"].get("dt"):
                    golden_dates.add(r["birth"]["dt"][:10])
                if r.get("stated_positions") and r.get("lagna_sign"):
                    golden_signs.add((r["lagna_sign"],) + tuple(
                        int(tg._materialise_lon(r["stated_positions"][g]) // 30) + 1
                        for g in _GRAHAS if g in r["stated_positions"]))
    charts = []
    for p in paths:
        src = _source(p.rsplit("/", 1)[-1].replace(".json", ""))
        for c in json.load(open(p, encoding="utf-8")):
            c["_src"] = src
            charts.append(c)
    report = defaultdict(list)
    accepted: dict[str, dict] = {}       # birth dt -> merged native
    for c in charts:
        book, cite = c["_src"]
        tag = f"{book}.chart_{c.get('chart_no')}"
        if not c.get("conclusions"):
            report["no conclusions"].append(tag); continue
        birth, why = _birth(c.get("birth") or {})
        if birth is None:
            st = _stated(c)
            if st is None:
                report[why + " and no complete stated positions"].append(tag); continue
            sp, lag = st
            sig = (lag,) + tuple(int(sp[g]["lon"] // 30) + 1 for g in _GRAHAS)
            if sig in golden_signs:
                report["stated positions equal a golden chart"].append(tag); continue
            key = f"{book}:stated:{c.get('chart_no')}"
            nat = accepted.setdefault(key, {"ids": [], "birth": None, "stated": sp, "lagna": lag,
                                             "book": book, "lines": [], "concl": defaultdict(list),
                                             "name": c.get("name")})
            nat["ids"].append(c.get("chart_no"))
            nat["lines"].append(f"{cite}:{c.get('first_line')}-{c.get('last_line')}")
            for k in c["conclusions"]:
                k = dict(k); k["_cite"] = cite
                nat["concl"][(k["house"], k["signification"])].append(k)
            continue
        if birth["dt"][:10] in golden_dates:
            report["already a golden chart"].append(tag); continue
        rec = {"id": tag, "birth": birth, "stated_positions": {}}
        chart = tg.build_chart(rec)
        pb = _printed_balance_any(c.get("dasa_balance"))
        if pb is None:
            report["no readable dasa balance"].append(tag); continue
        lord, yrs = _balance(chart.planets["Moon"].lon)
        if lord != pb[0] or abs(yrs - pb[1]) > 1.0:
            report[f"dasa balance disagrees"].append(f"{tag} printed {pb[0]} {pb[1]:.1f} cast {lord} {yrs:.1f}")
            continue
        ls = (c.get("lagna_sign_stated") or "").lower()
        named = next((i + 1 for i, s in enumerate(SIGNS) if s in ls), None)
        if named is not None and named != chart.asc_sign:
            report["Lagna disagrees"].append(f"{tag} printed {SIGNS[named-1]} cast {SIGNS[chart.asc_sign-1]}")
            continue
        key = birth["dt"][:16]
        nat = accepted.setdefault(key, {"ids": [], "birth": birth, "stated": {}, "lagna": chart.asc_sign,
                                         "book": book, "lines": [], "concl": defaultdict(list),
                                         "name": c.get("name")})
        nat["ids"].append(c.get("chart_no"))
        nat["lines"].append(f"{cite}:{c.get('first_line')}-{c.get('last_line')}")
        for k in c["conclusions"]:
            k = dict(k); k["_cite"] = cite
            nat["concl"][(k["house"], k["signification"])].append(k)
    records = []
    contested = []
    for key, nat in sorted(accepted.items()):
        by_house: dict[str, list] = defaultdict(list)
        for (house, sig), ks in nat["concl"].items():
            verdicts = {k["verdict"] for k in ks}
            if len(verdicts) > 1:
                contested.append(f"charts {nat['ids']} {house}/{sig}: {sorted(verdicts)}"); continue
            by_house[house].append((sig, ks[0]))
        n = max((len(v) for v in by_house.values()), default=0)
        for i in range(n):
            ev = {}
            for house, items in by_house.items():
                if i < len(items):
                    sig, k = items[i]
                    ev[house] = {"signification": sig, "verdict": k["verdict"],
                                 "verdict_prose": k["quote"], "verdict_review": "HOLDOUT",
                                 "review_note": f"Engine-blind extraction 2026-10-24 ({k['_cite']}:{k['line']}). {k.get('why','')}"}
            if not ev:
                continue
            ids = "+".join(str(x) for x in sorted(nat["ids"], key=lambda z: (z is None, z)))
            records.append({"id": f"{nat['book']}.chart_{ids}" + (f"#{i+1}" if i else ""), "book": nat["book"],
                            "name": nat.get("name") or (f"Three Hundred Important Combinations, Chart {ids}"
                                                         if nat["book"] == "3HC" else f"{nat['book']} Chart {ids}"),
                            "case_type": "holdout", "birth": nat["birth"], "lagna_sign": nat["lagna"],
                            "stated_positions": nat["stated"], "expected_verdicts": ev,
                            "expected_longevity": None, "track_eligibility": ["B"],
                            "confidence": 0.5, "citations": nat["lines"]})
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# SEALED HOLD-OUT (R6, docs/raman_saab/FIDELITY_FIXES_PREREG.md). Scored ONCE, after R1-R5\n")
        f.write("# shipping decisions are final. Never tune against it. Built by tools/raman_saab/build_holdout.py\n")
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
    print(f"natives accepted: {len(accepted)}  records: {len(records)}  scored rows: {rows}  labels: {dict(lab)}")
    print("contested (dropped):", contested)
    for k, v in report.items():
        print(f"REJECTED [{k}] {len(v)}: {v}")
    print("V0 verdict file sha256:", hashlib.sha256(blob).hexdigest())


if __name__ == "__main__":
    a = sys.argv[1:]
    out = a[a.index("--v0-out") + 1]
    fx = a[a.index("--out") + 1] if "--out" in a else OUT
    main([x for x in a if x.endswith(".json") and x not in (out, fx)], out, fx)
