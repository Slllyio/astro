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
    # v32 (2026-08-04, user-requested): the judgment graph — used already (Your Reading's
    # dominant-planet sentence quotes its census count) but never SHOWN. Rides along
    # immediately after plain_reading, the same non-append-at-the-end exception v5 already
    # established, so the graph that grounds "Your Reading" sits right beside it.
    SectionSpec("judgment_graph", "## Judgment graph", 'id="judgment-graph"', "v32"),
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
    # v34 (2026-08-18, user-requested): the integrated interpretation layer — the theme
    # synthesis reading ACROSS every section into one coherent whole (Executive Portrait,
    # dominant themes, house networks, contradictions, dasha evolution, varga matrix). A
    # conscious near-top amendment (the v5/v32 exception): the honesty gate and the
    # how-to-read precedence come first, then the integrated interpretation opens the
    # substantive reading, then the technical sections it explains. Re-read only; the
    # golden ratchet is untouched (theme_synthesis imports nothing in the verdict path).
    # _FROZEN grown in the same commit per the amendment procedure.
    SectionSpec("themes", "## The integrated reading", 'id="integrated-reading"', "v34"),
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
    # v31 (2026-08-04, user-requested): rectification confidence — birth-time
    # sensitivity measured at ±2/±5 minutes; placed with the checkable-inputs cluster
    # (a reading must be checkable — and so must its inputs' stability).
    SectionSpec("rect_confidence", "## Rectification confidence",
                'id="rect-confidence"', "v31"),
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
    # v33 (2026-08-14, user-requested): aptitude, intelligence & work style — the three
    # trait axes the report never had as output fields, re-read from already-judged
    # material (H5 intellect + Jupiter karaka, Mercury via graha_chapters, the fired
    # H1.M.* Moon-mind rule, H3 courage, the HTJAH-II vocational tables, H10 modes).
    # Appended at the END per the append-only default; _FROZEN grown in the same commit.
    SectionSpec("aptitude", "## Aptitude, intelligence & work style", 'id="aptitude"', "v33"),
)

#: The HTML renderer's document order (the signature chips live in the page header, and the
#: chart grids/now-box are HTML-only). Same append-only rule applies.
HTML_SECTION_ORDER: tuple[str, ...] = (
    "title", "plain_reading", "chart_signature", "judgment_graph", "ruler", "planet_bios", "psych",
    "now_box",
    "info_content", "interpretation_guide", "themes", "stands_out", "digest",
    "dashboard",
    "chart_grids", "positions", "rect_confidence", "shadbala", "yogas", "yoga_timing",
    "yoga_deep",
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
    "aptitude",   # v33 (2026-08-14): appended at the end, same order as SECTION_CONTRACT
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


#: The canonical measured population framing (Wave-2, 2026-08-17): the mechanism constants
#: recorded in CLAUDE.md / docs/raman_saab/CAPSTONE.md — calibration context for the
#: near-universal count, NEVER a validation claim. Rendered beneath the info sentence on
#: every surface.
POPULATION_NOTE: Final[str] = (
    "Population context (measured, for calibration - never validation): across 22,177 real "
    "charts judged by this same method, the median chart carries 19 afflicted and 31 "
    "favourable significations simultaneously, and 97.1% of charts offer both poles at "
    "once - which is why a near-universal reading says almost nothing about any one life.")


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


#: rarity-band precedence for "what stands out": rare strictly before notable before common
#: (the old two-way common/non-common split let the sole RARE row sort last — 2026-08-17 fix).
_RARITY_ORDER: Final[dict[str, int]] = {"rare": 0, "notable": 1, "common": 2}


def distinctive_entries(calibration: dict[int, CalibratedHouseReading], n: int | None = None):
    """The readings that most distinguish this chart — rarity band first (rare before
    notable before common), then furthest from the population midpoint within each band.
    Returns [(house, entry)] ranked. Pure information content, not prediction.

    With ``n=None`` (the default since 2026-08-17, report-critique fix) EVERY entry the
    info-content census counts as distinctive (``rarity != "common"``) is returned, so the
    table's row-count always equals the census sentence's "N are genuinely distinctive" —
    the old fixed cap of 7 showed 7 rows while the sentence said 17. Pass an explicit ``n``
    to cap the ranked list (legacy behaviour, top-n regardless of band)."""
    scored = [(h, e) for h, e in _all_entries(calibration)
              if e.favourability_percentile is not None]
    scored.sort(key=lambda he: (_RARITY_ORDER.get(he[1].rarity, 3),
                                -abs(he[1].favourability_percentile - 0.5)))
    if n is None:
        return tuple(he for he in scored if he[1].rarity != "common")
    return tuple(scored[:n])


def distinctive_gloss(e) -> str:
    """One plain sentence making a distinctive row intelligible: which side of the
    population midpoint it sits on — with an explicit flag when that direction and the
    verdict's own direction disagree (a favourable verdict at the 32nd percentile is a
    real, non-obvious combination, not a typo). Descriptive idiom only, never a claim
    about a life."""
    pct = getattr(e, "favourability_percentile", None)
    if pct is None:
        return ""
    if pct >= 0.5:
        gloss = f"more favourable than {pct:.0%} of charts"
        if e.verdict == "afflicted":
            gloss += ", despite the afflicted verdict"
    else:
        gloss = f"less favourable than {1 - pct:.0%} of charts"
        if e.verdict == "favourable":
            gloss += ", despite the favourable verdict"
    return gloss


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

    # Wave-2 D3 (2026-08-18, add-only): the moderating-factor clause — Raman's own
    # partial-affliction device ("the affliction is considerably reduced by..."),
    # composed ONLY from flags the judge's ledger already carries and disclosed
    # descriptively; never a remedy, never a date, never a re-weighing.
    mod = house_moderating_clause(r, house)
    if mod:
        bits.append(mod)

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


# ── Wave-2 house-block composers (2026-08-18, add-only; shared by BOTH renderers, the
#    `house_conclusion` no-drift precedent). Each is a pure re-read of already-computed
#    ledgers/metadata/timeline rows — no verdict, lean, count or gate is touched. ──────

#: The one rule-record fortified-branch placeholder that is maintenance text, not Raman's
#: effect prose — chief-combination rows carrying it are skipped (house-critique ADD-1).
_CHIEF_PLACEHOLDER: Final[str] = "no specifically favourable variant given"


def house_chief_combinations(r: "DetailedReport", house: int, per_sig: int = 3,
                             ) -> tuple[tuple[str, str, str, str], ...]:
    """The chief fired combinations of a house — (signification, rule id, Raman's effect
    prose, work:line) — exactly how HTJAH's own chapters argue a bhava: the combination,
    in his words, with its citation. Selection only, no judgment: per signification the
    LEAD ledger's fired rules, the branch matching the signification's own verdict tenor
    first (malefic rows on an afflicted verdict, benefic on favourable), capped at
    `per_sig`, de-duplicated by rule id across the house. Fortified rows whose text is
    the recorded no-variant placeholder are skipped (they are maintenance notes, not
    effect prose).

    Wave-3 (2026-08-18): the effect prose is routed through the marriage monograph's own
    `monographs.split_maintainer_notes` — encoding-scope artifacts ("v1-OOS", "owned by
    H7.C.60", "TODO(predicate: ...)") leave the client sentence and are re-emitted, in
    full, by `house_maintainer_notes` as a trailing fine-print line. Routing, never
    removal; one helper, not a second implementation."""
    from app.raman_saab.monographs import split_maintainer_notes
    pf = next((p for p in r.proformas if p.house == house), None)
    if pf is None:
        return ()
    out: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for sv in pf.significations:
        led = sv.ledger
        v = str(sv.verdict)
        ordered = ((*led.fired_malefic, *led.fired_benefic, *led.fired_neutral)
                   if v == "afflicted" else
                   (*led.fired_benefic, *led.fired_malefic, *led.fired_neutral))
        taken = 0
        for fr in ordered:
            if taken >= per_sig:
                break
            if fr.rule.id in seen:
                continue
            text = (fr.text or "").strip()
            if not text or _CHIEF_PLACEHOLDER in text:
                continue
            seen.add(fr.rule.id)
            client, _notes = split_maintainer_notes(text)
            out.append((sv.signification, fr.rule.id, client or text,
                        f"{fr.rule.source.work}:{fr.rule.source.line}"))
            taken += 1
    return tuple(out)


def house_maintainer_notes(r: "DetailedReport", house: int, per_sig: int = 3) -> str:
    """The encoding-scope fine print stripped out of this house's chief-combination
    prose, re-emitted verbatim in ONE trailing line (the marriage monograph's own
    device). Nothing is lost: `house_chief_combinations` carries the client sentence,
    this carries the maintainer half, and the raw rule text in the data is untouched."""
    from app.raman_saab.monographs import split_maintainer_notes
    pf = next((p for p in r.proformas if p.house == house), None)
    if pf is None:
        return ""
    kept = {rid for _s, rid, _t, _c in house_chief_combinations(r, house, per_sig)}
    notes: list[str] = []
    for sv in pf.significations:
        for _led in (sv.ledger,):
            for fr in (*_led.fired_malefic, *_led.fired_benefic, *_led.fired_neutral):
                if fr.rule.id not in kept:
                    continue
                _client, note = split_maintainer_notes((fr.text or "").strip())
                row = f"{fr.rule.id}: {note}" if note else ""
                if row and row not in notes:
                    notes.append(row)
    return " | ".join(notes)


def house_frame_line(r: "DetailedReport", house: int) -> str:
    """The frame-disclosure line — WHICH reference frame judged this house, with the
    Lagna frame named beside it (Raman names his frame in nearly every worked chart;
    the stronger frame-lord decides, HTJAH-I:645-646). Composed entirely from
    `lead_frame` + the frames' own ledgers; it re-states, never re-decides — and it
    reconciles the pillar line (always lagna-frame figures) with the reading line
    (lead-frame figures) by naming both."""
    pf = next((p for p in r.proformas if p.house == house), None)
    if pf is None or not pf.significations:
        return ""
    sv = pf.significations[0]
    lagna_led = _lagna_ledger(sv)

    def _facts(led) -> str:
        s = led.lord
        if led.lord_strong is not None:
            s += f", {'strong' if led.lord_strong else 'weak'}"
        s += f", navamsa {led.navamsa_status}"
        return s

    frame_word = {"lagna": "Lagna", "moon": "Moon (Chandra Lagna)",
                  "karaka": "karaka"}.get(str(sv.lead_frame), str(sv.lead_frame))
    if str(sv.lead_frame) == "lagna":
        line = f"Judged from the Lagna frame (lord {_facts(lagna_led)})"
        moon_led = next((L for L in (sv.ledger, *sv.alt_ledgers) if L.frame == "moon"),
                        None)
        if moon_led is not None:
            line += (f"; from the Moon (Chandra Lagna) the frame-lord is "
                     f"{_facts(moon_led)}")
    else:
        line = (f"Judged from the {frame_word} frame (lord {_facts(sv.ledger)}); "
                f"from the Lagna the lord is {_facts(lagna_led)}")
    return line + " - the stronger frame-lord's frame decides (HTJAH-I:645-646)."


def house_current_tiers(r: "DetailedReport") -> dict[int, str]:
    """{house: four-tier grade} for the RUNNING bhukti — computed once through the ONE
    shared `graded_buckets` implementation (HTJAH-I:1592-1596, 1635-1640). Houses that
    neither period-lord influences are simply absent from the mapping. Wave-3
    (2026-08-18): hoisted out of `house_current_tier_line` so the verdict-first strip and
    the per-house line read the SAME grading rather than each recomputing it."""
    tp = next((tp for tp in r.timeline.periods
               if tp.period.start_jd <= r.ref_jd < tp.period.end_jd), None)
    if tp is None:
        return {}
    _assoc, buckets = graded_buckets(tp, r.chart)
    out: dict[int, str] = {}
    for tier, items in buckets.items():          # buckets are already best-tier-first
        for a in items:
            out.setdefault(a.house, tier)
    return out


def house_current_tier_line(r: "DetailedReport", house: int) -> str:
    """The running period's fructification tier FOR THIS HOUSE — the same four-tier
    vocabulary (par excellence / ordinary / limited / feeble, HTJAH-I:1592-1596,
    1635-1640) the Life-narrative already computes via `vimshottari.bhukti_tier`,
    re-read per house where the reader is actually asking about the house. Pure re-read
    of the current timeline period through the ONE shared `graded_buckets`
    implementation; never a prediction."""
    tp = next((tp for tp in r.timeline.periods
               if tp.period.start_jd <= r.ref_jd < tp.period.end_jd), None)
    if tp is None:
        return ""
    maha, antar = tp.period.maha, tp.period.antar
    label = f"{maha} MD" + (f" / {antar} AD" if antar else "")
    tier = house_current_tiers(r).get(house)
    if tier is None:
        return (f"In the running {label} period neither period-lord influences this "
                f"house - no fructification grade for the current bhukti "
                f"(HTJAH-I:1592-1596).")
    return (f"In the running {label} period this house grades {tier} "
            f"(HTJAH-I:1592-1596).")


def house_moderating_clause(r: "DetailedReport", house: int) -> str:
    """The moderating-factor clause (house-critique ADD-3): when the ledger carries a
    qualification the judge ALREADY credited — a parivartana-resilient lord/karaka, an
    intact strong karaka under an afflicted headline, or a catastrophic-gate demotion —
    say so in the Conclusion, descriptively. Composed only from `FrameLedger` flags and
    `SignificationVerdict.metadata` the verdict path itself recorded; no remedy, no
    date, no re-weighing, and the headline stands verbatim."""
    pf = next((p for p in r.proformas if p.house == house), None)
    if pf is None or not pf.significations:
        return ""
    verdict = str(pf.rollup)
    sv = pf.significations[0]
    led = sv.ledger
    mods: list[str] = []
    if verdict in ("afflicted", "mixed") and led.parivartana_resilient:
        mods.append("the lord or karaka stands in a parivartana (exchange) - the "
                    "resilience the judge already credited in its ledger")
    if (verdict == "afflicted" and led.karaka_strong is True and led.karaka_intact
            and not led.lord_karaka_identical):
        mods.append(f"the karaka {led.karaka} itself stands strong and intact - the "
                    f"matter's core significator is not struck")
    gates = [v for k, v in pf.metadata if k == "catastrophic_gate"]
    for g in gates:
        mods.append(f"a catastrophic reading was demoted by the multiply-afflicted bar "
                    f"({g} - fewer fired malefic rules than Raman's own multiply-"
                    f"afflicted configurations carry)")
    if not mods:
        return ""
    return "the affliction is qualified - " + "; ".join(mods)


# ── Wave-3 (2026-08-18) traversal composers ─────────────────────────────────
# The house chapter is the report's longest stretch; these compose the SCANNING layer
# (a verdict-first strip, the in-block cross-references, the calibration rollup) out of
# state the judgment path already computed. Every one of them is selection or
# restatement — no verdict, count, band or gate is touched, and nothing below them is
# removed: the deep blocks render exactly as before, in full.


@dataclass(frozen=True)
class HouseStripRow:
    """One row of the verdict-first house strip — a pure re-read of the deep block that
    follows it (same verdict, same driver, same split note, same running-period tier)."""
    house: int
    name: str
    verdict: str
    driver: str          # the signification that drove the rollup ("" when none decided)
    split: str           # short split-status badge ("2-2 split" / "5/6 favourable"), "" if none
    split_note: str      # the full split sentence (tooltip / title text), "" if none
    tier: str            # running-bhukti four-tier grade, "" when neither period-lord acts
    inverted: bool       # the driver sits on an atlas-proven INVERTED channel


def house_strip_badge(split: "TenorSplit", note: str | None) -> str:
    """The short split badge label the HTML house-head already composes, hoisted so the
    markdown strip and the HTML strip cannot drift ("" when the tenor agrees with the
    headline and no note is emitted)."""
    if not note:
        return ""
    if split.favourable == split.afflicted and split.mixed == 0:
        return f"{split.favourable}-{split.afflicted} split"
    n = {"favourable": split.favourable, "afflicted": split.afflicted,
         "mixed": split.mixed}[split.majority]
    return f"{n}/{split.total} {split.majority}"


def house_strip_rows(r: "DetailedReport") -> tuple[HouseStripRow, ...]:
    """The twelve-row verdict-first strip that opens the house chapter — house, plain
    name, verdict, driver, split badge, and whether the running period lights it. Every
    cell restates a value the deep block below prints in full; the strip decides nothing
    and hides nothing (REPORT COMPLETENESS: it is a scanning index ABOVE the blocks, not
    a replacement for them)."""
    tiers = house_current_tiers(r)
    rows: list[HouseStripRow] = []
    for mr in r.synthesis.matters:
        cal = r.calibration[mr.house]
        drv = driver_entry(cal, mr.verdict)
        split = signification_tenor_split(cal)
        note = tenor_note(split, mr.verdict)
        rows.append(HouseStripRow(
            house=mr.house, name=mr.name, verdict=mr.verdict,
            driver=drv.signification if drv else "",
            split=house_strip_badge(split, note), split_note=note or "",
            tier=tiers.get(mr.house, ""),
            inverted=bool(drv is not None and drv.inverted_warning)))
    return tuple(rows)


def calibration_rollup_line(reading: "CalibratedHouseReading") -> str:
    """ONE summary line above a house's population-context rows when they repeat — the
    critique's H1 (three verbatim-identical lines) and H6 (five near-universal rows)
    case. Fires when >= 3 rows share a verdict+degree band, or >= 3 sit in a
    near-universal band. ADD-ONLY: every individual row is still rendered beneath it;
    this only tells the reader in advance that they repeat, so the rows that genuinely
    differ stand out. Empirical overlay wording — not Raman."""
    rows = [e for e in reading.entries if e.favourability_percentile is not None]
    total = len(rows)
    if total < 3:
        return ""
    bands: dict[tuple[str, str], int] = {}
    for e in rows:
        key = (str(e.verdict), str(e.degree))
        bands[key] = bands.get(key, 0) + 1
    (top_v, top_d), top_n = max(bands.items(), key=lambda kv: (kv[1], kv[0]))
    near = sum(1 for e in rows if e.band_share is not None and e.band_share >= 0.5)
    parts: list[str] = []
    if top_n >= 3:
        parts.append(f"{top_n} of {total} sub-readings return the same "
                     f"{top_v} ({top_d}) band")
    if near >= 3:
        parts.append(f"{near} of {total} are near-universal - that band carries "
                     f"little information")
    if not parts:
        return ""
    return "Rollup: " + "; ".join(parts) + ". Every individual row is kept below."


def house_dashboard_conflicts(r: "DetailedReport", house: int) -> tuple[str, ...]:
    """PREC-1 cross-references, in the block where the reader actually stumbles: the
    dashboard matters whose dedicated-reader verdict differs from THIS house's rollup.
    Same detection as `tension_narrator.narrate_tensions` item 2 (one `_MATTER_HOUSE`
    map, one comparison) — re-read per house so the pointer appears only where the
    disagreement is real. Empty for every house whose matters agree."""
    from app.raman_saab.tension_narrator import _MATTER_HOUSE
    prof = next((p for p in r.proformas if p.house == house), None)
    if prof is None:
        return ()
    rollup = str(prof.rollup)
    out: list[str] = []
    for en in r.dashboard.entries:
        if _MATTER_HOUSE.get(en.matter) != house:
            continue
        if (en.verdict in ("favourable", "afflicted")
                and rollup in ("favourable", "afflicted")
                and en.verdict != rollup):
            out.append(f"Cross-reference: the dashboard reads {en.matter} "
                       f"{en.verdict} while this bhava reads {rollup} - the matter is "
                       f"judged by its dedicated reader, the bhava by its weakest "
                       f"decided matter. PREC-1 in \"How to read this report\" governs: "
                       f"ask the dashboard for a matter, this block for the house.")
    return tuple(out)


#: Metadata keys whose detail is deliberately deferred to the Longevity chapter — the H8
#: block judges the bhava, the Longevity chapter carries the span/maraka detail (PREC-8).
_LONGEVITY_DEFERRED_KEYS: frozenset[str] = frozenset({"death_window", "decanate_cause"})


def house_longevity_pointer(r: "DetailedReport", house: int) -> str:
    """The deferral pointer for the house that computed longevity metadata it does NOT
    print (the H8 death-window / 22nd-decanate rows, `house_template._event_timing`).
    Conditional on the metadata actually being present, so it can never appear on a
    house that computed nothing to defer."""
    pf = next((p for p in r.proformas if p.house == house), None)
    if pf is None:
        return ""
    keys = {k for k, _v in pf.metadata}
    for sv in pf.significations:
        keys |= {k for k, _v in sv.metadata}
    if not (keys & _LONGEVITY_DEFERRED_KEYS):
        return ""
    return ("Cross-reference: the maraka-bhukti and 22nd-decanate detail this house "
            "computes is not repeated here - it is carried in the Longevity chapter "
            "below, where the band is established first and the marakas second "
            "(PREC-8).")


#: One pointer, reused wherever an atlas-proven inverted channel is flagged.
INVERTED_POINTER = ("Cross-reference: \"Information content of this reading\" above "
                    "lists every inverted channel in this chart and what the atlas "
                    "measured; PREC-9 governs - the overlay outranks the verdict as "
                    "skepticism, never as a re-judgment.")

#: One pointer, reused wherever a split-status note is emitted.
SPLIT_POINTER = ("Cross-reference: the precedence rules for this disagreement are in "
                 "\"How to read this report\" above - PREC-1 (a bhava is a different "
                 "grain from a matter) and PREC-3 (a split is disclosed, never "
                 "re-voted).")


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


def influence_basis_table(chart: RamanChart) -> dict[int, dict[str, tuple[str, ...]]]:
    """{house: {planet: (role tags)}} via the role-preserving `timer_roles` — computed once
    per report so every renderer (markdown / JSON / standalone HTML) derives the SAME
    influence basis for the tier buckets (Wave-2, 2026-08-18: derive the tier, don't
    assert it — HTJAH-I:1586-1596 names the factors individually)."""
    from app.raman_saab.primitives.vimshottari import timer_roles
    return {h: timer_roles(chart, h) for h in range(1, 13)}


def influence_basis(table: dict[int, dict[str, tuple[str, ...]]],
                    house: int, lord: Optional[str]) -> str:
    """The factor(s) by which `lord` influences `house`, as a short tag string ("owns+karaka").
    A lord that only reaches the house through its allied event house (the 2/11 and 9/12
    unions `active_houses` applies) is tagged "via H<n> <tags>" — honest about the union
    rather than implying a direct factor. "" when the lord is None or resolves nowhere
    (never expected for an activation row; kept as a loud-empty rather than a guess)."""
    from app.raman_saab.primitives.vimshottari import _EVENT_AUX_HOUSES
    if lord is None:
        return ""
    tags = table.get(house, {}).get(lord)
    if tags:
        return "+".join(tags)
    for aux in _EVENT_AUX_HOUSES.get(house, ()):
        aux_tags = table.get(aux, {}).get(lord)
        if aux_tags:
            return f"via H{aux} " + "+".join(aux_tags)
    return ""


def gochara_synthesis_sentence(g) -> str:
    """One deterministic synthesis sentence for a Gochara snapshot row — the join Raman's own
    transit paragraphs perform ("Jupiter in the 5th from the Moon, favourable, well supported
    at 7 bindus, yet Mars obstructs by vedha") composed strictly from the row's EXISTING
    fields (station, gochara_good, bav_bindus, kakshya, vedha_by, net_good). No new judgment:
    every clause restates a column the table above it already shows."""
    parts = [f"{g.planet} in the {_ordinal(g.house_from_moon)} from the Moon - "
             f"{'favourable' if g.gochara_good else 'adverse'} station"]
    if g.bav_bindus is not None:
        support = "well supported" if g.bav_bindus >= 4 else "weakly supported"
        parts.append(f"{support} at {g.bav_bindus} bindus")
    else:
        parts.append("no Ashtakavarga measure (node)")
    if g.kakshya_lord is not None:
        parts.append(f"in the Kakshya of {g.kakshya_lord} "
                     f"({'a bindu donated' if g.kakshya_favourable else 'no bindu donated'})")
    head = ", ".join(parts)
    if g.gochara_good and g.vedha_by:
        return (f"{head}, but obstructed by vedha from {', '.join(g.vedha_by)}: "
                f"the good is withheld.")
    if g.gochara_good:
        return f"{head}, no vedha: the indication stands."
    return (f"{head}; vedha applies to favourable stations only, "
            f"so the adverse reading stands as classical colour.")


def planet_rows(chart: RamanChart) -> tuple[tuple[str, PlanetPos], ...]:
    """Planets in canonical order for the positions table (a reading must be checkable)."""
    order = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    return tuple((n, chart.planets[n]) for n in order if n in chart.planets)


#: Two-letter sign abbreviations in Jagannatha Hora's own convention, so a printed longitude
#: ("23 Vi 59'17\"") can be checked against JHora directly (the project's pinning policy).
_SIGN_ABBR: Final[tuple[str, ...]] = ("Ar", "Ta", "Ge", "Cn", "Le", "Vi",
                                      "Li", "Sc", "Sg", "Cp", "Aq", "Pi")

#: Vimshottari nakshatra-lord cycle starting from Ashwini (nakshatra 1 -> Ketu) — derived from
#: the ONE canonical DASHA_LORDS table (app.core.ephemeris_engine) the Vimshottari engine
#: itself uses, so the column can never drift from the dasha math it makes auditable.
from app.core.ephemeris_engine import DASHA_LORDS as _DASHA_LORDS_TABLE  # noqa: E402
_NAK_LORD_SEQ: Final[tuple[str, ...]] = tuple(name for name, _ in _DASHA_LORDS_TABLE)


def nakshatra_lord(nakshatra: int) -> str:
    """Vimshottari lord of nakshatra 1-27 (Ashwini=Ketu ... Revati=Mercury). This is the very
    lord that seeds the birth Mahadasha when the Moon occupies that nakshatra, which is what
    makes the positions table's 'nak lord' column an audit trail for the Dasha section."""
    return _NAK_LORD_SEQ[(nakshatra - 1) % 9]


def format_longitude(lon: float) -> str:
    """Sidereal longitude in checkable sign-degree form, ASCII-safe: 173.988146 ->
    \"23 Vi 59'17\\\"\". Seconds rounded half-up; a 60s/60m carry rolls up (and across a sign
    boundary at 29 X 59'60\") so no cell ever prints 60."""
    lon %= 360.0
    sign_idx = int(lon // 30)
    d = lon % 30.0
    deg = int(d)
    minutes_f = (d - deg) * 60.0
    minutes = int(minutes_f)
    seconds = int(round((minutes_f - minutes) * 60.0))
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        deg += 1
    if deg == 30:
        deg = 0
        sign_idx = (sign_idx + 1) % 12
    return f"{deg} {_SIGN_ABBR[sign_idx]} {minutes:02d}'{seconds:02d}\""


def ascendant_position(chart: RamanChart) -> tuple[str, int, int, int, int]:
    """The Ascendant's (sign, nakshatra, pada, navamsa_sign, rasi-house=1) derived from
    `chart.asc_lon` with the SAME varga helpers every planet row uses — so the positions
    table can carry an Ascendant row and the whole cast is checkable against Jagannatha
    Hora. Returns (formatted longitude, nakshatra, pada, navamsa_sign, sign)."""
    from app.raman_saab.chart import varga
    nak, pada = varga.nakshatra_pada(chart.asc_lon)
    return (format_longitude(chart.asc_lon), nak, pada,
            varga.navamsa_sign(chart.asc_lon), chart.asc_sign)


def format_maraka_reasons(reasons: tuple[str, ...]) -> str:
    """Join a MarakaUnit's qualifying clauses for prose, merging plain lordship clauses:
    ('lord of the 2nd', 'lord of the 7th') -> 'lord of the 2nd and the 7th'; other clauses
    follow, '; '-separated. Empty reasons (pre-field units) -> ''."""
    lords = [x.removeprefix("lord of the ") for x in reasons if x.startswith("lord of the ")]
    others = [x for x in reasons if not x.startswith("lord of the ")]
    parts: list[str] = []
    if lords:
        parts.append("lord of the " + " and the ".join(lords))
    parts.extend(others)
    return "; ".join(parts)


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


def _divisional_verdict_summary(body: str) -> str:
    """The verdict fragment a matter-varga deep-read body itself prints (its ``>>> ... <<<``
    banner line(s), or the D-30 ``Health (H1) :`` row) — re-read for the section LABEL, so
    every collapsed summary / heading / JSON label leads with the verdict instead of the
    citation preamble (Wave-2, 2026-08-18: divisional verdict-first). Pure string re-read of
    a verdict the body already renders in full below; "" for the general vargas (D-27/40/45/
    60), which carry no matter verdict by design."""
    import re as _re
    frags = _re.findall(r">>>\s*(.*?)\s*<<<", body)
    if frags:
        return "; ".join(_re.sub(r"\s{2,}", ", ", f).strip() for f in frags)
    m = _re.search(r"Health \(H1\)\s*:\s*([A-Za-z-]+)", body)
    if m:
        return f"HEALTH (H1): {m.group(1)}"
    return ""


def _divisional_sections(chart: RamanChart) -> tuple[tuple[str, str], ...]:
    """Full varga deep-reads; a varga that cannot be cast on this chart is skipped.

    Item 12 (2026-08-04, content amendment — the divisional encyclopedia footer): each
    card gains its own STRENGTH line — the planets standing in OWN VARGA in this division
    (from `vargavisesha`, GBB-3 Art.28, the same saptavarga count the Parijatadi ladder
    uses) and the vargottama planets — the varga-level facts previously shown only in
    aggregate. Pure re-reads of already-computed values.

    Wave-2 (2026-08-18, verdict-first): the LABEL now appends the verdict banner the body
    already prints ("D-10 Career (Dasamsa) - CAREER: FAVOURABLE, ...") so the markdown
    heading, the standalone-HTML collapsed summary and the interactive page's label (all
    fed from this one tuple) are scannable — nothing removed, the full body is unchanged."""
    out: list[tuple[str, str]] = []
    try:
        from app.raman_saab.primitives.vargavisesha import vargavisesha
        vv = vargavisesha(chart)
    except Exception:  # noqa: BLE001 — Track-B sparse
        vv = ()
    for label, build, render in _DIVISIONAL:
        try:
            body = _clean_box(render(build(chart)))
        except Exception:  # noqa: BLE001 — same silent-skip contract as synthesis
            continue
        dtag = label.split(" ", 1)[0]                 # e.g. "D-9"
        own = [v.planet for v in vv
               if dtag.replace("-", "") in {ov.replace("-", "") for ov in v.own_vargas}]
        if own:
            body += (f"\n\nStrength in this varga (GBB-3 Art.28): "
                     f"{', '.join(own)} in own varga here.")
        verdict = _divisional_verdict_summary(body)
        out.append((f"{label} - {verdict}" if verdict else label, body))
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


def _dasha_transit_adverse(
    chart: RamanChart, timeline: DashaTimeline,
    outlook: dict[str, tuple[tr.GocharaSegment, ...]],
) -> tuple[ConfluenceWindow, ...]:
    """The ADVERSE mirror of `_dasha_transit_confluences` (Wave-2, 2026-08-18): every stretch
    where a bhukti's MD or AD lord is, at the same time, in one of its own classically-ADVERSE
    Gochara segments. The favourable builder was one-sided by construction (`if not
    seg.gochara_good: continue`); Raman's blending doctrine reads obstruction as well as
    reinforcement ("... blended with those of Gochara and Ashtakavarga, together with Vedha
    or obstructing forces", HPA-34:369-381), so both halves are stated. A NEW function — the
    favourable builder and its rows are byte-identical to before. Same coverage limit: only
    the four long-range movers (Jupiter/Saturn/Rahu/Ketu) contribute rows.

    `bav_bindus` is filled the same way `adverse_transit_windows` fills it (gochara_timeline
    leaves it None on adverse segments): the planet's own Bhinnashtakavarga bindus in the
    transited sign, Raman's mitigation proportion (ASP-13:416); None for the nodes only."""
    out: list[ConfluenceWindow] = []
    bav_of: dict[tuple[str, int], Optional[int]] = {}

    def _bav(planet: str, sign: int) -> Optional[int]:
        key = (planet, sign)
        if key not in bav_of:
            bav: Optional[int] = None
            if planet in ashtakavarga.PLANETS:
                try:
                    bav = ashtakavarga.bhinnashtakavarga(chart, planet)[sign]
                except Exception:  # noqa: BLE001 — sparse chart
                    bav = None
            bav_of[key] = bav
        return bav_of[key]

    for tp in timeline.periods:
        p = tp.period
        for role, lord in (("MD", p.maha), ("AD", p.antar)):
            if lord is None or lord not in outlook:
                continue
            for seg in outlook[lord]:
                if seg.gochara_good:
                    continue
                lo, hi = max(p.start_jd, seg.start_jd), min(p.end_jd, seg.end_jd)
                if lo < hi:
                    out.append(ConfluenceWindow(
                        planet=lord, role=role, period_start_jd=p.start_jd,
                        period_end_jd=p.end_jd, overlap_start_jd=lo, overlap_end_jd=hi,
                        sign=seg.sign, bav_bindus=_bav(lord, seg.sign),
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
    #: Wave-2 (2026-08-18, append-only): the Mahadasha lord an AD row runs UNDER —
    #: Raman's bhukti doctrine is MD-lord-relative (the locked four-tier scheme), so an
    #: AD window without its MD context under-states the read. None on MD rows (the row's
    #: own `planet` IS the MD lord there). Always computed from the same timeline period
    #: the row was built from (`p.maha`) — no new judgment.
    maha: Optional[str] = None


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
                                      vd.lord_quality(chart, p.antar), maha=p.maha))
    out.sort(key=lambda w: w.period_start_jd)
    return tuple(out)


def yoga_next_ripening(r: "DetailedReport") -> tuple[tuple[str, str], ...]:
    """Wave-2 C (2026-08-18, add-only): one (yoga name, ripening sentence) per fired yoga
    that has timing rows — is a constituent-lord window running NOW, and if not, which is
    the next one? A pure re-read of the SAME `yoga_timing` rows the full table renders
    (the table is retained per REPORT COMPLETENESS); shared by both renderers so the two
    surfaces cannot drift. Timed indications in the classical idiom, never a decree."""
    from app.raman_saab.render import _jd_to_date
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for y in r.yogas:
        if y.id in seen:
            continue
        seen.add(y.id)
        rows = [t for t in r.yoga_timing if t.yoga_id == y.id]
        if not rows:
            continue
        live = next((t for t in rows
                     if t.period_start_jd <= r.ref_jd < t.period_end_jd), None)
        if live is not None:
            ctx = (f" under {live.maha} MD" if live.role == "AD" and live.maha else "")
            out.append((y.name,
                        f"ripe NOW - {live.planet} {live.role}{ctx} runs until "
                        f"{_jd_to_date(live.period_end_jd)} (delivery: "
                        f"{live.quality.tag})"))
            continue
        future = next((t for t in rows if t.period_start_jd >= r.ref_jd), None)
        if future is not None:
            ctx = (f" under {future.maha} MD" if future.role == "AD" and future.maha
                   else "")
            out.append((y.name,
                        f"next ripens in {future.planet} {future.role}{ctx}, "
                        f"{_jd_to_date(future.period_start_jd)} to "
                        f"{_jd_to_date(future.period_end_jd)} (delivery: "
                        f"{future.quality.tag})"))
        else:
            out.append((y.name,
                        "no further constituent-lord window inside the shown timeline "
                        "(its windows above lie in the past)"))
    return tuple(out)


def yoga_timing_grouped(r: "DetailedReport") -> tuple[tuple[str, tuple], ...]:
    """Wave-3 (2026-08-18): the SAME `yoga_timing` rows, grouped by yoga instead of
    interleaved by date — the repetition-suppression fix for a table where one Venus
    Mahadasha printed three verbatim-identical rows under three different yogas.
    Grouping only: every row appears exactly once, in the chronological order it already
    had, and no column is dropped (the yoga name becomes each group's own label). Group
    order follows each yoga's first appearance in the flat table."""
    order: list[str] = []
    groups: dict[str, list] = {}
    for t in r.yoga_timing:
        if t.yoga_name not in groups:
            order.append(t.yoga_name)
            groups[t.yoga_name] = []
        groups[t.yoga_name].append(t)
    return tuple((name, tuple(groups[name])) for name in order)


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
    # append-only 2026-08-17 (report critique): the score's addends spelled out, e.g.
    # "Saturn 3 + Venus 3" for score 6 — the same MarakaSet.weight() values death_window
    # summed (primary=3/secondary=2/tertiary=1). "" when the recomputed weights do not
    # reproduce `score` (never expected; a guard, not a behaviour).
    score_parts: str = ""


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
    # The score's addends, from the SAME MarakaSet death_window itself summed — pure
    # re-read (maraka_set is deterministic on the chart), shown so "6" is checkable as
    # "Saturn 3 + Venus 3". Guarded to "" if the recomputation ever disagreed.
    ms = vd.maraka_set(chart)
    out: list[MarakaSaturnConfluence] = []
    for dw in dws:
        w_md, w_ad = ms.weight(dw.maha), ms.weight(dw.antar)
        parts = (f"{dw.maha} {w_md} + {dw.antar} {w_ad}"
                 if w_md + w_ad == dw.score else "")
        for seg in sat_segments:
            if seg.sign not in trines:
                continue
            lo, hi = max(dw.start_jd, seg.start_jd), min(dw.end_jd, seg.end_jd)
            if lo < hi:
                out.append(MarakaSaturnConfluence(
                    maha=dw.maha, antar=dw.antar, window_start_jd=dw.start_jd,
                    window_end_jd=dw.end_jd, overlap_start_jd=lo, overlap_end_jd=hi,
                    sign=seg.sign, score=dw.score, score_parts=parts))
    out.sort(key=lambda c: c.overlap_start_jd)
    return tuple(out)


# ---------------------------------------------------------------------------
# Wave-1 timing additions (2026-08-17, REPORT COMPLETENESS): the pratyantar
# drill-down for the current bhukti, the dated Sade-Sati phase spans, and the
# dated Chara dasha sequence. All three are pure re-reads / plain calendar
# arithmetic over already-encoded primitives — no verdict is touched.
# ---------------------------------------------------------------------------

#: Saturn's three Sade-Sati stations from the natal Moon (the same three houses
#: `transits.sade_sati` names for its point-in-time phase word).
_SADE_SATI_PHASE: Final[dict[int, str]] = {
    12: "rising (12th from Moon)", 1: "peak (over the Moon)", 2: "setting (2nd from Moon)"}


@dataclass(frozen=True)
class SadeSatiPhase:
    """One dated span of transiting Saturn in the 12th/1st/2nd sign from the natal Moon.
    DATES ONLY: no Sade-Sati x Moon result doctrine is on record in the encoded corpus (the
    same absence the report's method notes already disclose), so this row carries plain
    gochara arithmetic — Saturn's transiting sign against the natal Moon sign — and no
    intensity or result judgment. Boundaries inherit `gochara_timeline`'s ~week sampling
    resolution."""
    phase: str            # rising / peak / setting (the 12th / 1st / 2nd from the Moon)
    house_from_moon: int  # 12, 1 or 2
    sign: int             # the transited sign (1..12)
    start_jd: float
    end_jd: float
    current: bool         # the reference date falls inside this span


def _sade_sati_phases(chart: RamanChart, ref_jd: float,
                      ayanamsa: str) -> tuple[SadeSatiPhase, ...]:
    """The dated Sade-Sati episode nearest the reference date: Saturn's consecutive transits
    of the 12th/1st/2nd from the natal Moon, segmented by the SAME `tr.gochara_timeline`
    machinery the Gochara outlook uses (sign ingresses to ~week resolution). The scan runs 16
    years back / 31 years forward of `ref_jd` — wide enough to always hold either the episode
    containing `ref_jd` or the next complete one (Saturn's cycle is ~29.5 years, an episode
    ~7.5). Prefers the running episode; else the next upcoming; else the most recent past.
    A retrograde dip out of the three-house band splits the episode honestly (each re-entry
    is its own dated row). Empty on a Track-B chart (no jd_ut)."""
    if chart.planets.get("Moon") is None or getattr(chart, "jd_ut", None) is None:
        return ()
    segs = tr.gochara_timeline(chart, ref_jd, 16.0, 31.0, ayanamsa=ayanamsa,
                               planets=("Saturn",)).get("Saturn", ())
    episodes: list[list[tr.GocharaSegment]] = []
    run: list[tr.GocharaSegment] = []
    for seg in segs:
        if seg.house_from_moon in _SADE_SATI_PHASE:
            run.append(seg)
        elif run:
            episodes.append(run)
            run = []
    if run:
        episodes.append(run)
    if not episodes:
        return ()
    chosen = next((ep for ep in episodes if ep[0].start_jd <= ref_jd < ep[-1].end_jd), None)
    if chosen is None:
        chosen = next((ep for ep in episodes if ep[0].start_jd >= ref_jd), episodes[-1])
    return tuple(SadeSatiPhase(
        phase=_SADE_SATI_PHASE[seg.house_from_moon], house_from_moon=seg.house_from_moon,
        sign=seg.sign, start_jd=seg.start_jd, end_jd=seg.end_jd,
        current=seg.start_jd <= ref_jd < seg.end_jd) for seg in chosen)


@dataclass(frozen=True)
class CharaDashaSpan:
    """One dated Chara Dasha period — `chara_dasha_dated`'s plain JD arithmetic (period years
    x 365.2425 days from birth, the KN Rao convention already encoded in
    `primitives.chara_dasha`) wrapped with a current-period flag. No result judgment attaches:
    matters are read from Vimshottari; this dates the parallel Jaimini script the Chart
    signature chip and the Soul reading already name undated."""
    sign: int
    years: int
    start_jd: float
    end_jd: float
    current: bool


def _chara_sequence(chart: RamanChart, ref_jd: float) -> tuple[CharaDashaSpan, ...]:
    """The dated Chara Dasha sequence from birth through the cycle containing `ref_jd` —
    exactly one row carries `current=True` when the reference date falls inside the dated
    range. Empty on a Track-B chart."""
    from app.raman_saab.primitives import chara_dasha as cd
    return tuple(CharaDashaSpan(sign=s, years=y, start_jd=lo, end_jd=hi,
                                current=lo <= ref_jd < hi)
                 for s, y, lo, hi in cd.chara_dasha_dated(chart, through_jd=ref_jd))


def _pratyantar_rows(chart: RamanChart, ref_jd: float) -> tuple[vd.DashaPeriod, ...]:
    """The 9 Pratyantardashas of the bhukti running on `ref_jd` — `vimshottari.pratyantars`
    surfaced for the report. Raman names all three levels as carriers of a house's results
    ("as lords of the Dasas (main-periods), as lords of Bhuktis (Sub-periods) or as lords of
    the Antaras", HTJAH-II:668-702) — the drill-down is shown for the CURRENT bhukti only,
    since nine rows under every bhukti of a 30-year window would flood the narrative. Empty
    when no bhukti-level period resolves (Track-B / outside the unrolled timeline)."""
    if getattr(chart, "jd_ut", None) is None:
        return ()
    try:
        bh = vd.dasha_on(chart, ref_jd)
    except Exception:  # noqa: BLE001 — sparse chart
        return ()
    if bh is None or bh.antar is None:
        return ()
    return tuple(vd.pratyantars(bh))


def adverse_transit_windows(
    r: "DetailedReport",
) -> tuple[tuple[str, tr.GocharaSegment, Optional[int]], ...]:
    """The classically-ADVERSE Gochara outlook windows — the exact mirror of the favourable
    filter both renderers already apply (same >= 25-day noise floor, chronological), which
    `gochara_timeline` computes but no renderer showed. The third element is the planet's own
    Bhinnashtakavarga bindus in the transited sign, read by Raman's proportion law as the
    extent to which the evil is neutralised ("neutralises the evil to the extent of 75%" at
    6 of 8 bindus, ASP-13:416); None for the nodes (no classical Ashtakavarga — the 7-graha
    lock). Vedha (obstruction) is defined for favourable transits only, so no interference
    fraction exists for these rows — rendered as not-computed, never as zero."""
    rows: list[tuple[str, tr.GocharaSegment, Optional[int]]] = []
    for segs in r.gochara_outlook.values():
        for seg in segs:
            if seg.gochara_good or (seg.end_jd - seg.start_jd) < 25:
                continue
            bav: Optional[int] = None
            if seg.planet in ashtakavarga.PLANETS:
                try:
                    bav = ashtakavarga.bhinnashtakavarga(r.chart, seg.planet)[seg.sign]
                except Exception:  # noqa: BLE001 — sparse chart
                    bav = None
            rows.append((seg.planet, seg, bav))
    rows.sort(key=lambda t: t[1].start_jd)
    return tuple(rows)


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
class BavMatrixRow:
    """One planet's Bhinnashtakavarga row — bindus per sign, straight from
    `ashtakavarga.bhinnashtakavarga` (the canonical Parashari/BPHS benefic-places tables,
    checksum-guarded: each planet's BAV total is fixed and the seven rows always sum to SAV's
    337). `seat_sign`/`seat_bindus` are the planet's OWN natal sign and its bindus there — the
    exact cell the AV dasha-seat outlook and the gochara table's 'AV bindus' column read.
    Pure re-read of the primitive; no new judgment (AV completeness, 2026-08-17)."""
    planet: str
    bindus: tuple[int, ...]        # index 0 = Aries .. 11 = Pisces
    total: int
    seat_sign: Optional[int]       # planet's natal sign (1..12); None on sparse charts
    seat_bindus: Optional[int]


@dataclass(frozen=True)
class BavReducedRow:
    """One planet's HPA-26 reduced Ashtakavarga: after Trikona Sodhana alone, then after both
    reductions in Raman's stated order — "After the Thrikona reduction, the Ekadhipathya
    reduction must be applied" (HPA-26:466-467). Pure re-read of `ashtakavarga_reduction`
    (its regression fixture is Raman's own worked Sun table, HPA-26:432-462)."""
    planet: str
    trikona: tuple[int, ...]       # after Trikona Sodhana (HPA-26:403-421)
    reduced: tuple[int, ...]       # after BOTH reductions (Ekadhipathya: HPA-26:464-497)


@dataclass(frozen=True)
class SodyaPindaRow:
    """One planet's Rasi/Graha Gunakara figures and their sum — Raman's Sodya Pinda by his own
    naming, "The sum of the Rasi figures (Rasi Pinda) and Planetary figures (Graha Pinda) will
    be the Sodya Pinda for each planet" (ASP-14:196-198). Pure re-read of
    `ashtakavarga_pinda` (HPA-26:1130-1404)."""
    planet: str
    rasi: int
    graha: int
    total: int


def _bav_matrix_rows(chart: RamanChart) -> tuple[BavMatrixRow, ...]:
    """The full 7x12 Bhinnashtakavarga matrix, one row per graha — surfacing the layer the
    gochara 'AV bindus'/Kakshya columns and the AV dasha-seat outlook already read from."""
    out: list[BavMatrixRow] = []
    for planet in ashtakavarga.PLANETS:
        bav = ashtakavarga.bhinnashtakavarga(chart, planet)
        pos = chart.planets.get(planet)
        seat = pos.sign if pos is not None else None
        bindus = tuple(bav[s] for s in range(1, 13))
        out.append(BavMatrixRow(
            planet=planet, bindus=bindus, total=sum(bindus), seat_sign=seat,
            seat_bindus=bav[seat] if seat is not None else None))
    return tuple(out)


def _bav_reduced_rows(chart: RamanChart) -> tuple[BavReducedRow, ...]:
    """HPA-26's two ordered reductions per graha — a pure re-read of
    `ashtakavarga_reduction.trikona_shodhana` / `ekadhipatya_shodhana`; no math re-derived."""
    from app.raman_saab.primitives.ashtakavarga_reduction import (ekadhipatya_shodhana,
                                                                  trikona_shodhana)
    out: list[BavReducedRow] = []
    for planet in ashtakavarga.PLANETS:
        tri = trikona_shodhana(ashtakavarga.bhinnashtakavarga(chart, planet))
        red = ekadhipatya_shodhana(tri, chart)
        out.append(BavReducedRow(
            planet=planet,
            trikona=tuple(tri[s] for s in range(1, 13)),
            reduced=tuple(red[s] for s in range(1, 13))))
    return tuple(out)


def _sodya_pinda_rows(chart: RamanChart) -> tuple[SodyaPindaRow, ...]:
    """Sodya Pinda per graha — a pure re-read of `ashtakavarga_pinda.ashtakavarga_pinda`."""
    from app.raman_saab.primitives.ashtakavarga_pinda import ashtakavarga_pinda
    out: list[SodyaPindaRow] = []
    for planet in ashtakavarga.PLANETS:
        pb = ashtakavarga_pinda(chart, planet)
        out.append(SodyaPindaRow(planet=planet, rasi=pb.rasi, graha=pb.graha, total=pb.total))
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
    rect_confidence: object = None                   # birth-time sensitivity (v31)
    aptitude: object = None                          # aptitude/intelligence/work-style (v33)
    themes: object = None                            # integrated interpretation / theme synthesis (v34)
    # AV completeness (2026-08-17, REPORT_CRITIQUE yoga_strength appendix 4) — the whole
    # Ashtakavarga layer the engine always computed, now shown. Append-only.
    bav_matrix: tuple = ()                           # BavMatrixRow per graha (7x12 BAV + seats)
    bav_reduced: tuple = ()                          # BavReducedRow per graha (HPA-26 Sodhana)
    sodya_pinda: tuple = ()                          # SodyaPindaRow per graha (ASP-14 naming)
    # Wave-1 timing additions (2026-08-17, REPORT_CRITIQUE timing appendix) — append-only.
    pratyantar_now: tuple = ()                       # current bhukti's 9 pratyantardashas, dated
    sade_sati_phases: tuple = ()                     # dated Saturn 12th/1st/2nd-from-Moon spans
    chara_sequence: tuple = ()                       # dated Chara dasha spans, current flagged
    # Wave-2 timing/divisional/soul additions (2026-08-18, REPORT_CRITIQUE timing appendix)
    # — append-only.
    dasha_transit_adverse: tuple[ConfluenceWindow, ...] = ()  # MD/AD lord x its own ADVERSE transit


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
    #: Wave-2 (2026-08-17, append-only): the NEXT Mahadasha boundary after the reference
    #: date, with the incoming lord's natal-fixed Ishta/Kashta lean (GBB-10:134) — the
    #: forward half of the turning-points scan, indication idiom only. "" when the window
    #: holds no future boundary.
    forward_horizon: str = ""


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


#: Harmonised longevity-band labels (2026-08-18 report-critique item 5b): the
#: combination lines say "Purnayu (75-120y)" while the numeric cross-check said
#: bare "purna" — one reading, two words. Every surface now shows the dominant
#: Sanskrit form with the class word once: "Purnayu (purna band)".
_LONGEVITY_BAND_LABEL: Final[dict[str, str]] = {
    "alpa": "Alpayu (alpa band)",
    "madhya": "Madhyayu (madhya band)",
    "purna": "Purnayu (purna band)",
}


def longevity_band_label(longevity_class: str) -> str:
    """The harmonised display label for an ayurdaya class ('purna' -> 'Purnayu
    (purna band)'); unknown classes pass through unchanged."""
    return _LONGEVITY_BAND_LABEL.get(longevity_class, longevity_class)


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
        # relabeled 2026-08-18 (report-critique item 6): these two karaka rows come
        # from the SINGLE-CHART core (H1/H6/H8 + Moon/Mercury karakas), which the
        # module itself insists is NOT the D-30 — the old "D-30 health core" label
        # contradicted its own provenance doctrine.
        provenance="single-chart health core (H1/H6/H8 + karakas)"))
    rows.append(HealthIndicatorRow(
        area="Mercury — nervous-system karaka",
        verdict=str(core.mercury_dignity),
        note=("afflicted by " + ", ".join(core.mercury_afflictions)
              if core.mercury_afflictions else "no natural-malefic affliction"),
        # relabeled 2026-08-18 (report-critique item 6): these two karaka rows come
        # from the SINGLE-CHART core (H1/H6/H8 + Moon/Mercury karakas), which the
        # module itself insists is NOT the D-30 — the old "D-30 health core" label
        # contradicted its own provenance doctrine.
        provenance="single-chart health core (H1/H6/H8 + karakas)"))
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
        longevity_band=f"{longevity_band_label(r.longevity_class)} — a band, not a date",
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
    # ── the ruler's OWN condition block (append-only 2026-08-18, report-critique: the
    # chapter is titled after the Lagna lord yet described only the strongest planet).
    # All defaults so every existing construction — incl. _EMPTY_RULER — is unchanged. ──
    takeaway: str = ""                                # one-line chapter lead (composed)
    ll_dignity: Optional[str] = None                  # Lagna lord's dignity word
    ll_avastha: Optional[str] = None                  # Lagna lord's Deeptadi state
    ll_rupas: Optional[float] = None                  # Lagna lord's total Shadbala (rupas)
    ll_required: Optional[float] = None               # its GBB-8:303 minimum
    ll_powerful: Optional[bool] = None                # meets that minimum?
    ll_only_failing: bool = False                     # the ONLY planet below its minimum?
    ll_aspects_received: tuple[str, ...] = ()         # planets casting drishti on it
    ll_dispositor: Optional[str] = None               # lord of the sign it occupies
    ll_dispositor_house: Optional[int] = None         # ... and that dispositor's house
    ll_functional_nature: Optional[str] = None        # of the LAGNA LORD, for this Lagna
    foundation_line: str = ""                         # sound/unsound verdict (HTJAH-I:3880-3882)
    chandra_lagna_lord: Optional[str] = None          # third classical candidate (Moon-frame)
    chandra_ll_condition: Optional[str] = None        # its condition, one clause


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

    # ── the ruler's OWN condition block (append-only 2026-08-18, report-critique:
    # the chapter is titled after the Lagna lord, so the Lagna lord gets the same
    # full condition read as the strongest planet). Pure re-reads of the same
    # primitives every other section consumes; nothing is judged here. ────────────
    from app.raman_saab.doctrine import drishti as _drishti
    from app.raman_saab.primitives.deeptadi import RESULTS as _DEEPTADI_RESULTS
    from app.raman_saab.primitives.deeptadi import state as _deeptadi_state
    from app.raman_saab.primitives.dignity import dignity as _dignity_of
    from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED as _MIN_REQ
    from app.raman_saab.primitives.shadbala.total import is_powerful as _is_powerful
    ll_dignity: Optional[str] = None
    ll_avastha: Optional[str] = None
    ll_rupas: Optional[float] = None
    ll_required: Optional[float] = None
    ll_powerful: Optional[bool] = None
    ll_only_failing = False
    ll_aspects: tuple[str, ...] = ()
    ll_dispositor: Optional[str] = None
    ll_dispositor_house: Optional[int] = None
    if ll_pos is not None:
        try:
            ll_dignity = _dignity_of(lagna_lord, chart)
            ll_avastha = _deeptadi_state(lagna_lord, chart)
        except Exception:  # noqa: BLE001 — Track-B sparse chart
            pass
        ll_aspects = tuple(_drishti.aspecting_planets(lagna_lord, chart))
        ll_dispositor = SIGN_LORDS[ll_pos.sign]
        _dp = chart.planets.get(ll_dispositor)
        ll_dispositor_house = _dp.rasi_house if _dp is not None else None
        if ll_pos.shadbala_rupas is not None:
            ll_rupas = ll_pos.shadbala_rupas.total / 60.0
            ll_required = _MIN_REQ.get(lagna_lord)
            ll_powerful = _is_powerful(lagna_lord, ll_rupas)
            _failing = [n for n, v in sb if not _is_powerful(n, v)]
            ll_only_failing = _failing == [lagna_lord]
    ll_fn = dict(r.overview.functional_natures).get(lagna_lord)

    # the sound/unsound-foundation verdict line — the SAME HTJAH-I:3880-3882 test the
    # coincide branch already quotes, surfaced on BOTH branches (descriptive idiom only)
    foundation = ""
    if ll_powerful is True:
        foundation = (f"{lagna_lord}, the Lagnadhipati, meets Raman's required minimum"
                      + (" and is itself the strongest planet in the horoscope"
                         if coincide else "")
                      + " — the reading Raman marks with \"the foundation is quite "
                        "sound\" (HTJAH-I:3880-3882)")
    elif ll_powerful is False and ll_rupas is not None and ll_required is not None:
        foundation = (f"{lagna_lord}, the Lagnadhipati, falls below its required minimum "
                      f"({ll_rupas:.2f} of {ll_required:.1f} rupas"
                      + (" — the only planet in this chart that does"
                         if ll_only_failing else "")
                      + "), so this chart reads short of the \"foundation is quite "
                        "sound\" standard of that test (HTJAH-I:3880-3882)"
                      + (f"; the first impression leans instead on {strongest}, the "
                         f"strongest planet"
                         if strongest is not None and strongest != lagna_lord else ""))

    # the third classical candidate: when the signature reads the MOON as the stronger
    # frame (HTJAH-I:645-646), disclose the Chandra-lagna lord and its condition
    ch_lord: Optional[str] = None
    ch_cond: Optional[str] = None
    _moon_p = chart.planets.get("Moon")
    if r.overview.stronger_frame == "moon" and _moon_p is not None:
        ch_lord = SIGN_LORDS[_moon_p.sign]
        _cp = chart.planets.get(ch_lord)
        if _cp is not None:
            _parts = [f"in house {_cp.rasi_house}"]
            try:
                _parts.append(f"{_dignity_of(ch_lord, chart)} sign")
                _parts.append(f"{_deeptadi_state(ch_lord, chart)} avastha")
            except Exception:  # noqa: BLE001 — Track-B sparse chart
                pass
            if _cp.shadbala_rupas is not None:
                _parts.append(f"{_cp.shadbala_rupas.total / 60.0:.2f} rupas")
            _cfn = dict(r.overview.functional_natures).get(ch_lord)
            if _cfn:
                _parts.append(f"functional {_cfn} for this Lagna")
            ch_cond = ", ".join(_parts)

    # the one-line chapter lead — composed only from the conditions computed above
    takeaway = ""
    if ll_pos is not None:
        _strain: list[str] = []
        if ll_dignity == "enemy":
            _strain.append("in an enemy sign")
        elif ll_dignity == "debil":
            _strain.append("in debilitation")
        if ll_avastha is not None and _DEEPTADI_RESULTS.get(ll_avastha, (0, ""))[0] < 0:
            _strain.append(f"{ll_avastha} avastha")
        if ll_powerful is False:
            _strain.append("under its Shadbala minimum")
        _head = f"{lagna_lord} rules this nativity from house {ll_pos.rasi_house}"
        if coincide and ll_powerful:
            takeaway = (_head + " and is itself the strongest planet by Shadbala — "
                        "the chart rests on its own ruler.")
        elif _strain:
            takeaway = _head + ", but runs " + _human_list(_strain)
            if strongest is not None and strongest != lagna_lord:
                takeaway += (f"; {strongest}, the strongest planet by Shadbala, "
                             f"carries the chart")
            takeaway += "."
        else:
            takeaway = _head + " in serviceable condition"
            if strongest is not None and strongest != lagna_lord:
                takeaway += f"; {strongest} is the strongest planet by Shadbala"
            takeaway += "."

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
        takeaway=takeaway, ll_dignity=ll_dignity, ll_avastha=ll_avastha,
        ll_rupas=ll_rupas, ll_required=ll_required, ll_powerful=ll_powerful,
        ll_only_failing=ll_only_failing, ll_aspects_received=ll_aspects,
        ll_dispositor=ll_dispositor, ll_dispositor_house=ll_dispositor_house,
        ll_functional_nature=ll_fn, foundation_line=foundation,
        chandra_lagna_lord=ch_lord, chandra_ll_condition=ch_cond,
    )


#: Weekday -> its planetary lord (the vara lords) — used only to NOTE when the day lord is
#: also the chart's strongest planet; the vara itself comes from the synthesis panchanga.
_VARA_LORD: Final[dict[str, str]] = {
    "Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars", "Wednesday": "Mercury",
    "Thursday": "Jupiter", "Friday": "Venus", "Saturday": "Saturn",
}


def _ymd_from_days(days: float) -> tuple[int, int, int]:
    """Days -> (years, months, days) using the locked DAYS_PER_VEDIC_YEAR (365.2425) and its
    twelfth as the month — plain JD arithmetic, the same year-length every dasha computation
    in this codebase uses (CLAUDE.md lock); never `datetime.timedelta`."""
    y = int(days // _DAYS_PER_VEDIC_YEAR)
    rem = days - y * _DAYS_PER_VEDIC_YEAR
    month_len = _DAYS_PER_VEDIC_YEAR / 12.0
    m = int(rem // month_len)
    d = int(rem - m * month_len)
    return y, m, d


def signature_first_glance(r: DetailedReport) -> tuple[tuple[str, str], ...]:
    """Raman's first-glance rows for the Chart signature (append-only 2026-08-18,
    report-critique): balance of dasha at birth, the Lagna/Moon degrees, the Moon's paksha
    read against its own Shadbala, the Sun/Moon strong-weak flags, the Lagna lord's
    disposition in one clause, and the day-lord observation when the weekday lord is also
    the strongest planet. Every row is a COMPUTED re-read of values the report already
    holds (or plain JD arithmetic over the same Vimshottari timeline the Dasha section
    renders); nothing is judged here and no verdict is touched."""
    from app.raman_saab.primitives import vimshottari as _vd
    from app.raman_saab.primitives.deeptadi import state as _deeptadi_state
    from app.raman_saab.primitives.dignity import dignity as _dignity_of
    from app.raman_saab.primitives.shadbala.total import is_powerful as _is_powerful
    chart = r.chart
    rows: list[tuple[str, str]] = []
    # balance of dasha at birth — the birth MD's remainder from the SAME timeline math
    try:
        _first = _vd.mahadasha_timeline(chart)[0]
        _y, _m, _d = _ymd_from_days(_first.end_jd - chart.jd_ut)
        rows.append(("Balance of dasha at birth",
                     f"{_first.maha} {_y}y {_m}m {_d}d"))
    except Exception:  # noqa: BLE001 — Track-B sparse chart (no jd_ut)
        pass
    # exact degrees — the same sign-degree form the Planetary positions table prints
    if getattr(chart, "asc_lon", None) is not None:
        rows.append(("Lagna degree", format_longitude(chart.asc_lon)))
    moon = chart.planets.get("Moon")
    sun = chart.planets.get("Sun")
    if moon is not None:
        rows.append(("Moon degree", format_longitude(moon.lon)))
    # the Moon's paksha, read against its own Shadbala (waxing/waning is plain arithmetic
    # on the Sun-Moon elongation; the strength flag is the report's own Shadbala)
    if moon is not None and sun is not None:
        waxing = (moon.lon - sun.lon) % 360.0 < 180.0
        paksha = ("waxing (Sukla paksha)" if waxing else "waning (Krishna paksha)")
        if moon.shadbala_rupas is not None:
            mr = moon.shadbala_rupas.total / 60.0
            strong = _is_powerful("Moon", mr)
            joiner = ("and" if waxing == strong else "yet")
            word = "Shadbala-strong" if strong else "Shadbala-weak"
            rows.append(("Moon at a glance",
                         f"{paksha} {joiner} {word} ({mr:.2f} rupas)"))
        else:
            rows.append(("Moon at a glance", paksha))
    # Sun & Moon strength flags — by this report's OWN Shadbala thresholds (GBB-8:303)
    _lum_bits: list[str] = []
    for _lum in ("Sun", "Moon"):
        _lp = chart.planets.get(_lum)
        if _lp is not None and _lp.shadbala_rupas is not None:
            _lr = _lp.shadbala_rupas.total / 60.0
            _lum_bits.append(
                f"{_lum} {'strong' if _is_powerful(_lum, _lr) else 'weak'} ({_lr:.2f} rupas)")
    if _lum_bits:
        rows.append(("Luminaries", "; ".join(_lum_bits)
                     + " — by this report's own Shadbala (GBB-8:303)"))
    # the Lagna lord's disposition, one clause
    _ll = SIGN_LORDS[chart.asc_sign]
    _llp = chart.planets.get(_ll)
    if _llp is not None:
        _bits = [f"in H{_llp.rasi_house}"]
        try:
            _bits.append(f"{_dignity_of(_ll, chart)} sign")
            _bits.append(f"{_deeptadi_state(_ll, chart)} avastha")
        except Exception:  # noqa: BLE001 — Track-B sparse chart
            pass
        rows.append(("Lagna lord at a glance", f"{_ll} " + ", ".join(_bits)))
    # day-lord observation — only when the weekday lord IS the strongest planet
    _pan = getattr(r.synthesis, "panchanga", None)
    if _pan and r.ruler.strongest:
        _vara = _pan.split("|", 1)[0].replace("Vara", "").strip()
        if _VARA_LORD.get(_vara) == r.ruler.strongest:
            rows.append(("Day lord", f"born on {_vara}, the {r.ruler.strongest}'s day — "
                                     f"the {r.ruler.strongest} is also this chart's "
                                     f"strongest planet by Shadbala"))
    return tuple(rows)


def deeptadi_table(r: DetailedReport) -> tuple[tuple[str, str, str, str], ...]:
    """Per-planet Deeptadi rows for the avastha section (append-only 2026-08-18,
    report-critique: from trivia to testimony): (graha, state — with every SECONDARY
    state disclosed via `deeptadi.states_all`, dominant first —, Raman's stated result
    for the dominant state (HPA Ch.7:46-83, already encoded in `deeptadi.RESULTS`),
    and the houses the planet rules/occupies so the state reads as judgment-relevant
    testimony (\"the Lagna lord dejected\") instead of a bare label. Pure re-read;
    `deeptadi.state()` itself is untouched and no verdict is touched."""
    from app.raman_saab.primitives.deeptadi import RESULTS as _RES
    from app.raman_saab.primitives.deeptadi import states_all as _states_all
    chart = r.chart
    lagna_lord = SIGN_LORDS[chart.asc_sign]
    out: list[tuple[str, str, str, str]] = []
    for name, p in planet_rows(chart):
        states = _states_all(name, chart)
        dom, rest = states[0], states[1:]
        if name in ("Rahu", "Ketu") and dom == "Sakta":
            state_cell = "Sakta (definitional — the nodes are always retrograde)"
        elif rest:
            alsos = ", ".join(
                f"{_RES[s][1].split(' ->')[0]} -> {s}" for s in rest)
            state_cell = (f"{dom} (also {alsos}; the dignity-first order reads "
                          f"{dom} as dominant)")
        else:
            state_cell = dom
        ruled = [h for h in range(1, 13)
                 if SIGN_LORDS[((chart.asc_sign - 1 + h - 1) % 12) + 1] == name]
        if name in ("Rahu", "Ketu"):
            role = f"rules nothing (chayagraha); occupies H{p.rasi_house}"
        else:
            role = ("rules " + ", ".join(f"H{h}" for h in ruled)
                    if ruled else "rules nothing here") + f"; occupies H{p.rasi_house}"
        if name == lagna_lord:
            role += " — the Lagna lord" + (
                " dejected" if dom == "Deena"
                else " in an afflicted state" if _RES[dom][0] < 0 else "")
        out.append((name, state_cell, _RES[dom][1], role))
    return tuple(out)


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
    #: Wave-2 E (2026-08-18, append-only): the witness CLASS — "core" for the axes
    #: HTJAH-I:983-991 itself names as judgment's summing-up (the house's lord, its
    #: karaka, plus the navamsa the verdict path consults), "overlay" for the report's
    #: own cross-checks (SAV band, Bhava-Bala rank, matter-vargas, majority tenor,
    #: yoga bearings). A TAG on existing rows — Raman's unequal weighing made visible
    #: without inventing weights; no lean or count used for status words changes.
    klass: str = "overlay"


#: The witness names tagged "core" (Wave-2 E): the axes HTJAH-I:983-991 itself names —
#: the house's lord and karaka — plus the navamsa the verdict path consults directly.
_CORE_WITNESS_NAMES: Final[frozenset[str]] = frozenset(
    {"lord (lagna frame)", "karaka", "navamsa"})


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
    #: Wave-2 E (2026-08-18, append-only): the same tally restricted to the CORE
    #: witnesses (Testimony.klass == "core" — lord/karaka/navamsa, HTJAH-I:983-991).
    #: A second count PAIR shown beside the flat counts; the flat counts and the
    #: preponderance/status words derived from them are untouched.
    core_favourable: int = 0
    core_adverse: int = 0


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
    # Wave-2 E (2026-08-18): the append-only detail companion also tags WHICH factor
    # matched per house — "direct" (own/occupy, Raman-demonstrated) vs "aspect"
    # (the admitted extension) — so a yoga row can disclose its link; the house SET
    # and every lean stay exactly as before.
    from app.raman_saab.doctrine.synthesis_rules import (yoga_house_bearings,
                                                         yoga_house_bearings_detail)
    bearings = [(y, yoga_house_bearings(r.chart, y)) for y in r.yogas]
    bearing_tags = {y.id: (yoga_house_bearings_detail(r.chart, y) or {})
                    for y in r.yogas}

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
                # Wave-2 E: disclose WHICH bearing factor matched (direct vs
                # aspect-derived) — value enrichment only; the lean is unchanged.
                _btag = bearing_tags.get(y.id, {}).get(h)
                _bval = y.kind + (" [direct - own/occupy]" if _btag == "direct"
                                  else " [aspect-derived - admitted extension]"
                                  if _btag == "aspect" else "")
                tst.append(Testimony(f"yoga: {y.name}", _bval, _yoga_record_lean(y)))

        # Wave-2 E: tag the CORE witnesses (HTJAH-I:983-991's own axes — the house's
        # lord, karaka and the navamsa the verdict path consults); everything else is
        # an overlay cross-check. A retag of rows already built — no lean changes.
        tst = [(_dc_replace(t, klass="core") if t.name in _CORE_WITNESS_NAMES else t)
               for t in tst]

        fav = sum(1 for t in tst if t.lean == "favourable-leaning")
        adv = sum(1 for t in tst if t.lean == "adverse-leaning")
        neu = sum(1 for t in tst if t.lean == "neutral")
        ab = sum(1 for t in tst if t.lean == "absent")
        core_fav = sum(1 for t in tst
                       if t.klass == "core" and t.lean == "favourable-leaning")
        core_adv = sum(1 for t in tst
                       if t.klass == "core" and t.lean == "adverse-leaning")
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
            neutral=neu, absent=ab, preponderance=prep, status=status,
            core_favourable=core_fav, core_adverse=core_adv))

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
    if maha in ("Rahu", "Ketu"):
        # nodal MD: Shadbala/vargottama words never apply to a chayagraha, which used to
        # leave cond_words empty and render a dangling "…for this Lagna: ." (2026-08-17 fix).
        # The doctrine-licensed sentence instead: a node gives the results of its
        # sign-dispositor / occupied house (HTJAH-I:2764/8566 — the same citation the
        # vimshottari timer_set already encodes).
        np_ = r.chart.planets.get(maha)
        if np_ is not None:
            disp = SIGN_LORDS[np_.sign]
            disp_words: list[str] = []
            dstrong = _strong(r.chart, disp)
            if dstrong is not None:
                disp_words.append("strong in Shadbala" if dstrong else "weak in Shadbala")
            dp = r.chart.planets.get(disp)
            if dp is not None and dp.vargottama:
                disp_words.append("vargottama")
            cond_words.append(
                f"as a node, {maha} gives the results of its dispositor and of the house "
                f"it occupies (HTJAH-I:2764/8566) — it occupies {_SIGN_NAME[np_.sign]} "
                f"(H{np_.rasi_house}), and its dispositor {disp}"
                + (f" is {', '.join(disp_words)}" if disp_words
                   else "'s condition is read in its own chapter"))
    if cond is not None:
        if cond.strong is not None:
            cond_words.append("strong in Shadbala" if cond.strong else "weak in Shadbala")
        if cond.vargottama:
            cond_words.append("vargottama")
        if cond.at_maximum:
            cond_words.append("at the strength maximum — strong in both rasi and navamsa "
                              "(HPA-24:51-86; Raman's full maximum further requires freedom "
                              "from malefic aspect, not graded here)")
    elif not cond_words:
        cond_words.append("lord condition unavailable on this chart")
    if lean is not None:
        cond_words.append(f"a {lean} Ishta/Kashta lean")
    # never a dangling colon: with no condition words at all, close the sentence cleanly.
    bits.append(f"{lead}: {', '.join(cond_words)}." if cond_words else f"{lead}.")
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
    # chain the bits with "; " AFTER stripping each bit's own sentence-final period —
    # tenor_note ends with "." and joining raw produced the ".;" seam seen in real output.
    caution = ("; ".join(bit.rstrip().rstrip(".") for bit in caution_bits)
               if caution_bits else None)

    # the first-impression line, from the Ruler of the nativity card (HTJAH-I:16001-16002)
    ruler_bit = f"The ruler of the nativity is {r.ruler.lagna_lord}"
    if r.ruler.strongest is not None:
        if r.ruler.coincide:
            ruler_bit += (f", which is also the strongest planet — \"the foundation is quite "
                          f"sound\"")
        else:
            ruler_bit += f"; the strongest planet by Shadbala is {r.ruler.strongest}"
    ruler_bit += ". "
    # Wave-2 (2026-08-17): the Nichod opens the way Raman opens — frame, then ruler
    # (HTJAH-I:645-646, the stronger-frame re-read already shown in Chart signature).
    ruler_bit += ("The reading is weighed from the Moon's sign, the stronger frame here "
                  "(HTJAH-I:645-646). " if r.overview.stronger_frame == "moon" else
                  "The reading is weighed from the Lagna, the stronger frame here "
                  "(HTJAH-I:645-646). ")

    # S5 forward half (Wave-2, 2026-08-17): the next MD boundary after the reference date,
    # with the incoming lord's natal-fixed lean (GBB-10:134) — period indication, not event.
    md_rows = [ik for ik in r.ishta_kashta if ik.antar is None] or [
        ik for ik in r.ishta_kashta]
    forward_horizon = ""
    nxt = next((ik for ik in md_rows
                if ik.start_jd > r.ref_jd and ik.maha != (cur_tp.period.maha
                                                          if cur_tp is not None else None)),
               None)
    if nxt is not None and nxt.maha_lean:
        forward_horizon = (f"the {nxt.maha} chapter that follows from "
                           f"{_jd_month_year(nxt.start_jd)} carries a {nxt.maha_lean} "
                           f"Ishta/Kashta lean - a period indication, not an event")

    essence = (
        f"{identity}. {ruler_bit}{longevity}. "
        + (f"Yogas present: {yogas}. " if r.yogas else "")
        + f"Across the twelve matters, {matters_tally}. "
        + f"What most distinguishes this chart: {stands_out}. "
        + (f"The live cross-feature spotlight: {spotlight.rstrip('.')}. " if spotlight
           else "")
        + f"Right now, the running period is {current_period}; "
        + f"live transits: {live_transits}."
        + (f" {caution}." if caution else "")
        + (f" Looking forward, {forward_horizon}." if forward_horizon else "")
        + " This is a distillation of the method's own reading, assembled entirely from the "
          "sections above — not a prediction of events, and every distinctive claim here "
          "should be read against the population-context percentiles shown throughout this "
          "report."
    )

    # S5 — turning points: MD boundaries where the Ishta/Kashta MD lean flips (pure
    # re-read of the ishta_kashta rows; the lean is natal-fixed per lord, GBB-10:134).
    # `md_rows` is the same MD-level filter built for the forward horizon above.
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
        turning_points=tuple(turning), forward_horizon=forward_horizon,
    )


#: rough percentile -> plain-English intensity word, for the "what's distinctive" paragraph.
#: Guarded jointly on verdict direction + percentile (2026-08-17): a favourable verdict must
#: never carry a "challenging" intensity word (and an afflicted verdict never a "favourable"
#: one) — when the two directions disagree, a neutral descriptive word is used instead.
def _plain_intensity(pct: float, verdict: str | None = None) -> str:
    if pct >= 0.65 and verdict == "afflicted":
        return "an uncommon reading for this area"
    if pct <= 0.35 and verdict == "favourable":
        return "an uncommon reading for this area"
    if pct >= 0.80:
        return "unusually strong"
    if pct >= 0.65:
        return "distinctly favourable"
    if pct <= 0.20:
        return "distinctly challenging"
    if pct <= 0.35:
        return "notably challenging"
    return "worth noting"


def period_pairing(r: "DetailedReport", houses: tuple[int, ...],
                   *, max_lords: int = 3) -> tuple[tuple[str, ...], str]:
    """The Mahadasha lords whose chapters most light `houses` — a pure re-read of the
    already-graded ``life_chapters.houses_lit`` rows (Raman's locked fructification doctrine,
    HTJAH-I:1586-1596: indications ripen in the periods of the planets that influence the
    house or its lord). Returns ``(lords, span)`` — lords ordered best-peak-tier first, then
    chronologically, capped at ``max_lords``; ``span`` is the "YYYY-YYYY" year range those
    lords' runs cover. ``((), "")`` when nothing lights them. Ordering only — no grading is
    invented here; every tier was already computed by ``graded_buckets``."""
    want = set(houses)
    best: dict[str, tuple[int, float, float]] = {}
    for ch in r.life_chapters.chapters:
        ranks = [_TIER_ORDER.index(t) for h, t, _v in ch.houses_lit
                 if h in want and t in _TIER_ORDER]
        if not ranks:
            continue
        rank = min(ranks)
        cur = best.get(ch.maha)
        best[ch.maha] = ((rank, ch.start_jd, ch.end_jd) if cur is None else
                         (min(cur[0], rank), min(cur[1], ch.start_jd),
                          max(cur[2], ch.end_jd)))
    if not best:
        return (), ""
    ranked = sorted(best.items(), key=lambda kv: (kv[1][0], kv[1][1]))[:max_lords]
    import swisseph as swe
    lo = min(v[1] for _m, v in ranked)
    hi = max(v[2] for _m, v in ranked)
    span = f"{int(swe.revjul(lo, swe.GREG_CAL)[0])}-{int(swe.revjul(hi, swe.GREG_CAL)[0])}"
    return tuple(m for m, _v in ranked), span


def _joined_names(names: tuple[str, ...]) -> str:
    """'Venus' / 'Venus and Sun' / 'Venus, Sun and Moon' — plain list prose."""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def period_pairing_clause(r: "DetailedReport", houses: tuple[int, ...]) -> str:
    """One PLAIN clause pairing a life-theme with the periods that most light its houses —
    Raman's pair-indication-with-period discipline (HTJAH-I:1586-1596, the locked timer
    doctrine), spoken in the timed-indication idiom the 2026-08-17 guard decision allows.
    Empty string when no chapter in the display window lights the theme. Jargon-free by
    construction (planet names + years only) for the Your-Reading surface; the citation
    itself is carried by the technical sections this clause re-reads."""
    lords, span = period_pairing(r, houses)
    if not lords:
        return ""
    word = "chapter" if len(lords) == 1 else "chapters"
    return (f"These matters ripen most fully in the {_joined_names(lords)} {word} of life "
            f"({span}).")


#: plain-word glosses for the reconciliation bullets' method jargon (Wave-2, 2026-08-17):
#: Your Reading is the enforced jargon-free zone, so the S3 narrator's tokens are glossed
#: here at composition — the PREC id stays as the parenthetical pointer for the curious.
#: Pure rewording of already-composed sentences; both poles and the governing rule remain.
_RECONCILIATION_GLOSS: Final[tuple[tuple[str, str], ...]] = (
    ("the division is disclosed, never re-voted (PREC-3)",
     "the division is shown openly rather than put to a fresh vote "
     "(rule PREC-3 in 'How to read this report')"),
    ("and neither is wrong (PREC-1)",
     "and neither is wrong (rule PREC-1 in 'How to read this report')"),
    ("judged by its dedicated reader",
     "judged by the reader built specifically for that matter"),
)


def _plain_reconciliation(sentence: str) -> str:
    for token, gloss in _RECONCILIATION_GLOSS:
        sentence = sentence.replace(token, gloss)
    return sentence


#: guarded plain word for each Ayurdaya band — band word ONLY (the number stays in the
#: Longevity section), per the classical order that establishes ayurdaya before judgment.
_VITALITY_BAND_PLAIN: Final[dict[str, str]] = {
    "purna": "full", "madhya": "middle", "alpa": "short"}


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
    # Wave-2 (2026-08-17): Raman states the judging frame before judging (HTJAH-I:645-646,
    # cited in Chart signature) — when the Moon's frame is the stronger, say so up front in
    # plain words. Pure re-read of chart_overview's already-computed stronger_frame.
    if r.overview.stronger_frame == "moon":
        opening += (" This chart is read chiefly from the Moon's position, which is "
                    "stronger than the rising sign here - a choice Raman himself "
                    "prescribes.")
    # Wave-2 (2026-08-17): the classical order establishes vitality before judgment — one
    # guarded line, band word only (the number stays in the Longevity section). A re-read
    # of the already-computed longevity class; a foundation, never a forecast.
    band_word = _VITALITY_BAND_PLAIN.get(r.longevity_class)
    if band_word is not None:
        opening += (f" By the classical count, the chart's vitality reads at the "
                    f"{band_word} band - a foundation for the reading, not a forecast.")

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
            para = ". ".join(sentences) + "."
            # Wave-2 (2026-08-17): Raman never states an indication without its
            # fructification window (HTJAH-I:1586-1596, the locked timer doctrine) — close
            # each theme with the periods that most light its houses. Plain planet names
            # and years only; a pure re-read of the graded life-chapters.
            theme_houses = tuple(sorted({_MATTER_HOUSE[m] for m in matters
                                         if m in _MATTER_HOUSE}))
            pairing = period_pairing_clause(r, theme_houses) if theme_houses else ""
            if pairing:
                para += " " + pairing
            life_paragraphs.append((theme, para))

    md_theme = _PLANET_THEME.get(r.synthesis.running_md, "this planet's classical themes")
    now = (f"You're currently in a {r.synthesis.running_md}-led chapter of life "
          f"(with {r.synthesis.running_ad} adding its own flavour within it) — classically a "
          f"time that brings out {md_theme}.")

    if r.distinctive:
        bits = [f"{_plain_signification(e.signification)} "
                f"({_plain_intensity(e.favourability_percentile, e.verdict)})"
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
                        notable=notable, closing=closing,
                        reconciliations=tuple(_plain_reconciliation(s)
                                              for s in reconciliations))


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
    try:
        bav_matrix = _bav_matrix_rows(chart)
        bav_reduced = _bav_reduced_rows(chart)
        sodya_pinda = _sodya_pinda_rows(chart)
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        bav_matrix, bav_reduced, sodya_pinda = (), (), ()
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
    # Wave-2 (2026-08-18): the adverse mirror — a separate builder so the favourable rows
    # stay byte-identical (see _dasha_transit_adverse's docstring).
    dasha_transit_adverse = _dasha_transit_adverse(chart, timeline, gochara_outlook)
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
        bav_matrix=bav_matrix, bav_reduced=bav_reduced, sodya_pinda=sodya_pinda,
        info=information_content(calib), distinctive=distinctive_entries(calib),
        balarishta=getattr(chart, "balarishta", None),
        dashboard=build_matter_varga_dashboard(chart),
        soul=build_soul_reading(chart),
        pitru=build_pitru_dosha_reading(chart),
        gochara=tuple(gochara_rows), gochara_outlook=gochara_outlook,
        dasha_transit=dasha_transit, dasha_transit_adverse=dasha_transit_adverse,
        maraka_period_now=maraka_now,
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
    from app.raman_saab.monographs import (build_aptitude_profile,
                                           build_children_chapter,
                                           build_marriage_monograph,
                                           build_psych_profile)
    # one try per builder — a failure in one chapter must never silence the others
    for _field, _builder in (("arishta", build_arishta_chapter),
                             ("profession", build_profession_synthesis),
                             ("wealth", build_wealth_chapter),
                             ("marriage", build_marriage_monograph),
                             ("children", build_children_chapter),
                             ("psych", build_psych_profile),
                             ("aptitude", build_aptitude_profile)):
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
    from app.raman_saab.rect_confidence import build_rect_confidence
    try:
        enriched = _dc_replace(
            enriched, rect_confidence=build_rect_confidence(enriched, ayanamsa=ayanamsa))
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
    # Wave-1 timing additions (2026-08-17): the pratyantar drill-down for the current
    # bhukti, the dated Sade-Sati phase spans, and the dated Chara dasha sequence —
    # pure re-reads / plain JD arithmetic over already-encoded primitives.
    try:
        final = _dc_replace(
            final,
            pratyantar_now=_pratyantar_rows(chart, ref_jd),
            sade_sati_phases=_sade_sati_phases(chart, ref_jd, ayanamsa),
            chara_sequence=_chara_sequence(chart, ref_jd))
    except Exception:  # noqa: BLE001 — sparse/Track-B chart
        pass
    # v34 — the integrated interpretation layer reads the FULLY-built report (every section
    # above) and judges nothing anew; it re-reads finished verdicts into one coherent theme
    # synthesis (docs/raman_saab/SYNTHESIS_LAYER_ARCHITECTURE.md).
    try:
        from app.raman_saab.theme_synthesis import build_theme_synthesis
        final = _dc_replace(final, themes=build_theme_synthesis(final))
    except Exception:  # noqa: BLE001 — sparse/Track-B chart; must never block the report
        # log the cause: without this a synthesis regression silently degrades every chart to
        # the "not available" fallback with no trace of why
        logger.debug("integrated reading (theme synthesis) skipped", exc_info=True)
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


def _method_preamble(section_id: str) -> list[str]:
    """'Why astrologers examine this' (2026-08-04): the method's own inspection order for
    a major section — teaching what the section already does, never adding doctrine."""
    from app.raman_saab.plain_terms import SECTION_METHOD
    entry = SECTION_METHOD.get(section_id)
    if entry is None:
        return []
    why, order = entry
    lines = ["**Why astrologers examine this.** " + why + ":", ""]
    lines += [f"{i}. {step}" for i, step in enumerate(order, 1)]
    lines.append("")
    return lines


def passage_quote(cite: str, *, max_chars: int = 260) -> str:
    """Item 14 helper: the verbatim source snippet a citation points to, one clean line,
    trimmed at a sentence boundary within `max_chars`. Empty string when unresolvable."""
    import re as _re

    from app.raman_saab.doctrine.sources import passage as _passage
    p = _passage(cite, context=1)
    if not isinstance(p, dict):
        return ""
    text = _re.sub(r"[¬­]\s*\n\s*", "", p.get("text", ""))
    text = _re.sub(r"\s*\n\s*", " ", text).strip()
    if len(text) > max_chars:
        cut = text[:max_chars]
        dot = cut.rfind(". ")
        text = (cut[:dot + 1] if dot > 60 else cut + "...")
    return text


def _quote_or_absent(text: str | None, cite: str) -> str:
    """Render a verbatim doctrine quote with its citation — or, when the corpus is not
    mounted on this machine (passage()/_pull() legitimately return empty), an honest
    pointer to the passage instead. NEVER renders an empty string as a quotation
    (`— "" (CITE)` was a real 2026-08-17 defect)."""
    if text and text.strip():
        return f"\"{text}\" ({cite})"
    return f"passage {cite} - corpus not mounted on this machine"


_AXIS_LABEL = {"verdict": "verdict", "magnitude": "strength", "state": "state",
               "dasha": "timing", "varga": "divisional", "transit": "transit",
               "yoga": "yoga", "citation": "cross-feature"}


def _md_cell(s: object) -> str:
    """A markdown table cell. A literal `|` inside an interpolated value would split the row and
    shift every later cell, and these cells carry free prose (a fired insight's detail, a yoga
    name), so escape it."""
    return str(s).replace("|", "\\|")


def _theme_conv_label(t: object) -> str:
    """The reader-facing convergence phrase — the layer's own ``convergence_label`` when present
    (e.g. 'aligned, but lightly evidenced'), else the plain tier + 'convergence'."""
    lbl = getattr(t, "convergence_label", "") or ""
    if lbl:
        return lbl
    return getattr(t, "convergence", "").replace("_", " ").lower() + " convergence"


def _integrated_reading_lines(r: DetailedReport) -> list[str]:
    """The v34 integrated-interpretation section, in markdown. A re-read ACROSS the sections:
    an Executive Portrait, the dominant-theme spine, and per-theme evidence chains with their
    convergence and contradictions. Every claim traces to an authoritative verdict the report
    already made; this section judges nothing anew (theme_synthesis is read-only)."""
    L: list[str] = ["## The integrated reading", ""]
    ts = getattr(r, "themes", None)
    if ts is None or not getattr(ts, "themes", None):
        L.append("_The integrated reading is not available for this chart in the current "
                 "engine (a sparse or stated-position chart carries too few decided sections "
                 "to synthesize)._")
        L.append("")
        return L
    L.append("_One reading across every section above — not a new judgment. Each theme below "
             "gathers the independent findings the report already made (house verdict, "
             "strength, planetary state, divisional confirmation, yoga, timing) into one "
             "mechanism, states how strongly they converge, and names any tension with the "
             "precedence rule that resolves it. The direction of every theme is the engine's "
             "own house verdict, carried through unchanged._")
    L.append("")

    p = ts.portrait
    L.append("### Executive portrait")
    L.append("")
    if getattr(p, "identity", ""):
        L.append(f"- **Who the chart is** — {p.identity}")
    if p.frame:
        L.append(f"- **Reading frame** — judged chiefly from the {p.frame} "
                 f"(the stronger of the two lagnas here).")
    if p.temperament and p.temperament != f"read chiefly from the {p.frame}":
        L.append(f"- **Temperament** — {p.temperament}.")
    if p.dominant_actors:
        actors = "; ".join(f"**{name}** ({why})" for name, why in p.dominant_actors)
        L.append(f"- **Dominant actors** — {actors}.")
    if p.strongest_domains:
        L.append(f"- **Strongest domains** — {', '.join(p.strongest_domains)}.")
    if p.weakest_domains:
        L.append(f"- **Areas under strain** — {', '.join(p.weakest_domains)}.")
    if p.protective_factors:
        L.append(f"- **Protective factors** — {'; '.join(p.protective_factors)}.")
    if p.principal_tension:
        L.append(f"- **Principal tension** — {p.principal_tension}")
    if p.current_chapter:
        nxt = f"; {p.next_chapter}" if p.next_chapter else ""
        L.append(f"- **Current chapter** — {p.current_chapter}{nxt}.")
    if p.honesty_note:
        L.append(f"- _{p.honesty_note}_")
    L.append("")

    # the spine
    by_id = {t.theme_id: t for t in ts.themes}
    spine = [by_id[i] for i in ts.spine if i in by_id]
    if spine:
        L.append("### The interpretive spine")
        L.append("")
        L.append("_The few themes that explain a disproportionate amount of this chart, "
                 "strongest evidence first:_")
        L.append("")
        for t in spine:
            L.append(f"- **{t.name}** — {t.headline_verdict} "
                     f"({_theme_conv_label(t)})")
        L.append("")

    # every theme, ranked
    L.append("### Major life-themes")
    L.append("")
    for t in ts.themes:
        houses = ", ".join(f"H{h}" for h in t.houses)
        L.append(f"#### {t.name} — **{t.headline_verdict}** ({_theme_conv_label(t)})")
        L.append("")
        dom = ", ".join(t.dominant_planets) if t.dominant_planets else "the chart"
        L.append(f"_{t.final_interpretation}_")
        L.append("")
        L.append(f"- **Network** — {houses}"
                 + (f"; karakas {', '.join(t.karakas)}" if t.karakas else "")
                 + f"; driven by {dom}.")
        # the house's facets — each matter that lives here, with its own dedicated verdict
        if getattr(t, "sub_matters", None):
            facets = "; ".join(f"{m} reads {v}" for m, v in t.sub_matters)
            L.append(f"- **Within this house** — {facets}.")
        L.append(f"- **Convergence** — {_theme_conv_label(t)}: {t.convergence_why}")
        L.append(f"- **Divisional (D9)** — {t.varga_relation}.")
        if t.activation_span:
            L.append(f"- **Timing** — {t.activation_span}")
        # the evidence chain (traceable), grouped by axis
        L.append("")
        L.append("| axis | finding | source |")
        L.append("|---|---|---|")
        for lk in t.links:
            L.append(f"| {_AXIS_LABEL.get(lk.axis, lk.axis)} | "
                     f"{_md_cell(lk.label)}: {_md_cell(lk.value)} | "
                     f"`{_md_cell(lk.accessor.split('@')[-1].strip())}` |")
        L.append("")
        if t.contradictions:
            for c in t.contradictions:
                L.append(f"- **Tension ({c.kind})** — {c.poles[0]} vs {c.poles[1]}. "
                         f"Resolved by **{c.governing}**: {c.resolution}")
            L.append("")

    # how the themes connect (the cross-theme fabric — one mechanism behind several areas)
    if getattr(ts, "connections", None):
        L.append("### How the themes connect")
        L.append("")
        L.append("_Where one computed factor drives more than one life-area, so the chart "
                 "reads as a single fabric rather than separate modules:_")
        L.append("")
        for c in ts.connections:
            L.append(f"- {c.note}")
        L.append("")

    # dasha evolution — the horoscope through time (which themes each chapter emphasizes)
    if getattr(ts, "dasha_evolution", None):
        L.append("### Dasha evolution — the horoscope through time")
        L.append("")
        L.append("_Each Mahadasha chapter foregrounds the themes its lord actually drives — the "
                 "Saturn period brings forward what Saturn governs, not every house it touches — "
                 "split into what newly emerges and what continues from the chapter before. A "
                 "re-read of the life-narrative, no new timing math:_")
        L.append("")
        L.append("| chapter | span | lean | newly emphasized | continuing |")
        L.append("|---|---|---|---|---|")
        for ch in ts.dasha_evolution:
            now = " (now)" if ch.is_current else ""
            via = getattr(ch, "acts_through", ()) or ()
            through = f" (acting through {', '.join(via)})" if via else ""
            L.append(f"| {_md_cell(ch.maha)} MD{now}{through} | {_md_cell(ch.span)} | "
                     f"{_md_cell(ch.lean)} | {_md_cell(', '.join(ch.emerging) or '-')} | "
                     f"{_md_cell(', '.join(ch.continuing) or '-')} |")
        L.append("")
        if any(getattr(ch, "acts_through", ()) for ch in ts.dasha_evolution):
            L.append("_Rahu and Ketu own no sign, so a nodal chapter is read through the lord of "
                     "the sign the node occupies and any planet joined with it — the routing is "
                     "named above rather than assumed._")
            L.append("")

    # varga confirmation matrix — each theme's divisional relation to its natal indication
    L.append("### Varga confirmation matrix")
    L.append("")
    L.append("_Does the relevant division confirm, qualify or stay neutral on each theme's "
             "natal indication? (D9 is the only division that modulates a D1 verdict in this "
             "engine; the rest are read for their own domain in the divisional deep-reads.)_")
    L.append("")
    L.append("| theme | natal verdict | D9 relation |")
    L.append("|---|---|---|")
    for t in ts.themes:
        L.append(f"| {_md_cell(t.name)} | {_md_cell(t.headline_verdict)} | "
                 f"{_md_cell(t.varga_relation)} |")
    L.append("")
    return L


def to_markdown(r: DetailedReport) -> str:
    """Render the full detailed report as a Markdown document (ASCII-safe)."""
    s, b = r.synthesis, r.birth
    # deliberately un-shadowable names: a bare `y`/`mo`/`d` here was silently re-bound by a
    # later loop variable and leaked a dataclass repr into the Longevity sentence (2026-08-17).
    lon_y, lon_mo, lon_d = r.longevity_ymd
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
    L.append("")

    # ── judgment graph (v32) — USED already above (the dominant-planet census sentence);
    # shown here, right beside Your Reading, rather than buried later in the document.
    L.append("## Judgment graph")
    L.append("")
    try:
        from app.raman_saab.judgment_graph import (DOCTRINE_CONSTANT_RELATIONS,
                                                   build_judgment_graph, house_facts,
                                                   house_sentence)
        _jg = build_judgment_graph(r)
        _by_rel: dict[str, int] = {}
        for _e in _jg.edges:
            _by_rel[_e.relation] = _by_rel.get(_e.relation, 0) + 1
        L.append("The reasoning behind this reading: every planet linked to the houses it "
                 "rules, sits in, aspects or signifies, and to the periods that light them.")
        L.append("")
        L.append("### What shapes each area of your life")
        L.append("")
        L.append("| House | Verdict | What touches it | Natural significators | "
                 "Periods that light it (at best) |")
        L.append("|---|---|---|---|---|")
        for _h, _f in sorted(house_facts(_jg).items()):
            _tm = "; ".join(f"{lord}{f' ({g})' if g else ''}" for lord, g in _f.timers)
            L.append(f"| {_h} — {_HOUSE_NAME.get(_h, '-')} | {_f.verdict or '-'} | "
                     f"{house_sentence(_f)} | {', '.join(_f.karakas) or '-'} | {_tm or '-'} |")
        L.append("")
        _const = sum(_by_rel.get(k, 0) for k in DOCTRINE_CONSTANT_RELATIONS)
        if _const:
            L.append(f"A further **{_const}** edges record how the report's own sections "
                     f"relate (which section governs another, which re-reads another). Those "
                     f"are the same for every chart — they describe the method, not this "
                     f"nativity — and are set out in \"How to read this report\".")
            L.append("")
        L.append(f"**{len(_jg.nodes)} nodes, {len(_jg.edges)} edges** — " +
                 ", ".join(f"{k} {v}" for k, v in sorted(_by_rel.items())) + ".")
        L.append("")
    except Exception:  # noqa: BLE001 — sparse/Track-B chart; the graph is a re-read, not a verdict
        L.append("_Graph unavailable for this chart (sparse data) — the readings above stand "
                 "on their own evidence regardless._")
        L.append("")

    # ── the honesty headline (aggregate information content) ──────────────────
    L.append("")
    L.append("## Information content of this reading")
    L.append("")
    L.append(r.info.sentence)
    L.append("")
    # Wave-2 (2026-08-17): the sentence's arithmetic, checkable at a glance (each row is a
    # field of the same InfoContent aggregate — classes overlap by construction, so the
    # rows are a breakdown of the sentence, not a partition of the total).
    L.append("| class | count |")
    L.append("|---|---:|")
    L.append(f"| total readings | {r.info.total} |")
    L.append(f"| most common verdict ({r.info.modal_verdict}) | {r.info.modal_count} |")
    L.append(f"| near-universal (held by half the population or more) | "
             f"{r.info.near_universal} |")
    L.append(f"| proven inverted channels | {r.info.inverted} |")
    L.append(f"| genuinely distinctive | {r.info.distinctive} |")
    L.append("")
    L.append(f"_{POPULATION_NOTE}_")
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

    # ── the integrated reading (v34) — the theme synthesis, above the technical sections ──
    L.extend(_integrated_reading_lines(r))

    # ── what actually distinguishes this chart ────────────────────────────────
    if r.distinctive:
        L.append("## What stands out in this chart")
        L.append("")
        L.append("_The readings furthest from the population midpoint — where this chart is least "
                 "like everyone else's. Rare readings first, then notable, then common; within "
                 "each band, furthest from the midpoint first._")
        L.append("")
        L.append("| house | matter | verdict | percentile | share | in plain terms |")
        L.append("|---|---|---|---:|---:|---|")
        for house, e in r.distinctive:
            L.append(f"| H{house} {_HOUSE_NAME[house]} | {e.signification} | "
                     f"{e.verdict} ({e.degree}) | {e.favourability_percentile:.0%} | "
                     f"{e.band_share:.0%} ({e.rarity}) | {distinctive_gloss(e)} |")
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
            # 1-based rank for humans (Wave-2, 2026-08-17); `priority` stays 0-based in
            # the JSON/structured surfaces (the engine's own index, contract-stable).
            L.append(f"| {it.priority + 1} | {it.kind} | **{it.title}** — {it.detail} | "
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
             f"(Raman: begin from the ascendant or the Moon, whichever is stronger; "
             f"HTJAH-I:645-646 — measured here by the two sign-lords' total Shadbala, "
             f"a named operationalization, never a silent one)")
    L.append(f"- **Jaimini** — Karakamsa {s.karakamsa}  |  Upapada {s.upapada}  |  "
             f"spouse-lord (7th-from-D9) {s.spouse_significator}")
    L.append(f"- **Running periods** — Vimshottari {s.running_md} MD / {s.running_ad} AD  |  "
             f"Chara dasha {s.chara}" + (f"  |  {s.sade_sati}" if s.sade_sati else ""))
    if s.panchanga:
        L.append(f"- **Panchanga** — {s.panchanga}")
    if r.overview.functional_natures:
        nat = "; ".join(f"{p} {n}" for p, n in r.overview.functional_natures)
        L.append(f"- **Functional nature for this Lagna** — {nat}")
    # Raman's first glance (2026-08-18 report-critique): balance of dasha at birth, the
    # exact Lagna/Moon degrees, the Moon's paksha vs its Shadbala, the luminaries' own
    # strength flags, the Lagna lord's disposition and the day-lord observation — every
    # row a computed re-read (see `signature_first_glance`); append-only.
    for _fg_label, _fg_value in signature_first_glance(r):
        L.append(f"- **{_fg_label}** — {_fg_value}")
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
    if ru.takeaway:
        L.append(f"**{ru.takeaway}**")
        L.append("")
    ll_bit = f"{ru.lagna_lord}, lord of the {_SIGN_NAME[r.chart.asc_sign]} Lagna"
    if ru.lagna_lord_house is not None:
        ll_bit += f", in house {ru.lagna_lord_house}"
    L.append(f"- **Ruler of the nativity (Lagna lord)** — {ll_bit}")
    # the ruler's OWN condition block (2026-08-18 report-critique — the chapter's
    # namesake gets the same full read the strongest planet already had)
    ll_cond: list[str] = []
    if ru.lagna_lord_sign is not None:
        ll_cond.append(f"in {_SIGN_NAME[ru.lagna_lord_sign]}"
                       + (f" ({ru.ll_dignity} sign)" if ru.ll_dignity else ""))
    if ru.ll_avastha is not None:
        ll_cond.append(f"{ru.ll_avastha} avastha (HPA Ch.7)")
    if ru.ll_rupas is not None and ru.ll_required is not None:
        ll_cond.append(
            f"{ru.ll_rupas:.2f} rupas against its required {ru.ll_required:.1f} "
            f"(GBB-8:303) — {'meets' if ru.ll_powerful else 'below'} the minimum"
            + (", the only planet in this chart below its own"
               if ru.ll_only_failing else ""))
    if ru.ll_functional_nature is not None:
        ll_cond.append(f"functional {ru.ll_functional_nature} for this Lagna")
    if ru.lagna_lord_house is not None:
        ll_cond.append("aspected by "
                       + (", ".join(ru.ll_aspects_received)
                          if ru.ll_aspects_received else "no planet"))
    if ru.ll_dispositor is not None:
        ll_cond.append(f"dispositor {ru.ll_dispositor}"
                       + (f" in house {ru.ll_dispositor_house}"
                          if ru.ll_dispositor_house is not None else ""))
    if ll_cond:
        L.append(f"- **The ruler's own condition** — {'; '.join(ll_cond)}")
    if ru.foundation_line:
        L.append(f"- **Foundation** — {ru.foundation_line}")
    if ru.chandra_lagna_lord is not None:
        ch_bit = (f"the signature reads the MOON as the stronger frame (HTJAH-I:645-646), "
                  f"so the Chandra-lagna lord ({ru.chandra_lagna_lord}) is the third "
                  f"classical candidate")
        if ru.chandra_ll_condition:
            ch_bit += f" — it stands {ru.chandra_ll_condition}"
        L.append(f"- **Third classical candidate (Chandra Lagna)** — {ch_bit}")
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
            # role-first opener (2026-08-18 report-critique): the census is demoted to
            # a trailing receipts line; the chapter opens on the planet's computed roles
            L.append(f"### {b.planet}"
                     + (f" — {b.role_line}" if b.role_line else ""))
            L.append("")
            hdr_bits: list[str] = []
            if b.rupas is not None:
                hdr_bits.append(f"{b.rupas:.2f} rupas — "
                                + ("meets" if b.powerful else "below")
                                + " Raman's minimum (GBB-8:303)")
            elif b.planet in ("Rahu", "Ketu"):
                hdr_bits.append("no Shadbala (chayagraha — the measure is defined for "
                                "the seven visible planets)")
            if b.functional_nature:
                hdr_bits.append(f"functional {b.functional_nature} for "
                                f"{_SIGN_NAME[r.chart.asc_sign]} (HTJAH-I:523-604)")
            if hdr_bits:
                L.append(f"_{'; '.join(hdr_bits)}_")
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
            if b.casts_drishti:
                L.append(f"- **Casts drishti on** — {', '.join(b.casts_drishti)} "
                         f"(whole-sign)")
            if b.receives_drishti:
                L.append(f"- **Receives drishti from** — "
                         f"{', '.join(b.receives_drishti)}")
            elif b.rupas is not None or b.planet in ("Rahu", "Ketu"):
                L.append("- **Receives drishti from** — no planet aspects it")
            if b.avastha and b.avastha_result:
                L.append(f"- **Avastha consequence (HPA Ch.7)** — {b.avastha}: "
                         f"{b.avastha_result}")
            if b.family_role_named or b.family_role:
                L.append(f"- **Family/karaka duties** — "
                         f"{b.family_role_named or b.family_role}")
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
            L.append(f"- **Receipts** — {b.census_count} graph appearances "
                     f"({', '.join(f'{k} {v}' for k, v in b.census_by_relation)})")
            L.append("")

    # ── psychological profile (v27 — the mind stack woven) ────────────────────
    if r.psych is not None:
        ps = r.psych
        L.append("## Psychological profile")
        L.append("")
        L.extend(_method_preamble("psych"))
        L.append(f"_{ps.woven}_")
        L.append("")
        L.append(f"- **The rising sign's portrait (Raman verbatim)** — "
                 f"\"{ps.lagna_quote[0]}\" ({ps.lagna_quote[1]})")
        if ps.moon_state:
            L.append(f"- **The mind's significator** — {ps.moon_state}")
        for _mm_id, _mm_text, _mm_cite in ps.moon_mind:
            L.append(f"- **The Moon's sign (mental disposition)** [{_mm_id}] — "
                     f"{_mm_text} ({_mm_cite})")
        if ps.mercury_line:
            L.append(f"- **Mercury (buddhi)** — {ps.mercury_line}")
        if ps.deeptadi_moon:
            L.append(f"- **The Moon's avastha (cross-reference)** — {ps.deeptadi_moon}")
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
    L.append("_Longitudes are exact sidereal (Lahiri) degrees in sign-degree form "
             "(deg Sign min'sec\"), so every row — Ascendant included — can be checked "
             "against Jagannatha Hora or drikpanchang. The nakshatra lord is each star's "
             "Vimshottari lord: the Moon's row explains the birth Mahadasha._")
    L.append("")
    L.append("| graha | longitude | sign | house | nakshatra (pada) | nak lord | navamsa | notes |")
    L.append("|---|---|---|---:|---|---|---|---|")
    asc_lon_s, asc_nak, asc_pada, asc_nav, asc_sign = ascendant_position(r.chart)
    asc_nk = nakshatra_signature.signature_for(asc_nak)
    L.append(f"| Ascendant | {asc_lon_s} | {_SIGN_NAME[asc_sign]} | 1 | "
             f"{asc_nk.name if asc_nk else '?'} ({asc_pada}) | {nakshatra_lord(asc_nak)} | "
             f"{_SIGN_NAME[asc_nav]} | - |")
    for name, p in planet_rows(r.chart):
        nk = nakshatra_signature.signature_for(p.nakshatra)
        notes = []
        if p.retrograde:
            notes.append("retrograde")
        if p.vargottama:
            notes.append("vargottama")
        if getattr(p, "combust_fraction", 0) >= 0.5:
            notes.append("combust")
        L.append(f"| {name} | {format_longitude(p.lon)} | {_SIGN_NAME[p.sign]} | {p.rasi_house} | "
                 f"{nk.name if nk else '?'} ({p.pada}) | {nakshatra_lord(p.nakshatra)} | "
                 f"{_SIGN_NAME[p.navamsa_sign]} | "
                 f"{', '.join(notes) or '-'} |")
    L.append("")

    # ── rectification confidence (v31 — input sensitivity, measured as a RANGE) ────
    if r.rect_confidence is not None:
        rc = r.rect_confidence
        L.append("## Rectification confidence")
        L.append("")
        L.append(f"_{rc.frame}_")
        L.append("")
        L.append(f"- **Verdict** — {rc.label}")
        L.append(f"- **Every pillar holds together** from -{rc.overall_stable_minus} to "
                 f"+{rc.overall_stable_plus} minutes ({rc.stable_count} of {rc.total_count} "
                 f"pillars never flip inside the full ±{rc.scan_window}-minute scan)")
        L.append("")
        L.append("| Pillar | At the stated time | Stable range (minutes) | Flips to |")
        L.append("|---|---|---|---|")
        for pl in rc.pillars:
            rng = f"-{pl.stable_minus} to +{pl.stable_plus}"
            flips = "; ".join(
                f"{off:+d} min → {v}" for off, v in filter(None, (pl.flip_minus, pl.flip_plus)))
            if not flips:
                flips = f"stable beyond ±{rc.scan_window} min (not tested further)"
            L.append(f"| {pl.pillar} | {pl.base_value} | {rng} | {flips} |")
        L.append("")

    # ── Shadbala (the numbers behind every 'strong'/'weak') ───────────────────
    sb_rows = [(n, p) for n, p in planet_rows(r.chart) if p.shadbala_rupas is not None]
    if sb_rows:
        from app.raman_saab.primitives.shadbala.total import is_powerful
        from app.raman_saab.plain_terms import band_rupas
        L.append("## Shadbala (six-fold strength, rupas)")
        L.append("")
        L.append("_**Planetary strength — think of it as horsepower**: a powerful engine "
                 "can pull a heavier load, and a strong planet tends to deliver its "
                 "indications more effectively in its periods. The bands below compare "
                 "each planet against RAMAN'S OWN required minimum (GBB-8:303), never an "
                 "invented cutoff. This is the strength measure behind every "
                 "'strong/weak' in this report (HTJAH-I:611, Graha and Bhava Balas). "
                 "Ishta/Kashta = good-yield / hard-yield potential — the planet's "
                 "built-in inclination to deliver pleasant or difficult results._")
        L.append("")
        L.append("| graha | sthana | dig | kala | cheshta | naisargika | drik | **total** | "
                 "ratio | powerful? | ishta/kashta | in plain terms |")
        L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
        from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED as _SB_MIN
        _sb_notes: list[str] = []
        _comp_names = ("sthana", "dig", "kala", "cheshta", "naisargika", "drik")
        for name, p in sb_rows:
            sb = p.shadbala_rupas
            strong = is_powerful(name, sb.total / 60.0)
            ik = (f"{p.ishta:.1f}/{p.kashta:.1f}"
                  if p.ishta is not None and p.kashta is not None else "-")
            comps = (sb.sthana, sb.dig, sb.kala, sb.cheshta, sb.naisargika, sb.drik)
            cells = " | ".join(f"{v / 60.0:.2f}" for v in comps)
            _req = _SB_MIN.get(name)
            ratio = f"{(sb.total / 60.0) / _req:.2f}" if _req else "-"
            L.append(f"| {name} | {cells} | **{sb.total / 60.0:.2f}** | {ratio} | "
                     f"{'yes' if strong else 'no'} | {ik} | "
                     f"{band_rupas(name, sb.total / 60.0)} |")
            if not strong:
                # weakest-component pointer for a failing planet: arithmetic on the six
                # values the table already shows — NO per-component minimum is asserted
                # (Raman's component-wise requirements are not encoded here)
                _wk_name, _wk_val = min(zip(_comp_names, comps), key=lambda kv: kv[1])
                _sb_notes.append(
                    f"{name} falls below its minimum; of the six components shown, its "
                    f"smallest is {_wk_name} ({_wk_val / 60.0:.2f} rupas) — an arithmetic "
                    f"pointer to where the deficit sits, not a per-component judgment "
                    f"(no per-component minima are encoded)")
        L.append("")
        # scale + definitional notes (2026-08-18 report-critique, append-only)
        L.append("_Scale notes: **ratio** = total / Raman's required minimum (GBB-8:303) — "
                 "1.00 is exactly the bar. The Sun and Moon show **cheshta 0.00 by "
                 "definition** — they receive no Cheshta Bala in the Shadbala total "
                 "(GBB-6:23-28); that cell is not missing data. **Ishta/Kashta** are each "
                 "on a 0-60 scale (GBB-10:134); this chart's leans, in the same good/hard "
                 "vocabulary the period readings use: "
                 + "; ".join(f"{n} {_ishta_kashta_lean(r.chart, n)}" for n, _p in sb_rows
                             if _ishta_kashta_lean(r.chart, n) is not None)
                 + "._")
        for _note in _sb_notes:
            L.append("")
            L.append(f"_{_note}._")
        L.append("")

    # ── fired yogas ───────────────────────────────────────────────────────────
    from app.raman_saab.doctrine.yogas import YOGAS as _YOGA_RECORDS
    from app.raman_saab.doctrine.yogas import (MAHAPURUSHA_IDS as _MAHAPURUSHA_IDS,
                                               family_breakdown as _family_breakdown,
                                               yoga_family as _yoga_family)
    from app.raman_saab.yoga_deep_read import (
        kemadruma_cancellation_branch as _kem_branch)
    from app.raman_saab.primitives.bhangas import kemadruma as _kem_geometry
    L.append("## Yogas present in this chart")
    L.append("")
    if r.yogas:
        L.append("_Each carries its citation. A yoga's effect depends on the strength of the "
                 "planets causing it (HTJAH-I:611)._")
        L.append("")
        # Wave-2 A5 (2026-08-18): bullets ordered by the deep-read's measured comparison
        # rank (strongest participants first) so list order = importance; yogas the
        # deep-read could not rank keep their detection order after the ranked ones.
        _rank_of = {yd.id: yd.comparison_rank for yd in r.yoga_deep}
        _ordered = sorted(enumerate(r.yogas),
                          key=lambda iy: (_rank_of.get(iy[1].id, 10_000), iy[0]))
        for _i, yg in _ordered:
            # Wave-2 A4: family name where the bare "other" kind tag says nothing.
            _fam = _yoga_family(yg.id)
            _tag = _fam if (yg.kind == "other" and _fam) else yg.kind
            L.append(f"- **{yg.name}** ({_tag}) — {yg.effect}  "
                     f"`{yg.source.work}:{yg.source.line}`")
        if r.yoga_deep:
            L.append("")
            L.append("_Ordered by the deep-read's measured comparison rank (strongest "
                     "participants first); the full study of each is in the Yoga "
                     "deep-read below._")
    else:
        L.append("_No encoded yoga fires on this chart._")
    # Wave-2 A2 (2026-08-18): cancelled-Kemadruma surfacing — the bhanga primitives
    # compute both halves; the record `Y.KEMADRUMA` fires only while uncancelled, so a
    # geometry-plus-bhanga chart would otherwise show NOTHING here although 3HC's own
    # remarks treat the cancelled state as significant. Same three-state read the
    # Arishta chapter already narrates — re-read, not re-judged.
    if _kem_geometry(r.chart):
        _kb = _kem_branch(r.chart)
        if _kb is not None:
            L.append("")
            L.append(f"_Kemadruma geometry is present but cancelled by {_kb} - the yoga "
                     f"does not fire (bhanga per 3HC:2182-2185; the Arishta chapter "
                     f"reports the same three-state read)._")
    # Wave-2 A3: notable absences Raman himself checks in worked charts — computed
    # trivially from the same detection pass; disclosure, not judgment.
    _absent_bits = []
    if not any(y.id in _MAHAPURUSHA_IDS for y in r.yogas):
        _absent_bits.append("no Pancha Mahapurusha yoga fires")
    if not any(y.kind == "arishta" for y in r.yogas):
        _absent_bits.append("no encoded arishta yoga fires")
    if _absent_bits:
        L.append("")
        L.append(f"_Notable absences (computed from the same detection pass): "
                 f"{'; '.join(_absent_bits)}._")
    # Wave-2 A1: coverage honesty — what this list actually checks, so a reader can
    # distinguish "chart lacks Lakshmi Yoga" from "engine never checks Lakshmi Yoga".
    _fams = "; ".join(f"{fam} {n}" for fam, n in _family_breakdown())
    L.append("")
    L.append(f"_Coverage disclosure: {len(_YOGA_RECORDS)} named combinations are encoded "
             f"and checked against every chart, of the ~300 in Raman's Three Hundred "
             f"Important Combinations and allied chapters - by family: {_fams}. A yoga "
             f"absent from this list is unchecked, not absent._")
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
        # Wave-2 C (2026-08-18, add-only): one-line-per-yoga "next ripening" summary
        # ABOVE the retained full table (REPORT COMPLETENESS: the table stays).
        _ripening = yoga_next_ripening(r)
        if _ripening:
            L.append("_Next ripening, per yoga (the full table below is retained):_")
            L.append("")
            for _yn, _sent in _ripening:
                L.append(f"- **{_yn}** — {_sent}")
            L.append("")
        # Wave-3 (2026-08-18): the full table, GROUPED BY YOGA rather than interleaved
        # by date — every row is retained (nothing is de-duplicated away), the yoga name
        # is the group's own label, and the columns are unchanged.
        L.append("_Every window below is retained; the rows are grouped by yoga (they "
                 "were previously interleaved by date, which printed one Mahadasha as "
                 "three verbatim-identical rows under three yogas)._")
        L.append("")
        for _yname, _rows in yoga_timing_grouped(r):
            L.append(f"**{_yname}** - {len(_rows)} constituent-lord window"
                     f"{'s' if len(_rows) != 1 else ''}")
            L.append("")
            L.append("| Yoga | Period | Planet | Window | Delivery | Now |")
            L.append("|---|---|---|---|---|---|")
            for t in _rows:
                # Wave-2 C: AD rows carry their MD context (Raman's bhukti doctrine is
                # MD-lord-relative) and the row containing the reference date is marked.
                _role_cell = (f"AD (under {t.maha} MD)" if t.role == "AD" and t.maha
                              else t.role)
                _now_cell = ("NOW" if t.period_start_jd <= r.ref_jd < t.period_end_jd
                             else "")
                L.append(f"| {t.yoga_name} | {_role_cell} | {t.planet} | "
                         f"{_outlook_window_label(t.period_start_jd, t.period_end_jd)} | "
                         f"{t.quality.tag} | {_now_cell} |")
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
        for yd in r.yoga_deep:            # NOT `y` — it shadowed the longevity unpack above
            L.append(f"### {yd.comparison_rank}. {yd.name} ({yd.kind}) — {yd.cite}")
            L.append("")
            L.append(f"- **Definition (verbatim)** — \"{yd.definition_quote}\" ({yd.cite})")
            L.append(f"- **Computation** — `{yd.computation}`")
            if yd.participants:
                # Wave-2 B (2026-08-18): each participant also carries its
                # kendra/trikona/dusthana placement class (3HC remarks' standard
                # strength qualifier) and its functional nature for THIS Lagna
                # (HTJAH-I:523-604) — labels on values already computed.
                pf = "; ".join(
                    f"{f.planet}: house {f.house}"
                    + (f" ({f.placement})" if f.placement else "")
                    + f", {_SIGN_NAME[f.sign]}, {f.dignity}"
                    + (f" (effective: {f.effective_dignity})"
                       if f.effective_dignity != f.dignity else "")
                    + (f", {f.rupas} rupas" if f.rupas is not None else "")
                    + (f", functional {f.functional} for this Lagna"
                       if f.functional else "")
                    for f in yd.participants)
                L.append(f"- **Why it qualifies** — {pf}")
            L.append(f"- **Strength (measured)** — {yd.strength_note}")
            if yd.syn_r1_line:
                L.append(f"- **Stronger-participant delivery** — {yd.syn_r1_line}")
            L.append(f"- **Cancellation** — {yd.cancellation_note}")
            if yd.modifiers:
                L.append(f"- **Modifying planets** (aspecting the participants' houses) "
                         f"— {', '.join(yd.modifiers)}")
            if yd.periods:
                L.append(f"- **Operating periods** — {'; '.join(yd.periods)}")
            if yd.nh_examples:
                L.append(f"- **In Notable Horoscopes** — {', '.join(yd.nh_examples)}")
            L.append(f"- **Effect (Raman)** — {yd.effect}")
            L.append("")

    # ── Ashtakavarga strength row ─────────────────────────────────────────────
    if r.sav:
        L.append("## Ashtakavarga (Sarvashtakavarga bindus by sign)")
        L.append("")
        L.append("| " + " | ".join(_SIGN_NAME[i][:3] for i in range(1, 13)) + " |")
        L.append("|" + "---:|" * 12)
        L.append("| " + " | ".join(str(r.sav.get(i, 0)) for i in range(1, 13)) + " |")
        # AV completeness (2026-08-17, append-only): a plain deviation row vs the 337/12
        # average, then the Lagna and Moon-sign columns marked — Gochara is graded FROM the
        # Moon sign, so these two columns are the reader's anchors into the grid.
        L.append("| " + " | ".join(f"{r.sav.get(i, 0) - 28:+d}" for i in range(1, 13)) + " |")
        _moon_p = r.chart.planets.get("Moon")
        _moon_sign = _moon_p.sign if _moon_p is not None else None
        _col_marks = []
        for i in range(1, 13):
            m = [lbl for lbl, hit in (("Lagna", i == r.chart.asc_sign),
                                      ("Moon", i == _moon_sign)) if hit]
            _col_marks.append("+".join(m) if m else " ")
        L.append("| " + " | ".join(_col_marks) + " |")
        L.append("")
        L.append("_Average is 28 per sign (total 337). Raman rates Ashtakavarga corroborative, "
                 "not decisive: \"it does not seem to be quite reliable\" (HTJAH-II:4453-4456)._")
        L.append("")
        L.append("_Second row: deviation vs the 28-bindu average. Third row: the Lagna column "
                 "(house 1; count houses from it) and the Moon-sign column (transits in the "
                 "Gochara section are judged from the Moon)._")
        L.append("")
        # ── the 7x12 Bhinnashtakavarga matrix (AV completeness, 2026-08-17) ──
        if r.bav_matrix:
            L.append("### Bhinnashtakavarga (BAV) - each planet's own bindu row")
            L.append("")
            L.append("_The per-planet tables the SAV row above sums (canonical Parashari "
                     "benefic-places tables; each planet's total is a fixed checksum and the "
                     "seven rows always sum to 337). The Gochara table's 'AV bindus' and "
                     "Kakshya columns, and the AV dasha-seat outlook, all read from these "
                     "rows. A planet's **bold** cell is its own natal sign - its seat, shown "
                     "again in the last column._")
            L.append("")
            L.append("| Planet | " + " | ".join(_SIGN_NAME[i][:3] for i in range(1, 13))
                     + " | Total | Natal seat |")
            L.append("|---|" + "---:|" * 12 + "---:|---|")
            for bm in r.bav_matrix:
                cells = [f"**{v}**" if bm.seat_sign == i else str(v)
                         for i, v in enumerate(bm.bindus, start=1)]
                seat = (f"{_SIGN_NAME[bm.seat_sign][:3]} ({bm.seat_bindus})"
                        if bm.seat_sign is not None else "n/a")
                L.append(f"| {bm.planet} | " + " | ".join(cells)
                         + f" | {bm.total} | {seat} |")
            L.append("")
        # ── HPA-26 reductions (Trikona + Ekadhipathya Sodhana) ──
        if r.bav_reduced:
            L.append("### HPA-26 reductions (Trikona + Ekadhipathya Sodhana)")
            L.append("")
            L.append("_HPA-26 reductions - used classically for special calculations; shown "
                     "for completeness; ASP transit application deferred pending corpus. "
                     "Raman: the bindu tables \"must be subjected to two reductions, viz., "
                     "Thrikona reduction and Ekadhipathya reduction\" (HPA-26:390-393), in "
                     "that order - \"After the Thrikona reduction, the Ekadhipathya reduction "
                     "must be applied\" (HPA-26:466-467). Trikona follows Raman's own stated "
                     "SUBTRACT reading (HPA-26:423-431), regression-pinned to his worked Sun "
                     "table (HPA-26:432-462)._")
            L.append("")
            L.append("**After Trikona Sodhana** (HPA-26:403-421):")
            L.append("")
            L.append("| Planet | " + " | ".join(_SIGN_NAME[i][:3] for i in range(1, 13)) + " |")
            L.append("|---|" + "---:|" * 12)
            for br in r.bav_reduced:
                L.append(f"| {br.planet} | " + " | ".join(str(v) for v in br.trikona) + " |")
            L.append("")
            L.append("**After both reductions** (Ekadhipathya applied, HPA-26:464-497):")
            L.append("")
            L.append("| Planet | " + " | ".join(_SIGN_NAME[i][:3] for i in range(1, 13)) + " |")
            L.append("|---|" + "---:|" * 12)
            for br in r.bav_reduced:
                L.append(f"| {br.planet} | " + " | ".join(str(v) for v in br.reduced) + " |")
            L.append("")
        # ── Sodya Pinda (Rasi + Graha Gunakara) ──
        if r.sodya_pinda:
            L.append("### Sodya Pinda (Rasi + Graha Gunakara)")
            L.append("")
            L.append("| Planet | Rasi Gunakara | Graha Gunakara | Sodya Pinda |")
            L.append("|---|---:|---:|---:|")
            for sp in r.sodya_pinda:
                L.append(f"| {sp.planet} | {sp.rasi} | {sp.graha} | {sp.total} |")
            L.append("")
            L.append("_Computed from the reduced tables above: each sign's reduced bindus x "
                     "its fixed zodiacal factor (Rasi Gunakara, HPA-26:1149-1153), plus the "
                     "reduced bindus in each graha's occupied sign x its fixed planetary "
                     "factor (Graha Gunakara, HPA-26:1311-1315). The sum is Raman's Sodya "
                     "Pinda by his own naming (ASP-14:196-198); HPA-26 applies it to "
                     "LONGEVITY (the x7/27 Ayurdaya use, HPA-26:1400-1404 / ASP-14:199-201). "
                     "Honesty note, recorded not fudged: on ASP-14's worked Standard "
                     "Horoscope Raman prints Sun 96/86/182 where this pipeline gives "
                     "103/88/191 on his own stated longitudes - the divergence is in HIS "
                     "printed reduced tables (the 1962 book carries known misprints), so the "
                     "engine pins the RULES, anchored on HPA-26's own worked reduction, and "
                     "records this delta._")
            L.append("")

    # ── house-by-house, with pillars + calibration ────────────────────────────
    L.append("## House-by-house reading")
    L.append("")
    L.append(f"_{ROLLUP_RULE} Where the majority of a house's significations disagree with that "
             f"headline, a **Split status** note says so — and where the headline is driven by "
             f"an atlas-proven inverted channel, a **WARNING** is shown inline. Each house "
             f"leads with a **Conclusion** line — Raman's own closing device (essentially "
             f"every worked analysis in HTJAH ends with a \"Conclusion.—\" summation weighing "
             f"house, lord and karaka in free prose, e.g. HTJAH-I:4485, 8513, 8870) — a "
             f"summation of rows shown in full beneath it and in the strength/preponderance "
             f"sections below; nothing new is judged in it. The machine-composed evidence "
             f"chain that used to sit above it is unchanged, and now carries a **Working** "
             f"label where it stands._")
    # Wave-3 (2026-08-18): the verdict-first strip — a 12-row scanning index ABOVE the
    # twelve deep blocks (which follow unchanged, in full). Every cell restates the block
    # it points at; the strip judges nothing.
    _strip = house_strip_rows(r)
    if _strip:
        L.append("")
        L.append("**The twelve houses at a glance** — a scanning index; each row's full "
                 "judgment, evidence and population context follows below, unabridged.")
        L.append("")
        L.append("| # | House | Verdict | Driver | Split status | Running period |")
        L.append("|---|---|---|---|---|---|")
        for _row in _strip:
            _v = f"**{_row.verdict}**" + (" [INVERTED]" if _row.inverted else "")
            _d = f"_{_row.driver}_" if _row.driver else "-"
            _sp = _row.split or "consistent"
            _ti = _row.tier if _row.tier else "not lit"
            L.append(f"| H{_row.house} | {_row.name} | {_v} | {_d} | {_sp} | {_ti} |")
        L.append("")
        L.append("_\"Running period\" is this house's four-tier fructification grade in the "
                 "bhukti running at the reference date (par excellence / ordinary / limited "
                 "/ feeble, HTJAH-I:1592-1596); \"not lit\" means neither period-lord "
                 "influences the house. \"Split status\" repeats the block's own split note; "
                 "\"consistent\" means the majority tenor agrees with the headline._")
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
            # Wave-3 cross-reference: the precedence rules live 400 lines up; point at
            # them AT the moment of confusion, only when a split note actually fired.
            L.append(f"> _{SPLIT_POINTER}_")
        if drv_entry is not None and drv_entry.inverted_warning:
            L.append("")
            L.append(f"> **WARNING**: the driver, _{driver}_, is an atlas-proven INVERTED "
                     f"channel — real cases ran opposite to this reading; treat this house's "
                     f"headline with maximal skepticism.")
            L.append(f"> _{INVERTED_POINTER}_")
        # Wave-3: the PREC-1 pointer, composed from the dashboard's own verdicts — it
        # appears only on the houses whose matter reader and bhava rollup actually differ.
        for _xr in house_dashboard_conflicts(r, mr.house):
            L.append("")
            L.append(f"> _{_xr}_")
        # Wave-3: the H8-style deferral pointer, conditional on the deferred metadata
        # (death_window / decanate_cause) having actually been computed for this house.
        _lp = house_longevity_pointer(r, mr.house)
        if _lp:
            L.append("")
            L.append(f"> _{_lp}_")
        # Wave-3: the Conclusion — the block's best prose — promoted from below the
        # machine-composed evidence chain to the top of the block. MOVE ONLY: the same
        # `house_conclusion` text, rendered once.
        conclusion = house_conclusion(r, mr.house)
        if conclusion:
            L.append("")
            L.append(f"> **Conclusion** — {conclusion}")
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
            # Wave-2 D2 (2026-08-18): the deciding frame, named — the pillar line above
            # always shows LAGNA-frame figures while the reading below may be judged
            # from the Moon frame; naming both reconciles them (HTJAH-I:645-646).
            _frame_ln = house_frame_line(r, mr.house)
            if _frame_ln:
                L.append(f"_**Frame** — {_frame_ln}_")
                L.append("")
            # Wave-2 D4: the running period's four-tier grade for THIS house — the same
            # vimshottari.bhukti_tier vocabulary the Life-narrative computes, re-read
            # where the reader is asking about the house.
            _tier_ln = house_current_tier_line(r, mr.house)
            if _tier_ln:
                L.append(f"_**Current period** — {_tier_ln}_")
                L.append("")
            # computation badges (2026-08-04): REAL counts — evidence, fired rules,
            # distinct sources, and the testimony-support band; never a probability.
            _ht = next((h for h in r.preponderance.houses if h.house == mr.house), None)
            # Rules is deduped by rule id, matching Sources' dedup — counting every fired
            # INSTANCE across significations x frames inflated it under the same visual
            # grammar (H3 read "Rules 38" for ~9 distinct rules; 2026-08-17 fix).
            _rule_ids: set[str] = set()
            _cites: set[str] = set()
            for _sv in pf.significations:
                for _led in (_sv.ledger, *_sv.alt_ledgers):
                    for _fr in (*_led.fired_benefic, *_led.fired_malefic,
                                *_led.fired_neutral):
                        _rule_ids.add(_fr.rule.id)
                        _cites.add(f"{_fr.rule.source.work}:{_fr.rule.source.line}")
            if _ht is not None:
                _band = ("High" if "corrobor" in _ht.status else
                         "Low" if "contest" in _ht.status else "Medium")
                L.append(f"`Evidence {len(_ht.testimonies)}` · `Rules {len(_rule_ids)}` · "
                         f"`Sources {len(_cites)}` · `Support {_band} "
                         f"({_ht.favourable}F/{_ht.adverse}A)`")
                L.append("")
        # Wave-3: the machine-composed evidence chain, unchanged in every character —
        # now LABELLED for what it is, with the Conclusion it used to sit above promoted
        # to the head of the block.
        L.append(f"**Working** — {mr.reading}")
        # Wave-2 D1 (2026-08-18): the chief fired combinations, in Raman's own effect
        # prose with citations — exactly how HTJAH's chapters argue a bhava; previously
        # this chapter rendered only counts (`Rules N`) while the matter monographs
        # printed their rule prose. Selection only (house_chief_combinations); the
        # evidence was always computed, now it is shown.
        _chief = house_chief_combinations(r, mr.house)
        if _chief:
            L.append("")
            L.append("**Chief combinations** (the fired rules that decided, in Raman's "
                     "own words):")
            L.append("")
            for _csig, _cid, _ctext, _ccite in _chief:
                L.append(f"- _{_csig}_: `{_cid}` — \"{_ctext}\" ({_ccite})")
            # Wave-3: encoding-scope artifacts routed out of the client sentences into
            # ONE trailing fine-print line (the marriage monograph's own device, reusing
            # `monographs.split_maintainer_notes`). Routed, never dropped.
            _mnotes = house_maintainer_notes(r, mr.house)
            if _mnotes:
                L.append(f"  - _Encoding-scope notes (maintainer fine print, not "
                         f"readings): {_mnotes}_")
        # item 14 (2026-08-04 content amendment): "Raman writes..." — the driver
        # signification's own cited source, quoted verbatim before the computation.
        if pf is not None:
            _dr = next((sv for sv in pf.significations if sv.verdict == pf.rollup),
                       pf.significations[0] if pf.significations else None)
            if _dr is not None:
                from app.raman_saab.doctrine.significations import SIGNIFICATIONS
                _sig = next((s for s in SIGNIFICATIONS.get(mr.house, ())
                             if s.key == _dr.signification), None)
                if _sig is not None and _sig.source is not None:
                    _q = passage_quote(f"{_sig.source.work}:{_sig.source.line}")
                    if _q:
                        L.append("")
                        L.append(f"> **Raman writes** — \"{_q}\" "
                                 f"({_sig.source.work}:{_sig.source.line}) — and this "
                                 f"chart computes: {mr.verdict} for _{_dr.signification}_.")
        cal = _calibration_lines(cal_reading)
        if cal:
            L.append("")
            L.append("_Population context:_")
            # Wave-3: ONE rollup line above the rows when they repeat — and then every
            # individual row, unchanged (add-only; the rows are never collapsed).
            _rollup = calibration_rollup_line(cal_reading)
            if _rollup:
                L.append(f"  - _{_rollup}_")
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
        L.append("| House | Matter | Verdict | Bhava Bala rank | Bhava Bala (rupas) | SAV bindus |")
        L.append("|---|---|---|---|---:|---|")
        for row in r.house_strength:
            bb_rank = f"{row.bhava_bala_rank} of 12" if row.bhava_bala_rank else "n/a"
            # the rank's own underlying magnitude (Shashtiamsas/60 = rupas) — already in the
            # JSON and the interactive page, previously dropped from this table (2026-08-17).
            bb_rupas = f"{row.bhava_bala / 60.0:.2f}" if row.bhava_bala is not None else "n/a"
            sav_cell = f"{row.sav_bindus} ({row.sav_band})" if row.sav_bindus is not None else "n/a"
            L.append(f"| H{row.house} | {_HOUSE_NAME.get(row.house, '')} | {row.verdict} | "
                     f"{bb_rank} | {bb_rupas} | {sav_cell} |")
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
        # Wave-2 E (2026-08-18, add-only): the witness-class disclosure — a fourth
        # honesty rule beside the three above; the flat counts and every status word
        # derived from them are untouched.
        L.append("_(4) A witness-class tag separates core testimony - the house's own "
                 "lord, karaka and navamsa, the axes Raman's summing-up itself names "
                 "(HTJAH-I:983-991) - from overlay cross-checks (SAV band, Bhava-Bala "
                 "rank, matter-vargas, majority tenor, yoga bearings). The Core column "
                 "restates the same rows as a second count pair; it is Raman's unequal "
                 "weighing made visible, not a new weighting, and it alters nothing. "
                 "Yoga-bearing rows additionally disclose their link: [direct - "
                 "own/occupy], the factor his worked charts demonstrate, vs "
                 "[aspect-derived - admitted extension]._")
        L.append("")
        L.append("| House | Matter | Verdict | For | Against | Neutral | Absent | "
                 "Core (For/Against) | Preponderance | Status |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for ht_ in r.preponderance.houses:
            L.append(f"| H{ht_.house} | {_HOUSE_NAME.get(ht_.house, '')} | {ht_.verdict} | "
                     f"{ht_.favourable} | {ht_.adverse} | {ht_.neutral} | {ht_.absent} | "
                     f"core: {ht_.core_favourable} for / {ht_.core_adverse} against | "
                     f"{ht_.preponderance} | {ht_.status} |")
        L.append("")
        for ht_ in r.preponderance.houses:
            detail = "; ".join(f"{t.name} [{t.klass}] {t.value}" for t in ht_.testimonies
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
    L.extend(_method_preamble("longevity"))
    L.append("_Raman's order: first establish the band by combination (Balarishta / Alpayu / "
             "Madhyayu / Purnayu), THEN fix the period by the marakas (HTJAH-II:4465-4472). The "
             "numeric span is a cross-check, never a prediction of death._")
    L.append("")
    if r.balarishta is not None:
        bal = ("applies" if r.balarishta.applies and not r.balarishta.cancelled
               else "cancelled" if r.balarishta.cancelled else "does not apply")
        L.append(f"1. **Balarishta** (early-childhood danger): {bal}"
                 + (f" — {'; '.join(r.balarishta.reasons)}" if r.balarishta.reasons else ""))
        # Wave-2 (2026-08-18, item 5a): the clear case discloses WHAT was screened —
        # a re-read of the primitive's own checked conditions, so the reader can see
        # the method worked rather than take "does not apply" on faith.
        if not r.balarishta.applies:
            from app.raman_saab.primitives.balarishta import screened_conditions
            screened = "; ".join(f"{label} ({cite})"
                                 for label, cite in screened_conditions())
            L.append(f"   - screened: {screened} - none present")
    if s.longevity_combos:
        L.append("2. **Band by combination** (HTJAH-II):")
        for lcx in s.longevity_combos:
            L.append(f"   - {lcx}")
    # class label harmonised (Wave-2 item 5b): "Purnayu (purna band)", the combos'
    # own Sanskrit form beside the class word — one reading, one vocabulary; and the
    # old developer-speak coda ("the engine's own health layer defers lifespan")
    # replaced with reader language (item 5c).
    L.append(f"3. **Numeric cross-check (Ayurdaya)**: about **{round(r.longevity_years)} years** "
             f"({lon_y}y {lon_mo}m {lon_d}d) — class **{longevity_band_label(r.longevity_class)}"
             f"**. Treat as a band, not a date: this report never converts the band into a "
             f"date.")
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
            # each graha now names WHY it qualified (the clause recorded at assignment —
            # 2026-08-17 report-critique fix; previously computed and discarded).
            names = []
            for u in mp.units:
                if u.tier != tier:
                    continue
                why = format_maraka_reasons(u.reasons)
                names.append(f"{u.graha} ({why})" if why else u.graha)
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
            # tier addends spelled out (2026-08-17): "6 = Saturn 3 + Venus 3" — the same
            # per-lord weights the death-window summed, so the number is checkable.
            tier_cell = f"{c.score} = {c.score_parts}" if c.score_parts else str(c.score)
            L.append(f"| {c.maha}/{c.antar} | "
                     f"{_outlook_window_label(c.window_start_jd, c.window_end_jd)} | "
                     f"{_outlook_window_label(c.overlap_start_jd, c.overlap_end_jd)} | "
                     f"{_SIGN_NAME[c.sign]} | {tier_cell} |")
        L.append("")

    # ── health & vulnerability read-out (v17, pure re-read of existing verdicts) ─────
    if r.health_readout.rows:
        h = r.health_readout
        L.append("## Health & vulnerability read-out")
        L.append("")
        L.extend(_method_preamble("health_readout"))
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
        # Wave-2 (item 5a, shared with Longevity): disclose the screen on the clear case.
        if not a.balarishta_applies:
            from app.raman_saab.primitives.balarishta import screened_conditions
            _screened = "; ".join(f"{label} ({cite})"
                                  for label, cite in screened_conditions())
            L.append(f"  - screened: {_screened} - none present")
        L.append(f"- **Raman's antidotes (verbatim)** — "
                 f"{_quote_or_absent(a.antidote_quote, a.antidote_cite)}")
        if a.bhangas:
            for p, dig, eff in a.bhangas:
                L.append(f"- **Bhanga** — {p}: {dig} cancelled to effective {eff} "
                         f"(neecha bhanga)")
        # Wave-2 (item 5d): the two no-bhanga cases distinguished — an uncancelled
        # debility is a standing affliction; no debility at all raises no question.
        uncx = getattr(a, "uncancelled_debilities", ())
        if uncx:
            for p in uncx:
                L.append(f"- **Bhanga** — {p} is debilitated and NO cancellation "
                         f"operates: the debility stands (no neecha bhanga)")
        if not a.bhangas and not uncx:
            L.append("- **Bhanga** — no planet is debilitated in this chart, so no "
                     "cancellation question arises")
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
    # Wave-1 (2026-08-17): the lord_quality delivery tags were computed for every activation
    # row but dropped by this renderer — now shown per row (HTJAH-II:10004-10008: the activated
    # house's result is good/bad per the lord's strength; the licensed antidote to a wall of
    # par-excellence rows all reading alike).
    L.append("")
    L.append("**Delivery tags** (per lit house): how well each activating period-lord delivers "
             "what it lights - the same strength/dignity read the snapshot voice uses "
             "(HTJAH-II:10004-10008): well / mixed / poorly / unknown. 'MD well, AD mixed' "
             "means the Mahadasha lord delivers well and the bhukti lord mixed; a limited row "
             "carries only its AD tag, a feeble row only its MD tag.")

    # Wave-2 (2026-08-18): the influence BASIS — derive the tier, don't assert it. Raman
    # names the factor ("Saturn, as lord of the 2nd, aspecting its lord..."); the engine
    # knew it inside timer_set but flattened it away. `timer_roles` (role-preserving, pinned
    # equal to timer_set by test) restores the derivation per lit house.
    L.append("")
    L.append("**Influence basis** (per lit house, in square brackets): BY WHICH of Raman's "
             "enumerated factors (HTJAH-I:1586-1596) each period-lord influences the house - "
             "owns / karaka / occupies / aspects house / conjoins lord / aspects lord / lord "
             "from Moon / node of a timer's sign. 'via H11' (and 2/9/12 likewise) marks a "
             "lord reaching the house only through its allied event house (gains 2/11, "
             "travel 9/12), stated rather than implied.")
    _basis_table = influence_basis_table(r.chart)

    def _delivery(a) -> str:
        bits: list[str] = []
        if a.md_activates:
            bits.append(f"MD {a.md_quality.tag}")
        if a.antar_activates and a.antar_quality is not None:
            bits.append(f"AD {a.antar_quality.tag}")
        return ", ".join(bits) or "n/a"

    def _basis(a) -> str:
        bits: list[str] = []
        if a.md_activates:
            bits.append(f"MD {influence_basis(_basis_table, a.house, a.md_lord)}".rstrip())
        if a.antar_activates and a.antar_lord is not None:
            bits.append(f"AD {influence_basis(_basis_table, a.house, a.antar_lord)}".rstrip())
        return f" [{'; '.join(bits)}]" if bits else ""

    cur_md: Optional[str] = None
    for tp in r.timeline.periods:
        rows, maha, antar = tp.activated, tp.period.maha, tp.period.antar
        if maha != cur_md:
            cur_md = maha
            L.append("")
            L.append(f"### {cur_md} Mahadasha")
        associated, raw = graded_buckets(tp, r.chart)     # ONE grading implementation
        buckets = {k: [f"H{a.house} {a.natal_verdict} ({_delivery(a)}){_basis(a)}" for a in v]
                   for k, v in raw.items()}
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

    # ── Wave-1: pratyantar drill-down for the CURRENT bhukti (third Vimshottari level) ──
    if r.pratyantar_now:
        L.append("")
        L.append("### Pratyantardasha drill-down (current bhukti)")
        L.append("")
        L.append("_The third level of the Vimshottari hierarchy, for the bhukti running now "
                 "only - the same proportional lord-years/120 split, one level down, in JD "
                 "space. Raman names all three levels as carriers of a house's results: \"as "
                 "lords of the Dasas (main-periods), as lords of Bhuktis (Sub-periods) or as "
                 "lords of the Antaras\" (HTJAH-II:668-702). The running pratyantar is "
                 "marked; each span reads in the same indication idiom as the bhukti rows "
                 "above._")
        L.append("")
        for pr_ in r.pratyantar_now:
            now = "  **<- now**" if pr_.start_jd <= r.ref_jd < pr_.end_jd else ""
            L.append(f"- {pr_.maha} MD / {pr_.antar} AD / **{pr_.pratyantar} PD** "
                     f"({_jd_to_date(pr_.start_jd)} .. {_jd_to_date(pr_.end_jd)}){now}")
        L.append("")

    # ── Wave-1: the Chara dasha sequence, dated (was undated prose in the Soul reading) ──
    if r.chara_sequence:
        L.append("")
        L.append("### Chara dasha (Jaimini) - dated sequence")
        L.append("")
        L.append("_The parallel sign-based dasha the Chart signature chip names (see "
                 "glossary). Dates are plain JD arithmetic from birth (period years x "
                 "365.2425 days) over the KN Rao sequence already encoded in "
                 "`primitives/chara_dasha`; the 12-sign cycle repeats. The running sign is "
                 "marked. No result judgment attaches here - matters are read from "
                 "Vimshottari above._")
        L.append("")
        for cs in r.chara_sequence:
            now = "  **<- now**" if cs.current else ""
            L.append(f"- {_SIGN_NAME[cs.sign]} - {cs.years}y "
                     f"({_jd_to_date(cs.start_jd)} .. {_jd_to_date(cs.end_jd)}){now}")
        L.append("")

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
        # Wave-2 (2026-08-18): the synthesis sentences Raman's own transit paragraphs speak —
        # one per row, a deterministic join of the columns above (the table stays in full).
        L.append("**Read as sentences** - the same rows joined the way Raman narrates a "
                 "transit (station + support + vedha in one breath); every clause restates "
                 "a column above, no new judgment:")
        L.append("")
        for g in r.gochara:
            L.append(f"- {gochara_synthesis_sentence(g)}")
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

        # ── Wave-1: the ADVERSE windows the same computation always produced (previously
        # only the favourable half was rendered — REPORT COMPLETENESS repair, add-only) ──
        bad = adverse_transit_windows(r)
        if bad:
            lo_y2 = _jd_month_year(r.ref_jd - r.window_back * 365.2425)[-4:]
            hi_y2 = _jd_month_year(r.ref_jd + r.window_forward * 365.2425)[-4:]
            L.append(f"### Adverse transit windows ({lo_y2} to {hi_y2})")
            L.append("")
            L.append("**In simple terms:** the mirror of the favourable table above - the "
                     "stretches when Jupiter, Saturn, Rahu or Ketu sits in a house from your "
                     "Moon that the classical Gochara scheme does NOT count as supportive for "
                     "that planet. The same computation always produced these windows; only "
                     "the favourable half was shown before. Honest labels: 'what it concerns' "
                     "is the same life-area that planet governs, here classically unsupported "
                     "rather than supported; 'mitigation' applies Raman's own proportion law - "
                     "the planet's bindus in the transited sign neutralise the evil to that "
                     "extent (\"neutralises the evil to the extent of 75%\" at 6 of 8 bindus, "
                     "ASP-13:416); Vedha (interference) is defined for favourable transits "
                     "only, so that column reads '-' here - not computed, not zero. Per Raman "
                     "a transit stays secondary to the Dasha (HTJAH-II:4679): read an adverse "
                     "window as reduced transit support during whatever the running period "
                     "already indicates, never a stand-alone prediction.")
            L.append("")
            L.append("| Planet | Window | What it concerns | Mitigation (own AV bindus) | "
                     "Interference |")
            L.append("|---|---|---|---|---|")
            for planet_b, seg_b, bav_b in bad:
                mit = (f"{bav_b}/8 of the evil neutralised" if bav_b is not None
                       else "- (node: no classical Ashtakavarga)")
                L.append(f"| {planet_b} | "
                         f"{_outlook_window_label(seg_b.start_jd, seg_b.end_jd)} | "
                         f"{_PLANET_THEME[planet_b]} | {mit} | - |")
            L.append("")

    # ── Wave-1: Sade-Sati phase windows, dated (method-only; no result doctrine) ──
    if r.sade_sati_phases:
        L.append("### Sade-Sati phase windows (Saturn from the natal Moon)")
        L.append("")
        L.append("**In simple terms:** Sade-Sati is Saturn's roughly 7.5-year passage across "
                 "the 12th, 1st and 2nd signs from the natal Moon (see glossary). Below are "
                 "the dated phase spans of the episode nearest the reference date, with the "
                 "current position marked. **Method note (dates only):** no Sade-Sati x Moon "
                 "result doctrine is on record in the encoded corpus, so no intensity or "
                 "result reading is offered - the dates are plain gochara arithmetic "
                 "(transiting Saturn's sign against the natal Moon sign), at the outlook's "
                 "~week sampling resolution; a retrograde re-entry shows as its own dated "
                 "row.")
        L.append("")
        for ph in r.sade_sati_phases:
            now = "  **<- now**" if ph.current else ""
            L.append(f"- **{ph.phase}** - Saturn in {_SIGN_NAME[ph.sign]}: "
                     f"{_outlook_window_label(ph.start_jd, ph.end_jd)}{now}")
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

    # ── Wave-2 (2026-08-18): the ADVERSE half of the same cross-check — the favourable
    # builder filtered `if not seg.gochara_good: continue` by construction, a one-sided
    # table; Raman's blending doctrine reads obstruction too (HPA-34:369-381). The
    # favourable table above is untouched; this mirrors it, method-only.
    if r.dasha_transit_adverse:
        L.append("### Adverse dasha x transit confluence")
        L.append("")
        L.append("**In simple terms:** the mirror of the table above - the stretches where a "
                 "running MD or AD lord is, at the same time, transiting a station from your "
                 "Moon that the classical Gochara scheme counts AGAINST that planet. Raman's "
                 "blending doctrine weighs obstruction as well as reinforcement (\"the "
                 "influences of birth chart are blended with those of Gochara and "
                 "Ashtakavarga, together with Vedha or obstructing forces\", HPA-34:369-381) "
                 "- so the two tables are the two halves of one method statement: reduced "
                 "transit support during what the period already indicates, never a "
                 "stand-alone prediction. 'Mitigation' applies Raman's own proportion law "
                 "(the planet's bindus in the transited sign neutralise the evil to that "
                 "extent, ASP-13:416); Vedha (interference) is defined for favourable "
                 "transits only, so that column reads '-' here - not computed, not zero.")
        L.append("")
        L.append("_Same coverage and sampling honesty as above: only Jupiter, Saturn, Rahu "
                 "and Ketu are tracked long-range, so a period led by a fast planet has no "
                 "row here by construction; window edges carry the outlook's coarse ~week "
                 "sampling - method windows, not exact dates._")
        L.append("")
        L.append("| Period | Planet | Overlap | What it concerns | "
                 "Mitigation (own AV bindus) | Interference |")
        L.append("|---|---|---|---|---|---|")
        for c in r.dasha_transit_adverse:
            mit = (f"{c.bav_bindus}/8 of the evil neutralised" if c.bav_bindus is not None
                   else "- (node: no classical Ashtakavarga)"
                   if c.planet in ("Rahu", "Ketu") else "- (not computed)")
            L.append(f"| {c.role} | {c.planet} | "
                     f"{_outlook_window_label(c.overlap_start_jd, c.overlap_end_jd)} | "
                     f"{_PLANET_THEME[c.planet]} | {mit} | - |")
        L.append("")

    # ── muhurtha pointer (2026-08-17, report-critique item: the one interactive-only surface).
    # Wording deliberately avoids the walled subsystem's module name (the PRASNA/MUHURTHA
    # firewall test scans this module's SOURCE TEXT for it) — this is a prose pointer to the
    # interactive page, not an import, and must never read as one.
    L.append("_Live companion not reproducible here: the interactive report page carries an "
             "on-demand \"Today for you (Muhurtha)\" panel — Raman's Muhurtha rules judging "
             "the CURRENT day (tarabala/chandrabala, Rahu Kalam, Durmuhurtha) against this "
             "native's own janma nakshatra and rasi, computed live at view time. A static "
             "report is cast once; that panel is recast every day — open the interactive "
             "page for it._")
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
        L.extend(_method_preamble("profession"))
        L.append("**In simple terms:** Raman derives profession from several angles; "
                 "this section runs every encoded one and counts where they converge — "
                 "a deterministic overlap count, never a new judgment.")
        L.append("")
        L.append("| Derivation | Resolves to | Raman's vocation words | Cite |")
        L.append("|---|---|---|---|")
        for src in pf.sources:
            note = f" _{src.note}_" if src.note else ""
            L.append(f"| {src.source} | {src.key} | {src.trades}{note} | {src.cite} |")
        # Wave-2 (item 3a): the D-10 row the preamble promises — the computed Dasamsa
        # reading re-read as corroboration (deliberately NOT a convergence vote).
        d10 = getattr(pf, "dasamsa_row", ())
        if d10:
            L.append(f"| {d10[0]} | {d10[1]} | {d10[2]} | {d10[3]} |")
        if pf.mode_split:
            L.append("")
            L.append("- **H10 mode split** — "
                     + "; ".join(f"{k}: {v}" for k, v in pf.mode_split))
        if pf.convergent:
            L.append("- **Convergent trades** (named by 2+ derivations) — "
                     + ", ".join(f"{w} ({n})" for w, n in pf.convergent))
        # Wave-2 (item 3c): same-graha disclosure — several "votes" that are one
        # planet under several hats are not independent confirmations.
        if getattr(pf, "convergence_note", ""):
            L.append(f"- **One planet, several hats** — {pf.convergence_note}")
        # Wave-2 (item 3b): H10 activations — the same timeline lens the marriage
        # monograph shows for H7 (a timing lens, never a promise).
        if getattr(pf, "h10_windows", ()):
            L.append("- **H10 activations in the window** (a timing lens, never a "
                     "promise) — " + "; ".join(pf.h10_windows))
        L.append("")

    # ── wealth chapter (v24 — the channels, not a single verdict) ─────────────
    if r.wealth is not None:
        w = r.wealth
        L.append("## Wealth chapter")
        L.append("")
        L.extend(_method_preamble("wealth"))
        L.append("**In simple terms:** not one wealth verdict but the CHANNELS — how the "
                 "method reads earning, accumulating, inheriting, speculating, and where "
                 "expansion periods fall. Every row re-reads a judged signification or a "
                 "cited source-of-gains table.")
        L.append("")
        # Wave-2 (item 4d): the population-context column the signification rows
        # already carry in the House-by-house section — re-read per row ("-" where
        # a row is a source-of-gains lookup, not a calibrated signification).
        L.append("| Channel | Reading | Cite | Population context |")
        L.append("|---|---|---|---|")
        for row in w.rows:
            ctx = getattr(row, "context", "") or "-"
            L.append(f"| {row.channel} | {row.reading} | {row.cite} | {ctx} |")
        L.append("")
        # Wave-2 (item 4a): the classical first question — Dhana yogas and Daridra,
        # fired or absent, stated explicitly against the chart's own fired set.
        if getattr(w, "dhana_row", ""):
            L.append(f"- **Dhana / Daridra yogas** — {w.dhana_row}")
        # Wave-2 (item 4b): the wealth lords' computed conditions.
        for lc in getattr(w, "lord_conditions", ()):
            L.append(f"- **Lord condition** — {lc}")
        if w.expansion_periods:
            L.append("- **Periods of expansion** (H2/H11 activated at ordinary tier or "
                     "better — a timing lens, never a promise): "
                     + "; ".join(w.expansion_periods))
            # Wave-2 (item 4c): the chapter applies its own calibration standard to
            # itself when the expansion lens separates nothing.
            if getattr(w, "expansion_note", ""):
                L.append(f"  - _Self-disclosure: {w.expansion_note}._")
            L.append("")

    # ── marriage monograph (v25) ──────────────────────────────────────────────
    if r.marriage is not None:
        from app.raman_saab.monographs import MARRIAGE_INTRO as _MI
        m = r.marriage
        L.append("## Marriage monograph")
        L.append("")
        L.extend(_method_preamble("marriage"))
        L.append(f"**The 7th house's scope (Raman verbatim):** "
                 f"{_quote_or_absent(m.seventh_covers, f'HTJAH-II:{_MI[0]}')}")
        L.append("")
        L.append(f"- **Headline (unchanged H7 verdict)** — {m.verdict}")
        # Wave-2 (item 1a): the shipped B3 distinction surfaced where the client
        # looks — happiness of the union vs the partner's own longevity are separate
        # H7 significations and are shown apart.
        if getattr(m, "marital_happiness", None) or getattr(m, "coverture", None):
            L.append(f"- **Marital happiness: {m.marital_happiness or 'not judged'}; "
                     f"the partner's own longevity (coverture): "
                     f"{m.coverture or 'not judged'}** — two separate 7th-house "
                     f"significations, judged separately (re-read from House 7)")
        if m.lord_period_text:
            L.append(f"- **The 7th lord in house {m.lord_placement_house} (Raman "
                     f"verbatim, his periods)** — \"{m.lord_period_text}\" "
                     f"(HTJAH-II:710)")
        if m.spouse_sign_text:
            L.append(f"- **The partner's significator in its sign (HPA-22)** — "
                     f"\"{m.spouse_sign_text[0]}\" ({m.spouse_sign_text[1]})")
        if m.upapada:
            L.append(f"- **Upapada** — {m.upapada}")
        # Wave-2 (item 1b): the Kuja-dosha narration — the rule's own per-frame
        # evaluation (HTJAH-II:2579-2622), disclosed step by step.
        if getattr(m, "kuja_narration", ()):
            L.append("- **Kuja (Mangal) dosha, checked frame by frame "
                     "(HTJAH-II:2579-2622)** — the rule's own evaluation, disclosed:")
            for kn in m.kuja_narration:
                L.append(f"  - {kn}")
        if m.fired_kalatra:
            # Wave-2 (items 1d/1e): fortified-first grouping with a one-line tally,
            # and maintainer notes routed to trailing fine print (still rendered —
            # ADD-ONLY routing, and the raw text is unchanged in the data/JSON).
            from app.raman_saab.monographs import split_maintainer_notes
            _fort = [x for x in m.fired_kalatra if x[0] == "fortified"]
            _affl = [x for x in m.fired_kalatra if x[0] == "afflicted"]
            _rest = [x for x in m.fired_kalatra
                     if x[0] not in ("fortified", "afflicted")]
            L.append(f"- **Kalatra rules firing in THIS chart** (of the 50 encoded; "
                     f"{len(_fort)} fortified, {len(_affl)} afflicted"
                     + (f", {len(_rest)} other" if _rest else "") + "):")
            _fine: list[str] = []
            for branch, text, cite in (*_fort, *_affl, *_rest):
                clean, mnote = split_maintainer_notes(text)
                L.append(f"  - ({branch}) {clean} ({cite})")
                if mnote:
                    _fine.append(f"{cite}: {mnote}")
            if _fine:
                L.append("  - _Encoding-scope notes (maintainer fine print, not "
                         "readings): " + " | ".join(_fine) + "_")
        L.append(f"- **Timing doctrine (Raman verbatim)** — "
                 f"{_quote_or_absent(m.timing_navamsa, 'HTJAH-II:853')}")
        if m.timing_windows:
            L.append(f"- **H7 activations in the window** — {'; '.join(m.timing_windows)}")
        # Wave-2 (item 1c): the method's own favourable Jupiter windows touching the
        # 7th (from the Moon) — a pure filter of the Gochara outlook already computed
        # above; no new doctrine claim, a timing lens in the classical idiom.
        if getattr(m, "jupiter_h7_windows", ()):
            L.append("- **Jupiter transits touching the 7th (from the Moon)** — the "
                     "method's own favourable-transit windows (the Gochara outlook "
                     "above) in which Jupiter occupies the 7th from the Moon: "
                     + "; ".join(m.jupiter_h7_windows))
        if m.children_after:
            L.append(f"- **Children (H5)** — {m.children_after}")
        L.append("")
        L.append("_On separation and loss of the partner, the method's own statements — "
                 "quoted, not composed; A STATEMENT OF THE METHOD, NOT A PREDICTION "
                 "(this project's validation measured no real-outcome signal):_")
        L.append("")
        L.append(f"> {_quote_or_absent(m.separation_quote, 'HTJAH-II:887')}")
        L.append("")

    # ── children chapter (v26) ────────────────────────────────────────────────
    if r.children is not None:
        c = r.children
        L.append("## Children chapter")
        L.append("")
        L.extend(_method_preamble("children"))
        L.append(f"- **Headline (unchanged H5 verdict)** — {c.verdict}")
        for key, v in c.significations:
            L.append(f"- **{key}** — {v}")
        # Wave-2 (item 2b): Jupiter (putrakaraka) condition — computed facts only.
        if getattr(c, "putrakaraka_line", ""):
            L.append(f"- **{c.putrakaraka_line}**")
        # Wave-2 (item 2a): the D-7 corroboration the preamble promises — a re-read
        # of the Saptamsa section's own computed structures.
        if getattr(c, "d7_corroboration", ""):
            L.append(f"- **Saptamsa (D-7) corroboration** — {c.d7_corroboration}")
        # Wave-2 (item 2c): the doctrine-reviewed classical-shorthand reframe note,
        # copied VERBATIM from the D-7 section and placed BEFORE the fired rules —
        # "loses a number of children" must never be the first thing a parent reads.
        if getattr(c, "reframe_note", ""):
            L.append(f"- _{c.reframe_note}_")
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
        L.append(f"> {_quote_or_absent(c.combos_quote, 'HTJAH-I:5179')}")
        L.append("")
    if s.deeptadi:
        from app.raman_saab.plain_terms import TERM_GLOSS as _TG
        L.append("")
        L.append("## Deeptadi avasthas (each graha's result-state, HPA Ch.7)")
        L.append("")
        L.append("_**Avastha = the planet's state, its mood** — the same engine can run "
                 "bright or exhausted, and the state colours HOW a planet delivers what "
                 "it promises. Each state below carries its plain equivalent._")
        L.append("")
        L.append(", ".join(s.deeptadi))
        L.append("")
        _states = sorted({x.split(" ", 1)[1] if " " in x else x for x in s.deeptadi}
                         & set(_TG))
        for st in _states:
            t = _TG[st]
            L.append(f"- **{st}** — {t.plain}. {t.analogy}. _{t.why_it_matters}._")
        # per-planet testimony table (2026-08-18 report-critique: from trivia to
        # testimony) — Raman's own stated result per state (HPA Ch.7:46-83, already
        # encoded in deeptadi.RESULTS), the houses each planet rules/occupies, and
        # every SECONDARY state disclosed (deeptadi.states_all; state() untouched).
        _dt_rows = deeptadi_table(r)
        if _dt_rows:
            L.append("")
            L.append("_Each state read as testimony — Raman's stated result beside the "
                     "houses the planet answers for. Where a planet matches more than "
                     "one state, the secondary state is disclosed in parentheses; the "
                     "dignity-first priority order names the dominant one. Rahu/Ketu "
                     "are always retrograde, hence perpetually Sakta — definitional, "
                     "not a strength claim._")
            L.append("")
            L.append("| graha | state | Raman's stated result (HPA Ch.7:46-83) | "
                     "rules / occupies |")
            L.append("|---|---|---|---|")
            for _dt_name, _dt_state, _dt_result, _dt_role in _dt_rows:
                L.append(f"| {_dt_name} | {_dt_state} | {_dt_result} | {_dt_role} |")
        # Baladi/Jagradadi (2026-08-17 report-critique fix): the judge computes these per
        # planet and uses them to modulate verdict INTENSITY (house_template: a Mrita/
        # Sushupti deliverer demotes the degree one step) — computed and used, previously
        # never shown. Read-only re-read via the judge's own accessor; no verdict touched.
        from app.raman_saab.judges.house_template import baladi_jagradadi_states
        _bj = baladi_jagradadi_states(r.chart)
        if _bj:
            L.append("")
            L.append("_Baladi (ageing, by degree-in-sign) and Jagradadi (consciousness, by "
                     "incoming drishti) states — the judge's intensity dial: a house whose "
                     "deliverers sit in Mrita/Sushupti has its verdict DEGREE demoted one "
                     "step (never the verdict itself). Provenance: CLASSICAL_NONCITABLE "
                     "(Phaladeepika Ch.3 Sl.3/Sl.10/Sl.20; BPHS Ch.1 Sl.14-16) — outside "
                     "Raman's own canon, shown because the judge consumes it._")
            L.append("")
            L.append("| graha | Baladi (ageing) | Jagradadi (consciousness) |")
            L.append("|---|---|---|")
            for _n, _p in planet_rows(r.chart):
                if _n in _bj:
                    L.append(f"| {_n} | {_bj[_n]['baladi']} | {_bj[_n]['jagradadi']} |")
    if s.karakamsa_reading:
        L.append("")
        L.append("## Jaimini Karakamsa (the soul's inclination)")
        L.append("")
        # Wave-2 (2026-08-18): header context BEFORE the sutra fragments — the reader meets
        # whose navamsa seat this is (the computed AK + Karakamsa sign, re-read from the
        # chart signature) before Jaimini's indication lines. Pure re-read, no new judgment.
        L.append(f"_Context: the Atmakaraka (soul-planet) of this chart is **{s.atmakaraka}**; "
                 f"its navamsa seat - the Karakamsa - is **{s.karakamsa}**. The lines below "
                 f"are Jaimini's inclination indications for the grahas associated with that "
                 f"seat (JS 1.2 Su.14-22)._")
        L.append("")
        for line in s.karakamsa_reading:
            L.append(f"- {line}")
        L.append("")
        # Navigation only (Wave-2): the dated Chara sequence and this Karakamsa reading are
        # two halves the reader may hold together; the Studies-in-Jaimini passage that READS
        # karakamsa indications through the running chara period is corpus-gated and is NOT
        # composed here — this line points, it does not pair doctrinally.
        L.append("_See also: the dated Chara dasha (Jaimini) sequence under the "
                 "Life-narrative section above, and the full Karakamsa reading in Soul & "
                 "destiny below - cross-references only; the classical passage pairing the "
                 "two is corpus-gated and not composed here._")

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
        # Wave-2 (2026-08-18): one-sentence domain RE-READS, not the embedded full ASCII
        # blocks the chapter previously duplicated. REPORT COMPLETENESS holds by
        # construction: the full D-20/D-60 blocks still render, untrimmed, at their own
        # home in the Divisional deep-reads section above — nothing is hidden, this
        # chapter now points instead of pasting.
        if kv.d20_core:
            L.append(f"- **D-20 Vimsamsa (spiritual) - domain re-read** — {kv.d20_core}")
        if kv.d60_core:
            L.append(f"- **D-60 Shashtiamsa (totality) - domain re-read** — {kv.d60_core}")
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
    # the plain-terms layer (2026-08-04): four-field entries — plain name, analogy,
    # why it matters, example — vocabulary only, never new astrology.
    from app.raman_saab.plain_terms import TERM_GLOSS as _PT
    L.append("")
    L.append("### In plain terms (every technical word, with why it matters)")
    L.append("")
    for term in sorted(_PT):
        t = _PT[term]
        line = (f"- **{term}** — {t.plain}. _{t.analogy}._ "
                f"**Why it matters:** {t.why_it_matters}.")
        if t.example:
            line += f" _Example: {t.example}._"
        L.append(line)

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
    if n.forward_horizon:
        L.append(f"- **Forward horizon** (a period indication, not an event): "
                 f"{n.forward_horizon}")

    # ── aptitude, intelligence & work style (v33 — pure re-read) ──────────────
    if r.aptitude is not None:
        ap = r.aptitude
        L.append("")
        L.append("## Aptitude, intelligence & work style")
        L.append("")
        L.extend(_method_preamble("aptitude"))
        L.append(f"_{ap.woven}_")
        L.append("")
        if ap.intellect_verdict:
            L.append(f"- **Intellect (H5, Jupiter karaka)** — {ap.intellect_verdict} "
                     f"(HTJAH-I:5012)")
        for rid, text, cite in ap.intellect_fired:
            L.append(f"- **Fired intellect combo** [{rid}] — {text} ({cite})")
        L.append(f"- **Mercury (buddhi)** — {ap.mercury_state}")
        if ap.mercury_house_text:
            L.append(f"- **Mercury in its house (Raman verbatim)** — "
                     f"\"{ap.mercury_house_text[0]}\" ({ap.mercury_house_text[1]})")
        if ap.mercury_sign_text:
            L.append(f"- **Mercury in its sign (Raman verbatim)** — "
                     f"\"{ap.mercury_sign_text[0]}\" ({ap.mercury_sign_text[1]})")
        for rid, text, cite in ap.moon_mind_fired:
            L.append(f"- **The Moon's mental disposition** [{rid}] — {text} ({cite})")
        if ap.jupiter_state:
            L.append(f"- **Jupiter (intellect karaka)** — {ap.jupiter_state}")
        if ap.courage_verdict:
            L.append(f"- **Courage / initiative (H3)** — {ap.courage_verdict} "
                     f"(HTJAH-I:3324)")
        if ap.trade_indication:
            lord, disp, trade = ap.trade_indication
            L.append(f"- **Navamsa-dispositor trade** — 10th lord {lord}, dispositor "
                     f"{disp}: {trade} (HTJAH-II:10249)")
        if ap.tenth_sign_profile:
            L.append(f"- **10th-sign profile** — sign {ap.tenth_sign_profile[0]}: "
                     f"{ap.tenth_sign_profile[1]} (HTJAH-II:10340)")
        if ap.strongest_affinity:
            L.append(f"- **Strongest planet's field** — {ap.strongest_affinity[0]}: "
                     f"{ap.strongest_affinity[1]} (HTJAH-II:10249)")
        for key, verdict in ap.mode_split:
            L.append(f"- **H10 mode: {key}** — {verdict}")
        if ap.tenth_lord_state:
            L.append(f"- **10th lord's condition** — {ap.tenth_lord_state}")
        if ap.saturn_state:
            L.append(f"- **Saturn's condition** — {ap.saturn_state}")
        if ap.mars_state:
            L.append(f"- **Mars's condition** — {ap.mars_state}")
        if ap.style_modern:
            from app.raman_saab.planet_biographies import MODERN_BANNER
            L.append(f"- **Modern keywords** [{MODERN_BANNER}] — "
                     f"{'; '.join(ap.style_modern)}")

    # ── footer ────────────────────────────────────────────────────────────────
    L.append("")
    L.append("---")
    L.append(f"_Italicised population context is EMPIRICAL_ASTRODATABANK provenance (n="
             f"{pop:,}) - explicitly not Raman. {_VALIDITY}_")
    return _fold_ascii("\n".join(_inject_plain_layer(L)))


#: The ten SECTION_METHOD chapters added 2026-08-17 whose preambles are injected
#: generically here (the original eight are emitted at their own call sites and
#: must NOT be duplicated by this pass).
_INJECTED_PREAMBLE_IDS: frozenset[str] = frozenset(
    {"yogas", "timeline", "shadbala", "ashtakavarga", "gochara",
     "divisional", "soul", "ruler", "maraka", "karmic"})


def _inject_plain_layer(lines: list[str]) -> list[str]:
    """Reframe part 2 (2026-08-17): under each section heading, add the section_meta
    plain-language subtitle + the reader's question, and (for the ten chapters whose
    SECTION_METHOD entries postdate the per-site wiring) the method preamble.

    Add-only by construction: the pass inserts prose AFTER the first line carrying each
    contract md_marker — it emits no ``## `` lines, so the frozen markers, the
    first-occurrence order test, and the guard-slice cuts are all untouched. Subtitle
    wording is _FORBIDDEN_RE-guarded by tests/raman_saab/test_section_meta.py."""
    from app.raman_saab.section_meta import SECTION_META
    blocks: list[tuple[str, list[str]]] = []
    for spec in SECTION_CONTRACT:
        if not spec.md_marker or not spec.md_marker.startswith("## "):
            continue
        m = SECTION_META.get(spec.section_id)
        if m is None:
            continue
        block = [f"*{m.subtitle_en}* — **Answers:** {m.answers_en}", ""]
        if spec.section_id in _INJECTED_PREAMBLE_IDS:
            block += _method_preamble(spec.section_id)
        blocks.append((spec.md_marker, block))
    blocks.sort(key=lambda t: -len(t[0]))     # longest marker first: no prefix mis-match
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        out.append(line)
        for marker, block in blocks:
            if marker not in seen and line.startswith(marker):
                seen.add(marker)
                out.append("")
                out.extend(block)
                break
    return out


def _fold_ascii(s: str) -> str:
    """ASCII-safe, but FOLD Sanskrit diacritics to base letters (Navamsa, karaka) rather than
    blanking them to '?' — the varga renderers emit UTF-8 IAST that a raw ascii-replace mangles."""
    import unicodedata

    from app.raman_saab.render import _ascii
    folded = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return _ascii(folded)
