"""Astro-Databank run of the KP real-outcome test (pre-registration addendum A).

Read ``docs/kp/KP_REAL_OUTCOME_PREREG_ADDENDUM_ADB_2026-11-02.md`` first. Steps, in this order:

1. ``gate``: birth data only. Tiers A and B of the Astro-Databank part, kept when the cast tropical
   Ascendant agrees with the one Astro-Databank publishes. Tier C (the C1/C2 holdouts) is dropped
   before anything else is read.
2. ``lock-timing``: people with a day-precise marriage or new-job event (presence only), their
   timing windows locked by ``tools.kp.outcome_harness.lock``.
3. ``events``: only now are event dates read (earliest per person and matter); then score with
   ``python -m tools.kp.outcome_harness score``.
4. ``lock-traits``: Reader 2 rules (R29) for every gated person, locked with a digest.
5. ``score-traits``: only now are the category tags read; Fisher tests per the addendum.

Usage:
    python -m tools.kp.adb_test gate --derived E:/astro/data/astro_databank/derived --out data/private/kp_outcomes/adb_gated.json
    python -m tools.kp.adb_test lock-timing --derived E:/astro/data/astro_databank/derived --gated data/private/kp_outcomes/adb_gated.json --out data/private/kp_outcomes/adb_locked.json
    python -m tools.kp.adb_test events --derived E:/astro/data/astro_databank/derived --locked data/private/kp_outcomes/adb_locked.json --out data/private/kp_outcomes/adb_events.json
    python -m tools.kp.outcome_harness score --locked data/private/kp_outcomes/adb_locked.json --events data/private/kp_outcomes/adb_events.json
    python -m tools.kp.adb_test lock-traits --gated data/private/kp_outcomes/adb_gated.json --out data/private/kp_outcomes/adb_traits_locked.json
    python -m tools.kp.adb_test score-traits --derived E:/astro/data/astro_databank/derived --locked data/private/kp_outcomes/adb_traits_locked.json --out docs/kp/kp_adb_traits_2026-11-02.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

import swisseph as swe

from app.kp.chart import Birth, cast
from app.kp.fundamentals import fundamentals
from tools.kp import outcome_harness as harness

logger = logging.getLogger(__name__)

TIERS: Final[frozenset[str]] = frozenset({"A", "B"})
ASC_TOLERANCE_DEG: Final[float] = 1.5
_SIGNS: Final[tuple[str, ...]] = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                                  "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_ASC_RE: Final[re.Pattern[str]] = re.compile(r"Asc (\d+) (" + "|".join(_SIGNS) + ")")
TIMING_EVENTS: Final[dict[str, tuple[str, str]]] = {
    "marriage": ("Relationship", "Marriage"),
    "service": ("Work", "New Job"),
}
ALPHA_TRAITS: Final[float] = 0.0125
MIN_CASES: Final[int] = 40
SPEECH_RULES: Final[tuple[str, ...]] = ("speech.mercury6", "speech.mercury_moon", "speech.saturn_lagna")


def _master(derived: Path):
    import pandas as pd
    m = pd.read_parquet(Path(derived) / "raman" / "person_master.parquet")
    return m[(m.population == "celebrity_databank") & m.quality_tier.isin(TIERS)]


def published_asc(categories: str) -> float | None:
    g = _ASC_RE.search(categories or "")
    return None if g is None else _SIGNS.index(g.group(2)) * 30 + int(g.group(1)) + 0.5


def tropical_asc(rec: Mapping) -> float:
    jd = swe.julday(rec["year"], rec["month"], rec["day"], rec["hour"] + rec["minute"] / 60 - rec["tz"])
    return swe.houses(jd, rec["lat"], rec["lon"], b"P")[1][0]


def gate(derived: Path) -> list[dict]:
    """Birth records passing the population rules and the Ascendant gate (addendum A)."""
    out, dropped = [], {"no_asc": 0, "cast_error": 0, "asc_mismatch": 0}
    for r in _master(derived).itertuples():
        want = published_asc(r.categories_raw)
        if want is None:
            dropped["no_asc"] += 1
            continue
        y, mo, d = (int(x) for x in r.birth_date.split("-"))
        h, mi = (int(x) for x in r.birth_time.split(":")[:2])
        rec = {"id": r.person_id, "year": y, "month": mo, "day": d, "hour": h, "minute": mi,
               "tz": float(r.tz_offset), "lat": float(r.latitude), "lon": float(r.longitude),
               "tier": r.quality_tier}
        try:
            got = tropical_asc(rec)
        except (swe.Error, ValueError):
            dropped["cast_error"] += 1
            continue
        diff = abs(got - want) % 360
        if min(diff, 360 - diff) > ASC_TOLERANCE_DEG:
            dropped["asc_mismatch"] += 1
            continue
        rec["time_source"] = "certificate" if r.quality_tier == "A" else "adb_tier_b"
        rec["uncertainty_minutes"] = 1 if r.quality_tier == "A" else 15
        out.append(rec)
    logger.info("gate kept %d, dropped %s", len(out), dropped)
    print(f"gate: kept {len(out)}; dropped {dropped}")
    return out


def _events(derived: Path):
    import pandas as pd
    e = pd.read_parquet(Path(derived) / "raman" / "person_events.parquet")
    e = e[e.date_precision == "day"].copy()
    e["root"] = e.event_root.str.strip()
    e["sub"] = e.event_subtype.fillna("").str.strip()
    return e


def timing_ids(derived: Path, ids: set[str]) -> set[str]:
    """People with a day-precise event of a registered matter: presence only, no dates used."""
    e = _events(derived)
    keep = set()
    for root, sub in TIMING_EVENTS.values():
        keep |= set(e[(e.root == root) & (e["sub"] == sub)].person_id)
    return keep & ids


def timing_events(derived: Path, ids: Iterable[str]) -> list[dict]:
    """Earliest day-precise event per person and matter (read only after the lock)."""
    e = _events(derived)
    e = e[e.person_id.isin(set(ids))]
    out = []
    for matter, (root, sub) in TIMING_EVENTS.items():
        x = e[(e.root == root) & (e["sub"] == sub)].sort_values(["event_year", "event_month", "event_day"])
        for r in x.drop_duplicates("person_id").itertuples():
            out.append({"id": r.person_id, "matter": matter,
                        "date": f"{int(r.event_year):04d}-{int(r.event_month):02d}-{int(r.event_day):02d}"})
    return out


def _rules(rec: Mapping) -> tuple[str, list[str]]:
    b = Birth(rec["year"], rec["month"], rec["day"], rec["hour"], rec["minute"], tz=rec["tz"],
              lat=rec["lat"], lon=rec["lon"], label=rec["id"])
    return rec["id"], [f.key for f in fundamentals(cast(b)) if f.met]


def lock_traits(gated: Sequence[Mapping], workers: int = 8) -> dict:
    with ProcessPoolExecutor(workers) as ex:
        fired = dict(ex.map(_rules, gated, chunksize=200))
    body = {"addendum": "KP_REAL_OUTCOME_PREREG_ADDENDUM_ADB_2026-11-02",
            "engine_commit": harness._commit(),
            "people": {r["id"]: {"tier": r["tier"], "lat": r["lat"], "year": r["year"],
                                 "fired": fired[r["id"]]} for r in gated}}
    return {"digest": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(), **body}


def _verify(locked: Mapping) -> None:
    body = {k: v for k, v in locked.items() if k != "digest"}
    if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != locked.get("digest"):
        raise SystemExit("locked trait rules were changed after locking; the test is void")


def fisher_one_sided(a: int, b: int, c: int, d: int, greater: bool) -> float:
    """P of a table at least as extreme as [[a, b], [c, d]] in one direction (a = cases firing)."""
    r1, c1, n = a + b, a + c, a + b + c + d
    lo, hi = max(0, r1 + c1 - n), min(r1, c1)

    def pmf(x: int) -> float:
        return math.exp(math.lgamma(r1 + 1) - math.lgamma(x + 1) - math.lgamma(r1 - x + 1)
                        + math.lgamma(n - r1 + 1) - math.lgamma(c1 - x + 1) - math.lgamma(n - r1 - c1 + x + 1)
                        - math.lgamma(n + 1) + math.lgamma(c1 + 1) + math.lgamma(n - c1 + 1))
    xs = range(a, hi + 1) if greater else range(lo, a + 1)
    return min(1.0, sum(pmf(x) for x in xs))


def risk_ratio(a: int, n1: int, c: int, n0: int) -> tuple[float, float, float]:
    if not (a and c and n1 and n0):
        return float("nan"), float("nan"), float("nan")
    rr = (a / n1) / (c / n0)
    se = math.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n0)
    return rr, rr * math.exp(-1.96 * se), rr * math.exp(1.96 * se)


@dataclass(frozen=True, slots=True)
class TraitResult:
    test: str
    rule: str
    role: str
    sample: str
    direction: str
    cases: int
    cases_firing: int
    controls: int
    controls_firing: int
    rate_cases: float
    rate_controls: float
    risk_ratio: float
    rr_low: float
    rr_high: float
    p_value: float
    verdict: str


def _tags(categories: str) -> set[str]:
    return {x.strip() for x in (categories or "").split(";")}


def trait_groups(tags: set[str]) -> dict[str, str]:
    """Case / control membership per registered test (absent = in neither group)."""
    g: dict[str, str] = {}
    none, kids = "Family : Parenting : Kids none", {"Family : Parenting : Kids 1-3",
                                                    "Family : Parenting : Kids more than 3"}
    if none in tags and not tags & kids:
        g["T1"] = "case"
    elif tags & kids and none not in tags:
        g["T1"] = "control"
    late = "Family : Relationship : Married late/never"
    married = {"Family : Relationship : Number of Marriages", "Family : Relationship : Marriage more than 15 Yrs"}
    if late in tags:
        g["T2"] = "case"
    elif tags & married:
        g["T2"] = "control"
    g["T3"] = "case" if tags & {"Traits : Body : Voice/Speech", "Vocation : Education : Public speaker"} else "control"
    g["T4"] = "case" if "Diagnoses : Psychological : Stutter, Tics" in tags else "control"
    return g


#: (test, rule, role, predicted more often in cases)
TRAIT_TESTS: Final[tuple[tuple[str, str, str, bool], ...]] = (
    ("T1", "progeny.lessened", "primary", True),
    ("T1", "progeny.promised_either", "secondary", False),
    ("T2", "marriage.late", "primary", True),
    ("T3", "voice.second", "primary", True),
    ("T3", "voice.second_venus_mercury", "secondary", True),
    ("T4", "speech.any", "primary", True),
)


def _fires(fired: Sequence[str], rule: str) -> bool:
    return any(r in fired for r in SPEECH_RULES) if rule == "speech.any" else rule in fired


def score_traits(locked: Mapping, tags_by_id: Mapping[str, set[str]]) -> tuple[list[TraitResult], dict]:
    _verify(locked)
    people = locked["people"]
    groups = {pid: trait_groups(tags_by_id.get(pid, set())) for pid in people}
    out, diag = [], {}
    for sample, tiers in (("A+B", {"A", "B"}), ("A", {"A"})):
        for test, rule, role, greater in TRAIT_TESTS:
            case = [p for p in people if people[p]["tier"] in tiers and groups[p].get(test) == "case"]
            ctrl = [p for p in people if people[p]["tier"] in tiers and groups[p].get(test) == "control"]
            a = sum(_fires(people[p]["fired"], rule) for p in case)
            c = sum(_fires(people[p]["fired"], rule) for p in ctrl)
            p = fisher_one_sided(a, len(case) - a, c, len(ctrl) - c, greater)
            rr, lo, hi = risk_ratio(a, len(case), c, len(ctrl))
            if len(case) < MIN_CASES:
                verdict = "UNDERPOWERED"
            elif p < ALPHA_TRAITS:
                verdict = "SIGNAL"
            else:
                verdict = "BOUNDED_NULL"
            out.append(TraitResult(test, rule, role, sample, "more in cases" if greater else "fewer in cases",
                                   len(case), a, len(ctrl), c, round(a / len(case), 4) if case else float("nan"),
                                   round(c / len(ctrl), 4) if ctrl else float("nan"), round(rr, 3), round(lo, 3),
                                   round(hi, 3), round(p, 5), verdict))
            if role == "primary":
                def _d(ids: list[str]) -> dict:
                    if not ids:
                        return {}
                    lats = sorted(abs(people[i]["lat"]) for i in ids)
                    yrs = sorted(people[i]["year"] for i in ids)
                    return {"mean_abs_lat": round(sum(lats) / len(lats), 2), "median_year": yrs[len(yrs) // 2]}
                diag[f"{test}/{sample}"] = {"cases": _d(case), "controls": _d(ctrl)}
    return out, diag


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--derived", type=Path, required=True)
    g.add_argument("--out", required=True)
    lt = sub.add_parser("lock-timing")
    lt.add_argument("--derived", type=Path, required=True)
    lt.add_argument("--gated", required=True)
    lt.add_argument("--out", required=True)
    ev = sub.add_parser("events")
    ev.add_argument("--derived", type=Path, required=True)
    ev.add_argument("--locked", required=True)
    ev.add_argument("--out", required=True)
    lk = sub.add_parser("lock-traits")
    lk.add_argument("--gated", required=True)
    lk.add_argument("--out", required=True)
    lk.add_argument("--workers", type=int, default=8)
    st = sub.add_parser("score-traits")
    st.add_argument("--derived", type=Path, required=True)
    st.add_argument("--locked", required=True)
    st.add_argument("--out", default="")
    a = ap.parse_args()

    def write(path: str, obj: object) -> None:
        harness._guard(path).write_text(json.dumps(obj, indent=1), encoding="utf-8")

    if a.cmd == "gate":
        write(a.out, gate(a.derived))
    elif a.cmd == "lock-timing":
        gated = json.loads(Path(a.gated).read_text(encoding="utf-8"))
        ids = timing_ids(a.derived, {r["id"] for r in gated})
        births = [r for r in gated if r["id"] in ids]
        locked = harness.lock(births)
        write(a.out, locked)
        print(f"locked {len(births)} people ({sum(p['primary'] for p in locked['people'])} primary), "
              f"digest {locked['digest']}")
    elif a.cmd == "events":
        locked = json.loads(Path(a.locked).read_text(encoding="utf-8"))
        harness.verify(locked)
        evs = timing_events(a.derived, [p["id"] for p in locked["people"]])
        write(a.out, evs)
        print(f"wrote {len(evs)} events")
    elif a.cmd == "lock-traits":
        gated = json.loads(Path(a.gated).read_text(encoding="utf-8"))
        locked = lock_traits(gated, a.workers)
        write(a.out, locked)
        print(f"locked rules for {len(locked['people'])} people, digest {locked['digest']}")
    else:
        locked = json.loads(Path(a.locked).read_text(encoding="utf-8"))
        m = _master(a.derived)
        tags = {r.person_id: _tags(r.categories_raw) for r in m.itertuples()}
        res, diag = score_traits(locked, tags)
        for r in res:
            print(f"{r.test} {r.rule} [{r.role}, {r.sample}] cases {r.cases_firing}/{r.cases} "
                  f"({r.rate_cases}) vs controls {r.controls_firing}/{r.controls} ({r.rate_controls}); "
                  f"RR {r.risk_ratio} ({r.rr_low}-{r.rr_high}); p={r.p_value} -> {r.verdict}")
        if a.out:
            Path(a.out).write_text(json.dumps({"digest": locked["digest"], "results": [asdict(r) for r in res],
                                               "diagnostics": diag}, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
