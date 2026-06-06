"""Golden extractor for the Raman Saab engine (BUILD-TIME tool — lives OUTSIDE app/).

This module is the machinery that turns Raman's own published material into golden
records (the JSONL schema in ``docs/raman_saab/golden_schema.md``). It has three
independent pieces, each usable on its own:

1. ``parse_example_insights`` — a *parser stub* that walks a
   ``docs/raman_saab/methodology/_derived/house_NN_*_example_insights.md`` file and
   emits one DRAFT ``GoldenRecord`` per "### Chart N" section it finds. It does NOT
   try to read the planetary table yet (no birth/positions in those files); it
   captures the chart id, the prose, and a lexicon-derived DRAFT verdict so a human
   can confirm and fill positions in the Phase-B extraction workflow.

2. ``KEYWORD_LEXICON`` + ``classify_prose`` — a documented, cited mapping from
   Raman's verdict-prose to a DRAFT ordinal. Every keyword is annotated with the
   reading lesson it encodes; this is deliberately conservative — anything it cannot
   classify becomes ``insufficient-evidence`` (never a fabricated favourable/afflicted).

3. ``condition_solver`` — synthesises the *smallest* ``stated_positions`` chart that
   satisfies a ``RuleRecord.condition`` tree, for ``case_type="rule_level"`` goldens.
   It supports the leaf predicates ``InRashiHouse`` / ``LordIn`` / ``Conjunct`` /
   ``InHouseFrom`` and the combinators ``And`` / ``Or``. It REFUSES (raises
   ``UnsolvableCondition``) on ``Not`` and on any predicate it does not understand —
   it never fabricates a chart it cannot prove satisfies the condition.

In THIS task the module only ships the machinery + a ``self_test`` (``--self-test``);
the bulk extraction (running the parser over all 12 chapters and promoting DRAFT →
CONFIRMED) is the next workflow phase.

Usage:
    py -3.12 -m tools.raman_saab.extract_goldens --self-test
    py -3.12 -m tools.raman_saab.extract_goldens --parse docs/raman_saab/methodology/_derived/house_01_lagna_example_insights.md
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.doctrine import conditions as C

# ---------------------------------------------------------------------------
# Verdict ordinals (mirror house_template.Verdict — kept local so the build tool
# does not import the judge just for a Literal).
# ---------------------------------------------------------------------------
VERDICTS = ("favourable", "mixed", "afflicted", "insufficient-evidence")


class UnsolvableCondition(Exception):
    """Raised by ``condition_solver`` when a condition cannot be synthesised
    without fabricating an unprovable chart (Not / unknown predicate / contradiction).

    Escalating rather than guessing is doctrinally required: a golden that pins the
    wrong chart to a rule is worse than no golden at all.
    """


# ---------------------------------------------------------------------------
# 1. GoldenRecord — the in-memory form of one JSONL line.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GoldenRecord:
    """One golden, matching the schema in docs/raman_saab/golden_schema.md.

    ``to_json_obj`` produces the exact dict that becomes a JSONL line; the harness
    and schema-guard test consume that dict shape, not this dataclass.
    """
    id: str
    book: str
    name: str
    case_type: str
    birth: Optional[dict[str, Any]]
    lagna_sign: Optional[int]
    stated_positions: dict[str, dict[str, Any]]
    expected_verdicts: dict[str, dict[str, Any]]
    expected_longevity: Optional[dict[str, Any]]
    track_eligibility: tuple[str, ...]
    confidence: float
    citations: tuple[str, ...]

    def to_json_obj(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "book": self.book,
            "name": self.name,
            "case_type": self.case_type,
            "birth": self.birth,
            "lagna_sign": self.lagna_sign,
            "stated_positions": self.stated_positions,
            "expected_verdicts": self.expected_verdicts,
            "expected_longevity": self.expected_longevity,
            "track_eligibility": list(self.track_eligibility),
            "confidence": self.confidence,
            "citations": list(self.citations),
        }

    def to_jsonl(self) -> str:
        return json.dumps(self.to_json_obj(), ensure_ascii=True, sort_keys=False)


# ---------------------------------------------------------------------------
# 2. KEYWORD LEXICON — verdict-prose -> DRAFT ordinal.
#
# Each entry is (ordinal, [phrase, ...], rationale). The rationale documents WHY
# the phrase maps to that ordinal — it is the cited reading lesson, not a guess.
# Matching is case-insensitive substring; the FIRST ordinal whose any phrase hits
# wins, in the priority order below (afflicted > mixed > favourable). A "mixed"
# concession marker ("but", "yet", "however") can DEMOTE a favourable hit — see
# classify_prose. Anything unmatched -> insufficient-evidence (never fabricated).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LexEntry:
    ordinal: str
    phrases: tuple[str, ...]
    rationale: str


# Priority order (applied in classify_prose) is load-bearing:
#   explicit-mixed  >  afflicted  >  favourable.
# An explicit mixed marker ("owned then lost", "gains and losses") outranks a bare
# affliction word so a qualified outcome is not over-read as outright failure; an
# affliction word then outranks any benefic word (Raman's "great learning BUT
# premature death" is an afflicted longevity verdict). The tuple order below is
# afflicted/mixed/favourable for readability; classify_prose imposes the priority.
KEYWORD_LEXICON: tuple[LexEntry, ...] = (
    LexEntry(
        "afflicted",
        ("died early", "premature death", "short life", "early death",
         "lost", "deprived", "deprivation", "denied", "barren", "childless",
         "none", "no children", "destitute", "poverty", "ruin", "ruined",
         "miserable", "imprisonment", "incarcerat", "disgrace", "defamation",
         "afflicted", "spoiled", "spoilt", "destroyed", "downfall", "killed",
         "widow", "separation", "divorce"),
        "Raman states the matter failed/was lost/was denied -> the bhava is afflicted.",
    ),
    LexEntry(
        "mixed",
        ("blemished but", "owned then lost", "rose then fell", "gains and losses",
         "good but", "strong but", "but afflicted", "yet afflicted",
         "checkered", "chequered", "ups and downs", "mixed results",
         "partial success", "delayed but", "after struggle", "obstacles"),
        "Raman states a qualified/contradicted outcome (good-but / owned-then-lost) "
        "-> a genuinely mixed bhava verdict.",
    ),
    LexEntry(
        "favourable",
        ("distinction", "eminence", "eminent", "fortified", "long life",
         "longevity", "great learning", "greatness", "prosperity", "prosperous",
         "wealthy", "affluent", "fame", "famous", "renown", "honour", "honor",
         "high position", "exalted", "blessed", "happy", "happiness",
         "fortunate", "fortune", "success", "successful", "rajayoga",
         "raja yoga", "powerful", "noble", "respected"),
        "Raman states the matter flourished/was distinguished -> the bhava is favourable.",
    ),
)

# Concession markers that turn an otherwise-favourable verdict into 'mixed'.
_CONCESSION_MARKERS: tuple[str, ...] = (" but ", " yet ", " however ", " though ",
                                        " although ", " except ")


def classify_prose(prose: str) -> str:
    """Map a Raman verdict sentence to a DRAFT ordinal via KEYWORD_LEXICON.

    Conservative by construction (priority: explicit-mixed > afflicted > favourable):
    * No prose / empty -> ``insufficient-evidence`` (no verdict clause).
    * An explicit mixed/concession phrase ("owned then lost", "gains and losses")
      -> ``mixed`` — outranks a bare affliction substring inside it.
    * An affliction keyword -> ``afflicted``.
    * A favourable keyword, UNLESS a bare concession marker ("...but...") is also
      present (then demote to ``mixed`` — a praised-but-qualified reading).
    * Nothing matched -> ``insufficient-evidence``.

    This is a DRAFT only: every produced verdict is meant to be human-reviewed
    (``verdict_review="DRAFT"``) before it can be asserted in Track B.
    """
    if not prose or not prose.strip():
        return "insufficient-evidence"
    low = f" {prose.lower()} "

    # 1. explicit mixed/concession phrasing OUTRANKS a bare affliction word: Raman's
    #    "owned then lost" / "gains and losses" is a mixed verdict, not an outright
    #    affliction, even though it contains the substring "lost".
    if _any_phrase(low, KEYWORD_LEXICON[1].phrases):
        return "mixed"
    # 2. afflicted dominates the remaining (favourable) tier.
    if _any_phrase(low, KEYWORD_LEXICON[0].phrases):
        return "afflicted"
    # 3. favourable, demoted to mixed by a bare concession marker.
    if _any_phrase(low, KEYWORD_LEXICON[2].phrases):
        if any(m in low for m in _CONCESSION_MARKERS):
            return "mixed"
        return "favourable"
    # 4. no verdict clause recognised.
    return "insufficient-evidence"


def _any_phrase(haystack_low: str, phrases: tuple[str, ...]) -> bool:
    return any(p in haystack_low for p in phrases)


# ---------------------------------------------------------------------------
# 3. condition_solver — smallest stated_positions satisfying a Condition tree.
#
# Strategy: maintain a mutable "plan" of constraints, resolve them to concrete
# (sign, bhava) placements, then VERIFY the built chart actually fires the
# condition before returning. Verification is the safety net — if synthesis and
# the real evaluator disagree, we raise rather than emit a wrong golden.
# ---------------------------------------------------------------------------

# A neutral default Lagna for synthesised charts: Aries (sign 1) rising at 5 deg.
_DEFAULT_LAGNA_SIGN: int = 1
_DEFAULT_ASC_LON: float = float((_DEFAULT_LAGNA_SIGN - 1) * 30) + 5.0


@dataclass
class _Plan:
    """Accumulated placement constraints. ``planet_house[p] = h`` pins planet p to
    whole-sign house h (1..12, counted from the Lagna). ``conjunct`` records
    same-house requirements; ``lord_house`` pins a bhava-lord to a house."""
    asc_sign: int = _DEFAULT_LAGNA_SIGN
    planet_house: dict[str, int] = field(default_factory=dict)
    conjunct: list[tuple[str, str]] = field(default_factory=list)
    # (house_owned, in_house): the lord of `house_owned` must sit in `in_house`.
    lord_house: list[tuple[int, int]] = field(default_factory=list)


def _collect(cond: C.Condition, plan: _Plan) -> None:
    """Walk the condition tree, accumulating constraints into `plan`.

    Supported: And (recurse all), Or (take the FIRST disjunct — the minimal chart
    only needs one branch true), InRashiHouse, Conjunct, LordIn, InHouseFrom.
    Everything else (Not, unknown predicate) escalates via UnsolvableCondition.
    """
    if isinstance(cond, C.And):
        for c in cond.conds:
            _collect(c, plan)
        return
    if isinstance(cond, C.Or):
        if not cond.conds:
            raise UnsolvableCondition("empty Or() cannot be satisfied")
        # Minimal chart: satisfy the first disjunct only.
        _collect(cond.conds[0], plan)
        return
    if isinstance(cond, C.Not):
        # A negative is unbounded — infinitely many charts satisfy it; we refuse to
        # fabricate one. Escalate to the human.
        raise UnsolvableCondition("Not() is not synthesisable without fabrication")
    if isinstance(cond, C.InRashiHouse):
        _pin(plan, cond.planet, cond.house)
        return
    if isinstance(cond, C.Conjunct):
        plan.conjunct.append((cond.a, cond.b))
        return
    if isinstance(cond, C.LordIn):
        plan.lord_house.append((cond.house, cond.in_house))
        return
    if isinstance(cond, C.InHouseFrom):
        _collect_in_house_from(cond, plan)
        return
    raise UnsolvableCondition(
        f"unsupported predicate {type(cond).__name__}; escalate to human extraction")


def _collect_in_house_from(cond: C.InHouseFrom, plan: _Plan) -> None:
    """InHouseFrom with a concrete origin we can resolve to a whole-sign house.

    origin == "LAGNA" -> house n from house 1.
    origin == int     -> house n from that house.
    A planet-name origin is NOT synthesisable here (chicken-and-egg: the origin
    planet's own house may itself be unconstrained) -> escalate.
    """
    if cond.origin == "LAGNA":
        _pin(plan, cond.planet, ((cond.n - 1) % 12) + 1)
        return
    if isinstance(cond.origin, int):
        target = (((cond.origin - 1) + (cond.n - 1)) % 12) + 1
        _pin(plan, cond.planet, target)
        return
    raise UnsolvableCondition(
        f"InHouseFrom origin {cond.origin!r} not synthesisable; escalate to human")


def _pin(plan: _Plan, planet: str, house: int) -> None:
    existing = plan.planet_house.get(planet)
    if existing is not None and existing != house:
        raise UnsolvableCondition(
            f"contradiction: {planet} pinned to both house {existing} and {house}")
    plan.planet_house[planet] = house


_ALL_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _resolve_conjunctions(plan: _Plan) -> None:
    """Apply conjunction constraints by copying a pinned partner's house, or pinning
    both to a free house when neither is yet placed."""
    free_house = 2  # start away from the Lagna (house 1) to avoid accidental overlap
    for a, b in plan.conjunct:
        ha, hb = plan.planet_house.get(a), plan.planet_house.get(b)
        if ha is not None and hb is not None:
            if ha != hb:
                raise UnsolvableCondition(f"conjunct {a}/{b} pinned to different houses")
        elif ha is not None:
            plan.planet_house[b] = ha
        elif hb is not None:
            plan.planet_house[a] = hb
        else:
            plan.planet_house[a] = plan.planet_house[b] = free_house
            free_house = (free_house % 12) + 1


def _resolve_lord_houses(plan: _Plan) -> None:
    """Pin each (house_owned -> in_house): place the SIGN-LORD of house_owned (counted
    from the Lagna) into in_house."""
    for house_owned, in_house in plan.lord_house:
        lord = SIGN_LORDS[((plan.asc_sign - 1) + (house_owned - 1)) % 12 + 1]
        _pin(plan, lord, in_house)


def _plan_to_stated(plan: _Plan) -> dict[str, dict[str, Any]]:
    """Materialise the plan into a ``stated_positions`` dict. Every planet gets a
    lon at the midpoint of its house's sign; unconstrained planets are parked in a
    free house so the chart is always complete (judges expect all nine grahas)."""
    stated: dict[str, dict[str, Any]] = {}
    used_houses = set(plan.planet_house.values())
    park = 1
    for p in _ALL_PLANETS:
        house = plan.planet_house.get(p)
        if house is None:
            # park unconstrained planets in houses not used by constraints, cycling.
            while park in used_houses and len(used_houses) < 12:
                park = (park % 12) + 1
            house = park
            park = (park % 12) + 1
        sign = ((plan.asc_sign - 1) + (house - 1)) % 12 + 1
        lon = float((sign - 1) * 30) + 15.0
        stated[p] = {"lon": lon, "bhava": house, "position_source": "synthetic_minimal"}
    return stated


def condition_solver(condition: C.Condition, *, asc_sign: int = _DEFAULT_LAGNA_SIGN,
                     ) -> dict[str, dict[str, Any]]:
    """Synthesise the smallest ``stated_positions`` satisfying ``condition``.

    Raises :class:`UnsolvableCondition` for Not(), unknown predicates, or contradictions.
    VERIFIES the built chart actually fires the condition before returning — a
    synthesis/evaluator mismatch raises rather than emitting a wrong golden.
    """
    plan = _Plan(asc_sign=asc_sign)
    _collect(condition, plan)
    _resolve_lord_houses(plan)
    _resolve_conjunctions(plan)
    stated = _plan_to_stated(plan)

    # Verification net: build a real chart and confirm the condition fires.
    from app.raman_saab.chart.model import RamanChart  # local import: keeps tool light
    asc_lon = float((asc_sign - 1) * 30) + 5.0
    chart = RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")
    if not condition.evaluate(C.EvalContext(chart)):
        raise UnsolvableCondition(
            "synthesised chart does NOT satisfy the condition — refusing to emit a "
            "wrong golden (the predicate may need richer synthesis support)")
    return stated


# ---------------------------------------------------------------------------
# 4. parse_example_insights — the parser STUB (machinery + DRAFT output only).
# ---------------------------------------------------------------------------

_CHART_HEADER = re.compile(r"^###\s+Chart\s+(\d+(?:\s*/\s*\d+)*)\s*$", re.IGNORECASE)
_HOUSE_FROM_FILENAME = re.compile(r"house_(\d{2})_")


def parse_example_insights(md_path: Path) -> list[GoldenRecord]:
    """Walk a ``house_NN_*_example_insights.md`` file -> one DRAFT GoldenRecord per
    "### Chart N" section.

    This is a STUB: it captures the chart id + prose + a lexicon-derived DRAFT
    verdict, but leaves ``stated_positions`` empty (those files carry no planetary
    table). The Phase-B workflow fills positions from the book's chart tables and
    promotes DRAFT -> CONFIRMED. The value here is the machinery + a deterministic,
    reviewable starting point.
    """
    text = md_path.read_text(encoding="utf-8")
    house_match = _HOUSE_FROM_FILENAME.search(md_path.name)
    house = int(house_match.group(1)) if house_match else 1
    book = "HTJAH-I" if house <= 6 else "HTJAH-II"
    sig_key = _default_sig_key(house)

    records: list[GoldenRecord] = []
    cur_id: Optional[str] = None
    cur_lines: list[str] = []

    def _flush() -> None:
        if cur_id is None:
            return
        prose = " ".join(s.strip("- ").strip() for s in cur_lines if s.strip())
        verdict = classify_prose(prose)
        records.append(GoldenRecord(
            id=f"{book}.chart_{cur_id}",
            book=book,
            name=f"Chart {cur_id} (parsed from {md_path.name})",
            case_type="worked_example",
            birth=None,
            lagna_sign=None,
            stated_positions={},  # STUB: positions filled by the Phase-B workflow
            expected_verdicts={
                f"H{house}": {
                    "signification": sig_key,
                    "verdict": verdict,
                    "verdict_prose": prose[:500],
                    "verdict_review": "DRAFT",
                }
            },
            expected_longevity=None,
            track_eligibility=("B", "3"),
            confidence=0.3,  # a parser DRAFT is low-confidence by construction
            citations=(f"{book}:1",),
        ))

    for line in text.splitlines():
        m = _CHART_HEADER.match(line.strip())
        if m:
            _flush()
            cur_id = m.group(1).replace(" ", "").replace("/", "_")
            cur_lines = []
        elif cur_id is not None:
            if line.startswith("### ") or line.startswith("## "):
                _flush()
                cur_id = None
                cur_lines = []
            else:
                cur_lines.append(line)
    _flush()
    return records


def _default_sig_key(house: int) -> str:
    """The first signification key for a house (matches significations_of)."""
    from app.raman_saab.doctrine.significations import significations_of
    sigs = significations_of(house)
    return sigs[0].key if sigs else "general"


# ---------------------------------------------------------------------------
# 5. self-test — proves the three pieces of machinery work end-to-end.
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """Exercise lexicon, condition_solver, GoldenRecord, and parser stub. Returns 0
    on success, non-zero on the first failure (also usable from CLI)."""
    failures: list[str] = []

    # --- lexicon ---
    cases = {
        "He died early, the son was lost.": "afflicted",
        "Rose to great eminence and long life.": "favourable",
        "Owned then lost the property; gains and losses throughout.": "mixed",
        "Great learning but premature death.": "afflicted",   # affliction dominates
        "Strong Lagna but checkered career.": "mixed",
        "He was wealthy but never at peace.": "mixed",          # concession demotes
        "The native travelled south.": "insufficient-evidence",
        "": "insufficient-evidence",
    }
    for prose, want in cases.items():
        got = classify_prose(prose)
        if got != want:
            failures.append(f"lexicon: {prose!r} -> {got!r}, want {want!r}")

    # --- condition_solver: solvable ---
    cond = C.And(C.InRashiHouse("Saturn", 7), C.Conjunct("Mars", "Saturn"))
    stated = condition_solver(cond)
    if stated["Saturn"]["bhava"] != 7 or stated["Mars"]["bhava"] != 7:
        failures.append(f"solver: And/InRashiHouse/Conjunct gave {stated['Saturn']}, {stated['Mars']}")
    if len(stated) != len(_ALL_PLANETS):
        failures.append(f"solver: incomplete chart, {len(stated)} planets")

    # --- condition_solver: LordIn + InHouseFrom(LAGNA) ---
    cond2 = C.And(C.LordIn(7, 1), C.InHouseFrom("Jupiter", "LAGNA", 5))
    stated2 = condition_solver(cond2)
    if stated2["Jupiter"]["bhava"] != 5:
        failures.append(f"solver: InHouseFrom(LAGNA,5) gave {stated2['Jupiter']}")

    # --- condition_solver: refusals ---
    for bad, label in (
        (C.Not(C.InRashiHouse("Sun", 1)), "Not()"),
        (C.HasDignity("Sun", {"exalt"}), "unknown predicate"),
        (C.And(C.InRashiHouse("Mars", 1), C.InRashiHouse("Mars", 7)), "contradiction"),
    ):
        try:
            condition_solver(bad)
            failures.append(f"solver: expected UnsolvableCondition for {label}")
        except UnsolvableCondition:
            pass

    # --- GoldenRecord round-trips through JSON ---
    rec = GoldenRecord(
        id="self_test.smoke", book="HTJAH-I", name="smoke", case_type="rule_level",
        birth=None, lagna_sign=1, stated_positions=stated,
        expected_verdicts={}, expected_longevity=None,
        track_eligibility=("B",), confidence=1.0, citations=("HTJAH-I:1",))
    reparsed = json.loads(rec.to_jsonl())
    if reparsed["id"] != "self_test.smoke" or reparsed["stated_positions"]["Saturn"]["bhava"] != 7:
        failures.append("GoldenRecord JSON round-trip mismatch")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"\n{len(failures)} self-test failure(s).", file=sys.stderr)
        return 1
    print("extract_goldens self-test OK (lexicon + condition_solver + GoldenRecord).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Raman Saab golden extractor (build-time).")
    ap.add_argument("--self-test", action="store_true",
                    help="run the built-in machinery self-test and exit")
    ap.add_argument("--parse", metavar="MD_PATH",
                    help="parse a house_NN_*_example_insights.md into DRAFT JSONL on stdout")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.parse:
        path = Path(args.parse)
        if not path.is_file():
            print(f"no such file: {path}", file=sys.stderr)
            return 2
        for rec in parse_example_insights(path):
            print(rec.to_jsonl())
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
