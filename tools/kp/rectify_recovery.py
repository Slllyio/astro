"""Pre-registered recovery test for birth-time rectification (docs/kp/RECTIFICATION_PREREG_2026-10-31.md).

For each person with a known exact birth time: shift the time by a hidden seeded offset
(uniform whole minutes in [-30, +30]), search the shifted time ±45 min, and record where
the TRUE minute ranks among the 91 candidates (percentile rank: 0 best, 1 worst, ties at
mid-rank; chance = 0.5). Four tracks, scored on the same people and windows:

  kp           app.kp.rectify (timing + promise, Reader 3 rules)
  raman        app.raman_saab.rectification event channels (period lords + house activation),
               Raman ayanamsa
  moon_arith   the HPA ch.12 arithmetic channel (Moon nakshatra / rising-sign rules), Raman ayanamsa
  kp_placebo   the kp track with every event date moved by a seeded 2-6 years (sham)

Modes:
  synthetic    T0 machinery check. Events are generated from the KP rules at a hidden true
               time, so the kp track must recover it. Tests the search, not astrology.
  jsonl        T1 on a person file (one JSON object per line, schema in the prereg).
  adb          T1 straight from the Astro-Databank derived parquet on the PC
               (quality tier A/B only, Rodden AA/A, day-dated events; never tier C).

Usage:
    python -m tools.kp.rectify_recovery synthetic --n 200 --out docs/kp/RECTIFICATION_T0_RESULTS.md
    python -m tools.kp.rectify_recovery adb --derived E:/astro/data/astro_databank/derived --out docs/kp/RECTIFICATION_T1_RESULTS.md --ledger E:/astro/data/validation/kp_rect_ledger.json
    python -m tools.kp.rectify_recovery jsonl --people people.jsonl --out results.md
"""

from __future__ import annotations

import argparse
import json
import logging
import multiprocessing as mp
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional

logger = logging.getLogger(__name__)

PREREG: Final[str] = "docs/kp/RECTIFICATION_PREREG_2026-10-31.md"
SEED: Final[int] = 20261031
MAX_OFFSET: Final[int] = 30
WINDOW: Final[int] = 45
SESOI: Final[float] = 0.05
T0_PASS: Final[float] = 0.30
N_BOOT: Final[int] = 2000
T1_MAX_PEOPLE: Final[int] = 1000
MIN_RECT_EVENTS: Final[int] = 3
TRACKS: Final[tuple[str, ...]] = ("kp", "raman", "moon_arith", "kp_placebo")

#: KP event type -> Raman taxonomy key (same life matter, Raman's own house/karakas).
RAMAN_TYPE: Final[dict[str, str]] = {
    "marriage": "marriage", "service_start": "career_start", "service_end": "career_change",
    "gain": "income_gain", "illness": "illness_accident", "childbirth": "childbirth",
}

#: ADB event text -> KP event type. First match wins; None excludes. Frozen by the prereg.
ADB_MAP: Final[tuple[tuple[str, Optional[str]], ...]] = (
    (r"^death|death of", None),
    (r"divorce|end significant relationship|parents divorced", None),
    (r"\bmarriage\b", "marriage"),
    (r"birth of (a )?(child|son|daughter)|child born|became a (parent|father|mother)", "childbirth"),
    (r"new job|new career", "service_start"),
    (r"retired|fired/laid off/quit", "service_end"),
    (r"acute illness|chronic illness|medical diagnosis|medical procedure", "illness"),
    (r"gain significant money", "gain"),
)
_MONTHS = r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b"

#: Synthetic birthplaces (lat, lon), all at tz +5.5.
_PLACES: Final[tuple[tuple[float, float], ...]] = (
    (28.61, 77.21), (19.08, 72.88), (12.97, 77.59), (13.08, 80.27), (22.57, 88.36),
    (26.45, 80.33), (23.26, 77.41), (17.39, 78.49), (25.32, 82.97), (11.02, 76.96),
)


def map_adb(root: str, subtype: Optional[str]) -> Optional[str]:
    text = re.sub(_MONTHS, "", f"{root} {subtype or ''}".lower())
    text = re.sub(r"\s+", " ", text).strip()
    for pat, t in ADB_MAP:
        if re.search(pat, text):
            return t
    return None


@dataclass
class Person:
    pid: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    tz: float
    lat: float
    lon: float
    events: list[dict]          # {"type", "year", "month", "day", "id"}


# --- per-track minute scores -------------------------------------------------

def _kp_scores(birth, events, window: int) -> list[int]:
    from app.kp.rectify import rectify
    r = rectify(birth, events, window_minutes=window)
    return [m.total for m in r.minutes]


def _raman_scores(birth, kp_events, window: int) -> tuple[list[float], list[float]]:
    """Per-minute (event channels, arithmetic channel) from the Raman rectifier, Raman ayanamsa."""
    from app.raman_saab.rectification import candidates as C
    from app.raman_saab.rectification import scoring as S
    from app.raman_saab.rectification.events import LifeEvent
    evs = tuple(LifeEvent(RAMAN_TYPE[e.event_type], e.year, e.month, e.day) for e in kp_events)
    centre = birth.hour + birth.minute / 60
    lo, hi = centre - (window + 1) / 60, centre + (window + 1) / 60
    cands = C.generate_candidates(year=birth.year, month=birth.month, day=birth.day,
                                  latitude=birth.lat, longitude=birth.lon, tz_offset=birth.tz,
                                  window_local_hours=(lo, hi), ayanamsas=("raman",),
                                  event_jds=tuple(e.jd_point() for e in evs))
    cache = C.ChartCache()

    def sec(s: str) -> int:
        h, m, x = s.split(":")
        return int(h) * 3600 + int(m) * 60 + int(float(x))
    rows = []
    for c in cands:
        ch = S.score_candidate(c, cache, evs).channels
        a, b = c.interval_local
        rows.append((sec(a), sec(b), ch.event_lords + ch.event_houses, ch.arithmetic))
    ev_s, ar_s = [], []
    for k in range(-window, window + 1):
        t = int(round(centre * 3600)) + k * 60
        hit = next((r for r in rows if r[0] <= t < r[1]), rows[-1] if t >= rows[-1][1] else rows[0])
        ev_s.append(hit[2])
        ar_s.append(hit[3])
    return ev_s, ar_s


def pct_rank(scores: list, i: int) -> float:
    s = scores[i]
    better = sum(x > s for x in scores)
    ties = sum(x == s for x in scores) - 1
    return (better + 0.5 * ties) / (len(scores) - 1)


def _placebo(events, rng: random.Random):
    from app.kp.rectify import KPEvent
    out = []
    for e in events:
        shift = rng.choice((-1, 1)) * rng.randint(2, 6)
        d = e.day if not (e.month == 2 and e.day == 29) else 28
        out.append(KPEvent(e.event_type, e.year + shift, e.month, d, event_id=e.key + "#placebo"))
    return out


def run_person(task: tuple[Person, int, str, bool]) -> Optional[dict]:
    """Score one person on every track. Returns None if the person cannot be cast."""
    p, offset, mode, use_split = task
    try:
        from app.kp.chart import Birth
        from app.kp.rectify import KPEvent, rectify, split_events
        true = Birth(p.year, p.month, p.day, p.hour, p.minute, tz=p.tz, lat=p.lat, lon=p.lon)
        evs = [KPEvent(e["type"], e["year"], e["month"], e["day"], event_id=str(e.get("id", ""))) for e in p.events]
        rect, sealed = split_events(p.pid, evs) if use_split else (tuple(evs), ())
        if len(rect) < (MIN_RECT_EVENTS if use_split else 1):
            return None
        stated = true.shifted(offset)
        i_true = WINDOW - offset                      # index of the true minute in the window
        rng = random.Random(f"{SEED}|placebo|{p.pid}")
        out = {"pid": p.pid, "offset": offset, "n_rect": len(rect), "n_sealed": len(sealed),
               "rect_keys": [e.key for e in rect], "sealed_keys": [e.key for e in sealed]}
        r = rectify(stated, rect, window_minutes=WINDOW)
        kp = [m.total for m in r.minutes]
        out["kp"] = pct_rank(kp, i_true)
        out["kp_hit"] = kp[i_true] == max(kp)
        out["kp_top_share"] = r.top_share
        kb = r.kp_birth()
        centre = (min(r.top_offsets) + max(r.top_offsets)) / 2
        out["kp_abs_err"] = abs(centre - (-offset))
        out["stated_abs_err"] = abs(offset)
        out["kp_placebo"] = pct_rank(_kp_scores(stated, _placebo(rect, rng), WINDOW), i_true)
        if mode != "synthetic":
            ev, ar = _raman_scores(stated, rect, WINDOW)
            out["raman"] = pct_rank(ev, i_true)
            out["moon_arith"] = pct_rank(ar, i_true)
        out["kp_birth_uncertainty"] = kb.uncertainty_minutes
        return out
    except Exception as exc:  # noqa: BLE001 - per-person failure is counted, not hidden
        logger.warning("person %s failed: %s", p.pid, exc)
        return {"pid": p.pid, "error": str(exc)}


# --- populations -------------------------------------------------------------

def synthetic_people(n: int, seed: int = SEED) -> list[Person]:
    """T0: births with events planted in KP-matching antaras at the true time."""
    from app.kp.chart import Birth, cast
    from app.kp.dasa import periods_between
    from app.kp.rectify import KP_EVENT_TYPES
    from app.kp.significators import houses_signified, planet_significations
    import swisseph as swe
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        jd0 = swe.julday(1950, 1, 1, 0.0) + rng.random() * (swe.julday(1995, 12, 31, 0.0) - swe.julday(1950, 1, 1, 0.0))
        y, m, d, _ = swe.revjul(jd0)
        lat, lon = rng.choice(_PLACES)
        hh, mm = rng.randint(2, 21), rng.randint(0, 59)
        b = Birth(y, m, d, hh, mm, tz=5.5, lat=lat, lon=lon)
        chart = cast(b)
        sigs = planet_significations(chart)
        hs = {pl: houses_signified(chart, pl, sigs) for pl in sigs}
        events = []
        for t in rng.sample(sorted(KP_EVENT_TYPES), 4):
            sp = KP_EVENT_TYPES[t]
            wins = [w for w in periods_between(chart, chart.jd_ut + 18 * 365.2425, chart.jd_ut + 60 * 365.2425, depth=3)
                    if all(hs[l] & sp.houses for l in w.lords) and w.end_jd - w.start_jd > 3]
            if not wins:
                continue
            w = rng.choice(wins)
            ej = w.start_jd + 1 + rng.random() * (w.end_jd - w.start_jd - 2)
            ey, em, ed, _ = swe.revjul(ej)
            events.append({"type": t, "year": ey, "month": em, "day": ed, "id": f"{t}-{len(events)}"})
        if len(events) >= 3:
            out.append(Person(f"syn{len(out):04d}", y, m, d, hh, mm, 5.5, lat, lon, events))
    return out


def jsonl_people(path: Path) -> list[Person]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out.append(Person(r["pid"], *r["date"], *r["time"], r["tz"], r["lat"], r["lon"], r["events"]))
    return out


def adb_people(derived: Path) -> tuple[list[Person], dict]:
    """T1 population from the PC's Astro-Databank derived tables. Tier A/B only (never C)."""
    import pandas as pd
    R = derived / "raman"
    master = pd.read_parquet(R / "person_master.parquet")
    master = master[master.quality_tier.isin(["A", "B"]) & master.rodden_rating.isin(["AA", "A"])]
    master = master[master.birth_date.str.match(r"^\d{4}-\d\d-\d\d$") & master.birth_time.str.match(r"^\d\d:\d\d")]
    ev = pd.read_parquet(R / "person_events.parquet")
    ev = ev[ev.person_id.isin(set(master.person_id)) & (ev.date_precision == "day")]
    ev = ev.assign(kp_type=[map_adb(r, s) for r, s in zip(ev.event_root, ev.event_subtype)])
    categories = (ev.assign(text=ev.event_root.astype(str) + " | " + ev.event_subtype.astype(str))
                  .groupby(["text", "kp_type"], dropna=False).size().sort_values(ascending=False))
    ev = ev[ev.kp_type.notna()]
    by = {pid: g for pid, g in ev.groupby("person_id")}
    people = []
    for r in master.itertuples():
        g = by.get(r.person_id)
        if g is None:
            continue
        hh, mm = int(r.birth_time[:2]), int(r.birth_time[3:5])
        if not (75 <= hh * 60 + mm <= 1440 - 76):
            continue                                    # the ±(30+45) min window must stay inside the day
        y, mo, d = (int(x) for x in r.birth_date.split("-"))
        evs = []
        seen = set()
        for e in g.itertuples():
            key = (e.kp_type, int(e.event_year), int(e.event_month), int(e.event_day))
            if key in seen or int(e.event_year) - y < 5:
                continue
            seen.add(key)
            evs.append({"type": e.kp_type, "year": key[1], "month": key[2], "day": key[3],
                        "id": f"{e.kp_type}:{key[1]}-{key[2]:02d}-{key[3]:02d}"})
        people.append(Person(str(r.person_id), y, mo, d, hh, mm, float(r.tz_offset),
                             float(r.latitude), float(r.longitude), evs))
    cat = {f"{k[0]} -> {k[1]}": int(v) for k, v in categories.head(80).items()}
    return people, cat


# --- statistics --------------------------------------------------------------

def boot_ci(xs: list[float], seed: int = SEED) -> tuple[float, float, float]:
    rng = random.Random(seed)
    n = len(xs)
    means = sorted(sum(xs[rng.randrange(n)] for _ in range(n)) / n for _ in range(N_BOOT))
    return sum(xs) / n, means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]


def classify(mean: float, lo: float, hi: float) -> str:
    if hi < 0.5 and mean <= 0.5 - SESOI:
        return "SIGNAL"
    if lo > 0.5:
        return "WORSE_THAN_CHANCE"
    if lo >= 0.5 - SESOI and hi <= 0.5 + SESOI:
        return "BOUNDED_NULL"
    return "UNDERPOWERED"


def summarise(rows: list[dict], mode: str) -> dict:
    ok = [r for r in rows if "error" not in r]
    res = {"mode": mode, "n_people": len(ok), "n_failed": len(rows) - len(ok), "tracks": {}}
    for t in TRACKS:
        xs = [r[t] for r in ok if t in r]
        if xs:
            m, lo, hi = boot_ci(xs)
            res["tracks"][t] = {"mean_pct_rank": round(m, 4), "ci95": [round(lo, 4), round(hi, 4)],
                                "label": classify(m, lo, hi), "n": len(xs)}
    if ok:
        res["kp_hit_rate"] = round(sum(r["kp_hit"] for r in ok) / len(ok), 4)
        res["kp_chance_hit_rate"] = round(sum(r["kp_top_share"] for r in ok) / len(ok), 4)
        res["kp_mean_abs_err_min"] = round(sum(r["kp_abs_err"] for r in ok) / len(ok), 2)
        res["stated_mean_abs_err_min"] = round(sum(r["stated_abs_err"] for r in ok) / len(ok), 2)
        res["kp_closer_than_stated"] = round(sum(r["kp_abs_err"] < r["stated_abs_err"] for r in ok) / len(ok), 4)
        res["mean_rect_events"] = round(sum(r["n_rect"] for r in ok) / len(ok), 2)
    if mode == "synthetic":
        res["t0_pass"] = bool(res["tracks"].get("kp", {}).get("mean_pct_rank", 1) <= T0_PASS)
    res["placebo_gate_ok"] = res["tracks"].get("kp_placebo", {}).get("label") != "SIGNAL"
    return res


def to_markdown(res: dict, extra: dict | None = None) -> str:
    L = [f"# Rectification recovery: {res['mode']}", "", f"Pre-registration: `{PREREG}`.", "",
         f"People scored: {res['n_people']} (failed casts: {res['n_failed']}). "
         f"Mean events used to rectify: {res.get('mean_rect_events')}.", "",
         "Percentile rank of the true minute among the 91 candidates (0 best, 1 worst, chance 0.5):", "",
         "| track | n | mean | 95% CI | label |", "|---|---|---|---|---|"]
    for t, v in res["tracks"].items():
        L.append(f"| {t} | {v['n']} | {v['mean_pct_rank']} | {v['ci95'][0]} to {v['ci95'][1]} | **{v['label']}** |")
    L += ["", f"KP: true minute inside the top-scoring set {res.get('kp_hit_rate')} of the time; "
              f"chance for sets that size {res.get('kp_chance_hit_rate')}.",
          f"KP: mean distance of the rectified centre from the truth {res.get('kp_mean_abs_err_min')} min, "
          f"against {res.get('stated_mean_abs_err_min')} min for the shifted stated time; rectified closer in "
          f"{res.get('kp_closer_than_stated')} of people.",
          f"Placebo gate ok: {res['placebo_gate_ok']}."]
    if "t0_pass" in res:
        L.append(f"T0 machinery check (kp mean ≤ {T0_PASS}): **{'PASS' if res['t0_pass'] else 'FAIL'}**.")
    if extra:
        L += ["", "## Event categories as mapped (top 80)", ""] + [f"- {k}: {v}" for k, v in extra.items()]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("synthetic", "jsonl", "adb"))
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--people", type=Path)
    ap.add_argument("--derived", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rows", type=Path, help="write per-person rows (JSONL)")
    ap.add_argument("--ledger", type=Path, help="write the rectification/sealed event ledger (JSON)")
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    a = ap.parse_args(argv)
    extra = None
    if a.mode == "synthetic":
        people = synthetic_people(a.n)
    elif a.mode == "jsonl":
        people = jsonl_people(a.people)
    else:
        people, extra = adb_people(a.derived)
    rng = random.Random(SEED)
    if a.mode != "synthetic" and len(people) > T1_MAX_PEOPLE:
        from app.kp.chart import Birth  # noqa: F401  (import check before the long run)
        from app.kp.rectify import KPEvent, split_events
        eligible = [p for p in people if len(split_events(p.pid, [KPEvent(e["type"], e["year"], e["month"], e["day"], event_id=e["id"]) for e in p.events])[0]) >= MIN_RECT_EVENTS]
        people = rng.sample(sorted(eligible, key=lambda p: p.pid), T1_MAX_PEOPLE) if len(eligible) > T1_MAX_PEOPLE else eligible
    offsets = {p.pid: random.Random(f"{SEED}|offset|{p.pid}").randint(-MAX_OFFSET, MAX_OFFSET) for p in people}
    tasks = [(p, offsets[p.pid], a.mode, a.mode != "synthetic") for p in people]
    with mp.Pool(a.workers) as pool:
        rows = [r for r in pool.imap(run_person, tasks, chunksize=4) if r is not None]
    res = summarise(rows, a.mode)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(to_markdown(res, extra), encoding="utf-8")
    a.out.with_suffix(".json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    if a.rows:
        a.rows.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    if a.ledger:
        led = {r["pid"]: {"rectification": r["rect_keys"], "sealed": r["sealed_keys"]} for r in rows if "rect_keys" in r}
        a.ledger.write_text(json.dumps(led, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
