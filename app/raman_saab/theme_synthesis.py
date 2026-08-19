"""The integrated-interpretation (theme-synthesis) layer — a READ-ONLY overlay.

The engine answers "what does each section say?" well; this layer answers "what does the
whole horoscope say when the sections are read together?". It is built LAST in
``build_detailed_report`` and consumes only finished ``DetailedReport`` fields — it never
re-judges a house, never re-runs Shadbala, never recomputes a dasha date. Every synthesized
claim is a re-read of an authoritative verdict or a corroborating measurement, and every
link carries the ``accessor`` (the field it came from) so the claim stays auditable.

Design contract (see docs/raman_saab/SYNTHESIS_LAYER_ARCHITECTURE.md):

- **The headline verdict is a passthrough.** ``ThemeReading.headline_verdict`` byte-equals
  the house rollup / dashboard verdict. Only ``axis=='verdict'`` links carry a direction;
  magnitude / state / varga / transit / yoga / statistical links carry ``lean`` as
  CORROBORATION only and can never flip a verdict. This is what keeps the golden ratchet
  (259/293) byte-identical — the layer imports nothing in the D1 verdict path.
- **Convergence is an evidentiary count, never a probability**, and it always reports the
  opposing pole too (the median chart carries both poles at all times, CLAUDE.md ★★).
- **Contradictions cite the governing precedence rule** (``INTERPRETATION_GUIDE``), never a
  fabricated resolution.
- **Provenance travels on every link** (RAMAN / CLASSICAL / STATISTICAL / MODERN_SYNTHESIS);
  the layer authors no ``WORK:line`` — a model-authored citation is treated as fabricated.

Usage:
    from app.raman_saab.theme_synthesis import build_theme_synthesis
    ts = build_theme_synthesis(report)      # report: DetailedReport
    for theme in ts.themes: ...
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Optional

import swisseph as swe

from app.raman_saab.doctrine import varga_domains as vd

logger = logging.getLogger(__name__)

if TYPE_CHECKING:                                   # avoid the build_detailed_report import cycle
    from app.raman_saab.detailed_report import DetailedReport

Axis = Literal["verdict", "magnitude", "state", "dasha", "varga", "transit", "yoga", "citation"]
Convergence = Literal["VERY_HIGH", "HIGH", "MODERATE", "MIXED", "WEAK"]

# provenance labels the layer may stamp (mirrors the existing Tagged/banner vocabulary)
RAMAN_EXPLICIT = "RAMAN_EXPLICIT"
RAMAN_GENERAL = "RAMAN_GENERAL_PRINCIPLE"
CLASSICAL_NONCITABLE = "CLASSICAL_NONCITABLE"
STATISTICAL = "STATISTICAL"
MODERN_SYNTHESIS = "MODERN_SYNTHESIS"


# ─────────────────────────────────────────────────────────────────────────────
# data model
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ThemeEvidenceLink:
    """One piece of evidence for a theme, on exactly one axis, fully traceable.

    ``value`` is the finding verbatim from the source object. ``lean`` is a coarse
    direction (favourable/adverse/neutral) used ONLY for corroboration counting — a link
    whose ``axis`` is not 'verdict' can never carry the theme's direction. ``accessor`` is
    the report field + file:line the value came from, so any sentence built on this link can
    answer "which finding produced you?"."""
    axis: Axis
    label: str
    value: str
    lean: str                       # 'favourable' | 'adverse' | 'neutral' | 'mixed'
    accessor: str
    provenance: str = MODERN_SYNTHESIS
    cite: Optional[object] = None   # a Citation object IF the source already carried one; never authored here


@dataclass(frozen=True)
class Contradiction:
    """Two findings that appear to conflict, classified and resolved by an existing
    precedence rule rather than forced to cancel."""
    kind: str                       # the taxonomy class (see _contradictions)
    poles: tuple[str, str]          # the two findings, each carrying its own accessor
    governing: str                  # the PREC-id (or doctrine tag) that resolves it
    resolution: str
    parties: tuple[str, ...] = ()   # the named participants (e.g. the facets that differ), as DATA
    #: `poles` is prose for the reader; `parties` carries the same names structurally so a
    #: renderer never has to parse the sentence back apart to recover them.


@dataclass(frozen=True)
class ThemeReading:
    """One life-theme, its evidence chain across every axis, its convergence and its
    contradictions — a re-read on top of the authoritative verdicts, judging nothing anew."""
    theme_id: str
    name: str
    domain: str
    houses: tuple[int, ...]
    karakas: tuple[str, ...]
    headline_verdict: str           # PASSTHROUGH of the primary house rollup — never recomputed
    driver: str
    sub_matters: tuple[tuple[str, str], ...]   # (matter, its own dashboard verdict) — the house's facets
    dominant_planets: tuple[str, ...]
    links: tuple[ThemeEvidenceLink, ...]
    convergence: Convergence
    convergence_label: str          # reader-facing phrase ('high convergence' / 'aligned, lightly evidenced')
    convergence_why: str
    contradictions: tuple[Contradiction, ...]
    activation_span: str            # period_pairing_clause — timed-indication idiom, never decree
    varga_relation: str             # confirms / strengthens / qualifies / modifies / contradicts / D9-only
    final_interpretation: str
    evidence_weight: float = 0.0    # for ranking only; NOT a probability or a verdict
    #: does the engine's OWN testimony ledger agree with this theme's verdict? (r.preponderance)
    concordance: Optional[BhavaConcordance] = None
    #: the concordance of the grahas that drive this theme (force vs intent, cross-checked)
    driver_concordance: tuple[GrahaConcordance, ...] = ()
    #: this theme's OWN divisional deep-reads set against its natal verdict (r.divisional)
    divisional_checks: tuple[DivisionalCheck, ...] = ()
    #: how unusual this theme's readings are in the population (r.distinctive)
    distinctive: tuple[Distinctiveness, ...] = ()
    #: the WALLED karmic/Jaimini lens on this bhava, where one exists (never corroboration)
    karmic_lens: Optional[KarmicLens] = None
    #: the yogas bearing here, read whole: promise + strength + cancellation + operating windows
    yogas: tuple[YogaReading, ...] = ()
    #: Ashtakavarga backing for the driving grahas, in the sign this bhava occupies
    av_support: tuple[AshtakavargaSupport, ...] = ()
    #: slow-mover transits bearing here — subordinate, never a direction
    transits: tuple[TransitNote, ...] = ()
    #: how many independent systems dissent from this verdict — the integration of the integrations
    dissent: Optional[DissentSummary] = None
    #: this theme's own forward window read INSIDE the longevity band (PREC-8: the span frames
    #: the reading). Names the age the window falls at and, where one exists, the maraka-tier
    #: confluence it coincides with — disclosure of the method, never a forecast.
    activation_in_span: str = ""
    #: what transit weather runs ACROSS this theme's own window (PREC-6/PREC-7 — subordinate)
    weather_on_window: str = ""
    #: the non-Raman ancestral screen where it bears on this bhava — a DIFFERENT layer, never a
    #: contradiction of the Raman verdict (PREC-12), and never admitted to the cross-checks
    pitru_screen: str = ""


@dataclass(frozen=True)
class BhavaConcordance:
    """Do the independent techniques AGREE about this bhava? — a re-read of the engine's OWN
    testimony ledger (``r.preponderance``), which is Raman's three-fold method made explicit:
    a matter is judged from the BHAVA, its LORD and its KARAKA (the ``core`` testimonies), with
    Bhava Bala, SAV, the matter-varga, the majority tenor and the fired yogas as ``overlay``.

    The layer computes none of this — it consumes it. The interesting output is ``divergence``:
    a house whose verdict runs against the weight of its own testimony (H4/H5/H8 on Mainpuri all
    read afflicted while every core testimony leans favourable) is a genuinely different reading
    from one where verdict and testimony concur, and the report never said so."""
    house: int
    verdict: str                    # PASSTHROUGH of the house rollup
    preponderance: str              # 'benefic' | 'adverse' | 'evenly balanced' (engine's own)
    status: str                     # 'well-corroborated' | 'contested' | '(mixed headline)'
    core_for: tuple[str, ...]       # the core testimonies (lord/karaka/navamsa) leaning favourable
    core_against: tuple[str, ...]   # ... and those leaning adverse
    overlay_for: tuple[str, ...]
    overlay_against: tuple[str, ...]
    divergence: str                 # '' when verdict and preponderance agree
    reading: str


@dataclass(frozen=True)
class GrahaConcordance:
    """Do the independent techniques AGREE about this graha? The engine computes several readings
    of the same planet and never cross-checks them: Shadbala (capacity/magnitude), Ishta vs Kashta
    (benefic vs malefic POTENCY — a different axis entirely), the Deeptadi avastha (the condition
    it acts from), and the plain flags (vargottama / retrograde / combust).

    The classical pattern that falls out is exactly Raman's strength-is-not-direction distinction
    (PREC-2, GBB-9): a graha can be strong AND harmful. Naming that is integration; listing the
    numbers separately, as the report did, is not."""
    planet: str
    rupas: Optional[float]          # Shadbala total in rupas — magnitude
    ishta: Optional[float]          # benefic potency
    kashta: Optional[float]         # malefic potency
    avastha: str                    # Deeptadi state
    flags: tuple[str, ...]          # vargottama / retrograde / combust
    agreement: str                  # 'unanimous' | 'mostly agrees' | 'split'
    pattern: str                    # the named diagnostic
    reading: str


@dataclass(frozen=True)
class DivisionalCheck:
    """One divisional deep-read set against the natal verdict it bears on.

    The engine casts and reads FIFTEEN vargas (``r.divisional``) — D-2 for wealth, D-7 for
    children, D-10 for career, D-30 for health, and so on — each with its own verdict and its own
    citations. The theme roster names the varga that belongs to each bhava and then, until now,
    read only the D9 relation: fourteen finished divisional judgments went unconsulted.

    A varga IS the classical confirmation device; asking whether it concurs with the rasi is what
    it is for. ``relation`` is that answer, and nothing here re-judges either side."""
    varga: str                      # 'D-7 Children (Saptamsa)'
    verdict: str                    # the division's own verdict line, verbatim
    relation: str                   # 'concurs' | 'diverges' | 'reads a facet'
    note: str


@dataclass(frozen=True)
class Distinctiveness:
    """How UNUSUAL a reading is in the population — the companion the concordance needs.

    Techniques agreeing is only informative if the thing they agree on is differential. The
    calibration layer already measures this per signification (``r.distinctive``: rarity band,
    favourability percentile, the share of charts holding the same reading), and the integrated
    reading never said it. A house that every technique confirms AND that 92% of charts share is
    a weaker finding than one only 1% share — the project's Measured-Truth directive in miniature."""
    house: int
    signification: str
    verdict: str
    rarity: str                     # 'rare' | 'notable' | ...
    population_note: str            # the calibration layer's own sentence


@dataclass(frozen=True)
class KarmicLens:
    """The karmic/Jaimini layer's own reading of a bhava, set beside the natal verdict.

    ``r.soul`` carries independent verdicts on three bhavas this layer already themes —
    poorvapunya (the 5th, merit carried from past births), dharma (the 9th) and moksha (the 12th).
    They were computed and never set against the Parashari reading of the same houses.

    **This lens is WALLED.** ``r.karmic.frame`` states it plainly: nothing in the Jaimini layer
    feeds or alters the Parashari natal verdicts. So this records agreement or difference for the
    reader and carries an explicit wall note — it is a second lens on the same bhava, never
    corroboration that could move a verdict, and it is excluded from every convergence count."""
    house: int
    aspect: str                     # 'poorvapunya' | 'dharma' | 'moksha'
    karmic_verdict: str
    natal_verdict: str
    relation: str                   # 'concurs' | 'differs'
    note: str


@dataclass(frozen=True)
class YogaReading:
    """One fired yoga, read whole — what it promises, how strong its participants measure,
    whether a cancellation applies, and WHEN it operates.

    A yoga IS a combination: the classical integrative unit, the one place the tradition itself
    already does the synthesising. The engine computes it across three fields — ``r.yogas`` (that
    it fired), ``r.yoga_deep`` (participants, measured strength, cancellations, rank) and
    ``r.yoga_timing`` (the periods when its participants actually run, each with that lord's own
    quality) — and the layer had been using a fragment of the first: a bare "bears on [2, 6, 10]".

    Setting the promise beside its operating windows is Raman's own framing: a yoga promises, and
    the dasha of its participants is when it delivers. ``cancellation`` is carried verbatim
    because a cancelled yoga must never be presented as an active one."""
    name: str
    kind: str
    effect: str                     # what the yoga promises, verbatim from the engine
    rank: Optional[int]             # comparison_rank — which yoga is strongest in THIS chart
    strength_note: str              # participants' measured Shadbala; no invented percentage
    cancellation: str               # the bhanga note, verbatim — never summarised away
    participants: tuple[str, ...]   # 'Venus (H1, friend, 7.61 rupas)'
    windows: tuple[str, ...]        # 'Venus AD 2015-2018 (well)' — when it actually operates
    ahead: bool                     # does any operating window lie ahead of the reference moment?


@dataclass(frozen=True)
class AshtakavargaSupport:
    """Does Ashtakavarga back the graha that carries this theme, IN THE PLACE it must act?

    An entirely independent measurement system from Shadbala and from the house judges. The
    engine computes the full per-planet matrix (``r.bav_matrix``), the trikona/ekadhipatya
    reductions (``r.bav_reduced``) and the Sodya Pinda weights (``r.sodya_pinda``) — and the
    synthesis read none of it. SAV reached the reading only indirectly, inside a preponderance
    testimony. The question this answers is narrower and sharper than a chart-wide total: how many
    bindus does THIS theme's driving graha hold in the sign THIS theme's bhava occupies."""
    planet: str
    house: int
    sign: int
    bindus: int                     # that planet's BAV in the theme's house-sign
    reduced: int                    # after the trikona/ekadhipatya reductions
    sodya_pinda: int                # the planet's overall AV weight
    verdict: str                    # 'well supported' | 'about average' | 'poorly supported'


@dataclass(frozen=True)
class TransitNote:
    """A slow-mover's CURRENT transit bearing on this theme — strictly subordinate.

    Raman is explicit (HTJAH-II:4679-4687): transits are catalytic, and all conclusions are drawn
    primarily on Dasa-vichara. So this carries no direction of its own; it records what the engine
    already computed for the transit — the house from the Moon, whether the Gochara is good, the
    BAV bindus under it, and any vedha (obstruction) cancelling it — and nothing more."""
    planet: str
    house_from_moon: int
    gochara_good: bool
    bav_bindus: Optional[int]
    vedha_by: tuple[str, ...]       # obstructing planets, if any
    net_good: bool                  # the engine's own net verdict AFTER vedha
    note: str


@dataclass(frozen=True)
class CrossCheck:
    """One independent cross-check, placed on the CITED reliability ladder rather than counted.

    An earlier version of this graded a bhava settled / qualified / seriously contested by
    counting how many cross-checks dissented. Three findings killed that:

    1. ``docs/raman_saab/COMPARATIVE_WEIGHING.md:52-56`` — the project already tested
       head-counting against Raman's own reasoning on all 7 Type-A cases: *"The
       benefic/malefic-preponderance hypothesis held 0 of 7. Raman does NOT head-count
       influences."* Counting cross-checks re-runs a hypothesis this repo falsified.
    2. ``detailed_report.py`` (HouseTestimonies) already records, with citation, that *"Raman
       states no numeric N-testimonies rule (HTJAH-I:495 says only 'all these must be properly
       weighed')"* — so any 0/1/2 cutoff is an invented threshold, the exact class of thing a
       bphs-doctrine-reviewer pass already struck out of the Bhava-Bala lean.
    3. ``report_html.py`` states the witnesses *"are NOT independent votes: lord, karaka and
       navamsa are the verdict's own inputs restated by name"* — so the testimony ledger cannot
       be tallied as an independent dissenter at all without double-counting the verdict.

    What IS citable is the reliability LADDER, so each cross-check is reported at its own tier
    with the rule that governs it. No score, no tier count, no aggregate grade."""
    system: str                     # the cross-check's name
    tier: str                       # where it sits on the cited ladder
    independent: bool               # False when it restates the verdict's own inputs
    relation: str                   # 'reads with' | 'reads against' | 'restates the verdict'
    governing: str                  # the PREC-id that governs this pair
    citation: str                   # the corpus token behind that rule, or '' when uncited
    note: str


@dataclass(frozen=True)
class DissentSummary:
    """The cross-checks on a bhava, laid out by reliability tier — deliberately NOT scored.

    ``dissenting`` names the checks reading against the verdict so a reader can see them at a
    glance; it is an INVENTORY in Raman's own vocabulary (HTJAH-I:8870 "preponderance"), never a
    tally that grades the reading. The engine's own preponderance ledger draws exactly this line
    and says so; this follows it rather than inventing a rival scheme."""
    checks: tuple[CrossCheck, ...]
    dissenting: tuple[str, ...]     # names only — an inventory, never a count that grades
    walled_note: str                # the karmic lens, recorded outside the cross-checks entirely
    reading: str
    method_note: str                # why no grade is given, with the citation


@dataclass(frozen=True)
class WeatherWindow:
    """One forward stretch of TIMING WEATHER — never a verdict, always a modifier of one.

    Three independent schemes the engine computes in full and the integrated reading never
    consulted: Sade Sati's phases (`r.sade_sati_phases`), the MD/AD lord meeting its own ADVERSE
    transit (`r.dasha_transit_adverse` — the mirror of the favourable confluence already read),
    and the eightfold Dasha Kakshya split of each Mahadasha (`r.dasa_kakshya`).

    Each is subordinate BY CITATION, and the ``governing`` field carries which rule subordinates
    it: transits are "always secondary in importance… like catalytic agents" (PREC-6,
    HTJAH-II:4679), and Dasha Kakshya is "a timing lens, never a verdict" (PREC-7, ASP-12:174).
    So a window here can say a stretch is rough going; it can never say a bhava is afflicted."""
    kind: str                       # 'Sade Sati' | 'Dasha x adverse transit' | 'Dasha Kakshya'
    label: str                      # the scheme's own name for this stretch
    span: str                       # 'YYYY-YYYY'
    start_year: int
    end_year: int
    current: bool                   # does it cover the reading's anchor date
    detail: str                     # the scheme's own measured particulars
    governing: str                  # the PREC-id that subordinates it
    citation: str


@dataclass(frozen=True)
class AfflictionCalendar:
    """The transit weather across the years this reading names — subordinate, and said so.

    The engine measured all of it and the synthesis timed every theme without once asking what
    else was running. A bhukti that grades *par excellence* for a bhava while Sade Sati sits over
    the Moon and the Mahadasha lord meets its own adverse transit is not the same window as one
    running clear, and the report held both halves and never joined them.

    Strictly a modifier: nothing here moves a bhava verdict or a fructification grade. PREC-6 and
    PREC-7 are quoted on every window so the subordination travels with the data."""
    windows: tuple[WeatherWindow, ...]
    now: tuple[str, ...]            # what is running at the anchor date
    frame: str
    honesty: str


@dataclass(frozen=True)
class LongevityFrame:
    """The span the whole reading is read INSIDE — Raman's own first step, restored.

    ``PREC-8`` states his order verbatim: *"first establish the band by combination, THEN fix the
    period by the marakas. The numeric span is a cross-check, never a prediction of death"*
    (HTJAH-II:4465-4472). The engine performed step one on every chart and the integrated reading
    never said it: themes named forward windows out to the 2040s without once asking whether those
    windows sit inside the span the ayurdaya gives. That is the wrong way round — the band frames
    the reading, it is not a chapter beside it.

    Deliberately NOT a death forecast. The band and the maraka periods are stated in the classical
    timed-indication idiom the 2026-08-17 guard decision permits; the Measured-Truth disclosure
    (`honesty`) rides on every surface, because the validation program measured no chart-specific
    death-timing signal at all."""
    band: str                       # harmonised class label, e.g. 'Purnayu (purna band)'
    years: float                    # the ayurdaya numeric — a CROSS-CHECK on the band, never a date
    ymd: tuple[int, int, int]
    balarishta: str                 # 'applies' / 'cancelled' / '' when neither
    span_year: int                  # calendar year the band reaches, for the within-span test
    reading_reaches: int            # furthest calendar year any theme window names (0 if none)
    within_span: bool               # every window this reading names falls inside the band
    maraka_now: bool                # does the RUNNING period carry a maraka-tier lord
    #: (bhukti, span, tier-score, standing-vs-band), ahead only. The fourth element is the
    #: cross-check the two methods force on each other: the maraka scheme runs the whole
    #: Vimshottari timeline while the ayurdaya band ends where it ends, so some maraka-tier
    #: bhuktis fall BEYOND the span. Raman's order settles it — band first (PREC-8) — and
    #: the disagreement is disclosed rather than quietly reconciled.
    maraka_windows: tuple[tuple[str, str, int, str], ...]
    frame: str                      # the framing sentence — band first, marakas second
    honesty: str                    # the Measured-Truth disclosure that rides with it
    citation: str


@dataclass(frozen=True)
class ExecutivePortrait:
    """The two-page opening: if you read only this, what is this horoscope?"""
    identity: str                   # Lagna / lagna-lord / Atmakaraka / Karakamsa / Moon — who the chart is
    temperament: str
    frame: str
    dominant_actors: tuple[tuple[str, str], ...]    # (planet, why-dominant)
    strongest_domains: tuple[str, ...]
    weakest_domains: tuple[str, ...]
    principal_tension: str
    #: how far the chart's independent techniques agree with each other overall — the honest
    #: confidence statement the reading owes the reader, computed from the engine's own ledgers
    concordance_note: str
    protective_factors: tuple[str, ...]
    current_chapter: str
    next_chapter: str
    honesty_note: str               # r.info.sentence — calibration, not validation
    #: how much of this reading survives an error in the birth time (r.rect_confidence). Every
    #: verdict above rests on the cast moment, so its stability qualifies ALL of them — the
    #: engine measured it and the synthesis never said it.
    reading_stability: str = ""
    #: the WALLED Jaimini chara dasha running now, beside the Vimshottari chapter (r.chara_sequence)
    chara_now: str = ""


@dataclass(frozen=True)
class ThemeConnection:
    """Two themes discovered to share a mechanism — the same driving planet or a common house —
    so the reader sees the horoscope as one fabric, not independent modules."""
    theme_a: str
    theme_b: str
    shared: str                     # the planet(s)/house(s) they share
    note: str


@dataclass(frozen=True)
class DashaChapter:
    """One Mahadasha run and how the life-themes evolve across it — the horoscope's movement
    through time. A re-read of r.life_chapters (never new dasha math). A chapter foregrounds a
    theme when the Mahadasha lord is one of that theme's OWN driving planets — the differential
    signal (the Saturn period foregrounds what Saturn drives, not every house it happens to
    aspect). Split into those NEWLY emphasized in this chapter versus those CONTINUING from the
    previous one (Raman's item-9 evolution question)."""
    maha: str
    span: str                       # 'YYYY-YYYY' (JD arithmetic, GREG_CAL)
    is_current: bool
    lean: str                       # the MD Ishta/Kashta lean, re-read
    activates: tuple[str, ...]      # themes the MD lord actually drives (differential, not flooding)
    emerging: tuple[str, ...]       # newly emphasized vs the previous chapter
    continuing: tuple[str, ...]     # carried over from the previous chapter
    acts_through: tuple[str, ...] = ()   # for a NODE chapter: the planets it gives results for
    #: the chapter's OWN lord graded by the engine (r.md_condition) — a period run by a strong,
    #: vargottama lord is not the same chapter as one run by a weak one, and the report computed
    #: that grading without ever attaching it to the narrative of the period
    lord_condition: str = ""
    #: Ashtakavarga's own verdict on the chapter (r.av_dasha_seats): the sign the Mahadasha
    #: seats in and its bindus. An independent system agreeing or disagreeing with the lean.
    av_seat: str = ""



@dataclass(frozen=True)
class ThemeSynthesis:
    """The whole integrated interpretation: ranked themes, the dominant-theme spine, the
    executive portrait, the cross-theme fabric, and the dasha evolution. Built last, re-read
    only."""
    themes: tuple[ThemeReading, ...]
    spine: tuple[str, ...]          # theme_ids of the 3-5 dominant themes (see _spine_size)
    frame: str
    portrait: ExecutivePortrait
    connections: tuple[ThemeConnection, ...] = ()
    dasha_evolution: tuple[DashaChapter, ...] = ()
    #: every graha's force-vs-intent cross-check, busiest first — the chart-level concordance
    graha_concordance: tuple[GrahaConcordance, ...] = ()
    #: bhavas whose verdict runs against the weight of their own testimony (the contested ones)
    contested_bhavas: tuple[BhavaConcordance, ...] = ()
    #: divisions that read against the rasi verdict they confirm — disclosed, never applied
    divisional_divergences: tuple[tuple[str, DivisionalCheck], ...] = ()
    #: themes where 2+ independent cross-checks read against the verdict — read these lightly
    contested_themes: tuple[tuple[str, DissentSummary], ...] = ()
    #: the span the whole reading is read inside — Raman's first step (PREC-8), restored to the
    #: front of the synthesis instead of sitting in a chapter of its own
    longevity: Optional[LongevityFrame] = None
    #: the transit weather over the years this reading names — subordinate by citation (PREC-6,
    #: PREC-7), never a verdict, and never previously joined to the timing it qualifies
    calendar: Optional[AfflictionCalendar] = None


# ─────────────────────────────────────────────────────────────────────────────
# the theme roster — engine-sourced, not hardcoded per chart
# ─────────────────────────────────────────────────────────────────────────────
# A theme is a BHAVA (or house-cluster), NOT a dashboard matter — several dashboard matters can
# share one house (mother/property/comforts/education all live in H4; father/dharma in H9), and
# treating each as its own theme produced clones that all inherited the same house verdict and the
# same tensions. So each theme names its PRIMARY house, the dashboard MATTERS that live there (its
# facets), the varga whose domain (varga_domains.DOMAINS) supplies karakas, and candidate SUPPORT
# houses (kept only when a driving planet actually touches them — pass 3). The headline is the
# primary house rollup; the facets carry each matter's own dashboard verdict, so a house that reads
# afflicted while its matters read favourable tells that story ONCE, inside the theme.
@dataclass(frozen=True)
class _PlainDomain:
    """The domain stand-in for a bhava with NO classical divisional chart of its own (H8, H12).
    Carries a plain description, no karakas and no citation — the engine must not imply Raman
    (or the Parashari scheme) assigned a varga where none is assigned. Such a theme is still read
    from the rasi, with the navamsa applying as the general strength check as it does everywhere."""
    domain: str
    karakas: tuple[str, ...] = ()
    source: Optional[object] = None


@dataclass(frozen=True)
class _ThemeSpec:
    """One roster entry. ``varga`` names the division whose domain (varga_domains.DOMAINS)
    supplies this theme's karakas and citation; ``None`` means no classical division covers this
    bhava, and ``domain_note`` describes it instead."""
    theme_id: str
    name: str
    primary_house: int
    matters: tuple[str, ...]        # dashboard matters that live in this house (its facets)
    varga: Optional[int]
    support: tuple[int, ...]        # CANDIDATE network houses, kept only when a driver touches one
    domain_note: str = ""           # used only when varga is None


_THEME_ROSTER: tuple[_ThemeSpec, ...] = (
    _ThemeSpec("wealth",      "Wealth & resources",         2,  ("wealth",),   2,  (11, 8)),
    _ThemeSpec("career",      "Career & public standing",   10, ("career",),   10, (2, 6, 11)),
    _ThemeSpec("marriage",    "Marriage & partnership",     7,  ("marriage",), 9,  ()),
    _ThemeSpec("children",    "Children & creativity",      5,  ("children",), 7,  (9,)),
    _ThemeSpec("foundations", "Home, mother & foundations", 4,
               ("mother", "property", "comforts", "education"), 4, (2,)),
    _ThemeSpec("fortune",     "Fortune, father & dharma",   9,  ("father", "spiritual"), 20, (5, 10)),
    _ThemeSpec("health",      "Health & vitality",          6,  ("health",),   30, (1, 8)),
    _ThemeSpec("siblings",    "Siblings & courage",         3,  ("siblings",), 3,  ()),
    # The four bhavas that carry no dashboard matter of their own. They were previously visible
    # only as SUPPORT houses inside other themes, so the reading never stated what the chart says
    # about the self, about gains, about crisis and longevity, or about loss and withdrawal — a
    # completeness gap. D1 covers the body explicitly; H8, H11 and H12 are assigned no division in
    # the domain table, so they carry a plain description and say so rather than borrowing one.
    _ThemeSpec("self",        "Self, body & constitution",  1,  (),            1,  (6, 8)),
    _ThemeSpec("gains",       "Gains, friends & fulfilment", 11, (),        None,  (2, 10),
               "income, gains, friendships and the fulfilment of desires — read from the rasi "
               "(no classical division is assigned to this bhava)"),
    # NB: a theme name must not START with a pinned "## <label>" section marker — a theme renders
    # as "#### <name>", which contains "## <name>", so such a name silently hijacks every
    # find("## <label>") / _section(md, "## <label>") lookup in the report tests. "Longevity, …"
    # did exactly that to the real "## Longevity" section. Guarded by
    # test_theme_names_cannot_hijack_a_pinned_section_marker.
    _ThemeSpec("longevity",   "Crisis, longevity & the hidden", 8, (),      None,  (1, 12),
               "longevity, upheaval and what is hidden — read from the rasi (no classical "
               "division is assigned to this bhava)"),
    _ThemeSpec("liberation",  "Loss, seclusion & liberation", 12, (),       None,  (4, 8),
               "expenditure, withdrawal and moksha — read from the rasi (no classical division "
               "is assigned to this bhava)"),
)


# ─────────────────────────────────────────────────────────────────────────────
# small direction helpers (reuse the engine's own lean vocabulary)
# ─────────────────────────────────────────────────────────────────────────────
def _dir(lean: str) -> int:
    """+1 favourable, -1 adverse, 0 neutral/mixed — for corroboration counting only."""
    return {"favourable": 1, "adverse": -1}.get(lean, 0)


def _nav_lean(navamsa: Optional[str]) -> str:
    """The D9 relation as a coarse lean (the only verdict-bearing varga signal)."""
    n = (navamsa or "").lower()
    if "confirm" in n or "delivered" in n or "support" in n:
        return "favourable"
    if "weaken" in n or "contradict" in n or "undercut" in n or "denies" in n:
        return "adverse"
    return "neutral"


# ─────────────────────────────────────────────────────────────────────────────
# the builder
# ─────────────────────────────────────────────────────────────────────────────
def build_theme_synthesis(r: "DetailedReport") -> ThemeSynthesis:
    """Assemble the integrated interpretation from an already-built ``DetailedReport``.

    Six deterministic passes: theme roster -> evidence gather -> dominant actors ->
    convergence -> contradictions -> ranking + portrait. Read-only throughout; the one
    permitted rebuild is ``build_judgment_graph(r)`` (a pure re-read of relations)."""
    # lazy imports — detailed_report has finished importing by the time this runs, so this
    # avoids the build_detailed_report <-> theme_synthesis cycle
    from app.raman_saab import detailed_report as dr
    from app.raman_saab.insight_digest import _lean_of
    from app.raman_saab.judgment_graph import build_judgment_graph
    from app.raman_saab.planet_biographies import planet_census
    from app.raman_saab.doctrine.synthesis_rules import yoga_house_bearings

    proformas = {pf.house: pf for pf in r.proformas}
    dash = {e.matter: e for e in r.dashboard.entries}

    # pass 3 inputs (structural graph, once) — tolerate a sparse/Track-B failure
    try:
        graph = build_judgment_graph(r)
        census = planet_census(graph)
    except Exception:
        census = {}
    # planet -> the houses it touches (lord/karaka/occupy/aspect), from the census breakdown
    planet_houses = _planet_house_map(r)

    # the chart-level graha cross-check, computed once and shared by every theme
    graha_conc = _graha_concordance(r)

    # the transit weather over the forward years, computed once: every theme's own window is
    # then read against it, which is the join the report never made (PREC-6 / PREC-7)
    weather = _safe(lambda: _weather_windows(r), ()) or ()

    themes: list[ThemeReading] = []
    for spec in _THEME_ROSTER:
        theme_id, name, prim_house = spec.theme_id, spec.name, spec.primary_house
        matters, support = spec.matters, spec.support
        if prim_house not in proformas:
            continue
        if spec.varga is None:                      # a bhava with no classical division
            domain = _PlainDomain(spec.domain_note or f"house {prim_house}")
        else:
            try:
                domain = vd.domain_for(spec.varga)
            except ValueError:
                continue

        pf = proformas[prim_house]
        headline = pf.rollup                        # PASSTHROUGH — never recomputed
        driver = dr.rollup_driver(r.calibration.get(prim_house), headline) or name.split()[0].lower()
        # the house's facets — each dashboard matter that lives here, with its OWN verdict
        facets = tuple((m, dash[m].verdict) for m in matters if m in dash)

        # pass 2 + 3: gather evidence links and discover the network / dominant planets
        links: list[ThemeEvidenceLink] = []
        dom_planets = _dominant_planets(r, prim_house, domain, census, planet_houses)
        kept_support = _discover_support(prim_house, support, dom_planets, planet_houses)
        houses = (prim_house,) + kept_support

        links.extend(_verdict_links(r, prim_house, kept_support, proformas))
        links.extend(_facet_links(facets))
        links.extend(_varga_links(r, prim_house, domain))
        links.extend(_yoga_links(r, houses, yoga_house_bearings))
        links.extend(_strength_state_links(r, prim_house, pf, dom_planets))
        links.extend(_dasha_links(r, houses))
        links.extend(_transit_links(r, houses, dom_planets, planet_houses))
        links.extend(_insight_links(r, houses))

        # pass 4: convergence (evidentiary count, both poles)
        convergence, conv_label, why = _convergence(headline, facets, links, r)
        # pass 5: contradictions — ONE consolidated statement per axis, not one per matter
        contradictions = _contradictions(r, prim_house, pf, headline, facets, name)

        activation, act_years = _theme_timing(r, name, prim_house, houses, dom_planets)
        varga_rel = _varga_relation(r, prim_house, domain)
        conc = _bhava_concordance(r, prim_house)
        div_checks = _divisional_checks(r, spec, facets, headline)
        av_sup = _av_support(r, prim_house, dom_planets)
        klens = _karmic_lens(r, prim_house, headline)
        dissent = _dissent_summary(conc, div_checks, av_sup, klens, headline)
        final = _final_interpretation(name, headline, convergence, conv_label, contradictions,
                                      activation, dom_planets, facets,
                                      tuple(g for g in graha_conc if g.planet in dom_planets),
                                      dissent)
        weight = _weight(convergence, links, r, houses, dom_planets)

        themes.append(ThemeReading(
            theme_id=theme_id, name=name, domain=domain.domain, houses=houses,
            karakas=domain.karakas, headline_verdict=headline, driver=driver, sub_matters=facets,
            dominant_planets=dom_planets, links=tuple(links), convergence=convergence,
            convergence_label=conv_label, convergence_why=why, contradictions=contradictions,
            activation_span=activation, varga_relation=varga_rel, final_interpretation=final,
            evidence_weight=weight,
            concordance=conc,
            driver_concordance=tuple(g for g in graha_conc if g.planet in dom_planets),
            divisional_checks=div_checks,
            distinctive=_distinctiveness(r, houses),
            karmic_lens=klens,
            yogas=_theme_yogas(r, houses, yoga_house_bearings),
            av_support=av_sup,
            transits=_transit_notes(r, houses, dom_planets),
            dissent=dissent,
            activation_in_span=_activation_in_span(r, act_years),
            weather_on_window=_weather_on_window(weather, act_years),
            pitru_screen=_safe(lambda: _pitru_screen(r, prim_house), "") or ""))

    # pass 6: rank + spine + portrait + the cross-theme fabric + dasha evolution
    themes.sort(key=lambda t: t.evidence_weight, reverse=True)
    spine = tuple(t.theme_id for t in themes[:_spine_size(themes)])
    frame = getattr(r.overview, "stronger_frame", "") or ""
    portrait = _portrait(r, themes, spine, frame, graha_conc)
    connections = _connections(themes)
    evolution = _dasha_evolution(r, themes)
    contested = tuple(t.concordance for t in themes
                      if t.concordance is not None and t.concordance.divergence)
    divergent = tuple((t.name, d) for t in themes for d in t.divisional_checks
                      if d.relation == "diverges")
    # themes carrying ANY cross-check that reads against the verdict. Deliberately not filtered
    # by a count threshold (>=2 was an invented cutoff) — the inventory is the disclosure.
    contested_th = tuple((t.name, t.dissent) for t in themes
                         if t.dissent is not None and t.dissent.dissenting)
    return ThemeSynthesis(themes=tuple(themes), spine=spine, frame=frame, portrait=portrait,
                          connections=connections, dasha_evolution=evolution,
                          graha_concordance=graha_conc, contested_bhavas=contested,
                          divisional_divergences=divergent, contested_themes=contested_th,
                          longevity=_safe(lambda: _longevity_frame(r, themes), None),
                          calendar=_safe(lambda: _affliction_calendar(r, weather), None))


# ─────────────────────────────────────────────────────────────────────────────
# pass helpers
# ─────────────────────────────────────────────────────────────────────────────
def _safe(fn, default):
    """Run ``fn``, and on ANY failure return ``default`` instead of aborting the synthesis.

    The overlay must degrade, never crash a reading — but a silent swallow also hides a real
    defect behind a section that merely goes missing, so the exception is logged at debug."""
    try:
        return fn()
    except Exception:
        logger.debug("theme_synthesis: a section degraded to its default", exc_info=True)
        return default


def _planet_house_map(r: "DetailedReport") -> dict[str, set[int]]:
    """planet -> the set of houses it influences (lord/karaka/helps/obstructs), from the
    already-built planet biographies. Pure re-read; empty on sparse charts."""
    out: dict[str, set[int]] = {}
    for bio in getattr(r, "planet_bios", ()) or ():
        hs: set[int] = set()
        hs.update(getattr(bio, "lord_of", ()) or ())
        hs.update(getattr(bio, "karaka_of", ()) or ())
        hs.update(getattr(bio, "helps", ()) or ())
        hs.update(getattr(bio, "obstructs", ()) or ())
        occ = getattr(bio, "occupies", 0) or 0
        if occ:
            hs.add(occ)
        out[bio.planet] = hs
    return out


def _matter_reading(r, house):
    """The MatterReading for a house (carries the D9 navamsa relation). None if absent."""
    return next((m for m in r.synthesis.matters if m.house == house), None)


def _dominant_planets(r, prim_house, domain, census, planet_houses) -> tuple[str, ...]:
    """The planets that STRUCTURALLY drive this theme's primary house — its lagna-frame lord and
    its domain karakas, in that order. A broad-census planet is added ONLY if it actually LORDS
    or is a KARAKA of the primary house (not merely aspects it) — so a weak, unrelated graha is
    never listed as a 'driver' just because it casts a distant aspect. Deduped, capped at 3."""
    out: list[str] = []
    # 1. the primary house's lagna-frame lord (frame-lord-trap-safe: HouseProforma.lord is the
    #    lagna-frame lord's name)
    pf = next((p for p in r.proformas if p.house == prim_house), None)
    if pf is not None and pf.lord:
        out.append(pf.lord)
    # 2. domain karakas the census confirms as participating
    for k in domain.karakas:
        if k not in out and (k in census or prim_house in planet_houses.get(k, set())):
            out.append(k)
    # 3. a further planet ONLY if it lords/karaka-s this very house (a real structural tie,
    #    not a distant aspect) — from the planet biographies' lord_of/karaka_of
    if len(out) < 3:
        for bio in getattr(r, "planet_bios", ()) or ():
            if bio.planet in out:
                continue
            if prim_house in (getattr(bio, "lord_of", ()) or ()) or \
                    prim_house in (getattr(bio, "karaka_of", ()) or ()):
                out.append(bio.planet)
            if len(out) >= 3:
                break
    return tuple(out[:3])


def _discover_support(prim_house, candidates, dom_planets, planet_houses) -> tuple[int, ...]:
    """Keep a candidate supporting house ONLY when a dominant planet actually touches it — the
    network is discovered from the graph, never asserted. Falls back to the classical candidates
    when the graph is empty (sparse chart), disclosed as such downstream."""
    if not planet_houses:
        return tuple(candidates)
    touched = set()
    for p in dom_planets:
        touched |= planet_houses.get(p, set())
    kept = tuple(h for h in candidates if h in touched and h != prim_house)
    return kept


def _verdict_links(r, prim_house, support, proformas) -> list[ThemeEvidenceLink]:
    from app.raman_saab import detailed_report as dr
    from app.raman_saab.insight_digest import _lean_of
    out: list[ThemeEvidenceLink] = []
    pf = proformas[prim_house]
    out.append(ThemeEvidenceLink(
        "verdict", f"House {prim_house} rollup", pf.rollup, _lean_of(pf.rollup),
        f"r.proformas[{prim_house-1}].rollup @ house_template.py:236", RAMAN_EXPLICIT))
    for h in support:
        spf = proformas.get(h)
        if spf is not None:
            out.append(ThemeEvidenceLink(
                "verdict", f"House {h} (network) rollup", spf.rollup, _lean_of(spf.rollup),
                f"r.proformas[{h-1}].rollup @ house_template.py:236", RAMAN_EXPLICIT))
    return out


def _facet_links(facets) -> list[ThemeEvidenceLink]:
    """One verdict link per dashboard matter that lives in this house (its facets) — each judged
    by its own dedicated reader. This is where a house-vs-matter grain difference shows up."""
    from app.raman_saab.insight_digest import _lean_of
    out: list[ThemeEvidenceLink] = []
    for matter, verdict in facets:
        out.append(ThemeEvidenceLink(
            "verdict", f"{matter} (dedicated reader)", verdict, _lean_of(verdict),
            "r.dashboard.entries[*].verdict @ matter_varga_dashboard.py:38", RAMAN_EXPLICIT))
    return out


def _varga_links(r, prim_house, domain) -> list[ThemeEvidenceLink]:
    m = _matter_reading(r, prim_house)
    if m is None or not m.navamsa:
        return []
    return [ThemeEvidenceLink(
        "varga", "D9 (navamsa) confirmation", m.navamsa, _nav_lean(m.navamsa),
        f"r.synthesis.matters[h={prim_house}].navamsa @ synthesis.py:39", RAMAN_EXPLICIT,
        cite=domain.source)]


def _yoga_links(r, houses, yoga_house_bearings) -> list[ThemeEvidenceLink]:
    from app.raman_saab import detailed_report as dr
    out: list[ThemeEvidenceLink] = []
    hset = set(houses)
    for y in getattr(r, "yogas", ()) or ():
        bearing = _safe(lambda: yoga_house_bearings(r.chart, y), None)
        if not bearing or not (bearing & hset):
            continue
        lean = _safe(lambda: dr._yoga_record_lean(y), "neutral") or "neutral"
        name = getattr(y, "name", getattr(y, "id", "yoga"))
        out.append(ThemeEvidenceLink(
            "yoga", f"{name} bears on {sorted(bearing & hset)}", name, lean,
            "yoga_house_bearings(r.chart, y) @ synthesis_rules.py:238",
            RAMAN_EXPLICIT, cite=getattr(y, "source", None)))
    return out


def _strength_state_links(r, prim_house, pf, dom_planets) -> list[ThemeEvidenceLink]:
    """Magnitude (Shadbala/Bhava Bala) and state (Deeptadi) as CORROBORATION only — never a
    direction. Uses the frame-lord-trap-safe lagna ledger for the strength readout."""
    from app.raman_saab import detailed_report as dr
    out: list[ThemeEvidenceLink] = []
    # Bhava Bala rank (magnitude) for the primary house
    row = next((hs for hs in getattr(r, "house_strength", ()) if getattr(hs, "house", None) == prim_house), None)
    if row is not None and getattr(row, "bhava_bala_rank", None) is not None:
        out.append(ThemeEvidenceLink(
            "magnitude", f"House {prim_house} Bhava Bala rank", f"rank {row.bhava_bala_rank}/12",
            "neutral", "r.house_strength[*].bhava_bala_rank @ detailed_report.py:1734",
            RAMAN_GENERAL))
    # the driving planet's Shadbala (magnitude)
    for p in dom_planets[:1]:
        pl = r.chart.planets.get(p)
        if pl is not None and getattr(pl, "shadbala_rupas", None) is not None:
            out.append(ThemeEvidenceLink(
                "magnitude", f"{p} Shadbala", f"{pl.shadbala_rupas.total/60.0:.2f} rupas",
                "neutral", "r.chart.planets[p].shadbala_rupas.total @ chart/model.py:26",
                RAMAN_GENERAL))
    # the driving planet's Deeptadi STATE (a distinct axis from magnitude/direction; HPA Ch.7,
    # verdict-invariant — testimony about the CONDITION the planet acts from, never a direction)
    from app.raman_saab.primitives import deeptadi as _deeptadi
    states = _safe(lambda: _deeptadi.chart_states(r.chart), {}) or {}
    for p in dom_planets[:1]:
        st = states.get(p)
        if st:
            out.append(ThemeEvidenceLink(
                "state", f"{p} Deeptadi state", f"{st[0]} ({st[1]})", "neutral",
                "deeptadi.chart_states(r.chart) @ deeptadi.py:100", RAMAN_EXPLICIT))
    return out


def _dasha_links(r, houses) -> list[ThemeEvidenceLink]:
    from app.raman_saab import detailed_report as dr
    tiers = _safe(lambda: dr.house_current_tiers(r), {}) or {}
    out: list[ThemeEvidenceLink] = []
    for h in houses:
        t = tiers.get(h)
        if t:
            out.append(ThemeEvidenceLink(
                "dasha", f"House {h} in the running period", t, "neutral",
                "house_current_tiers(r) @ detailed_report.py:1029", RAMAN_EXPLICIT))
    return out


def _transit_links(r, houses, dom_planets, planet_houses) -> list[ThemeEvidenceLink]:
    """Transit as the SUBORDINATE modifier only — a dasha-x-transit confluence whose period lord
    bears on this theme. Never an independent prediction (HTJAH-II:4679-4687: transits are
    catalytic, all conclusions drawn primarily on Dasa-vichara).

    ``ConfluenceWindow`` carries ``planet``/``role``/JD bounds — it has NO ``houses`` or ``label``
    field, so the earlier attribute probe silently matched nothing and this axis emitted zero
    links on every chart. The confluence is matched by its PLANET instead: it bears on the theme
    when that planet drives the theme or influences one of the theme's houses. One link per
    planet+role — ``r.dasha_transit`` holds a row per bhukti-and-segment overlap, so a single
    period lord otherwise repeats the identical row many times over."""
    hset = set(houses)
    drivers = set(dom_planets)
    out: list[ThemeEvidenceLink] = []
    seen: set[tuple[str, str]] = set()
    for c in getattr(r, "dasha_transit", ()) or ():
        planet = getattr(c, "planet", None)
        if not planet:
            continue
        if planet not in drivers and not (planet_houses.get(planet, set()) & hset):
            continue
        role = str(getattr(c, "role", "") or "")
        if (planet, role) in seen:
            continue
        seen.add((planet, role))
        out.append(ThemeEvidenceLink(
            "transit", "Dasha x transit confluence",
            f"{planet}{f' ({role})' if role else ''} well-placed by transit in its own period",
            "neutral", "r.dasha_transit[*].planet @ detailed_report.py:1526", RAMAN_GENERAL))
    return out


def _insight_links(r, houses) -> list[ThemeEvidenceLink]:
    """Fired cross-feature insights whose linked sections touch this theme — carrying the
    insight's own provenance band so a classical/AV insight never outranks a Raman one."""
    from app.raman_saab.insight_digest import _lean_of
    out: list[ThemeEvidenceLink] = []
    hset = set(houses)
    for fi in getattr(r, "insights", ()) or ():
        ih = set(getattr(fi.rule, "houses", ()) or ()) if hasattr(fi, "rule") else set()
        if ih and not (ih & hset):
            continue
        if not ih:
            continue
        band = getattr(fi.rule, "band", "") or ""
        prov = {"raman": RAMAN_EXPLICIT, "classical": CLASSICAL_NONCITABLE,
                "av": CLASSICAL_NONCITABLE}.get(str(band).lower(), MODERN_SYNTHESIS)
        out.append(ThemeEvidenceLink(
            "citation", f"Insight ({band})", fi.detail[:120], "neutral",
            "r.insights @ synthesis_rules.py:101", prov))
    return out


def _convergence(headline, facets, links, r) -> tuple[Convergence, str, str]:
    """Count agreeing vs opposing INDEPENDENT direction-bearing axes (the support-house verdicts,
    the facet dashboard verdicts, D9, and yoga leans — NOT the headline itself, which would
    trivially agree). Returns (tier, reader_label, why). Always reports both poles; convergence
    is evidentiary agreement, never a probability."""
    from app.raman_saab.insight_digest import _lean_of
    head = _dir(_lean_of(headline))
    agree = oppose = 0
    for lk in links:
        if lk.axis not in ("verdict", "varga", "yoga"):
            continue
        # the primary-house rollup IS the headline — don't count it as its own witness
        if lk.label.startswith("House ") and "rollup" in lk.label and "(network)" not in lk.label:
            continue
        d = _dir(lk.lean)
        if d == 0 or head == 0:
            continue
        agree += (d == head)
        oppose += (d != head)
    d9 = any(lk.axis == "varga" and _dir(lk.lean) == head and head != 0 for lk in links)
    active = any(lk.axis == "dasha" for lk in links)
    present = agree + oppose
    # a NON-DIRECTIONAL headline (a 'mixed' rollup) has nothing for an axis to agree or disagree
    # with, so the counting loop above skips every link. Reporting that as WEAK/'aligned' would
    # claim an alignment that was never tested — say plainly that the headline is undecided.
    if head == 0:
        conv: Convergence = "MIXED"
    elif present >= 5 and oppose == 0 and d9 and active:
        conv = "VERY_HIGH"
    elif agree >= 4 and oppose <= 1:
        conv = "HIGH"
    elif present >= 3 and agree > oppose:
        conv = "MODERATE"
    elif present < 3:
        conv = "WEAK"
    else:
        conv = "MIXED"
    # reader label — 'weak' when few axes AGREE is misleading; call that 'lightly evidenced'
    if head == 0:
        label = "the headline itself is undecided"
    elif conv == "WEAK":
        label = "aligned, but lightly evidenced" if oppose == 0 else "little agreement"
    elif conv == "MIXED":
        label = "the evidence splits both ways"
    else:
        label = conv.replace("_", " ").lower() + " convergence"
    counted = ("the headline is undecided, so no axis can agree or oppose it (0 agree, 0 oppose)"
               if head == 0 else
               f"{agree} of {present} independent axes agree with the headline and "
               f"{oppose} oppose it")
    why = (f"{counted} "
           f"({'the navamsa confirms' if d9 else 'the navamsa is neutral/absent'}; "
           f"{'the running period lights it' if active else 'not currently lit'}); "
           f"an evidentiary count, not a probability.")
    return conv, label, why


def _contradictions(r, prim_house, pf, headline, facets, theme_name) -> tuple[Contradiction, ...]:
    """Classify the apparent conflicts and cite the precedence rule that resolves each — ONE
    consolidated statement per axis, never one line per matter (the old per-matter loop printed
    the same H4 grain tension three times)."""
    from app.raman_saab import detailed_report as dr
    from app.raman_saab.insight_digest import _lean_of
    out: list[Contradiction] = []

    # B. house-vs-facet grain (the archetypal 'H4 afflicted but mother/comforts/schooling
    # favourable') -> PREC-1. Consolidated: name every facet whose own verdict differs from the
    # house rollup in ONE line.
    hlean = _dir(_lean_of(headline))
    differ = [m for m, v in facets if _dir(_lean_of(v)) != 0 and _dir(_lean_of(v)) != hlean]
    if differ and hlean != 0:
        other = "favourable" if hlean < 0 else "afflicted"
        out.append(Contradiction(
            "house vs its matters (different grain)",
            (f"House {prim_house} reads {headline} @ house_template.py:236",
             f"but {', '.join(differ)} each read {other} by their dedicated readers"),
            "PREC-1",
            f"The bhava is graded by its single weakest matter, so H{prim_house} reads "
            f"{headline}; each matter above is judged by its own dedicated reader. Both are "
            f"true at different grain — ask the matter for {', '.join(differ)}, the house for "
            f"the bhava as a whole.",
            parties=tuple(differ)))

    # D. split-status within the house -> PREC-3
    split = _safe(lambda: dr.signification_tenor_split(r.calibration.get(prim_house)), None)
    if split is not None and getattr(split, "majority", None) and \
            _dir(_lean_of(split.majority)) != 0 and _dir(_lean_of(split.majority)) != _dir(_lean_of(headline)):
        out.append(Contradiction(
            "house condition vs sub-matters",
            (f"Headline {headline} (weakest matter)",
             f"Majority of significations read {split.majority} "
             f"({split.favourable}F/{split.afflicted}A/{split.mixed}M) @ detailed_report.py:764"),
            "PREC-3",
            "The headline is the weakest decided matter, not the house's overall tenor; the "
            "split is disclosed, the verdict unchanged."))

    # E. strength vs beneficence -> GBB-9
    L = _safe(lambda: dr._lagna_ledger(pf.significations[0]) if pf.significations else None, None)
    if L is not None and (getattr(L, "bhava_bala_strong", None) or getattr(L, "lord_strong", None)) \
            and _lean_of(headline) == "adverse":
        out.append(Contradiction(
            "strength vs beneficence",
            (f"House {prim_house} is strong (Bhava Bala / lord) @ house_template.py:187",
             f"yet the verdict is {headline}"),
            "GBB-9",
            "A strong-but-afflicted house delivers its difficulty with unusual force; strength "
            "is magnitude, not direction (PREC-2)."))

    # F. general vs divisional (D9) -> PREC-11 (the D1 core decides, the divisional
    # corroborates). NB: this was mis-cited as PREC-5 in six places; PREC-5 governs the
    # Laghu Parashari TIMING bands yielding to Raman, nothing to do with divisionals.
    m = _matter_reading(r, prim_house)
    if m is not None and _nav_lean(m.navamsa) != "neutral" and \
            _dir(_nav_lean(m.navamsa)) != _dir(_lean_of(headline)) and _dir(_lean_of(headline)) != 0:
        out.append(Contradiction(
            "natal vs divisional confirmation",
            (f"D1 rollup {headline}", f"D9 navamsa: {m.navamsa} @ synthesis.py:39"),
            "PREC-11",
            "The navamsa modulates confidence in the natal indication; it does not overturn "
            "the D1 verdict."))

    return tuple(out)


def _varga_relation(r, prim_house, domain) -> str:
    m = _matter_reading(r, prim_house)
    if m is None or not m.navamsa:
        return "D9-only (no dedicated varga reader for this theme)"
    nl = _nav_lean(m.navamsa)
    if nl == "favourable":
        return "confirms"
    if nl == "adverse":
        return "qualifies (D9 weakens)"
    return "neutral (D9 neither confirms nor weakens)"


#: Raman's four fructification grades, strongest first (HTJAH-I:1592-1596, 1635-1640).
_TIER_ORDER = ("par excellence", "ordinary", "limited", "feeble")


def _theme_timing(r, name, prim_house, houses, dom_planets) -> tuple[str, Optional[tuple[int, int]]]:
    """A DIFFERENTIAL, FORWARD-LOOKING timing note, graded by Raman's own fructification scheme.

    Scans the bhuktis ahead of ``ref_jd`` through the engine's shared ``graded_buckets`` (the ONE
    implementation of HTJAH-I:1592-1596 — par excellence / ordinary / limited / feeble) and names
    the window in which this theme's primary bhava is best supported. Three deliberate choices:

    - **Forward only.** A reader asks "when next", not "when was the high-water mark since birth";
      scanning the whole life also makes almost every house peak in the same early bhukti.
    - **Same-lord bhuktis are skipped.** When MD lord == AD lord the association test is trivially
      true, so that bhukti grades par excellence for nearly every house — a degenerate window that
      would drown the differential signal (measured: 11 of 12 houses on one chart).
    - **A theme that never reaches the top tier says so.** That is a real finding (a bhava the
      coming years support only weakly), not an absence to hide.

    Timed-indication idiom throughout — a window that supports an indication, never a decree that
    an event occurs. Silent (empty) when the timeline carries no forward bhukti for the house.

    Returns the clause AND the window's ``(start_year, end_year)``, so the longevity frame can
    read the same window inside the band without re-scanning the timeline (PREC-8)."""
    from app.raman_saab import detailed_report as dr
    ref = getattr(r, "ref_jd", 0.0)
    periods = getattr(getattr(r, "timeline", None), "periods", ()) or ()
    best: Optional[tuple[int, str, str, str, int, int]] = None
    for tp in periods:
        per = tp.period
        if getattr(per, "end_jd", 0.0) <= ref:          # already past
            continue
        if per.antar and per.maha == per.antar:         # degenerate same-lord bhukti
            continue
        _assoc, buckets = _safe(lambda: dr.graded_buckets(tp, r.chart), (False, {}))
        for tier, items in (buckets or {}).items():
            if not any(getattr(a, "house", None) == prim_house for a in items):
                continue
            rank = _TIER_ORDER.index(tier) if tier in _TIER_ORDER else len(_TIER_ORDER)
            if best is None or rank < best[0]:
                best = (rank, tier, per.maha, per.antar or "",
                        _year(per.start_jd), _year(per.end_jd))
    if best is None:
        return "", None
    _rank, tier, maha, antar, y0, y1 = best
    bhukti = f"{maha}/{antar}" if antar else maha
    span = f"{y0}-{y1}" if y1 != y0 else str(y0)
    # both variants open on the same noun phrase so the clause reads correctly standalone AND
    # after the "In time, …" connector the final interpretation puts in front of it
    if tier == _TIER_ORDER[0]:
        return (f"the {bhukti} bhukti ({span}) is the window ahead that best supports it — "
                f"H{prim_house} grades {tier} there on Raman's fructification scheme "
                f"(HTJAH-I:1592-1596).", (y0, y1))
    return (f"the {bhukti} bhukti ({span}) offers the strongest support ahead, and only at the "
            f"{tier} grade — H{prim_house} is not carried to the top tier in the years shown "
            f"(HTJAH-I:1592-1596).", (y0, y1))


def _final_interpretation(name, headline, convergence, conv_label, contradictions, activation,
                          dom_planets, facets, driver_conc=(), dissent=None) -> str:
    """A single astrologer's sentence, not a template. Names the driving planet AND what the
    independent measures say about it (force vs intent), the verdict, and — where the bhava's own
    testimony ledger runs against the verdict, or its matters read against its headline — that
    split as the theme's own story rather than a bolted-on 'a tension is disclosed'."""
    lead = dom_planets[0] if dom_planets else "the chart"
    body = f"{name} reads {headline}, carried chiefly by {lead}"
    # The lead graha's own condition cross-checked against the theme's verdict. Two questions:
    # do its measures agree with EACH OTHER (force vs intent), and does its quality agree with the
    # verdict it is said to carry? A favourable matter carried by a Kashta-dominant graha, or an
    # afflicted one carried by a benefic graha, is exactly the sort of cross-technique tension the
    # report computed on both sides and never put together.
    from app.raman_saab.insight_digest import _lean_of
    lead_c = next((g for g in driver_conc if g.planet == lead), None)
    if lead_c is not None and lead_c.ishta is not None and lead_c.kashta is not None:
        harmful = lead_c.kashta > lead_c.ishta
        hlean = _lean_of(headline)
        # the cross-check against the VERDICT is the more informative of the two clauses, so it
        # supersedes the bare force-vs-intent note rather than being appended to it (saying both
        # restates the same fact twice in one sentence)
        if hlean == "favourable" and harmful:
            body += (" — whose own potency is Kashta-dominant, so the good this brings tends to "
                     "arrive costly")
        elif hlean == "adverse" and not harmful:
            body += (", though that graha is benefic in potency — the difficulty here is "
                     "structural rather than ill-intentioned")
        elif "strong but harmful" in lead_c.pattern:
            body += " — which acts with force but toward a difficult end"
        elif "benefic but weak" in lead_c.pattern:
            body += " — benefic in intent but short of the force to carry it"
    grain = next((c for c in contradictions if c.governing == "PREC-1"), None)
    if grain and grain.parties:
        # the house-vs-matters split IS the interpretation here. The differing facets come from
        # `parties` as data — recovering them by slicing the pole PROSE (as this once did) breaks
        # silently the moment the contradiction's wording changes.
        body += (f"; the bhava as a whole takes its tone from its weakest matter, though "
                 f"{', '.join(grain.parties)} read the other way")
    elif convergence in ("VERY_HIGH", "HIGH"):
        body += ", and the independent readings converge strongly"
    else:
        # the reader-facing label, so the sentence and the heading never disagree
        body += f" ({conv_label})"
    # NB: the testimony-ledger divergence used to get its own clause here. DissentSummary now
    # counts that ledger among the cross-checks, so stating it twice said the same thing twice —
    # the full ledger still renders in its own "Do the techniques agree?" line on every surface.
    # Ashtakavarga is a wholly independent measurement of the same grahas: when every driver is
    # poorly supported in the very sign the bhava occupies, a favourable verdict is resting on
    # something AV does not corroborate, and that is worth one clause
    # NB: the per-system dissent clauses that used to be chained here (Ashtakavarga withholding
    # support, the assigned division disagreeing) are gone. DissentSummary now states them
    # together, which is both more informative and shorter than three separate clauses;
    # repeating them inline made the sentence a 560-character paragraph.
    if dissent is not None and dissent.dissenting:
        # named, never counted into a grade: Raman states no numeric N-testimonies rule
        # (HTJAH-I:495) and head-counting influences was measured against his own reasoning
        # at 0 of 7 (COMPARATIVE_WEIGHING.md)
        body += (f". Reading against it: {', '.join(dissent.dissenting)} — each at its own tier, "
                 f"none able to overturn the verdict")
    if activation:
        # the narrative sentence carries the clause without its citation — the Timing line
        # renders the same note in full, so traceability is not lost by shortening here
        body += ". In time, " + activation.split(" (HTJAH-")[0].rstrip(" .—-")
    return body.rstrip(".") + "."


def _weight(convergence, links, r, houses, dom_planets) -> float:
    """Ranking score for the spine — how load-bearing a theme is, NOT a probability or a verdict.

    Four terms, each of which actually varies across themes:

    - **convergence** — how well the independent readings agree (the dominant term).
    - **centrality** — whether the chart's own busiest grahas drive it (census-ranked biographies).
    - **network breadth** — how many support bhavas survived the evidence gate, i.e. how widely
      the theme is wired into the rest of the chart.
    - **digest salience** — the engine's own ranked digest already says what stands out.

    The previous version added ``len({axes}) * 0.3``, which measured nothing: every theme carries
    the same 5-6 axes, so it was a constant offset masquerading as a signal."""
    base = {"VERY_HIGH": 5.0, "HIGH": 4.0, "MODERATE": 3.0, "MIXED": 2.0, "WEAK": 1.0}[convergence]
    # centrality — the chart's top-3 census grahas that actually drive this theme
    top = [b.planet for b in (getattr(r, "planet_bios", ()) or ())[:3]]
    centrality = min(0.8, 0.4 * sum(1 for p in dom_planets if p in top))
    breadth = 0.25 * max(0, len(set(houses)) - 1)
    # digest salience — highest-ranked digest item touching any of the theme's houses
    prio = 0.0
    hset = set(houses)
    for i, it in enumerate(getattr(getattr(r, "digest", None), "items", ()) or ()):
        if set(getattr(it, "houses", ()) or ()) & hset:
            prio = max(prio, 1.0 - i * 0.1)
    return base + centrality + breadth + prio


def _connections(themes) -> tuple[ThemeConnection, ...]:
    """Discover a shared MECHANISM between two themes and say what it does on each side.

    A connection needs EITHER the same CHIEF driving graha (``dominant_planets[0]`` equal), OR one
    theme's PRIMARY house sitting inside the other's network. A shared broad karaka does not
    qualify — Jupiter signifies half the chart, and that produced the old "everything connects to
    wealth" noise.

    What changed here is the NOTE. It used to be a template — *"A and B overlap at H6, tying the
    two areas together"* — which restates the join without saying anything about the chart: the
    reader learns that two themes share a house, not what that house is doing in each. A shared
    bhava is the SAME bhava wearing two roles, so the note now names the role on each side (whose
    primary it is, what it contributes to the other), sets the two verdicts against each other
    (one bhava that is the strength of one theme and the strain of the other is a real finding),
    and for a shared graha reports that graha's own measured condition — the concordance the layer
    already computed — because a tie carried by a Kashta-dominant, weak-by-Shadbala graha means
    something different from one carried by a strong benefic.

    Ranking and fairness: ties are ordered by strength (a shared chief graha outranks a structural
    overlap) and then by the combined evidence weight of both ends, and NO theme may appear in
    more than ``_CONN_PER_THEME`` connections. Without that cap the chart's busiest theme took
    four of six slots and crowded out every other pairing — an artefact of it having the widest
    network, not a finding about the nativity."""
    from app.raman_saab.insight_digest import _HOUSE_LABEL
    picks = list(themes)
    scored: list[tuple[float, ThemeConnection, str, str]] = []
    seen: set[frozenset] = set()
    for i, a in enumerate(picks):
        for b in picks[i + 1:]:
            key = frozenset((a.theme_id, b.theme_id))
            if key in seen:
                continue
            lead_a = a.dominant_planets[0] if a.dominant_planets else None
            lead_b = b.dominant_planets[0] if b.dominant_planets else None
            same_lead = bool(lead_a) and lead_a == lead_b
            prim_overlap = (a.houses and a.houses[0] in b.houses) or \
                           (b.houses and b.houses[0] in a.houses)
            if not same_lead and not prim_overlap:
                continue
            seen.add(key)
            if same_lead:
                shared, note = lead_a, _graha_tie_note(a, b, lead_a)
                tier = 2.0
            else:
                h = a.houses[0] if a.houses and a.houses[0] in b.houses else b.houses[0]
                shared, note = f"H{h}", _house_tie_note(a, b, h, _HOUSE_LABEL)
                tier = 1.0
            scored.append((tier + (a.evidence_weight + b.evidence_weight) / 1000.0,
                           ThemeConnection(a.name, b.name, shared, note), a.name, b.name))

    scored.sort(key=lambda row: -row[0])
    out: list[ThemeConnection] = []
    used: dict[str, int] = {}
    for _w, conn, na, nb in scored:
        if used.get(na, 0) >= _CONN_PER_THEME or used.get(nb, 0) >= _CONN_PER_THEME:
            continue
        used[na] = used.get(na, 0) + 1
        used[nb] = used.get(nb, 0) + 1
        out.append(conn)
        if len(out) >= 6:
            break
    return tuple(out)


#: no theme may carry more than this many connections. The busiest theme has the widest network
#: by construction, so an uncapped list reports its breadth, not the chart's fabric.
_CONN_PER_THEME = 2


def _tie_verdict_clause(a, b) -> str:
    """What the shared mechanism MEANS given the two verdicts it joins — the part a template
    cannot supply. Same verdict on both ends is one story; opposite verdicts on one shared
    mechanism is the more interesting one, and it is exactly what the reader wants named."""
    va, vb = a.headline_verdict, b.headline_verdict
    if va == vb:
        return f"Both ends read {va}, so the tie runs the same way on each side."
    # only a true inversion (favourable one end, afflicted the other) earns the strength/strain
    # reading. A favourable-vs-mixed pair is a difference of degree, and saying "strain" of a
    # mixed verdict overstates what the engine decided.
    poles = {va, vb}
    if poles == {"favourable", "afflicted"}:
        return (f"{a.name} reads {va} while {b.name} reads {vb} — the same mechanism is the "
                f"strength of one and the strain of the other, which is why they move together "
                f"without moving in the same direction.")
    return (f"{a.name} reads {va} while {b.name} reads {vb} — one mechanism, but it does not "
            f"deliver the same grade at both ends.")


def _graha_tie_note(a, b, lead: str) -> str:
    """Two themes led by one graha — reported WITH that graha's own measured condition.

    The layer already cross-checks every driver's force (Shadbala) against its intent
    (Ishta/Kashta) in ``driver_concordance``. A tie carried by a Kashta-dominant, weak graha is a
    different fact from one carried by a strong benefic, and naming the graha without naming its
    condition throws that away."""
    cond = ""
    gc = next((g for g in getattr(a, "driver_concordance", ()) if g.planet == lead), None)
    if gc is None:
        gc = next((g for g in getattr(b, "driver_concordance", ()) if g.planet == lead), None)
    if gc is not None:
        bits = []
        if getattr(gc, "ishta", None) is not None and getattr(gc, "kashta", None) is not None:
            bits.append("Kashta-dominant" if gc.kashta > gc.ishta else "Ishta-dominant")
        if getattr(gc, "avastha", ""):
            bits.append(f"avastha {gc.avastha}")
        if getattr(gc, "pattern", ""):
            bits.append(gc.pattern)
        if bits:
            cond = f" {lead} itself reads {', '.join(bits)}, so that is the quality it carries " \
                   f"into both."
    return (f"{lead} leads both {a.name} and {b.name} — one graha carries the two, so they ripen "
            f"and strain on the same clock.{cond} {_tie_verdict_clause(a, b)}")


def _house_tie_note(a, b, h: int, labels) -> str:
    """Two themes joined at one bhava — reported as the SAME bhava in two roles.

    Which theme owns it as its primary and which merely draws on it is the whole content of the
    tie, and the old template stated neither. Where the shared bhava also hosts a named facet of
    the borrowing theme, that facet is the concrete channel and is named too."""
    area = labels.get(h, f"house {h}")
    owner, borrower = (a, b) if (a.houses and a.houses[0] == h) else (b, a)
    role = (f"H{h} ({area}) is the own bhava of {owner.name}; {borrower.name} draws on it as "
            f"part of its network")
    # the concrete channel, when the borrowing theme names a facet that lives in the shared bhava
    facet = next((m for m, _v in getattr(borrower, "sub_matters", ()) or ()
                  if m.lower() in area.lower()), "")
    if facet:
        role += f", through {facet}"
    return f"{role}. {_tie_verdict_clause(a, b)}"


def _bhava_concordance(r, house: int) -> Optional[BhavaConcordance]:
    """Re-read the engine's own testimony ledger for one bhava (``r.preponderance``) into the
    concordance question: does the verdict agree with the weight of the testimony behind it?

    Nothing is recomputed — the ledger already separates Raman's three-fold CORE (lord, karaka,
    navamsa) from the OVERLAY (Bhava Bala, SAV, matter-varga, majority tenor, yogas) and grades
    the house 'well-corroborated' or 'contested'. What was missing is the sentence."""
    pr = getattr(r, "preponderance", None)
    row = next((h for h in getattr(pr, "houses", ()) or () if h.house == house), None)
    if row is None:
        return None
    def _split(klass: str, want: str) -> tuple[str, ...]:
        return tuple(f"{t.name} ({t.value})" for t in row.testimonies
                     if t.klass == klass and want in (t.lean or ""))
    core_for, core_against = _split("core", "favourable"), _split("core", "adverse")
    ov_for, ov_against = _split("overlay", "favourable"), _split("overlay", "adverse")

    # the divergence: the house's verdict pulling against its own preponderance
    verdict, prep = row.verdict, row.preponderance
    divergence = ""
    if verdict == "afflicted" and prep == "benefic":
        divergence = (f"H{house} reads {verdict}, yet the weight of its testimony is {prep} "
                      f"({row.favourable} favourable to {row.adverse} adverse). The bhava takes "
                      f"its grade from its weakest decided matter, not from a majority vote — so "
                      f"the affliction is real but narrow, and the support around it is real too.")
    elif verdict == "favourable" and prep == "adverse":
        divergence = (f"H{house} reads {verdict} while the weight of its testimony is {prep} "
                      f"({row.adverse} adverse to {row.favourable} favourable) — the favourable "
                      f"grade rests on fewer supports than the house's overall tenor suggests.")

    if divergence:
        reading = divergence
    elif row.status == "well-corroborated":
        reading = (f"H{house} is {verdict} and its independent testimonies concur "
                   f"({row.favourable} favourable, {row.adverse} adverse; core "
                   f"{len(core_for)}-{len(core_against)}) — a well-corroborated reading.")
    else:
        reading = (f"H{house} is {verdict}; its testimonies are {row.status} "
                   f"({row.favourable} favourable, {row.adverse} adverse) — read it with the "
                   f"spread in mind rather than as a settled verdict.")
    return BhavaConcordance(
        house=house, verdict=verdict, preponderance=prep, status=row.status,
        core_for=core_for, core_against=core_against,
        overlay_for=ov_for, overlay_against=ov_against,
        divergence=divergence, reading=reading)


def _graha_concordance(r) -> tuple[GrahaConcordance, ...]:
    """Cross-check the independent readings of each graha the engine already computed.

    Shadbala answers "how much force?"; Ishta/Kashta answers "to what end?" — they are DIFFERENT
    axes, and the engine has always computed both without ever setting them side by side. The
    named patterns below are Raman's own strength-is-not-direction distinction (PREC-2 / GBB-9)
    made legible: a strong graha with Kashta dominant delivers its difficulty with force."""
    from app.raman_saab.primitives import deeptadi as _deeptadi
    from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED, is_powerful
    states = _safe(lambda: _deeptadi.chart_states(r.chart), {}) or {}
    planets = getattr(getattr(r, "chart", None), "planets", {}) or {}
    out: list[GrahaConcordance] = []
    for name, p in planets.items():
        ru = (p.shadbala_rupas.total / 60.0) if getattr(p, "shadbala_rupas", None) else None
        ish, kas = getattr(p, "ishta", None), getattr(p, "kashta", None)
        st = states.get(name)
        avastha = st[0] if st else ""
        flags = tuple(f for f, on in (("vargottama", getattr(p, "vargottama", False)),
                                      ("retrograde", getattr(p, "retrograde", False)),
                                      ("combust", (getattr(p, "combust_fraction", 0) or 0) >= 0.5))
                      if on)
        # "strong" is Raman's OWN per-planet minimum (GBB-8:303), not a cross-chart median: each
        # graha has its own required rupas, so comparing them to each other would misgrade both
        # the naturally strong and the naturally weak.
        required = MIN_REQUIRED.get(name)
        strong = bool(ru is not None and _safe(lambda: is_powerful(name, ru), None))
        benefic = (ish is not None and kas is not None and ish > kas)
        # the four classical quadrants of force x intent, plus the chayagraha case
        if ish is None or kas is None:
            pattern = "no Ishta/Kashta (chayagraha — the nodes carry no Shadbala)"
            agreement = "not applicable"
            reading = (f"{name} is a shadowy planet: the strength systems do not measure it, so "
                       f"it is read through its dispositor and co-tenants.")
        elif strong and benefic:
            pattern = "strong and benefic"
            agreement = "unanimous"
            reading = (f"{name} carries force ({ru:.2f} rupas, over its {required} required) and its "
                       f"potency is benefic (Ishta {ish:.0f} over Kashta {kas:.0f}) — capacity "
                       f"and intent agree.")
        elif (not strong) and (not benefic):
            pattern = "weak and harmful"
            agreement = "unanimous"
            reading = (f"{name} is short of force ({ru:.2f} rupas against its {required} required) "
                       f"and Kashta-dominant (Kashta {kas:.0f} over Ishta {ish:.0f}) — every "
                       f"measure concurs.")
        elif strong and not benefic:
            pattern = "strong but harmful (strength is magnitude, not direction)"
            agreement = "split"
            reading = (f"{name} is well-supplied with force ({ru:.2f} rupas, over its {required} "
                       f"required) but Kashta-dominant "
                       f"(Kashta {kas:.0f} over Ishta {ish:.0f}) — it acts with power toward a "
                       f"difficult end. Strength is magnitude, never direction (PREC-2, GBB-9).")
        else:
            pattern = "benefic but weak"
            agreement = "split"
            reading = (f"{name} is benefic in potency (Ishta {ish:.0f} over Kashta {kas:.0f}) but "
                       f"short of force ({ru:.2f} against its {required} required) — well-meaning "
                       f"and limited in what it "
                       f"can carry through.")
        if avastha:
            reading += f" It acts from the {avastha} state."
        if flags:
            reading += f" ({', '.join(flags)})"
        out.append(GrahaConcordance(
            planet=name, rupas=ru, ishta=ish, kashta=kas, avastha=avastha, flags=flags,
            agreement=agreement, pattern=pattern, reading=reading))
    # busiest grahas first, so the reader meets the chart's main actors at the top
    order = {b.planet: i for i, b in enumerate(getattr(r, "planet_bios", ()) or ())}
    out.sort(key=lambda g: order.get(g.planet, 99))
    return tuple(out)


def _divisional_checks(r, spec, facets, headline) -> tuple[DivisionalCheck, ...]:
    """Set this theme's OWN divisional deep-reads against its natal verdict.

    Two ways a division bears on a theme: it is the varga the roster assigns to the bhava (D-2 for
    wealth, D-7 for children, D-30 for health...), or its reading names one of the theme's facet
    matters (D-12 names MOTHER and FATHER, D-16 COMFORTS, D-24 EDUCATION — all facets of other
    bhavas). Both are matched from the engine's own headline text; nothing is recomputed and no
    verdict is altered — a varga corroborates the D1 core, which decides (PREC-11)."""
    from app.raman_saab.insight_digest import _lean_of
    rows = getattr(r, "divisional", ()) or ()
    hlean = _lean_of(headline)
    out: list[DivisionalCheck] = []
    seen: set[str] = set()
    for head, _body in rows:
        label, _, verdict = str(head).partition(" - ")
        if not verdict:                      # a division with no verdict of its own (D-27/40/45/60)
            continue
        n = None
        if label.startswith("D-"):
            # a bare "D-" splits to [] and [0] would raise; the varga number is optional here
            parts = label[2:].split()
            digits = parts[0] if parts else ""
            n = int(digits) if digits.isdigit() else None
        facet_hit = next((m for m, _v in facets if m.upper() in verdict.upper()), None)
        is_own = (spec.varga is not None and n == spec.varga)
        if not is_own and facet_hit is None:
            continue
        if label in seen:
            continue
        seen.add(label)
        vlean = _lean_of(verdict.lower())
        if is_own:
            if vlean == "neutral" or hlean == "neutral":
                relation, note = "reads its own matter", (
                    f"{label} reads this bhava's own division; neither side carries a clean "
                    f"direction to compare.")
            elif vlean == hlean:
                relation, note = "concurs", (
                    f"{label} — the division assigned to this bhava — reads the same way as the "
                    f"rasi, so the natal indication is confirmed in its own varga.")
            else:
                relation, note = "diverges", (
                    f"{label} reads against the rasi here. A division modulates confidence in the "
                    f"natal indication; it does not overturn it (PREC-11), so the verdict stands "
                    f"and the disagreement is disclosed.")
        else:
            relation, note = "reads a facet", (
                f"{label} bears on this theme through its {facet_hit} facet.")
        out.append(DivisionalCheck(varga=label, verdict=verdict.strip(), relation=relation,
                                   note=note))
    return tuple(out)


def _distinctiveness(r, houses) -> tuple[Distinctiveness, ...]:
    """What in this theme is statistically UNUSUAL — a re-read of the calibration layer's own
    per-signification rarity (``r.distinctive``). Agreement across techniques means little when the
    thing agreed on is what nearly every chart shows; this is the disclosure that keeps the
    concordance honest (CLAUDE.md ★★ Measured Truth)."""
    hset = set(houses)
    out: list[Distinctiveness] = []
    for house, entry in getattr(r, "distinctive", ()) or ():
        if house not in hset:
            continue
        out.append(Distinctiveness(
            house=house,
            signification=str(getattr(entry, "signification", "")),
            verdict=str(getattr(entry, "verdict", "")),
            rarity=str(getattr(entry, "rarity", "")),
            population_note=str(getattr(entry, "note", ""))))
    return tuple(out)


#: the three bhavas the soul layer reads independently (SoulCore verdict field -> house)
_KARMIC_ASPECTS = (("poorvapunya", 5), ("dharma", 9), ("moksha", 12))


def _karmic_lens(r, house: int, natal_verdict: str) -> Optional[KarmicLens]:
    """The karmic layer's own verdict on this bhava, beside the natal one. Walled: recorded for
    the reader, never counted as corroboration and never able to move a verdict."""
    core = getattr(getattr(r, "soul", None), "core", None)
    if core is None:
        return None
    for aspect, h in _KARMIC_ASPECTS:
        if h != house:
            continue
        kv = getattr(core, f"{aspect}_verdict", None)
        if not kv:
            return None
        relation = "concurs" if str(kv) == str(natal_verdict) else "differs"
        if relation == "concurs":
            note = (f"The karmic layer reads {aspect} as {kv}, the same way the rasi reads this "
                    f"bhava. A separate lens reaching the same place — but a WALLED one: the "
                    f"Jaimini layer never feeds the Parashari verdict, so this corroborates "
                    f"nothing and is excluded from the convergence count.")
        else:
            note = (f"The karmic layer reads {aspect} as {kv} where the rasi reads this bhava "
                    f"{natal_verdict}. The two are answering different questions and the layer is "
                    f"WALLED — the Jaimini reading never feeds the Parashari verdict, so this is "
                    f"recorded as a second lens, not as a contradiction to resolve.")
        return KarmicLens(house=house, aspect=aspect, karmic_verdict=str(kv),
                          natal_verdict=str(natal_verdict), relation=relation, note=note)
    return None


def _theme_yogas(r, houses, yoga_house_bearings) -> tuple[YogaReading, ...]:
    """The yogas bearing on this theme, read whole: promise + measured strength + cancellation +
    the periods when their participants actually run. Pure re-read across r.yogas / r.yoga_deep /
    r.yoga_timing — the layer computes no yoga and grades none."""
    hset = set(houses)
    deep = {d.name: d for d in getattr(r, "yoga_deep", ()) or ()}
    ref = getattr(r, "ref_jd", 0.0)
    timing: dict[str, list] = {}
    for t in getattr(r, "yoga_timing", ()) or ():
        timing.setdefault(t.yoga_name, []).append(t)
    out: list[YogaReading] = []
    for y in getattr(r, "yogas", ()) or ():
        bearing = _safe(lambda: yoga_house_bearings(r.chart, y), None)
        if not bearing or not (bearing & hset):
            continue
        name = getattr(y, "name", "")
        d = deep.get(name)
        parts: list[str] = []
        for pf in (getattr(d, "participants", ()) or ()) if d else ():
            ru = getattr(pf, "rupas", None)
            parts.append(f"{pf.planet} (H{pf.house}, {pf.dignity}"
                         + (f", {ru:.2f} rupas" if ru is not None else "") + ")")
        wins: list[str] = []
        ahead = False
        for t in sorted(timing.get(name, ()), key=lambda x: x.period_start_jd):
            y0, y1 = _year(t.period_start_jd), _year(t.period_end_jd)
            tag = getattr(getattr(t, "quality", None), "tag", "") or ""
            wins.append(f"{t.planet} {t.role} {y0}-{y1}" + (f" ({tag})" if tag else ""))
            if t.period_end_jd > ref:
                ahead = True
        out.append(YogaReading(
            name=name, kind=getattr(y, "kind", "") or "",
            effect=getattr(y, "effect", "") or "",
            rank=getattr(d, "comparison_rank", None) if d else None,
            strength_note=(getattr(d, "strength_note", "") or "") if d else "",
            cancellation=(getattr(d, "cancellation_note", "") or "") if d else "",
            participants=tuple(parts), windows=tuple(wins), ahead=ahead))
    out.sort(key=lambda z: (z.rank if z.rank is not None else 99))
    return tuple(out)


def _house_sign(chart, house: int) -> int:
    """The sign occupying a whole-sign house (the project's locked whole-sign convention)."""
    return ((getattr(chart, "asc_sign", 1) - 1 + house - 1) % 12) + 1


def _av_support(r, prim_house, dom_planets) -> tuple[AshtakavargaSupport, ...]:
    """The theme's driving grahas measured by Ashtakavarga in the sign its bhava occupies.

    ``BavMatrixRow.bindus`` is a 12-tuple indexed by sign (verified against the row's own
    ``seat_sign``/``seat_bindus``). Four bindus is the per-sign average of a 337-point SAV over
    twelve signs and eight contributors, so it is the natural break — above it the graha is
    supported where it must act, below it it is not."""
    chart = getattr(r, "chart", None)
    if chart is None:
        return ()
    sign = _house_sign(chart, prim_house)
    bav = {row.planet: row for row in getattr(r, "bav_matrix", ()) or ()}
    red = {row.planet: row for row in getattr(r, "bav_reduced", ()) or ()}
    pinda = {row.planet: row for row in getattr(r, "sodya_pinda", ()) or ()}
    out: list[AshtakavargaSupport] = []
    for p in dom_planets:
        row = bav.get(p)
        if row is None:                      # the nodes carry no Ashtakavarga of their own
            continue
        b = row.bindus[sign - 1]
        rr = red.get(p)
        reduced = rr.reduced[sign - 1] if rr is not None else b
        verdict = ("well supported" if b >= 5 else
                   "about average" if b == 4 else "poorly supported")
        out.append(AshtakavargaSupport(
            planet=p, house=prim_house, sign=sign, bindus=b, reduced=reduced,
            sodya_pinda=getattr(pinda.get(p), "total", 0) or 0, verdict=verdict))
    return tuple(out)


def _transit_notes(r, houses, dom_planets) -> tuple[TransitNote, ...]:
    """The slow-movers currently transiting this theme's houses, or transiting for one of its
    driving grahas. Subordinate by construction: the engine's own ``net_good`` (which already
    applies vedha) is reported, and no direction is derived from it here."""
    hset = set(houses)
    drivers = set(dom_planets)
    out: list[TransitNote] = []
    for row in getattr(r, "gochara", ()) or ():
        hl = getattr(row, "house_from_lagna", None)
        if hl not in hset and getattr(row, "planet", None) not in drivers:
            continue
        vedha = tuple(getattr(row, "vedha_by", ()) or ())
        good = bool(getattr(row, "gochara_good", False))
        net = bool(getattr(row, "net_good", False))
        note = (f"{row.planet} transits the {row.house_from_moon}th from the Moon — "
                + ("a favourable Gochara" if good else "not a favourable Gochara"))
        if vedha:
            note += f", obstructed (vedha) by {', '.join(vedha)}"
        note += (f"; the engine's net reading is "
                 f"{'favourable' if net else 'not favourable'}. Transits are catalytic only — "
                 f"all conclusions rest primarily on the dasha (HTJAH-II:4679-4687).")
        out.append(TransitNote(
            planet=getattr(row, "planet", ""), house_from_moon=getattr(row, "house_from_moon", 0),
            gochara_good=good, bav_bindus=getattr(row, "bav_bindus", None),
            vedha_by=vedha, net_good=net, note=note))
    return tuple(out)


_MEASURED_TRUTH_SPAN = (
    "The numeric span is a cross-check on the band, never a forecast: the validation program "
    "measured no chart-specific death-timing signal on 22,177 verified charts "
    "(REAL_OUTCOME_GENERALIZATION.md). This is a disclosure of Raman's method, not a prediction.")


def _birth_year(r) -> int:
    """The nativity's calendar year, from the engine's own BirthData."""
    return int(getattr(getattr(r, "birth", None), "year", 0) or 0)


def _span_end_year(r) -> int:
    """The calendar year the ayurdaya band reaches.

    JD arithmetic on the project's Vedic-year constant, never ``timedelta`` (CLAUDE.md): the
    span is a count of years from the birth moment, so it is added to ``chart.jd_ut`` and read
    back through ``swe.revjul`` rather than approximated on the calendar."""
    jd0 = getattr(getattr(r, "chart", None), "jd_ut", 0.0) or 0.0
    yrs = float(getattr(r, "longevity_years", 0.0) or 0.0)
    if not jd0 or not yrs:
        return 0
    from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR as _DPY
    return _year(jd0 + yrs * _DPY)


def _maraka_window_rows(r) -> tuple[tuple[str, str, int, str], ...]:
    """The maraka-tier bhuktis carrying Raman's classical Saturn signal, FORWARD of ``ref_jd``.

    Raman's step two, and only after the band: a maraka period is fixed by the 2nd/7th-lord
    scheme, and its "last signal" is Ayushkaraka Saturn transiting the 8th from birth or its
    trines during that period (HTJAH-II:4846-4849). The engine computed these confluences and
    the integrated reading never named one. Deduplicated per bhukti — the same Venus/Saturn
    period can carry several separate Saturn passes and that is one window, not three."""
    ref = getattr(r, "ref_jd", 0.0)
    span_to = _span_end_year(r)
    seen: dict[str, tuple[str, str, int, str]] = {}
    for c in getattr(r, "maraka_saturn", ()) or ():
        if getattr(c, "window_end_jd", 0.0) <= ref:
            continue
        bhukti = f"{c.maha}/{c.antar}" if getattr(c, "antar", "") else c.maha
        y0, y1 = _year(c.window_start_jd), _year(c.window_end_jd)
        span = f"{y0}-{y1}" if y1 != y0 else str(y0)
        standing = ("beyond the band" if span_to and y0 > span_to
                    else "inside the band" if span_to else "")
        prev = seen.get(bhukti)
        if prev is None or c.score > prev[2]:
            seen[bhukti] = (bhukti, span, int(c.score), standing)
    return tuple(sorted(seen.values(), key=lambda row: int(row[1].split("-")[0])))


def _activation_in_span(r, years: Optional[tuple[int, int]]) -> str:
    """Read ONE theme's forward window inside the longevity band (PREC-8).

    Two things the reader could not get before: the window's AGE (a bhukti labelled 2034-2035
    means nothing until it is "the 45th year"), and whether it coincides with a maraka-tier
    bhukti carrying the classical Saturn signal. Both are stated in the timed-indication idiom
    — the window is where an indication is supported, never a decree that an event occurs."""
    if years is None:
        return ""
    y0, y1 = years
    born = _birth_year(r)
    span_to = _span_end_year(r)
    if not born:
        return ""
    # Raman's own idiom is the ordinal year of life ("the 83rd year"), which tracks completed
    # age — his 83.54-year span reads as "about the 84th year". A window in calendar year Y is
    # therefore the (Y - birth_year)th year, NOT (Y - birth_year + 1): off by one the other way
    # would put a 2034 window on a 1989 nativity in the 46th year when they turn 45 in it.
    a0, a1 = y0 - born, y1 - born
    age = f"the {_ordinal(a0)} year" if a0 == a1 else f"the {_ordinal(a0)}-{_ordinal(a1)} years"
    out = f"That window falls at {age} of life"
    if span_to:
        inside = y1 <= span_to
        out += (f", inside the band the ayurdaya cross-check gives (to about "
                f"the {_ordinal(int(round(float(getattr(r, 'longevity_years', 0.0)))))} year)."
                if inside else
                f", BEYOND the band the ayurdaya cross-check gives (about the "
                f"{_ordinal(int(round(float(getattr(r, 'longevity_years', 0.0)))))} year) — the "
                f"window is shown because the timeline reaches it, and disclosed as outside "
                f"the span rather than quietly dropped.")
    else:
        out += "."
    hits = [row for row in _maraka_window_rows(r)
            if _overlaps_years(row[1], y0, y1)]
    if hits:
        names = "; ".join(f"{b} ({sp}, tier-score {sc})" for b, sp, sc, _st in hits)
        out += (f" It coincides with a maraka-tier bhukti carrying the classical Saturn signal "
                f"— {names} — which Raman treats as classically sensitive (HTJAH-II:4846-4849). "
                f"{_MEASURED_TRUTH_SPAN}")
    return out


def _overlaps_years(span: str, y0: int, y1: int) -> bool:
    """True when a 'YYYY-YYYY' (or bare 'YYYY') span overlaps the closed interval [y0, y1]."""
    parts = span.split("-")
    try:
        s0 = int(parts[0])
        s1 = int(parts[1]) if len(parts) > 1 else s0
    except ValueError:
        return False
    return not (s1 < y0 or s0 > y1)


def _ordinal(n: int) -> str:
    """1 -> '1st', 83 -> '83rd' — Raman's own way of naming a year of life."""
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _weather_windows(r) -> tuple[WeatherWindow, ...]:
    """Every forward stretch of timing weather, from the four schemes the engine already ran.

    Forward-only against ``ref_jd`` (plus whatever is running AT it): a reader asks what is
    coming, and the past stretches are already narrated by the life-chapters. Contiguous runs of
    the same adverse confluence are merged — ``r.dasha_transit_adverse`` carries one row per
    Saturn pass, and three passes inside one Mahadasha are one rough stretch, not three.

    Each scheme is collected under its OWN guard. A single `_safe` around the whole function
    meant one malformed record anywhere took the entire calendar — and every theme's
    ``weather_on_window`` with it — down to ``()``, rendering nothing and logging nothing.
    Partial weather is a real reading; no weather is a silently missing section."""
    ref = getattr(r, "ref_jd", 0.0)

    def _sade_sati() -> list[WeatherWindow]:
        acc: list[WeatherWindow] = []
        for ph in getattr(r, "sade_sati_phases", ()) or ():
            if getattr(ph, "end_jd", 0.0) <= ref and not getattr(ph, "current", False):
                continue
            y0, y1 = _year(ph.start_jd), _year(ph.end_jd)
            acc.append(WeatherWindow(
                kind="Sade Sati", label=ph.phase, span=_span(y0, y1), start_year=y0, end_year=y1,
                current=bool(getattr(ph, "current", False)),
                detail=(f"Saturn transits the {_ord_house(ph.house_from_moon)} from the natal "
                        f"Moon (sign {ph.sign})."),
                governing="PREC-6", citation="HTJAH-II:4679"))
        return acc

    def _adverse_confluence() -> list[WeatherWindow]:
        # merge the adverse dasha x transit rows per (planet, role, Mahadasha run)
        acc: list[WeatherWindow] = []
        merged: dict[tuple, list] = {}
        for w in getattr(r, "dasha_transit_adverse", ()) or ():
            if getattr(w, "overlap_end_jd", 0.0) <= ref:
                continue
            merged.setdefault((w.planet, w.role, round(w.period_start_jd, 3)), []).append(w)
        for (planet, role, _ps), rows in merged.items():
            y0 = min(_year(x.overlap_start_jd) for x in rows)
            y1 = max(_year(x.overlap_end_jd) for x in rows)
            bindus = [x.bav_bindus for x in rows if x.bav_bindus is not None]
            det = (f"{planet} runs as {role} while transiting a sign its own gochara reads "
                   f"adverse"
                   + (f"; {min(bindus)}-{max(bindus)} bindus in its own Bhinnashtakavarga there"
                      if bindus else "")
                   + (f" ({len(rows)} separate passes)" if len(rows) > 1 else "") + ".")
            acc.append(WeatherWindow(
                kind="Dasha x adverse transit", label=f"{planet} ({role})", span=_span(y0, y1),
                start_year=y0, end_year=y1, current=(y0 <= _year(ref) <= y1), detail=det,
                governing="PREC-6", citation="HTJAH-II:4679"))
        return acc

    def _slow_movers() -> list[WeatherWindow]:
        # the slow-mover long-horizon gochara (r.gochara_outlook): Jupiter/Saturn/Rahu/Ketu
        # segment by segment. Raw it is 61 forward adverse segments on one chart — because a
        # retrograde pass back into the same sign is several rows for ONE stretch — so runs with
        # the same house-from-Moon are merged, and the horizon is the reading's own forward
        # window rather than the whole ephemeris.
        acc: list[WeatherWindow] = []
        horizon = _year(ref) + int(getattr(r, "window_forward", 0) or 0)
        for planet, segs in (getattr(r, "gochara_outlook", {}) or {}).items():
            runs: list[list] = []
            for seg in sorted(segs, key=lambda x: x.start_jd):
                if getattr(seg, "gochara_good", True) or seg.end_jd <= ref:
                    continue
                if _year(seg.start_jd) > horizon:
                    continue
                if runs and runs[-1][-1].house_from_moon == seg.house_from_moon:
                    runs[-1].append(seg)
                else:
                    runs.append([seg])
            for run in runs:
                y0, y1 = _year(run[0].start_jd), _year(run[-1].end_jd)
                hfm = run[0].house_from_moon
                acc.append(WeatherWindow(
                    kind="Slow-mover gochara",
                    label=f"{planet} in the {_ord_house(hfm)} from Moon",
                    span=_span(y0, y1), start_year=y0, end_year=y1,
                    current=(y0 <= _year(ref) <= y1),
                    detail=(f"{planet} transits the {_ord_house(hfm)} from the natal Moon, which "
                            f"the gochara scheme reads adverse"
                            + (f" ({len(run)} passes, retrograde included)"
                               if len(run) > 1 else "")
                            + "."),
                    governing="PREC-6", citation="HTJAH-II:4679"))
        return acc

    def _kakshya() -> list[WeatherWindow]:
        acc: list[WeatherWindow] = []
        for k in getattr(r, "dasa_kakshya", ()) or ():
            if getattr(k, "end_jd", 0.0) <= ref:
                continue
            y0, y1 = _year(k.start_jd), _year(k.end_jd)
            # the scheme's own `reading` may already name the mechanic ("adverse-neutralised"),
            # so only append a tag the reading has not stated — else it reads twice in one clause
            reading = str(getattr(k, "reading", "") or "")
            tags = [tag for tag, on in (("donated", getattr(k, "donated", False)),
                                        ("neutralised", getattr(k, "neutralised", False)))
                    if on and tag not in reading]
            acc.append(WeatherWindow(
                kind="Dasha Kakshya", label=f"{k.maha} MD, {k.ruler} kakshya", span=_span(y0, y1),
                start_year=y0, end_year=y1, current=(y0 <= _year(ref) <= y1),
                detail=(f"The eightfold Kakshya split reads this stretch {reading}"
                        + (f" ({', '.join(tags)})" if tags else "") + "."),
                governing="PREC-7", citation="ASP-12:174"))
        return acc

    out: list[WeatherWindow] = []
    for collect in (_sade_sati, _adverse_confluence, _slow_movers, _kakshya):
        out.extend(_safe(collect, []))
    out.sort(key=lambda w: (w.start_year, w.kind))
    return tuple(out)


def _span(y0: int, y1: int) -> str:
    """'2025-2027', or a bare year when the stretch opens and closes in one."""
    return f"{y0}-{y1}" if y1 != y0 else str(y0)


def _ord_house(h: int) -> str:
    """'12th', '1st' — the house-from-Moon in the idiom the gochara section already uses."""
    return _ordinal(int(h))


def _affliction_calendar(r, windows) -> Optional[AfflictionCalendar]:
    """The transit weather over the reading's own years — subordinate, and saying so.

    Two citations carry the whole frame. Raman on transits: *"Transits are always secondary in
    importance. They are like catalytic agents"* (PREC-6, HTJAH-II:4679). And on the eightfold
    scheme: Dasha Kakshya is *"a timing lens, never a verdict"* (PREC-7, ASP-12:174). Both are
    quoted, so nothing here can be mistaken for a judgment on a bhava."""
    if not windows:
        return None
    now = tuple(f"{w.kind}: {w.label} ({w.span})" for w in windows if w.current)
    kinds = sorted({w.kind for w in windows})
    frame = (f"The weather over the years below, from {len(kinds)} independent scheme"
             f"{'s' if len(kinds) != 1 else ''} the engine already ran "
             f"({', '.join(kinds)}). All of it is SUBORDINATE: Raman holds that "
             f"\"transits are always secondary in importance — they are like catalytic agents\" "
             f"(PREC-6, HTJAH-II:4679), and the eightfold Kakshya split is \"a timing lens, never "
             f"a verdict\" (PREC-7, ASP-12:174). A window here can say a stretch runs rough; it "
             f"can never say a bhava is afflicted, and none of it has moved a verdict above.")
    if now:
        frame += f" Running at the reading's anchor date: {'; '.join(now)}."
    else:
        frame += " Nothing from these schemes is running at the reading's anchor date."
    honesty = ("Weather is not outcome. The validation program measured no chart-specific "
               "real-outcome signal from transit or dasha timing on 22,177 verified charts "
               "(REAL_OUTCOME_GENERALIZATION.md); these windows disclose what the classical "
               "method flags, not what happens.")
    return AfflictionCalendar(windows=tuple(windows), now=now, frame=frame, honesty=honesty)


def _weather_on_window(windows, years: Optional[tuple[int, int]]) -> str:
    """What weather runs ACROSS one theme's own forward window.

    This is the join the report never made: a bhukti that grades *par excellence* for a bhava
    while Sade Sati sits over the Moon is not the same window as one running clear. Both halves
    were computed; neither knew about the other."""
    if years is None or not windows:
        return ""
    y0, y1 = years
    hits = [w for w in windows if not (w.end_year < y0 or w.start_year > y1)]
    if not hits:
        return ("Nothing from the Sade Sati, adverse-transit or Dasha Kakshya schemes runs "
                "across that window — it is clear weather on all three.")
    # grouped BY SCHEME, not one flat chain: a window can catch four slow-mover segments and a
    # kakshya at once, and a flat list of nine "Kind — label (span)" clauses is 800 characters of
    # one sentence. Nothing is dropped — the full calendar table below carries every row.
    by_kind: dict[str, list[str]] = {}
    for w in hits:
        by_kind.setdefault(w.kind, []).append(f"{w.label} ({w.span})")
    parts = ". ".join(f"{kind} — {'; '.join(items)}" for kind, items in by_kind.items())
    return (f"Running across that window — {parts}. Subordinate throughout: transits are "
            f"catalytic, never causal (PREC-6, HTJAH-II:4679), and the Kakshya split is a timing "
            f"lens, never a verdict (PREC-7, ASP-12:174); none of it has changed the grade above.")


def _pitru_screen(r, house: int) -> str:
    """The non-Raman ancestral screen, where it bears on this bhava — a DIFFERENT layer.

    PREC-12 governs exactly this: *non-Raman screens are a different layer, not a contradiction.*
    ``r.pitru`` is tagged CLASSICAL_NONCITABLE (BPHS provenance), so it is reported with its
    provenance on its face, walled out of the cross-checks and the evidence links, and never
    allowed to qualify the Raman verdict on the 5th or the 9th."""
    pit = getattr(r, "pitru", None)
    if pit is None or house not in (5, 9):
        return ""
    bits: list[str] = []
    if house == 5 and getattr(pit, "raman_children_verdict", ""):
        bits.append(f"the screen was run against Raman's own H5 verdict "
                    f"({pit.raman_children_verdict})")
    curses = getattr(pit, "curse_yogas", ()) or ()
    bits.append(f"{len(curses)} curse-yoga gate{'s' if len(curses) != 1 else ''} fire"
                f"{'' if len(curses) != 1 else 's'}"
                + (": " + "; ".join(getattr(c, "name", str(c)) for c in curses) if curses else ""))
    if house == 9:
        seats = getattr(pit, "pitru_bhava", ()) or ()
        if seats:
            bits.append(f"{len(seats)} classical note{'s' if len(seats) != 1 else ''} on the "
                        f"pitr-sthana itself")
    return ("Pitru dosha screen (NOT Raman — classical/BPHS provenance, reported as a separate "
            "layer and never a contradiction of the verdict above, PREC-12): "
            + "; ".join(bits) + ".")


def _longevity_frame(r, themes) -> Optional[LongevityFrame]:
    """Raman's FIRST step, restored to the front of the integrated reading (PREC-8).

    *"First establish the band by combination, THEN fix the period by the marakas. The numeric
    span is a cross-check, never a prediction of death"* (HTJAH-II:4465-4472). The engine ran
    step one on every chart; the synthesis read forward windows out to the 2040s without ever
    setting them against the span. This states the band, states the marakas AFTER it, and tests
    every window the reading names against the span — the integration the order itself asks for."""
    from app.raman_saab.detailed_report import longevity_band_label
    band_raw = getattr(r, "longevity_class", "") or ""
    if not band_raw:
        return None
    band = _safe(lambda: longevity_band_label(band_raw), band_raw) or band_raw
    yrs = float(getattr(r, "longevity_years", 0.0) or 0.0)
    ymd = tuple(getattr(r, "longevity_ymd", (0, 0, 0)) or (0, 0, 0))
    bal = ""
    b = getattr(r, "balarishta", None)
    if b is not None:
        if getattr(b, "cancelled", False):
            bal = "cancelled"
        elif getattr(b, "applies", False):
            bal = "applies"
    span_year = _span_end_year(r)
    # the furthest calendar year ANY theme window names — the reading's own reach
    reaches = 0
    for t in themes:
        m = re.search(r"\((\d{4})(?:-(\d{4}))?\)", t.activation_span or "")
        if m:
            reaches = max(reaches, int(m.group(2) or m.group(1)))
    within = bool(span_year and reaches and reaches <= span_year)
    maraka_now = bool(getattr(r, "maraka_period_now", False))
    windows = _maraka_window_rows(r)

    frame = (f"Raman judges the span FIRST and the maraka periods second (PREC-8; "
             f"HTJAH-II:4465-4472). This chart reads at the {band}; the Ayurdaya cross-check "
             f"gives about the {_ordinal(int(round(yrs)))} year")
    if ymd and any(ymd):
        frame += f" ({ymd[0]}y {ymd[1]}m {ymd[2]}d)"
    if bal == "applies":
        frame += ", with Balarishta applying"
    elif bal == "cancelled":
        frame += ", Balarishta cancelled"
    frame += ". "
    if reaches and span_year:
        frame += (f"Every window this reading names falls inside that span (the furthest reaches "
                  f"{reaches}). " if within else
                  f"One or more windows this reading names ({reaches}) fall outside that span; "
                  f"each is disclosed as such where it appears. ")
    frame += ("The running period carries a maraka-tier lord."
              if maraka_now else "The running period carries no maraka-tier lord.")
    if windows:
        first = windows[0]
        frame += (f" Ahead, {len(windows)} maraka-tier bhukti"
                  f"{'s' if len(windows) != 1 else ''} carry the classical Saturn signal, the "
                  f"first at {first[0]} ({first[1]}) — classically sensitive periods "
                  f"(HTJAH-II:4846-4849), named in Raman's order and never used to move a "
                  f"bhava verdict.")
        # the two methods are independent and they do NOT agree here: the maraka scheme runs the
        # whole Vimshottari timeline, the ayurdaya band stops. Disclosed, not reconciled.
        beyond = [w for w in windows if w[3] == "beyond the band"]
        if beyond and span_year:
            frame += (f" {len(beyond)} of them fall BEYOND the band itself (after {span_year}) — "
                      f"the maraka scheme runs the whole Vimshottari timeline while the ayurdaya "
                      f"stops where it stops, so the two do not agree here. Raman's order settles "
                      f"which leads: the band is established first, and the marakas are read "
                      f"inside it (PREC-8).")
    return LongevityFrame(
        band=band, years=yrs, ymd=(int(ymd[0]), int(ymd[1]), int(ymd[2])), balarishta=bal,
        span_year=span_year, reading_reaches=reaches, within_span=within,
        maraka_now=maraka_now,
        maraka_windows=windows, frame=frame, honesty=_MEASURED_TRUTH_SPAN,
        citation="HTJAH-II:4465-4472; HTJAH-II:4846-4849 (PREC-8)")


def _dissent_summary(concordance, div_checks, av_support, karmic, headline) -> DissentSummary:
    """Lay out the cross-checks on this bhava by their CITED reliability tier — and give no grade.

    The ladder is derivable entirely from cited material:

    * the D1 core (the house's lord and karaka) is what Raman's summing-up itself names,
      HTJAH-I:983-991 — but it is NOT independent of the verdict, because those are the verdict's
      own inputs restated by name (the report's own honesty rule 3);
    * a divisional CORROBORATES the D1 core and does not decide it (PREC-11);
    * Ashtakavarga sits a tier lower still on Raman's own caveat — "Ashtakavarga method is equally
      important. But, it does not seem to be quite reliable" (HTJAH-II:4453-4456, PREC-4) — so it
      may be reported but must never weigh equally against a Raman-band reading;
    * the karmic/Jaimini lens is walled out of the cross-checks altogether.

    No tier is converted into a number and no aggregate grade is produced, because Raman states no
    numeric N-testimonies rule (HTJAH-I:495) and this project already measured that head-counting
    influences does not reproduce his reasoning (COMPARATIVE_WEIGHING.md, 0 of 7)."""
    from app.raman_saab.insight_digest import _lean_of
    checks: list[CrossCheck] = []

    if concordance is not None:
        against = bool(concordance.divergence)
        checks.append(CrossCheck(
            system="the bhava's own testimony ledger",
            tier="D1 core (lord / karaka / navamsa)",
            independent=False,
            relation="reads against" if against else "reads with",
            governing="PREC-3", citation="HTJAH-I:983, HTJAH-I:495",
            note=("These are the verdict's OWN inputs restated by name, so they are not an "
                  "independent vote and are never tallied as one — a divided ledger means the "
                  "witnesses split, not that the verdict is wrong (PREC-3).")))

    own_div = [d for d in div_checks if d.relation in ("concurs", "diverges")]
    if own_div:
        against = any(d.relation == "diverges" for d in own_div)
        checks.append(CrossCheck(
            system="the assigned division",
            tier="corroborating (the D1 core decides)",
            independent=True,
            relation="reads against" if against else "reads with",
            governing="PREC-11", citation="",
            note=("The Raman D1 core is authoritative and the divisional corroborates "
                  "(PREC-11); a division reading the other way qualifies confidence and settles "
                  "nothing on its own.")))

    if av_support:
        hlean = _lean_of(headline)
        weak = not any(a.verdict == "well supported" for a in av_support)
        # AV withholding support only speaks against a FAVOURABLE reading; against an afflicted
        # one, thin bindus point the same way as the verdict
        against = bool(weak and hlean == "favourable")
        checks.append(CrossCheck(
            system="Ashtakavarga",
            tier="lower-reliability tier (Raman's own caveat)",
            independent=True,
            relation="reads against" if against else "reads with",
            governing="PREC-4", citation="HTJAH-II:4453",
            note=('Raman on this method: "Ashtakavarga method is equally important. But, it does '
                  'not seem to be quite reliable" (HTJAH-II:4453-4456). It never outranks a '
                  "Raman-band reading, so it is shown at its own tier and not weighed level with "
                  "the core.")))

    walled = ""
    if karmic is not None:
        walled = (f"Outside the cross-checks entirely: the karmic lens reads {karmic.aspect} as "
                  f"{karmic.karmic_verdict} and {karmic.relation}. The Jaimini layer never feeds "
                  f"the Parashari verdict, so it is neither a cross-check nor a dissent.")

    dissenting = tuple(c.system for c in checks if c.relation == "reads against")
    if not dissenting:
        reading = ("Every cross-check reads with the verdict, each at its own tier "
                   "(D1 core, then the corroborating division, then Ashtakavarga).")
    else:
        reading = ("Reading against the verdict: "
                   + "; ".join(f"{c.system} ({c.tier})" for c in checks
                               if c.relation == "reads against")
                   + ". None of these may overturn a bhava judgment; each is weighed where "
                     "Raman places it, not counted.")
    method_note = ("No overall confidence grade is given. Raman states no numeric "
                   "N-testimonies rule — HTJAH-I:495 says only that all must be properly weighed "
                   "— and this project measured that head-counting influences does not reproduce "
                   "his reasoning (0 of 7 worked cases). The tiers are his; the arithmetic would "
                   "have been ours.")
    return DissentSummary(checks=tuple(checks), dissenting=dissenting, walled_note=walled,
                          reading=reading, method_note=method_note)


def _year(jd: float) -> int:
    return int(swe.revjul(jd, swe.GREG_CAL)[0])


def _node_agents(r) -> dict[str, tuple[str, ...]]:
    """{node: the planets it acts for} — Rahu and Ketu carry no rulership of their own, so they
    give the results of the lord of the sign they occupy (their dispositor) and of any planet
    joined with them. Without this a node can NEVER appear among a theme's driving planets (it is
    never a sign-lord and never a domain karaka), so every Rahu/Ketu Mahadasha — a quarter of the
    120-year Vimshottari cycle — would foreground nothing at all.

    Conjunction is sign membership, per the project's locked drishti convention. Pure re-read of
    the cast chart; empty when a node is absent."""
    from app.raman_saab.chart.constants import SIGN_LORDS
    out: dict[str, tuple[str, ...]] = {}
    planets = getattr(getattr(r, "chart", None), "planets", {}) or {}
    for node in ("Rahu", "Ketu"):
        p = planets.get(node)
        if p is None:
            continue
        agents: list[str] = []
        disp = _safe(lambda: SIGN_LORDS[p.sign], None)
        if disp and disp not in agents:
            agents.append(disp)
        for other, op in planets.items():
            if other in ("Rahu", "Ketu") or other in agents:
                continue
            if getattr(op, "sign", None) == p.sign:      # joined with the node (same sign)
                agents.append(other)
        out[node] = tuple(agents)
    return out


def _dasha_evolution(r, themes) -> tuple[DashaChapter, ...]:
    """Which life-themes each Mahadasha FOREGROUNDS, chapter by chapter — the horoscope's
    evolution through time. Differential, not flooding: a theme is foregrounded by a chapter only
    when the Mahadasha lord is one of that theme's OWN driving planets (``dominant_planets``), so
    the Saturn period foregrounds career and foundations (which Saturn drives), not all nine
    themes at once. A pure re-read — the lord names and spans are the chapters' own; no new dasha
    math. When a chapter's lord drives none of the tracked themes that is stated as such (a fallow
    stretch), never padded with everything the lord distantly touches."""
    lc = getattr(r, "life_chapters", None)
    chapters = getattr(lc, "chapters", ()) if lc else ()
    if not chapters:
        return ()
    theme_drivers = [(t.name, set(t.dominant_planets)) for t in themes]
    agents = _node_agents(r)
    # the engine grades each Mahadasha lord's own condition; attach it so a chapter says what
    # kind of lord is running it, not merely which one
    cond = {c.maha: c for c in getattr(r, "md_condition", ()) or ()}
    # Ashtakavarga's own verdict on each Mahadasha — an independent system that can agree or
    # disagree with the chapter's Ishta/Kashta lean, and never had the chance to before
    seats = {sc.maha: sc for sc in getattr(r, "av_dasha_seats", ()) or ()}
    out: list[DashaChapter] = []
    prev: set[str] = set()
    for ch in chapters:
        lord = getattr(ch, "maha", "") or ""
        # a node rules nothing of its own — it foregrounds what its dispositor and its
        # co-tenants drive, and the routing is disclosed rather than silently assumed
        acts_through = agents.get(lord, ()) if lord in agents else ()
        keys = {lord} | set(acts_through)
        active = tuple(name for name, drv in theme_drivers if keys & drv)
        aset = set(active)
        emerging = tuple(n for n in active if n not in prev)
        continuing = tuple(n for n in active if n in prev)
        mc = cond.get(lord)
        if mc is None:
            lord_condition = ""
        else:
            bits = ["strong" if getattr(mc, "strong", False) else "not strong by Shadbala"]
            if getattr(mc, "vargottama", False):
                bits.append("vargottama")
            if getattr(mc, "at_maximum", False):
                bits.append("at maximum")
            lord_condition = ", ".join(bits)
        sc = seats.get(lord)
        if sc is None or getattr(sc, "bindus", None) is None:
            # Rahu/Ketu contribute no Ashtakavarga of their own, so a nodal chapter has no seat
            # reading — an honest absence, not a neutral verdict
            av_seat = ("" if sc is None else
                       f"seats in sign {sc.sign}; the nodes contribute no Ashtakavarga, so this "
                       f"chapter carries no bindu reading")
        else:
            av_seat = (f"seats in sign {sc.sign} with {sc.bindus} bindus — Ashtakavarga reads "
                       f"this chapter {sc.read}")
        out.append(DashaChapter(
            maha=lord,
            span=f"{_year(ch.start_jd)}-{_year(ch.end_jd)}",
            is_current=bool(getattr(ch, "is_current", False)),
            lean=getattr(ch, "lean", None) or "neutral",
            activates=active, emerging=emerging, continuing=continuing,
            acts_through=acts_through, lord_condition=lord_condition, av_seat=av_seat))
        prev = aset
    return tuple(out)


def _spine_size(themes) -> int:
    """How many themes form the spine: 3-5, cut where the ranked weights actually fall away.

    A spine that names most of the roster names nothing. The old rule took up to SEVEN and only
    stopped on a drop greater than 1.0 — a threshold the distribution almost never crosses, so
    every chart returned the maximum (measured: 7 of 12 on all three test charts). Instead, choose
    among the allowed sizes the one that sits at the LARGEST drop in the ranking, so the cut lands
    on this chart's own break rather than on an absolute constant."""
    n = len(themes)
    if n <= 3:
        return n
    lo, hi = 3, min(5, n)
    best_size, best_gap = lo, -1.0
    for size in range(lo, hi + 1):
        if size >= n:
            break
        gap = themes[size - 1].evidence_weight - themes[size].evidence_weight
        if gap > best_gap:
            best_gap, best_size = gap, size
    return best_size


# plain-language names for the census relation keys (planet_biographies census_by_relation)
_REL_WORD = {
    "karaka_of": "as karaka", "lord_of": "as house-lord", "aspects": "by aspect",
    "occupies": "by occupation", "maraka_tier": "in a maraka role",
    "conjoins": "by conjunction", "helps": "as a helper", "obstructs": "as an obstructor",
}


def _identity_line(r) -> str:
    """Who the chart IS, in one line: Lagna and its lord, the Atmakaraka and its Karakamsa sign,
    and the Moon's nakshatra. Pure re-read of r.synthesis + r.chart; empty on a sparse chart."""
    from app.raman_saab.chart.constants import SIGN_LORDS
    from app.raman_saab.primitives import nakshatra_signature
    sy = getattr(r, "synthesis", None)
    if sy is None:
        return ""
    parts: list[str] = []
    lagna = getattr(sy, "lagna", "") or ""
    asc = getattr(getattr(r, "chart", None), "asc_sign", None)
    if lagna and asc is not None:
        lord = _safe(lambda: SIGN_LORDS[asc], "")
        parts.append(f"{lagna} lagna ruled by {lord}" if lord else f"{lagna} lagna")
    ak = getattr(sy, "atmakaraka", "") or ""
    km = getattr(sy, "karakamsa", "") or ""
    if ak:
        parts.append(f"Atmakaraka {ak}" + (f" with Karakamsa in {km}" if km else ""))
    moon = _safe(lambda: r.chart.planets.get("Moon"), None)
    if moon is not None:
        nk = _safe(lambda: nakshatra_signature.signature_for(moon.nakshatra), None)
        if nk is not None:
            pada = getattr(moon, "pada", None)
            parts.append(f"Moon in {nk.name}" + (f" (pada {pada})" if pada else ""))
    return "; ".join(parts) + "." if parts else ""


def _concordance_note(r, themes, graha_conc) -> str:
    """How far do the chart's independent techniques agree with each other? A single honest line,
    counted from the engine's own ledgers — the bhavas whose verdict runs against the weight of
    their testimony, and the grahas whose force and intent point different ways."""
    contested = [t.concordance for t in themes
                 if t.concordance is not None and t.concordance.divergence]
    corroborated = [t.concordance for t in themes
                    if t.concordance is not None and t.concordance.status == "well-corroborated"]
    split = [g for g in graha_conc if g.agreement == "split"]
    bits: list[str] = []
    if corroborated:
        bits.append(f"{len(corroborated)} of the twelve bhavas read the same way from every "
                    f"independent testimony")
    if contested:
        houses = ", ".join(f"H{c.house}" for c in contested)
        bits.append(f"{len(contested)} ({houses}) carry a verdict that runs against the weight of "
                    f"their own testimony — read those with the spread in mind")
    if split:
        names = ", ".join(g.planet for g in split)
        bits.append(f"{len(split)} graha ({names}) measure strong in force but not in benefic "
                    f"potency, or the reverse — strength is magnitude, never direction")
    return "; ".join(bits) + "." if bits else ""


def _portrait(r, themes, spine, frame, graha_conc=()) -> ExecutivePortrait:
    from app.raman_saab.insight_digest import _lean_of
    by_id = {t.theme_id: t for t in themes}
    spine_themes = [by_id[i] for i in spine if i in by_id]

    identity = _identity_line(r)

    # temperament — Moon frame / lagna nature word from the overview, plus the dominant graha
    temperament = _safe(lambda: getattr(r.overview, "temperament", "") or "", "") or \
        (f"read chiefly from the {frame}" if frame else "")

    # dominant actors — census-ranked biographies (planet_bios[0] is dominant), why in plain words
    actors: list[tuple[str, str]] = []
    for i, bio in enumerate((getattr(r, "planet_bios", ()) or ())[:3]):
        breakdown = sorted((getattr(bio, 'census_by_relation', ()) or ()),
                           key=lambda kv: kv[1], reverse=True)
        roles = ", ".join(f"{v}x {_REL_WORD.get(k, k.replace('_', ' '))}" for k, v in breakdown[:4])
        lead = "the chart's busiest graha" if i == 0 else "also prominent"
        why = f"{lead} — {bio.census_count} structural roles" + (f" ({roles})" if roles else "")
        actors.append((bio.planet, why))

    fav = [t for t in spine_themes if _lean_of(t.headline_verdict) == "favourable"]
    adv = [t for t in spine_themes if _lean_of(t.headline_verdict) == "adverse"]

    # principal tension — the chart's REAL structural pull, not a method note: the strongest
    # favourable spine theme set against the strongest strained one (both already weight-sorted).
    # Falls back to the single most-load-bearing contradiction, then to an honest 'no dominant
    # tension' when the spine agrees in direction.
    tensions = [c for t in themes for c in t.contradictions]
    if fav and adv:
        a, b = fav[0], adv[0]
        al, bl = a.dominant_planets[0] if a.dominant_planets else "", \
            b.dominant_planets[0] if b.dominant_planets else ""
        principal = (f"the chart's centre of gravity is {a.name.lower()} "
                     f"({a.headline_verdict}"
                     + (f", carried by {al}" if al else "") + "), while "
                     f"{b.name.lower()} carries the countervailing strain "
                     f"({b.headline_verdict}"
                     + (f", on {bl}" if bl else "") + ") — the central negotiation of the life "
                     "runs between the two.")
    elif tensions:
        principal = tensions[0].resolution
    else:
        principal = ("No single structural tension dominates — the spine themes agree in "
                     "direction, so the chart reads as of a piece.")

    protective = _protective_factors(r)
    cur = _safe(lambda: f"{r.synthesis.running_md} MD / {r.synthesis.running_ad} AD", "")
    # the running pratyantardasha — the engine computes the third level and the portrait stopped
    # at the second, so "the current chapter" was coarser than the report's own resolution
    # ...and it must be the one RUNNING at ref_jd, not pn[0]. `pratyantar_now` holds all nine
    # pratyantars of the current bhukti, so taking the first named a PD that is not running for
    # roughly eight ninths of every bhukti (measured: Mainpuri said "Jupiter PD" while Ketu PD
    # was running). Same selection `_pratyantar_block` in report_html.py already uses.
    pn = (getattr(r, "pratyantar_now", ()) or ())
    if pn and cur:
        ref = getattr(r, "ref_jd", 0.0)
        run = next((x for x in pn
                    if getattr(x, "start_jd", 0.0) <= ref < getattr(x, "end_jd", 0.0)), None)
        if run is not None:
            cur += f" / {run.pratyantar} PD"
    stability = _safe(lambda: getattr(r.rect_confidence, "label", "") or "", "") or ""
    if stability:
        stability = (f"{stability} ({r.rect_confidence.stable_count} of "
                     f"{r.rect_confidence.total_count} pillars stable across the scan window). "
                     f"Every verdict in this reading rests on the cast moment, so this qualifies "
                     f"all of them.")
    # the Jaimini chara dasha running now — a WALLED parallel to the Vimshottari chapter, never
    # a second timing authority (the Jaimini layer never feeds the Parashari reading)
    chara = ""
    span = next((c for c in getattr(r, "chara_sequence", ()) or () if getattr(c, "current", False)),
                None)
    if span is not None:
        chara = (f"the Jaimini chara dasha of sign {span.sign} ({span.years} years, "
                 f"{_year(span.start_jd)}-{_year(span.end_jd)}) runs alongside — a walled "
                 f"parallel, never a second timing authority over the Vimshottari reading")
    nxt = _next_chapter(r)
    honesty = _safe(lambda: r.info.sentence, "") or ""

    return ExecutivePortrait(
        identity=identity, temperament=temperament, frame=frame, dominant_actors=tuple(actors),
        strongest_domains=tuple(t.name for t in fav[:4]),
        weakest_domains=tuple(t.name for t in adv[:4]),
        principal_tension=principal, concordance_note=_concordance_note(r, themes, graha_conc),
        reading_stability=stability, chara_now=chara,
        protective_factors=protective,
        current_chapter=cur, next_chapter=nxt, honesty_note=honesty)


def _protective_factors(r) -> tuple[str, ...]:
    """Bhanga / neecha-bhanga / benefic-relief already flagged on the report — never invented.

    The Arishta chapter carries the engine's OWN cited protections (the combinations that placed
    the chart in its longevity band) plus any bhangas and any UNCANCELLED debility. Listing the
    protections without their counterweight would be selective, so the debilities come too."""
    out: list[str] = []
    bal = getattr(r, "balarishta", None)
    if bal is not None and getattr(bal, "cancelled", False):
        out.append("Balarishta present but cancelled (bhanga)")
    ar = getattr(r, "arishta", None)
    for prot in (getattr(ar, "protections", ()) or ()) if ar else ():
        out.append(str(prot))
    for bh in (getattr(ar, "bhangas", ()) or ()) if ar else ():
        out.append(f"bhanga: {bh}")
    # longevity band as a protective foundation (band word only, never a date)
    lc = getattr(r, "longevity_class", "") or ""
    if lc:
        out.append(f"longevity reads at the {lc} band")
    # the honest counterweight — a protection list without it would be selective
    for deb in (getattr(ar, "uncancelled_debilities", ()) or ()) if ar else ():
        out.append(f"uncancelled debility (not a protection): {deb}")
    return tuple(out)


def _next_chapter(r) -> str:
    """The next MD boundary and its lean, from the timeline — a timed indication, not a decree."""
    tl = getattr(r, "life_chapters", None)
    chapters = getattr(tl, "chapters", ()) if tl else ()
    ref = getattr(r, "ref_jd", 0.0)
    for ch in chapters:
        start = getattr(ch, "start_jd", None)
        if start is not None and start > ref:
            lord = getattr(ch, "lord", getattr(ch, "maha", "the next"))
            return f"the {lord} chapter follows"
    return ""
