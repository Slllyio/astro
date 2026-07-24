"""Real-outcome GENERALIZATION test — the Prime-Directive second axis, at scale.

The golden ratchet measures TEXTBOOK FIDELITY (does the engine reproduce Raman's printed verdicts).
It does NOT measure REAL-OUTCOME GENERALIZATION (does the engine predict actual lives). This harness
does the latter, using the AstroDatabank AA-rated charts + dated life events under
``data/astro_databank/`` (local, gitignored; the tool skips gracefully if absent).

Two tests:
  1. LONGEVITY — the engine's Ayurdaya predicted lifespan vs the ACTUAL death age (own, natural
     deaths only). Numeric, external, hard to overfit.
  2. TIMING — does the Vimshottari ``active_houses`` at a dated event contain the event's house
     ABOVE the base rate (the fraction of houses active by chance)?

Both are honest, held-out real-outcome measures: the birth data and outcomes are external, never
tuned against. Usage: py -3.12 -m tools.raman_saab.real_outcome_test
"""
from __future__ import annotations

import csv
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import ayurdaya
from app.raman_saab.primitives import vimshottari as vim

_DIR = Path("data/astro_databank")
_PEOPLE = _DIR / "raw_lunarastro_aa.csv"
_EVENTS = _DIR / "events_all.csv"

_EVENT_HOUSE = [
    (r"marriage|wedding|betroth", 7), (r"divorce|separation|widow", 7),
    (r"disease|illness|medical|health|surgery|diagnos", 6),
    (r"career|new job|profession|employ|retire", 10),
    (r"fame|prize|award|published|exhibit|released|honou?r", 10),
    (r"education|graduat|degree|school|college|univers", 4),
    (r"child|son born|daughter|pregnan", 5),
    (r"property|real estate|house", 4), (r"finance|wealth|lottery|inherit", 2),
    (r"legal|court|prison|jail|arrest", 12),
]


def _people() -> dict[str, tuple[BirthData, int]]:
    out: dict[str, tuple[BirthData, int]] = {}
    for r in csv.DictReader(_PEOPLE.open(encoding="utf-8")):
        t = r.get("time_of_birth") or ""
        if not t or t.startswith("12:00:00") or r["name"].startswith("Animal"):
            continue
        try:
            y, mo, da = (int(x) for x in r["date_of_birth"].split("-"))
            out[r["name"]] = (BirthData(r["name"], y, mo, da, int(t[:2]), int(t[3:5]),
                              float(r["tz_offset"]), float(r["latitude"]), float(r["longitude"])), y)
        except Exception:  # noqa: BLE001
            continue
    return out


def _class(y: float) -> str:
    return "alpa" if y < 32 else "madhya" if y < 72 else "purna"


def longevity_test(ppl: dict) -> None:
    deaths: dict[str, int] = {}
    for r in csv.DictReader(_EVENTS.open(encoding="utf-8")):
        root, sub = r.get("event_root", ""), r.get("event_subtype", "")
        low = f"{root} {sub}".lower()
        if not root.startswith("Death") or "death of" in low:
            continue
        if any(v in low for v in ("accident", "suicide", "homicide", "murder", "execution", "killed")):
            continue
        if r["name"] in ppl and r.get("event_year", "").isdigit():
            age = int(r["event_year"]) - ppl[r["name"]][1]
            if 15 < age < 105:
                deaths[r["name"]] = age
    pred, actual, cmatch = [], [], 0
    for nm, age in deaths.items():
        try:
            res = ayurdaya.longevity(cast_chart(ppl[nm][0], ayanamsa="raman"))
        except Exception:  # noqa: BLE001
            continue
        pred.append(res.total_years); actual.append(age)
        cmatch += _class(age) == res.longevity_class
    n = len(pred)
    print(f"\n[LONGEVITY] AA own-natural-death charts scored: {n}")
    if n >= 3:
        mp, ma = statistics.mean(pred), statistics.mean(actual)
        cov = sum((p-mp)*(a-ma) for p, a in zip(pred, actual)) / n
        sp, sa = statistics.pstdev(pred), statistics.pstdev(actual)
        print(f"  Pearson r (predicted span vs actual age): {cov/(sp*sa) if sp and sa else 0:+.3f}")
        print(f"  MAE={statistics.mean(abs(p-a) for p,a in zip(pred,actual)):.1f}yr  "
              f"mean predicted={mp:.1f} actual={ma:.1f} (over-predicts = capacity>realized)")
        print(f"  longevity-CLASS match: {cmatch}/{n}={cmatch/n:.1%}  (random 3-class = 33%)")


def _house(root: str, sub: str) -> int | None:
    s = f"{root} {sub}".lower()
    return next((h for pat, h in _EVENT_HOUSE if re.search(pat, s)), None)


def timing_test(ppl: dict, cap: int = 3000) -> None:
    events = defaultdict(list)
    for r in csv.DictReader(_EVENTS.open(encoding="utf-8")):
        if r["name"] not in ppl:
            continue
        h = _house(r.get("event_root", ""), r.get("event_subtype", ""))
        if h and r.get("event_year", "").isdigit():
            events[r["name"]].append((h, int(r["event_year"])))
    hit = base = total = 0
    for nm, evs in events.items():
        if total >= cap:
            break
        try:
            ch = cast_chart(ppl[nm][0], ayanamsa="raman")
        except Exception:  # noqa: BLE001
            continue
        for h, yr in evs:
            if total >= cap:
                break
            act = vim.active_houses(ch, vim.date_to_jd(yr, 7, 1))
            if not act:
                continue
            active = {a.house for a in act}
            total += 1; hit += h in active; base += len(active) / 12.0
    print(f"\n[TIMING] dated events scored: {total}")
    if total:
        print(f"  active-house hit-rate={hit/total:.3f}  base-rate={base/total:.3f}  "
              f"lift={hit/total - base/total:+.3f}  (active_houses is broad-recall -> near-saturated)")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    if not _PEOPLE.is_file() or not _EVENTS.is_file():
        print(f"[real-outcome] astrobank data not found under {_DIR} (local/gitignored) — skipping.")
        return 0
    ppl = _people()
    print(f"[real-outcome] AA charts with clean birth times: {len(ppl)}")
    longevity_test(ppl)
    timing_test(ppl)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
