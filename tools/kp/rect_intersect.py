"""Constraint-intersection rectification: every method as a per-minute likelihood, combined, stress-tested.

For one native with a stated time and a set of dated events and life facts:

1. Candidate grid: every minute in a window.
2. Each piece of evidence e gives, at each minute t, a hit h_e(t) in {0,1} and a chance rate
   b_e: how often that evidence would fit a RANDOM minute (coverage of the matching periods over
   the life span for dated events; share of the day's minutes for yes/no facts). Under "t is the
   true time" the hit probability is P1 (rules imperfect); under "t is not" it is b_e. The
   log-likelihood ratio is
       hit:  log(P1 / b_e)        miss: log((1 - P1) / (1 - b_e))
   so a rare window that is hit counts for a lot, a common one for little, and a miss costs more
   when the window was wide.
3. Methods are combined by adding LLRs (independence assumed, which is false: the KP dasa
   sequence is shared by every event, so the posterior is OVERCONFIDENT; it is reported with
   that warning). A uniform prior over the window gives a posterior and 50 % / 90 % credible sets.
4. Stress tests: leave-one-event-out, leave-one-TYPE-out, and the all-subsets peak distribution
   over event classes, so the user sees which single answers the result hangs on.
5. Hard-constraint intersection: the minutes where every "sharp" boolean (b_e < 0.3) is hit.

Usage:
    python -m tools.kp.rect_intersect --spec mainpuri.json --out intersect.md
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import swisseph as swe

from app.kp.chart import Birth, cast
from app.kp.events import EVENTS, event_windows
from app.kp.judgment import MATTERS, _core, generic_matter
from app.kp.rectify import stability_band

P1 = 0.9
YEAR = 365.2425


def jd_interval(y: int, m: Optional[int], d: Optional[int]) -> tuple[float, float]:
    if d:
        a = swe.julday(y, m, d, 0.0)
        return a, a + 1.0
    if m:
        return swe.julday(y, m, 1, 0.0), swe.julday(y + (m == 12), m % 12 + 1, 1, 0.0)
    return swe.julday(y, 1, 1, 0.0), swe.julday(y + 1, 1, 1, 0.0)


def llr(hit: bool, b: float) -> float:
    b = min(max(b, 0.01), 0.99)
    return math.log(P1 / b) if hit else math.log((1 - P1) / (1 - b))


@dataclass
class Evidence:
    key: str
    kind: str              # dated | fact | classical
    group: str             # for leave-one-type-out
    hits: dict[int, bool]  # offset -> hit
    base: dict[int, float] # offset -> chance rate at that minute
    note: str = ""

    def llr(self, off: int) -> float:
        return llr(self.hits[off], self.base[off])


def dated_evidence(b0: Birth, offsets: list[int], events: list[dict], life: tuple[float, float]) -> list[Evidence]:
    out = []
    charts = {o: cast(b0.shifted(o)) for o in offsets}
    for ev in events:
        a, b = jd_interval(ev["year"], ev.get("month"), ev.get("day"))
        hits, base = {}, {}
        for o, c in charts.items():
            ws = [(w.period.start_jd, w.period.end_jd) for w in event_windows(c, ev["type"], from_age=life[0], to_age=life[1])]
            cov = lambda x, y: sum(max(0.0, min(y, e) - max(x, s)) for s, e in ws) / (y - x)
            j0, j1 = c.jd_ut + life[0] * YEAR, c.jd_ut + life[1] * YEAR
            hits[o] = cov(a, b) > 0.5
            base[o] = cov(j0, j1)
        out.append(Evidence(ev["id"], "dated", ev.get("group", ev["type"]), hits, base, ev.get("note", "")))
    return out


def fact_evidence(b0: Birth, offsets: list[int], facts: list[dict], day_step: int = 3) -> list[Evidence]:
    """facts: {id, matter, ok: [verdicts that count as a hit]}. Chance rate = share of the day's minutes."""
    matters = {m: (MATTERS[m] if m in MATTERS else generic_matter(int(m[5:]))) for m in {f["matter"] for f in facts}}
    day = {}
    for k in range(0, 1440, day_step):
        c = cast(Birth(b0.year, b0.month, b0.day, k // 60, k % 60, b0.tz, b0.lat, b0.lon))
        day[k] = {m: _core(c, mt)[0] for m, mt in matters.items()}
    charts = {o: cast(b0.shifted(o)) for o in offsets}
    out = []
    for f in facts:
        ok = set(f["ok"])
        b = sum(v[f["matter"]] in ok for v in day.values()) / len(day)
        hits = {o: _core(c, matters[f["matter"]])[0] in ok for o, c in charts.items()}
        out.append(Evidence(f["id"], "fact", "facts", hits, {o: b for o in offsets}, f.get("note", "")))
    return out


def classical_evidence(b0: Birth, offsets: list[int], day_step: int = 3) -> list[Evidence]:
    """Kunda trine Moon; navamsa-lagna vargottama. Chance rate = share of the day."""
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData

    def feats(h: int, m: int) -> dict[str, bool]:
        c = cast_chart(BirthData(name="x", year=b0.year, month=b0.month, day=b0.day, hour=h, minute=m,
                                 tz_offset=b0.tz, latitude=b0.lat, longitude=b0.lon), ayanamsa="raman")
        asc, moon = c.asc_lon, c.planets["Moon"].lon
        kunda = (asc * 81) % 360
        nav = int(((asc % 30) * 9) // 30)
        nav_sign = (int(asc // 30) * 9 + nav) % 12
        return {"kunda_trine_moon": (int(moon // 30) - int(kunda // 30)) % 12 in (0, 4, 8),
                "vargottama": nav_sign == int(asc // 30)}
    day = [feats(k // 60, k % 60) for k in range(0, 1440, day_step)]
    out = []
    for key in ("kunda_trine_moon", "vargottama"):
        b = sum(d[key] for d in day) / len(day)
        hits = {}
        for o in offsets:
            s = b0.shifted(o)
            hits[o] = feats(s.hour, s.minute)[key]
        out.append(Evidence(key, "classical", "classical", hits, {o: b for o in offsets},
                            "Kunda (Sepharial): lagna x 81 in trine to the Moon's sign" if key.startswith("k") else
                            "Navamsa lagna = rasi lagna (vargottama); a strength mark, not a rectification rule"))
    return out


def posterior(evs: list[Evidence], offsets: list[int]) -> dict[int, float]:
    tot = {o: sum(e.llr(o) for e in evs) for o in offsets}
    mx = max(tot.values())
    w = {o: math.exp(v - mx) for o, v in tot.items()}
    z = sum(w.values())
    return {o: v / z for o, v in w.items()}


def credible(post: dict[int, float], mass: float) -> list[tuple[int, int]]:
    order = sorted(post, key=post.get, reverse=True)
    acc, keep = 0.0, []
    for o in order:
        keep.append(o); acc += post[o]
        if acc >= mass:
            break
    return runs(sorted(keep))


def runs(xs: list[int]) -> list[tuple[int, int]]:
    out: list[list[int]] = []
    for x in xs:
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return [tuple(r) for r in out]


def peak(evs: list[Evidence], offsets: list[int]) -> tuple[int, float]:
    tot = {o: sum(e.llr(o) for e in evs) for o in offsets}
    o = max(tot, key=tot.get)
    return o, tot[o]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    S = json.load(open(a.spec))
    b0 = Birth(*S["date"], *S["time"], tz=S["tz"], lat=S["lat"], lon=S["lon"])
    offsets = list(range(S["window"][0], S["window"][1] + 1))
    life = tuple(S.get("life_ages", (5, 37.2)))
    evs = dated_evidence(b0, offsets, S["events"], life) + fact_evidence(b0, offsets, S["facts"]) + classical_evidence(b0, offsets)
    fmt = lambda o: (lambda s: f"{s.hour:02d}:{s.minute:02d}")(b0.shifted(o))
    fr = lambda rs: ", ".join(f"{fmt(x)}-{fmt(y)}" for x, y in rs)

    L = [f"# Constraint-intersection rectification: {S['label']}", "",
         f"Stated {fmt(0)}; grid {fmt(offsets[0])} to {fmt(offsets[-1])} by the minute ({len(offsets)} candidates). "
         f"P1 = {P1}. Evidence: {sum(e.kind=='dated' for e in evs)} dated events, {sum(e.kind=='fact' for e in evs)} facts, "
         f"{sum(e.kind=='classical' for e in evs)} classical checks.", ""]

    # per-evidence table at reference minutes
    refs = S.get("reference_offsets", [0])
    L += ["## Each piece of evidence: chance rate and hit at reference times", "",
          "| evidence | kind | chance rate | " + " | ".join(fmt(o) for o in refs) + " | minutes hit (share of grid) |",
          "|---|---|---|" + "---|" * len(refs) + "---|"]
    for e in evs:
        hit_share = sum(e.hits.values()) / len(offsets)
        bavg = sum(e.base.values()) / len(offsets)
        L.append(f"| {e.key} | {e.kind} | {bavg:.2f} | " + " | ".join("yes" if e.hits[o] else "no" for o in refs) + f" | {hit_share:.2f} |")

    # combined
    post = posterior(evs, offsets)
    po, pv = peak(evs, offsets)
    L += ["", "## Combined (all evidence, LLRs added)", "",
          f"Peak {fmt(po)} (total LLR {pv:+.2f}). 50 % credible set: {fr(credible(post, .5))}. 90 %: {fr(credible(post, .9))}.",
          f"Posterior at stated {fmt(0)}: {post[0]:.3f} (uniform would be {1/len(offsets):.3f}).", "",
          "Caveat: the LLRs are added as if independent. Every dated event shares one dasa sequence and the cusp sub-lords move together, so the real evidence is weaker than this looks.", ""]
    L += ["Posterior by minute (×100): " + " ".join(f"{fmt(o)}:{post[o]*100:.0f}" for o in offsets if post[o] > 0.005)]

    # by method family
    L += ["", "## Each family alone", ""]
    for kind in ("dated", "fact", "classical"):
        sub = [e for e in evs if e.kind == kind]
        if sub:
            p = posterior(sub, offsets); o, v = peak(sub, offsets)
            L.append(f"- **{kind}**: peak {fmt(o)}; 50 % set {fr(credible(p, .5))}; 90 % set {fr(credible(p, .9))}.")
    groups = sorted({e.group for e in evs})
    L += ["", "By event group (dated events only):", ""]
    for g in groups:
        sub = [e for e in evs if e.group == g and e.kind == "dated"]
        if sub:
            p = posterior(sub, offsets); o, _ = peak(sub, offsets)
            L.append(f"- {g} ({len(sub)}): peak {fmt(o)}; 50 % set {fr(credible(p, .5))}.")

    # hard intersection of sharp constraints
    sharp = [e for e in evs if sum(e.base.values()) / len(offsets) < 0.3]
    inter = [o for o in offsets if all(e.hits[o] for e in sharp)]
    L += ["", "## Hard intersection of the sharp constraints (chance rate < 0.30)", "",
          f"Sharp constraints: {', '.join(e.key for e in sharp) or 'none'}.",
          f"Minutes satisfying all of them: {fr(runs(inter)) if inter else 'none'}."]
    for k in range(len(sharp), 0, -1):
        ok = [o for o in offsets if sum(e.hits[o] for e in sharp) >= k]
        if ok:
            L.append(f"Satisfying at least {k} of {len(sharp)}: {fr(runs(ok))}.")
            if k == len(sharp) and len(ok) < len(offsets):
                continue
            break

    # leave-one-out
    L += ["", "## Stress test 1: leave one piece of evidence out", "", "| removed | new peak | 50 % set | peak moved by |", "|---|---|---|---|"]
    for e in evs:
        sub = [x for x in evs if x is not e]
        p = posterior(sub, offsets); o, _ = peak(sub, offsets)
        L.append(f"| {e.key} | {fmt(o)} | {fr(credible(p, .5))} | {o - po:+d} min |")

    # leave-one-group-out
    L += ["", "## Stress test 2: leave one whole group out", "", "| removed group | new peak | 50 % set | 90 % set |", "|---|---|---|---|"]
    for g in groups + ["facts", "classical"]:
        sub = [x for x in evs if x.group != g]
        if len(sub) < len(evs):
            p = posterior(sub, offsets); o, _ = peak(sub, offsets)
            L.append(f"| {g} | {fmt(o)} | {fr(credible(p, .5))} | {fr(credible(p, .9))} |")

    # all subsets of groups
    allg = groups + ["classical"]
    L += ["", "## Stress test 3: every combination of evidence groups", "", "Where the peak lands for each subset of groups (at least two groups):", ""]
    hist: dict[int, int] = defaultdict(int)
    n = 0
    for r in range(2, len(allg) + 1):
        for combo in itertools.combinations(allg, r):
            sub = [x for x in evs if x.group in combo]
            o, _ = peak(sub, offsets); hist[o] += 1; n += 1
    tops = sorted(hist.items(), key=lambda kv: -kv[1])[:8]
    L.append(f"{n} subsets. Peak minutes: " + ", ".join(f"{fmt(o)} ({c})" for o, c in tops) + ".")
    bins: dict[str, int] = defaultdict(int)
    for o, c in hist.items():
        bins[f"{fmt(o - (o - offsets[0]) % 10)}+"] += c
    L.append("By 10-minute bin: " + ", ".join(f"{k} {v}" for k, v in sorted(bins.items())) + ".")

    # stability band at peak and at stated
    for o in sorted({0, po}):
        sb = stability_band(b0.shifted(o), 3)
        L += ["", f"## Cusp sub-lords at {fmt(o)} ±3 min", "", "Stable: " + ", ".join(f"{c}:{sb.stable(c)}" for c in sb.stable_cusps) + "; changing: " + ", ".join(str(c) for c in range(1, 13) if not sb.stable(c))]

    L += ["", "## Reading rules", "",
          "- A peak that survives every leave-one-out and most group subsets is robust to the evidence; it is still not validated against known births.",
          "- A peak that moves when one answer is removed rests on that answer. Say so.",
          "- The hard intersection is the honest range: minutes no sharp constraint rules out.",
          "- Facts are judgment calls (what counts as 'troubled health'); they are listed so they can be flipped."]
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
