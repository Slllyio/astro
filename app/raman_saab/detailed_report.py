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
from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges.calibrated_reading import (
    _VALIDITY,
    CalibratedHouseReading,
    build_calibrated_reading,
)
from app.raman_saab.chart.model import PlanetPos
from app.raman_saab.doctrine.synthesis_rules import (
    FiredInsight,
    _rupas,
    _strong,
    _yoga_planets,
    descriptive_rules,
    detect_synthesis,
)
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.insight_digest import InsightDigest, build_insight_digest
from app.raman_saab.judges.chart_overview import ChartOverview, chart_overview
from app.raman_saab.judges.dasamsa_career_reading import build_dasamsa_career_reading
from app.raman_saab.judges.dwadasamsa_parents_reading import build_dwadasamsa_parents_reading
from app.raman_saab.judges.navamsa_marriage_reading import build_navamsa_marriage_reading
from app.raman_saab.judges.saptamsa_reading import build_saptamsa_children_reading
from app.raman_saab.judges.siddhamsa_education_reading import build_siddhamsa_education_reading
from app.raman_saab.judges.trimsamsa_health_reading import build_trimsamsa_health_reading
from app.raman_saab.judges.general_varga_reading import build_general_varga_reading
from app.raman_saab.judges.house_template import FrameLedger, HouseProforma, SignificationVerdict
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
from app.raman_saab.primitives import vimshottari as vd
from app.raman_saab.primitives.balarishta import BalarishtaState
from app.raman_saab.proforma import read_chart
from app.raman_saab.reading_timeline import DashaTimeline, reading_timeline
from app.raman_saab.synthesis import Synthesis, synthesize

_HOUSE_NAME = {1: "Self/Body", 2: "Wealth/Family", 3: "Siblings/Courage", 4: "Mother/Home",
               5: "Children/Mind", 6: "Health/Enemies", 7: "Spouse/Partnership", 8: "Longevity",
               9: "Father/Fortune", 10: "Career", 11: "Gains", 12: "Loss/Moksha/Spirituality"}

_SIGN_NAME = ("", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
              "Sagittarius", "Capricorn", "Aquarius", "Pisces")

#: Raman's strongest-planet temperament lines, lightly condensed (OCR-normalized) from
#: HTJAH-I:6248-6268 — "The strongest planet in the horoscope determines the predominance of
#: the physical, mental and spiritual peculiarities of the person" (6248-6250). The Moon is
#: deliberately ABSENT: Raman's passage names Sun, Mars, Mercury, Jupiter, Venus and Saturn
#: only — an honest absence, nothing invented. Two distinct categories of clause are omitted:
#: (a) the grade-gated weak/afflicted clauses (Sun "predominantly weak" blindness/heart cluster,
#: 6252-6254; Mars "highly afflicted" scaffold, 6256-6257), genuinely inapplicable to a
#: strongest-planet reading; and (b) the named-disease and appearance clauses Raman attaches
#: even to the strongest case (Sun fire accidents 6251-6252; Mars apoplexy/skin 6255-6256;
#: Venus 6262-6264; Saturn varicose veins / insanity escalation / uncouth appearance
#: 6265-6268) — a DISCLOSED editorial condensation under the card's "shorthand for tendencies,
#: never medical statements" framing, not a claim of inapplicability.
_RULER_TEMPERAMENT: Final[dict[str, str]] = {
    "Sun": "enjoys well-balanced health and looks only at the bright side of things; "
           "the weak point is the eyesight",
    "Mars": "the sanguine temperament — the blood is rich; runs a great risk of wounds "
            "in quarrels",
    "Mercury": "endowed with a bilious temperament; the weak points are the nervous system, "
               "liver and digestive organs",
    "Jupiter": "the temperament is both phlegmatic and sanguine; may suffer from excessive "
               "indulgence in eating and drinking",
    "Venus": "strong, healthy and happy — sensual, fond of the good things of life; "
             "the disposition is cheerful",
    "Saturn": "worries a great deal and suffers from a chronic melancholic tendency; "
              "the spinal column requires special care",
}


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


def _lagna_ledger(sv: SignificationVerdict) -> FrameLedger:
    """The LAGNA-frame ledger for a signification. `sv.ledger` is the LEAD ledger — it may be
    the MOON-frame ledger when the moon-frame lord out-strengths the lagna lord — while
    `HouseProforma.lord` (what every renderer displays as the house's Lord) is always the
    LAGNA-frame lord's name. Reading `lord_strong` or `navamsa_status` (both depend on the
    frame's own lord) off the lead ledger would pair the lagna lord's NAME with a DIFFERENT
    planet's strength/navamsa — `house_template.HouseProforma.as_house_verdict` already guards
    against exactly this for its own `lord_strong` readout (see its docstring); this is the same
    lookup, reused here because the renderers read the ledger directly rather than going through
    `as_house_verdict`. `karaka`/`karaka_strong`/`bhava_bala` are frame-independent (the karaka is
    fixed per signification and Bhava Bala is computed from the house alone, not from `lord`), so
    only the lord-dependent fields need this correction."""
    return next((L for L in (sv.ledger,) + sv.alt_ledgers if L.frame == "lagna"), sv.ledger)


#: lay-reader life-area names (for the plain-language bhukti summary).
_PLAIN_AREA = {1: "self & health", 2: "wealth & family", 3: "courage & siblings",
               4: "home & mother", 5: "children & creativity", 6: "health & rivals",
               7: "marriage & partnership", 8: "longevity", 9: "fortune & father",
               10: "career", 11: "gains", 12: "losses & spirituality"}

#: hand-written (never templated) plain-English lines for each of the 12-matter dashboard's
#: matters, by verdict — the actual content of "Your Reading". Deliberately warm, honest, and
#: free of jargon; afflicted lines name real friction without alarm; this is prose written for
#: a person, not a restatement of a technical verdict.
_PLAIN_MATTER: dict[str, dict[str, "str | tuple[str, ...]"]] = {
    "wealth": {
        "favourable": ("money and material comfort come to you relatively easily, and your "
                       "resources tend to grow over time",
                       "there is a natural ease around money and material security, with resources "
                       "that build steadily rather than dramatically"),
        "afflicted": ("financial ease may take real effort on your part — steady habits will "
                      "matter more than luck here",
                      "wealth here is earned rather than gifted; discipline and patience carry more "
                      "weight than fortune in your material life"),
        "mixed": ("your finances show a real mix of ease and effort — some years flow, others "
                  "ask for discipline",
                  "money moves in cycles for you — genuinely comfortable stretches alongside years "
                  "that call for care")},
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
        "favourable": ("the chart favours ease and joy around children",
                       "matters of children read warmly here — ease and gladness rather than "
                       "difficulty"),
        "afflicted": ("this chart shows real strain around children — fertility, timing, or the "
                      "parent-child bond may ask for patience. This is one of the more sensitive "
                      "readings here and deserves a compassionate, unhurried view, not alarm",
                      "children are a tender area in this chart — fertility, timing, or the "
                      "parent-child bond may call for patience. This reading deserves a gentle, "
                      "unhurried view rather than alarm"),
        "mixed": ("children bring both joy and real challenge in this chart — a mixed but not "
                  "unusual pattern",
                  "the reading around children holds both real gladness and real challenge — a "
                  "mixed but entirely ordinary pattern")},
    "marriage": {
        "favourable": ("marriage and partnership read favourably — a supportive, workable bond "
                       "is the picture here",
                       "partnership is a genuine strength in this chart — the makings of a "
                       "supportive, steady marriage"),
        "afflicted": ("marriage may need real effort and patience — the chart shows genuine "
                      "friction to work through, not a smooth path",
                      "partnership here asks for real work; the chart reads friction to be met "
                      "with patience rather than an effortless union"),
        "mixed": ("marriage shows both real warmth and real friction — a genuine partnership, "
                  "not an easy one",
                  "your partnership carries both real closeness and real challenge — a bond with "
                  "depth, but one that is worked at")},
    "father": {
        "favourable": "your relationship with your father, and your broader sense of fortune, "
                      "read as a genuine asset",
        "afflicted": "your bond with your father, or your sense of fortune, may carry some "
                     "distance or difficulty",
        "mixed": "fortune and your father's influence bring both support and occasional "
                 "strain"},
    "career": {
        "favourable": ("career and public standing read strongly — recognition and steady "
                       "progress are the pattern here",
                       "professional life is a clear strength — the chart supports recognition and "
                       "steady advancement"),
        "afflicted": ("career may involve real struggle — slower recognition or harder-won "
                      "progress than you'd like",
                      "professional life here is hard-won; recognition tends to come slowly and "
                      "through effort rather than smoothly"),
        "mixed": ("career shows both real opportunity and real obstacles — success here takes "
                  "deliberate effort",
                  "your working life mixes genuine opportunity with genuine obstacle — progress "
                  "that rewards persistence")},
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

def _pick_plain_variant(birth, key: str, variants):
    """Deterministically pick one plain-language phrasing for this chart. A single string is
    returned as-is; a tuple of variants is indexed by a stable hash of the birth data + key — so
    the SAME chart always reads the same (reproducible) while DIFFERENT charts get different
    wording. This breaks the cross-chart sentence repetition of the templated fallback WITHOUT any
    randomness (an engine value must be reproducible)."""
    if not isinstance(variants, tuple):
        return variants
    if len(variants) == 1:
        return variants[0]
    import hashlib
    seed = (f"{birth.year}-{birth.month}-{birth.day}-{birth.hour}-{birth.minute}-"
            f"{birth.latitude}-{birth.longitude}-{key}")
    idx = int(hashlib.blake2b(seed.encode(), digest_size=4).hexdigest(), 16) % len(variants)
    return variants[idx]


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
    # v18 (2026-08-03, conscious amendment, user-requested coherence work): the
    # interpretation guide — which section governs when two overlap, collected from the
    # eleven precedence statements the report already makes locally (coherence audit,
    # DOCTRINE_BACKLOG). Placed directly after the honesty headline: the reader learns how
    # much to believe, then how to read, then reads. Chart-independent doctrine metadata
    # (app/raman_saab/interpretation_guide.py), also shipped machine-readable in the JSON.
    SectionSpec("interpretation_guide", "## How to read this report",
                'id="interpretation-guide"', "v18"),
    SectionSpec("stands_out", "## What stands out in this chart", 'id="stands-out"', "v1"),
    # v19 (2026-08-03, conscious amendment, same audit as v18): the engine's own ranked
    # digest — computed since the share-the-app arc and shipped in JSON + the interactive
    # page, but never rendered in markdown/standalone HTML: a REPORT COMPLETENESS
    # violation found by the coherence audit, repaired here. Placed after What-stands-out,
    # which it generalizes (convergence -> current period -> insights -> tension ->
    # distinctive, the digest's own fixed cross-category order).
    SectionSpec("digest", "## What matters most (ranked digest)", 'id="digest"', "v19"),
    SectionSpec("dashboard", "## The twelve matters at a glance", 'id="dashboard"', "v2"),
    SectionSpec("chart_signature", "## Chart signature", 'class="sig"', "v1"),
    # v13 (2026-07-26, conscious amendment): Raman's own first-impression move — "first of all
    # consider the ruler of the nativity" (HTJAH-I:16001-16002) — placed directly after the
    # Chart signature it opens from; the natural narrative position (v6-v12 precedent).
    SectionSpec("ruler", "## Ruler of the nativity", 'id="ruler"', "v13"),
    # v20 (2026-08-03, synthesis layer S2): planet biographies — the dominant grahas by
    # judgment-graph census, each told as one story (role, strength, helps, obstructs,
    # activates). Placed after the ruler card it generalizes from one planet to the
    # dominant set. Pure re-read; Raman-tier themes cite HTJAH-II:10249-10274; the modern
    # keyword tier always carries the MODERN_SYNTHESIS banner.
    SectionSpec("planet_bios", "## Planet biographies (dominant grahas)",
                'id="planet-bios"', "v20"),
    # v27 (2026-08-04, user-requested): the psychological profile — the computed mind
    # stack (HPA-18 lagna portrait quoted verbatim, Moon manas state, temperament,
    # nature stamp, AK) woven into one profile; follows the planet cluster it re-reads.
    SectionSpec("psych", "## Psychological profile", 'id="psych"', "v27"),
    SectionSpec("chart_grids", None, 'id="charts"', "v1"),
    SectionSpec("positions", "## Planetary positions", 'id="positions"', "v1"),
    SectionSpec("shadbala", "## Shadbala", 'id="shadbala"', "v2"),
    SectionSpec("yogas", "## Yogas present in this chart", 'id="yogas"', "v1"),
    # v7 (2026-07-26, conscious amendment): inserted right after Yogas, since it directly extends
    # that section with WHEN each yoga's own lord runs — the natural narrative position.
    SectionSpec("yoga_timing", "## Yoga x Dasha timing", 'id="yoga-timing"', "v7"),
    # v21 (2026-08-03, user-requested): the yoga deep-read — every fired yoga as a full
    # study (quoted definition, computation tree, participant facts, measured strength,
    # cancellation state, modifiers, periods, NH examples, comparison). Placed after the
    # timing companion it extends. Strength is MEASURED rupas, never a percentage.
    SectionSpec("yoga_deep", "## Yoga deep-read", 'id="yoga-deep"', "v21"),
    SectionSpec("ashtakavarga", "## Ashtakavarga", 'id="sav"', "v1"),
    SectionSpec("houses", "## House-by-house reading", 'id="houses"', "v1"),
    # v8 (2026-07-26, conscious amendment): inserted right after House-by-house, since it
    # cross-checks the verdicts just shown against two independent strength measures — the
    # natural narrative position (read the verdicts, then see how strong their ground is).
    SectionSpec("house_strength", "## House strength cross-check", 'id="house-strength"', "v8"),
    # v14 (2026-07-26, conscious amendment): the per-house testimony ledgers — Raman's
    # "judgment is the summing up of the influence of planets" (HTJAH-I:983-991) applied to
    # every already-computed axis — placed right after the House strength cross-check it
    # generalizes from two axes to all of them; the natural narrative position.
    SectionSpec("preponderance", "## Preponderance of testimonies", 'id="preponderance"', "v14"),
    SectionSpec("longevity", "## Longevity", 'id="longevity"', "v1"),
    SectionSpec("maraka", "## The maraka scheme", 'id="maraka"', "v2"),
    # v11 (2026-07-26, conscious amendment): inserted right after The maraka scheme, since it
    # cross-references that section's own death-window against transiting Saturn — framed
    # strictly as textbook doctrine (this project's real-outcome research measured no
    # death-timing signal; see docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md).
    SectionSpec("maraka_saturn", "## Maraka x Saturn-transit confluence",
                'id="maraka-saturn"', "v11"),
    # v17 (2026-08-03, conscious amendment, user-approved feature): the health/vulnerability
    # READ-OUT — a pure re-read of the D-30 health core, H12 rollup, maraka tiers and longevity
    # band, gathered in one place. Placed at the end of the longevity/maraka neighbourhood it
    # summarizes (the v11 precedent for this cluster); descriptive idiom only, caveat rendered
    # in every surface, never a medical statement or prediction.
    SectionSpec("health_readout", "## Health & vulnerability read-out",
                'id="health-readout"', "v17"),
    # v22 (2026-08-03, user-requested): Arishta & Bhanga — balarishta with Raman's
    # antidote passage quoted, the bhanga states, Kemadruma, the fired longevity
    # protections and the band; closes the longevity cluster it belongs to.
    SectionSpec("arishta", "## Arishta & Bhanga", 'id="arishta"', "v22"),
    SectionSpec("timeline", "## Life-narrative (Vimshottari Dasha)", 'id="timeline"', "v1"),
    # v9 (2026-07-26, conscious amendment): inserted right after Life-narrative, since it paints
    # the SAME windowed MD/AD timeline with each lord's Ishta/Kashta lean — the natural
    # narrative position, a colour-strip companion to the section directly above it.
    SectionSpec("ishta_kashta", "## Ishta/Kashta outlook", 'id="ishta-kashta"', "v9"),
    # v10 (2026-07-26, conscious amendment): grouped with the Ishta/Kashta outlook, right after
    # it — both are Life-narrative companions painting a different natal-fixed lens (strength/
    # vargottama here, Ishta/Kashta lean there) across the SAME MD timeline.
    SectionSpec("md_condition", "## MD-lord condition outlook", 'id="md-condition"', "v10"),
    # v12 (2026-07-26, conscious amendment): the third Life-narrative companion (Ishta/Kashta,
    # MD-lord condition, and now this) — placed last of the three since it is AV-tier, the
    # weakest doctrinal standing of the group, under Raman's own reliability caveat.
    SectionSpec("av_dasha_seat", "## AV dasha-seat outlook", 'id="av-dasha-seat"', "v12"),
    # v16 (2026-08-03): the fourth Life-narrative companion — the ASP-12 eightfold Kakshya
    # division of each MD run, judged by bindu donation. Placed after the AV seat row since
    # it is the finest-grained of the group.
    SectionSpec("dasa_kakshya", "## Dasha Kakshya intervals", 'id="dasa-kakshya"', "v16"),
    # v15 (2026-07-26, conscious amendment): one woven prose chapter per Mahadasha — the
    # Napoleon-narration shape (HTJAH-I:15950-15999) merging what Life-narrative and its three
    # companion tables show separately; placed as the capstone of that companion cluster.
    SectionSpec("life_chapters", "## Life-chapters", 'id="life-chapters"', "v15"),
    # v28 (2026-08-04, user-requested, RENAMED from the proposal's "event probability
    # timeline" per Measured-Truth): the decade INDICATION timeline — the method's
    # indications per decade sliced from the windowed timeline; never probabilities.
    SectionSpec("decades", "## Decade indication timeline", 'id="decades"', "v28"),
    SectionSpec("gochara", "## Current transits (Gochara", 'id="gochara"', "v2"),
    # v6 (2026-07-26, conscious amendment): inserted right after Gochara, since it cross-
    # references the Life-narrative (timeline) and Gochara sections directly above it — the
    # natural narrative position, the same precedent as v2/v3 mid-document insertions.
    SectionSpec("dasha_transit", "## Dasha x Transit confluence", 'id="dasha-transit"', "v6"),
    SectionSpec("divisional", "## Divisional deep-reads (Shodasavarga)", 'id="vargas"', "v1"),
    SectionSpec("career", "## Career (HTJAH-II", 'id="career"', "v1"),
    # v23 (2026-08-03, user-requested): the profession synthesis — every encoded angle
    # (10th sign, navamsa-dispositor, strongest planet, AK, running MD, H10 modes,
    # career yogas) with a deterministic convergence count; extends the Career line above.
    SectionSpec("profession", "## Profession synthesis", 'id="profession"', "v23"),
    # v24 (2026-08-03, user-requested): the wealth chapter — the CHANNELS (earning style,
    # accumulation, gains, inheritance, speculation, authority, trade, land, foreign)
    # from the judged significations + the cited source-of-gains tables, with the
    # expansion periods from the timeline's own H2/H11 activations.
    SectionSpec("wealth", "## Wealth chapter", 'id="wealth"', "v24"),
    # v25/v26 (2026-08-04, user-requested): the marriage monograph and children chapter —
    # HTJAH mined verbatim by frozen range + the fired kalatra/putra rules + timing.
    SectionSpec("marriage", "## Marriage monograph", 'id="marriage"', "v25"),
    SectionSpec("children", "## Children chapter", 'id="children"', "v26"),
    SectionSpec("deeptadi", "## Deeptadi avasthas", 'id="deeptadi"', "v1"),
    SectionSpec("karakamsa", "## Jaimini Karakamsa", 'id="karakamsa"', "v1"),
    SectionSpec("soul", "## Soul & destiny", 'id="soul"', "v2"),
    # v30 (2026-08-04, user-requested, enabled by the JAIMINI lift): the karmic-evolution
    # chapter — AK, Karakamsa, Upapada, the JAIMINI-9 doctrine verbatim, D-20/D-60 cores;
    # walled (natal verdicts never touched); after the soul reading it deepens.
    SectionSpec("karmic", "## Karmic evolution (Jaimini)", 'id="karmic"', "v30"),
    SectionSpec("pitru", "## Pitru dosha", 'id="pitru"', "v2"),
    # v3 (2026-07-25, conscious amendment): inserted BEFORE glossary so the reference material
    # stays last; _FROZEN in the contract test was amended in the same commit per the procedure.
    SectionSpec("synthesis", "## Integrated insights", 'id="synthesis"', "v3"),
    # v29 (2026-08-04, user-requested): the full life synthesis — the biography-closing
    # chapter weaving every monograph above; STRICT PREC-10, no new judgments; placed
    # before the reference material, after everything it re-reads.
    SectionSpec("life_synthesis", "## Full life synthesis", 'id="life-synthesis"', "v29"),
    SectionSpec("glossary", "## Glossary", 'id="glossary"', "v1"),
    # v4 (2026-07-26, conscious amendment): the capstone integration, appended LAST — after
    # reference material — since it distils sections that appear throughout the whole document.
    SectionSpec("nichod", "## Nichod", 'id="nichod"', "v4"),
)

#: The HTML renderer's document order (the signature chips live in the page header, and the
#: chart grids/now-box are HTML-only). Same append-only rule applies.
HTML_SECTION_ORDER: tuple[str, ...] = (
    "title", "plain_reading", "chart_signature", "ruler", "planet_bios", "psych",
    "now_box",
    "info_content", "interpretation_guide", "stands_out", "digest",
    "dashboard",
    "chart_grids", "positions", "shadbala", "yogas", "yoga_timing", "yoga_deep",
    "ashtakavarga", "houses",
    "house_strength", "preponderance", "longevity",
    "maraka", "maraka_saturn", "health_readout", "arishta", "timeline", "ishta_kashta",
    "md_condition",
    "av_dasha_seat", "dasa_kakshya",   # dasa_kakshya added here 2026-08-03 (v16 omission repair)
    "life_chapters", "decades",
    "gochara", "dasha_transit",
    "divisional", "career", "profession", "wealth", "marriage", "children",
    "deeptadi",
    "karakamsa", "soul", "karmic", "pitru", "synthesis", "life_synthesis", "glossary",
    "nichod",
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


#: Ordinal suffixes for the Conclusion line's neutral rank clause ("stands 7th of 12").
def _ordinal(n: int) -> str:
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def house_conclusion(r: "DetailedReport", house: int) -> str:
    """Raman's own closing device, applied to our house blocks: essentially every worked
    per-house analysis in HTJAH ends with a "Conclusion.—" summation weighing house strength,
    lord and karaka in one free-prose sentence (~149 occurrences in HTJAH-I, ~107 in HTJAH-II
    — e.g. "The fourth house is moderately strong, but the lord and the Karaka are
    considerably afflicted", HTJAH-I:4485; "quite strongly disposed but the malefic influences
    are not negligible", HTJAH-I:8513; "a preponderance of benefic influences", HTJAH-I:8870).
    His conclusions are ALWAYS free prose — his only fixed named taxonomy is longevity's four
    bands (HTJAH-I:9699-9705) — so this composes prose, never an archetype label.

    STRICT COMPOSITION RULES (each refusing a specific unfaithful mechanism):
    - The verdict is restated verbatim, never re-derived and never outvoted — the witness
      split is DISCLOSURE ("the headline follows the weakest-link rule and stands"), never
      mitigation; no real-world severity claim is ever composed.
    - The ONLY rank-conditional clauses are the two superlatives, rank 1 and rank 12 —
      GBB-9:332's own vocabulary ("the most powerful Bhava... the least powerful") licenses
      exactly those; every other rank renders neutrally as a magnitude. No cutoffs.
    - Ashtakavarga is mentioned as support, never decisive (Raman's own reliability caveat).
    - Missing inputs degrade clause-by-clause to omission — nothing is guessed.
    One helper consumed by BOTH renderers (the `graded_buckets` no-drift precedent)."""
    pf = next((p for p in r.proformas if p.house == house), None)
    if pf is None:
        return ""
    verdict = str(pf.rollup)
    name = _HOUSE_NAME.get(house, "")
    bits: list[str] = [f"The {name} house reads {verdict}"]

    led = _lagna_ledger(pf.significations[0]) if pf.significations else None
    if led is not None:
        pillar: list[str] = []
        if led.lord_strong is not None:
            # On an AFFLICTION_MATTER house a bare "the lord is strong" would carry a
            # mitigating implicature the v14 ledger explicitly reads the opposite way —
            # reuse the ledger's own shipped gloss (bphs-doctrine-reviewer finding).
            if led.lord_strong and "AFFLICTION_MATTER" in led.flags:
                pillar.append("the lord is strong — on this affliction matter it feeds the "
                              "affliction, never rescues")
            else:
                pillar.append(f"the lord is {'strong' if led.lord_strong else 'weak'}")
        if led.karaka_strong is not None:
            if not led.karaka_intact:
                pillar.append("the karaka is broken — the affliction veto the headline obeyed")
            else:
                pillar.append(f"the karaka {'strong' if led.karaka_strong else 'weak'}")
        if pillar:
            bits.append("; ".join(pillar))

    hs = next((row for row in r.house_strength if row.house == house), None)
    if hs is not None and hs.bhava_bala_rank is not None:
        rank = hs.bhava_bala_rank
        if rank == 1 and verdict == "afflicted":
            bits.append("it carries the highest Bhava Bala of the twelve — the "
                        "strong-yet-afflicted tendency above applies: the difficulty tends "
                        "to be delivered with unusual force and certainty")
        elif rank == 1 and verdict == "favourable":
            bits.append("it carries the highest Bhava Bala of the twelve — its good "
                        "indications the most fully enjoyed")
        elif rank == 12 and verdict == "favourable":
            bits.append("it stands on the chart's lowest Bhava Bala — real good, mildly or "
                        "partly enjoyed (a tendency, not an absolute rule)")
        elif rank == 12 and verdict == "afflicted":
            # Attributed to the report's own v8 magnitude reading, NOT to GBB-9 directly —
            # GBB-9:32-34 is enjoyment-framed; the symmetric extension to an affliction's
            # fullness is this project's synthesis (bphs-doctrine-reviewer finding).
            bits.append("it stands on the chart's lowest Bhava Bala — by the magnitude "
                        "reading in the strength cross-check above, even its difficulty "
                        "tends to be less fully manifest (a tendency, not a rule — and never "
                        "a reprieve)")
        else:
            bits.append(f"it stands {_ordinal(rank)} of 12 in Bhava Bala (a magnitude, not "
                        f"a direction)")
        if hs.sav_bindus is not None:
            bits[-1] += (f", with {hs.sav_band} Ashtakavarga support ({hs.sav_bindus} "
                         f"bindus)")

    ht_row = next((x for x in r.preponderance.houses if x.house == house), None)
    if ht_row is not None:
        bearing_names = [t.name[len("yoga: "):] for t in ht_row.testimonies
                         if t.name.startswith("yoga: ")]
        if bearing_names:
            bits.append(f"fired yogas bearing on it (via their planets' own/occupy/aspect): "
                        f"{', '.join(bearing_names)}")
        # Counts are labelled by TENOR (favourable/adverse, the preponderance table's own
        # column sense) — "for/against" read as headline-relative and inverted on an
        # afflicted headline (bphs-doctrine-reviewer finding).
        if ht_row.status == "well-corroborated":
            bits.append(f"its witnesses agree ({ht_row.favourable} favourable, "
                        f"{ht_row.adverse} adverse) — a preponderance in the headline's own "
                        f"direction")
        elif ht_row.status == "contested":
            bits.append(f"its witnesses split ({ht_row.favourable} favourable, "
                        f"{ht_row.adverse} adverse) — disclosure, not re-weighing: the "
                        f"headline follows the weakest-link rule and stands")
        else:
            bits.append("for the sub-matter split behind this headline, see the Split "
                        "status note above")
    return ". ".join(b[0].upper() + b[1:] for b in bits) + "."


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
    its own favourable Gochara transit — Raman's own reason this matters (HTJAH-II:4679-4687:
    "Transits are always secondary in importance. They are like catalytic agents. All
    conclusions must be primarily drawn on the basis of Dasa-vichara" — i.e. a transit only
    catalyses what the running period permits) applied concretely: the clearest confirmation
    is when the period's own
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
class YogaTiming:
    """A stretch where a fired yoga's own constituent lord runs as MD or AD — Raman's own rule
    that a yoga ripens in its lord's Dasha or Bhukti made concrete (HTJAH-I:4324), with magnitude
    scaling to that lord's strength/vargottama (HTJAH-I:5372: "the rank conferred is consistent
    with the strength of the lords concerned; when they attain Vargottama the position acquired
    is the highest"). `quality` reuses `vimshottari.lord_quality` — the SAME strength read
    Life-narrative already computes for its own MD/AD delivery quality (previously computed
    there but never rendered); nothing here is a new judgment."""
    yoga_id: str
    yoga_name: str
    yoga_kind: str
    planet: str
    role: str                    # "MD" | "AD"
    period_start_jd: float
    period_end_jd: float
    quality: "vd.LordQuality"


def _md_runs(timeline: DashaTimeline) -> tuple[tuple[str, float, float], ...]:
    """Collapse the windowed bhukti-level timeline into contiguous Mahadasha spans — one row per
    MD run, not one per bhukti (a windowed timeline lists ~9 bhuktis per MD; a yoga-lord MD
    confluence is one continuous stretch, not 9 near-duplicate rows)."""
    runs: list[list] = []
    for tp in timeline.periods:
        p = tp.period
        if runs and runs[-1][0] == p.maha and runs[-1][2] == p.start_jd:
            runs[-1][2] = p.end_jd
        else:
            runs.append([p.maha, p.start_jd, p.end_jd])
    return tuple(tuple(r) for r in runs)


def _yoga_dasha_confluences(
    chart: RamanChart, timeline: DashaTimeline, yogas: tuple[FiredYoga, ...],
) -> tuple[YogaTiming, ...]:
    """When does each fired yoga's own lord run as MD or AD — for every yoga whose constituent
    lords `_yoga_planets` can structurally resolve (a fixed named planet, a lordship that is a
    deterministic function of the Lagna, or a small exactly-checkable candidate set — Pancha
    Mahapurusha, Gajakesari, Budha-Aditya, the Raja/Dhana lordship yogas, the flank/benefic
    yogas, and more). The Nabhasa whole-chart-distribution yogas (Asraya/Dala/Sankhya/Akriti)
    have no single "lord" in Raman's own definition and contribute no rows here — a genuine
    coverage gap the renderer states plainly, not a judgment that they lack timing."""
    out: list[YogaTiming] = []
    md_runs = _md_runs(timeline)
    for y in yogas:
        pls = _yoga_planets(chart, y)
        if not pls:
            continue
        for lord, start_jd, end_jd in md_runs:
            if lord in pls:
                out.append(YogaTiming(y.id, y.name, y.kind, lord, "MD", start_jd, end_jd,
                                      vd.lord_quality(chart, lord)))
        for tp in timeline.periods:
            p = tp.period
            if p.antar is not None and p.antar in pls:
                out.append(YogaTiming(y.id, y.name, y.kind, p.antar, "AD", p.start_jd, p.end_jd,
                                      vd.lord_quality(chart, p.antar)))
    out.sort(key=lambda w: w.period_start_jd)
    return tuple(out)


@dataclass(frozen=True)
class HouseStrengthRow:
    """One house's verdict cross-checked against two INDEPENDENT strength measures Raman also
    uses — Bhava Bala (the lord's Shadbala + Bhavadig + Bhava-Drig, RANKED 1st-strongest to
    12th-weakest across the chart; Raman gives no numeric cutoff, only a ranking, GBB-9:332) and
    Sarvashtakavarga bindus (that house's sign, average 28 per sign out of 337 total). Neither
    measure changes `verdict` — the same rollup the House-by-house section already shows; this
    only says whether that verdict stands on strong or shaky ground."""
    house: int
    bhava_bala: Optional[float]
    bhava_bala_rank: Optional[int]        # 1 = strongest of the 12, 12 = weakest
    sav_bindus: Optional[int]
    sav_band: str                         # "strong" | "average" | "weak" | "n/a" — SAME wording
                                           # as house_template._ashtakavarga_overlay's own band
    verdict: str


def _house_strength_rows(
    proformas: tuple[HouseProforma, ...], asc_sign: int, sav: dict[int, int],
    bhava_balas: dict[int, float],
) -> tuple[HouseStrengthRow, ...]:
    """Cross-tabulate Bhava Bala rank + SAV band against each house's own (unchanged) verdict —
    pure selection and ranking of values the rest of the report already computes
    (`HouseProforma.rollup`, the SAME `bhava_balas` dict `SYN_R6_BHAVA_BALA_RANK` already ranks
    for its one-line fired insight, and Sarvashtakavarga bindus); no new judgment — this is the
    full 12-house table version of that one-liner."""
    ranked = sorted(bhava_balas, key=lambda h: -bhava_balas[h])
    rank_of = {house: i + 1 for i, house in enumerate(ranked)}
    rows: list[HouseStrengthRow] = []
    for pf in proformas:
        sign = ((asc_sign - 1) + (pf.house - 1)) % 12 + 1
        bindus = sav.get(sign)
        # SAME thresholds/wording as house_template._ashtakavarga_overlay (the House-by-house
        # prose's own band rule) — the two used to disagree (this table's old >28/<28 cutoff
        # called 26-27 bindus "below average" while the prose called the identical count
        # "average"); aligned here rather than touching the older, more widely-depended-on
        # judge-layer function.
        band = ("n/a" if bindus is None else
               "strong" if bindus >= 30 else
               "weak" if bindus <= 25 else "average")
        rows.append(HouseStrengthRow(
            house=pf.house, bhava_bala=bhava_balas.get(pf.house),
            bhava_bala_rank=rank_of.get(pf.house),
            sav_bindus=bindus, sav_band=band, verdict=pf.rollup))
    return tuple(rows)


@dataclass(frozen=True)
class IshtaKashtaPeriod:
    """One bhukti's Ishta/Kashta reading, painted across the WHOLE windowed timeline — Raman's
    rule that a planet with more Ishta Phala inclines to good results in its Dasha/Bhukti, more
    Kashta to harder ones (GBB-10:134), and the stronger (by Shadbala) period-lord's character
    prevails in the sub-period (GBB-10:145-152 states only the MD-predominates direction; no
    converse is asserted — the same one-directional reading `SYN_R5_ISHTA_KASHTA_PERIOD` already
    encodes for the CURRENT period only). Both Ishta/Kashta and Shadbala are natal-fixed values —
    this is a pure lookup onto the already-built timeline, not a new computation."""
    maha: str
    antar: Optional[str]
    start_jd: float
    end_jd: float
    maha_lean: Optional[str]        # "good" | "hard" | "balanced" | None (no data)
    antar_lean: Optional[str]
    prevails: Optional[str]         # e.g. "Jupiter's character prevails" (MD-predominates only)


def _ishta_kashta_lean(chart: RamanChart, planet: Optional[str]) -> Optional[str]:
    if planet is None:
        return None
    p = chart.planets.get(planet)
    if p is None or p.ishta is None or p.kashta is None:
        return None
    if p.ishta > p.kashta:
        return "good"
    if p.kashta > p.ishta:
        return "hard"
    return "balanced"


def _ishta_kashta_periods(
    chart: RamanChart, timeline: DashaTimeline,
) -> tuple[IshtaKashtaPeriod, ...]:
    """Paint every bhukti in the windowed timeline with its MD/AD lords' Ishta/Kashta lean —
    the full-timeline version of `SYN_R5_ISHTA_KASHTA_PERIOD`'s current-period-only one-liner."""
    out: list[IshtaKashtaPeriod] = []
    for tp in timeline.periods:
        p = tp.period
        prevails = None
        if p.antar is not None and p.antar != p.maha:
            rm, ra = _rupas(chart, p.maha), _rupas(chart, p.antar)
            if rm is not None and ra is not None and rm >= ra:
                prevails = f"{p.maha}'s character prevails"
        out.append(IshtaKashtaPeriod(
            maha=p.maha, antar=p.antar, start_jd=p.start_jd, end_jd=p.end_jd,
            maha_lean=_ishta_kashta_lean(chart, p.maha),
            antar_lean=_ishta_kashta_lean(chart, p.antar), prevails=prevails))
    return tuple(out)


@dataclass(frozen=True)
class MdLordCondition:
    """One Mahadasha RUN's own lord condition, painted across the WHOLE windowed timeline —
    extends `SYN_R4_MD_LORD_CONDITION`'s current-period-only reading. Raman: a Dasha's result is
    modified by its lord's strength/weakness and Navamsa disposition, reaching its maximum only
    when strong in BOTH the rasi and navamsa charts (HPA-24:51-86). Strength, vargottama and
    navamsa are all natal-fixed — a pure lookup onto the already-built MD timeline (via
    `_md_runs`), not a new computation. Scoped to the MD lord only, matching SYN_R4's own scope
    (it never checks the AD/bhukti lord)."""
    maha: str
    start_jd: float
    end_jd: float
    strong: Optional[bool]      # Shadbala is_powerful; None if no Shadbala data
    vargottama: bool
    navamsa_sign: Optional[int]
    at_maximum: bool            # strong AND vargottama — HPA-24's stated maximum


@dataclass(frozen=True)
class DasaKakshyaInterval:
    """One eighth of a Mahadasha run, symbolically ruled in Kakshya order (ASP-12:174-182).

    The judgment is Raman's ch.XII working: the interval of a ruler that did not donate a
    bindu to the MD lord's natal sign (in the lord's own Ashtakavarga) runs adverse
    (ASP-12:211-214), relieved when the ruler's own signs hold optimum bindus there
    (ASP-12:215-219). Raman introduces the division as "some scholars opine" and then works
    it over his own signature — a timing lens, never a verdict input."""
    maha: str
    ruler: str
    start_jd: float
    end_jd: float
    donated: bool
    neutralised: bool
    reading: str          # favourable | adverse-neutralised | adverse


def _dasa_kakshya_rows(chart: RamanChart, timeline: DashaTimeline) -> tuple[DasaKakshyaInterval, ...]:
    """The eightfold Kakshya division of each windowed Mahadasha run (ASP-12), via
    `kakshya_timing.kakshya_intervals`. Nodal MDs yield no rows — the scheme is undefined
    for a lord with no Ashtakavarga, not adverse."""
    from app.raman_saab.primitives import kakshya_timing as kt
    out: list[DasaKakshyaInterval] = []
    for maha, start_jd, end_jd in _md_runs(timeline):
        for iv in kt.kakshya_intervals(chart, maha, start_jd, end_jd):
            reading = ("favourable" if iv.donated
                       else "adverse-neutralised" if iv.neutralised else "adverse")
            out.append(DasaKakshyaInterval(
                maha=maha, ruler=iv.ruler, start_jd=iv.start_jd, end_jd=iv.end_jd,
                donated=iv.donated, neutralised=iv.neutralised, reading=reading))
    return tuple(out)


def _md_lord_conditions(
    chart: RamanChart, timeline: DashaTimeline,
) -> tuple[MdLordCondition, ...]:
    """The full-timeline version of `SYN_R4_MD_LORD_CONDITION`'s current-MD-only one-liner —
    one row per contiguous Mahadasha run (`_md_runs`, not per bhukti, since the rule is scoped
    to the MD lord alone)."""
    out: list[MdLordCondition] = []
    for maha, start_jd, end_jd in _md_runs(timeline):
        pos = chart.planets.get(maha)
        if pos is None:
            continue
        strong = _strong(chart, maha)
        out.append(MdLordCondition(
            maha=maha, start_jd=start_jd, end_jd=end_jd, strong=strong,
            vargottama=pos.vargottama, navamsa_sign=pos.navamsa_sign,
            at_maximum=bool(strong) and pos.vargottama))
    return tuple(out)


@dataclass(frozen=True)
class MarakaSaturnConfluence:
    """A stretch where a maraka-tier Bhukti (from the ayurdaya-anchored `death_window`) overlaps
    transiting Saturn sitting on the NATAL Saturn's own rasi or trine — Raman's classical "last
    signal" of a maraka period (HTJAH-II:4846-4849: the signal is given by Ayushkaraka Saturn
    transiting the Rasi... he occupied at birth, or its trines). RASI HALF ONLY — the Amsa
    (navamsa) half of the classical signature is not computed here, same honest scope as
    `SYN_R9_MARAKA_SATURN_SIGNAL`'s current-period-only reading.

    STRICTLY A STATEMENT OF THE METHOD, NOT A PREDICTION: this project's own real-outcome
    validation measured NO death-timing signal from maraka checks generally (see
    docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md) — this section exists to show what Raman's
    textbook method says, faithfully, never as a strengthened death signal."""
    maha: str
    antar: str
    window_start_jd: float      # the death_window's own bounds (ayurdaya-anchored)
    window_end_jd: float
    overlap_start_jd: float     # intersection with Saturn's rasi/trine transit segment
    overlap_end_jd: float
    sign: int
    score: int                  # the DeathWindow's own maraka tier-score (MD-weight + AD-weight)


def _maraka_saturn_confluences(
    chart: RamanChart, ref_jd: float, ayanamsa: str,
) -> tuple[MarakaSaturnConfluence, ...]:
    """Cross-reference the ayurdaya-anchored maraka death-window (`vimshottari.death_window`)
    against transiting Saturn's own rasi/trine signal (HTJAH-II:4846-4849). Saturn's transit is
    computed FRESH across the death-window's own span — which can run decades beyond the
    report's usual -10/+20-year display window, since the death window is anchored to the
    ayurdaya estimate, not to "today" — rather than reused from the report's own
    `gochara_outlook`, which would silently miss the relevant years for most charts."""
    dws = vd.death_window(chart)
    sat = chart.planets.get("Saturn")
    if not dws or sat is None:
        return ()
    lo_jd = min(dw.start_jd for dw in dws)
    hi_jd = max(dw.end_jd for dw in dws)
    years_back = max(0.0, (ref_jd - lo_jd) / _DAYS_PER_VEDIC_YEAR)
    years_forward = max(0.0, (hi_jd - ref_jd) / _DAYS_PER_VEDIC_YEAR)
    sat_segments = tr.gochara_timeline(
        chart, ref_jd, years_back, years_forward, ayanamsa=ayanamsa,
        planets=("Saturn",)).get("Saturn", ())
    trines = {sat.sign, (sat.sign - 1 + 4) % 12 + 1, (sat.sign - 1 + 8) % 12 + 1}
    out: list[MarakaSaturnConfluence] = []
    for dw in dws:
        for seg in sat_segments:
            if seg.sign not in trines:
                continue
            lo, hi = max(dw.start_jd, seg.start_jd), min(dw.end_jd, seg.end_jd)
            if lo < hi:
                out.append(MarakaSaturnConfluence(
                    maha=dw.maha, antar=dw.antar, window_start_jd=dw.start_jd,
                    window_end_jd=dw.end_jd, overlap_start_jd=lo, overlap_end_jd=hi,
                    sign=seg.sign, score=dw.score))
    out.sort(key=lambda c: c.overlap_start_jd)
    return tuple(out)


@dataclass(frozen=True)
class AvDashaSeat:
    """One Mahadasha run's lord graded by his OWN Ashtakavarga bindus at his natal seat —
    CLASSICAL_NONCITABLE (Patel ch015:996-1034: 5+ bindus auspicious, <=3 adverse, 4 mixed),
    under Raman's own caveat that Ashtakavarga "does not seem to be quite reliable"
    (HTJAH-II:4453-4456). Extends `SYN_N7_AV_DASHA_SEAT`'s current-MD-only reading across the
    whole windowed timeline. Bindus are natal-fixed — a pure lookup onto `_md_runs`, not a new
    computation. AV-TIER: never overrides a Raman-band insight elsewhere in this report."""
    maha: str
    start_jd: float
    end_jd: float
    sign: int
    bindus: Optional[int]
    read: str            # "auspicious" | "adverse" | "mixed" | "no data"


def _av_dasha_seats(chart: RamanChart, timeline: DashaTimeline) -> tuple[AvDashaSeat, ...]:
    """The full-timeline version of `SYN_N7_AV_DASHA_SEAT`'s current-MD-only one-liner — one row
    per contiguous Mahadasha run. Nodes (Rahu/Ketu) carry no classical Ashtakavarga and are
    skipped, same as the existing one-liner checker."""
    out: list[AvDashaSeat] = []
    for maha, start_jd, end_jd in _md_runs(timeline):
        pos = chart.planets.get(maha)
        if pos is None:
            continue
        try:
            bav = ashtakavarga.bhinnashtakavarga(chart, maha)
        except Exception:  # noqa: BLE001 — nodes have no BAV
            bav = None
        bindus = bav.get(pos.sign) if bav else None
        read = ("no data" if bindus is None else
               "auspicious" if bindus >= 5 else
               "adverse" if bindus <= 3 else "mixed")
        out.append(AvDashaSeat(
            maha=maha, start_jd=start_jd, end_jd=end_jd, sign=pos.sign, bindus=bindus, read=read))
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
    yoga_timing: tuple[YogaTiming, ...]               # when a yoga's own lord runs as MD/AD
    house_strength: tuple[HouseStrengthRow, ...]      # Bhava Bala rank + SAV band per house
    ishta_kashta: tuple[IshtaKashtaPeriod, ...]       # Ishta/Kashta lean per MD/AD, whole timeline
    md_condition: tuple[MdLordCondition, ...]         # MD lord strength/vargottama, whole timeline
    maraka_saturn: tuple[MarakaSaturnConfluence, ...]  # maraka window x Saturn rasi/trine signal
    av_dasha_seats: tuple[AvDashaSeat, ...]           # MD lord's own BAV bindus, whole timeline
    dasa_kakshya: tuple[DasaKakshyaInterval, ...]     # eightfold Kakshya split per MD run (ASP-12)
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
    ruler: "RulerOfNativity"                         # Raman's first-impression card (v13)
    preponderance: "PreponderanceReading"            # per-house testimony ledgers (v14)
    life_chapters: "LifeChapters"                    # one woven chapter per MD run (v15)
    digest: "InsightDigest"                          # ranked "what matters most" (pure re-read)
    health_readout: "HealthReadout"                  # health/vulnerability read-out (v17)
    planet_bios: tuple = ()                          # dominant-graha biographies (v20, S2)
    yoga_deep: tuple = ()                            # per-yoga deep-reads (v21)
    arishta: object = None                           # Arishta & Bhanga chapter (v22)
    profession: object = None                        # profession synthesis (v23)
    wealth: object = None                            # the wealth chapter (v24)
    marriage: object = None                          # marriage monograph (v25)
    children: object = None                          # children chapter (v26)
    psych: object = None                             # psychological profile (v27)
    decades: object = None                           # decade indication timeline (v28)
    life_synthesis: object = None                    # the biography-closing chapter (v29)
    karmic: object = None                            # Jaimini karmic evolution (v30)


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
    #: S3 (2026-08-03, append-only): tensions WOVEN, never hidden — one sentence per
    #: already-detected conflict, both poles named, the governing v18 rule cited.
    reconciliations: tuple[str, ...] = ()


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
    #: S5 (2026-08-03, append-only): MD boundaries where the Ishta/Kashta lean flips —
    #: (window label, what changes). Pure re-read of the timeline + ishta_kashta rows.
    turning_points: tuple[tuple[str, str], ...] = ()


_EMPTY_NICHOD: Final[Nichod] = Nichod(
    identity="", strength_profile="", longevity="", yogas="", stands_out="",
    matters_tally="", current_period="", live_transits="", spotlight=None, caution=None,
    essence="",
)


@dataclass(frozen=True)
class HealthIndicatorRow:
    """One physical-vulnerability indicator, re-read from an already-computed verdict."""
    area: str            # e.g. "House 6 — resistance to illness and rivals"
    verdict: str         # the existing verdict/dignity word, unchanged
    note: str            # descriptive detail, guard-safe idiom only
    provenance: str      # which existing layer said it (proforma / D-30 core / HPA-14 ...)


@dataclass(frozen=True)
class HealthReadout:
    """The health/vulnerability READ-OUT (v17) — a report-only synthesis of verdicts the
    report already computes elsewhere: the D-30 health core (H1/H6/H8 + Moon/Mercury karakas
    + balarishta), the H12 proforma rollup, the maraka tiers, and the longevity band.
    NOTHING here is a new judgment, a medical statement, or a prediction — the caveat field
    is rendered with the section in every surface."""
    rows: tuple[HealthIndicatorRow, ...]
    maraka_tiers: tuple[tuple[str, str], ...]    # (graha, tier), primary/secondary/tertiary
    drekkana22_lord: str
    navamsa64_lord: str
    maraka_period_now: bool
    longevity_band: str                          # e.g. "Madhyayu — a band, not a date"
    caveat: str


_EMPTY_HEALTH_READOUT: Final[HealthReadout] = HealthReadout(
    rows=(), maraka_tiers=(), drekkana22_lord="", navamsa64_lord="",
    maraka_period_now=False, longevity_band="", caveat="",
)

#: The one fixed caveat sentence for the health read-out — composed from the report's two
#: existing framings (the "never medical statements" comment and the maraka-section
#: method-not-prediction idiom). Deliberately free of every guard token.
_HEALTH_CAVEAT: Final[str] = (
    "A statement of the method, not a prognosis: these rows re-read verdicts computed "
    "elsewhere in this report as Raman's method describes a chart's tendencies — never "
    "medical statements, never a prediction (the project's own validation measured no "
    "real-outcome signal; REAL_OUTCOME_GENERALIZATION.md)."
)


def build_health_readout(r: DetailedReport) -> HealthReadout:
    """Second-pass synthesis (the `build_preponderance` species): selects and re-labels
    already-computed health-adjacent verdicts. Returns the empty sentinel on sparse/Track-B
    charts where the D-30 health core cannot be assembled."""
    from app.raman_saab.judges.trimsamsa_health_reading import build_trimsamsa_health_reading
    try:
        core = build_trimsamsa_health_reading(r.chart).core
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        return _EMPTY_HEALTH_READOUT

    rows: list[HealthIndicatorRow] = [
        HealthIndicatorRow(
            area="House 1 — constitution",
            verdict=core.health_verdict,
            note=(f"lagna lord {core.lagna_lord} in house {core.lagna_lord_house}, "
                  f"dignity {core.lagna_lord_dignity}"),
            provenance="H1 'health' signification (house proforma)"),
        HealthIndicatorRow(
            area="House 6 — resistance to chronic illness",
            verdict=core.disease_verdict,
            note="the 6th is read for illness and rivals; its verdict is the one shown in "
                 "the house-by-house section",
            provenance="H6 'disease_chronic' signification (house proforma)"),
        HealthIndicatorRow(
            area="House 8 — longevity lean",
            verdict=core.longevity_verdict,
            note="a lean only — the engine defers lifespan to the Longevity section's band",
            provenance="H8 'longevity' signification (house proforma)"),
    ]
    if len(r.proformas) >= 12:
        rows.append(HealthIndicatorRow(
            area="House 12 — confinement and loss",
            verdict=r.proformas[11].rollup,
            note=f"house rollup under lord {r.proformas[11].lord}; per-signification detail "
                 "sits in the house-by-house section",
            provenance="H12 rollup (house proforma)"))
    rows.append(HealthIndicatorRow(
        area="Moon — mind (manas) karaka",
        verdict=str(core.moon_dignity),
        note=("afflicted by " + ", ".join(core.moon_afflictions)
              if core.moon_afflictions else "no natural-malefic affliction"),
        provenance="D-30 health core (Raman's single-chart method)"))
    rows.append(HealthIndicatorRow(
        area="Mercury — nervous-system karaka",
        verdict=str(core.mercury_dignity),
        note=("afflicted by " + ", ".join(core.mercury_afflictions)
              if core.mercury_afflictions else "no natural-malefic affliction"),
        provenance="D-30 health core (Raman's single-chart method)"))
    bal = ("applies" if core.balarishta_applies and not core.balarishta_cancelled
           else "cancelled" if core.balarishta_cancelled else "does not apply")
    rows.append(HealthIndicatorRow(
        area="Balarishta — early-childhood danger",
        verdict=bal,
        note="; ".join(core.balarishta_reasons) if core.balarishta_reasons else "no yoga fires",
        provenance="HPA-14 balarishta primitive"))

    mp = getattr(r.chart, "maraka_points", None)
    tiers = tuple((u.graha, u.tier) for u in mp.units) if mp is not None else ()
    return HealthReadout(
        rows=tuple(rows),
        maraka_tiers=tiers,
        drekkana22_lord=mp.drekkana22_lord if mp is not None else "",
        navamsa64_lord=mp.navamsa64_lord if mp is not None else "",
        maraka_period_now=r.maraka_period_now,
        longevity_band=f"{r.longevity_class} — a band, not a date",
        caveat=_HEALTH_CAVEAT,
    )


@dataclass(frozen=True)
class RulerOfNativity:
    """Raman's own opening move, made nowhere else in the report: "In order to obtain a first
    impression we must first of all consider the ruler of the nativity" (HTJAH-I:16001-16002 —
    where the ruler he examines is the LAGNA LORD), and separately "The strongest planet in the
    horoscope determines the predominance of the physical, mental and spiritual peculiarities
    of the person" (HTJAH-I:6248-6250). These are TWO distinct concepts that Raman's own worked
    chart praises when they coincide: "He is by far the strongest planet in the horoscope and
    since he is also the Lagnadhipati, the foundation is quite sound" (HTJAH-I:3880-3882). For
    nature and appearance he compares the strongest planet against the lord of the Navamsa
    Lagna — the more powerful stamps them (HTJAH-I:3892-3897). Presentation-only: every field
    is a pure re-read of values the report already computes; no verdict is touched."""
    lagna_lord: str                                   # the "ruler of the nativity" proper
    lagna_lord_house: Optional[int]
    lagna_lord_sign: Optional[int]
    strongest: Optional[str]                          # strongest Shadbala-bearing graha
    strongest_rupas: Optional[float]
    coincide: bool                                    # strongest == lagna lord
    navamsa_lagna_lord: Optional[str]
    nl_lord_rupas: Optional[float]
    stamps_nature: Optional[str]                      # HTJAH-I:3892-3897 comparison winner
    temperament: Optional[str]                        # _RULER_TEMPERAMENT; None for Moon (absent)
    functional_nature: Optional[str]                  # of the strongest, for this Lagna
    avastha: Optional[str]                            # Deeptadi state of the strongest
    ik_lean: Optional[str]                            # "good" | "hard" | "balanced"
    house: Optional[int]                              # placement of the strongest
    sign: Optional[int]
    navamsa_sign: Optional[int]
    vargottama: bool
    retrograde: bool
    yogas_involving: tuple[str, ...]                  # fired yogas the strongest participates in
    md_windows: tuple[tuple[float, float], ...]       # its own MD runs inside the window
    gochara_good_windows: tuple[tuple[float, float], ...]
    slow_mover: bool                                  # tracked by the 4-planet Gochara outlook?
    signature: str                                    # the knitted first-impression paragraph


_EMPTY_RULER: Final[RulerOfNativity] = RulerOfNativity(
    lagna_lord="", lagna_lord_house=None, lagna_lord_sign=None, strongest=None,
    strongest_rupas=None, coincide=False, navamsa_lagna_lord=None, nl_lord_rupas=None,
    stamps_nature=None, temperament=None, functional_nature=None, avastha=None, ik_lean=None,
    house=None, sign=None, navamsa_sign=None, vargottama=False, retrograde=False,
    yogas_involving=(), md_windows=(), gochara_good_windows=(), slow_mover=False, signature="",
)


def build_ruler(r: DetailedReport) -> RulerOfNativity:
    """Assemble the first-impression card from an already-fully-built DetailedReport — pure
    re-reads (Shadbala totals, functional natures, Deeptadi states, fired yogas, MD runs and
    Gochara segments the report renders elsewhere); nothing is judged here."""
    chart = r.chart
    lagna_lord = SIGN_LORDS[chart.asc_sign]
    ll_pos = chart.planets.get(lagna_lord)

    order = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    sb = [(n, chart.planets[n].shadbala_rupas.total / 60.0) for n in order
          if n in chart.planets and chart.planets[n].shadbala_rupas is not None]
    strongest: Optional[str] = None
    rupas: Optional[float] = None
    if sb:
        # max by rupas; an exact tie is broken by canonical planet order for determinism —
        # disclosed here rather than silent: an exact float-sum rupa tie between two grahas is
        # practically unreachable, so the tie-break is reader-invisible by construction (the
        # nature/appearance comparison below, where a tie IS meaningful doctrine, abstains
        # instead — HTJAH-I:3892-3897 gives no tiebreaker).
        strongest, rupas = max(sb, key=lambda kv: (kv[1], -order.index(kv[0])))

    nl_lord: Optional[str] = None
    if r.synthesis.navamsa_lagna in _SIGN_NAME[1:]:
        nl_lord = SIGN_LORDS[_SIGN_NAME.index(r.synthesis.navamsa_lagna)]
    nl_rupas: Optional[float] = None
    if nl_lord is not None:
        np_ = chart.planets.get(nl_lord)
        if np_ is not None and np_.shadbala_rupas is not None:
            nl_rupas = np_.shadbala_rupas.total / 60.0
    stamps: Optional[str] = None
    if strongest is not None and nl_lord is not None:
        if nl_lord == strongest:
            stamps = strongest
        elif rupas is not None and nl_rupas is not None and rupas != nl_rupas:
            stamps = strongest if rupas > nl_rupas else nl_lord

    pos = chart.planets.get(strongest) if strongest else None
    avastha = None
    if strongest is not None:
        avastha = next((x.split(" ", 1)[1] for x in r.synthesis.deeptadi
                        if x.startswith(strongest + " ")), None)

    yogas_involving: list[str] = []
    if strongest is not None:
        for y in r.yogas:
            pls = _yoga_planets(chart, y)
            if pls and strongest in pls and y.name not in yogas_involving:
                yogas_involving.append(y.name)

    md_windows = tuple((s0, e0) for m, s0, e0 in _md_runs(r.timeline) if m == strongest)
    slow_mover = strongest in r.gochara_outlook if strongest else False
    good_windows = tuple((seg.start_jd, seg.end_jd)
                         for seg in r.gochara_outlook.get(strongest or "", ())
                         if seg.gochara_good)

    coincide = strongest is not None and strongest == lagna_lord
    fn = dict(r.overview.functional_natures).get(strongest) if strongest else None

    bits: list[str] = []
    ll_bit = f"{lagna_lord}, lord of the {_SIGN_NAME[chart.asc_sign]} Lagna"
    if ll_pos is not None:
        ll_bit += f", placed in house {ll_pos.rasi_house}"
    bits.append(f"The first impression begins with the ruler of the nativity: {ll_bit}.")
    if strongest is not None and rupas is not None:
        s_bit = f"The strongest planet by Shadbala is {strongest} ({rupas:.1f} rupas)"
        if coincide:
            s_bit += " — the ruler itself, and \"the foundation is quite sound\""
        bits.append(s_bit + ".")
        if stamps is not None and nl_lord is not None and nl_lord != strongest:
            bits.append(f"As between the strongest planet and the lord of the Navamsa Lagna "
                        f"({nl_lord}), {stamps} is the more powerful and stamps the nature "
                        f"and appearance.")
        temper = _RULER_TEMPERAMENT.get(strongest)
        if temper is not None:
            bits.append(f"Classical temperament for a {strongest}-dominant chart: {temper}.")
        cond_bits = []
        if fn is not None:
            cond_bits.append(f"{fn} for this Lagna")
        if avastha is not None:
            cond_bits.append(f"in {avastha} avastha")
        lean = _ishta_kashta_lean(chart, strongest)
        if lean is not None:
            cond_bits.append(f"with a {lean} Ishta/Kashta lean")
        if cond_bits:
            bits.append(f"{strongest} stands {', '.join(cond_bits)}.")
    else:
        bits.append("No Shadbala is available on this chart, so the strongest planet cannot "
                    "be determined by strength — nothing is guessed in its place.")
    signature = " ".join(bits)

    return RulerOfNativity(
        lagna_lord=lagna_lord,
        lagna_lord_house=ll_pos.rasi_house if ll_pos is not None else None,
        lagna_lord_sign=ll_pos.sign if ll_pos is not None else None,
        strongest=strongest, strongest_rupas=rupas, coincide=coincide,
        navamsa_lagna_lord=nl_lord, nl_lord_rupas=nl_rupas, stamps_nature=stamps,
        temperament=_RULER_TEMPERAMENT.get(strongest) if strongest else None,
        functional_nature=fn, avastha=avastha,
        ik_lean=_ishta_kashta_lean(chart, strongest) if strongest else None,
        house=pos.rasi_house if pos is not None else None,
        sign=pos.sign if pos is not None else None,
        navamsa_sign=pos.navamsa_sign if pos is not None else None,
        vargottama=pos.vargottama if pos is not None else False,
        retrograde=pos.retrograde if pos is not None else False,
        yogas_involving=tuple(yogas_involving), md_windows=md_windows,
        gochara_good_windows=good_windows, slow_mover=slow_mover, signature=signature,
    )


#: Which D1 house each matter-varga dashboard matter is anchored to — verified against each
#: deep reader's OWN documented anchor: wealth→2, siblings→3, property→4, comforts→4,
#: spiritual→9 (`matter_varga_reading.py` module docstring); mother→4 (HTJAH-I:4387) and
#: father→9 (`dwadasamsa_parents_reading.py`); children→5 (`saptamsa_reading`); marriage→7
#: (`navamsa_marriage_reading`); career→10 (`dasamsa_career_reading`); education→4 (AFB-6:23,
#: HTJAH-I:4701 — `siddhamsa_education_reading.py`); health→6 (`trimsamsa_health_reading`,
#: the disease/chronic axis). Houses 1, 8, 11 and 12 have no dedicated matter reader — they
#: get an explicit "absent" testimony row, never a guessed one.
_MATTER_HOUSE: Final[dict[str, int]] = {
    "wealth": 2, "siblings": 3, "mother": 4, "property": 4, "comforts": 4, "education": 4,
    "children": 5, "health": 6, "marriage": 7, "father": 9, "spiritual": 9, "career": 10,
}


@dataclass(frozen=True)
class Testimony:
    """One already-computed axis, restated as a named witness for or against a house's own
    headline verdict. `lean` is direction-of-corroboration only — never a re-judgment."""
    name: str
    value: str
    lean: str        # "favourable-leaning" | "adverse-leaning" | "neutral" | "absent"


@dataclass(frozen=True)
class HouseTestimonies:
    """One house's full testimony ledger. The `verdict` is the authoritative House-by-house
    rollup, displayed but deliberately EXCLUDED from its own tally (counting the headline as a
    witness to itself would be circular — the ledger exists to test the headline against its
    witnesses). Counts are an inventory in Raman's own qualitative vocabulary (HTJAH-I:8870
    "preponderance"), never a score: Raman states no numeric N-testimonies rule (HTJAH-I:495
    says only "all these must be properly weighed")."""
    house: int
    verdict: str
    testimonies: tuple[Testimony, ...]
    favourable: int
    adverse: int
    neutral: int
    absent: int
    preponderance: str   # "benefic" | "adverse" | "evenly balanced" | "insufficient"
    status: str          # "well-corroborated" | "contested" | "thinly attested" | "(mixed/undecided headline)"


@dataclass(frozen=True)
class PreponderanceReading:
    """The whole-chart testimony cross-tabulation (v14) — Raman's 'judgment is the summing up
    of the influence of planets' (HTJAH-I:983-991) applied to every already-computed axis the
    report holds, per house. Presentation-only; no verdict is touched."""
    houses: tuple[HouseTestimonies, ...]
    most_corroborated_favourable: Optional[int]
    most_corroborated_afflicted: Optional[int]
    most_contested: Optional[int]


_EMPTY_PREPONDERANCE: Final[PreponderanceReading] = PreponderanceReading(
    houses=(), most_corroborated_favourable=None, most_corroborated_afflicted=None,
    most_contested=None,
)


def _lean_word(favourable: bool) -> str:
    return "favourable-leaning" if favourable else "adverse-leaning"


#: The specific "other"-kind yogas leaned by record (each still carries its own citation, shown
#: in the Yogas section). Benefic on the worldly-fortune axis this tally uses: Budha-Aditya
#: ("highly intelligent, of good repute"), Vasumathi ("always commands plenty of wealth",
#: 3HC:2708), Jaya ("ever successful, victorious", 3HC:5670), Parvata ("wealthy, prosperous...
#: head of a town", 3HC:3170) — all unambiguously favourable printed effects — PLUS the five
#: Pancha Mahapurusha (Ruchaka/Bhadra/Hamsa/Malavya/Sasa), leaned on their raja-status ("great
#: men", Raman groups all five as Raja Yogas, 3HC) rather than an unambiguous printed effect:
#: Sasa in particular carries an explicit mixed-character clause ("character questionable...
#: covetous", 3HC:3741-3745) that the fortune-axis tally deliberately sets aside. Adverse:
#: Daridra ("heavy debts and very poor", 3HC:7289) and Asatyavadi ("loving falsehood...
#: fraudulent schemes", HPA-20:225 — a high-base-rate ~1/6 contributor, so its recurring
#: adverse row should not be over-weighted). The set is complete among CURRENTLY-RESOLVABLE
#: other-kind yogas: Chatussagara qualifies on effect but resolves no constituents (no bearing
#: row); the Nabhasa/Akriti shapes likewise resolve none. lunar stays neutral (Gajakesari-type
#: yogas are only conditionally benefic — nullified in dusthana formation, HTJAH-I:2948-2956).
_BENEFIC_RECORD_YOGAS: Final[frozenset[str]] = frozenset({
    "Y.RUCHAKA", "Y.BHADRA", "Y.HAMSA", "Y.MALAVYA", "Y.SASA",
    "Y.BUDHA_ADITYA", "Y.VASUMATHI", "Y.JAYA", "Y.PARVATA"})
_ADVERSE_RECORD_YOGAS: Final[frozenset[str]] = frozenset({"Y.DARIDRA", "Y.ASATYAVADI"})


def _yoga_record_lean(y: FiredYoga) -> str:
    """The preponderance-witness lean for a bearing yoga: a per-record override for the
    directionally-unambiguous 'other'-kind yogas, else the encoded-kind lean, else neutral."""
    if y.id in _BENEFIC_RECORD_YOGAS:
        return "favourable-leaning"
    if y.id in _ADVERSE_RECORD_YOGAS:
        return "adverse-leaning"
    return {"raja": "favourable-leaning", "dhana": "favourable-leaning",
            "arishta": "adverse-leaning"}.get(y.kind, "neutral")


def build_preponderance(r: DetailedReport) -> PreponderanceReading:
    """Assemble the per-house testimony ledgers from an already-fully-built DetailedReport —
    every testimony is a value the report renders elsewhere (lagna-frame lord strength, karaka
    strength, navamsa status, Bhava-Bala rank, SAV band, the matter-varga dashboard verdicts,
    the calibration majority tenor). Pure re-reads; the headline verdict is `pf.rollup`, read
    and displayed, never re-decided and never counted in its own tally."""
    hs_by_house = {row.house: row for row in r.house_strength}
    dash_by_matter = {e.matter: e for e in r.dashboard.entries}
    # yoga -> houses it bears on (Raman's Primary Considerations link, resolved via each
    # yoga's constituent planets' own/occupy/aspect — see yoga_house_bearings' docstring).
    from app.raman_saab.doctrine.synthesis_rules import yoga_house_bearings
    bearings = [(y, yoga_house_bearings(r.chart, y)) for y in r.yogas]

    houses: list[HouseTestimonies] = []
    for pf in r.proformas:
        h = pf.house
        verdict = str(pf.rollup)
        led = _lagna_ledger(pf.significations[0]) if pf.significations else None
        tst: list[Testimony] = []

        affliction_matter = led is not None and "AFFLICTION_MATTER" in led.flags

        # Lord strength is directional in Raman's own words — "if the strength of the lord is
        # full or complete there will be in general a good influence on the house"
        # (HTJAH-I:497) — EXCEPT on a dusthana affliction matter, where the engine's own
        # clause-1.5 doctrine is "a strong dusthana lord strengthens [the affliction], never
        # rescues": there a strong lord is an adverse witness. The weak-lord converse on an
        # affliction matter is NOT engine-encoded, so it reads neutral, not guessed.
        if led is None or led.lord_strong is None:
            tst.append(Testimony("lord (lagna frame)", "no data", "absent"))
        elif affliction_matter and led.lord_strong:
            tst.append(Testimony("lord (lagna frame)",
                                 "strong [feeds the affliction — a strong dusthana lord "
                                 "strengthens, never rescues]", "adverse-leaning"))
        elif affliction_matter:
            tst.append(Testimony("lord (lagna frame)",
                                 "weak (affliction matter — no directional read encoded)",
                                 "neutral"))
        else:
            tst.append(Testimony("lord (lagna frame)", "strong" if led.lord_strong else "weak",
                                 _lean_word(led.lord_strong)))

        # A broken karaka (karaka_intact False) is the clause-1 VETO the headline actually
        # obeyed — it must never tally as a favourable witness, whatever its raw strength.
        if led is None or led.karaka_strong is None:
            tst.append(Testimony("karaka", "no data", "absent"))
        elif not led.karaka_intact:
            tst.append(Testimony("karaka",
                                 ("strong" if led.karaka_strong else "weak")
                                 + " but broken [the affliction veto the headline obeyed]",
                                 "adverse-leaning"))
        else:
            tst.append(Testimony("karaka", "strong" if led.karaka_strong else "weak",
                                 _lean_word(led.karaka_strong)))

        # Navamsa is direction-ABSOLUTE, the same monotone sense the verdict path gives it
        # (house_template._navamsa_modulate and the clause-2 navamsa guard): "confirms" is a
        # D9-dignity lift and always a favourable witness; "weakens" a D9 debility/dusthana
        # seat and always adverse — on an afflicted headline a weakens CORROBORATES it (it may
        # even have caused it) and a confirms CONTESTS it. (A first draft read this
        # verdict-relative; a bphs-doctrine-reviewer pass showed that inverts the engine's own
        # semantics.)
        nav = led.navamsa_status if led is not None else "unknown"
        if nav == "confirms":
            tst.append(Testimony("navamsa", nav, "favourable-leaning"))
        elif nav == "weakens":
            tst.append(Testimony("navamsa", nav, "adverse-leaning"))
        else:
            tst.append(Testimony("navamsa", nav,
                                 "neutral" if nav == "neutral" else "absent"))

        # Bhava-Bala rank is a MAGNITUDE — how fully the house's indications are enjoyed
        # (GBB-9:32-34), ranked without any cutoff (GBB-9:332) — so it is shown but carries NO
        # direction. (A first draft leaned it by top/bottom half; a bphs-doctrine-reviewer
        # pass flagged that as an invented threshold contradicting the report's own
        # magnitude-vs-direction explainer.)
        hs = hs_by_house.get(h)
        if hs is None or hs.bhava_bala_rank is None:
            tst.append(Testimony("bhava bala rank", "no data", "absent"))
        else:
            tst.append(Testimony("bhava bala rank",
                                 f"{hs.bhava_bala_rank} of 12 (magnitude, not direction)",
                                 "neutral"))

        if hs is None or hs.sav_bindus is None:
            tst.append(Testimony("SAV band", "no data", "absent"))
        else:
            band_lean = {"strong": "favourable-leaning", "weak": "adverse-leaning"}.get(
                hs.sav_band, "neutral")
            tst.append(Testimony("SAV band", f"{hs.sav_bindus} bindus ({hs.sav_band})",
                                 band_lean))

        matters_here = [m for m, mh in _MATTER_HOUSE.items() if mh == h]
        if not matters_here:
            tst.append(Testimony("matter-varga", "no dedicated matter-varga reader for this "
                                                 "house", "absent"))
        else:
            for m in sorted(matters_here, key=lambda x: list(_MATTER_HOUSE).index(x)):
                en = dash_by_matter.get(m)
                if en is None:
                    tst.append(Testimony(f"matter-varga: {m}", "no data", "absent"))
                elif en.verdict in ("favourable", "afflicted"):
                    tst.append(Testimony(f"matter-varga: {m}", en.verdict,
                                         _lean_word(en.verdict == "favourable")))
                elif en.verdict == "mixed":
                    tst.append(Testimony(f"matter-varga: {m}", en.verdict, "neutral"))
                else:
                    tst.append(Testimony(f"matter-varga: {m}", en.verdict, "absent"))

        split = signification_tenor_split(r.calibration[h]) if h in r.calibration else None
        if split is None or split.majority == "insufficient-evidence":
            tst.append(Testimony("majority tenor", "insufficient evidence", "absent"))
        elif split.majority == "mixed":
            tst.append(Testimony("majority tenor", "mixed", "neutral"))
        else:
            tst.append(Testimony("majority tenor", split.majority,
                                 _lean_word(split.majority == "favourable")))

        # Yogas bearing on this house (Raman's Primary Considerations, HTJAH-I:4135-4139),
        # via the constituents' own/occupy/aspect link his worked charts use. One row per
        # bearing yoga. Lean by the encoded kind (raja/dhana favourable, arishta adverse) and
        # by a per-record override for the specific "other"-kind yogas whose PRINTED EFFECT is
        # unambiguously directional (`_yoga_record_lean`); the remaining other/lunar yogas stay
        # neutral (Nabhasa shapes resolve no constituents so never reach here; Gajakesari-type
        # lunar yogas are only conditionally benefic).
        here = [y for y, bh in bearings if bh is not None and h in bh]
        if not here:
            tst.append(Testimony("yogas bearing", "none of the fired yogas resolves onto "
                                                  "this house", "absent"))
        else:
            for y in here:
                tst.append(Testimony(f"yoga: {y.name}", y.kind, _yoga_record_lean(y)))

        fav = sum(1 for t in tst if t.lean == "favourable-leaning")
        adv = sum(1 for t in tst if t.lean == "adverse-leaning")
        neu = sum(1 for t in tst if t.lean == "neutral")
        ab = sum(1 for t in tst if t.lean == "absent")
        if fav > adv:
            prep = "benefic"
        elif adv > fav:
            prep = "adverse"
        elif fav:                        # fav == adv > 0
            prep = "evenly balanced"
        else:
            prep = "insufficient"

        if verdict == "favourable":
            status = ("well-corroborated" if prep == "benefic"
                      else "contested" if prep in ("adverse", "evenly balanced")
                      else "thinly attested")
        elif verdict == "afflicted":
            status = ("well-corroborated" if prep == "adverse"
                      else "contested" if prep in ("benefic", "evenly balanced")
                      else "thinly attested")
        elif verdict == "mixed":
            status = "(mixed headline)"
        else:
            status = "(undecided headline)"

        houses.append(HouseTestimonies(
            house=h, verdict=verdict, testimonies=tuple(tst), favourable=fav, adverse=adv,
            neutral=neu, absent=ab, preponderance=prep, status=status))

    def _pick(cands: list[HouseTestimonies], key) -> Optional[int]:
        if not cands:
            return None
        return min(cands, key=lambda ht_: (-key(ht_), ht_.house)).house

    fav_c = [x for x in houses if x.verdict == "favourable" and x.preponderance == "benefic"]
    aff_c = [x for x in houses if x.verdict == "afflicted" and x.preponderance == "adverse"]
    con_c = [x for x in houses if x.status == "contested"]
    return PreponderanceReading(
        houses=tuple(houses),
        most_corroborated_favourable=_pick(fav_c, lambda x: x.favourable),
        most_corroborated_afflicted=_pick(aff_c, lambda x: x.adverse),
        most_contested=_pick(con_c, lambda x: (x.adverse if x.verdict == "favourable"
                                               else x.favourable)),
    )


#: Tier order for the best-tier-per-house aggregation in Life-chapters — Raman's own four
#: grades in descending strength (HTJAH-I:1592-1596, 1635-1640; the same vocabulary
#: `graded_buckets` buckets by). Ordering only — no new grading is invented here.
_TIER_ORDER: Final[tuple[str, ...]] = ("par excellence", "ordinary", "limited", "feeble")


@dataclass(frozen=True)
class LifeChapter:
    """One Mahadasha run, narrated as a single woven chapter — the shape of Raman's own
    worked-nativity narration (Chart No. 203, HTJAH-I:15950-15999, where each dasha period is
    read from yoga + lord condition + house placement + directional influence in one
    paragraph), and his blending doctrine ("Astrological predictions can be accurate when the
    influences of birth chart are blended with those of Gochara and Ashtakavarga, together
    with Vedha or obstructing forces", HPA-34:369-381 — Vedha itself is applied in the Gochara
    table and sampled in the Dasha x Transit table, not re-narrated per chapter). Every field
    is a pure JOIN of rows the report already renders in the
    Life-narrative companions above it; the narrative orders natal factors first and transits
    last per HTJAH-I:8410-8411 ("Primary importance must be given to the natal positions and
    Dasha and only secondary consideration to transiting planets")."""
    maha: str
    start_jd: float
    end_jd: float
    is_current: bool
    condition: Optional[MdLordCondition]              # joined from r.md_condition
    lean: Optional[str]                               # maha_lean from r.ishta_kashta
    av_seat: Optional[AvDashaSeat]                    # joined from r.av_dasha_seats
    yogas_ripening: tuple[YogaTiming, ...]            # r.yoga_timing rows inside the run
    houses_lit: tuple[tuple[int, str, str], ...]      # (house, best_tier, natal_verdict)
    confluences: tuple[ConfluenceWindow, ...]         # r.dasha_transit overlapping the run
    maraka_overlaps: tuple[MarakaSaturnConfluence, ...]
    narrative: str


@dataclass(frozen=True)
class LifeChapters:
    """The per-Mahadasha chapter view (v15) — one prose chapter per MD run, merging what the
    Life-narrative and its three companion tables show separately. Presentation-only."""
    chapters: tuple[LifeChapter, ...]


_EMPTY_LIFE_CHAPTERS: Final[LifeChapters] = LifeChapters(chapters=())
_EMPTY_DIGEST: Final[InsightDigest] = InsightDigest(headline="", items=())


def _chapter_narrative(r: DetailedReport, maha: str, lo: float, hi: float,
                       cond: Optional[MdLordCondition], lean: Optional[str],
                       seat: Optional[AvDashaSeat], yts: tuple[YogaTiming, ...],
                       houses_lit: tuple[tuple[int, str, str], ...],
                       conf: tuple[ConfluenceWindow, ...],
                       mar: tuple[MarakaSaturnConfluence, ...]) -> str:
    """Knit one chapter paragraph — natal factors FIRST, transits LAST (HTJAH-I:8410-8411)."""
    bits: list[str] = []
    fn = dict(r.overview.functional_natures).get(maha)
    # "in view", not "rules": _md_runs bounds are clipped to the report's display window, so a
    # Mahadasha may begin before or continue past the dates shown — asserting "rules X to Y"
    # on a clipped run would state a false rulership span (bphs-doctrine-reviewer finding).
    lead = f"{maha}'s Mahadasha is in view {_jd_month_year(lo)} to {_jd_month_year(hi)}"
    if fn is not None:
        lead += f"; {maha} is a {fn} for this Lagna"
    cond_words: list[str] = []
    if cond is not None:
        if cond.strong is not None:
            cond_words.append("strong in Shadbala" if cond.strong else "weak in Shadbala")
        if cond.vargottama:
            cond_words.append("vargottama")
        if cond.at_maximum:
            cond_words.append("at the strength maximum — strong in both rasi and navamsa "
                              "(HPA-24:51-86; Raman's full maximum further requires freedom "
                              "from malefic aspect, not graded here)")
    else:
        cond_words.append("lord condition unavailable on this chart")
    if lean is not None:
        cond_words.append(f"a {lean} Ishta/Kashta lean")
    bits.append(f"{lead}: {', '.join(cond_words)}.")
    if yts:
        names = ", ".join(f"{t.yoga_name} ({t.role})" for t in yts)
        bits.append(f"Yogas ripening here: {names} — a yoga's lord delivers its results in "
                    f"his own Dasha or Bhukti (HTJAH-I:4324).")
    if houses_lit:
        hl = ", ".join(f"H{h} ({tier}; natal {v})" for h, tier, v in houses_lit)
        bits.append(f"Houses whose indications fructify across its bhuktis — peak tier "
                    f"reached in at least one bhukti, see the Life-narrative rows above for "
                    f"which sub-period: {hl} — each delivering per its unchanged natal "
                    f"verdict.")
    if seat is not None and seat.bindus is not None:
        bits.append(f"His own Ashtakavarga seat reads {seat.read} ({seat.bindus} bindus) — "
                    f"under Raman's own reliability caveat for the AV tier.")
    # transits LAST — secondary to the natal positions and Dasha (HTJAH-I:8410-8411)
    if conf:
        bits.append(f"Secondarily, {len(conf)} transit-reinforcement window(s) fall in these "
                    f"years (the period lord favourably placed by its own transit — see Dasha "
                    f"x Transit confluence).")
    if mar:
        bits.append("A maraka-window x Saturn-transit overlap also falls in this stretch — a "
                    "statement of the classical method only, not a prediction (see the Maraka "
                    "x Saturn-transit section and its null real-outcome disclosure).")
    return " ".join(bits)


def build_life_chapters(r: DetailedReport, *, dominant: Optional[str] = None) -> LifeChapters:
    """Assemble one chapter per Mahadasha run — pure joins of the already-computed
    `md_condition` / `ishta_kashta` / `av_dasha_seats` / `yoga_timing` / `dasha_transit` /
    `maraka_saturn` rows onto `_md_runs`, with houses lit aggregated through the ONE existing
    grading helper `graded_buckets` (best tier per house across the run's bhuktis; tier order
    fixed by `_TIER_ORDER` — ordering only, nothing re-graded).

    `dominant` (pipeline wiring, 2026-08-03): the census-dominant graha from the S2 theme
    extraction — when a chapter's MD lord IS that planet, one added sentence marks it. A
    pure re-read of the census; None (Track-B / sparse) changes nothing."""
    chapters: list[LifeChapter] = []
    for maha, lo, hi in _md_runs(r.timeline):
        cond = next((c for c in r.md_condition if c.maha == maha and c.start_jd == lo), None)
        if cond is None:   # interval fallback (md_condition skips lords absent from the chart)
            cond = next((c for c in r.md_condition
                         if c.maha == maha and c.start_jd < hi and c.end_jd > lo), None)
        lean = next((ik.maha_lean for ik in r.ishta_kashta
                     if ik.maha == maha and lo <= ik.start_jd < hi), None)
        seat = next((a for a in r.av_dasha_seats if a.maha == maha and a.start_jd == lo), None)
        if seat is None:
            seat = next((a for a in r.av_dasha_seats
                         if a.maha == maha and a.start_jd < hi and a.end_jd > lo), None)

        seen: set[tuple[str, str]] = set()
        yts: list[YogaTiming] = []
        for t in r.yoga_timing:
            if (lo <= t.period_start_jd and t.period_end_jd <= hi
                    and (t.yoga_id, t.role) not in seen):
                seen.add((t.yoga_id, t.role))
                yts.append(t)

        best: dict[int, tuple[int, str]] = {}
        for tp in r.timeline.periods:
            if tp.period.maha != maha or not (lo <= tp.period.start_jd < hi):
                continue
            _assoc, buckets = graded_buckets(tp, r.chart)
            for idx, tier in enumerate(_TIER_ORDER):
                for a in buckets[tier]:
                    cur = best.get(a.house)
                    if cur is None or idx < cur[0]:
                        best[a.house] = (idx, str(a.natal_verdict))
        houses_lit = tuple(sorted(
            ((h, _TIER_ORDER[i], v) for h, (i, v) in best.items()),
            key=lambda x: (_TIER_ORDER.index(x[1]), x[0])))

        conf = tuple(c for c in r.dasha_transit
                     if c.overlap_start_jd < hi and c.overlap_end_jd > lo)
        mar = tuple(m for m in r.maraka_saturn
                    if m.overlap_start_jd < hi and m.overlap_end_jd > lo)
        narrative = _chapter_narrative(r, maha, lo, hi, cond, lean, seat, tuple(yts),
                                       houses_lit, conf, mar)
        if dominant is not None and maha == dominant:
            narrative += (f" This is {maha}'s own period — the planet that drives more "
                          f"of this chart's computed readings than any other (the "
                          f"judgment-graph census; see Planet biographies).")
        chapters.append(LifeChapter(
            maha=maha, start_jd=lo, end_jd=hi, is_current=lo <= r.ref_jd < hi,
            condition=cond, lean=lean, av_seat=seat, yogas_ripening=tuple(yts),
            houses_lit=houses_lit, confluences=conf, maraka_overlaps=mar,
            narrative=narrative))
    return LifeChapters(chapters=tuple(chapters))


def build_nichod(r: DetailedReport) -> Nichod:
    """Assemble the Nichod from an already-fully-built DetailedReport (every input below is
    something the report renders elsewhere; this only selects, counts, and knits)."""
    from collections import Counter

    s, chart = r.synthesis, r.chart

    moon = chart.planets.get("Moon")
    nak = nakshatra_signature.signature_for(moon.nakshatra) if moon is not None else None
    nak_bit = f", Moon in {nak.name} (pada {moon.pada})" if nak is not None else ""
    identity = (f"{s.lagna} Lagna, ruler of the nativity {r.ruler.lagna_lord}, "
               f"{r.overview.stronger_frame.upper()} the stronger frame, "
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
    if r.preponderance.most_contested is not None:
        mc = r.preponderance.most_contested
        caution_bits.append(
            f"H{mc} is the most-contested house — its own witnesses lean against its headline "
            f"(see Preponderance of testimonies); read that house's section with extra care")
    caution = "; ".join(caution_bits) if caution_bits else None

    # the first-impression line, from the Ruler of the nativity card (HTJAH-I:16001-16002)
    ruler_bit = f"The ruler of the nativity is {r.ruler.lagna_lord}"
    if r.ruler.strongest is not None:
        if r.ruler.coincide:
            ruler_bit += (f", which is also the strongest planet — \"the foundation is quite "
                          f"sound\"")
        else:
            ruler_bit += f"; the strongest planet by Shadbala is {r.ruler.strongest}"
    ruler_bit += ". "

    essence = (
        f"{identity}. {ruler_bit}{longevity}. "
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

    # S5 — turning points: MD boundaries where the Ishta/Kashta MD lean flips (pure
    # re-read of the ishta_kashta rows; the lean is natal-fixed per lord, GBB-10:134).
    md_rows = [ik for ik in r.ishta_kashta if ik.antar is None] or [
        ik for ik in r.ishta_kashta]
    turning: list[tuple[str, str]] = []
    prev_maha: Optional[str] = None
    prev_lean: Optional[str] = None
    for ik in md_rows:
        if ik.maha != prev_maha:
            if (prev_maha is not None and ik.maha_lean and prev_lean
                    and ik.maha_lean != prev_lean):
                turning.append((
                    f"{_jd_month_year(ik.start_jd)}",
                    f"{prev_maha} MD ({prev_lean}) gives way to {ik.maha} MD "
                    f"({ik.maha_lean}) — the period lean changes"))
            prev_maha, prev_lean = ik.maha, ik.maha_lean
    return Nichod(
        identity=identity, strength_profile=strength_profile, longevity=longevity, yogas=yogas,
        stands_out=stands_out, matters_tally=matters_tally, current_period=current_period,
        live_transits=live_transits, spotlight=spotlight, caution=caution, essence=essence,
        turning_points=tuple(turning),
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


def build_plain_reading(r: DetailedReport, *, reconciliations: tuple[str, ...] = (),
                        dominant=None) -> PlainReading:
    """Assemble 'Your Reading' — the report's one genuinely plain-English section, meant to be
    read FIRST. Translates the already-computed 12-matter dashboard, the running period, and
    the distinctive readings into hand-written prose; invents no new judgment.

    Pipeline wiring (2026-08-03): `reconciliations` are the S3 conflict narrator's woven
    sentences, composed here (not attached after); `dominant` is the S2 census-leading
    PlanetBiography — its sentence sits beside the Shadbala one because the two measure
    DIFFERENT dominances (strength vs breadth of participation), and says so."""
    name = r.birth.name.strip() or "this chart"
    opening = (f"Here is what {name}'s chart says, in plain terms — before any of the "
               f"technical detail below.")
    # the plain first impression: the planet that most shapes the overall temperament
    # (the Ruler of the nativity card, HTJAH-I:6248-6250)
    if r.ruler.strongest is not None:
        theme = _PLANET_THEME.get(r.ruler.strongest, "its own classical themes")
        opening += (f" The planet that most shapes the overall temperament here is "
                    f"{r.ruler.strongest} — classically bringing out {theme}.")
    if dominant is not None:
        opening += (f" Measured differently — by how many of this report's computed "
                    f"readings a planet participates in — {dominant.planet} touches the "
                    f"most ({dominant.census_count} connections in the judgment graph); "
                    f"its classical themes of {dominant.themes_raman} "
                    f"(HTJAH-II:10249) run through this chart.")

    by_matter = {en.matter: en.verdict for en in r.dashboard.entries}
    life_paragraphs: list[tuple[str, str]] = []
    for theme, matters in _PLAIN_GROUPS:
        sentences = []
        for m in matters:
            verdict = by_matter.get(m)
            line = _PLAIN_MATTER.get(m, {}).get(verdict) if verdict else None
            if line:
                line = _pick_plain_variant(r.birth, m + (verdict or ""), line)
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
    if r.preponderance.most_contested is not None:
        area = _PLAIN_AREA.get(r.preponderance.most_contested, "one area")
        notable += (f" One area reads less settled than the rest — {area} — where the "
                   f"underlying signals pull in different directions; the report weighs "
                   f"them out below rather than forcing a single verdict.")

    closing = ("This is a plain-language reading of what the classical method sees in the "
              "pattern of the birth chart — not a prediction of specific events. The full "
              "technical report below shows exactly how each conclusion was reached.")

    return PlainReading(opening=opening, life_paragraphs=tuple(life_paragraphs), now=now,
                        notable=notable, closing=closing, reconciliations=reconciliations)


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
    yoga_timing = _yoga_dasha_confluences(chart, timeline, fired_yogas)
    bhava_balas = {pf.house: pf.significations[0].ledger.bhava_bala
                   for pf in reading.proformas
                   if pf.significations and pf.significations[0].ledger.bhava_bala is not None}
    insights = detect_synthesis(
        chart, ref_jd, gochara=tuple(gochara_rows), yogas=fired_yogas, sav=sav,
        bhava_balas=bhava_balas, maraka_now=maraka_now)
    house_strength = _house_strength_rows(reading.proformas, chart.asc_sign, sav, bhava_balas)
    ishta_kashta = _ishta_kashta_periods(chart, timeline)
    md_condition = _md_lord_conditions(chart, timeline)
    dasa_kakshya = _dasa_kakshya_rows(chart, timeline)
    try:
        maraka_saturn = _maraka_saturn_confluences(chart, ref_jd, ayanamsa)
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        maraka_saturn = ()
    av_dasha_seats = _av_dasha_seats(chart, timeline)
    provisional = DetailedReport(
        birth=birth, chart=chart, synthesis=syn, calibration=calib,
        proformas=reading.proformas, overview=chart_overview(chart),
        yogas=fired_yogas, yoga_timing=yoga_timing, house_strength=house_strength,
        ishta_kashta=ishta_kashta, md_condition=md_condition, dasa_kakshya=dasa_kakshya,
        maraka_saturn=maraka_saturn, av_dasha_seats=av_dasha_seats,
        sav=sav, insights=insights,
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
        nichod=_EMPTY_NICHOD, plain_reading=_EMPTY_PLAIN_READING, ruler=_EMPTY_RULER,
        preponderance=_EMPTY_PREPONDERANCE, life_chapters=_EMPTY_LIFE_CHAPTERS,
        digest=_EMPTY_DIGEST, health_readout=_EMPTY_HEALTH_READOUT,
    )
    # Ruler / preponderance / life-chapters are built FIRST (they read only the base fields
    # above), then the digest RANKS what those enriched fields hold, and finally the plain
    # layers (Nichod + Your Reading) are built from that ENRICHED report — they now weave in
    # the ruler of the nativity and the most-contested house, so they must see populated
    # synthesis fields, not the empty sentinels. Each stage only selects, counts and knits
    # fields already produced; no verdict is re-judged.
    # ── the synthesis pipeline, in the diagram's order (wired 2026-08-03) ─────
    # Judgment objects (provisional) -> ruler/preponderance summaries -> the EVIDENCE
    # GRAPH (from first-pass objects only) -> the CONFLICT NARRATOR -> THEME EXTRACTION
    # (census -> biographies) -> the LIFE NARRATIVE ENGINE (chapters + digest + nichod +
    # plain reading, each consuming the layers above) -> the final report. Prose that
    # names census values can only exist because the census ran first — the order is
    # enforced by consumption, not by comments alone.
    from app.raman_saab.judgment_graph import build_judgment_graph
    from app.raman_saab.planet_biographies import build_planet_biographies
    from app.raman_saab.tension_narrator import narrate_tensions
    enriched = _dc_replace(provisional,
                           ruler=build_ruler(provisional),
                           preponderance=build_preponderance(provisional),
                           health_readout=build_health_readout(provisional))
    try:
        _graph = build_judgment_graph(enriched)
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        _graph = None
    try:
        _recs = narrate_tensions(enriched)
    except Exception:  # noqa: BLE001
        _recs = ()
    _bios: tuple = ()
    _deep: tuple = ()
    if _graph is not None:
        try:
            _bios = build_planet_biographies(enriched, _graph)
        except Exception:  # noqa: BLE001
            _bios = ()
        try:
            from app.raman_saab.yoga_deep_read import build_yoga_deep_reads
            _deep = build_yoga_deep_reads(enriched, _graph)
        except Exception:  # noqa: BLE001
            _deep = ()
    enriched = _dc_replace(enriched, planet_bios=_bios, yoga_deep=_deep,
                           life_chapters=build_life_chapters(
                               enriched, dominant=_bios[0].planet if _bios else None,
                           ))
    # v22-v24 chapters (pure re-reads; life_chapters feeds the expansion periods).
    from app.raman_saab.arishta_wealth_profession import (build_arishta_chapter,
                                                          build_profession_synthesis,
                                                          build_wealth_chapter)
    from app.raman_saab.monographs import (build_children_chapter,
                                           build_marriage_monograph,
                                           build_psych_profile)
    # one try per builder — a failure in one chapter must never silence the others
    for _field, _builder in (("arishta", build_arishta_chapter),
                             ("profession", build_profession_synthesis),
                             ("wealth", build_wealth_chapter),
                             ("marriage", build_marriage_monograph),
                             ("children", build_children_chapter),
                             ("psych", build_psych_profile)):
        try:
            enriched = _dc_replace(enriched, **{_field: _builder(enriched)})
        except Exception:  # noqa: BLE001 — sparse/Track-B chart
            pass
    from app.raman_saab.life_arc import build_decade_timeline
    try:
        enriched = _dc_replace(enriched, decades=build_decade_timeline(enriched))
    except Exception:  # noqa: BLE001
        pass
    from app.raman_saab.karmic_evolution import build_karmic_evolution
    try:
        enriched = _dc_replace(enriched, karmic=build_karmic_evolution(enriched))
    except Exception:  # noqa: BLE001
        pass
    enriched = _dc_replace(enriched, digest=build_insight_digest(enriched))
    final = _dc_replace(enriched, nichod=build_nichod(enriched),
                        plain_reading=build_plain_reading(
                            enriched, reconciliations=_recs,
                            dominant=_bios[0] if _bios else None))
    # v29 — the life synthesis reads the FULLY-built report (incl. the nichod).
    from app.raman_saab.life_arc import build_life_synthesis
    try:
        final = _dc_replace(final, life_synthesis=build_life_synthesis(final))
    except Exception:  # noqa: BLE001
        pass
    return final


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
    if pr.reconciliations:
        L.append("**Where readings pull in different directions** (both poles shown; "
                 "the rule that reconciles them is in How to read this report):")
        for rec in pr.reconciliations:
            L.append(f"- {rec}")
        L.append("")
    L.append(f"_{pr.closing}_")

    # ── the honesty headline (aggregate information content) ──────────────────
    L.append("")
    L.append("## Information content of this reading")
    L.append("")
    L.append(r.info.sentence)
    L.append("")

    # ── how to read this report (v18, chart-independent interpretation guide) ─
    from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE as _IG
    L.append("## How to read this report")
    L.append("")
    L.append(f"_{_IG['preamble']}_")
    L.append("")
    L.append("**Start here — five sections answer most questions:**")
    L.append("")
    for step in _IG["reading_order"]:
        L.append(f"{step['step']}. **{step['title']}** — {step['answers']} {step['adds']}")
    L.append("")
    L.append("**When two sections seem to disagree, these rules govern** (each is a rule "
             "this report already states in the section that yields):")
    L.append("")
    L.append("| # | Sections | Relation | The rule |")
    L.append("|---|---|---|---|")
    for prec in _IG["precedence"]:
        L.append(f"| {prec['id']} | {', '.join(prec['sections'])} | {prec['relation']} | "
                 f"{prec['rule_text']} |")
    L.append("")
    L.append("**Parallel lenses — no ranking exists; read side by side, never averaged:**")
    L.append("")
    for par in _IG["parallel_lenses"]:
        L.append(f"- {par['id']} ({', '.join(par['sections'])}): {par['why']}")
    L.append("")
    L.append("**The independent axes** (disagreement between axes is not a contradiction):")
    L.append("")
    L.append("| axis | measures | shown in | citation |")
    L.append("|---|---|---|---|")
    for ax in _IG["axes"]:
        qual = f" — {ax['qualification']}" if ax.get("qualification") else ""
        L.append(f"| {ax['axis']} | {ax['means']}{qual} | {', '.join(ax['sections'])} | "
                 f"{ax['citation']} |")
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

    # ── what matters most (v19, the engine's own ranked digest) ───────────────
    if r.digest.items:
        L.append("## What matters most (ranked digest)")
        L.append("")
        L.append(f"_{r.digest.headline}_")
        L.append("")
        L.append("| # | Kind | Finding | Lean | Bridges | Cites |")
        L.append("|---|---|---|---|---|---|")
        for it in r.digest.items:
            bridges = ", ".join(it.sections) if it.sections else "-"
            cites = ", ".join(it.cites) if it.cites else "-"
            L.append(f"| {it.priority} | {it.kind} | **{it.title}** — {it.detail} | "
                     f"{it.lean} | {bridges} | {cites} |")
        L.append("")

    # ── the twelve matters at a glance (executive dashboard) ──────────────────
    L.append("## The twelve matters at a glance")
    L.append("")
    L.append("_Each matter's authoritative verdict from its dedicated deep reader (Raman's method "
             "decides; the divisional chart corroborates). Detail in the deep-read sections below._")
    L.append("")
    # item 15 (2026-08-04 content amendment): the support column — a re-read of the
    # preponderance ledgers (High = corroborated, Low = contested, else Medium), with
    # the testimony counts; NEVER a probability of an event.
    from app.raman_saab.tension_narrator import _MATTER_HOUSE
    _supp = {ht.house: ("High" if "corrobor" in ht.status else
                        "Low" if "contest" in ht.status else "Medium",
                        f"{ht.favourable}F/{ht.adverse}A")
             for ht in r.preponderance.houses}
    L.append("| matter | divisional | verdict | classical support (testimonies) |")
    L.append("|---|---|---|---|")
    for en in r.dashboard.entries:
        _h = _MATTER_HOUSE.get(en.matter)
        _sp = _supp.get(_h)
        sup = f"{_sp[0]} ({_sp[1]})" if _sp else "-"
        L.append(f"| {en.matter} | D-{en.varga} {en.varga_name} | **{en.verdict}** | "
                 f"{sup} |")
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

    # ── ruler of the nativity (Raman's own first-impression move, v13) ───────
    ru = r.ruler
    L.append("## Ruler of the nativity")
    L.append("")
    L.append("**In simple terms:** Raman opens a judgment from here: \"in order to obtain a "
             "first impression we must first of all consider the ruler of the nativity\" — the "
             "Lagna lord (HTJAH-I:16001-16002) — and separately, \"the strongest planet in the "
             "horoscope determines the predominance of the physical, mental and spiritual "
             "peculiarities of the person\" (HTJAH-I:6248-6250). This card gathers what the "
             "report already computes about those one or two planets into a single first "
             "impression. The classical temperament lines are shorthand for tendencies, never "
             "medical statements — and as everywhere in this report: how the method reads this "
             "chart, not a prediction.")
    L.append("")
    ll_bit = f"{ru.lagna_lord}, lord of the {_SIGN_NAME[r.chart.asc_sign]} Lagna"
    if ru.lagna_lord_house is not None:
        ll_bit += f", in house {ru.lagna_lord_house}"
    L.append(f"- **Ruler of the nativity (Lagna lord)** — {ll_bit}")
    if ru.strongest is not None and ru.strongest_rupas is not None:
        s_bit = f"{ru.strongest} ({ru.strongest_rupas:.1f} rupas)"
        if ru.coincide:
            s_bit += (" — the ruler itself: \"the foundation is quite sound\" "
                      "(HTJAH-I:3880-3882)")
        L.append(f"- **Strongest planet (Shadbala)** — {s_bit}")
        if ru.navamsa_lagna_lord is not None:
            if ru.navamsa_lagna_lord == ru.strongest:
                L.append(f"- **Nature & appearance** — the lord of the Navamsa Lagna is the "
                         f"strongest planet itself ({ru.strongest}); it stamps the nature and "
                         f"appearance either way (HTJAH-I:3892-3897)")
            elif ru.stamps_nature is not None:
                L.append(f"- **Nature & appearance** — as between the strongest planet and the "
                         f"lord of the Navamsa Lagna ({ru.navamsa_lagna_lord}), "
                         f"**{ru.stamps_nature}** is the more powerful and stamps the nature "
                         f"and appearance (HTJAH-I:3892-3897)")
            else:
                L.append(f"- **Nature & appearance** — the strongest planet and the lord of "
                         f"the Navamsa Lagna ({ru.navamsa_lagna_lord}) cannot be ranked here "
                         f"(equal or unmeasured strength) — no winner is guessed "
                         f"(HTJAH-I:3892-3897)")
        if ru.temperament is not None:
            L.append(f"- **Classical temperament** — {ru.temperament} (HTJAH-I:6248-6268)")
        else:
            L.append("- **Classical temperament** — Raman's strongest-planet passage "
                     "(HTJAH-I:6248-6268) gives no line for the Moon — an honest absence, "
                     "nothing invented")
        cond = []
        if ru.functional_nature is not None:
            cond.append(f"{ru.functional_nature} for this Lagna")
        if ru.avastha is not None:
            cond.append(f"{ru.avastha} avastha (HPA Ch.7)")
        if ru.ik_lean is not None:
            cond.append(f"{ru.ik_lean} Ishta/Kashta lean (GBB-10:134)")
        if ru.vargottama:
            cond.append("vargottama")
        if ru.retrograde:
            cond.append("retrograde")
        if cond:
            L.append(f"- **Condition of the strongest** — {'; '.join(cond)}")
        if ru.yogas_involving:
            L.append(f"- **Yogas it participates in** — {', '.join(ru.yogas_involving)}")
        else:
            L.append("- **Yogas it participates in** — none of the fired yogas resolves to it")
        if ru.md_windows:
            spans = ", ".join(f"{_jd_month_year(s0)} to {_jd_month_year(e0)}"
                              for s0, e0 in ru.md_windows)
            L.append(f"- **Its own Mahadasha in the window** — {spans}")
        else:
            L.append("- **Its own Mahadasha in the window** — does not fall inside the "
                     "displayed window")
        if ru.slow_mover:
            L.append(f"- **Its transit outlook** — {len(ru.gochara_good_windows)} favourable "
                     f"window(s) in the Gochara outlook below")
        else:
            L.append(f"- **Its transit outlook** — {ru.strongest} is not one of the four slow "
                     f"movers the Gochara outlook tracks (coverage gap, disclosed — not a "
                     f"reading)")
    else:
        L.append("- **Strongest planet (Shadbala)** — no Shadbala on this chart; the strongest "
                 "planet cannot be determined by strength, and nothing is guessed in its place")
    L.append("")
    L.append(f"_{ru.signature}_")
    L.append("")

    # ── planet biographies (v20, S2 — dominant grahas by judgment-graph census) ─
    if r.planet_bios:
        from app.raman_saab.planet_biographies import MODERN_BANNER
        L.append("## Planet biographies (dominant grahas)")
        L.append("")
        L.append("**In simple terms:** the grahas that drive the most of this chart's "
                 "computed readings (counted over the judgment graph — lordships, "
                 "occupancy, aspects, karaka duties, dasha rulerships), each told as one "
                 "story. Every line re-reads a value shown elsewhere; nothing here is a "
                 "new judgment.")
        L.append("")
        for b in r.planet_bios:
            L.append(f"### {b.planet} — {b.census_count} graph appearances "
                     f"({', '.join(f'{k} {v}' for k, v in b.census_by_relation)})")
            L.append("")
            L.append(b.prose)
            L.append("")
            # the graha-chapter subsections — Raman's OWN paragraphs, verbatim by range
            if b.sign_text:
                L.append(f"- **In its sign (HPA-22)** — \"{b.sign_text[0]}\" "
                         f"({b.sign_text[1]})")
            elif b.planet in ("Rahu", "Ketu"):
                L.append("- **In its sign** — the nodes are aprakasha grahas; HPA-22 "
                         "states no per-sign results (HPA-22:522) — an honest absence")
            if b.house_text:
                L.append(f"- **In its house (HPA-21)** — \"{b.house_text[0]}\" "
                         f"({b.house_text[1]})")
            if b.family_role:
                L.append(f"- **Family/karaka duties** — {b.family_role}")
            if b.disease_text:
                L.append(f"- **Disease indications** — {b.disease_text[0]} "
                         f"({b.disease_text[1]})")
            if b.md_result_now:
                L.append(f"- **Its Mahadasha runs NOW (HPA-24)** — "
                         f"\"{b.md_result_now[0]}\" ({b.md_result_now[1]})")
            if b.ad_result_now:
                L.append(f"- **Its Bhukti runs NOW (HPA-24)** — "
                         f"\"{b.ad_result_now[0]}\" ({b.ad_result_now[1]})")
            if b.transit_text:
                L.append(f"- **Transit results (HPA-34, house-by-house from the Moon)** "
                         f"— \"{b.transit_text[0]}\" ({b.transit_text[1]})")
            if b.md_windows:
                spans = ", ".join(f"{_jd_month_year(s0)} to {_jd_month_year(e0)}"
                                  for s0, e0 in b.md_windows)
                L.append(f"- **Its own Mahadasha** — {spans}")
            if b.themes_raman:
                L.append(f"- **Raman's vocation words** (HTJAH-II:10249-10274) — "
                         f"{b.themes_raman}")
            if b.themes_modern:
                L.append(f"- **Modern keywords** [{MODERN_BANNER}] — "
                         f"{', '.join(b.themes_modern)}")
            L.append("")

    # ── psychological profile (v27 — the mind stack woven) ────────────────────
    if r.psych is not None:
        ps = r.psych
        L.append("## Psychological profile")
        L.append("")
        L.append(f"_{ps.woven}_")
        L.append("")
        L.append(f"- **The rising sign's portrait (Raman verbatim)** — "
                 f"\"{ps.lagna_quote[0]}\" ({ps.lagna_quote[1]})")
        if ps.moon_state:
            L.append(f"- **The mind's significator** — {ps.moon_state}")
        if ps.temperament:
            L.append(f"- **Temperament of the strongest planet** — {ps.temperament} "
                     f"(HTJAH-I:6248-6268)")
        if ps.nature_stamp:
            L.append(f"- **Nature & appearance stamped by** — {ps.nature_stamp} "
                     f"(HTJAH-I:3892-3897)")
        if ps.atmakaraka:
            L.append(f"- **Atmakaraka** — {ps.atmakaraka} (the 7-karaka scheme)")
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

    # ── yoga x dasha timing: when does a fired yoga's own lord actually run? ──
    if r.yoga_timing:
        L.append("## Yoga x Dasha timing")
        L.append("")
        L.append("**In simple terms:** a yoga is not always \"on\" — Raman says it ripens most "
                 "clearly during the periods of its own ruling planet(s) (HTJAH-I:4324). "
                 "\"Delivery\" is how well-placed that planet is in your natal chart (well / "
                 "mixed / poorly / unknown) — the same strength read the rest of this report "
                 "already uses; magnitude scales with it, and doubles at Vargottama "
                 "(HTJAH-I:5372).")
        L.append("")
        L.append("_Most named yogas above can be pinned to specific ruling planets by this "
                 "engine — a fixed planet (e.g. Ruchaka is always Mars), a house-lordship "
                 "(e.g. the 9th/10th lords), or a small checkable set (e.g. which planet "
                 "actually sits in the required position for Sunapha/Vesi/Amala). The whole-"
                 "chart-pattern yogas — where all seven visible planets together form a shape "
                 "or count, not any specific one or two of them (Rajju/Musala/Nala, the Sankhya "
                 "count yogas, the Akriti shape yogas) — have no single \"lord\" in Raman's own "
                 "definition and simply have no row here. That is a genuine coverage gap, not a "
                 "judgment that they lack timing._")
        L.append("")
        L.append("| Yoga | Period | Planet | Window | Delivery |")
        L.append("|---|---|---|---|---|")
        for t in r.yoga_timing:
            L.append(f"| {t.yoga_name} | {t.role} | {t.planet} | "
                     f"{_outlook_window_label(t.period_start_jd, t.period_end_jd)} | "
                     f"{t.quality.tag} |")
        L.append("")

    # ── yoga deep-read (v21 — every fired yoga as a full study) ───────────────
    if r.yoga_deep:
        L.append("## Yoga deep-read")
        L.append("")
        L.append("**In simple terms:** every yoga this chart fires, studied in full — "
                 "Raman's definition quoted verbatim at its citation, the exact rule the "
                 "engine computed, who participates and in what state, measured strength "
                 "(rupas — Raman assigns no percentage and none is invented), any stated "
                 "cancellation, the periods in which it ripens, and where the same yoga "
                 "appears in Notable Horoscopes.")
        L.append("")
        for y in r.yoga_deep:
            L.append(f"### {y.comparison_rank}. {y.name} ({y.kind}) — {y.cite}")
            L.append("")
            L.append(f"- **Definition (verbatim)** — \"{y.definition_quote}\" ({y.cite})")
            L.append(f"- **Computation** — `{y.computation}`")
            if y.participants:
                pf = "; ".join(
                    f"{f.planet}: house {f.house}, {_SIGN_NAME[f.sign]}, {f.dignity}"
                    + (f" (effective: {f.effective_dignity})"
                       if f.effective_dignity != f.dignity else "")
                    + (f", {f.rupas} rupas" if f.rupas is not None else "")
                    for f in y.participants)
                L.append(f"- **Why it qualifies** — {pf}")
            L.append(f"- **Strength (measured)** — {y.strength_note}")
            L.append(f"- **Cancellation** — {y.cancellation_note}")
            if y.modifiers:
                L.append(f"- **Modifying planets** (aspecting the participants' houses) "
                         f"— {', '.join(y.modifiers)}")
            if y.periods:
                L.append(f"- **Operating periods** — {'; '.join(y.periods)}")
            if y.nh_examples:
                L.append(f"- **In Notable Horoscopes** — {', '.join(y.nh_examples)}")
            L.append(f"- **Effect (Raman)** — {y.effect}")
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
             f"an atlas-proven inverted channel, a **WARNING** is shown inline. Each house "
             f"closes with a **Conclusion** line — Raman's own closing device (essentially "
             f"every worked analysis in HTJAH ends with a \"Conclusion.—\" summation weighing "
             f"house, lord and karaka in free prose, e.g. HTJAH-I:4485, 8513, 8870) — a "
             f"summation of rows already shown above and in the strength/preponderance "
             f"sections below; nothing new is judged in it._")
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
            lagna_led = _lagna_ledger(pf.significations[0])
            lord_p = r.chart.planets.get(pf.lord)
            lord_bits = f"**Lord** {pf.lord}"
            if lord_p is not None:
                lord_bits += f" in H{lord_p.rasi_house}"
            if lagna_led.lord_strong is not None:
                lord_bits += f" ({'strong' if lagna_led.lord_strong else 'weak'})"
            kar_bits = f"**Karaka** {led.karaka}"
            if led.karaka_strong is not None:
                kar_bits += f" ({'strong' if led.karaka_strong else 'weak'})"
            if not led.karaka_intact:
                kar_bits += " [afflicted]"
            bb = f"  |  **Bhava Bala** {led.bhava_bala:.1f}" if led.bhava_bala is not None else ""
            L.append(f"{lord_bits}  |  {kar_bits}{bb}  |  **Navamsa** {lagna_led.navamsa_status}")
            L.append("")
        L.append(mr.reading)
        conclusion = house_conclusion(r, mr.house)
        if conclusion:
            L.append("")
            L.append(f"> **Conclusion** — {conclusion}")
        cal = _calibration_lines(cal_reading)
        if cal:
            L.append("")
            L.append("_Population context:_")
            L.extend(cal)

    # ── house strength cross-check: is each verdict on strong or shaky ground? ──
    if r.house_strength:
        L.append("")
        L.append("## House strength cross-check")
        L.append("")
        L.append("**In simple terms:** every house above got a verdict — favourable, afflicted "
                 "or mixed — but not every house stands on equally strong ground. This table "
                 "cross-checks each verdict against two independent strength measures Raman "
                 "also uses: Bhava Bala (the house's own strength — its lord's Shadbala plus "
                 "positional strength — RANKED 1st-strongest to 12th-weakest across your chart; "
                 "Raman gives no numeric cutoff, only a ranking, GBB-9:332) and its "
                 "Sarvashtakavarga bindus (that sign's share of the 337 total, average 28). "
                 "Neither measure changes the verdict shown above — they say whether it is "
                 "well-supported or sits on thinner ground.")
        L.append("")
        L.append("_What a strong-yet-afflicted or weak-yet-favourable house means: Raman lists "
                 "a house's own strength and its aspects/qualities as SEPARATE considerations "
                 "when judging a house — \"the strength of the house itself\" and \"the natural "
                 "qualities of the house... or the planets... having aspects\" are numbered "
                 "separately (HTJAH-I:468-478). Bhava Bala is mostly a magnitude — HOW FULLY a "
                 "house's indications are enjoyed (\"otherwise he will not sufficiently enjoy "
                 "them,\" GBB-9:32-34) — though not perfectly independent of direction: one of "
                 "its three components, Bhava Drig Bala, is itself signed positive or negative "
                 "by benefic or malefic aspect (GBB-9:180-219). In practice the lord's Shadbala "
                 "(always a magnitude, never signed) dominates the total, so a strong-but-"
                 "afflicted house tends to deliver its difficulty with unusual force and "
                 "certainty, and a weak-but-favourable house tends to deliver real good "
                 "results only mildly or partly enjoyed — a tendency, not an absolute rule._")
        L.append("")
        L.append("| House | Matter | Verdict | Bhava Bala rank | SAV bindus |")
        L.append("|---|---|---|---|---|")
        for row in r.house_strength:
            bb_rank = f"{row.bhava_bala_rank} of 12" if row.bhava_bala_rank else "n/a"
            sav_cell = f"{row.sav_bindus} ({row.sav_band})" if row.sav_bindus is not None else "n/a"
            L.append(f"| H{row.house} | {_HOUSE_NAME.get(row.house, '')} | {row.verdict} | "
                     f"{bb_rank} | {sav_cell} |")
        L.append("")

    # ── preponderance of testimonies (v14, the full per-house ledger) ─────────
    if r.preponderance.houses:
        L.append("")
        L.append("## Preponderance of testimonies")
        L.append("")
        L.append("**In simple terms:** Raman defines judgment itself as \"the summing up of "
                 "the influence of planets\" — the house, its lord, its occupants and its "
                 "karaka weighed together (HTJAH-I:983-991), with everything \"properly "
                 "weighed before any result can be deduced\" (HTJAH-I:495; HTJAH-II:654-661 "
                 "repeats the injunction for marriage, and \"never... on the basis of one or "
                 "two combinations\" is his own wording, said of mental diagnosis, "
                 "HTJAH-I:6245-6246). This table lines up, per house, every already-computed "
                 "testimony the report holds elsewhere and counts where the balance lies — "
                 "Raman's own conclusion word: \"there is a preponderance of benefic "
                 "influences...\" (HTJAH-I:8870).")
        L.append("")
        L.append("_Three honesty rules govern this table. (1) The Verdict column is the "
                 "authoritative House-by-house verdict, unchanged — and it is deliberately "
                 "NOT counted among its own witnesses (a headline cannot corroborate itself). "
                 "(2) Raman states NO numeric rule for how many testimonies decide a matter "
                 "(HTJAH-I:495 says only that all must be properly weighed — and his own "
                 "worked conclusion weighs witnesses unequally, HTJAH-I:8870-8876); the "
                 "Preponderance column here is a simple equal-weight majority of leaning "
                 "witnesses — a presentation convention borrowing his vocabulary, not his "
                 "weighing — it never alters a verdict, and a 'contested' row means the "
                 "witnesses split, not that the verdict is wrong. (3) The witnesses are NOT "
                 "independent votes: lord, karaka and navamsa are the verdict's own inputs "
                 "restated by name, and the majority tenor derives from the same "
                 "significations as the headline. Yogas bearing on a house (Raman's Primary "
                 "Considerations, e.g. HTJAH-I:4135-4139) ARE now tallied, mapped on his "
                 "worked-chart principle — the houses each yoga's constituent planets own, "
                 "occupy or aspect (\"the nature of ownership of the planets causing the "
                 "yoga,\" HTJAH-I:2879-2890 — the principle, not an exact derivation; his own "
                 "example there names one house this mapping cannot produce) — with disclosed "
                 "limits: whole-chart pattern yogas carry no constituent identity and are "
                 "unmapped, and formation-strength modifiers are not graded — dusthana "
                 "formation can nullify Gajakesari (HTJAH-I:2948-2956) and can bring "
                 "Raja-Yoga Bhanga (HTJAH-I:15903, 16139; not absolutely, 15531), so a "
                 "dusthana-formed raja yoga may lean favourable here despite a possible "
                 "bhanga. A yoga row leans by its encoded kind (raja/dhana favourable, arishta "
                 "adverse) and, for the specific yogas whose classical printed effect is "
                 "unambiguous, by that effect — the Pancha Mahapurusha, Budha-Aditya, "
                 "Vasumathi and Jaya favourable; Daridra and Asatyavadi adverse (each with its "
                 "own citation in the Yogas section). Lunar and the remaining other-kind yogas "
                 "stay neutral (a conditionally-benefic lunar yoga can be nullified in dusthana "
                 "formation). Bhava-Bala rank is shown as a magnitude and carries no "
                 "direction._")
        L.append("")
        L.append("| House | Matter | Verdict | For | Against | Neutral | Absent | "
                 "Preponderance | Status |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for ht_ in r.preponderance.houses:
            L.append(f"| H{ht_.house} | {_HOUSE_NAME.get(ht_.house, '')} | {ht_.verdict} | "
                     f"{ht_.favourable} | {ht_.adverse} | {ht_.neutral} | {ht_.absent} | "
                     f"{ht_.preponderance} | {ht_.status} |")
        L.append("")
        for ht_ in r.preponderance.houses:
            detail = "; ".join(f"{t.name} {t.value}" for t in ht_.testimonies
                               if t.lean != "absent")
            L.append(f"- **H{ht_.house}** — {detail if detail else 'no decided testimony'}")
        pr = r.preponderance
        L.append("")
        if pr.most_corroborated_favourable is not None:
            L.append(f"- **Most-corroborated favourable house** — "
                     f"H{pr.most_corroborated_favourable}")
        if pr.most_corroborated_afflicted is not None:
            L.append(f"- **Most-corroborated afflicted house** — "
                     f"H{pr.most_corroborated_afflicted}")
        if pr.most_contested is not None:
            L.append(f"- **Most-contested house** — H{pr.most_contested} (its witnesses lean "
                     f"against its own headline — read that house's own section with extra "
                     f"care)")
        L.append("")

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

    # ── maraka x saturn-transit confluence: the classical "last signal" ──────
    if r.maraka_saturn:
        L.append("## Maraka x Saturn-transit confluence")
        L.append("")
        L.append("**In simple terms:** Raman names one specific classical signal for a maraka "
                 "period — Ayushkaraka Saturn transiting back over the sign it occupied at your "
                 "birth, or its trines, during a maraka-tier Dasha/Bhukti (HTJAH-II:4846-4849). "
                 "The windows below are where BOTH conditions the classical method asks for line "
                 "up. This shows only the RASI half of that signature — the Navamsa half is not "
                 "computed here. \"Maraka tier\" is how strong a death-signal the Bhukti's own "
                 "lords carry (primary=3, secondary=2, tertiary=1 per lord, summed) — a higher "
                 "number means both the MD and AD lord are more central to the classical maraka "
                 "set, not a stronger prediction.")
        L.append("")
        L.append("_A STATEMENT OF THE METHOD, NOT A PREDICTION: this project's own real-outcome "
                 "validation measured NO death-timing signal from maraka checks generally "
                 "(REAL_OUTCOME_GENERALIZATION.md). This section exists to show what Raman's "
                 "textbook method says, faithfully — never as a strengthened death signal._")
        L.append("")
        L.append("| Maraka Bhukti | Bhukti window | Confluence window | Sign | Maraka tier |")
        L.append("|---|---|---|---|---|")
        for c in r.maraka_saturn:
            L.append(f"| {c.maha}/{c.antar} | "
                     f"{_outlook_window_label(c.window_start_jd, c.window_end_jd)} | "
                     f"{_outlook_window_label(c.overlap_start_jd, c.overlap_end_jd)} | "
                     f"{_SIGN_NAME[c.sign]} | {c.score} |")
        L.append("")

    # ── health & vulnerability read-out (v17, pure re-read of existing verdicts) ─────
    if r.health_readout.rows:
        h = r.health_readout
        L.append("## Health & vulnerability read-out")
        L.append("")
        L.append("**In simple terms:** the health-adjacent verdicts this report already computed "
                 "— the 1st/6th/8th/12th house readings, the Moon and Mercury karakas, the "
                 "balarishta screen, the maraka tiers and the longevity band — gathered on one "
                 "page. Every row names the section it re-reads; nothing here is new.")
        L.append("")
        L.append(f"_{h.caveat}_")
        L.append("")
        L.append("| Indicator | Verdict | Detail | Re-read from |")
        L.append("|---|---|---|---|")
        for row in h.rows:
            L.append(f"| {row.area} | **{row.verdict}** | {row.note} | {row.provenance} |")
        L.append("")
        if h.maraka_tiers:
            tier_txt = ", ".join(f"{g} ({t})" for g, t in h.maraka_tiers)
            L.append(f"- **Maraka tiers** (re-read from The maraka scheme): {tier_txt}")
            L.append(f"- **22nd drekkana lord**: {h.drekkana22_lord}  |  "
                     f"**64th navamsa lord**: {h.navamsa64_lord}")
        L.append(f"- **Running period**: "
                 + ("carries a maraka-tier lord" if h.maraka_period_now
                    else "carries no maraka-tier lord")
                 + " (broad, low-discrimination flag by design)")
        L.append(f"- **Longevity band** (re-read from Longevity): {h.longevity_band}")
        L.append("")

    # ── Arishta & Bhanga (v22 — the affliction/cancellation chapter) ──────────
    if r.arishta is not None:
        a = r.arishta
        L.append("## Arishta & Bhanga")
        L.append("")
        L.append("**In simple terms:** the afflictions Raman screens for and — equally "
                 "doctrinal — the cancellations that neutralise them. Every row re-reads "
                 "a computed state; the antidote passage is Raman verbatim.")
        L.append("")
        bal = ("applies" if a.balarishta_applies and not a.balarishta_cancelled
               else "CANCELLED" if a.balarishta_cancelled else "does not apply")
        L.append(f"- **Balarishta (HPA-14)** — {bal}"
                 + (f" — {'; '.join(a.balarishta_reasons)}" if a.balarishta_reasons
                    else ""))
        L.append(f"- **Raman's antidotes (verbatim)** — \"{a.antidote_quote}\" "
                 f"({a.antidote_cite})")
        if a.bhangas:
            for p, dig, eff in a.bhangas:
                L.append(f"- **Bhanga** — {p}: {dig} cancelled to effective {eff} "
                         f"(neecha bhanga)")
        else:
            L.append("- **Bhanga** — no debilitation-cancellation operates in this chart")
        L.append(f"- **Kemadruma** — {a.kemadruma_note}")
        if a.protections:
            for pr_line in a.protections:
                L.append(f"- **Longevity protection** — {pr_line}")
        L.append(f"- **Band** — {a.band}")
        L.append(f"- **Maraka context** — {a.maraka_note}")
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

    # ── ishta/kashta outlook: the SAME windowed timeline, painted good/hard ────
    if r.ishta_kashta:
        L.append("")
        L.append("## Ishta/Kashta outlook")
        L.append("")
        L.append("**In simple terms:** a planet with more Ishta Phala (its own \"good "
                 "tendency\") inclines to give good results in its Dasha or Bhukti; more Kashta "
                 "Phala (\"hard tendency\") inclines to harder ones (GBB-10:134). This paints "
                 "that SAME lean across every period in the Life-narrative timeline above, not "
                 "just the one running now. Where a bhukti's own lord is stronger (by Shadbala) "
                 "than the Mahadasha lord, no general rule is stated for whose character wins — "
                 "so only the MD-predominates direction is shown (GBB-10:145-152).")
        L.append("")
        cur_md_ik: Optional[str] = None
        for ik in r.ishta_kashta:
            if ik.maha != cur_md_ik:
                cur_md_ik = ik.maha
                lean_word = ik.maha_lean or "no Ishta/Kashta data"
                L.append("")
                L.append(f"### {cur_md_ik} Mahadasha — {lean_word}")
            ad = ik.antar or ik.maha
            lean_word = ik.antar_lean or "no data"
            tail = f" — {ik.prevails}" if ik.prevails else ""
            L.append(f"- **{ad} AD** ({_outlook_window_label(ik.start_jd, ik.end_jd)}): "
                     f"{lean_word}{tail}")
        L.append("")

    # ── md-lord condition outlook: strength/vargottama painted onto the MD timeline ──
    if r.md_condition:
        L.append("## MD-lord condition outlook")
        L.append("")
        L.append("**In simple terms:** a Dasha delivers in proportion to how well-placed its "
                 "own ruling planet actually is — its strength, and its Navamsa disposition — "
                 "reaching its stated maximum only when strong in BOTH the main chart and the "
                 "Navamsa (HPA-24:51-86). This is the SAME check the Life-narrative timeline "
                 "above already runs for whichever Mahadasha is current, painted onto every "
                 "Mahadasha in the window — Shadbala strength, Vargottama and Navamsa are all "
                 "fixed at birth, so this is a lookup, not a new judgment.")
        L.append("")
        L.append("| Mahadasha | Window | Shadbala | Vargottama | Navamsa | At maximum |")
        L.append("|---|---|---|---|---|---|")
        for c in r.md_condition:
            strong_word = "strong" if c.strong else "weak" if c.strong is False else "unknown"
            nav = _SIGN_NAME[c.navamsa_sign] if c.navamsa_sign else "n/a"
            L.append(f"| {c.maha} | {_outlook_window_label(c.start_jd, c.end_jd)} | "
                     f"{strong_word} | {'yes' if c.vargottama else 'no'} | {nav} | "
                     f"{'yes' if c.at_maximum else 'no'} |")
        L.append("")

    # ── av dasha-seat outlook: the MD lord graded by his own bindus (AV-tier) ──
    if r.av_dasha_seats:
        L.append("## AV dasha-seat outlook")
        L.append("")
        L.append("> **Raman's own caveat governs this section**: \"Ashtakavarga method is "
                 "equally important. But, it does not seem to be quite reliable\" "
                 "(HTJAH-II:4453-4456). This classical method never overrides the Raman-band "
                 "readings elsewhere in this report — it is shown last among the Life-narrative "
                 "companions for that reason.")
        L.append("")
        L.append("**In simple terms:** a Dasha's lord can also be graded by how many "
                 "Ashtakavarga bindus he holds in his OWN natal sign — 5 or more reads "
                 "auspicious, 3 or fewer adverse, exactly 4 mixed (Patel ch015:996-1034). "
                 "Painted across every Mahadasha in the window; bindus are fixed at birth, so "
                 "this is a lookup, not a new judgment.")
        L.append("")
        L.append("| Mahadasha | Window | Sign | Bindus | Reading |")
        L.append("|---|---|---|---|---|")
        for a in r.av_dasha_seats:
            bindus_cell = str(a.bindus) if a.bindus is not None else "n/a"
            L.append(f"| {a.maha} | {_outlook_window_label(a.start_jd, a.end_jd)} | "
                     f"{_SIGN_NAME[a.sign]} | {bindus_cell} | {a.read} |")
        L.append("")

    # ── Dasha Kakshya intervals (v16, ASP-12 eightfold division per MD run) ─────────────
    if r.dasa_kakshya:
        L.append("## Dasha Kakshya intervals")
        L.append("")
        L.append("**In simple terms:** each Mahadasha can be split into 8 equal parts ruled in "
                 "Kakshya order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna — "
                 "ASP-12:174-182). A part whose ruler donated a bindu to the Dasha lord's own "
                 "natal sign inclines favourable; one whose ruler did not runs adverse "
                 "(ASP-12:211-214), relieved when the ruler's own signs hold optimum bindus "
                 "there (ASP-12:215-219). Raman reports the scheme from other scholars and "
                 "then works it over his own signature — a timing lens, never a verdict.")
        L.append("")
        L.append("| Mahadasha | Interval ruler | Window | Donated | Reading |")
        L.append("|---|---|---|---|---|")
        for k in r.dasa_kakshya:
            L.append(f"| {k.maha} | {k.ruler} | {_outlook_window_label(k.start_jd, k.end_jd)} | "
                     f"{'yes' if k.donated else 'no'} | {k.reading} |")
        L.append("")

    # ── life-chapters (v15, one woven chapter per Mahadasha) ──────────────────
    if r.life_chapters.chapters:
        L.append("")
        L.append("## Life-chapters")
        L.append("")
        L.append("**In simple terms:** the Life-narrative above and its three companion tables "
                 "(Ishta/Kashta, MD-lord condition, AV dasha-seat) each paint ONE lens across "
                 "the same years. This section reads them TOGETHER, one chapter per Mahadasha "
                 "— the way Raman himself narrates a nativity (his Chart No. 203 reads each "
                 "dasha from yoga + lord condition + house placement + directional influence "
                 "in one paragraph, HTJAH-I:15950-15999), and the way his blending doctrine "
                 "demands: \"astrological predictions can be accurate when the influences of "
                 "birth chart are blended with those of Gochara and Ashtakavarga, together "
                 "with Vedha or obstructing forces\" (HPA-34:369-381; Vedha is not "
                 "re-narrated per chapter — it is applied in the Gochara table and sampled as "
                 "interference in the Dasha x Transit confluence table). Nothing here is a "
                 "new judgment — every clause re-reads a row already shown in the sections "
                 "above, and chapter spans are clipped to the report's display window (a "
                 "Mahadasha may begin before or continue past its shown dates). Within each "
                 "chapter the natal factors come FIRST and transits LAST: \"primary "
                 "importance must be given to the natal positions and Dasha and only "
                 "secondary consideration to transiting planets\" (HTJAH-I:8410-8411; "
                 "HTJAH-II:4679-4687 repeats it — transits are secondary, catalytic, "
                 "conclusions rest on Dasa-vichara). As everywhere in this report: how the "
                 "method reads this chart, not a prediction.")
        for ch in r.life_chapters.chapters:
            now_tag = " — now" if ch.is_current else ""
            L.append("")
            L.append(f"### {ch.maha} Mahadasha "
                     f"({_outlook_window_label(ch.start_jd, ch.end_jd)}){now_tag}")
            L.append("")
            L.append(ch.narrative)
        L.append("")

    # ── decade indication timeline (v28 — NEVER probabilities) ────────────────
    if r.decades is not None:
        dt = r.decades
        L.append("## Decade indication timeline")
        L.append("")
        L.append(f"_{dt.frame}_")
        L.append("")
        for d in dt.decades:
            L.append(f"### {d.label}")
            L.append("")
            if not d.inside_window:
                L.append(f"_{d.note}_")
                L.append("")
                continue
            L.append(f"- **Running Mahadashas** — {', '.join(d.md_lords) or '-'}"
                     + (f" (leans: {', '.join(d.leans)})" if d.leans else ""))
            if d.areas_favourable:
                L.append(f"- **Areas the method reads favourably here** — "
                         f"{'; '.join(d.areas_favourable)}")
            if d.areas_challenged:
                L.append(f"- **Areas the method reads as challenged here** — "
                         f"{'; '.join(d.areas_challenged)}")
            if d.yogas_ripening:
                L.append(f"- **Yogas ripening** — {'; '.join(d.yogas_ripening)}")
            L.append(f"- _{d.note}_")
            L.append("")

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
        L.append("| planet | sign | from Moon | classical | AV bindus | proportion | Kakshya | Vedha by | **net** |")
        L.append("|---|---|---:|---|---|---|---|---|---|")
        for g in r.gochara:
            av = str(g.bav_bindus) if g.bav_bindus is not None else "-"
            vedha = ", ".join(g.vedha_by) if g.vedha_by else "-"
            # Kakshya micro-transit (ASP-13): the 3¾° arc's lord and whether it donated a bindu
            # to the transited sign — Raman's finer within-sign dial. bindus/8 is his own
            # proportion law ("to the extent of 62%" = 5/8, ASP-13:280-282).
            prop = f"{g.bav_proportion:.0%}" if g.bav_proportion is not None else "-"
            kak = ("-" if g.kakshya_lord is None else
                   f"{g.kakshya_lord} ({'donated' if g.kakshya_favourable else 'no bindu'})")
            L.append(f"| {g.planet} | {_SIGN_NAME[g.sign]} | {g.house_from_moon} | "
                     f"{'favourable' if g.gochara_good else 'adverse'} | {av} | {prop} | {kak} | "
                     f"{vedha} | **{'favourable' if g.net_good else 'obstructed/adverse'}** |")
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

    # ── profession synthesis (v23 — every encoded angle, then the convergence) ─
    if r.profession is not None:
        pf = r.profession
        L.append("")
        L.append("## Profession synthesis")
        L.append("")
        L.append("**In simple terms:** Raman derives profession from several angles; "
                 "this section runs every encoded one and counts where they converge — "
                 "a deterministic overlap count, never a new judgment.")
        L.append("")
        L.append("| Derivation | Resolves to | Raman's vocation words | Cite |")
        L.append("|---|---|---|---|")
        for src in pf.sources:
            note = f" _{src.note}_" if src.note else ""
            L.append(f"| {src.source} | {src.key} | {src.trades}{note} | {src.cite} |")
        if pf.mode_split:
            L.append("")
            L.append("- **H10 mode split** — "
                     + "; ".join(f"{k}: {v}" for k, v in pf.mode_split))
        if pf.convergent:
            L.append("- **Convergent trades** (named by 2+ derivations) — "
                     + ", ".join(f"{w} ({n})" for w, n in pf.convergent))
        L.append("")

    # ── wealth chapter (v24 — the channels, not a single verdict) ─────────────
    if r.wealth is not None:
        w = r.wealth
        L.append("## Wealth chapter")
        L.append("")
        L.append("**In simple terms:** not one wealth verdict but the CHANNELS — how the "
                 "method reads earning, accumulating, inheriting, speculating, and where "
                 "expansion periods fall. Every row re-reads a judged signification or a "
                 "cited source-of-gains table.")
        L.append("")
        L.append("| Channel | Reading | Cite |")
        L.append("|---|---|---|")
        for row in w.rows:
            L.append(f"| {row.channel} | {row.reading} | {row.cite} |")
        L.append("")
        if w.expansion_periods:
            L.append("- **Periods of expansion** (H2/H11 activated at ordinary tier or "
                     "better — a timing lens, never a promise): "
                     + "; ".join(w.expansion_periods))
            L.append("")

    # ── marriage monograph (v25) ──────────────────────────────────────────────
    if r.marriage is not None:
        from app.raman_saab.monographs import MARRIAGE_INTRO as _MI
        m = r.marriage
        L.append("## Marriage monograph")
        L.append("")
        L.append(f"**The 7th house's scope (Raman verbatim):** \"{m.seventh_covers}\" "
                 f"(HTJAH-II:{_MI[0]})")
        L.append("")
        L.append(f"- **Headline (unchanged H7 verdict)** — {m.verdict}")
        if m.lord_period_text:
            L.append(f"- **The 7th lord in house {m.lord_placement_house} (Raman "
                     f"verbatim, his periods)** — \"{m.lord_period_text}\" "
                     f"(HTJAH-II:710)")
        if m.spouse_sign_text:
            L.append(f"- **The partner's significator in its sign (HPA-22)** — "
                     f"\"{m.spouse_sign_text[0]}\" ({m.spouse_sign_text[1]})")
        if m.upapada:
            L.append(f"- **Upapada** — {m.upapada}")
        if m.fired_kalatra:
            L.append("- **Kalatra rules firing in THIS chart** (of the 50 encoded):")
            for branch, text, cite in m.fired_kalatra:
                L.append(f"  - ({branch}) {text} ({cite})")
        L.append(f"- **Timing doctrine (Raman verbatim)** — \"{m.timing_navamsa}\" "
                 f"(HTJAH-II:853)")
        if m.timing_windows:
            L.append(f"- **H7 activations in the window** — {'; '.join(m.timing_windows)}")
        if m.children_after:
            L.append(f"- **Children (H5)** — {m.children_after}")
        L.append("")
        L.append("_On separation and loss of the partner, the method's own statements — "
                 "quoted, not composed; A STATEMENT OF THE METHOD, NOT A PREDICTION "
                 "(this project's validation measured no real-outcome signal):_")
        L.append("")
        L.append(f"> \"{m.separation_quote}\" (HTJAH-II:887)")
        L.append("")

    # ── children chapter (v26) ────────────────────────────────────────────────
    if r.children is not None:
        c = r.children
        L.append("## Children chapter")
        L.append("")
        L.append(f"- **Headline (unchanged H5 verdict)** — {c.verdict}")
        for key, v in c.significations:
            L.append(f"- **{key}** — {v}")
        if c.fired_rules:
            L.append("- **Putra rules firing in THIS chart:**")
            for branch, text, cite in c.fired_rules:
                L.append(f"  - ({branch}) {text} ({cite})")
        if c.timing_windows:
            L.append(f"- **H5 activations in the window** — {'; '.join(c.timing_windows)}")
        L.append("")
        L.append("_Raman's fifth-house combinations, verbatim (fertility, many issues, "
                 "delay, loss — the classical spectrum, quoted whole so nothing is "
                 "cherry-picked):_")
        L.append("")
        L.append(f"> \"{c.combos_quote}\" (HTJAH-I:5179)")
        L.append("")
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

    # ── karmic evolution (v30 — the walled Jaimini layer, post-lift) ──────────
    if r.karmic is not None:
        kv = r.karmic
        L.append("")
        L.append("## Karmic evolution (Jaimini)")
        L.append("")
        L.append(f"_{kv.frame}_")
        L.append("")
        L.append(f"- **Atmakaraka** — {kv.atmakaraka} (the 7-karaka scheme, locked)")
        if kv.karakamsa:
            L.append(f"- **Karakamsa** — {kv.karakamsa}")
        if kv.upapada:
            L.append(f"- **Upapada** — {kv.upapada}")
        L.append(f"- **Raman's Jaimini doctrine (verbatim)** — \"{kv.doctrine_quote}\" "
                 f"({kv.doctrine_cite})")
        if kv.d20_core:
            L.append(f"- **D-20 Vimsamsa (spiritual) core** — {kv.d20_core}")
        if kv.d60_core:
            L.append(f"- **D-60 Shashtiamsa (totality) core** — {kv.d60_core}")
        L.append("")

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
    L.append("")
    L.append("_How to read several strength measures at once (the general form of the House "
             "strength cross-check's own finding above): Raman's system tracks a house/planet/"
             "period along SEVERAL INDEPENDENT axes, not one score. The VERDICT (favourable/"
             "afflicted) comes from aspect, lordship and association — a direction "
             "(HTJAH-I:468-478 lists a house's strength and its aspects/qualities as separate "
             "considerations). Bhava Bala/Shadbala is mostly a MAGNITUDE — how fully results are "
             "enjoyed, not whether they are good (GBB-9:32-34). Avastha is a STATE the planet "
             "acts from (Deeptadi avasthas, HPA Ch.7). Ishta/Kashta is a period's own good-vs-"
             "hard TENDENCY (GBB-10:134). Ashtakavarga bindus are a separate, lower-reliability "
             "CORROBORATING tier by Raman's own admission (\"it does not seem to be quite "
             "reliable,\" HTJAH-II:4453-4456). These axes are not meant to always agree — a "
             "planet can be strong yet in a hard state, or favourable yet thin — and reading two "
             "of them apart is not a contradiction to resolve._")
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
    # ── full life synthesis (v29 — the biography-closing chapter) ─────────────
    if r.life_synthesis is not None:
        ls = r.life_synthesis
        L.append("## Full life synthesis")
        L.append("")
        L.append("**In simple terms:** the report's chapters read as one biography — "
                 "temperament, destiny, career, wealth, marriage, children, protections, "
                 "reputation, health, turning points, dominant themes — every line a "
                 "re-read of a section above, nothing judged anew.")
        L.append("")
        for theme, para in ls.paragraphs:
            L.append(f"**{theme}.** {para}")
            L.append("")
        L.append(f"_{ls.closing}_")
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
    if n.turning_points:
        L.append("- **Turning points** (where the period lean changes — a timing lens, "
                 "not an event): "
                 + "; ".join(f"{when}: {what}" for when, what in n.turning_points))

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
