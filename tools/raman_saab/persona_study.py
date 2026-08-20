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


#: Fields that would betray which option is the chart's own. `build` asserts none of them
#: reaches a payload file rather than trusting that they do not — the blind is the study.
_KEY_TOKENS = ("band_share", "signification", "verdict", "inverted_warning",
               "favourability_percentile", "rarity")


def _cmd_build(args) -> int:
    """Cast each admitted nativity and split what it produces into two directories.

    `payloads/` is what a persona agent may see: questions and options, nothing else.
    `verdicts/` is answer-key material — the chart's own reading of every signification,
    needed later for the cross-chart control — and no agent is given its path.
    """
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict

    roster = json.loads((OUT / "roster.json").read_text(encoding="utf-8"))
    (OUT / "payloads").mkdir(parents=True, exist_ok=True)
    (OUT / "verdicts").mkdir(parents=True, exist_ok=True)

    for rec in roster["admitted"]:
        dest = OUT / "payloads" / f"{rec['slug']}.json"
        if dest.is_file() and not args.force:
            print(f"[persona-study] {rec['slug']:26} payload exists, skipping")
            continue
        birth = BirthData(rec["name"], rec["year"], rec["month"], rec["day"], rec["hour"],
                          rec["minute"], float(rec["tz_offset"]), float(rec["latitude"]),
                          float(rec["longitude"]))
        report = to_report_dict(build_detailed_report(
            birth, on=tuple(rec["reference_date"])))
        inst = report["feedback_instrument"]

        blob = json.dumps(inst, ensure_ascii=False)
        leaked = [t for t in _KEY_TOKENS if t in blob]
        if leaked:
            raise SystemExit(f"[persona-study] ABORT: {rec['slug']} payload leaks {leaked}")

        dest.write_text(json.dumps(
            {"slug": rec["slug"], "name": rec["name"], "instrument": inst},
            indent=1, ensure_ascii=False), encoding="utf-8")
        (OUT / "verdicts" / f"{rec['slug']}.json").write_text(json.dumps(
            {"slug": rec["slug"],
             "chart_key": chart_key_for(rec),
             "verdicts": {e["signification"]: {"house": int(h), "verdict": e["verdict"],
                                               "band_share": e["band_share"]}
                          for h, hd in report["calibration"].items()
                          for e in hd["entries"]}},
            indent=1, ensure_ascii=False), encoding="utf-8")
        counts = inst["counts"]
        print(f"[persona-study] {rec['slug']:26} built  A{counts['A']} B{counts['B']} "
              f"C{counts['C']} D{counts['D']}  no key in payload")
    return 0


def render_questions(payload: dict) -> str:
    """The instrument as a compact block a blind answerer can work from.

    Deliberately carries the qid, the question, and the option CODES only. No part labels
    beyond the section titles, no hints about which option a chart would pick, and — because
    the payload never held them — no verdicts to leak.
    """
    lines: list[str] = []
    for part in payload["instrument"]["parts"]:
        lines.append(f"\n## {part['part']}. {part['title_en']}")
        for q in part["questions"]:
            opts = "  |  ".join(f"{o['value']} = {o['text_en']}" for o in q["options"])
            lines.append(f"[{q['qid']}] ({q['kind']}) {q['text_en']}")
            if opts:
                lines.append(f"    {opts}")
            if q.get("confidence"):
                lines.append(f"    also answer {q['qid']}.confidence = 1..5")
    return "\n".join(lines)


def _cmd_questions(args) -> int:
    (OUT / "questions").mkdir(parents=True, exist_ok=True)
    for src in sorted((OUT / "payloads").glob("*.json")):
        payload = json.loads(src.read_text(encoding="utf-8"))
        dest = OUT / "questions" / f"{payload['slug']}.txt"
        dest.write_text(render_questions(payload), encoding="utf-8")
        print(f"[persona-study] {payload['slug']:26} {len(dest.read_text()):6d} chars")
    return 0


def coinflip_answers(payload: dict, *, seed: str) -> dict:
    """The control arm: an answerer with no knowledge of anything.

    Deterministic so the arm is reproducible — the digest of (seed, qid) picks the option,
    which is the same construction the instrument itself uses to shuffle them. It must score
    0.5, and until it does no other number in the study may be read (PREREG §2b).
    """
    out: dict[str, str] = {}
    for part in payload["instrument"]["parts"]:
        for q in part["questions"]:
            if q["kind"] != "choice" or not q["options"]:
                continue
            digest = hashlib.sha256(f"{seed}:{q['qid']}".encode()).hexdigest()
            pick = q["options"][int(digest[:8], 16) % len(q["options"])]
            out[q["qid"]] = pick["value"]
    return out


def chart_key_for(rec: dict) -> str:
    """The server's own chart_key format (`report_routes._chart_key`), reproduced so a
    submission and a score agree on which nativity they are talking about."""
    return (f"{rec['year']:04d}-{rec['month']:02d}-{rec['day']:02d}"
            f"T{rec['hour']:02d}:{rec['minute']:02d}{float(rec['tz_offset']):+.2f}"
            f"@{float(rec['latitude']):.4f},{float(rec['longitude']):.4f}")


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Run a stage of the persona study.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster", help="resolve the pre-registered candidates through the gate")
    b = sub.add_parser("build", help="cast each nativity, emit its blind question payload")
    b.add_argument("--force", action="store_true", help="rebuild payloads that already exist")
    sub.add_parser("questions", help="render each payload as a compact blind question block")
    args = ap.parse_args(argv)
    return {"roster": _cmd_roster, "build": _cmd_build,
            "questions": _cmd_questions}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
