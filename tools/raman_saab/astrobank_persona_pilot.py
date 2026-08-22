"""Pilot extension of the persona study to `data/astro_databank` names (n=12).

The original study (`persona_study.py`) found the blind arm null and the contaminated arm
directionally positive but underpowered at n=23 ("this cannot size the effect, only its
direction"). This pilot tests whether the SAME rigorous method (blind biography-reading,
forced-choice instrument, coin-flip sham gate, cross-chart control, contaminated arm) holds
up on a fresh, non-overlapping name pool drawn from `data/astro_databank/raw_lapaas.csv` —
which already carries Rodden-rated, quality-gated birth data, so no astrotheme fetch or
geocoding is needed here.

This is a SEPARATE, unregistered pilot, not an amendment to `PERSONA_STUDY_PREREG.md` — that
document was fixed before any chart in the original study was cast, and this roster was not.
Treat any number out of this pilot as suggestive, not confirmatory; a real extension would need
its own pre-registration in the same spirit.

Deviation from the original gate: candidates are restricted to births from 1910 onward so the
standard-time-offset check (`persona_study.standard_time_offset` equivalent, done once here at
selection time against each CSV `tz_offset`, all confirmed quarter-hour) cannot land on a
pre-standard-time LMT-vs-zone mismatch — the exact trap `persona_birthdata.py` documents.

Usage:
    py -3.12 -m tools.raman_saab.astrobank_persona_pilot roster
    py -3.12 -m tools.raman_saab.astrobank_persona_pilot build
    py -3.12 -m tools.raman_saab.astrobank_persona_pilot readings
    py -3.12 -m tools.raman_saab.astrobank_persona_pilot questions
    py -3.12 -m tools.raman_saab.astrobank_persona_pilot verify
    py -3.12 -m tools.raman_saab.astrobank_persona_pilot score --html data/astrobank_persona_pilot/scorecard.html
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from tools.raman_saab import persona_study as ps

#: Collected answers are primary data (see persona_study.py's own note on this) — committed,
#: not derived. Same directory shape as the original study, different root.
OUT = Path("tests/fixtures/astrobank_persona_pilot")


@dataclass(frozen=True)
class Candidate:
    slug: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    tz_offset: float
    latitude: float
    longitude: float
    rodden: str


#: Selected 2026-08-22 from data/astro_databank/raw_lapaas.csv: Rodden AA, born 1910+ (sidesteps
#: the pre-standard-time LMT trap), tz_offset already a quarter-hour multiple (verified), and
#: NONE overlapping persona_study.py's ROSTER (a fresh, independent name pool). Diversity by
#: domain (tech/music/sport/humanitarian/politics), not hand-picked for any expected outcome —
#: this is every AA-rated, standard-time-safe name found on a fixed initial search list, in the
#: order found, not curated post-hoc for favourable cases.
ROSTER: tuple[Candidate, ...] = (
    Candidate("Steve_Jobs", 1955, 2, 24, 19, 15, -8.0, 37.7749, -122.4194, "AA"),
    Candidate("Michael_Jackson", 1958, 8, 29, 19, 33, -5.0, 41.5933, -87.3461, "AA"),
    Candidate("John_Lennon", 1940, 10, 9, 18, 30, 1.0, 53.4084, -2.9916, "AA"),
    Candidate("David_Bowie", 1947, 1, 8, 9, 0, 0.0, 51.452, 0.007, "AA"),
    Candidate("Madonna", 1958, 8, 16, 7, 5, -5.0, 43.015, -83.6875, "AA"),
    Candidate("Muhammad_Ali", 1942, 1, 17, 18, 35, -6.0, 38.2527, -85.7585, "AA"),
    Candidate("Mother_Teresa", 1910, 8, 26, 14, 25, 1.0, 42.0, 21.4333, "AA"),
    Candidate("Margaret_Thatcher", 1925, 10, 13, 9, 0, 0.0, 52.9131, -0.6394, "AA"),
    Candidate("Bill_Clinton", 1946, 8, 19, 8, 51, -5.0, 33.6609, -93.5933, "AA"),
    Candidate("Justin_Trudeau", 1971, 12, 25, 21, 27, -5.0, 45.5017, -73.5673, "AA"),
    Candidate("Jacinda_Ardern", 1980, 7, 26, 16, 18, 12.0, -37.787, 175.2793, "AA"),
    Candidate("Emmanuel_Macron", 1977, 12, 21, 10, 40, 1.0, 49.8941, 2.2958, "AA"),
)


def resolve_roster() -> dict:
    """No fetch/geocode needed — astro_databank already carries resolved coordinates and a
    standard-time offset per person. Reference date follows persona_study's rule: the 40th
    birthday (none of these 12 died before 40)."""
    rows = []
    for c in ROSTER:
        rows.append({
            "slug": c.slug, "name": c.slug.replace("_", " "),
            "year": c.year, "month": c.month, "day": c.day,
            "hour": c.hour, "minute": c.minute, "tz_offset": c.tz_offset,
            "latitude": c.latitude, "longitude": c.longitude,
            "rodden": c.rodden, "source_note": "data/astro_databank/raw_lapaas.csv",
            "reference_date": [c.year + 40, c.month, c.day],
        })
    return {"admitted": rows, "dropped": [], "counts": {"1": len(rows)}}


def _cmd_roster(args) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data = resolve_roster()
    dest = OUT / "roster.json"
    dest.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[astrobank-pilot] admitted {len(data['admitted'])}, dropped {len(data['dropped'])}")
    print(f"[astrobank-pilot] wrote {dest}  sha256={ps.sha256_of(dest)[:16]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    global OUT
    ap = argparse.ArgumentParser(description=__doc__)
    # Collected answers can never be rebuilt (a model does not answer identically twice), so a
    # second run of the same roster writes to its own directory rather than over the first.
    ap.add_argument("--out", type=Path, default=OUT,
                    help="study directory (default: %(default)s)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster")
    for name in ("build", "readings", "questions"):
        p = sub.add_parser(name)
        p.add_argument("--force", action="store_true")
    sub.add_parser("verify")
    p = sub.add_parser("score")
    p.add_argument("--html", type=Path, default=None)
    p.add_argument("--seed", default="astrobank-persona-pilot")
    p.add_argument("--permutations", type=int, default=2000)
    args = ap.parse_args(argv)

    # Delegate the heavy machinery to persona_study.py by pointing its OUT at ours — every
    # _cmd_* there resolves paths through the module-global OUT looked up at call time.
    OUT = args.out
    ps.OUT = args.out

    dispatch = {
        "roster": _cmd_roster,
        "build": ps._cmd_build,
        "readings": ps._cmd_readings,
        "questions": ps._cmd_questions,
        "verify": ps._cmd_verify,
        "score": ps._cmd_score,
    }
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
