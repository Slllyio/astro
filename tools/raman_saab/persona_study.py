"""The persona study — famous documented lives answering the feedback instrument, blind.

BUILD-TIME tool — lives OUTSIDE app/. REPORT-ONLY: it reads verdicts and never changes them,
so the golden ratchet is untouched by construction.

Read `docs/raman_saab/PERSONA_STUDY_PREREG.md` first. It fixes the roster, the admission gate,
the primary endpoint and the three control arms, and it was committed before any chart here
was cast. This module only executes what that document specifies.

The stages are separate subcommands, each resumable, because one of them is not a program:
the persona answers come from agents reading biographies with no access to the chart, and the
blind is enforced by ORDER — answers are written and hashed before any answer key exists.

    roster    resolve the pre-registered candidates through the admission gate
    build     cast each admitted nativity and emit its blind question payload
    verify    assert the payloads carry no answer key, and hash the collected answers
    submit    post the answers through the real endpoint, context=before_reading
    score     the primary, the cross-chart control, and the coin-flip sham gate

Usage:
    py -3.12 -m tools.raman_saab.persona_study roster
    py -3.12 -m tools.raman_saab.persona_study build
    py -3.12 -m tools.raman_saab.persona_study verify
    py -3.12 -m tools.raman_saab.persona_study submit --base-url http://127.0.0.1:8000
    py -3.12 -m tools.raman_saab.persona_study score --html data/persona_study/scorecard.html
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tools.raman_saab.persona_birthdata import (
    ACCEPTED_RATINGS, BirthRecord, fetch_page, geocode, parse_astrotheme,
    standard_time_offset)

logger = logging.getLogger(__name__)

OUT = Path("data/persona_study")

#: Times that are not a claim about the hour. `astrobank/_names.py` classifies a 12:00 prefix
#: as `noon_default` and `quality_tier` returns None for it at every tier — see the
#: pre-registration's Deviation 1.
_NOON_DEFAULT = (12, 0)


@dataclass(frozen=True)
class Candidate:
    """One pre-registered name, in its registered order within a stratum."""
    slug: str
    stratum: int
    zone: str
    #: Year of death, or None if they reached 40 while living. Used only to place the
    #: reference date inside the documented life (see `reference_date`).
    died_before_40: Optional[int] = None


#: The candidate list from PREREG §4, in registered order. The first four per stratum that
#: pass the admission gate enter the study; the rest are recorded as drops.
ROSTER: tuple[Candidate, ...] = (
    # 1 — long life, broad success
    Candidate("Elizabeth_II", 1, "Europe/London"),
    Candidate("Katharine_Hepburn", 1, "America/New_York"),
    Candidate("Jimmy_Carter", 1, "America/New_York"),
    Candidate("George_Burns", 1, "America/New_York"),
    Candidate("Bob_Hope", 1, "Europe/London"),
    Candidate("Clint_Eastwood", 1, "America/Los_Angeles"),
    Candidate("Sean_Connery", 1, "Europe/London"),
    Candidate("Charlie_Chaplin", 1, "Europe/London"),
    # 2 — early or violent death
    Candidate("Marilyn_Monroe", 2, "America/Los_Angeles", died_before_40=1962),
    Candidate("James_Dean", 2, "America/Indiana/Indianapolis", died_before_40=1955),
    Candidate("John_Fitzgerald_Kennedy", 2, "America/New_York"),
    Candidate("Martin_Luther_King", 2, "America/New_York"),
    Candidate("Janis_Joplin", 2, "America/Chicago", died_before_40=1970),
    Candidate("Jimi_Hendrix", 2, "America/Los_Angeles", died_before_40=1970),
    Candidate("Bruce_Lee", 2, "America/Los_Angeles", died_before_40=1973),
    Candidate("Lady_Diana", 2, "Europe/London"),
    # 3 — imprisonment or legal ruin
    Candidate("Nelson_Mandela", 3, "Africa/Johannesburg"),
    Candidate("Al_Capone", 3, "America/New_York"),
    Candidate("Bernard_Madoff", 3, "America/New_York"),
    Candidate("Mike_Tyson", 3, "America/New_York"),
    Candidate("O.J._Simpson", 3, "America/Los_Angeles"),
    Candidate("Martha_Stewart", 3, "America/New_York"),
    Candidate("Jean_Genet", 3, "Europe/Paris"),
    Candidate("Patty_Hearst", 3, "America/Los_Angeles"),
    # 4 — chronic illness or disability
    Candidate("Stephen_Hawking", 4, "Europe/London"),
    Candidate("Ray_Charles", 4, "America/New_York"),
    Candidate("Stevie_Wonder", 4, "America/Detroit"),
    Candidate("Christopher_Reeve", 4, "America/New_York"),
    Candidate("Michael_J._Fox", 4, "America/Edmonton"),
    Candidate("Helen_Keller", 4, "America/Chicago"),
    Candidate("Frida_Kahlo", 4, "America/Mexico_City"),
    Candidate("Franklin_D._Roosevelt", 4, "America/New_York"),
    # 5 — childlessness or family rupture
    Candidate("Elizabeth_Taylor", 5, "Europe/London"),
    Candidate("Marlene_Dietrich", 5, "Europe/Berlin"),
    Candidate("Greta_Garbo", 5, "Europe/Stockholm"),
    Candidate("Oprah_Winfrey", 5, "America/Chicago"),
    Candidate("Dolly_Parton", 5, "America/New_York"),
    Candidate("Coco_Chanel", 5, "Europe/Paris"),
    Candidate("Mia_Farrow", 5, "America/Los_Angeles"),
    Candidate("Jack_Nicholson", 5, "America/New_York"),
    # 6 — wealth to ruin, or ruin to wealth
    Candidate("Walt_Disney", 6, "America/Chicago"),
    Candidate("Willie_Nelson", 6, "America/Chicago"),
    Candidate("Elvis_Presley", 6, "America/Chicago"),
    Candidate("MC_Hammer", 6, "America/Los_Angeles"),
    Candidate("Donald_Trump", 6, "America/New_York"),
    Candidate("Larry_King", 6, "America/New_York"),
    Candidate("Judy_Garland", 6, "America/Chicago"),
    Candidate("Burt_Reynolds", 6, "America/Detroit"),
)

PER_STRATUM = 4


def admit(cand: Candidate, rec: Optional[BirthRecord]) -> tuple[Optional[BirthRecord], str]:
    """Run PREREG §4's gate. Returns (record or None, reason) — the reason is kept even on
    success so the roster file records why every name was where it ended up."""
    if rec is None:
        return None, "page states no nativity"
    if rec.rodden.upper() not in ACCEPTED_RATINGS:
        return None, f"Rodden {rec.rodden or 'none stated'}"
    if (rec.hour, rec.minute) == _NOON_DEFAULT:
        return None, "12:00 is a noon default, not a stated hour (Deviation 1)"
    offset = standard_time_offset(cand.zone, rec)
    if offset is None:
        return None, f"{rec.place} was not on standard time in {rec.year}"
    coords = geocode(rec.place)
    if coords is None:
        return None, f"no coordinates for {rec.place!r}"
    lat, lon = coords
    return dataclasses.replace(rec, latitude=lat, longitude=lon,
                               zone=cand.zone, tz_offset=offset), "admitted"


def time_precision(rec: BirthRecord) -> str:
    """Minute / quarter / round_hour, recorded so results can be split by it."""
    if rec.minute == 0:
        return "round_hour"
    return "quarter" if rec.minute in (15, 30, 45) else "minute"


def reference_date(rec: BirthRecord, cand: Candidate) -> tuple:
    """The date the chart is read as of — inside the documented life (PREREG §4).

    The 40th birthday, or for someone who did not reach 40 the midpoint between 18 and
    death. Read as of today a historical chart has an empty timeline, and every timing
    measurement would be vacuous; Part C's verdicts do not depend on this at all.
    """
    if cand.died_before_40 is None:
        return (rec.year + 40, rec.month, rec.day)
    age_at_death = cand.died_before_40 - rec.year
    return (rec.year + max(18, (18 + age_at_death) // 2), rec.month, rec.day)


def resolve_roster(*, pause: float = 0.3) -> dict:
    """Fetch and gate every candidate, take the first `PER_STRATUM` per stratum that pass."""
    picked: dict[int, list] = {}
    rows, drops = [], []
    for cand in ROSTER:
        chosen = picked.setdefault(cand.stratum, [])
        if len(chosen) >= PER_STRATUM:
            drops.append({"slug": cand.slug, "stratum": cand.stratum,
                          "reason": "stratum already filled by earlier registered names"})
            continue
        try:
            parsed = parse_astrotheme(fetch_page(cand.slug), slug=cand.slug)
        except Exception as exc:                          # noqa: BLE001 — network
            logger.warning("fetch failed for %s: %s", cand.slug, exc)
            parsed = None
        time.sleep(pause)
        rec, reason = admit(cand, parsed)
        if rec is None:
            drops.append({"slug": cand.slug, "stratum": cand.stratum, "reason": reason})
            continue
        entry = {**dataclasses.asdict(rec), "stratum": cand.stratum,
                 "time_precision": time_precision(rec),
                 "reference_date": list(reference_date(rec, cand))}
        chosen.append(entry)
        rows.append(entry)
    return {"admitted": rows, "dropped": drops,
            "counts": {str(s): len(v) for s, v in sorted(picked.items())}}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cmd_roster(args) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data = resolve_roster()
    dest = OUT / "roster.json"
    dest.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    for s, n in data["counts"].items():
        print(f"[persona-study] stratum {s}: {n}/{PER_STRATUM}")
    print(f"[persona-study] admitted {len(data['admitted'])}, "
          f"dropped {len(data['dropped'])}")
    for d in data["dropped"]:
        print(f"    drop  {d['slug']:26} {d['reason']}")
    print(f"[persona-study] wrote {dest}  sha256={sha256_of(dest)[:16]}")
    return 0


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Run a stage of the persona study.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster", help="resolve the pre-registered candidates through the gate")
    args = ap.parse_args(argv)
    return {"roster": _cmd_roster}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
