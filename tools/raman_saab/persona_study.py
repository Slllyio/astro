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
    score     the primary, the cross-chart control, and the coin-flip sham gate

Usage:
    py -3.12 -m tools.raman_saab.persona_study roster
    py -3.12 -m tools.raman_saab.persona_study build
    py -3.12 -m tools.raman_saab.persona_study verify
    py -3.12 -m tools.raman_saab.persona_study score --html data/persona_study/scorecard.html
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tools.raman_saab.persona_birthdata import (
    ACCEPTED_RATINGS, BirthRecord, fetch_page, geocode, parse_astrotheme,
    standard_time_offset)

logger = logging.getLogger(__name__)

#: Where the study's data lives. `tests/fixtures/` and not `data/`, because these are
#: COLLECTED answers — a language model does not answer identically twice, so nothing here can
#: be rebuilt once lost. `data/` is gitignored for DERIVED artifacts that always can be, and
#: the first run learned the difference the hard way: a container restart took every answer
#: file and the hash manifest that evidenced the blind with it. `tests/fixtures/field_case_01.json`
#: is the existing precedent for committed primary data.
OUT = Path("tests/fixtures/persona_study")
#: Derived and NOT committed: both are reproducible from the roster plus the engine at a known
#: commit, which is why `results.json` records `engine_git_sha`.
_DERIVED = ("payloads", "verdicts", "questions", "readings")

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


def engine_git_sha() -> str:
    """The commit the engine was at when a run was scored.

    Recorded in `results.json` because the payloads and verdicts are NOT committed — they are
    reproducible from the roster, but only against the same engine. Without this, a later
    reader could re-run `score` on a moved engine and get different numbers with nothing to
    say why. Follows `tools/raman_saab/astrobank/real_outcome_baseline.json`, which stamps the
    same field for the same reason.
    """
    import subprocess
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             timeout=10)
        return out.stdout.strip() or "(unknown)"
    except Exception:                                     # noqa: BLE001 — no git, no matter
        return "(unknown)"


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

    `payloads/` is what a persona agent may see: questions and options, nothing else — the
    leak assertion below proves it carries no verdict, band share or signification name.
    `verdicts/` is answer-key material — the chart's own reading of every signification,
    needed by `readings` and by the cross-chart control — and no agent is given its path.

    Note what the blind therefore does and does not rest on. It rests on CONSTRUCTION: the
    payload provably cannot carry the key, so an answerer cannot see one however it is
    served. It does NOT rest on the key being computed later — `verdicts/` is written here,
    at build time, because the contaminated arm's own input is derived from it. What
    `verify` adds is the operator's half: once answers are hashed they cannot be revised in
    the light of a score.
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


def _answer_rows(doc: dict) -> list:
    """(question_id, answer, free_text) triples — the shape `score_chart` consumes."""
    free = doc.get("free_text") or {}
    rows = [(qid, str(val), free.get(qid)) for qid, val in (doc.get("answers") or {}).items()]
    return rows + [(qid, "answered", text) for qid, text in free.items()
                   if qid not in (doc.get("answers") or {})]


def _cmd_readings(args) -> int:
    """Emit each persona's rendered reading — the contaminated arm's input (PREREG 2c).

    This is the ONE directory an answerer is meant to see the chart through. It exists to
    measure the curation asymmetry: an answerer who has read the reading first should agree
    with it more than a blind one, and by how much is the number worth having.
    """
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict
    from app.raman_saab.chart.model import BirthData

    roster = json.loads((OUT / "roster.json").read_text(encoding="utf-8"))
    (OUT / "readings").mkdir(parents=True, exist_ok=True)
    for rec in roster["admitted"]:
        dest = OUT / "readings" / f"{rec['slug']}.txt"
        if dest.is_file() and not args.force:
            print(f"[persona-study] {rec['slug']:26} reading exists, skipping")
            continue
        birth = BirthData(rec["name"], rec["year"], rec["month"], rec["day"], rec["hour"],
                          rec["minute"], float(rec["tz_offset"]), float(rec["latitude"]),
                          float(rec["longitude"]))
        d = to_report_dict(build_detailed_report(birth, on=tuple(rec["reference_date"])))
        sr = d.get("short_reading") or {}
        ss = d.get("simple_summary") or {}
        lines = [f"# What the chart says about {rec['name']}", ""]
        for label, key, src in (
                ("In plain words", "opening_en", ss), ("About you", "you_en", ss),
                ("What reads well", "good_en", ss), ("What reads hard", "hard_en", ss),
                ("Mixed", "mixed_en", ss), ("Right now", "now_en", ss),
                ("Unusual for this chart", "unusual_en", ss),
                ("What is coming", "periods_en", sr), ("Combinations", "combinations_en", sr)):
            val = src.get(key)
            if val:
                lines += [f"## {label}", str(val), ""]
        for label, key in (("Matters that read well", "good_items_en"),
                           ("Matters that read hard", "hard_items_en"),
                           ("Matters that read mixed", "mixed_items_en"),
                           ("Live right now", "now_items_en")):
            items = ss.get(key) or ()
            if items:
                lines += [f"## {label}"] + [f"- {i}" for i in items] + [""]
        dest.write_text("\n".join(lines), encoding="utf-8")
        print(f"[persona-study] {rec['slug']:26} reading {len(dest.read_text()):6d} chars")
    return 0


#: An answer arriving from an events question carries its code behind the date: `1990-06:marriage`.
_EVENT_ANSWER = re.compile(r"^\d{4}(?:-\d{2})?:(.+)$")

#: Both collected arms. The blind arm answers from a life alone; the contaminated arm reads the
#: chart's own reading first (PREREG 2c). Both are collected data and both are hashed before any
#: key exists — the second one is not a lesser record for having been contaminated by design.
ARMS: tuple = ("answers", "answers_contaminated")


def option_vocabulary(payload: dict) -> dict:
    """Every legal option code, by qid, from the chart's own question payload.

    A question that offers no options — a year, a date, free prose — maps to an empty set,
    which is how `off_vocabulary` tells "nothing to check here" apart from "no such question".
    """
    return {q["qid"]: frozenset(o["value"] for o in q["options"])
            for part in payload["instrument"]["parts"] for q in part["questions"]}


def off_vocabulary(answers: dict, vocab: dict) -> dict:
    """Answer tokens no question offered — the quiet data error the scorer absorbs.

    An unknown code crashes nothing. It simply never matches, so the item scores as one
    fewer agreement and the study reports a colder number for a reason that appears nowhere
    on the record. That is the worst kind of error this study can make, because it looks
    exactly like an honest result. Naming the strays at verify time, before any key is
    computed, is the last point at which seeing them is still free.
    """
    stray: dict = {}
    for qid, value in answers.items():
        base = qid.removesuffix(".confidence").split("#", 1)[0]
        if base not in vocab:
            stray[qid] = ("<no such question>",)
            continue
        if qid.endswith(".confidence"):
            continue
        options = vocab[base]
        if not options:
            continue
        given = []
        for token in str(value).split(","):
            token = token.strip()
            if not token:
                continue
            m = _EVENT_ANSWER.match(token)
            given.append(m.group(1) if m else token)
        bad = tuple(g for g in given if g not in options)
        if bad:
            stray[qid] = bad
    return stray


def _cmd_verify(args) -> int:
    """Hash every collected answer file before it is scored.

    This is the operator's half of the blind — the answerer's half is enforced in `build`, by
    a payload that provably carries no key. Once the digest is written the answers cannot be
    revised in the light of a score. (It is NOT a claim that no key existed yet: `build`
    writes `verdicts/` because the contaminated arm is rendered from it.) Both arms are
    hashed, and each file is checked against its own chart's option bank on the way past.
    """
    manifest: dict = {}
    strays = 0
    for arm in ARMS:
        for path in sorted((OUT / arm).glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            payload = json.loads(
                (OUT / "payloads" / f"{doc['slug']}.json").read_text(encoding="utf-8"))
            given = doc.get("answers") or {}
            off = off_vocabulary(given, option_vocabulary(payload))
            strays += len(off)
            entry = {"sha256": sha256_of(path), "answers": len(given),
                     "free_text": len(doc.get("free_text") or {}),
                     "off_vocabulary": {k: list(v) for k, v in sorted(off.items())}}
            manifest.setdefault(arm, {})[doc["slug"]] = entry
            flag = f"  OFF-VOCAB {off}" if off else ""
            print(f"[persona-study] {arm:20} {doc['slug']:26} {entry['answers']:3d} answers "
                  f"sha256={entry['sha256'][:16]}{flag}")
    dest = OUT / "answers_manifest.json"
    dest.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    counts = " + ".join(f"{len(v)} {k}" for k, v in manifest.items())
    print(f"[persona-study] {counts} hashed -> {dest}")
    print(f"[persona-study] off-vocabulary answers: {strays}"
          + ("  (recorded, not corrected — they score as misses)" if strays else ""))
    return 0


#: How a Part C answer decodes into a claim about a life. The instrument pairs the chart's
#: own predicate with its exact inverse, so answering the key means claiming the chart's
#: pole and answering the other means claiming its opposite (`feedback_instrument._OPPOSITE`).
def _pole(verdict: str, chose_key: bool) -> str:
    from app.raman_saab.feedback_instrument import _OPPOSITE
    pair = _OPPOSITE.get(verdict)
    return "" if pair is None else (pair[0] if chose_key else pair[1])


def _pole_matches(pole: str, verdict: str) -> Optional[bool]:
    """Does a claimed pole agree with some chart's verdict on the same signification?

    `one_way` is the inverse of `mixed` and means "solidly one thing or the other", so it
    agrees with a favourable OR an afflicted verdict. A verdict the engine abstained on
    (`insufficient-evidence`) is not comparable and returns None rather than a miss.
    """
    if verdict not in ("favourable", "afflicted", "mixed"):
        return None
    if pole == "one_way":
        return verdict in ("favourable", "afflicted")
    if pole == "mixed":
        return verdict == "mixed"
    if pole in ("favourable", "afflicted"):
        return verdict == pole
    return None


def cross_chart(claims: dict, verdicts: dict) -> dict:
    """The study's decisive control (PREREG §2a).

    `claims[slug]` is that persona's list of (signification, pole). `verdicts[slug]` is that
    chart's verdict per signification. Scores each persona against their OWN chart and
    against every OTHER chart, and reports the contrast — because neither arm has a null of
    0.5 on its own and between-chart agreement is itself unstable.
    """
    matched_hits = matched_n = 0
    mism_hits = mism_n = 0
    per_persona = {}
    for slug, items in claims.items():
        own = verdicts.get(slug, {})
        m_h = m_n = 0
        for sig, pole in items:
            got = _pole_matches(pole, (own.get(sig) or {}).get("verdict", ""))
            if got is not None:
                m_n += 1
                m_h += int(got)
        x_h = x_n = 0
        for other, their in verdicts.items():
            if other == slug:
                continue
            for sig, pole in items:
                got = _pole_matches(pole, (their.get(sig) or {}).get("verdict", ""))
                if got is not None:
                    x_n += 1
                    x_h += int(got)
        matched_hits += m_h
        matched_n += m_n
        mism_hits += x_h
        mism_n += x_n
        per_persona[slug] = {"matched": [m_h, m_n], "mismatched": [x_h, x_n]}
    return {"matched": [matched_hits, matched_n], "mismatched": [mism_hits, mism_n],
            "matched_rate": (matched_hits / matched_n) if matched_n else None,
            "mismatched_rate": (mism_hits / mism_n) if mism_n else None,
            "contrast": ((matched_hits / matched_n) - (mism_hits / mism_n))
                        if matched_n and mism_n else None,
            "per_persona": per_persona}


def permutation_p(claims: dict, verdicts: dict, *, rounds: int = 2000,
                  seed: str = "persona-study") -> Optional[float]:
    """How often a RANDOM persona-to-chart assignment beats the real one.

    The null is "the chart carries no person-specific information", under which the real
    pairing is just one of the many possible pairings. Deterministic: the shuffle is driven
    by a digest, because `random` is not reproducible across runs without pinning and this
    number goes into a results document.
    """
    slugs = [s for s in claims if s in verdicts]
    if len(slugs) < 3:
        return None

    def rate(assign: dict) -> Optional[float]:
        hits = n = 0
        for persona, chart in assign.items():
            their = verdicts[chart]
            for sig, pole in claims[persona]:
                got = _pole_matches(pole, (their.get(sig) or {}).get("verdict", ""))
                if got is not None:
                    n += 1
                    hits += int(got)
        return (hits / n) if n else None

    observed = rate({s: s for s in slugs})
    if observed is None:
        return None
    beat = 0
    for r in range(rounds):
        order = sorted(slugs, key=lambda s: hashlib.sha256(f"{seed}:{r}:{s}".encode()).digest())
        shuffled = rate(dict(zip(slugs, order)))
        if shuffled is not None and shuffled >= observed:
            beat += 1
    return (beat + 1) / (rounds + 1)


def _report_for(rec: dict):
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict
    birth = BirthData(rec["name"], rec["year"], rec["month"], rec["day"], rec["hour"],
                      rec["minute"], float(rec["tz_offset"]), float(rec["latitude"]),
                      float(rec["longitude"]))
    return to_report_dict(build_detailed_report(birth, on=tuple(rec["reference_date"])))


def _cmd_score(args) -> int:
    from app.raman_saab.feedback_instrument import instrument_key
    from app.raman_saab.feedback_scoring import (
        aggregate, binomial_p_two_sided, render_aggregate, render_aggregate_html, score_chart)

    roster = json.loads((OUT / "roster.json").read_text(encoding="utf-8"))
    by_slug = {r["slug"]: r for r in roster["admitted"]}
    cards, coin_cards, claims, coin_claims, verdicts = [], [], {}, {}, {}

    for slug, rec in sorted(by_slug.items()):
        ans_path = OUT / "answers" / f"{slug}.json"
        if not ans_path.is_file():
            print(f"[persona-study] {slug:26} no answers yet — skipped")
            continue
        doc = json.loads(ans_path.read_text(encoding="utf-8"))
        report = _report_for(rec)
        key = instrument_key(report)
        ckey = chart_key_for(rec)

        rows = _answer_rows(doc) + [(f"inst.v2.meta.context", "before_reading", None)]
        cards.append(score_chart(report, rows, chart_key=ckey))

        payload = json.loads((OUT / "payloads" / f"{slug}.json").read_text(encoding="utf-8"))
        coin = coinflip_answers(payload, seed=args.seed)
        coin_cards.append(score_chart(
            report, [(q, v, None) for q, v in coin.items()]
            + [("inst.v2.meta.context", "before_reading", None)], chart_key=ckey))

        def _claims(given: dict) -> list:
            out = []
            for qid, expected in key["answers"].items():
                meta = key["meta"].get(qid, {})
                if meta.get("kind") != "forced_choice" or qid not in given:
                    continue
                pole = _pole(meta["verdict"], given[qid] == expected)
                if pole:
                    out.append((meta["signification"], pole))
            return out

        claims[slug] = _claims(doc.get("answers") or {})
        coin_claims[slug] = _claims(coin)
        verdicts[slug] = json.loads(
            (OUT / "verdicts" / f"{slug}.json").read_text(encoding="utf-8"))["verdicts"]

    if not cards:
        print("[persona-study] no answers collected yet")
        return 1

    blind, coin = aggregate(cards), aggregate(coin_cards)
    print("\n=== SHAM GATE (PREREG 2b) — coin-flip arm ===")
    print(f"  {coin.forced.hits}/{coin.forced.n} = {coin.forced.rate}   "
          f"p={coin.forced.p_value}")
    gate_ok = coin.forced.n > 0 and coin.forced.p_value is not None \
        and coin.forced.p_value > 0.05
    print(f"  gate {'PASS — the rest may be read' if gate_ok else 'FAIL — STOP, pipeline defect'}")
    if not gate_ok:
        # Pre-registered: no other number may be read until the coin-flip arm returns chance.
        # Printing the primary anyway and trusting the operator not to look at it is not a gate.
        print("[persona-study] the sham gate did not pass — nothing further is reported")
        return 1

    print("\n=== PRIMARY — blind forced choice against own chart ===")
    print(f"  {blind.forced.hits}/{blind.forced.n} = {blind.forced.rate}   "
          f"p={blind.forced.p_value}")
    print(f"  rarity-weighted {blind.forced.weighted_rate}")
    print(f"  inverted channels (read backwards) {blind.inverted.hits}/{blind.inverted.n}")
    print(f"  confident {blind.confident.hits}/{blind.confident.n}   "
          f"unsure {blind.unsure.hits}/{blind.unsure.n}")

    cc = cross_chart(claims, verdicts)
    pperm = permutation_p(claims, verdicts, rounds=args.permutations)
    print("\n=== CONTROL — cross-chart falsification (PREREG 2a) ===")
    print(f"  matched     {cc['matched'][0]}/{cc['matched'][1]} = "
          f"{cc['matched_rate'] and round(cc['matched_rate'], 4)}")
    print(f"  mismatched  {cc['mismatched'][0]}/{cc['mismatched'][1]} = "
          f"{cc['mismatched_rate'] and round(cc['mismatched_rate'], 4)}")
    print(f"  contrast    {cc['contrast'] is not None and round(cc['contrast'], 4)}   "
          f"permutation p={pperm}")

    # The sham gate has to cover the CONTRAST too, not only the primary. The contrast is a
    # difference between two arms with different item compositions — Part C selects each
    # chart's RAREST readings, so a persona's significations are unusual for their own chart
    # and typical elsewhere — and an asymmetry there would manufacture a contrast out of an
    # answerer who knows nothing. Running the coin-flip arm through the identical machinery
    # is the only way to tell a real contrast from a biased statistic.
    cc_coin = cross_chart(coin_claims, verdicts)
    pperm_coin = permutation_p(coin_claims, verdicts, rounds=args.permutations)
    print("\n=== SHAM GATE on the CONTRAST — the same control, coin-flip answers ===")
    print(f"  matched     {cc_coin['matched'][0]}/{cc_coin['matched'][1]} = "
          f"{cc_coin['matched_rate'] and round(cc_coin['matched_rate'], 4)}")
    print(f"  mismatched  {cc_coin['mismatched'][0]}/{cc_coin['mismatched'][1]} = "
          f"{cc_coin['mismatched_rate'] and round(cc_coin['mismatched_rate'], 4)}")
    print(f"  contrast    {cc_coin['contrast'] is not None and round(cc_coin['contrast'], 4)}"
          f"   permutation p={pperm_coin}")
    contrast_gate = cc_coin["contrast"] is not None and abs(cc_coin["contrast"]) < 0.02
    print(f"  gate {'PASS — the contrast statistic is unbiased' if contrast_gate else 'FAIL — the contrast is biased; the real one cannot be read as evidence'}")

    out = {"charts": len(cards), "sham_gate_passed": gate_ok,
           "engine_git_sha": engine_git_sha(), "instrument_version": "v2",
           "coinflip": {"hits": coin.forced.hits, "n": coin.forced.n,
                        "rate": coin.forced.rate, "p": coin.forced.p_value},
           "primary": {"hits": blind.forced.hits, "n": blind.forced.n,
                       "rate": blind.forced.rate, "p": blind.forced.p_value,
                       "weighted_rate": blind.forced.weighted_rate},
           "inverted": {"hits": blind.inverted.hits, "n": blind.inverted.n},
           "confident": {"hits": blind.confident.hits, "n": blind.confident.n},
           "unsure": {"hits": blind.unsure.hits, "n": blind.unsure.n},
           "spine": {"near": blind.spine_near, "events": blind.spine_events,
                     "chance": blind.spine_chance, "p": blind.spine_p},
           "event_houses": {"top": blind.event_top_grade, "n": blind.event_scored},
           "cross_chart": cc, "permutation_p": pperm,
           "contrast_sham": {"cross_chart": cc_coin, "permutation_p": pperm_coin,
                             "passed": contrast_gate},
           "per_signification": blind.per_signification}
    (OUT / "results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    if args.html:
        Path(args.html).write_text(render_aggregate_html(blind, cards), encoding="utf-8")
        print(f"\n[persona-study] wrote {args.html}")
    (OUT / "scorecard.txt").write_text(render_aggregate(blind), encoding="utf-8")
    print(f"[persona-study] wrote {OUT / 'results.json'}")
    return 0


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Run a stage of the persona study.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster", help="resolve the pre-registered candidates through the gate")
    b = sub.add_parser("build", help="cast each nativity, emit its blind question payload")
    b.add_argument("--force", action="store_true", help="rebuild payloads that already exist")
    sub.add_parser("questions", help="render each payload as a compact blind question block")
    r = sub.add_parser("readings", help="render each reading — the contaminated arm's input")
    r.add_argument("--force", action="store_true", help="re-render readings that exist")
    sub.add_parser("verify", help="hash the collected answers BEFORE any key is computed")
    s = sub.add_parser("score", help="primary, controls, and the sham gate")
    s.add_argument("--html", default="", help="write the operator scorecard here")
    s.add_argument("--seed", default="persona-study", help="coin-flip control arm seed")
    s.add_argument("--permutations", type=int, default=2000)
    args = ap.parse_args(argv)
    return {"roster": _cmd_roster, "build": _cmd_build, "questions": _cmd_questions,
            "readings": _cmd_readings, "verify": _cmd_verify,
            "score": _cmd_score}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
