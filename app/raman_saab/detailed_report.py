"""Detailed report — the engine's full reading as ONE honest document.

This composes what already exists into a single comprehensive report and adds the piece nothing
else joins in: the **population-calibration honesty overlay** woven through every house. For each
bhava it prints Raman's UNCHANGED verdict (the synthesis line — D1 promise, navamsa fruit,
matter-varga, activation windows, live transits) AND, beneath it, how that verdict sits against
16,450 real charts — the percentile, how common the exact reading is, and the atlas-proven INVERTED
warnings (H3 courage, H12 incarceration). It also carries the numeric Ayurdaya span, the fired
longevity combinations, the HTJAH-II career line, the Deeptadi avasthas and the Jaimini Karakamsa
soul reading.

The report is deliberately two-voiced: the doctrine speaks (faithful to Raman), and then the
instrument discloses its own information content (empirical, tagged NOT-Raman). Per the program's
governance the verdict path is untouched — this is assembly + disclosure, never re-judgment.

Usage:
    from app.raman_saab.detailed_report import build_detailed_report, to_markdown
    print(to_markdown(build_detailed_report(birth)))
    # or via the CLI:  py -3.12 -m app.raman_saab --name ... --format report
"""
from __future__ import annotations

from dataclasses import dataclass, replace as _dc_replace
from typing import Final, Optional

from app.raman_saab import (
    render_dasamsa, render_dwadasamsa, render_general_varga, render_matter_varga,
    render_navamsa, render_pitru, render_saptamsa, render_siddhamsa, render_soul,
    render_trimsamsa,
)
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges.calibrated_reading import (
    _VALIDITY,
    CalibratedHouseReading,
    build_calibrated_reading,
)
from app.raman_saab.chart.model import PlanetPos
from app.raman_saab.doctrine.synthesis_rules import (
    FiredInsight,
    descriptive_rules,
    detect_synthesis,
)
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.judges.chart_overview import ChartOverview, chart_overview
from app.raman_saab.judges.dasamsa_career_reading import build_dasamsa_career_reading
from app.raman_saab.judges.dwadasamsa_parents_reading import build_dwadasamsa_parents_reading
from app.raman_saab.judges.navamsa_marriage_reading import build_navamsa_marriage_reading
from app.raman_saab.judges.saptamsa_reading import build_saptamsa_children_reading
from app.raman_saab.judges.siddhamsa_education_reading import build_siddhamsa_education_reading
from app.raman_saab.judges.trimsamsa_health_reading import build_trimsamsa_health_reading
from app.raman_saab.judges.general_varga_reading import build_general_varga_reading
from app.raman_saab.judges.house_template import HouseProforma
from app.raman_saab.judges.matter_varga_dashboard import (
    MatterVargaDashboard,
    build_matter_varga_dashboard,
)
from app.raman_saab.judges.matter_varga_reading import build_matter_varga_reading
from app.raman_saab.judges.pitru_dosha_reading import (
    PitruDoshaReading,
    build_pitru_dosha_reading,
)
from app.raman_saab.judges.soul_reading import SoulReading, build_soul_reading
from app.raman_saab.primitives import ashtakavarga, ayurdaya, nakshatra_signature
from app.raman_saab.primitives import transits as tr
from app.raman_saab.primitives.balarishta import BalarishtaState
from app.raman_saab.proforma import read_chart
from app.raman_saab.reading_timeline import DashaTimeline, reading_timeline
from app.raman_saab.synthesis import Synthesis, synthesize

_HOUSE_NAME = {1: "Self/Body", 2: "Wealth/Family", 3: "Siblings/Courage", 4: "Mother/Home",
               5: "Children/Mind", 6: "Health/Enemies", 7: "Spouse/Partnership", 8: "Longevity",
               9: "Father/Fortune", 10: "Career", 11: "Gains", 12: "Loss/Moksha/Spirituality"}

_SIGN_NAME = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
              "Sagittarius", "Capricorn", "Aquarius", "Pisces")


def _jd_ym(jd: float) -> str:
    """Julian Day -> 'YYYY-MM' (calendar month, GREG_CAL) — display-only, per CLAUDE.md's
    'JD arithmetic for calendar dates' rule (no datetime.timedelta anywhere upstream)."""
    import swisseph as swe
    y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y)}-{int(m):02d}"


def _vedha_word(frac: float) -> str:
    """Plain word for a Gochara outlook window's sampled Vedha-obstruction share — the fraction
    is a coarse, week-resolution estimate (see `GocharaSegment`), so it is deliberately reported
    as a word, not a false-precision percentage, in the reader-facing table."""
    if frac >= 0.7:
        return "sustained — mostly cancelled across this window"
    if frac >= 0.4:
        return "frequent"
    if frac >= 0.15:
        return "occasional"
    if frac > 0:
        return "rare"
    return "none sampled"


_MONTH_ABBR: Final[tuple[str, ...]] = (
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _jd_month_year(jd: float) -> str:
    """Julian Day -> 'Mon YYYY' (e.g. 'Mar 2024') — the plain, reader-facing date format for the
    Gochara outlook. Month-only, not day, matching the ~week sampling-resolution honesty note
    (see `gochara_timeline`'s docstring) — showing an exact day would overclaim precision this
    computation doesn't have."""
    import swisseph as swe
    y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
    return f"{_MONTH_ABBR[int(m)]} {int(y)}"


def _outlook_window_label(start_jd: float, end_jd: float) -> str:
    """'Mar 2024 to Oct 2025', or just 'Apr 2019' when a genuinely-real but short window (>=25
    days, past the retrograde-station noise floor) rounds to the same displayed month at both
    ends — avoids the misleading 'Apr 2019 to Apr 2019' (reads as zero-length) at month
    resolution."""
    lo, hi = _jd_month_year(start_jd), _jd_month_year(end_jd)
    return lo if lo == hi else f"{lo} to {hi}"


def _outlook_strength_word(bav: int | None) -> str:
    """Plain strength word for a favourable Gochara window, from that planet's own Ashtakavarga
    bindus in the transited sign (HPA-34:127: 4+ bindus is Raman's own threshold for a stronger
    result). Rahu/Ketu carry no Ashtakavarga in classical doctrine (bav is None) — reported as
    plain "supportive", not scored, rather than guessing a number that isn't there."""
    if bav is None:
        return "supportive"
    if bav >= 6:
        return "strongly supportive"
    if bav >= 4:
        return "supportive"
    return "mildly supportive"

#: lay-reader life-area names (for the plain-language bhukti summary).
_PLAIN_AREA = {1: "self & health", 2: "wealth & family", 3: "courage & siblings",
               4: "home & mother", 5: "children & creativity", 6: "health & rivals",
               7: "marriage & partnership", 8: "longevity", 9: "fortune & father",
               10: "career", 11: "gains", 12: "losses & spirituality"}

#: hand-written (never templated) plain-English lines for each of the 12-matter dashboard's
#: matters, by verdict — the actual content of "Your Reading". Deliberately warm, honest, and
#: free of jargon; afflicted lines name real friction without alarm; this is prose written for
#: a person, not a restatement of a technical verdict.
_PLAIN_MATTER: dict[str, dict[str, str]] = {
    "wealth": {
        "favourable": "money and material comfort come to you relatively easily, and your "
                      "resources tend to grow over time",
        "afflicted": "financial ease may take real effort on your part — steady habits will "
                     "matter more than luck here",
        "mixed": "your finances show a real mix of ease and effort — some years flow, others "
                 "ask for discipline"},
    "siblings": {
        "favourable": "you share a warm, supportive bond with your brothers and sisters",
        "afflicted": "relationships with siblings may carry some friction or distance at times",
        "mixed": "your bond with siblings runs hot and cold — close at times, strained at "
                 "others"},
    "mother": {
        "favourable": "your relationship with your mother, and your sense of home, tend to be "
                      "a genuine source of comfort",
        "afflicted": "home life or your bond with your mother may need patience and conscious "
                     "care",
        "mixed": "home and your mother's influence bring both comfort and occasional friction"},
    "property": {
        "favourable": "property, land and material assets tend to work out favourably for you "
                      "over time",
        "afflicted": "property matters — buying, holding or inheriting land or a home — may "
                     "involve extra complication",
        "mixed": "property dealings show a mixed pattern — real gains alongside real "
                 "complications"},
    "children": {
        "favourable": "the chart favours ease and joy around children",
        "afflicted": "this chart shows real strain around children — fertility, timing, or the "
                     "parent-child bond may ask for patience. This is one of the more sensitive "
                     "readings here and deserves a compassionate, unhurried view, not alarm",
        "mixed": "children bring both joy and real challenge in this chart — a mixed but not "
                 "unusual pattern"},
    "marriage": {
        "favourable": "marriage and partnership read favourably — a supportive, workable bond "
                      "is indicated",
        "afflicted": "marriage may need real effort and patience — the chart shows genuine "
                     "friction to work through, not a smooth path",
        "mixed": "marriage shows both real warmth and real friction — a genuine partnership, "
                 "not an easy one"},
    "father": {
        "favourable": "your relationship with your father, and your broader sense of fortune, "
                      "read as a genuine asset",
        "afflicted": "your bond with your father, or your sense of fortune, may carry some "
                     "distance or difficulty",
        "mixed": "fortune and your father's influence bring both support and occasional "
                 "strain"},
    "career": {
        "favourable": "career and public standing read strongly — recognition and steady "
                      "progress are indicated",
        "afflicted": "career may involve real struggle — slower recognition or harder-won "
                     "progress than you'd like",
        "mixed": "career shows both real opportunity and real obstacles — success here takes "
                 "deliberate effort"},
    "comforts": {
        "favourable": "material comforts and the pleasures of life come easily to you",
        "afflicted": "comfort and ease may need to be earned rather than given",
        "mixed": "comfort in life is uneven — some abundance, some austerity"},
    "spiritual": {
        "favourable": "you carry a genuine pull toward spiritual life and inner growth",
        "afflicted": "spiritual life may develop later, or through real struggle rather than "
                     "ease",
        "mixed": "your spiritual path shows both genuine seeking and real obstacles"},
    "education": {
        "favourable": "learning comes naturally to you, and formal education tends to go well",
        "afflicted": "education may involve real struggle — interrupted schooling or hard-won "
                     "qualifications",
        "mixed": "your educational path shows both natural ability and real interruption"},
    "health": {
        "favourable": "overall vitality and physical resilience read as a genuine strength",
        "afflicted": "health needs real attention — this chart does not favour taking your "
                     "wellbeing for granted",
        "mixed": "health shows both real resilience and real vulnerability — worth ongoing "
                 "attention, not alarm"},
}

#: how each period-lord's classical theme reads in plain English (for "Right now").
_PLANET_THEME: dict[str, str] = {
    "Sun": "confidence, authority and recognition", "Moon": "emotional life, home and the public",
    "Mars": "action, courage and drive", "Mercury": "communication, learning and business",
    "Jupiter": "growth, wisdom and expanding opportunity",
    "Venus": "relationships, comfort and creativity",
    "Saturn": "discipline, patience and long-term effort",
    "Rahu": "ambition and unconventional drive", "Ketu": "detachment and inner reflection",
}

#: how the 12 matters group into a few readable life-domain paragraphs.
_PLAIN_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Money, property and comfort", ("wealth", "property", "comforts")),
    ("Family and home", ("mother", "father", "siblings")),
    ("Career and learning", ("career", "education")),
    ("Relationships and children", ("marriage", "children")),
    ("Health and inner life", ("health", "spiritual")),
)

#: plain-English gloss for every signification key (doctrine/significations.py) — so "Your
#: Reading" never leaks a Sanskrit or technical term (e.g. "poorvapunya", "coverture").
#: Any key not listed falls back to a simple underscore-to-space conversion.
_SIGNIFICATION_PLAIN: dict[str, str] = {
    "self": "your sense of self", "body": "physical vitality", "health": "health",
    "wealth": "wealth", "family": "family life", "speech": "speech and communication",
    "vision": "eyesight", "siblings": "siblings", "courage": "courage and drive",
    "short_journeys": "short journeys", "ear_throat": "ear and throat health",
    "mother": "your bond with your mother", "happiness": "domestic happiness",
    "education": "education", "vehicles": "vehicles and conveyances",
    "property": "property and land", "home_comforts": "comfort at home",
    "children": "children", "intellect": "intellect and reasoning",
    "poorvapunya": "merit carried from the past",
    "enemies_disease": "resistance to illness and rivals", "accidents": "accident-proneness",
    "debts": "debt and financial obligations", "enemies": "open rivals and conflict",
    "disease_chronic": "resistance to chronic illness",
    "spouse": "your spouse", "marital_happiness": "happiness in marriage",
    "virility": "vitality and drive", "coverture": "security within marriage",
    "wealth_through_marriage": "wealth gained through marriage",
    "partnership": "partnership and cooperation",
    "longevity": "longevity", "death": "life-span", "legacies": "inheritance",
    "sudden_gains": "sudden windfalls",
    "father": "your bond with your father", "fortune": "fortune and luck",
    "dharma": "sense of purpose", "higher_learning": "higher education",
    "long_journeys": "travel abroad",
    "career": "career", "profession_authority": "authority in your career",
    "profession_trade": "career in trade or business",
    "profession_learned": "career in a learned profession",
    "profession_labour": "career built on hands-on work",
    "status_honour": "public standing and honour",
    "gains": "gains and income", "elder_siblings": "elder siblings",
    "friends": "friendships", "acquisitions": "acquiring possessions",
    "loss_moksha": "release and letting go", "expenditure": "spending",
    "foreign_residence": "living abroad", "moksha": "spiritual liberation",
    "incarceration": "confinement", "left_eye": "left-eye health",
}


def _plain_signification(key: str) -> str:
    return _SIGNIFICATION_PLAIN.get(key, key.replace("_", " "))

#: one-line plain meaning of each fructification grade (shown once as a legend).
_TIER_MEANING = {
    "par excellence": "full, strong results — both period-lords reinforce the house",
    "ordinary": "normal results — both lords touch it, but do not reinforce",
    "limited": "slight results — only the current sub-period (bhukti) lord touches it",
    "feeble": "faint results — only the major-period (Mahadasha) lord touches it",
}


#: plain-language glossary — ONE source of truth, consumed by both renderers.
GLOSSARY: dict[str, str] = {
    "rasi": "the main birth chart (the 12 zodiac signs and where the planets sit in them)",
    "bhava": "a house — one of the 12 life-areas of the chart",
    "navamsa": "the 1/9th divisional chart; Raman treats it as the test of whether a promise is "
               "actually delivered",
    "karaka": "the natural significator of a matter (e.g. Jupiter for children, Venus for marriage)",
    "lord": "the planet that rules a house's sign, and therefore carries that house's affairs",
    "Ashtakavarga": "a bindu (dot) scoring system; more bindus in a sign = more support there. "
                    "Raman rates it corroborative, not decisive",
    "vargottama": "a planet in the same sign in the birth chart and the navamsa — doubly strong",
    "Arudha Lagna": "the chart's public image — how life appears to others, as distinct from "
                    "what it is",
    "Karakamsa": "the navamsa sign of the Atmakaraka — the Jaimini soul axis",
    "Upapada": "the marriage/spouse image point",
    "Sade-Sati": "Saturn's ~7.5-year passage over and around the natal Moon",
    "maraka": "literally 'killer' — a planet or period the classics associate with the end of life",
    "Balarishta": "classical combinations for early-childhood danger, and their cancellations",
    "Kuja dosha": "the 'Mars affliction' for marriage. NOTE: tested on 2,322 real charts by this "
                  "project it did NOT distinguish divorced from long-married (odds ratio 1.09)",
    "Deeptadi avastha": "each planet's result-state (Deepta = blazing, Deena = wretched, etc.)",
    "Beeja / Kshetra": "the male and female fertility points",
    "Atmakaraka": "the planet at the highest degree — the 'soul indicator' in Jaimini",
    "par excellence": "full, strong results (both period-lords reinforce the house)",
    "Mahadasha": "a major planetary period in the Vimshottari system (years to decades)",
    "Antardasha": "a sub-period (bhukti) inside a Mahadasha",
    "Shadbala": "the classical six-fold strength measure (positional, directional, temporal, "
                "motional, natural, aspectual), totalled in rupas",
    "Gochara": "the current transits, read from the natal Moon. Raman: secondary, catalytic — "
               "conclusions rest on the dashas",
    "Vedha": "an obstruction point: a planet transiting the Vedha position cancels an otherwise "
             "favourable transit",
    "Ishta-Devata": "the guiding deity indicated by the Karakamsa (Jaimini)",
    "chara dasha": "Jaimini's sign-based period system, running parallel to Vimshottari",
    "Hora": "the D-2 divisional chart (wealth)",
}


@dataclass(frozen=True)
class SectionSpec:
    """One contracted report section: its id, stable output markers, and the version that
    introduced it. `md_marker` / `html_marker` are None when the section exists in only one
    renderer (e.g. the chart grids are HTML-only)."""
    section_id: str
    md_marker: str | None
    html_marker: str | None
    since: str


#: THE REPORT TEMPLATE CONTRACT (docs/raman_saab/REPORT_TEMPLATE.md). Append-only: rows may be
#: ADDED (with a new `since`), but existing rows must never be removed, renamed, or reordered —
#: tests/raman_saab/test_report_template_contract.py enforces both renderers emitting every marker
#: in this order, and that the v1 prefix is byte-stable.
SECTION_CONTRACT: tuple[SectionSpec, ...] = (
    SectionSpec("title", "# Detailed reading", 'class="name"', "v1"),
    # v5 (2026-07-26, conscious amendment): "Your Reading" inserted right after the title — the
    # ONE deliberate exception to "append at the end". Every prior amendment (v2/v3/v4) only
    # ever grew the list downward; this one must come FIRST, because it exists specifically to
    # be the plain-English answer a reader meets before any technical section, including the
    # report's own self-referential "Information content" statistics. _FROZEN in the contract
    # test was reordered to match, in the same commit, per the procedure.
    SectionSpec("plain_reading", "## Your Reading", 'id="plain-reading"', "v5"),
    SectionSpec("now_box", None, 'class="nowbox"', "v1"),
    SectionSpec("info_content", "## Information content of this reading", 'class="infobox"', "v1"),
    SectionSpec("stands_out", "## What stands out in this chart", 'id="stands-out"', "v1"),
    SectionSpec("dashboard", "## The twelve matters at a glance", 'id="dashboard"', "v2"),
    SectionSpec("chart_signature", "## Chart signature", 'class="sig"', "v1"),
    SectionSpec("chart_grids", None, 'id="charts"', "v1"),
    SectionSpec("positions", "## Planetary positions", 'id="positions"', "v1"),
    SectionSpec("shadbala", "## Shadbala", 'id="shadbala"', "v2"),
    SectionSpec("yogas", "## Yogas present in this chart", 'id="yogas"', "v1"),
    SectionSpec("ashtakavarga", "## Ashtakavarga", 'id="sav"', "v1"),
    SectionSpec("houses", "## House-by-house reading", 'id="houses"', "v1"),
    SectionSpec("longevity", "## Longevity", 'id="longevity"', "v1"),
    SectionSpec("maraka", "## The maraka scheme", 'id="maraka"', "v2"),
    SectionSpec("timeline", "## Life-narrative (Vimshottari Dasha)", 'id="timeline"', "v1"),
    SectionSpec("gochara", "## Current transits (Gochara", 'id="gochara"', "v2"),
    # v6 (2026-07-26, conscious amendment): inserted right after Gochara, since it cross-
    # references the Life-narrative (timeline) and Gochara sections directly above it — the
    # natural narrative position, the same precedent as v2/v3 mid-document insertions.
    SectionSpec("dasha_transit", "## Dasha x Transit confluence", 'id="dasha-transit"', "v6"),
    SectionSpec("divisional", "## Divisional deep-reads (Shodasavarga)", 'id="vargas"', "v1"),
    SectionSpec("career", "## Career (HTJAH-II", 'id="career"', "v1"),
    SectionSpec("deeptadi", "## Deeptadi avasthas", 'id="deeptadi"', "v1"),
    SectionSpec("karakamsa", "## Jaimini Karakamsa", 'id="karakamsa"', "v1"),
    SectionSpec("soul", "## Soul & destiny", 'id="soul"', "v2"),
    SectionSpec("pitru", "## Pitru dosha", 'id="pitru"', "v2"),
    # v3 (2026-07-25, conscious amendment): inserted BEFORE glossary so the reference material
    # stays last; _FROZEN in the contract test was amended in the same commit per the procedure.
    SectionSpec("synthesis", "## Integrated insights", 'id="synthesis"', "v3"),
    SectionSpec("glossary", "## Glossary", 'id="glossary"', "v1"),
    # v4 (2026-07-26, conscious amendment): the capstone integration, appended LAST — after
    # reference material — since it distils sections that appear throughout the whole document.
    SectionSpec("nichod", "## Nichod", 'id="nichod"', "v4"),
)

#: The HTML renderer's document order (the signature chips live in the page header, and the
#: chart grids/now-box are HTML-only). Same append-only rule applies.
HTML_SECTION_ORDER: tuple[str, ...] = (
    "title", "plain_reading", "chart_signature", "now_box", "info_content", "stands_out",
    "dashboard",
    "chart_grids", "positions", "shadbala", "yogas", "ashtakavarga", "houses", "longevity",
    "maraka", "timeline", "gochara", "dasha_transit", "divisional", "career", "deeptadi",
    "karakamsa", "soul", "pitru", "synthesis", "glossary", "nichod",
)


@dataclass(frozen=True)
class InfoContent:
    """How much of this reading actually distinguishes THIS chart (the honesty headline)."""
    total: int
    modal_verdict: str
    modal_count: int
    near_universal: int
    inverted: int
    distinctive: int
    inverted_locations: tuple[str, ...] = ()   # e.g. ("H3 courage", "H12 incarceration")

    @property
    def sentence(self) -> str:
        where = f" ({', '.join(self.inverted_locations)})" if self.inverted_locations else ""
        return (
            f"{self.total} readings. {self.modal_count} return the single most common verdict "
            f"({self.modal_verdict}). {self.near_universal} are near-universal — held by half the "
            f"population or more. {self.inverted} sit on channels this project's validation "
            f"program proved run backwards{where} — treat any house driven by one of these with "
            f"maximal skepticism. {self.distinctive} are genuinely distinctive. This is a "
            f"disclosure about the method's output, not a statement about a life.")


def _all_entries(calibration: dict[int, CalibratedHouseReading]):
    """(house, entry) for every calibrated signification, house order."""
    for house in sorted(calibration):
        for e in calibration[house].entries:
            yield house, e


def information_content(calibration: dict[int, CalibratedHouseReading]) -> InfoContent:
    """Aggregate the calibration overlay into the report's honesty headline."""
    pairs = list(_all_entries(calibration))
    scored = [(h, e) for h, e in pairs if e.favourability_percentile is not None]
    counts: dict[str, int] = {}
    for _h, e in scored:
        key = f"{e.verdict} ({e.degree})"
        counts[key] = counts.get(key, 0) + 1
    modal_verdict, modal_count = max(counts.items(), key=lambda kv: kv[1]) if counts else ("-", 0)
    inv_locs = tuple(f"H{h} {e.signification}" for h, e in pairs if e.inverted_warning)
    return InfoContent(
        total=len(pairs), modal_verdict=modal_verdict, modal_count=modal_count,
        near_universal=sum(1 for _h, e in scored if (e.band_share or 0) >= 0.5),
        inverted=sum(1 for _h, e in pairs if e.inverted_warning),
        distinctive=sum(1 for _h, e in scored if e.rarity != "common"),
        inverted_locations=inv_locs,
    )


def distinctive_entries(calibration: dict[int, CalibratedHouseReading], n: int = 7):
    """The n readings that most distinguish this chart — furthest from the population midpoint,
    rare readings first. Returns [(house, entry)] ranked. Pure information content, not prediction."""
    scored = [(h, e) for h, e in _all_entries(calibration)
              if e.favourability_percentile is not None]
    scored.sort(key=lambda he: (-(0 if he[1].rarity == "common" else 1),
                                -abs(he[1].favourability_percentile - 0.5)))
    return tuple(scored[:n])


def driver_entry(reading: CalibratedHouseReading, rollup: str):
    """The CalibratedEntry that drove the house rollup (first signification sharing the
    house's verdict) — the engine grades a bhava by its WORST decided matter, so one afflicted
    signification makes the whole house read afflicted. Returning the entry (not just its name)
    lets a caller check whether that specific driver sits on an atlas-proven inverted channel."""
    hits = [e for e in reading.entries if e.verdict == rollup]
    return hits[0] if hits else None


def rollup_driver(reading: CalibratedHouseReading, rollup: str) -> str | None:
    """Which signification drove the house rollup (name only). See ``driver_entry``."""
    e = driver_entry(reading, rollup)
    return e.signification if e else None


ROLLUP_RULE = ("A bhava is graded by its weakest decided matter — one afflicted signification "
               "makes the whole house read afflicted even when the rest are sound.")


@dataclass(frozen=True)
class TenorSplit:
    """How a house's significations actually split, independent of the weakest-link headline.
    Answers the reader's real question directly: is this house MOSTLY favourable with one sore
    spot, or genuinely afflicted throughout?"""
    favourable: int
    afflicted: int
    mixed: int
    total: int
    majority: str            # "favourable" | "afflicted" | "mixed" | "insufficient-evidence"


def signification_tenor_split(reading: CalibratedHouseReading) -> TenorSplit:
    """Count each house's significations by their OWN verdict (never re-judged) and report the
    majority tenor — the counterweight to the single-worst-wins headline."""
    counts = {"favourable": 0, "afflicted": 0, "mixed": 0}
    for e in reading.entries:
        if e.verdict in counts:
            counts[e.verdict] += 1
    decided = sum(counts.values())
    if decided == 0:
        majority = "insufficient-evidence"
    else:
        top = max(counts.values())
        tied = [k for k, v in counts.items() if v == top]
        majority = tied[0] if len(tied) == 1 else "mixed"   # a genuine tie reads as mixed
    return TenorSplit(favourable=counts["favourable"], afflicted=counts["afflicted"],
                      mixed=counts["mixed"], total=len(reading.entries), majority=majority)


def tenor_note(split: TenorSplit, rollup: str) -> str | None:
    """A plain sentence when the majority tenor disagrees with the weakest-link headline —
    None when they already agree (no need to belabour a house that is genuinely afflicted)."""
    if split.total <= 1 or split.majority == rollup or split.majority == "insufficient-evidence":
        return None
    if split.majority == "favourable":
        return (f"{split.favourable} of {split.total} sub-readings are actually favourable — "
                f"the headline follows the single weakest decided matter, not the majority.")
    if split.majority == "afflicted":
        return (f"{split.afflicted} of {split.total} sub-readings are actually afflicted — "
                f"the headline follows the single weakest decided matter, not the majority.")
    # majority == "mixed": either a genuine mixed-verdict plurality, or signification_tenor_split
    # resolved a favourable/afflicted TIE to "mixed" — the two need different wording.
    if split.mixed > 0 and split.mixed >= split.favourable and split.mixed >= split.afflicted:
        return (f"{split.mixed} of {split.total} sub-readings are genuinely mixed — the "
                f"headline follows the single weakest decided matter, not the majority.")
    if split.favourable == split.afflicted and split.favourable > 0:
        return (f"an even split ({split.favourable} favourable vs {split.afflicted} afflicted) "
                f"— the headline follows the single weakest decided matter, not a genuine "
                f"consensus either way.")
    return None


def graded_buckets(tp, chart) -> tuple[bool, dict[str, list]]:
    """(AD-associated-with-MD, {tier: [ActivatedHouseReading]}) for one bhukti.

    Hoisted here so BOTH renderers consume one implementation — the doctrine grading must never
    be duplicated in presentation code where the two could silently drift apart.
    """
    from app.raman_saab.primitives import vimshottari as vd
    maha, antar = tp.period.maha, tp.period.antar
    associated = antar is not None and vd.lords_associated(chart, maha, antar)
    buckets: dict[str, list] = {"par excellence": [], "ordinary": [], "limited": [], "feeble": []}
    for a in tp.activated:
        tier = vd.bhukti_tier(a.md_activates, a.antar_activates, associated)
        if tier:
            buckets[tier].append(a)
    return associated, buckets


def planet_rows(chart: RamanChart) -> tuple[tuple[str, PlanetPos], ...]:
    """Planets in canonical order for the positions table (a reading must be checkable)."""
    order = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    return tuple((n, chart.planets[n]) for n in order if n in chart.planets)


def _human_list(items: list[str]) -> str:
    """Join names for prose: 'a', 'a and b', 'a, b and c'."""
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def plain_bhukti_summary(rows, associated: bool) -> str:
    """A lay-reader gloss of one bhukti: its overall intensity (from the association tier) and the
    life-areas under strain (the afflicted houses at that tier, named). A plain restatement of
    Raman's reading — never a prediction of real events."""
    from app.raman_saab.primitives.vimshottari import bhukti_tier
    top = "par excellence" if associated else "ordinary"
    strained = sorted({(a.house, _PLAIN_AREA[a.house]) for a in rows
                       if a.natal_verdict == "afflicted"
                       and bhukti_tier(a.md_activates, a.antar_activates, associated) == top})
    intensity = ("a strong, well-supported stretch" if associated
                 else "a steady, ordinary stretch")
    s = f"In plain terms: {intensity}; most matters run supportively"
    if strained:
        names = [name for _, name in strained]
        s += f", but {_human_list(names)} {'meets' if len(names) == 1 else 'meet'} friction"
    return s + "."

def _matter(m: str):
    return lambda chart: build_matter_varga_reading(chart, m)


def _general(n: int):
    return lambda chart: build_general_varga_reading(chart, n)


#: Shodasavarga deep-reads: (label, build_reading(chart), render.to_text(reading)).
#: The FULL sixteen minus D-1 (which is the main reading): the six matter deep-reads that
#: shipped first, then D2/D3/D4 (after D-12), D16/D20 (after D-30), D27/D40/D45/D60 (after D-24).
_DIVISIONAL: tuple[tuple[str, object, object], ...] = (
    ("D-9 Marriage (Navamsa)", build_navamsa_marriage_reading, render_navamsa.to_text),
    ("D-10 Career (Dasamsa)", build_dasamsa_career_reading, render_dasamsa.to_text),
    ("D-7 Children (Saptamsa)", build_saptamsa_children_reading, render_saptamsa.to_text),
    ("D-12 Parents (Dwadasamsa)", build_dwadasamsa_parents_reading, render_dwadasamsa.to_text),
    ("D-2 Wealth (Hora)", _matter("wealth"), render_matter_varga.to_text),
    ("D-3 Siblings (Drekkana)", _matter("siblings"), render_matter_varga.to_text),
    ("D-4 Property (Chaturthamsa)", _matter("property"), render_matter_varga.to_text),
    ("D-30 Health (Trimsamsa)", build_trimsamsa_health_reading, render_trimsamsa.to_text),
    ("D-16 Comforts (Shodasamsa)", _matter("comforts"), render_matter_varga.to_text),
    ("D-20 Spiritual (Vimsamsa)", _matter("spiritual"), render_matter_varga.to_text),
    ("D-24 Education (Siddhamsa)", build_siddhamsa_education_reading, render_siddhamsa.to_text),
    ("D-27 Strength (Bhamsa)", _general(27), render_general_varga.to_text),
    ("D-40 Auspiciousness (Khavedamsa)", _general(40), render_general_varga.to_text),
    ("D-45 Character (Akshavedamsa)", _general(45), render_general_varga.to_text),
    ("D-60 Totality (Shashtiamsa)", _general(60), render_general_varga.to_text),
)


def _clean_box(text: str) -> str:
    """Drop a renderer's own ==== rule lines (we supply the markdown heading instead)."""
    return "\n".join(ln for ln in text.splitlines()
                     if not (ln.strip() and set(ln.strip()) <= {"="}))


def _divisional_sections(chart: RamanChart) -> tuple[tuple[str, str], ...]:
    """Full varga deep-reads; a varga that cannot be cast on this chart is skipped."""
    out: list[tuple[str, str]] = []
    for label, build, render in _DIVISIONAL:
        try:
            out.append((label, _clean_box(render(build(chart)))))
        except Exception:  # noqa: BLE001 — same silent-skip contract as synthesis
            continue
    return tuple(out)


@dataclass(frozen=True)
class ConfluenceWindow:
    """A stretch where the running Mahadasha or Antardasha LORD is, at the same time, undergoing
    its own favourable Gochara transit — Raman's own reason this matters (transits are secondary,
    catalytic to the Dasha, HTJAH-II:4679: "a good transit only delivers what the running period
    already permits") applied concretely: the clearest confirmation is when the period's own
    planet is well-placed by transit too. `role` is "MD" or "AD"; the overlap window is the
    INTERSECTION of the bhukti's bounds and the planet's own favourable Gochara segment — both
    already computed elsewhere in the report (DashaTimeline, gochara_outlook); nothing here is a
    new judgment, only an overlap of two existing computations."""
    planet: str
    role: str                    # "MD" | "AD"
    period_start_jd: float
    period_end_jd: float
    overlap_start_jd: float
    overlap_end_jd: float
    sign: int
    bav_bindus: int | None
    vedha_sample_fraction: float


def _dasha_transit_confluences(
    timeline: DashaTimeline, outlook: dict[str, tuple[tr.GocharaSegment, ...]],
) -> tuple[ConfluenceWindow, ...]:
    """Cross-reference the windowed Vimshottari timeline against the Gochara outlook: every
    stretch where a bhukti's MD or AD lord is ALSO, at the same time, in one of its own
    favourable Gochara windows. Only Jupiter/Saturn/Rahu/Ketu are tracked long-range (the same
    four `gochara_timeline` covers) — a bhukti whose lord is Sun/Moon/Mars/Mercury/Venus simply
    contributes no rows here, which the renderer states explicitly rather than implying an
    absence of support."""
    out: list[ConfluenceWindow] = []
    for tp in timeline.periods:
        p = tp.period
        for role, lord in (("MD", p.maha), ("AD", p.antar)):
            if lord is None or lord not in outlook:
                continue
            for seg in outlook[lord]:
                if not seg.gochara_good:
                    continue
                lo, hi = max(p.start_jd, seg.start_jd), min(p.end_jd, seg.end_jd)
                if lo < hi:
                    out.append(ConfluenceWindow(
                        planet=lord, role=role, period_start_jd=p.start_jd,
                        period_end_jd=p.end_jd, overlap_start_jd=lo, overlap_end_jd=hi,
                        sign=seg.sign, bav_bindus=seg.bav_bindus,
                        vedha_sample_fraction=seg.vedha_sample_fraction))
    out.sort(key=lambda c: c.overlap_start_jd)
    return tuple(out)


@dataclass(frozen=True)
class DetailedReport:
    """Everything the engine can say about one chart, plus the honesty overlay."""
    birth: BirthData
    chart: RamanChart                                # kept for pillars / positions / grading
    synthesis: Synthesis
    calibration: dict[int, CalibratedHouseReading]   # house -> per-signification calibration
    proformas: tuple[HouseProforma, ...]             # per-house lord + rule evidence (Raman's core)
    overview: ChartOverview                          # stronger frame, functional natures
    yogas: tuple[FiredYoga, ...]                     # fired yogas, each with its citation
    sav: dict[int, int]                              # Sarvashtakavarga bindus per sign
    info: InfoContent                                # the honesty headline
    distinctive: tuple[tuple[int, object], ...]      # (house, CalibratedEntry) most distinguishing
    balarishta: BalarishtaState | None
    dashboard: MatterVargaDashboard                  # the 12-matter executive verdict table
    soul: SoulReading                                # extended Jaimini soul/destiny reading
    pitru: PitruDoshaReading                         # ancestral screen (non-Raman provenance)
    gochara: tuple[tr.TransitRow, ...]               # transits at ref date, WITH Vedha/net
    gochara_outlook: dict[str, tuple[tr.GocharaSegment, ...]]  # Jupiter/Saturn/Rahu/Ketu, over time
    dasha_transit: tuple[ConfluenceWindow, ...]      # MD/AD lord x its own favourable transit
    maraka_period_now: bool                          # is the running period maraka-tier?
    insights: tuple[FiredInsight, ...]               # fired cross-feature synthesis rules
    longevity_years: float
    longevity_ymd: tuple[int, int, int]
    longevity_class: str
    divisional: tuple[tuple[str, str], ...]          # (label, full varga deep-read body)
    timeline: DashaTimeline                          # windowed Vimshottari MD -> AD narrative
    ref_jd: float                                    # the "now" anchor (on-date or today)
    window_back: int                                 # years of past shown
    window_forward: int                              # years of future shown
    nichod: "Nichod"                                 # the one deep-level integration of it all
    plain_reading: "PlainReading"                    # the plain-English reading, read FIRST


@dataclass(frozen=True)
class PlainReading:
    """'Your Reading' — the report's genuine plain-English answer, meant to be read FIRST,
    before any technical detail. Every clause is hand-written prose (never a templated
    restatement of a verdict string) built from the SAME already-computed verdicts the rest of
    the report shows — this is a translation, not a new judgment. No house numbers, no
    Sanskrit terms, no percentiles as the primary voice."""
    opening: str
    life_paragraphs: tuple[tuple[str, str], ...]     # (theme, paragraph)
    now: str
    notable: str
    closing: str


_EMPTY_PLAIN_READING: Final[PlainReading] = PlainReading(
    opening="", life_paragraphs=(), now="", notable="", closing="",
)


@dataclass(frozen=True)
class Nichod:
    """The report's final distillation — 'nichod', the concentrated essence squeezed from every
    section above into one deep-level read. NOTHING here is a new judgment: every clause
    selects, counts, or quotes something the rest of the report has already computed and
    disclosed (yogas from detect_yogas, the tally from the 12-matter dashboard, the split-status
    machinery from the house-by-house fix, the running period from the timeline, transits with
    Vedha already applied, a spotlighted cross-feature insight already fired). Presentation-only;
    the verdict path is never touched by, nor feeds, this composition."""
    identity: str              # Lagna, stronger frame, Atmakaraka, Karakamsa, birth nakshatra
    strength_profile: str      # strongest/weakest graha by Shadbala
    longevity: str             # band + years + Balarishta state
    yogas: str                 # fired yogas, named
    stands_out: str            # the chart's most distinctive readings
    matters_tally: str         # the 12-matter dashboard, tallied
    current_period: str        # running MD/AD + the houses it lights, tiered
    live_transits: str         # net-favourable count under Vedha, subordinate to the dasha
    spotlight: Optional[str]   # one live cross-feature synthesis insight, if any fired
    caution: Optional[str]     # split-status / inverted-channel flags on what's active NOW
    essence: str               # the single distilled paragraph knitting all of the above


_EMPTY_NICHOD: Final[Nichod] = Nichod(
    identity="", strength_profile="", longevity="", yogas="", stands_out="",
    matters_tally="", current_period="", live_transits="", spotlight=None, caution=None,
    essence="",
)


def build_nichod(r: DetailedReport) -> Nichod:
    """Assemble the Nichod from an already-fully-built DetailedReport (every input below is
    something the report renders elsewhere; this only selects, counts, and knits)."""
    from collections import Counter

    s, chart = r.synthesis, r.chart

    moon = chart.planets.get("Moon")
    nak = nakshatra_signature.signature_for(moon.nakshatra) if moon is not None else None
    nak_bit = f", Moon in {nak.name} (pada {moon.pada})" if nak is not None else ""
    identity = (f"{s.lagna} Lagna, {r.overview.stronger_frame.upper()} the stronger frame, "
               f"Atmakaraka {s.atmakaraka}, Karakamsa {s.karakamsa}{nak_bit}")

    sb = [(n, p.shadbala_rupas.total / 60.0) for n, p in chart.planets.items()
          if p.shadbala_rupas is not None]
    if sb:
        sb.sort(key=lambda kv: -kv[1])
        hi, lo = sb[0], sb[-1]
        strength_profile = (f"{hi[0]} is the strongest graha by Shadbala ({hi[1]:.1f} rupas); "
                           f"{lo[0]} the weakest ({lo[1]:.1f})")
    else:
        strength_profile = "Shadbala unavailable for this chart"

    y, mo, d = r.longevity_ymd
    bal_bit = ""
    if r.balarishta is not None:
        if r.balarishta.applies and not r.balarishta.cancelled:
            bal_bit = " (Balarishta applies)"
        elif r.balarishta.cancelled:
            bal_bit = " (Balarishta cancelled)"
    longevity = f"{r.longevity_class} band, about {round(r.longevity_years)} years{bal_bit}"

    if r.yogas:
        names = [yg.name for yg in r.yogas[:3]]
        extra = f" (+{len(r.yogas) - 3} more)" if len(r.yogas) > 3 else ""
        yogas = "; ".join(names) + extra
    else:
        yogas = "no encoded yoga fires on this chart"

    if r.distinctive:
        stands_out = "; ".join(f"H{h} {e.signification} ({e.favourability_percentile:.0%})"
                               for h, e in r.distinctive[:3])
    else:
        stands_out = "no signification strays far from the population midpoint"

    tally = Counter(en.verdict for en in r.dashboard.entries)
    matters_tally = (f"{tally.get('favourable', 0)} of {len(r.dashboard.entries)} matters read "
                     f"favourable, {tally.get('afflicted', 0)} afflicted"
                     + (f", {tally.get('mixed', 0)} mixed" if tally.get("mixed") else ""))

    caution_bits: list[str] = []
    cur_tp = next((tp for tp in r.timeline.periods
                  if tp.period.start_jd <= r.ref_jd < tp.period.end_jd), None)
    if cur_tp is not None:
        associated, buckets = graded_buckets(cur_tp, chart)
        tier = "par excellence" if associated else "ordinary"
        focus_houses = sorted({a.house for a in buckets[tier]})
        current_period = (f"{cur_tp.period.maha} MD / {cur_tp.period.antar or cur_tp.period.maha} "
                          f"AD, {tier}"
                          + (f" — lighting H{', H'.join(map(str, focus_houses))}"
                             if focus_houses else ""))
        for h in focus_houses:
            cal_h, mr_h = r.calibration.get(h), next(
                (m for m in s.matters if m.house == h), None)
            if cal_h is None or mr_h is None:
                continue
            note_h = tenor_note(signification_tenor_split(cal_h), mr_h.verdict)
            if note_h:
                caution_bits.append(f"H{h}: {note_h}")
            drv = driver_entry(cal_h, mr_h.verdict)
            if drv is not None and drv.inverted_warning:
                caution_bits.append(f"H{h}'s headline is driven by an atlas-proven INVERTED "
                                    f"channel ({drv.signification}) — treat with skepticism")
    else:
        current_period = "no running period resolved for this reference date"

    if r.gochara:
        fav = sum(1 for g in r.gochara if g.net_good)
        live_transits = (f"{fav} of {len(r.gochara)} current transits read net favourable "
                        f"(Vedha and Ashtakavarga already applied) — subordinate to the dasha")
    else:
        live_transits = "no transit data available for this chart"

    spotlight = None
    for ins in r.insights:
        if ins.rule.band == "raman" and "Life-narrative" in ins.rule.links:
            spotlight = f"{ins.rule.name} — {ins.detail}"
            break
    if spotlight is None and r.insights:
        top = r.insights[0]
        spotlight = f"{top.rule.name} — {top.detail}"

    if r.info.inverted_locations:
        caution_bits.append(
            f"this chart carries atlas-proven inverted channels at "
            f"{', '.join(r.info.inverted_locations)} — any headline they drive should be read "
            f"with extra skepticism")
    caution = "; ".join(caution_bits) if caution_bits else None

    essence = (
        f"{identity}. {longevity}. "
        + (f"Yogas present: {yogas}. " if r.yogas else "")
        + f"Across the twelve matters, {matters_tally}. "
        + f"What most distinguishes this chart: {stands_out}. "
        + f"Right now, the running period is {current_period}; "
        + f"live transits: {live_transits}."
        + (f" {caution}." if caution else "")
        + " This is a distillation of the method's own reading, assembled entirely from the "
          "sections above — not a prediction of events, and every distinctive claim here "
          "should be read against the population-context percentiles shown throughout this "
          "report."
    )

    return Nichod(
        identity=identity, strength_profile=strength_profile, longevity=longevity, yogas=yogas,
        stands_out=stands_out, matters_tally=matters_tally, current_period=current_period,
        live_transits=live_transits, spotlight=spotlight, caution=caution, essence=essence,
    )


#: rough percentile -> plain-English intensity word, for the "what's distinctive" paragraph.
def _plain_intensity(pct: float) -> str:
    if pct >= 0.80:
        return "unusually strong"
    if pct >= 0.65:
        return "distinctly favourable"
    if pct <= 0.20:
        return "distinctly challenging"
    if pct <= 0.35:
        return "notably challenging"
    return "worth noting"


def build_plain_reading(r: DetailedReport) -> PlainReading:
    """Assemble 'Your Reading' — the report's one genuinely plain-English section, meant to be
    read FIRST. Translates the already-computed 12-matter dashboard, the running period, and
    the distinctive readings into hand-written prose; invents no new judgment."""
    name = r.birth.name.strip() or "this chart"
    opening = (f"Here is what {name}'s chart says, in plain terms — before any of the "
               f"technical detail below.")

    by_matter = {en.matter: en.verdict for en in r.dashboard.entries}
    life_paragraphs: list[tuple[str, str]] = []
    for theme, matters in _PLAIN_GROUPS:
        sentences = []
        for m in matters:
            verdict = by_matter.get(m)
            line = _PLAIN_MATTER.get(m, {}).get(verdict) if verdict else None
            if line:
                sentences.append(line[0].upper() + line[1:])
        if sentences:
            life_paragraphs.append((theme, ". ".join(sentences) + "."))

    md_theme = _PLANET_THEME.get(r.synthesis.running_md, "this planet's classical themes")
    now = (f"You're currently in a {r.synthesis.running_md}-led chapter of life "
          f"(with {r.synthesis.running_ad} adding its own flavour within it) — classically a "
          f"time that brings out {md_theme}.")

    if r.distinctive:
        bits = [f"{_plain_signification(e.signification)} ({_plain_intensity(e.favourability_percentile)})"
                for _h, e in r.distinctive[:3]]
        notable = ("A few things stand out as distinctly this chart's own, not the generic "
                  "picture most charts show: " + "; ".join(bits) + ".")
    else:
        notable = ("Nothing in this chart strays far from what most charts show — a fairly "
                  "even, unremarkable spread across the board.")

    closing = ("This is a plain-language reading of what the classical method sees in the "
              "pattern of the birth chart — not a prediction of specific events. The full "
              "technical report below shows exactly how each conclusion was reached.")

    return PlainReading(opening=opening, life_paragraphs=tuple(life_paragraphs), now=now,
                        notable=notable, closing=closing)


_DAYS_PER_VEDIC_YEAR: float = 365.2425


def _windowed_timeline(
    birth: BirthData, on: Optional[tuple[int, int, int]], ayanamsa: str,
    back: int, forward: int,
) -> tuple[DashaTimeline, float]:
    """MD -> AD (bhukti) timeline clipped to [ref - back yr, ref + forward yr].

    ref = the on-date (if given) else today. JD arithmetic per project convention. The full-life
    bhukti walk is built once, then filtered to the periods overlapping the window.
    """
    import swisseph as swe

    if on is not None:
        y, m, d = on
    else:
        from datetime import datetime, timezone
        t = datetime.now(timezone.utc)
        y, m, d = t.year, t.month, t.day
    ref_jd = swe.julday(y, m, d, 12.0)
    lo, hi = ref_jd - back * _DAYS_PER_VEDIC_YEAR, ref_jd + forward * _DAYS_PER_VEDIC_YEAR
    full = reading_timeline(birth, ayanamsa=ayanamsa, expand_bhuktis=True)
    periods = tuple(p for p in full.periods
                    if p.period.end_jd >= lo and p.period.start_jd <= hi)
    return DashaTimeline(birth=full.birth, promise=full.promise, periods=periods), ref_jd


def build_detailed_report(
    birth: BirthData, *, on: Optional[tuple[int, int, int]] = None, ayanamsa: str = "lahiri",
    years_back: int = 10, years_forward: int = 20,
) -> DetailedReport:
    """Assemble the full reading + calibration for one chart (no verdict is re-judged).

    The life-narrative is focused on [now - years_back, now + years_forward] and expanded to
    Mahadasha -> Antardasha, so the near-term periods are the ones detailed.
    """
    chart: RamanChart = cast_chart(birth, ayanamsa=ayanamsa)
    syn = synthesize(birth, on=on, ayanamsa=ayanamsa)
    calib = {h: build_calibrated_reading(chart, h) for h in range(1, 13)}
    ayur = ayurdaya.longevity(chart)
    timeline, ref_jd = _windowed_timeline(birth, on, ayanamsa, years_back, years_forward)
    reading = read_chart(birth, ayanamsa=ayanamsa)       # carries the per-house pillars + evidence
    try:
        sav = ashtakavarga.sarvashtakavarga(chart)
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        sav = {}
    import swisseph as swe

    from app.raman_saab.primitives.vimshottari import is_maraka_period
    ry, rm, rd, _ = swe.revjul(ref_jd, swe.GREG_CAL)
    try:
        gochara_rows = tr.gochara(chart, int(ry), int(rm), int(rd), ayanamsa=ayanamsa)
    except Exception:  # noqa: BLE001 — sparse chart
        gochara_rows = ()
    try:
        gochara_outlook = tr.gochara_timeline(
            chart, ref_jd, years_back, years_forward, ayanamsa=ayanamsa)
    except Exception:  # noqa: BLE001 — sparse chart
        gochara_outlook = {}
    try:
        maraka_now = is_maraka_period(chart, ref_jd)
    except Exception:  # noqa: BLE001
        maraka_now = False
    dasha_transit = _dasha_transit_confluences(timeline, gochara_outlook)
    fired_yogas = detect_yogas(chart)
    bhava_balas = {pf.house: pf.significations[0].ledger.bhava_bala
                   for pf in reading.proformas
                   if pf.significations and pf.significations[0].ledger.bhava_bala is not None}
    insights = detect_synthesis(
        chart, ref_jd, gochara=tuple(gochara_rows), yogas=fired_yogas, sav=sav,
        bhava_balas=bhava_balas, maraka_now=maraka_now)
    provisional = DetailedReport(
        birth=birth, chart=chart, synthesis=syn, calibration=calib,
        proformas=reading.proformas, overview=chart_overview(chart),
        yogas=fired_yogas, sav=sav, insights=insights,
        info=information_content(calib), distinctive=distinctive_entries(calib),
        balarishta=getattr(chart, "balarishta", None),
        dashboard=build_matter_varga_dashboard(chart),
        soul=build_soul_reading(chart),
        pitru=build_pitru_dosha_reading(chart),
        gochara=tuple(gochara_rows), gochara_outlook=gochara_outlook,
        dasha_transit=dasha_transit, maraka_period_now=maraka_now,
        longevity_years=round(ayur.total_years, 2), longevity_ymd=ayur.ymd(),
        longevity_class=ayur.longevity_class, divisional=_divisional_sections(chart),
        timeline=timeline, ref_jd=ref_jd,
        window_back=years_back, window_forward=years_forward,
        nichod=_EMPTY_NICHOD, plain_reading=_EMPTY_PLAIN_READING,
    )
    # nichod + plain_reading are computed LAST, from the fully-assembled report — both only
    # select, count and knit together fields the rest of this function already produced.
    return _dc_replace(provisional, nichod=build_nichod(provisional),
                       plain_reading=build_plain_reading(provisional))


def _calibration_lines(reading: CalibratedHouseReading) -> list[str]:
    """Per-signification honesty rows for one house (empirical, not Raman)."""
    out: list[str] = []
    for e in reading.entries:
        if e.favourability_percentile is None:               # abstained / uncalibrated
            out.append(f"  - _{e.signification}_: {e.verdict} — (uncalibrated)")
            continue
        flags = []
        if e.band_share is not None and e.band_share >= 0.5:
            flags.append("NEAR-UNIVERSAL — carries little information")
        if e.inverted_warning:
            flags.append("INVERTED channel — real cases ran opposite; treat with maximal skepticism")
        tail = f"  [{'; '.join(flags)}]" if flags else ""
        out.append(
            f"  - _{e.signification}_: **{e.verdict} ({e.degree})** — more favourable than "
            f"{e.favourability_percentile:.0%} of charts; this exact reading in "
            f"{e.band_share:.0%} ({e.rarity}){tail}")
    return out


def to_markdown(r: DetailedReport) -> str:
    """Render the full detailed report as a Markdown document (ASCII-safe)."""
    s, b = r.synthesis, r.birth
    y, mo, d = r.longevity_ymd
    L: list[str] = []
    L.append(f"# Detailed reading — {b.name}")
    L.append("")
    L.append(f"**Born** {b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d} "
             f"(tz {b.tz_offset:+g}) at lat {b.latitude:.4f}, lon {b.longitude:.4f}  |  "
             f"ayanamsa Lahiri sidereal")
    L.append("")

    # ── the two-voice preamble ────────────────────────────────────────────────
    pop = r.calibration[1].population_n
    L.append(f"> **How to read this.** Each house first states Raman's verdict, faithful to his "
             f"texts. Beneath it, in _italics_, the instrument discloses how that verdict compares "
             f"with {pop:,} real charts — its information content, NOT a validated prediction about "
             f"your life.")
    L.append("")

    # ── your reading: the one genuinely plain-English section, read FIRST ──────
    pr = r.plain_reading
    L.append("## Your Reading")
    L.append("")
    L.append(pr.opening)
    for theme, para in pr.life_paragraphs:
        L.append("")
        L.append(f"**{theme}.** {para}")
    L.append("")
    L.append(pr.now)
    L.append("")
    L.append(pr.notable)
    L.append("")
    L.append(f"_{pr.closing}_")

    # ── the honesty headline (aggregate information content) ──────────────────
    L.append("")
    L.append("## Information content of this reading")
    L.append("")
    L.append(r.info.sentence)
    L.append("")

    # ── what actually distinguishes this chart ────────────────────────────────
    if r.distinctive:
        L.append("## What stands out in this chart")
        L.append("")
        L.append("_The readings furthest from the population midpoint — where this chart is least "
                 "like everyone else's. Rare readings first._")
        L.append("")
        L.append("| house | matter | verdict | percentile | share |")
        L.append("|---|---|---|---:|---:|")
        for house, e in r.distinctive:
            L.append(f"| H{house} {_HOUSE_NAME[house]} | {e.signification} | "
                     f"{e.verdict} ({e.degree}) | {e.favourability_percentile:.0%} | "
                     f"{e.band_share:.0%} ({e.rarity}) |")
        L.append("")

    # ── the twelve matters at a glance (executive dashboard) ──────────────────
    L.append("## The twelve matters at a glance")
    L.append("")
    L.append("_Each matter's authoritative verdict from its dedicated deep reader (Raman's method "
             "decides; the divisional chart corroborates). Detail in the deep-read sections below._")
    L.append("")
    L.append("| matter | divisional | verdict |")
    L.append("|---|---|---|")
    for en in r.dashboard.entries:
        L.append(f"| {en.matter} | D-{en.varga} {en.varga_name} | **{en.verdict}** |")
    L.append("")

    # ── chart signature ───────────────────────────────────────────────────────
    L.append("## Chart signature")
    L.append("")
    L.append(f"- **Lagna** {s.lagna}  |  **Navamsa Lagna** {s.navamsa_lagna}  |  "
             f"**Atmakaraka** {s.atmakaraka}  |  **Arudha Lagna** {s.arudha_lagna}")
    moon = r.chart.planets.get("Moon")
    if moon is not None:
        sig = nakshatra_signature.signature_for(moon.nakshatra)
        if sig is not None:
            L.append(f"- **Birth nakshatra** (Moon) — {sig.name} pada {moon.pada}, "
                     f"devata {sig.devata}, gana {sig.gana} — _{sig.soul_keyword}_")
    L.append(f"- **Stronger frame** — {r.overview.stronger_frame.upper()} "
             f"(Raman: begin from the ascendant or the Moon, whichever is stronger; HTJAH-I:645-646)")
    L.append(f"- **Jaimini** — Karakamsa {s.karakamsa}  |  Upapada {s.upapada}  |  "
             f"spouse-lord (7th-from-D9) {s.spouse_significator}")
    L.append(f"- **Running periods** — Vimshottari {s.running_md} MD / {s.running_ad} AD  |  "
             f"Chara dasha {s.chara}" + (f"  |  {s.sade_sati}" if s.sade_sati else ""))
    if s.panchanga:
        L.append(f"- **Panchanga** — {s.panchanga}")
    if r.overview.functional_natures:
        nat = "; ".join(f"{p} {n}" for p, n in r.overview.functional_natures)
        L.append(f"- **Functional nature for this Lagna** — {nat}")
    L.append("")

    # ── planet positions (a reading must be checkable) ────────────────────────
    L.append("## Planetary positions")
    L.append("")
    L.append("| graha | sign | house | nakshatra (pada) | navamsa | notes |")
    L.append("|---|---|---:|---|---|---|")
    for name, p in planet_rows(r.chart):
        nk = nakshatra_signature.signature_for(p.nakshatra)
        notes = []
        if p.retrograde:
            notes.append("retrograde")
        if p.vargottama:
            notes.append("vargottama")
        if getattr(p, "combust_fraction", 0) >= 0.5:
            notes.append("combust")
        L.append(f"| {name} | {_SIGN_NAME[p.sign]} | {p.rasi_house} | "
                 f"{nk.name if nk else '?'} ({p.pada}) | {_SIGN_NAME[p.navamsa_sign]} | "
                 f"{', '.join(notes) or '-'} |")
    L.append("")

    # ── Shadbala (the numbers behind every 'strong'/'weak') ───────────────────
    sb_rows = [(n, p) for n, p in planet_rows(r.chart) if p.shadbala_rupas is not None]
    if sb_rows:
        from app.raman_saab.primitives.shadbala.total import is_powerful
        L.append("## Shadbala (six-fold strength, rupas)")
        L.append("")
        L.append("_The strength measure behind every 'strong/weak' in this report (Raman: a yoga's "
                 "effect depends on Shadbala; HTJAH-I:611, Graha and Bhava Balas)._")
        L.append("")
        L.append("| graha | sthana | dig | kala | cheshta | naisargika | drik | **total** | "
                 "powerful? | ishta/kashta |")
        L.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---|")
        for name, p in sb_rows:
            sb = p.shadbala_rupas
            strong = is_powerful(name, sb.total / 60.0)
            ik = (f"{p.ishta:.1f}/{p.kashta:.1f}"
                  if p.ishta is not None and p.kashta is not None else "-")
            cells = " | ".join(f"{v / 60.0:.2f}" for v in
                               (sb.sthana, sb.dig, sb.kala, sb.cheshta, sb.naisargika, sb.drik))
            L.append(f"| {name} | {cells} | **{sb.total / 60.0:.2f}** | "
                     f"{'yes' if strong else 'no'} | {ik} |")
        L.append("")

    # ── fired yogas ───────────────────────────────────────────────────────────
    L.append("## Yogas present in this chart")
    L.append("")
    if r.yogas:
        L.append("_Each carries its citation. A yoga's effect depends on the strength of the "
                 "planets causing it (HTJAH-I:611)._")
        L.append("")
        for yg in r.yogas:
            L.append(f"- **{yg.name}** ({yg.kind}) — {yg.effect}  "
                     f"`{yg.source.work}:{yg.source.line}`")
    else:
        L.append("_No encoded yoga fires on this chart._")
    L.append("")

    # ── Ashtakavarga strength row ─────────────────────────────────────────────
    if r.sav:
        L.append("## Ashtakavarga (Sarvashtakavarga bindus by sign)")
        L.append("")
        L.append("| " + " | ".join(_SIGN_NAME[i][:3] for i in range(1, 13)) + " |")
        L.append("|" + "---:|" * 12)
        L.append("| " + " | ".join(str(r.sav.get(i, 0)) for i in range(1, 13)) + " |")
        L.append("")
        L.append("_Average is 28 per sign (total 337). Raman rates Ashtakavarga corroborative, "
                 "not decisive: \"it does not seem to be quite reliable\" (HTJAH-II:4453-4456)._")
        L.append("")

    # ── house-by-house, with pillars + calibration ────────────────────────────
    L.append("## House-by-house reading")
    L.append("")
    L.append(f"_{ROLLUP_RULE} Where the majority of a house's significations disagree with that "
             f"headline, a **Split status** note says so — and where the headline is driven by "
             f"an atlas-proven inverted channel, a **WARNING** is shown inline._")
    for mr in s.matters:
        pf = r.proformas[mr.house - 1] if len(r.proformas) >= mr.house else None
        cal_reading = r.calibration[mr.house]
        L.append("")
        drv_entry = driver_entry(cal_reading, mr.verdict)
        driver = drv_entry.signification if drv_entry else None
        head = f"### House {mr.house} — {mr.name}: {mr.verdict.upper()}"
        if driver:
            head += f" (driven by _{driver}_)"
        L.append(head)
        split = signification_tenor_split(cal_reading)
        note = tenor_note(split, mr.verdict)
        if note:
            L.append("")
            L.append(f"> **Split status**: {note}")
        if drv_entry is not None and drv_entry.inverted_warning:
            L.append("")
            L.append(f"> **WARNING**: the driver, _{driver}_, is an atlas-proven INVERTED "
                     f"channel — real cases ran opposite to this reading; treat this house's "
                     f"headline with maximal skepticism.")
        L.append("")
        if pf is not None:
            led = pf.significations[0].ledger
            lord_p = r.chart.planets.get(pf.lord)
            lord_bits = f"**Lord** {pf.lord}"
            if lord_p is not None:
                lord_bits += f" in H{lord_p.rasi_house}"
            if led.lord_strong is not None:
                lord_bits += f" ({'strong' if led.lord_strong else 'weak'})"
            kar_bits = f"**Karaka** {led.karaka}"
            if led.karaka_strong is not None:
                kar_bits += f" ({'strong' if led.karaka_strong else 'weak'})"
            if not led.karaka_intact:
                kar_bits += " [afflicted]"
            bb = f"  |  **Bhava Bala** {led.bhava_bala:.1f}" if led.bhava_bala is not None else ""
            L.append(f"{lord_bits}  |  {kar_bits}{bb}  |  **Navamsa** {led.navamsa_status}")
            L.append("")
        L.append(mr.reading)
        cal = _calibration_lines(cal_reading)
        if cal:
            L.append("")
            L.append("_Population context:_")
            L.extend(cal)

    # ── longevity (band FIRST, per Raman's own order) ─────────────────────────
    L.append("")
    L.append("## Longevity")
    L.append("")
    L.append("_Raman's order: first establish the band by combination (Balarishta / Alpayu / "
             "Madhyayu / Purnayu), THEN fix the period by the marakas (HTJAH-II:4465-4472). The "
             "numeric span is a cross-check, never a prediction of death._")
    L.append("")
    if r.balarishta is not None:
        bal = ("applies" if r.balarishta.applies and not r.balarishta.cancelled
               else "cancelled" if r.balarishta.cancelled else "does not apply")
        L.append(f"1. **Balarishta** (early-childhood danger): {bal}"
                 + (f" — {'; '.join(r.balarishta.reasons)}" if r.balarishta.reasons else ""))
    if s.longevity_combos:
        L.append("2. **Band by combination** (HTJAH-II):")
        for lcx in s.longevity_combos:
            L.append(f"   - {lcx}")
    L.append(f"3. **Numeric cross-check (Ayurdaya)**: about **{round(r.longevity_years)} years** "
             f"({y}y {mo}m {d}d) — class **{r.longevity_class}**. Treat as a band, not a date; the "
             f"engine's own health layer defers lifespan.")
    L.append("")

    # ── the maraka scheme (Raman's step 2, after the band) ────────────────────
    mp = getattr(r.chart, "maraka_points", None)
    if mp is not None:
        L.append("## The maraka scheme (death-dealing determinants)")
        L.append("")
        L.append("_Raman's second step after the longevity band (HTJAH-I:761-814; HTJAH-II:"
                 "4485-4546): the 2nd and 7th are the houses of death; their lords, occupants and "
                 "associates carry maraka power in their periods. A DISCLOSURE OF THE METHOD, not "
                 "a prediction — the validation program measured no chart-specific death-timing "
                 "signal (REAL_OUTCOME_GENERALIZATION.md)._")
        L.append("")
        for tier in ("primary", "secondary", "tertiary"):
            names = [u.graha for u in mp.units if u.tier == tier]
            if names:
                L.append(f"- **{tier}**: {', '.join(names)}")
        L.append(f"- **22nd drekkana lord**: {mp.drekkana22_lord}  |  "
                 f"**64th navamsa lord**: {mp.navamsa64_lord}")
        L.append(f"- **Running period ({s.running_md} MD / {s.running_ad} AD)**: "
                 + ("carries a maraka-tier lord" if r.maraka_period_now
                    else "carries no maraka-tier lord")
                 + " (broad, low-discrimination flag by design)")
        L.append("")

    # ── life-narrative (Vimshottari MD -> AD, windowed) ───────────────────────
    from app.raman_saab.render import _jd_to_date
    w_lo = _jd_to_date(r.ref_jd - r.window_back * _DAYS_PER_VEDIC_YEAR)
    w_hi = _jd_to_date(r.ref_jd + r.window_forward * _DAYS_PER_VEDIC_YEAR)
    L.append("")
    L.append(f"## Life-narrative (Vimshottari Dasha) - {w_lo} to {w_hi}")
    L.append("")
    from app.raman_saab.primitives import vimshottari as vd
    L.append(f"_Mahadasha -> Antardasha across the near term ({r.window_back} years back, "
             f"{r.window_forward} years ahead). A planet influences a house by owning, occupying or "
             f"aspecting the house OR its lord (HTJAH-I:1586-1629). Grades (uniform for every house, "
             f"HTJAH-I:1592-1640, 2588-2599): both lords influence + AD associated with MD = PAR "
             f"EXCELLENCE, both but not associated = ORDINARY, bhukti lord only = LIMITED, MD lord "
             f"only = FEEBLE. Verdicts are the UNCHANGED natal readings above._")
    L.append("")
    L.append("**What the grades mean:** " + "; ".join(
        f"_{k}_ = {v}" for k, v in _TIER_MEANING.items()) + ".")
    _TIER_LABEL = {"par excellence": "par excellence", "ordinary": "ordinary",
                   "limited": "limited (bhukti lord only)", "feeble": "feeble (MD lord only)"}
    cur_md: Optional[str] = None
    for tp in r.timeline.periods:
        rows, maha, antar = tp.activated, tp.period.maha, tp.period.antar
        if maha != cur_md:
            cur_md = maha
            L.append("")
            L.append(f"### {cur_md} Mahadasha")
        associated, raw = graded_buckets(tp, r.chart)     # ONE grading implementation
        buckets = {k: [f"H{a.house} {a.natal_verdict}" for a in v] for k, v in raw.items()}
        assoc = "own bhukti" if antar == maha else \
            ("AD associated with MD" if associated else "AD not associated with MD")
        now = "  **<- now**" if tp.period.start_jd <= r.ref_jd < tp.period.end_jd else ""
        ad = antar or maha
        seg = [f"{'**' if k in ('par excellence', 'ordinary') else ''}{_TIER_LABEL[k]}: "
               f"{', '.join(buckets[k])}{'**' if k in ('par excellence', 'ordinary') else ''}"
               for k in _TIER_LABEL if buckets[k]]
        L.append(f"- **{ad} AD** ({_jd_to_date(tp.period.start_jd)} .. "
                 f"{_jd_to_date(tp.period.end_jd)}){now} - {assoc}; "
                 f"{'; '.join(seg) or '(no house influenced)'}")
        L.append(f"  - _{plain_bhukti_summary(rows, associated)}_")

    # ── current transits with Vedha (the honest gochara table) ────────────────
    if r.gochara:
        L.append("")
        L.append("## Current transits (Gochara) with Vedha")
        L.append("")
        L.append("_At the reference date, from the natal Moon. Raman: transits are secondary, "
                 "catalytic — conclusions rest on Dasa-vichara (HTJAH-II:4679-4687). The NET column "
                 "applies Vedha (obstruction): a favourable transit obstructed by a planet in its "
                 "Vedha position does not deliver._")
        L.append("")
        L.append("| planet | sign | from Moon | classical | AV bindus | Vedha by | **net** |")
        L.append("|---|---|---:|---|---|---|---|")
        for g in r.gochara:
            av = str(g.bav_bindus) if g.bav_bindus is not None else "-"
            vedha = ", ".join(g.vedha_by) if g.vedha_by else "-"
            L.append(f"| {g.planet} | {_SIGN_NAME[g.sign]} | {g.house_from_moon} | "
                     f"{'favourable' if g.gochara_good else 'adverse'} | {av} | {vedha} | "
                     f"**{'favourable' if g.net_good else 'obstructed/adverse'}** |")
        L.append("")

    # ── the same Gochara scheme, over time: which windows in the past/future are favourable ──
    if r.gochara_outlook:
        good = sorted(
            (seg for segs in r.gochara_outlook.values() for seg in segs
             if seg.gochara_good and (seg.end_jd - seg.start_jd) >= 25),
            key=lambda s: s.start_jd)
        if good:
            lo_y = _jd_month_year(r.ref_jd - r.window_back * 365.2425)[-4:]
            hi_y = _jd_month_year(r.ref_jd + r.window_forward * 365.2425)[-4:]
            L.append(f"### Favourable transit windows ({lo_y} to {hi_y})")
            L.append("")
            L.append("**In simple terms:** these are the months ahead (and behind) when Jupiter, "
                     "Saturn, Rahu or Ketu sits in a position that classically supports the side "
                     "of life that planet governs — see \"what it supports\" below. \"Strength\" "
                     "is how well-backed that support is; \"interference\" says how often, across "
                     "that whole stretch, another planet's position was blocking some of it, so "
                     "the support was real but partly blunted. Raman treats a transit as "
                     "secondary to your Dasha (HTJAH-II:4679) — read a window below as *added* "
                     "support during whatever your running period (Life-narrative, below) already "
                     "indicates, not as a stand-alone prediction.")
            L.append("")
            L.append("| Planet | Window | What it supports | Strength | Interference |")
            L.append("|---|---|---|---|---|")
            for seg in good:
                L.append(f"| {seg.planet} | {_outlook_window_label(seg.start_jd, seg.end_jd)} | "
                         f"{_PLANET_THEME[seg.planet]} | "
                         f"{_outlook_strength_word(seg.bav_bindus)} | "
                         f"{_vedha_word(seg.vedha_sample_fraction).split(' ')[0]} |")
            L.append("")
            L.append("_How this is measured: a window is a continuous span where the planet "
                     "occupies a classical Gochara-benefic house from your Moon (HPA/HTJAH); "
                     "strength reflects that planet's own Ashtakavarga bindus in the transited "
                     "sign (HPA-34:127); interference estimates, from samples across the whole "
                     "window, how often another planet sat in the paired Vedha (obstruction) "
                     "house — a coarse read, not exact dates (the exact-day check is the snapshot "
                     "table above). Dates are accurate to about a week and shown by month, not "
                     "day, for that reason; windows under a month (a planet stationing back "
                     "across a sign boundary) are dropped as sampling noise, not real transits._")
            L.append("")

    # ── dasha x transit confluence: where the running period's own lord is well-transited ──
    if r.dasha_transit:
        L.append("## Dasha x Transit confluence")
        L.append("")
        L.append("**In simple terms:** these are the specific stretches where your running "
                 "Mahadasha (MD) or Antardasha (AD) lord is *also*, at the same time, transiting "
                 "favourably in the sky. Raman treats a transit as secondary to the Dasha "
                 "(HTJAH-II:4679) — \"a good transit only delivers what the running period "
                 "already permits\" — so a confluence below is the clearest confirmation this "
                 "report can offer: the very planet already ruling this stretch of your life is "
                 "also well placed by transit.")
        L.append("")
        L.append("_Only Jupiter, Saturn, Rahu and Ketu are tracked long-range (the same four the "
                 "outlook above covers). A period led by the Sun, Moon, Mars, Mercury or Venus "
                 "simply has no row here — that is a gap in what this cross-check computes, not a "
                 "judgment that the period lacks support._")
        L.append("")
        L.append("| Period | Planet | Overlap | Supports | Strength | Interference |")
        L.append("|---|---|---|---|---|---|")
        for c in r.dasha_transit:
            L.append(f"| {c.role} | {c.planet} | "
                     f"{_outlook_window_label(c.overlap_start_jd, c.overlap_end_jd)} | "
                     f"{_PLANET_THEME[c.planet]} | {_outlook_strength_word(c.bav_bindus)} | "
                     f"{_vedha_word(c.vedha_sample_fraction).split(' ')[0]} |")
        L.append("")

    # ── divisional deep-reads (Shodasavarga) ──────────────────────────────────
    if r.divisional:
        L.append("")
        L.append("## Divisional deep-reads (Shodasavarga)")
        L.append("")
        L.append("_Each divisional chart magnifies one matter. The Raman core is authoritative; "
                 "the varga block corroborates (report-only)._")
        for label, body in r.divisional:
            L.append("")
            L.append(f"### {label}")
            L.append("")
            L.append("```")
            L.append(body.strip("\n"))
            L.append("```")

    # ── the parallel doctrine layers ──────────────────────────────────────────
    if s.career:
        L.append("")
        L.append("## Career (HTJAH-II — navamsa-dispositor of the 10th lord)")
        L.append("")
        L.append(s.career)
    if s.deeptadi:
        L.append("")
        L.append("## Deeptadi avasthas (each graha's result-state, HPA Ch.7)")
        L.append("")
        L.append(", ".join(s.deeptadi))
    if s.karakamsa_reading:
        L.append("")
        L.append("## Jaimini Karakamsa (the soul's inclination)")
        L.append("")
        for line in s.karakamsa_reading:
            L.append(f"- {line}")

    # ── soul & destiny (the full Jaimini reading behind the stub above) ───────
    L.append("")
    L.append("## Soul & destiny (extended Jaimini reading)")
    L.append("")
    L.append("```")
    L.append(_clean_box(render_soul.to_text(r.soul)).strip("\n"))
    L.append("```")

    # ── pitru dosha screen (non-Raman provenance, clearly bannered) ───────────
    L.append("")
    L.append("## Pitru dosha screen")
    L.append("")
    L.append("> **Provenance notice.** Only the children verdict below is Raman "
             "(HTJAH-I:5018). The curse-yoga screens are CLASSICAL_NONCITABLE "
             "(BPHS / Prasna Marga) — reported for completeness, outside Raman's canon, and "
             "carrying no demonstrated predictive weight.")
    L.append("")
    L.append("```")
    L.append(_clean_box(render_pitru.to_text(r.pitru)).strip("\n"))
    L.append("```")

    # ── integrated insights (cross-feature synthesis) ─────────────────────────
    L.append("")
    L.append("## Integrated insights (cross-feature synthesis)")
    L.append("")
    L.append("_Where the report's sections meet: encoded combination doctrine connecting "
             "Shadbala, yogas, dashas, transits, Ashtakavarga and the houses. Each insight leads "
             "with a plain-language reading, backed by the exact text it draws from. As "
             "everywhere in this report: how the method reads this chart, not a prediction._")
    _BAND_HEAD = {
        "raman": ("### Raman's own combination doctrine", None),
        "classical": ("### Classical corroboration",
                      "> **Provenance notice.** The rules below are CLASSICAL_NONCITABLE "
                      "(Laghu Parashari, BPHS, Uttara Kalamrita, Saravali) — outside Raman's "
                      "citable canon; where they conflict with Raman, Raman wins."),
        "av": ("### Ashtakavarga combinations",
               "> **Raman's own caveat governs this band**: \"Ashtakavarga method is equally "
               "important. But, it does not seem to be quite reliable\" (HTJAH-II:4453-4456, "
               "said of longevity determination). These classical AV methods never override "
               "an insight from the bands above."),
    }
    cur_band: Optional[str] = None
    for ins in r.insights:
        if ins.rule.band != cur_band:
            cur_band = ins.rule.band
            head, banner = _BAND_HEAD[cur_band]
            L.append("")
            L.append(head)
            if banner:
                L.append("")
                L.append(banner)
        cite = f"  `{ins.rule.source.work}:{ins.rule.source.line}`" if ins.rule.source else ""
        L.append("")
        L.append(f"- **{ins.rule.name}**{cite} — {ins.rule.simple_meaning}")
        L.append(f"  - _This chart_: {ins.detail}")
        L.append(f"  - _The text says_: \"{ins.rule.doctrine}\"")
        L.append(f"  - _links_: {' x '.join(ins.rule.links)}")
    on_record = descriptive_rules()
    if on_record:
        L.append("")
        L.append("### Further combination doctrine on record (not yet computed)")
        L.append("")
        for dr_ in on_record:
            cite = f" `{dr_.source.work}:{dr_.source.line}`" if dr_.source else ""
            L.append(f"- **{dr_.name}**{cite} — {dr_.doctrine}")
    L.append("")
    L.append("_Excluded by project locks (recorded, not encoded): BPHS rasi-dasha Argala "
             "grading; the KP sub-lord chain (non-Lahiri); nodal Vedha. Absence findings "
             "honoured: Raman states no direct Shadbala x Ashtakavarga rule, no numeric "
             "requisite-Shadbala minima, no Bhava Bala cutoff, no Sade-Sati x Moon doctrine "
             "— none were invented._")

    # ── glossary ──────────────────────────────────────────────────────────────
    L.append("")
    L.append("## Glossary")
    L.append("")
    for term, meaning in GLOSSARY.items():
        L.append(f"- **{term}** — {meaning}")

    # ── nichod: the capstone integration of every section above ───────────────
    n = r.nichod
    L.append("")
    L.append("## Nichod")
    L.append("")
    L.append("_The distilled essence: every section above, squeezed into one. Nothing here is "
             "a new judgment — each clause selects, counts, or quotes what the report already "
             "showed. Not a prediction._")
    L.append("")
    L.append(f"> {n.essence}")
    L.append("")
    L.append("**Ingredients** (so the essence can be checked against its parts):")
    L.append("")
    L.append(f"- **Identity**: {n.identity}")
    L.append(f"- **Strength profile**: {n.strength_profile}")
    L.append(f"- **Longevity**: {n.longevity}")
    L.append(f"- **Yogas**: {n.yogas}")
    L.append(f"- **What stands out**: {n.stands_out}")
    L.append(f"- **The twelve matters**: {n.matters_tally}")
    L.append(f"- **Running now**: {n.current_period}")
    L.append(f"- **Live transits**: {n.live_transits}")
    if n.spotlight:
        L.append(f"- **Cross-feature spotlight**: {n.spotlight}")
    if n.caution:
        L.append(f"- **Caution**: {n.caution}")

    # ── footer ────────────────────────────────────────────────────────────────
    L.append("")
    L.append("---")
    L.append(f"_Italicised population context is EMPIRICAL_ASTRODATABANK provenance (n="
             f"{pop:,}) - explicitly not Raman. {_VALIDITY}_")
    return _fold_ascii("\n".join(L))


def _fold_ascii(s: str) -> str:
    """ASCII-safe, but FOLD Sanskrit diacritics to base letters (Navamsa, karaka) rather than
    blanking them to '?' — the varga renderers emit UTF-8 IAST that a raw ascii-replace mangles."""
    import unicodedata

    from app.raman_saab.render import _ascii
    folded = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return _ascii(folded)
