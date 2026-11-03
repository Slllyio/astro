"""Real-outcome test harness for the KP engine, run under a pre-registration.

Pre-registration: ``docs/kp/KP_REAL_OUTCOME_PREREG_2026-11-02.md``. Read it before using this.
The harness has two steps and they must run in this order:

1. ``lock`` reads ONLY birth data, computes each person's timing windows for the registered
   matters, and writes them with a SHA-256 digest. No outcome is read at this step.
2. ``score`` reads the locked predictions (refusing them if the digest no longer matches) and
   the dated events, then compares hits with an age-matched shuffled-chart baseline and returns
   SIGNAL, BOUNDED_NULL or UNDERPOWERED per matter, as fixed in the pre-registration.

Files live under ``data/private/kp_outcomes/`` (gitignored). Nothing in this module ships data.
The older outcome file ``data/private/real_outcomes.json`` is refused outright.

Births file (JSON list):
    [{"id": "p01", "year": 1989, "month": 10, "day": 10, "hour": 15, "minute": 15,
      "tz": 5.5, "lat": 26.45, "lon": 80.33, "time_source": "certificate",
      "uncertainty_minutes": 2}]
Events file (JSON list), supplied only after ``lock``:
    [{"id": "p01", "matter": "marriage", "date": "2014-02-11"}]

Usage:
    python -m tools.kp.outcome_harness lock --births data/private/kp_outcomes/births.json --out data/private/kp_outcomes/locked.json
    python -m tools.kp.outcome_harness score --locked data/private/kp_outcomes/locked.json --events data/private/kp_outcomes/events.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import swisseph as swe

from app.kp.chart import Birth, cast
from app.kp.judgment import timing_windows
from app.kp.selection import selected_windows

logger = logging.getLogger(__name__)

DAYS_PER_YEAR: Final[float] = 365.2425
# Registered in the pre-registration; changing any of these after `lock` voids the test.
MATTERS: Final[tuple[str, ...]] = ("marriage", "children", "service")
PRIMARY: Final[tuple[str, str]] = ("marriage", "r25")
AGE_FROM: Final[float] = 16.0
AGE_TO: Final[float] = 50.0
MIN_EVENTS: Final[int] = 40
ALPHA: Final[float] = 0.05
SHUFFLES: Final[int] = 2000
SEED: Final[int] = 20261102
PRIMARY_SOURCES: Final[frozenset[str]] = frozenset({"certificate", "hospital_record", "horoscope_at_birth"})
MAX_UNCERTAINTY_MIN: Final[float] = 5.0
FORBIDDEN: Final[str] = "real_outcomes.json"


def _guard(path: str | Path) -> Path:
    p = Path(path)
    if p.name == FORBIDDEN:
        raise SystemExit(f"refusing {p}: that file is not part of this harness")
    return p


def _jd(date: str) -> float:
    y, m, d = (int(x) for x in date.split("-"))
    return swe.julday(y, m, d, 12.0, swe.GREG_CAL)


def _iso(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{y:04d}-{m:02d}-{d:02d}"


def _birth(rec: Mapping) -> Birth:
    return Birth(int(rec["year"]), int(rec["month"]), int(rec["day"]), int(rec["hour"]),
                 int(rec["minute"]), tz=float(rec["tz"]), lat=float(rec["lat"]), lon=float(rec["lon"]),
                 uncertainty_minutes=float(rec.get("uncertainty_minutes", 0.0)), label=str(rec["id"]))


def primary_eligible(rec: Mapping) -> bool:
    """Pre-registered: recorded time from a document, at most five minutes uncertain."""
    return (rec.get("time_source") in PRIMARY_SOURCES
            and float(rec.get("uncertainty_minutes", 99)) <= MAX_UNCERTAINTY_MIN)


def _digest(payload: Mapping) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def predict(rec: Mapping) -> dict:
    """Windows per matter and rule (R17 = all signifying lords, R25 = fruitful significators)."""
    chart = cast(_birth(rec))
    a, b = chart.jd_ut + AGE_FROM * DAYS_PER_YEAR, chart.jd_ut + AGE_TO * DAYS_PER_YEAR
    out = {"id": rec["id"], "birth_jd": chart.jd_ut, "primary": primary_eligible(rec), "windows": {}}
    for m in MATTERS:
        out["windows"][m] = {
            "r17": [[w.period.start_jd, w.period.end_jd] for w in timing_windows(chart, m, a, b)],
            "r25": [[w.period.start_jd, w.period.end_jd] for w in selected_windows(chart, m, a, b)],
        }
    return out


def lock(births: Sequence[Mapping]) -> dict:
    ids = [r["id"] for r in births]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate person ids")
    people = [predict(r) for r in births]
    body = {"registered": {"matters": MATTERS, "primary": PRIMARY, "age_from": AGE_FROM,
                           "age_to": AGE_TO, "min_events": MIN_EVENTS, "alpha": ALPHA,
                           "shuffles": SHUFFLES, "seed": SEED},
            "engine_commit": _commit(), "people": people}
    return {"digest": _digest(body), **body}


def verify(locked: Mapping) -> None:
    body = {k: v for k, v in locked.items() if k != "digest"}
    if _digest(body) != locked.get("digest"):
        raise SystemExit("locked predictions were changed after locking; the test is void")


@dataclass(frozen=True, slots=True)
class Result:
    matter: str
    rule: str
    events: int
    hits: int
    shuffled_mean: float
    p_value: float
    lift: float
    lift_shuffled_95: float
    verdict: str


def _inside(jd: float, windows: Iterable[Sequence[float]]) -> bool:
    return any(s <= jd < e for s, e in windows)


def _score_one(people: Mapping[str, Mapping], events: Sequence[tuple[str, float]], matter: str,
               rule: str, rng: random.Random) -> Result:
    """Hits on the person's own windows vs the same ages laid on a shuffled person's windows."""
    ages = [(pid, jd - people[pid]["birth_jd"]) for pid, jd in events]
    ids = sorted(people)

    def hits(assign: Mapping[str, str]) -> int:
        return sum(_inside(people[assign[pid]]["birth_jd"] + age, people[assign[pid]]["windows"][matter][rule])
                   for pid, age in ages)

    observed = hits({i: i for i in ids})
    null = []
    for _ in range(SHUFFLES):
        perm = ids[:]
        rng.shuffle(perm)
        null.append(hits(dict(zip(ids, perm, strict=True))))
    mean = sum(null) / len(null)
    p = (1 + sum(n >= observed for n in null)) / (1 + len(null))
    q95 = sorted(null)[int(0.95 * len(null)) - 1]
    lift = observed / mean if mean else float("nan")
    lift95 = q95 / mean if mean else float("nan")
    if len(events) < MIN_EVENTS:
        verdict = "UNDERPOWERED"
    elif p < ALPHA and observed > mean:
        verdict = "SIGNAL"
    else:
        verdict = "BOUNDED_NULL"
    return Result(matter, rule, len(events), observed, round(mean, 3), round(p, 4), round(lift, 3),
                  round(lift95, 3), verdict)


def score(locked: Mapping, events: Sequence[Mapping], *, primary_only: bool = True) -> list[Result]:
    verify(locked)
    people = {p["id"]: p for p in locked["people"] if p["primary"] or not primary_only}
    rng = random.Random(locked["registered"]["seed"])
    out = []
    for m in MATTERS:
        ev = []
        for e in events:
            if e["matter"] != m or e["id"] not in people:
                continue
            jd = _jd(e["date"])
            age = (jd - people[e["id"]]["birth_jd"]) / DAYS_PER_YEAR
            if AGE_FROM <= age < AGE_TO:
                ev.append((e["id"], jd))
        for rule in ("r25", "r17"):
            out.append(_score_one(people, ev, m, rule, rng))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lk = sub.add_parser("lock")
    lk.add_argument("--births", required=True)
    lk.add_argument("--out", required=True)
    sc = sub.add_parser("score")
    sc.add_argument("--locked", required=True)
    sc.add_argument("--events", required=True)
    sc.add_argument("--all-times", action="store_true", help="secondary: include unverified birth times")
    a = ap.parse_args()
    if a.cmd == "lock":
        births = json.loads(_guard(a.births).read_text(encoding="utf-8"))
        locked = lock(births)
        _guard(a.out).write_text(json.dumps(locked, indent=1), encoding="utf-8")
        print(f"locked {len(births)} people, digest {locked['digest']}")
        return
    locked = json.loads(_guard(a.locked).read_text(encoding="utf-8"))
    events = json.loads(_guard(a.events).read_text(encoding="utf-8"))
    for r in score(locked, events, primary_only=not a.all_times):
        tag = "PRIMARY " if (r.matter, r.rule) == PRIMARY else ""
        print(f"{tag}{r.matter}/{r.rule}: {r.hits} of {r.events} events in windows; shuffled mean "
              f"{r.shuffled_mean}; lift {r.lift} (shuffled 95th pct {r.lift_shuffled_95}); "
              f"p={r.p_value} -> {r.verdict}")


if __name__ == "__main__":
    main()
