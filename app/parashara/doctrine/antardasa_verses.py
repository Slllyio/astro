"""The 81 antardasa verses — BPHS's OWN grading of every (dasa lord, antardasa lord) pair (ch.52-60).

Parashara gives each of the 81 Vimshottari pairs its own section: the conditions under which that
antardasa gives good effects, the conditions for bad ones, and lordship / maraka / remedy notes.
`antardasa_verses.json` holds all 81 sections, extracted clause by clause with the exact corpus
line and a verbatim quote for every condition (465 clauses; every quote verified against its cited
line, 2026-10-13). File chapters: 52 Sun, 53 Moon AND Mars (Mars's dasa is the printed ch.54, found
inside the ch.53 file), 55 Rahu, 56 Jupiter, 57 Saturn, 58 Mercury, 59 Ketu, 60 Venus.

`grade_pair` evaluates a pair's good and bad clauses on a chart:
  * a clause's conditions are houses (counted in the frame the verse names: from the Ascendant, from
    the dasa lord, or either), sign states of the antardasa lord (exalted, own, moolatrikona,
    friend's, enemy's, debilitated, combust), and lordship of named houses;
  * "alternatives" clauses fire on ANY listed condition, the rest only when ALL hold;
  * quality: good AND bad clauses fired -> mixed; only good -> auspicious; only bad -> adverse;
    none -> neutral.

NAMED APPROXIMATIONS (not silent): a clause whose frame the verse leaves UNSTATED is read from the
Ascendant (doctrine reviews judged it the likely sense — Parashara or the translator names "from the
lord of the Dasa" when that frame is meant). REQUIRED qualifiers ("associated with or aspected by
benefics", "endowed with strength", "weak and ...") are not yet read, so such a clause is flagged
`requires_qualifier` and counted UNEVALUATED — never fired on placement alone; an "or ..." qualifier
is an alternative path, so the checkable condition alone suffices. Clauses whose condition is on
OTHER planets placed from the dasa lord (Sun/Moon :129, Moon/Mars :119) are unevaluated likewise.
Nodes have no ch.3 exaltation, so dignity clauses on Rahu/Ketu antardasas can never fire. OCR-lost
houses were left out; ONE OCR reading was corrected and flagged `ocr_uncertain` — Mars/Jupiter
(ch.53 file :738) prints "5th, 8th or 12th", recorded as 6/8/12 (the 5th contradicts its own good
clause). Data fixes from the 2026-10-13 doctrine review (REVISE) are applied in the JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.combustion import is_combust
from app.parashara.primitives.relationships import (
    EXALTATION, MOOLATRIKONA, SIGN_LORDS, naisargika)

_DATA: Final[Path] = Path(__file__).with_name("antardasa_verses.json")


@dataclass(frozen=True)
class FiredClause:
    """One verse condition that holds in the chart."""
    kind: str            # "good" | "bad"
    effects: str         # the verse's effects, paraphrased
    source: Citation     # the exact corpus line


@dataclass(frozen=True)
class PairGrade:
    """A pair's quality by its own verse, with the clauses that fired and those left unevaluated."""
    quality: str                      # auspicious | mixed | neutral | adverse
    fired: tuple[FiredClause, ...]
    evaluable: int                    # good/bad clauses with a checkable condition
    unevaluated: int                  # clauses needing a qualifier this engine does not yet read


@lru_cache(maxsize=1)
def verses() -> Mapping[tuple[str, str], dict[str, Any]]:
    """(dasa lord, antardasa lord) -> its extracted BPHS section."""
    return {(s["md"], s["ad"]): s for s in json.loads(_DATA.read_text(encoding="utf-8"))}


def all_citations() -> tuple[Citation, ...]:
    """Every clause citation in the 81-pair table — registered with the source lock, so a corpus
    edit that moves these lines fails loudly instead of silently mis-citing."""
    return tuple(Citation(f"BPHS-{s['chapter']}", int(c["line"]))
                 for s in verses().values()
                 for kind in ("good", "bad", "mixed_or_other") for c in s.get(kind, ()))


def _sign_states(planet: str, sign: int, longitudes: Mapping[str, float],
                 speeds: Mapping[str, float]) -> set[str]:
    states: set[str] = set()
    if planet in EXALTATION:
        if sign == EXALTATION[planet]:
            states.add("exalted")
        if sign == ((EXALTATION[planet] - 1 + 6) % 12) + 1:
            states.add("debilitated")
        lord = SIGN_LORDS[sign]
        if lord == planet:
            states.add("own")
        elif lord in MOOLATRIKONA:
            rel = naisargika(planet, lord)
            if rel == "mitra":
                states.add("friend")
            elif rel == "shatru":
                states.add("enemy")
    if MOOLATRIKONA.get(planet) == sign:
        states.add("moolatrikona")
    if "Sun" in longitudes and planet in longitudes and is_combust(
            planet, longitudes[planet], longitudes["Sun"],
            retrograde=speeds.get(planet, 0.0) < 0.0):
        states.add("combust")
    return states


@dataclass(frozen=True)
class QualifierContext:
    """What the commonest required qualifiers need about the antardasa lord. "Associated with" =
    CONJUNCTION and "aspected by" = graha-drishti are kept apart: the verses themselves say
    "associated with OR aspected by" when they mean either (review 2026-10-13)."""
    benefic_conj: bool        # shares a sign with a (functional-nature) benefic
    benefic_asp: bool         # receives a benefic's graha-drishti
    malefic_conj: bool
    malefic_asp: bool
    strong: Optional[bool]    # Shadbala vs BPHS's required minimum (None = unknown, e.g. a node)


#: Words meaning "lacking" — any of these before "strength" means WEAK (never strong).
_LACKING = ("without", "devoid", "bereft", "deprived", "lacking", "not ")


def _qualifier_holds(q: str, ctx: QualifierContext) -> Optional[bool]:
    """True/False for a recognised required qualifier; None if it is too complex to read yet.

    One category per qualifier: benefic/malefic CONTACT, read by its stated mode — "associated with"
    / "in (conjunction|association) with" = conjunction, "aspected by" = drishti, "associated with
    or aspected by" = either; STRENGTH ("endowed with strength"); WEAKNESS ("weak", or any lacking-
    word + strength). Refused (None, stays unevaluated): any extra "and" requirement, any "or"
    alternative, navamsa / varga / named lords / yogakarakas / named planets, mixed natures.
    """
    t = " ".join(q.lower().replace("(conjunctive)", "").split()).strip(" .;,")
    for lead in ("and be ", "and ", "be "):
        if t.startswith(lead):
            t = t[len(lead):]
    either = False
    for phrase in ("associated with or aspected by", "aspected by or associated with"):
        if phrase in t:
            t, either = t.replace(phrase, "contact-either"), True
    if t.startswith("or ") or " or " in t or " and " in t:
        return None                                   # alternatives / extra conjuncts: not read
    if any(w in t for w in ("navamsa", "varga", "lord", "yogakaraka", "saturn", "mars", "rahu",
                            "ketu", "jupiter", "venus", "mercury", "moon", "sun", "evil")):
        return None
    has_b, has_m = "benefic" in t, "malefic" in t
    if has_b != has_m:                                # exactly one nature named
        conj = either or "associated with" in t or "association with" in t or "conjunction with" in t
        asp = either or "aspected by" in t
        if not (conj or asp) or any(w in t for w in _LACKING):
            return None
        c, a = ((ctx.benefic_conj, ctx.benefic_asp) if has_b
                else (ctx.malefic_conj, ctx.malefic_asp))
        return (conj and c) or (asp and a)
    if not has_b and not has_m:
        weak = t.startswith("weak") or " weak" in t or (
            "strength" in t and any(w in t for w in _LACKING))
        if weak:
            return None if ctx.strong is None else not ctx.strong
        if "strength" in t:
            return ctx.strong
    return None


def _clause_holds(c: dict[str, Any], h_lagna: int, h_md: int, states: set[str],
                  owned: set[int], sign: int,
                  ctx: Optional[QualifierContext] = None) -> Optional[bool]:
    """True/False if the clause's conditions hold; None if it cannot be checked.

    A clause flagged `requires_qualifier` names a REQUIRED condition this engine does not yet read
    ("and be endowed with strength", "associated with benefics", ...): it is UNEVALUATED, never fired
    on placement alone (doctrine review 2026-10-13 — firing them biased windows ~2.5:1 auspicious).
    An `unconditional` clause states the antardasa's general result with no condition: it always holds.
    """
    if c.get("unconditional"):
        return True
    if c.get("requires_qualifier"):
        qual = _qualifier_holds(c.get("qualifier") or "", ctx) if ctx is not None else None
        if qual is None:
            return None
        if not qual:
            return False
        # the required qualifier holds: the clause's placement conditions (if any) must hold too
        rest = {k: v for k, v in c.items() if k not in ("requires_qualifier", "qualifier")}
        if not (rest.get("houses") or rest.get("dignity") or rest.get("lord_of") or rest.get("signs")):
            return True
        return _clause_holds(rest, h_lagna, h_md, states, owned, sign, ctx)
    checks: list[bool] = []
    named_signs = set(c.get("signs") or ())
    if named_signs and c.get("signs_mode") == "or":
        checks.append(sign in named_signs)        # an alternative path, OR-ed below
    elif named_signs:
        if sign not in named_signs:               # a required sign condition (AND)
            return False
    houses = set(c.get("houses") or ())
    if houses:
        frame = c.get("frame", "unstated")
        if frame == "md_lord":
            checks.append(h_md in houses)
        elif frame == "lagna_or_md_lord":
            checks.append(h_lagna in houses or h_md in houses)
        else:                                       # "lagna" or "unstated" (read from the Ascendant)
            checks.append(h_lagna in houses)
    dignity = set(c.get("dignity") or ())
    if dignity:
        checks.append(bool(dignity & states))
    lord_of = set(c.get("lord_of") or ())
    if lord_of:
        checks.append(bool(lord_of & owned))
    if not checks:
        return True if named_signs else None
    if named_signs and c.get("signs_mode") == "or":
        return any(checks)
    return any(checks) if c.get("alternatives") else all(checks)


def grade_pair(md: str, ad: str, *, asc_sign: int, signs: Mapping[str, int],
               longitudes: Mapping[str, float], speeds: Mapping[str, float] | None = None,
               ctx: Optional[QualifierContext] = None) -> Optional[PairGrade]:
    """The pair's quality by its own BPHS verse, or None if the pair has no evaluable clause.
    `ctx` lets the commonest required qualifiers (benefic/malefic contact, strength) be read."""
    section = verses().get((md, ad))
    if section is None or ad not in signs or md not in signs:
        return None
    speeds = speeds or {}
    h_lagna = ((signs[ad] - asc_sign) % 12) + 1
    h_md = ((signs[ad] - signs[md]) % 12) + 1
    states = _sign_states(ad, signs[ad], longitudes, speeds)
    owned = {h for h in range(1, 13) if SIGN_LORDS[((asc_sign - 1 + h - 1) % 12) + 1] == ad}
    fired: list[FiredClause] = []
    evaluable = unevaluated = 0
    for kind in ("good", "bad"):
        for c in section.get(kind, ()):
            holds = _clause_holds(c, h_lagna, h_md, states, owned, signs[ad], ctx)
            if holds is None:
                unevaluated += 1
                continue
            evaluable += 1
            if holds:
                fired.append(FiredClause(kind, c.get("effects", ""),
                                         Citation(f"BPHS-{section['chapter']}", int(c["line"]))))
    if evaluable == 0:
        return None
    good = any(f.kind == "good" for f in fired)
    bad = any(f.kind == "bad" for f in fired)
    quality = ("mixed" if good and bad else "auspicious" if good
               else "adverse" if bad else "neutral")
    return PairGrade(quality=quality, fired=tuple(fired), evaluable=evaluable,
                     unevaluated=unevaluated)
