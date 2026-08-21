"""Scoring the feedback instrument — how well is the engine actually doing?

`feedback_instrument.py` asks the questions; this module answers the question the questions
exist for. It takes what a reader selected, rebuilds what the engine said about the same
matters, and compares them CODE AGAINST CODE — the instrument's option vocabularies are the
engine's own (HPA-29's body regions, HTJAH-II's trade families, the four H10 work modes), which
is what makes this a measurement rather than a reading of somebody's prose.

Four independent measurements, never averaged into one number:

  * FORCED CHOICE (Part C) — the only one with a clean null. Each item pairs the chart's own
    reading with its exact inverse, so a reader who knows nothing scores 0.5. Reported as hits
    of n with an exact two-sided binomial p, plus a rarity-weighted variant: an item only 4% of
    the population shares is worth more than one 45% share it.
  * INVERTED CHANNELS — scored SEPARATELY and read backwards. These sit on channels the
    astrobank atlas proved run the wrong way, so agreement there is evidence the reader is
    agreeing with whatever is put in front of them, and pooling them with the rest would
    launder acquiescence into accuracy.
  * LIFE FACTS (Part A) — each answer against the engine's own verdict for the same matter.
    No null hypothesis: a reader's marriage really is happy or not, and the base rates are
    unknown, so these are reported as hit/miss counts per matter and NOT as a p-value.
  * THE DATED SPINE — turning points the reader dated before reading, against the Mahadasha
    boundaries. This one has a computable chance rate, and it is computed from the actual
    union of tolerance windows over the actual span rather than assumed, because the recent
    period changes cluster and a naive rate flatters the method badly.

Part D is not scored at all — it is counted. "Which chapters got me wrong" aggregated across
readers is a work list, not a measurement.

Usage:
    from app.raman_saab.feedback_scoring import score_chart, aggregate, parse_chart_key

    card = score_chart(report_dict, rows)          # rows: (question_id, answer, free_text)
    agg  = aggregate([card, ...])                  # across charts: what carries signal
    birth = parse_chart_key("1990-07-15T12:00+5.50@12.9700,77.5900")

    python -m app.raman_saab.feedback_scoring --database-url sqlite+aiosqlite:///./app.db
    python -m app.raman_saab.feedback_scoring --chart-key "1990-07-15T12:00+5.50@..." --json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import re
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterable, Optional, Sequence

from app.raman_saab.chart.model import BirthData
from app.raman_saab.feedback_instrument import (
    BODY_REGIONS, EVENT_HOUSE, EVENT_VALENCE, TRADE_FAMILIES, build_feedback_instrument,
    instrument_key)

logger = logging.getLogger(__name__)

#: Months either side of a Mahadasha boundary that count as "near" it. Three, not six: the
#: period changes cluster, and at six months the windows swallow a quarter of a testable life
#: and the test half-passes itself. The chance rate below is computed from the actual union of
#: windows over the actual span, so widening this is visible in the null rather than free.
SPINE_TOLERANCE_MONTHS = 3

#: How a prose body-region string from HPA-29's table maps onto the closed vocabulary the
#: reader chose from. Keyword match, longest first, so "cervical vertebrae" reaches throat_neck
#: rather than back_spine. Anything unmatched contributes to neither side of the comparison and
#: is counted as unmapped, so a table change shows up as coverage loss instead of a silent miss.
_REGION_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("cervical", "throat_neck"), ("larynx", "throat_neck"), ("thyroid", "throat_neck"),
    ("throat", "throat_neck"), ("neck", "throat_neck"), ("oesophagus", "throat_neck"),
    ("tonsil", "throat_neck"),
    ("lower jaw", "teeth_jaw"), ("jaw", "teeth_jaw"), ("teeth", "teeth_jaw"),
    ("brain", "head"), ("head", "head"), ("cerebral", "head"), ("skull", "head"),
    ("eye", "eyes"), ("vision", "eyes"),
    ("ear", "ears"),
    ("lung", "chest_lungs"), ("bronch", "chest_lungs"), ("chest", "chest_lungs"),
    ("breath", "chest_lungs"), ("pleur", "chest_lungs"), ("thorax", "chest_lungs"),
    ("heart", "heart"), ("circulation", "heart"), ("blood pressure", "heart"),
    ("arter", "heart"),
    ("stomach", "stomach"), ("abdomen", "stomach"), ("bowel", "stomach"),
    ("alimentary", "stomach"), ("duoden", "stomach"), ("intestin", "stomach"),
    ("digest", "stomach"), ("anus", "stomach"), ("rectum", "stomach"), ("tongue", "stomach"),
    ("liver", "liver"), ("bile", "liver"), ("gall", "liver"), ("spleen", "liver"),
    ("kidney", "kidney_urinary"), ("bladder", "kidney_urinary"), ("urin", "kidney_urinary"),
    ("ureter", "kidney_urinary"),
    ("generative", "reproductive"), ("ovar", "reproductive"), ("uter", "reproductive"),
    ("semen", "reproductive"), ("genito", "reproductive"), ("privates", "reproductive"),
    ("skin", "skin"), ("cutaneous", "skin"), ("hair", "skin"),
    ("knee", "joints"), ("joint", "joints"), ("arthrit", "joints"), ("ankle", "joints"),
    ("spine", "back_spine"), ("back", "back_spine"), ("vertebra", "back_spine"),
    ("nerve", "nerves"), ("neuro", "nerves"), ("brain and nervous", "nerves"),
    ("marrow", "nerves"),
    ("sugar", "blood_sugar"), ("pancrea", "blood_sugar"), ("metabol", "blood_sugar"),
    ("phlegm", "chest_lungs"), ("muscular", "joints"),
    ("foot", "legs_feet"), ("feet", "legs_feet"), ("leg", "legs_feet"),
    ("phalange", "legs_feet"), ("carpus", "joints"), ("meta-tars", "legs_feet"),
    ("meta-carp", "joints"), ("shin", "legs_feet"), ("calf", "legs_feet"),
    ("thigh", "legs_feet"), ("hip", "legs_feet"),
)

#: The same idea for Raman's vocation words -> the closed trade families.
_TRADE_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("metal", "metals_machinery"), ("mineral", "metals_machinery"),
    ("machin", "metals_machinery"), ("engineer", "metals_machinery"),
    ("building", "construction"), ("construct", "construction"), ("mason", "construction"),
    ("architect", "construction"),
    ("fire-trade", "fire_heat"), ("fire", "fire_heat"), ("chemical", "fire_heat"),
    ("military", "military_police"), ("police", "military_police"), ("army", "military_police"),
    ("surgery", "medicine_surgery"), ("surgeon", "medicine_surgery"),
    ("chemist", "medicine_surgery"), ("medicine", "medicine_surgery"),
    ("physician", "medicine_surgery"), ("doctor", "medicine_surgery"),
    ("driving", "transport"), ("transport", "transport"), ("ships", "transport"),
    ("writing", "writing_media"), ("journalis", "writing_media"), ("poetry", "writing_media"),
    ("editing", "writing_media"), ("language", "writing_media"), ("publish", "writing_media"),
    ("mathemat", "maths_accounts"), ("accountan", "maths_accounts"),
    ("statistic", "maths_accounts"), ("analysis", "maths_accounts"),
    ("teacher", "teaching"), ("teaching", "teaching"), ("research", "teaching"),
    ("professor", "teaching"),
    ("astrolog", "astrology_occult"), ("occult", "astrology_occult"),
    ("priestcraft", "astrology_occult"), ("preacher", "religious"),
    ("art", "design_art"), ("sculpture", "design_art"), ("music", "design_art"),
    ("show-business", "design_art"), ("humour", "design_art"),
    ("lawyer", "law"), ("judge", "law"), ("legal", "law"),
    ("counsel", "counselling"), ("minister", "counselling"),
    ("banker", "banking_finance"), ("banking", "banking_finance"),
    ("insurance", "banking_finance"), ("finance", "banking_finance"),
    ("agricultur", "agriculture"), ("horticultur", "agriculture"), ("pearls", "agriculture"),
    ("sea-product", "agriculture"),
    ("textile", "textiles_luxury"), ("jewell", "textiles_luxury"), ("gold", "textiles_luxury"),
    ("luxury", "textiles_luxury"), ("clothes", "textiles_luxury"),
    ("service", "trade_retail"), ("trade", "trade_retail"),
)

_VERDICT_GOOD = "favourable"
_VERDICT_BAD = "afflicted"


# ── small statistics, with no scipy ─────────────────────────────────────────────────────────

def binomial_p_two_sided(hits: int, n: int, p: float = 0.5) -> Optional[float]:
    """Exact two-sided binomial p — the probability of a result at least this extreme under the
    null. Written out rather than imported because the whole point of the forced-choice design
    is that its null is exactly known, and a dependency that might not be installed is a poor
    place to keep the one number that decides whether any of this means anything."""
    if n <= 0 or not 0.0 < p < 1.0:
        return None
    probs = [math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    observed = probs[hits]
    return min(1.0, sum(x for x in probs if x <= observed + 1e-12))


def poisson_binomial_tail(probs: Sequence[float], hits: int) -> Optional[float]:
    """P(X >= hits) where each trial has its OWN success probability.

    The event-house test needs this rather than a plain binomial: each dated event is scored
    against the base rate of ITS house, and those differ — a house at top grade for 60% of the
    timeline and one at 30% are not the same trial. Averaging them into a single p would be an
    approximation dressed as an exact test, and the counts here are small enough (a reader
    lists five to eight turning points) that the exact DP costs nothing.
    """
    if not probs:
        return None
    dist = [1.0]
    for p in probs:
        p = min(max(float(p), 0.0), 1.0)
        nxt = [0.0] * (len(dist) + 1)
        for k, acc in enumerate(dist):
            nxt[k] += acc * (1.0 - p)
            nxt[k + 1] += acc * p
        dist = nxt
    return min(1.0, sum(dist[min(hits, len(dist) - 1):]))


def _months(year: int, month: int) -> int:
    return year * 12 + (month - 1)


# ── the parsed answer set ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Answers:
    """One reader's submission, indexed the way the scorer needs it."""
    by_qid: dict[str, str]                       # base qid -> answer value
    multi: dict[str, tuple[str, ...]]            # base qid -> selected codes
    events: dict[str, tuple[tuple[int, Optional[int], str], ...]]   # qid -> (y, m|None, kind)
    confidence: dict[str, int]
    free_text: dict[str, str]
    context: str = "after_reading"


def parse_answers(rows: Iterable[tuple[str, str, Optional[str]]]) -> Answers:
    """Stored rows -> a usable answer set. `rows` are (question_id, answer, free_text)."""
    by_qid: dict[str, str] = {}
    multi: dict[str, tuple[str, ...]] = {}
    events: dict[str, list[tuple[int, Optional[int], str]]] = {}
    confidence: dict[str, int] = {}
    free_text: dict[str, str] = {}
    context = "after_reading"
    ev_re = re.compile(r"^(\d{4})(?:-(\d{2}))?:([a-z_]+)$")
    for qid, answer, free in rows:
        if qid.endswith(".meta.context"):
            context = answer or context
            continue
        if qid.endswith(".confidence"):
            base = qid.removesuffix(".confidence")
            if (answer or "").isdigit():
                confidence[base] = int(answer)
            continue
        base = qid.split("#", 1)[0]
        if free:
            free_text[base] = free
        m = ev_re.match(answer or "")
        if m:
            events.setdefault(base, []).append(
                (int(m.group(1)), int(m.group(2)) if m.group(2) else None, m.group(3)))
            continue
        if "," in (answer or ""):
            multi[base] = tuple(v.strip() for v in answer.split(",") if v.strip())
            continue
        if answer:
            by_qid[base] = answer
    return Answers(by_qid=by_qid,
                   multi={k: v for k, v in multi.items()},
                   # Sort on a key rather than the raw tuples: an event's month is None when
                   # the reader gave only a year, and `None < 3` raises. Tuples compare
                   # element by element, so this only bites when two events share a YEAR —
                   # "March 1990" beside a bare "1990" — which is why it went unnoticed and
                   # why it is entirely ordinary. The stored value keeps its None; only the
                   # ordering treats it as 0, so an undated event leads its year.
                   events={k: tuple(sorted(v, key=lambda e: (e[0], e[1] or 0, e[2])))
                           for k, v in events.items()},
                   confidence=confidence, free_text=free_text, context=context)


_CHART_KEY_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})([+-][\d.]+)@([-\d.]+),([-\d.]+)$")


def parse_chart_key(key: str, *, name: str = "feedback") -> Optional[BirthData]:
    """A stored `chart_key` back into birth data, so a submission can be rescored without the
    original request. The key keeps latitude and longitude to four places, which is why
    `feedback_instrument._seed` is defined at exactly that precision — a recast from here
    reproduces the shuffle the reader answered, not a different one."""
    m = _CHART_KEY_RE.match(key.strip())
    if m is None:
        return None
    y, mo, d, h, mi, tz, lat, lon = m.groups()
    return BirthData(name=name, year=int(y), month=int(mo), day=int(d), hour=int(h),
                     minute=int(mi), tz_offset=float(tz), latitude=float(lat),
                     longitude=float(lon))


# ── reading the engine's own side of each comparison ────────────────────────────────────────

def _verdict(report: dict, house: int, signification: str) -> Optional[str]:
    for e in ((report.get("calibration") or {}).get(str(house), {}) or {}).get("entries", ()):
        if e.get("signification") == signification:
            return e.get("verdict")
    return None


def _band_share(report: dict, house: int, signification: str) -> Optional[float]:
    for e in ((report.get("calibration") or {}).get(str(house), {}) or {}).get("entries", ()):
        if e.get("signification") == signification:
            return e.get("band_share")
    return None


def _map_words(text: str, table: Sequence[tuple[str, str]]) -> set[str]:
    """Prose from a doctrine table -> the closed codes the reader chose from."""
    low = text.casefold()
    return {code for kw, code in table if kw in low}


def _engine_regions(report: dict) -> tuple[set[str], int]:
    """The body regions this chart marks, as reader-vocabulary codes, plus how many of the
    engine's own prose regions could not be mapped (coverage, reported not hidden)."""
    med = report.get("medical") or {}
    codes: set[str] = set()
    unmapped = 0
    for region in med.get("regions_marked") or ():
        hit = _map_words(str(region), _REGION_KEYWORDS)
        if hit:
            codes |= hit
        else:
            unmapped += 1
    return codes, unmapped


def _career_frames(prof: dict) -> tuple:
    """The vocation frames, whichever shape `profession.career_frames` arrives in.

    It is a DICT — `{"frames": (...), "strongest": ..., "citation": ...}` — not a list of
    frames. Iterating it directly yields its KEYS, so the old code called `.get("trade")` on
    the string `"frames"` and raised. The list form is accepted too, so a later change to the
    report shape cannot silently empty this comparison instead of failing loudly.
    """
    frames = prof.get("career_frames")
    if isinstance(frames, dict):
        frames = frames.get("frames") or ()
    return tuple(f for f in (frames or ()) if isinstance(f, dict))


def _engine_trades(report: dict) -> set[str]:
    """Every trade family any of the engine's vocation frames names for this chart."""
    prof = report.get("profession") or {}
    blob = " ".join(str(s.get("trades", "")) for s in prof.get("sources") or ())
    for f in _career_frames(prof):
        blob += " " + str(f.get("trade", "")) + " " + str(f.get("sign_career", ""))
    return _map_words(blob, _TRADE_KEYWORDS)


def _marriage_delay_fires(report: dict) -> Optional[bool]:
    timing = (report.get("marriage") or {}).get("timing") or {}
    delays = timing.get("delays")
    if not delays:
        return None
    return any(bool(d.get("fired")) for d in delays)


# ── one scored comparison ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Item:
    """One life fact put beside what the engine said about the same matter."""
    qid: str
    maps_to: str
    question: str
    given: str                      # what the reader selected, as codes
    engine: str                     # what the engine says, in the same terms
    verdict: str                    # hit | miss | partial | not_scoreable | informational
    weight: float = 1.0
    note: str = ""


def _polarity(value: str, good: Sequence[str], bad: Sequence[str]) -> Optional[str]:
    if value in good:
        return _VERDICT_GOOD
    if value in bad:
        return _VERDICT_BAD
    return None


#: For each `maps_to` that reads a single house signification: the house, the signification,
#: and which answer codes count as the good pole and which as the bad one. Everything not
#: listed either has its own function below or is informational.
_POLARITY_MAP: dict[str, tuple[int, str, tuple[str, ...], tuple[str, ...]]] = {
    # Two questions share this key (A10 relationship, A11 the father's own fortunes), so both
    # vocabularies belong here — with only A10's, every A11 answer fell out as not_scoreable.
    "h9.father": (9, "father", ("close", "prospered"),
                  ("conflicted", "absent", "died_early", "reversal")),
    "h4.mother": (4, "mother", ("close",), ("conflicted", "absent", "died_early")),
    "h3.siblings": (3, "siblings", ("close",), ("distant", "conflicted", "lost")),
    "h9.higher_learning": (9, "higher_learning", ("graduate", "postgraduate", "doctorate"),
                           ("none", "school")),
    "h4.education": (4, "education", ("no",), ("serious",)),
    "h6.debts": (6, "debts", ("none",), ("serious_past", "serious_now")),
    "h8.legacies": (8, "legacies", ("significant",), ("none",)),
    "h5.poorvapunya": (5, "poorvapunya", ("net_gain",), ("net_loss",)),
    "h10.status_honour": (10, "status_honour", ("above",), ("short",)),
    "h12.foreign_residence": (12, "foreign_residence", ("abroad", "over5", "most"),
                              ("never", "none")),
    "h12.moksha": (12, "moksha", ("strong", "central"), ("none",)),
    "h12.incarceration": (12, "incarceration", ("never",), ("extended",)),
    "h7.marital_happiness": (7, "marital_happiness", ("happy",), ("strained", "ended")),
    # Likewise A28 (how many) and A29 (was it difficult) — "no" is no difficulty, i.e. the
    # favourable pole. Neither token collides with A28's none/one/two/three_plus.
    "h5.children": (5, "children", ("two", "three_plus", "no"), ("none", "yes")),
}


def _score_life(report: dict, inst: dict, ans: Answers) -> list[Item]:
    """Every Part A / Part B answer that has an engine fact to sit beside.

    No p-values here and none possible: the base rate of a happy marriage or a distant father
    in the population is not known to this project, so a hit count is a hit count. It is still
    the most useful column in the scorecard, because it says WHICH matters the engine gets
    right — which is what a next improvement is chosen from.
    """
    by_qid = {q["qid"]: q for p in inst["parts"] for q in p["questions"]}
    out: list[Item] = []

    for qid, q in by_qid.items():
        maps_to = q.get("maps_to") or ""
        if not maps_to or q["part"] not in ("A", "B"):
            continue
        given_multi = ans.multi.get(qid)
        given = ans.by_qid.get(qid)
        # A multi-select answered with exactly ONE option arrives with no comma in it, so the
        # parser cannot tell it from a single-choice answer. The question knows, so coalesce
        # here — otherwise a reader who ticks one body region is silently not scored at all.
        if given_multi is None and given is not None and q["kind"] == "multi":
            given_multi, given = (given,), None
        if given is None and not given_multi and qid not in ans.events:
            continue
        text = q["text_en"]

        if maps_to in _POLARITY_MAP:
            house, sig, good, bad = _POLARITY_MAP[maps_to]
            engine = _verdict(report, house, sig)
            reader = _polarity(str(given), good, bad)
            share = _band_share(report, house, sig)
            weight = round(1.0 - float(share), 3) if share is not None else 1.0
            if engine is None or reader is None:
                out.append(Item(qid, maps_to, text, str(given), str(engine),
                                "not_scoreable", weight,
                                "no direction in the answer or no verdict on the chart"))
            else:
                out.append(Item(qid, maps_to, text, reader, engine,
                                "hit" if reader == engine else "miss", weight,
                                f"H{house} {sig}"))
            continue

        if maps_to == "medical.regions" and given_multi:
            engine_codes, unmapped = _engine_regions(report)
            picked = {c for c in given_multi if c != "none"}
            overlap = picked & engine_codes
            if not picked or not engine_codes:
                verdict = "not_scoreable"
            elif overlap:
                verdict = "hit" if len(overlap) >= max(1, len(picked) // 2) else "partial"
            else:
                verdict = "miss"
            out.append(Item(qid, maps_to, text, ",".join(sorted(picked)),
                            ",".join(sorted(engine_codes)), verdict, 1.0,
                            f"{len(overlap)} of {len(picked)} reported regions are marked; "
                            f"{unmapped} engine region(s) had no code"))
            continue

        if maps_to == "career.trades" and given_multi:
            engine_codes = _engine_trades(report)
            picked = {c for c in given_multi if c != "none"}
            overlap = picked & engine_codes
            out.append(Item(qid, maps_to, text, ",".join(sorted(picked)),
                            ",".join(sorted(engine_codes)),
                            "not_scoreable" if not picked or not engine_codes
                            else "hit" if overlap else "miss", 1.0,
                            f"{len(overlap)} of {len(picked)} reported trades are named"))
            continue

        if maps_to == "h10.authority_vs_trade" and given in ("under_authority", "own"):
            modes = dict((k, v) for k, v in (report.get("profession") or {}).get(
                "mode_split") or ())
            auth = str(modes.get("profession_authority", ""))
            trade = str(modes.get("profession_trade", ""))
            if not auth or not trade or auth == trade:
                out.append(Item(qid, maps_to, text, str(given), f"{auth}/{trade}",
                                "not_scoreable", 1.0,
                                "the engine does not separate the two on this chart"))
            else:
                engine_says = "own" if trade.startswith(_VERDICT_GOOD) else "under_authority"
                out.append(Item(qid, maps_to, text, str(given), engine_says,
                                "hit" if given == engine_says else "miss", 1.0,
                                f"authority {auth}, own trade {trade}"))
            continue

        if maps_to == "marriage.delay" and given in ("early", "on_time", "late", "very_late"):
            fires = _marriage_delay_fires(report)
            if fires is None:
                out.append(Item(qid, maps_to, text, str(given), "-", "not_scoreable"))
            else:
                engine_says = "late" if fires else "not_late"
                reader_says = "late" if given in ("late", "very_late") else "not_late"
                out.append(Item(qid, maps_to, text, reader_says, engine_says,
                                "hit" if reader_says == engine_says else "miss", 1.0,
                                "Raman's delay screen" +
                                (" fires" if fires else " is silent")))
            continue

        if maps_to == "arishta.balarishta" and given in ("sickly", "robust", "yes", "no"):
            ar = report.get("arishta") or {}
            applies = bool(ar.get("balarishta_applies")) and not ar.get("balarishta_cancelled")
            reader_says = "danger" if given in ("sickly", "yes") else "no_danger"
            engine_says = "danger" if applies else "no_danger"
            out.append(Item(qid, maps_to, text, reader_says, engine_says,
                            "hit" if reader_says == engine_says else "miss", 1.0,
                            "balarishta " + ("applies" if applies else "does not apply")))
            continue

        if maps_to == "rect.portrait":
            key = instrument_key(report)["answers"].get(qid)
            if key and given:
                out.append(Item(qid, maps_to, text, str(given), str(key),
                                "hit" if given == key else "miss", 1.0,
                                "the reader's own temperament against the cast ascendant"))
            continue

        # `psych.mind_screen` is here rather than in `_POLARITY_MAP` on purpose. The engine's
        # mind screen is present-or-absent and ships its own caution that it is not a
        # diagnosis (`psych.mind_caution`); scoring a reader's history of low mood as a hit
        # would have this scorecard claim the engine diagnoses mental illness. It is recorded
        # because the reader answered it, and left unscored because it is not ours to score.
        if maps_to in ("longevity.family", "rect.source", "rect.precision", "rect.build",
                       "rect.apparent_age", "rect.birth_order", "rect.birth_place",
                       "psych.temperament", "psych.mind_screen", "h10.modes",
                       "health.hospitalisations",
                       "health.surgeries", "marriage.status", "marriage.year",
                       "spine.recent", "rect.already_rectified", "rect.anchors"):
            out.append(Item(qid, maps_to, text,
                            ",".join(given_multi) if given_multi else str(given or ""),
                            "-", "informational", 0.0,
                            "recorded for context and rectification, not scored"))
            continue

    return out


# ── the four measurements ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ForcedChoice:
    """Part C, the only measurement with a clean null."""
    n: int
    hits: int
    p_value: Optional[float]
    weighted_hits: float
    weighted_n: float
    per_item: tuple[tuple[str, str, bool, float], ...] = ()   # qid, signification, hit, weight

    @property
    def rate(self) -> Optional[float]:
        return round(self.hits / self.n, 3) if self.n else None

    @property
    def weighted_rate(self) -> Optional[float]:
        return round(self.weighted_hits / self.weighted_n, 3) if self.weighted_n else None


@dataclass(frozen=True)
class Spine:
    """Dated turning points against the Mahadasha boundaries."""
    events: int
    near_boundary: int
    chance_rate: Optional[float]
    expected: Optional[float]
    p_value: Optional[float]
    span_months: int
    boundaries_in_span: int
    tolerance_months: int = SPINE_TOLERANCE_MONTHS
    detail: tuple[tuple[str, str, bool], tuple[()], ...] | tuple = ()


#: The activation grades the engine emits, best first. A house is "strongly lit" in a period
#: when it carries the top grade; the four-tier scheme is Raman's own (HTJAH-I "When Do
#: Indications Fructify?") and only the top tier is treated as a positive claim here.
_TOP_GRADES: frozenset[str] = frozenset({"par_excellence"})


@dataclass(frozen=True)
class EventHouses:
    """Dated life events against the periods the engine graded highest for THEIR house.

    Why grade and not "was the house active at all": measured, every house is activated in
    74-100% of periods on a real chart (mean ~88%). That is Raman's timer_set being
    deliberately broad — the five/six factors light nearly everything nearly always — so a
    was-it-lit test scores ~88% by construction and says nothing. The GRADE does discriminate:
    61%/39% top-vs-lower across a chart, and per house it swings much further.

    `direction` is reported as bare counts. Its null is not computable from one chart — it
    would need the population base rate of good-vs-bad life events, which this project does not
    have — so a p-value there would be invented. The same restraint the life-facts section
    takes.
    """
    events: int                       # dated events that fell inside the timeline window
    outside_window: int               # dated events the timeline does not cover
    unscoreable: int                  # inside the window but the house was not activated
    top_grade: int                    # events landing in a top-grade period for their house
    expected: Optional[float]         # sum of the per-event base rates
    p_value: Optional[float]          # exact Poisson-binomial, P(X >= top_grade)
    direction_scored: int = 0         # events with a good/bad valence and a house verdict
    direction_hits: int = 0
    per_event: tuple[tuple[str, str, int, str, bool], ...] = ()   # date, kind, house, grade, top


@dataclass(frozen=True)
class Reaction:
    """Part D, counted rather than scored."""
    overall: Optional[str]
    worth_paying: Optional[str]
    harm: Optional[str]
    wrong_chapters: tuple[str, ...] = ()
    specific_chapters: tuple[str, ...] = ()
    barnum_chapters: tuple[str, ...] = ()
    skipped_chapters: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChartScorecard:
    chart_key: str
    instrument_version: str
    context: str
    answered: int
    forced: ForcedChoice
    inverted: ForcedChoice
    #: The same items split by how sure the reader said they were. A confident hit and a
    #: coin-flip hit are different evidence, and a reader who scores at chance exactly where
    #: they were most certain is telling you something the pooled number hides.
    confident: ForcedChoice
    unsure: ForcedChoice
    life: tuple[Item, ...]
    spine: Spine
    event_houses: EventHouses
    reaction: Reaction
    #: qid -> what the reader wrote there, carried so `aggregate` can group it by question.
    free_text: dict[str, str] = field(default_factory=dict)
    rectification_tight: bool = False
    headline: str = ""


#: A rating at or above this is "sure"; at or below the other, "unsure". The middle value is
#: neither and is left out of both, rather than being pushed to whichever side makes the
#: numbers look better.
_CONFIDENT_AT = 4
_UNSURE_AT = 2


def _score_forced(report: dict, inst: dict, ans: Answers,
                  ) -> tuple[ForcedChoice, ForcedChoice, ForcedChoice, ForcedChoice]:
    key = instrument_key(report)
    meta = key["meta"]
    inverted_ids = set(key["inverted"])
    buckets: dict[bool, list[tuple[str, str, bool, float]]] = {False: [], True: []}
    for qid, expected in key["answers"].items():
        m = meta.get(qid, {})
        if m.get("kind") != "forced_choice":
            continue
        given = ans.by_qid.get(qid)
        if given is None:
            continue
        share = float(m.get("band_share") or 0.5)
        # An item only 4% of charts share discriminates; one 45% share it barely can. Weighting
        # by 1 - share says so in the arithmetic instead of in a footnote.
        buckets[qid in inverted_ids].append(
            (qid, str(m.get("signification", "")), given == expected, round(1.0 - share, 3)))

    def build(rows: list[tuple[str, str, bool, float]]) -> ForcedChoice:
        n = len(rows)
        hits = sum(1 for _q, _s, hit, _w in rows if hit)
        wn = sum(w for _q, _s, _h, w in rows)
        wh = sum(w for _q, _s, hit, w in rows if hit)
        return ForcedChoice(n=n, hits=hits, p_value=binomial_p_two_sided(hits, n),
                            weighted_hits=round(wh, 3), weighted_n=round(wn, 3),
                            per_item=tuple(rows))

    main = buckets[False]
    sure = [r for r in main if (ans.confidence.get(r[0]) or 0) >= _CONFIDENT_AT]
    unsure = [r for r in main if 0 < (ans.confidence.get(r[0]) or 0) <= _UNSURE_AT]
    return build(main), build(buckets[True]), build(sure), build(unsure)


def _score_spine(inst: dict, ans: Answers) -> Spine:
    """Turning points against period changes, with the chance rate COMPUTED.

    The boundaries cluster — several Mahadasha changes can fall inside a few years — so their
    tolerance windows overlap. Taking the union of the windows over the span the reader actually
    reported from is the difference between an honest null and a flattering one; summing the
    windows instead would roughly double the apparent chance rate's denominator and make a
    coin-flip result look like a finding.
    """
    events: list[tuple[int, Optional[int], str]] = []
    for qid, evs in ans.events.items():
        if qid.endswith(".A35") or qid.endswith(".B6"):
            events.extend(evs)
    dated = [(y, m or 6, kind) for y, m, kind in events]
    bounds: list[int] = []
    for row in inst.get("boundaries") or ():
        try:
            y, mo, _d = str(row["date"]).split("-")
            bounds.append(_months(int(y), int(mo)))
        except (KeyError, ValueError):
            continue
    if not dated or not bounds:
        return Spine(events=len(dated), near_boundary=0, chance_rate=None, expected=None,
                     p_value=None, span_months=0, boundaries_in_span=0)

    ev_months = [_months(y, m) for y, m, _k in dated]
    lo, hi = min(ev_months), max(ev_months)
    span = max(1, hi - lo + 1)
    tol = SPINE_TOLERANCE_MONTHS
    covered: set[int] = set()
    in_span = 0
    for b in bounds:
        if lo - tol <= b <= hi + tol:
            in_span += 1
        for mth in range(b - tol, b + tol + 1):
            if lo <= mth <= hi:
                covered.add(mth)
    chance = len(covered) / span
    near = sum(1 for m in ev_months if any(abs(m - b) <= tol for b in bounds))
    n = len(ev_months)
    detail = tuple((f"{y:04d}-{m:02d}", kind,
                    any(abs(_months(y, m) - b) <= tol for b in bounds))
                   for y, m, kind in dated)
    return Spine(events=n, near_boundary=near, chance_rate=round(chance, 3),
                 expected=round(n * chance, 2),
                 p_value=binomial_p_two_sided(near, n, chance) if 0 < chance < 1 else None,
                 span_months=span, boundaries_in_span=in_span, detail=detail)


def _house_top_grade_base_rate(report: dict) -> dict[int, float]:
    """Per house, the share of the covered timeline spent at the TOP activation grade.

    Duration-weighted, not period-counted: bhuktis differ in length by years, so counting
    periods would let a run of short ones outvote a long one and quietly bias the null in
    whichever direction the chart happens to favour.
    """
    span: dict[int, float] = {}
    top: dict[int, float] = {}
    for p in report.get("timeline") or ():
        try:
            days = float(p["end_jd"]) - float(p["start_jd"])
        except (KeyError, TypeError, ValueError):
            continue
        if days <= 0:
            continue
        for a in p.get("activated") or ():
            h = a.get("house")
            if not isinstance(h, int):
                continue
            span[h] = span.get(h, 0.0) + days
            if a.get("grade") in _TOP_GRADES:
                top[h] = top.get(h, 0.0) + days
    return {h: (top.get(h, 0.0) / d) for h, d in span.items() if d > 0}


def _score_event_houses(report: dict, ans: Answers) -> EventHouses:
    """Dated life events against the grade the engine gave THEIR house at THAT time.

    This is the strongest test the instrument can run, because the reader supplies both halves
    blind: they date the event before reading anything, and the house each kind of event is
    read from is fixed doctrine, not a choice made after the fact.
    """
    import swisseph as swe

    events: list[tuple[int, Optional[int], str]] = []
    for qid, evs in ans.events.items():
        if qid.endswith(".A35"):                 # the turning points, not the rectification grid
            events.extend(evs)
    periods = list(report.get("timeline") or ())
    base = _house_top_grade_base_rate(report)
    if not events or not periods:
        return EventHouses(events=0, outside_window=0, unscoreable=0, top_grade=0,
                           expected=None, p_value=None)

    outside = unscoreable = top = 0
    dir_scored = dir_hits = 0
    probs: list[float] = []
    detail: list[tuple[str, str, int, str, bool]] = []

    for year, month, kind in events:
        house = EVENT_HOUSE.get(kind, 0)
        if not house:
            continue                              # "other" maps nowhere and is not scored
        jd = swe.julday(year, month or 6, 15, 12.0, swe.GREG_CAL)
        period = next((p for p in periods
                       if float(p.get("start_jd", 0)) <= jd <= float(p.get("end_jd", 0))), None)
        if period is None:
            outside += 1
            continue
        act = next((a for a in period.get("activated") or ()
                    if a.get("house") == house), None)
        if act is None:
            unscoreable += 1
            continue
        grade = str(act.get("grade", ""))
        is_top = grade in _TOP_GRADES
        top += 1 if is_top else 0
        probs.append(base.get(house, 0.5))
        detail.append((f"{year:04d}-{(month or 6):02d}", kind, house, grade, is_top))

        valence = EVENT_VALENCE.get(kind, "neutral")
        verdict = act.get("natal_verdict")
        if valence in ("good", "bad") and verdict in (_VERDICT_GOOD, _VERDICT_BAD):
            dir_scored += 1
            if (valence == "good") == (verdict == _VERDICT_GOOD):
                dir_hits += 1

    return EventHouses(
        events=len(probs), outside_window=outside, unscoreable=unscoreable, top_grade=top,
        expected=round(sum(probs), 2) if probs else None,
        p_value=poisson_binomial_tail(probs, top) if probs else None,
        direction_scored=dir_scored, direction_hits=dir_hits, per_event=tuple(detail))


def _score_reaction(inst: dict, ans: Answers) -> Reaction:
    by_maps = {q["maps_to"]: q["qid"] for p in inst["parts"] for q in p["questions"]
               if q.get("maps_to")}

    def multi(name: str) -> tuple[str, ...]:
        qid = by_maps.get(name)
        return tuple(ans.multi.get(qid, ())) if qid else ()

    def one(name: str) -> Optional[str]:
        qid = by_maps.get(name)
        return ans.by_qid.get(qid) if qid else None

    return Reaction(overall=one("reaction.overall"),
                    worth_paying=one("reaction.worth_paying"),
                    harm=one("reaction.harm"),
                    wrong_chapters=multi("reaction.wrong"),
                    specific_chapters=multi("reaction.specific"),
                    barnum_chapters=multi("reaction.barnum"),
                    skipped_chapters=multi("reaction.skipped"))


def score_chart(report: dict, rows: Iterable[tuple[str, str, Optional[str]]], *,
                chart_key: str = "") -> ChartScorecard:
    """One reader's submission, measured against the chart they were given."""
    inst = build_feedback_instrument(report)
    ans = parse_answers(rows)
    forced, inverted, confident, unsure = _score_forced(report, inst, ans)
    life = tuple(_score_life(report, inst, ans))
    spine = _score_spine(inst, ans)
    event_houses = _score_event_houses(report, ans)
    reaction = _score_reaction(inst, ans)
    answered = (len(ans.by_qid) + len(ans.multi)
                + sum(len(v) for v in ans.events.values()))
    scored = [i for i in life if i.verdict in ("hit", "miss", "partial")]
    hits = sum(1 for i in scored if i.verdict == "hit")

    bits = []
    if forced.n:
        bits.append(f"forced choice {forced.hits}/{forced.n}"
                    + (f" (p={forced.p_value:.3f})" if forced.p_value is not None else ""))
    if scored:
        bits.append(f"life facts {hits}/{len(scored)}")
    if spine.events:
        bits.append(f"turning points near a period change "
                    f"{spine.near_boundary}/{spine.events}"
                    + (f" (expected {spine.expected})" if spine.expected is not None else ""))
    if event_houses.events:
        bits.append(f"events in a top-graded period for their own matter "
                    f"{event_houses.top_grade}/{event_houses.events}"
                    + (f" (expected {event_houses.expected})"
                       if event_houses.expected is not None else ""))
    if ans.context != "before_reading":
        bits.append("ANSWERED AFTER READING — treat as a satisfaction survey, not evidence")

    return ChartScorecard(
        chart_key=chart_key, instrument_version=str(inst.get("version", "")),
        context=ans.context, answered=answered, forced=forced, inverted=inverted,
        confident=confident, unsure=unsure,
        life=life, spine=spine, event_houses=event_houses, reaction=reaction,
        free_text=dict(ans.free_text),
        rectification_tight=bool((inst.get("rectification") or {}).get("tight")),
        headline="; ".join(bits) or "nothing scoreable was answered")


# ── across charts: what actually carries signal ─────────────────────────────────────────────

@dataclass(frozen=True)
class Aggregate:
    """The answer to 'how is the engine doing', and the work list that follows from it."""
    charts: int
    blind_charts: int
    forced: ForcedChoice
    inverted: ForcedChoice
    forced_blind_only: ForcedChoice
    #: The same items split by how sure the reader said they were, pooled across charts.
    confident: ForcedChoice
    unsure: ForcedChoice
    spine_events: int
    spine_near: int
    spine_p: Optional[float]
    #: The pooled spine null, event-weighted across the charts that contributed events. Each
    #: chart computes its OWN chance rate from its own event span and the Mahadasha boundaries
    #: inside it (`_score_spine`); pooling has to carry those rates forward rather than assume
    #: a shared one. `None` when no chart supplied a computable rate.
    spine_chance: Optional[float] = None
    #: Pooled event-house result. No pooled p-value: each chart's null is its own set of
    #: per-house base rates, so the tails cannot simply be added.
    event_top_grade: int = 0
    event_scored: int = 0
    #: signification -> (hits, n). The improvement list: a reading that scores at chance across
    #: many readers is not carrying information about a life, however faithful it is to Raman.
    per_signification: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: what each life-fact comparison scored, by `maps_to`
    per_life_fact: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: chapter -> how many readers said it was wrong / uncannily specific / true-of-everyone
    chapter_wrong: dict[str, int] = field(default_factory=dict)
    chapter_specific: dict[str, int] = field(default_factory=dict)
    chapter_barnum: dict[str, int] = field(default_factory=dict)
    chapter_skipped: dict[str, int] = field(default_factory=dict)
    overall_scale: dict[str, int] = field(default_factory=dict)
    harm_reports: int = 0
    #: What people wrote, grouped by the question they wrote it against. Quotations, never
    #: summarised and never sent to a model: the whole point of keeping one free-text box in an
    #: otherwise closed form is to hear the thing the options did not anticipate, and a summary
    #: is exactly where that gets lost.
    free_text: dict[str, tuple[str, ...]] = field(default_factory=dict)
    notes: tuple[str, ...] = ()


def _pool(cards: Sequence[ChartScorecard], attr: str) -> ForcedChoice:
    rows: list[tuple[str, str, bool, float]] = []
    for c in cards:
        rows.extend(getattr(c, attr).per_item)
    n = len(rows)
    hits = sum(1 for _q, _s, hit, _w in rows if hit)
    wn = sum(w for _q, _s, _h, w in rows)
    wh = sum(w for _q, _s, hit, w in rows if hit)
    return ForcedChoice(n=n, hits=hits, p_value=binomial_p_two_sided(hits, n),
                        weighted_hits=round(wh, 3), weighted_n=round(wn, 3),
                        per_item=tuple(rows))


def _pooled_spine_chance(rates: Sequence[tuple[int, float]]) -> Optional[float]:
    """The pooled dated-spine null: each chart's own computed chance rate, weighted by how
    many events that chart contributed.

    Event-weighted rather than a plain mean because the pooled statistic counts EVENTS, not
    charts — a reader who dated ten turning points must move the null ten times as far as one
    who dated a single event, or the p-value is tested against a rate the pooled numerator
    never had. Returns None when no chart produced a rate (no events, or a span too short to
    derive one), which is the honest answer: there is no null, so there is no p-value.
    """
    total = sum(n for n, _r in rates)
    if not total:
        return None
    return sum(n * r for n, r in rates) / total


def aggregate(cards: Sequence[ChartScorecard]) -> Aggregate:
    """Pool the scorecards. Two things are kept separate on purpose and must stay that way.

    Submissions answered AFTER the reading was read are pooled separately, because a reader who
    has been told what the chart says is no longer reporting what they would have said. And the
    inverted-channel items never join the main pool: agreement there is evidence against.
    """
    blind = [c for c in cards if c.context == "before_reading"]
    per_sig: dict[str, list[int]] = {}
    per_life: dict[str, list[int]] = {}
    chap_wrong: dict[str, int] = {}
    chap_specific: dict[str, int] = {}
    chap_barnum: dict[str, int] = {}
    chap_skipped: dict[str, int] = {}
    scale: dict[str, int] = {}
    harm = 0
    ev = near = 0
    #: (events, chance_rate) per contributing chart, so the pooled null can be event-weighted
    #: from the rates the charts actually computed instead of a shared guess.
    spine_rates: list[tuple[int, float]] = []
    ev_top = ev_n = 0
    free: dict[str, list[str]] = {}

    for c in cards:
        for _qid, sig, hit, _w in c.forced.per_item:
            slot = per_sig.setdefault(sig, [0, 0])
            slot[0] += 1 if hit else 0
            slot[1] += 1
        for item in c.life:
            if item.verdict in ("hit", "miss", "partial"):
                slot = per_life.setdefault(item.maps_to, [0, 0])
                slot[0] += 1 if item.verdict == "hit" else 0
                slot[1] += 1
        for ch in c.reaction.wrong_chapters:
            chap_wrong[ch] = chap_wrong.get(ch, 0) + 1
        for ch in c.reaction.specific_chapters:
            chap_specific[ch] = chap_specific.get(ch, 0) + 1
        for ch in c.reaction.barnum_chapters:
            chap_barnum[ch] = chap_barnum.get(ch, 0) + 1
        for ch in c.reaction.skipped_chapters:
            chap_skipped[ch] = chap_skipped.get(ch, 0) + 1
        if c.reaction.overall:
            scale[c.reaction.overall] = scale.get(c.reaction.overall, 0) + 1
        if c.reaction.harm in ("mildly", "yes"):
            harm += 1
        ev += c.spine.events
        near += c.spine.near_boundary
        if c.spine.events and c.spine.chance_rate is not None:
            spine_rates.append((c.spine.events, float(c.spine.chance_rate)))
        ev_top += c.event_houses.top_grade
        ev_n += c.event_houses.events
        for qid, text in c.free_text.items():
            if text and text.strip():
                free.setdefault(qid.rsplit(".", 1)[-1], []).append(text.strip())

    notes: list[str] = []
    if not blind and cards:
        notes.append("NO submission was answered before the reading — every number here is a "
                     "satisfaction measure, not evidence about the method.")
    if len(cards) < 30:
        notes.append(f"only {len(cards)} chart(s): far too few to conclude anything; the "
                     f"forced-choice pool needs hundreds of items before its p-value means "
                     f"much.")
    if harm:
        notes.append(f"{harm} reader(s) reported the reading as upsetting or frightening — "
                     f"that is a product defect to fix before any accuracy work.")

    spine_chance = _pooled_spine_chance(spine_rates)

    return Aggregate(
        charts=len(cards), blind_charts=len(blind),
        forced=_pool(cards, "forced"), inverted=_pool(cards, "inverted"),
        forced_blind_only=_pool(blind, "forced"),
        confident=_pool(cards, "confident"), unsure=_pool(cards, "unsure"),
        spine_events=ev, spine_near=near,
        spine_chance=spine_chance,
        spine_p=(binomial_p_two_sided(near, ev, spine_chance)
                 if ev and spine_chance is not None else None),
        per_signification={k: (v[0], v[1]) for k, v in sorted(per_sig.items())},
        per_life_fact={k: (v[0], v[1]) for k, v in sorted(per_life.items())},
        chapter_wrong=dict(sorted(chap_wrong.items(), key=lambda kv: -kv[1])),
        chapter_specific=dict(sorted(chap_specific.items(), key=lambda kv: -kv[1])),
        chapter_barnum=dict(sorted(chap_barnum.items(), key=lambda kv: -kv[1])),
        chapter_skipped=dict(sorted(chap_skipped.items(), key=lambda kv: -kv[1])),
        overall_scale=scale, harm_reports=harm,
        free_text={k: tuple(v) for k, v in sorted(free.items())},
        event_top_grade=ev_top, event_scored=ev_n,
        notes=tuple(notes))


def render_aggregate(agg: Aggregate) -> str:
    """The scorecard as a person reads it. Deliberately leads with the caveats: a number here
    that is quoted without them is exactly the mistake this project's own validation record
    exists to prevent."""
    L = [f"charts scored: {agg.charts}  (answered blind: {agg.blind_charts})", ""]
    for n in agg.notes:
        L.append(f"  ! {n}")
    if agg.notes:
        L.append("")
    f = agg.forced
    L.append(f"FORCED CHOICE   {f.hits}/{f.n} = {f.rate}   chance 0.5"
             + (f"   p={f.p_value:.4f}" if f.p_value is not None else ""))
    L.append(f"  rarity-weighted {f.weighted_hits}/{f.weighted_n} = {f.weighted_rate}")
    b = agg.forced_blind_only
    if b.n:
        L.append(f"  blind submissions only: {b.hits}/{b.n} = {b.rate}"
                 + (f"   p={b.p_value:.4f}" if b.p_value is not None else ""))
    i = agg.inverted
    if i.n:
        L.append(f"  INVERTED channels (agreement is evidence AGAINST): {i.hits}/{i.n}"
                 f" = {i.rate}")
    conf, unsure = agg.confident, agg.unsure
    if conf.n or unsure.n:
        L.append(f"  answered SURE   {conf.hits}/{conf.n} = {conf.rate}"
                 + (f"   p={conf.p_value:.4f}" if conf.p_value is not None else ""))
        L.append(f"  answered UNSURE {unsure.hits}/{unsure.n} = {unsure.rate}")
        if conf.n >= 5 and unsure.n >= 5 and conf.rate is not None \
                and unsure.rate is not None and conf.rate <= unsure.rate:
            L.append("  ! scored no better where the reader was MORE certain — that pattern "
                     "belongs to agreeing with whatever is shown, not to recognising a chart.")
    L.append("")
    if agg.event_scored:
        L.append(f"EVENT vs PERIOD  {agg.event_top_grade}/{agg.event_scored} dated events fell "
                 f"in a top-graded period for their own matter")
        L.append("  (no pooled p-value: each chart's null is its own per-house base rates, so "
                 "the tails cannot be added — see the per-chart cards)")
        L.append("")
    if agg.spine_events:
        L.append(f"DATED SPINE     {agg.spine_near}/{agg.spine_events} turning points within "
                 f"{SPINE_TOLERANCE_MONTHS} months of a period change"
                 + (f"   p={agg.spine_p:.4f}" if agg.spine_p is not None else ""))
        if agg.spine_chance is not None:
            L.append(f"  chance rate {agg.spine_chance:.3f} — event-weighted from each chart's "
                     f"own event span and boundaries, never assumed")
        else:
            L.append("  no chance rate could be computed, so no p-value is offered")
        L.append("")
    if agg.per_signification:
        L.append("BY READING (forced choice) — the improvement list, worst first:")
        for sig, (h, n) in sorted(agg.per_signification.items(),
                                  key=lambda kv: (kv[1][0] / kv[1][1]) if kv[1][1] else 1):
            L.append(f"  {sig:<24} {h}/{n}")
        L.append("")
    if agg.per_life_fact:
        L.append("BY LIFE FACT (no null — a count, not a p-value):")
        for k, (h, n) in sorted(agg.per_life_fact.items(),
                                key=lambda kv: (kv[1][0] / kv[1][1]) if kv[1][1] else 1):
            L.append(f"  {k:<28} {h}/{n}")
        L.append("")
    if agg.chapter_wrong:
        L.append("CHAPTERS READERS CALLED WRONG:")
        for ch, n in agg.chapter_wrong.items():
            L.append(f"  {ch:<20} {n}")
        L.append("")
    if agg.chapter_barnum:
        L.append("CHAPTERS READERS SAID WERE TRUE OF EVERYONE (a rewrite list, not a bug list):")
        for ch, n in agg.chapter_barnum.items():
            L.append(f"  {ch:<20} {n}")
        L.append("")
    if agg.overall_scale:
        L.append("OVERALL FIT: " + ", ".join(f"{k}={v}" for k, v in agg.overall_scale.items()))
    if agg.free_text:
        L.append("")
        L.append("WHAT PEOPLE WROTE (verbatim — the options did not anticipate these):")
        for qid, texts in agg.free_text.items():
            L.append(f"  {qid}:")
            for t in texts:
                L.append(f"    \u201c{t}\u201d")
    return "\n".join(L)



# ── reading the stored rows ─────────────────────────────────────────────────────────────────

async def load_and_score(database_url: str = "", *, chart_key: str = "",
                         limit_charts: int = 500) -> tuple[list[ChartScorecard], Aggregate]:
    """Read `chart_feedback`, recast each chart from its own key, and score every submission.

    A chart whose key cannot be parsed, or whose recast fails, is skipped with a log line
    rather than aborting the run — one bad row must not cost the whole measurement.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.models.domain import ChartFeedback
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict

    if not database_url:
        from app.core.config import settings
        database_url = settings.DATABASE_URL
    engine = create_async_engine(database_url)
    try:
        sm = async_sessionmaker(engine, expire_on_commit=False)
        async with sm() as s:
            q = select(ChartFeedback)
            if chart_key:
                q = q.where(ChartFeedback.chart_key == chart_key)
            rows = (await s.execute(q)).scalars().all()
    finally:
        await engine.dispose()

    grouped: dict[str, list[tuple[str, str, Optional[str]]]] = {}
    for r in rows:
        grouped.setdefault(r.chart_key, []).append(
            (r.question_id, r.answer, r.free_text))

    from app.raman_saab.feedback_instrument import INSTRUMENT_VERSION
    current = f"inst.{INSTRUMENT_VERSION}."
    cards: list[ChartScorecard] = []
    stale_rows = 0
    legacy_charts = 0
    for key, answers in list(grouped.items())[:limit_charts]:
        instrument_rows = [a for a in answers if a[0].startswith("inst.")]
        if not instrument_rows:
            legacy_charts += 1
            continue                        # rows from the older five-question flow
        # An earlier instrument version asked different questions under qids that no longer
        # exist, so its rows would rebuild to nothing and score zero — data loss that reads
        # exactly like a null result. Count them and say so rather than letting them vanish.
        stale = [a for a in instrument_rows if not a[0].startswith(current)]
        if stale:
            stale_rows += len(stale)
            answers = [a for a in answers if a not in stale]
            if not any(a[0].startswith(current) for a in answers):
                continue
        birth = parse_chart_key(key)
        if birth is None:
            logger.warning("unparseable chart_key, skipped: %s", key)
            continue
        try:
            report = to_report_dict(build_detailed_report(birth))
        except Exception:  # noqa: BLE001 — one bad chart must not cost the run
            logger.exception("could not recast chart, skipped: %s", key)
            continue
        cards.append(score_chart(report, answers, chart_key=key))
    agg = aggregate(cards)
    extra: list[str] = []
    if stale_rows:
        extra.append(f"{stale_rows} stored answer(s) came from an older instrument version "
                     f"than {INSTRUMENT_VERSION} and were SKIPPED, not scored — their "
                     f"questions no longer exist, so scoring them would read as disagreement.")
    if legacy_charts:
        extra.append(f"{legacy_charts} chart(s) carried only the older five-question feedback "
                     f"flow and are not part of any number here.")
    if extra:
        agg = replace(agg, notes=tuple(extra) + agg.notes)
    return cards, agg


def render_aggregate_html(agg: Aggregate, cards: Sequence[ChartScorecard]) -> str:
    """The scorecard as a self-contained page for whoever is running the study.

    A FILE, deliberately, and not a route. This codebase has no admin role — `app/core/auth.py`
    offers only `CurrentAccount` — so a live scorecard endpoint would be readable by any signed-in
    user, and a reader who can see which readings score well can infer the answer key for their
    own chart. That would poison every submission after it. If an admin role is ever added, this
    is still the wrong thing to expose without thinking about that inference.
    """
    def esc(x: object) -> str:
        return (str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))

    def fc_row(label: str, f: ForcedChoice) -> str:
        if not f.n:
            return ""
        p = f"{f.p_value:.4f}" if f.p_value is not None else "&mdash;"
        return (f"<tr><td>{esc(label)}</td><td class='n'>{f.hits}/{f.n}</td>"
                f"<td class='n'>{f.rate}</td><td class='n'>{p}</td></tr>")

    rows = "".join([fc_row("All forced choices", agg.forced),
                    fc_row("Answered blind only", agg.forced_blind_only),
                    fc_row("Answered SURE", agg.confident),
                    fc_row("Answered UNSURE", agg.unsure),
                    fc_row("INVERTED channels (agreement is evidence AGAINST)", agg.inverted)])

    def bar(hits: int, n: int) -> str:
        pct = int(round(100 * hits / n)) if n else 0
        return (f"<span class='bar'><span style='width:{pct}%'></span></span> "
                f"<span class='n'>{hits}/{n}</span>")

    sig = "".join(f"<tr><td>{esc(k)}</td><td>{bar(h, n)}</td></tr>"
                  for k, (h, n) in sorted(agg.per_signification.items(),
                                          key=lambda kv: (kv[1][0] / kv[1][1]) if kv[1][1] else 1))
    life = "".join(f"<tr><td>{esc(k)}</td><td>{bar(h, n)}</td></tr>"
                   for k, (h, n) in sorted(agg.per_life_fact.items(),
                                           key=lambda kv: (kv[1][0] / kv[1][1]) if kv[1][1] else 1))
    chap = "".join(f"<tr><td>{esc(k)}</td><td class='n'>{v}</td></tr>"
                   for k, v in agg.chapter_wrong.items())
    barnum = "".join(f"<tr><td>{esc(k)}</td><td class='n'>{v}</td></tr>"
                     for k, v in agg.chapter_barnum.items())
    quotes = "".join(
        f"<h3>{esc(q)}</h3>" + "".join(f"<blockquote>{esc(t)}</blockquote>" for t in texts)
        for q, texts in agg.free_text.items())
    per_chart = "".join(
        f"<tr><td class='mono'>{esc(c.chart_key or '—')}</td>"
        f"<td>{esc(c.context)}</td><td class='n'>{c.forced.hits}/{c.forced.n}</td>"
        f"<td class='n'>{c.event_houses.top_grade}/{c.event_houses.events}</td>"
        f"<td class='n'>{c.spine.near_boundary}/{c.spine.events}</td></tr>" for c in cards)
    notes = "".join(f"<li>{esc(n)}</li>" for n in agg.notes)

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Feedback scorecard</title><style>
:root{{--ink:#1b1e28;--muted:#5a6070;--rule:#e2ddd4;--paper:#f7f5f1;--accent:#2f3e8c;
--warn:#8a5a16;--warnbg:#faf0de}}
@media(prefers-color-scheme:dark){{:root{{--ink:#e9e7e2;--muted:#9ba1b2;--rule:#2b2f3a;
--paper:#12141a;--accent:#94a2f0;--warn:#e0a44e;--warnbg:#2c2314}}}}
body{{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.6 system-ui,-apple-system,'Segoe UI',sans-serif}}
main{{max-width:52rem;margin:0 auto;padding:2rem 1.2rem 5rem}}
h1{{font-size:1.6rem;margin:0 0 .3rem}}h2{{font-size:1.05rem;margin:2.2rem 0 .5rem;
letter-spacing:.04em;text-transform:uppercase;color:var(--accent)}}
h3{{font-size:.92rem;margin:1rem 0 .3rem;color:var(--muted)}}
table{{border-collapse:collapse;width:100%;margin:.5rem 0;font-size:.94rem}}
td,th{{text-align:left;padding:.4rem .6rem;border-bottom:1px solid var(--rule);
vertical-align:middle}}
.n{{font-variant-numeric:tabular-nums;white-space:nowrap}}
.mono{{font-family:ui-monospace,Menlo,monospace;font-size:.8rem}}
.bar{{display:inline-block;width:8rem;height:.55rem;background:var(--rule);
border-radius:3px;overflow:hidden;vertical-align:middle;margin-right:.5rem}}
.bar>span{{display:block;height:100%;background:var(--accent)}}
.notes{{background:var(--warnbg);border-left:3px solid var(--warn);padding:.8rem 1rem;
margin:1rem 0;border-radius:3px}}.notes li{{margin:.3rem 0}}
blockquote{{margin:.4rem 0;padding:.5rem .8rem;border-left:2px solid var(--rule);
color:var(--muted);font-style:italic}}
.sub{{color:var(--muted);margin:0 0 1rem}}
</style></head><body><main>
<h1>Feedback scorecard</h1>
<p class="sub">{agg.charts} chart(s) scored &middot; {agg.blind_charts} answered before the
reading. Read the caveats first &mdash; a number here quoted without them is the exact mistake
this project's validation record exists to prevent.</p>
{f'<div class="notes"><ul>{notes}</ul></div>' if notes else ''}
<h2>Forced choice &mdash; chance is 0.5</h2>
<table><tr><th>Pool</th><th>Hits</th><th>Rate</th><th>p</th></tr>{rows}</table>
<h2>Dated events vs the periods for their own matter</h2>
<p class="sub">{agg.event_top_grade}/{agg.event_scored} landed in a top-graded period.
No pooled p-value: each chart's null is its own set of per-house base rates.</p>
<h2>By reading &mdash; the improvement list, worst first</h2>
<table>{sig or '<tr><td>nothing scored yet</td></tr>'}</table>
<h2>By life fact &mdash; counts, not p-values</h2>
<table>{life or '<tr><td>nothing scored yet</td></tr>'}</table>
<h2>Chapters readers called wrong</h2>
<table>{chap or '<tr><td>none reported</td></tr>'}</table>
<h2>Chapters readers said were true of everyone</h2>
<table>{barnum or '<tr><td>none reported</td></tr>'}</table>
<h2>Per chart</h2>
<table><tr><th>Chart</th><th>Answered</th><th>Forced</th><th>Events</th>
<th>Spine</th></tr>{per_chart}</table>
<h2>What people wrote</h2>
{quotes or '<p class="sub">nothing yet</p>'}
</main></body></html>"""


def _card_json(c: ChartScorecard) -> dict[str, Any]:
    d = asdict(c)
    # `asdict` drops @property values, so every nested ForcedChoice loses `rate` and
    # `weighted_rate`. Re-adding them for some pools and not others left a JSON consumer
    # looking at four pools with three different shapes.
    for name in ("forced", "inverted", "confident", "unsure"):
        pool = getattr(c, name)
        d[name]["rate"] = pool.rate
        d[name]["weighted_rate"] = pool.weighted_rate
    return d


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Score the stored chart feedback against what the engine said.")
    ap.add_argument("--database-url", default="",
                    help="SQLAlchemy async URL; defaults to settings.DATABASE_URL")
    ap.add_argument("--chart-key", default="", help="score one nativity only")
    ap.add_argument("--limit-charts", type=int, default=500)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--html", default="", metavar="PATH",
                    help="write a self-contained operator page (a FILE, never a route — see "
                         "render_aggregate_html)")
    args = ap.parse_args(argv)

    cards, agg = asyncio.run(load_and_score(args.database_url, chart_key=args.chart_key,
                                            limit_charts=args.limit_charts))
    if args.html:
        import pathlib as _pl
        _pl.Path(args.html).write_text(render_aggregate_html(agg, cards), encoding="utf-8")
        print(f"wrote {args.html}")
    if args.json:
        print(json.dumps({"charts": [_card_json(c) for c in cards],
                          "aggregate": asdict(agg)}, indent=2, default=str))
    elif not args.html:
        print(render_aggregate(agg))
        if args.chart_key and cards:
            print()
            print("this chart:", cards[0].headline)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
