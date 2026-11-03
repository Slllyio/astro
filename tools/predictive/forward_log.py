"""Forward (prospective) prediction log: KP ruling planets / horary, plus dasa-transit claims.

Pre-registration: docs/predictive/PREDICTIVE_PREREG_2026-11-02.md, addenda 1 (item 6) and 2.
Every entry is locked BEFORE its window opens: it carries the SHA-256 of its own content chained to
the previous entry's hash, so no entry can be edited or removed later without breaking the chain.
Commit or share the printed head hash after each `ask` so the lock is independently dated.

    python -m tools.predictive.forward_log ask --log L --text "Will I get the job?" --area career \
        --question promotion --number 117 --when "2026-11-03 10:42" --tz 5.5 --lat 26.45 --lon 80.33 \
        --prior 0.6 --quarter 2027Q1 --window 2026-11-03:2027-11-02
    python -m tools.predictive.forward_log resolve --log L --id 3 --outcome yes --date 2027-02-10
    python -m tools.predictive.forward_log verify --log L
    python -m tools.predictive.forward_log score --log L

`--question` is a key of app.kp.horary.questions.QUESTIONS (Reader 6 question rules) or, with
--matter, a KP matter (marriage, children, health, wealth, service, house<N>) judged by horary.
By default only the moment of the question is used: no birth data is needed or stored.

Optional natal KP (ruling R26), only with the asker's consent: add
    --birth "1990-07-15 12:00" --birth-tz 5.5 --birth-lat 12.97 --birth-lon 77.59 \
        --birth-matter marriage --consent-birth
and the entry also seals, from the natal chart judged at the question moment:
`app.kp.selection.select(chart, matter, judged=<question moment>)`, the R26 windows
(`selected_windows`) inside the question window, and Sun day-fixing passes (`day_fix`, R27). The
birth data is then stored in the hashed entry, because the lock must show what was judged.
KP's natal prediction is "yes" if any R26 window falls in the question window; its quarter is the
quarter of the first day-fixing pass inside a window, else of the first window's start.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

AREAS = ("career", "marriage", "children", "health", "wealth", "education", "travel", "parents", "other")


def _hash(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def read(log: Path) -> list[dict]:
    return [json.loads(x) for x in log.read_text().splitlines() if x.strip()] if log.exists() else []


def _write(log: Path, rec: dict) -> dict:
    entries = read(log)
    rec["prev"] = entries[-1]["hash"] if entries else "genesis"
    rec["hash"] = _hash(rec)
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def judge(a) -> dict:
    from app.kp.chart import Birth
    from app.kp.horary.judge import judge_horary
    from app.kp.horary.questions import answer
    t = datetime.strptime(a.when, "%Y-%m-%d %H:%M")
    b = Birth(t.year, t.month, t.day, t.hour, t.minute, a.tz, a.lat, a.lon)
    if a.question:
        ans = answer(a.number, b, a.question)
        out = {"rule": "question", **ans.to_dict()}
        from app.kp.chart import cast
        from app.kp.ruling import ruling_planets
        rp = ruling_planets(cast(b))
        out["ruling_planets_at_question"] = list(rp.planets) + list(rp.node_agents)
        return out
    hv = judge_horary(a.number, b, a.matter, body=a.timing_body)
    return {"rule": "horary_matter", **hv.to_dict()}


def _jd(d: str) -> float:
    import swisseph as swe
    x = date.fromisoformat(d)
    return swe.julday(x.year, x.month, x.day, 0.0)


def _iso(jd: float) -> str:
    import swisseph as swe
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{y:04d}-{m:02d}-{d:02d}"


def natal(a, w0: str, w1: str) -> dict:
    """R26 selection, windows and day-fixing for the asker's chart, judged at the question moment."""
    from app.kp.chart import Birth, cast
    from app.kp.selection import day_fix, select, selected_windows
    t = datetime.strptime(a.when, "%Y-%m-%d %H:%M")
    q = Birth(t.year, t.month, t.day, t.hour, t.minute, a.tz, a.lat, a.lon)
    bt = datetime.strptime(a.birth, "%Y-%m-%d %H:%M")
    chart = cast(Birth(bt.year, bt.month, bt.day, bt.hour, bt.minute, a.birth_tz, a.birth_lat, a.birth_lon))
    j0, j1 = _jd(w0), _jd(w1)
    sel = select(chart, a.birth_matter, judged=q)
    wins = [(w.period.start_jd, w.period.end_jd, w.period.label())
            for w in selected_windows(chart, a.birth_matter, j0, j1, judged=q)]
    passes = [p for p in day_fix(chart, a.birth_matter, j0, j1)
              if any(s <= p.start_jd < e for s, e, _ in wins)] if wins else []
    first = passes[0].start_jd if passes else (max(wins[0][0], j0) if wins else None)
    return {"birth_local": a.birth, "birth_tz": a.birth_tz, "birth_lat": a.birth_lat, "birth_lon": a.birth_lon,
            "matter": a.birth_matter, "selection": sel.to_dict(),
            "windows": [[_iso(max(s, j0)), _iso(min(e, j1)), lab] for s, e, lab in wins],
            "day_fix": [[_iso(p.start_jd), _iso(p.end_jd), p.label()] for p in passes],
            "window_coverage": round(sum(min(e, j1) - max(s, j0) for s, e, _ in wins) / (j1 - j0), 4),
            "verdict": "YES" if wins else "NO",
            "quarter": _quarter(_iso(first)) if first is not None else None}


def cmd_ask(a) -> None:
    if a.area not in AREAS:
        raise SystemExit(f"--area must be one of {AREAS}")
    w0, w1 = a.window.split(":")
    if date.fromisoformat(w0) < date.fromisoformat(a.when[:10]):
        raise SystemExit("the window must open on or after the question moment")
    rec = {"type": "ask", "id": len([e for e in read(a.log) if e["type"] == "ask"]) + 1,
           "logged_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
           "text": a.text, "area": a.area, "when_local": a.when, "tz": a.tz, "lat": a.lat, "lon": a.lon,
           "number": a.number, "asker_prior_yes": a.prior, "asker_quarter": a.quarter,
           "window": [w0, w1], "judgment": judge(a)}
    if a.birth:
        if not a.consent_birth:
            raise SystemExit("natal KP stores the birth data in the log: pass --consent-birth only with the asker's consent")
        if not a.birth_matter or a.birth_tz is None or a.birth_lat is None or a.birth_lon is None:
            raise SystemExit("--birth needs --birth-tz, --birth-lat, --birth-lon and --birth-matter")
        rec["natal"] = natal(a, w0, w1)
    rec = _write(a.log, rec)
    j = rec["judgment"]
    extra = ""
    if "natal" in rec:
        n = rec["natal"]
        extra = f"; natal KP says {n['verdict']}" + (f" ({n['quarter']})" if n["quarter"] else "")
    print(f"locked #{rec['id']}: KP says {j['verdict']}{extra}; head {rec['hash']}")


def cmd_resolve(a) -> None:
    asks = {e["id"]: e for e in read(a.log) if e["type"] == "ask"}
    if a.id not in asks:
        raise SystemExit(f"no question #{a.id}")
    w1 = date.fromisoformat(asks[a.id]["window"][1])
    if a.outcome == "no" and date.today() <= w1:
        raise SystemExit("a 'no' can only be recorded after the window closes")
    rec = _write(a.log, {"type": "resolve", "id": a.id, "outcome": a.outcome, "event_date": a.date,
                         "evidence": a.evidence,
                         "resolved_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds") + "Z"})
    print(f"resolved #{a.id}: {a.outcome}; head {rec['hash']}")


def cmd_verify(a) -> bool:
    prev = "genesis"
    for i, e in enumerate(read(a.log)):
        if e["prev"] != prev or _hash(e) != e["hash"]:
            print(f"BROKEN at line {i + 1}")
            return False
        prev = e["hash"]
    print(f"chain intact; head {prev}")
    return True


def _quarter(d: str) -> str:
    x = date.fromisoformat(d)
    return f"{x.year}Q{(x.month - 1) // 3 + 1}"


def score(entries: list[dict]) -> dict:
    asks = {e["id"]: e for e in entries if e["type"] == "ask"}
    res = {e["id"]: e for e in entries if e["type"] == "resolve"}
    rows = []
    for i, q in asks.items():
        if i not in res:
            continue
        yes = res[i]["outcome"] == "yes"
        v = q["judgment"]["verdict"].upper()
        kp = True if v in ("YES", "PROMISED") else False if v in ("NO", "DENIED") else None
        prior = q["asker_prior_yes"]
        rows.append({"id": i, "area": q["area"], "yes": yes, "kp": kp, "prior": prior,
                     "kp_right": None if kp is None else kp == yes,
                     "asker_right": (prior >= 0.5) == yes,
                     "asker_brier": (prior - yes) ** 2,
                     "quarter_hit_asker": bool(yes and res[i].get("event_date")
                                               and _quarter(res[i]["event_date"]) == q["asker_quarter"])})
        n = q.get("natal")
        if n:
            ev = res[i].get("event_date")
            rows[-1].update({
                "natal_kp": n["verdict"] == "YES",
                "natal_right": (n["verdict"] == "YES") == yes,
                "window_hit": bool(yes and ev and any(s <= ev < e for s, e, _ in n["windows"])),
                "quarter_hit_kp": bool(yes and ev and n["quarter"] and _quarter(ev) == n["quarter"]),
            })
    decided = [r for r in rows if r["kp"] is not None]
    out = {"resolved": len(rows), "kp_decided": len(decided),
           "kp_accuracy": sum(r["kp_right"] for r in decided) / len(decided) if decided else None,
           "asker_accuracy_same_rows": (sum(r["asker_right"] for r in decided) / len(decided)) if decided else None,
           "kp_right_asker_wrong": sum(r["kp_right"] and not r["asker_right"] for r in decided),
           "kp_wrong_asker_right": sum((not r["kp_right"]) and r["asker_right"] for r in decided),
           "bar": "KP accuracy >= 65% on >= 85 decided questions, and above the asker's own accuracy"}
    nat = [r for r in rows if "natal_kp" in r]
    happened = [r for r in nat if r["yes"]]
    out["natal"] = {
        "with_birth_data": len(nat),
        "natal_accuracy": sum(r["natal_right"] for r in nat) / len(nat) if nat else None,
        "asker_accuracy_same_rows": sum(r["asker_right"] for r in nat) / len(nat) if nat else None,
        "events_that_happened": len(happened),
        "event_inside_kp_window": sum(r["window_hit"] for r in happened),
        "quarter_hit_kp": sum(r["quarter_hit_kp"] for r in happened),
        "quarter_hit_asker": sum(r["quarter_hit_asker"] for r in happened),
        "mean_window_coverage": (sum(q["natal"]["window_coverage"] for q in asks.values() if q.get("natal"))
                                 / sum(1 for q in asks.values() if q.get("natal"))) if nat else None,
        "note": "descriptive; the window hit rate must be read against the share of the question window the KP windows cover",
    }
    if len(decided) >= 85:
        from scipy.stats import binomtest
        b, c = out["kp_right_asker_wrong"], out["kp_wrong_asker_right"]
        out["p_vs_50"] = binomtest(sum(r["kp_right"] for r in decided), len(decided), 0.5, alternative="greater").pvalue
        out["p_vs_asker_mcnemar"] = binomtest(b, b + c, 0.5, alternative="greater").pvalue if b + c else None
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("ask")
    s.add_argument("--log", type=Path, required=True)
    s.add_argument("--text", required=True)
    s.add_argument("--area", required=True)
    s.add_argument("--question")
    s.add_argument("--matter")
    s.add_argument("--timing-body", default="Sun")
    s.add_argument("--number", type=int, required=True, help="KP horary number 1-249 given by the asker")
    s.add_argument("--when", required=True, help="local time of the question, YYYY-MM-DD HH:MM")
    s.add_argument("--tz", type=float, required=True)
    s.add_argument("--lat", type=float, required=True)
    s.add_argument("--lon", type=float, required=True)
    s.add_argument("--prior", type=float, required=True, help="asker's own probability of yes, 0-1")
    s.add_argument("--quarter", required=True, help="asker's own best-guess quarter, e.g. 2027Q1")
    s.add_argument("--window", required=True, help="YYYY-MM-DD:YYYY-MM-DD")
    s.add_argument("--birth", help="optional asker's birth, local YYYY-MM-DD HH:MM (stored; needs --consent-birth)")
    s.add_argument("--birth-tz", type=float)
    s.add_argument("--birth-lat", type=float)
    s.add_argument("--birth-lon", type=float)
    s.add_argument("--birth-matter", help="KP matter for the natal reading, e.g. marriage, service, children")
    s.add_argument("--consent-birth", action="store_true", help="the asker agreed to their birth data being stored")
    r = sub.add_parser("resolve")
    r.add_argument("--log", type=Path, required=True)
    r.add_argument("--id", type=int, required=True)
    r.add_argument("--outcome", choices=("yes", "no"), required=True)
    r.add_argument("--date")
    r.add_argument("--evidence", default="")
    for name in ("verify", "score"):
        x = sub.add_parser(name)
        x.add_argument("--log", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "ask":
        if bool(a.question) == bool(a.matter):
            raise SystemExit("give exactly one of --question or --matter")
        cmd_ask(a)
    elif a.cmd == "resolve":
        cmd_resolve(a)
    elif a.cmd == "verify":
        return 0 if cmd_verify(a) else 1
    else:
        print(json.dumps(score(read(a.log)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
