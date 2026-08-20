"""Per-signification house judge (NEW engine) — `judges/house_template.py`.

This is the spec §6.1 refinement of the house-level judge (`house_judge.py`,
left untouched): instead of one verdict per Bhava, each **signification**
(sub-matter — e.g. H4 mother / education / property) is judged through its own
karaka, in up to three frames (LAGNA / MOON / KARAKA), each producing a
``FrameLedger`` of strength + evidence. ``_decide`` collapses a ledger to an
ordinal ``Verdict``; ``judge_house`` aggregates the per-signification verdicts
into a ``HouseProforma`` whose :meth:`HouseProforma.as_house_verdict` reproduces
the legacy :class:`house_judge.HouseVerdict` so the two engines are swappable.

Frame scoping
-------------
* LAGNA  — always built. Lord = sign-lord of the house counted from the Lagna.
* MOON   — always built. Lord = sign-lord of the house counted from the Moon's
           rasi-house (Chandra-Lagna). Karaka is the natural karaka (frame-free).
* KARAKA — built ONLY when ``sig.alternate_frame_core`` is set (mother→Moon-as-Lagna,
           spouse→Venus-as-Lagna, father→Sun-as-Lagna, …). Lord = sign-lord of the
           house counted from the alternate-core planet's sign.

Lead frame = the frame whose LORD has the larger total Shadbala (LAGNA vs MOON);
on Track-B (no Shadbala) the lead defaults to LAGNA. The KARAKA frame, when
present, rides as an alternate ledger (its longevity use lands in Phase E).

Decision order in ``_decide`` is LOAD-BEARING — see the inline numbering.

Usage:
    from app.raman_saab.judges import house_template as ht
    pf = ht.judge_house(chart, 4)          # HouseProforma for the 4th
    for sv in pf.significations:
        print(sv.signification, sv.verdict, sv.lead_frame)
    legacy_shaped = pf.as_house_verdict()  # drop-in HouseVerdict
"""
from __future__ import annotations

import dataclasses

from app.core.avastha import compute_avasthas
from dataclasses import dataclass, field
from typing import Final, Literal, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart import varga
from app.raman_saab.chart.varga_chart import VargaChart, cast_varga_chart
from app.raman_saab.primitives import ashtakavarga
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine import lookups
from app.raman_saab.doctrine.conditions import EvalContext, HemmedBy
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA
from app.raman_saab.doctrine.significations import Signification, significations_of
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.judges import rule_firing as rf
from app.raman_saab.judges.house_judge import HouseVerdict
from app.raman_saab.primitives import ayurdaya
from app.raman_saab.primitives import relationships as r
from app.raman_saab.primitives import vimshottari
from app.raman_saab.primitives.bhangas import neecha_bhanga, parivartana
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.effective_strength import effective_strength
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS, is_yogakaraka)
from app.raman_saab.primitives.shadbala import bhava_bala as bhava_bala_mod
from app.raman_saab.primitives.shadbala import total as shadbala_total
from app.raman_saab.primitives.sphutas import beeja_kshetra

Verdict = Literal["favourable", "mixed", "afflicted", "insufficient-evidence"]
# The graded INTENSITY of a verdict (Layer A): surfaces the gradation the engine already
# computes (pillar count, decisive/veto flags, marginal-shift) WITHOUT inventing a doctrinal
# verdict level. verdict x degree gives 7 graded output states (fav/mixed/afflicted x
# strong/moderate/mild) — never a literal 7-level ordinal (that would be false precision).
Degree = Literal["strong", "moderate", "mild"]
Frame = Literal["lagna", "moon", "karaka"]
NavStatus = Literal["confirms", "weakens", "neutral", "unknown"]

#: Frozen-safe judge metadata: deterministic (key, value) string pairs.
Metadata = tuple[tuple[str, str], ...]

# Combust threshold for the karaka-intact "graded combustion" test: a half-combust planet
# (combust_fraction >= 0.5) counts as a true affliction.
#
# B7 (2026-06-15, doctrine-foundation): the former Saturn/Venus 0.85 "resilience" exemption
# (a NOVEL heuristic, explicitly NOT cited to Raman) was REMOVED — unified to a single 0.5 bar
# for all planets. Chart 59 contradicts the exemption: Raman calls a 0.79-combust Venus
# "powerless" (HTJAH-I:3788, the very chart H3.C.39 is built on), so a higher Venus/Saturn bar
# is doctrinally wrong. Unifying is zero-regression on the golden corpus and removes the
# inconsistency the bphs-doctrine-reviewer flagged (this 0.5 now matches H3.C.39's lord-combust
# bar — one combustion doctrine).
_COMBUST_HARD_FRACTION: float = 0.5            # half-combust counts (all planets)

# Dusthana houses (6/8/12) counted from the navamsa lagna weaken the D9 verdict.
_D9_WEAK_HOUSES: frozenset[int] = frozenset({6, 8, 12})
# 6/8/12 counted from ANY varga lagna weaken that varga's testimony — the same dusthana
# principle _navamsa_status applies in D9. Used by the D-7 (Sapthamsa) children layer.
_VARGA_DUSTHANA: frozenset[int] = frozenset({6, 8, 12})

# ── Round-8 wiring constants (yoga modifier + sphuta gate + lookup surfacing) ──
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
#: Canonical graha iteration order — keeps occupant metadata deterministic.
_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
# Yoga modifier scopes (HTJAH-I consideration #4, :480-482), kind -> matters:
#   dhana   supports wealth/gains matters (H2 / H11);
#   arishta (Sakata, uncancelled Kemadruma, et al.) weighs on H1 self/Moon-matters;
#   raja    supports fortune/career matters (H9 / H10).
_DHANA_HOUSES: Final[frozenset[int]] = frozenset({2, 11})
_DHANA_TAGS: Final[frozenset[str]] = frozenset({"wealth", "gains"})
_ARISHTA_TAGS: Final[frozenset[str]] = frozenset({"self"})
_RAJA_HOUSES: Final[frozenset[int]] = frozenset({9, 10})
_RAJA_TAGS: Final[frozenset[str]] = frozenset({"fortune", "career"})
# H5 fertility gate scope (HTJAH-I:5517-5527): children/progeny matters only —
# intellect/poorvapunya share the H5 'children' rule bucket but are not begetting
# matters, so the sphuta gate deliberately does NOT touch them.
_FERTILITY_KEYS: Final[frozenset[str]] = frozenset({"children", "progeny"})
# Lookup-surfacing scopes (doctrinal review promotion #6 — metadata only).
_H8_DEATH_KEYS: Final[frozenset[str]] = frozenset({"longevity", "death"})
_H11_GAINS_KEYS: Final[frozenset[str]] = frozenset({"gains", "acquisitions"})
_H6_DISEASE_KEYS: Final[frozenset[str]] = frozenset({"enemies_disease", "disease_chronic"})

# Dusthana-affliction matters (Stage-3 calibration, user-signed-off). INHERENTLY-malefic
# significations where a fired malefic with NO benefic contradiction CONFIRMS the affliction:
# a strong dusthana lord STRENGTHENS the evil (a powerful 6th lord gives serious disease), so
# pillar strength must not rescue the matter and a confirming navamsa must not lift it. Scope:
# the 6th's five afflictions + the 12th's incarceration / left_eye. H8 is DELIBERATELY EXCLUDED
# (legacies / sudden_gains are GAINS; death / longevity are owned by the Phase-E longevity
# pre-pass). H12 expenditure / moksha / foreign_residence are excluded (not pure afflictions —
# the wealthy spend lavishly, moksha is liberation). Every key is unique to its dusthana, so
# scoping by key alone carries no cross-house leakage. Read in _build_frame_ledger to set the
# AFFLICTION_MATTER flag that _decide clause-1.5 consumes.
_DUSTHANA_AFFLICTION_KEYS: Final[frozenset[str]] = frozenset({
    "enemies_disease", "accidents", "debts", "enemies", "disease_chronic",  # H6
    "incarceration", "left_eye",                                            # H12
    "death",                                                                # H8 (manner/cause)
})

# CATASTROPHIC sub-significations — bodily/liberty ruin (imprisonment, blindness, grave
# accident) that Raman pronounces ONLY on a MULTIPLY-afflicted configuration, never on a
# lone malefic. His own worked charts show it: h12_13 "the 2nd AND the 12th heavily
# afflicted, the Sun in papakartari"; h12_14 "the 12th lord afflicted by the nodes in Rasi
# AND in Navamsa". Empirically EVERY confirmed-afflicted incarceration/left_eye golden
# carries >= 3 fired malefic rules; an ordinary dusthana matter (disease/enemies/debts)
# fires on one. The severity gate below encodes that bar so a thin single/no-malefic
# affliction cannot escalate to "you were jailed / went blind / had a grave accident".
_CATASTROPHIC_KEYS: Final[frozenset[str]] = frozenset({
    "incarceration", "left_eye", "accidents"})
_CATASTROPHIC_MIN_MALEFIC: Final[int] = 3

# Rule ids the judge treats as DECISIVE afflictions (Stage-3 H3/H7 rule-authoring). A fired
# MALEFIC rule whose id is listed here confirms 'afflicted' in _decide clause-1.6, even
# against a strong-pillar preponderance and a benefic aspect — the rule-level analogue of
# the dusthana clause-1.5. Each is a combination Raman reads as verdict-driving and is
# specific enough to fire only on genuine severe affliction (the >=2-affliction / D9-
# papakartari / separation-yoga gates keep them off the favourable twin charts).
_DECISIVE_AFFLICTION_RULE_IDS: Final[frozenset[str]] = frozenset({
    "H3.C.36",  # Karaka Mars multiply afflicted (>=2 of dusthana/debil/combust/papakartari)
    "H3.C.37",  # 3rd house hemmed between malefics in the Navamsha (papakartari in amsa)
    "H3.C.38",  # 3rd lord==Karaka Mars, afflicted (lord+karaka struck together)
    "H3.C.39",  # 3rd lord substantially combust (powerless lord -> bhava weak)
    "H3.C.40",  # Saturn-aspects-3rd + debilitated-3rd-lord-in-dusthana (ear: partial deafness)
    "H7.C.82",  # Saturn+Mars besiege the 7th, no benefic relief (marital separation)
    "H7.C.83",  # 7th lord in the 12th + malefic on the 7th (marital loss/separation)
    "H7.C.84",  # 7th lord in the 8th + node/Saturn aggravator (coverture: vaidhavya/spouse death)
    "H7.C.85",  # Mars-in-8th + debilitated 7th lord (coverture: vaidhavya/spouse death)
    "H7.C.86",  # 7th lord node-conjunct+aspected / papakartari (spouse: vitiated marriage)
    "H9.A.20a", # Sun-Pitrukaraka in a dusthana + papakartari (father: early death)
    "H5.C.38",  # PutraKaraka Jupiter papakartari + malefic rashi (children: progeny denied)
    "H4.C.18a", # Moon (Matru-karaka) in 4th conjoined by a malefic (mother: early death)
})


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FrameLedger:
    """One frame's strength + evidence record for a single signification."""
    frame: Frame
    lord: str
    lord_strong: Optional[bool]           # None on Track-B (no Shadbala)
    karaka: str
    karaka_strong: Optional[bool]
    bhava_bala: Optional[float]           # Shashtiamsas; None on Track-B
    bhava_bala_strong: Optional[bool]
    navamsa_status: NavStatus
    karaka_intact: bool
    maraka_active: bool
    parivartana_resilient: bool
    lord_karaka_identical: bool
    fired_benefic: tuple[rf.FiredRule, ...]
    fired_malefic: tuple[rf.FiredRule, ...]
    fired_neutral: tuple[rf.FiredRule, ...]
    flags: tuple[str, ...] = field(default_factory=tuple)
    #: B1 — the LORD carries a hard placement affliction (combust, or an uncancelled
    #: debilitation) that Raman reads as powerless independently of its Shadbala total.
    #: None on Track-B (no positions to judge). See `_lord_hard_afflicted`.
    lord_hard_afflicted: Optional[bool] = None


@dataclass(frozen=True)
class SignificationVerdict:
    """A single sub-matter's verdict, its lead frame, and the alternate ledgers.

    ``metadata`` carries frozen-safe (key, value) string pairs in deterministic
    order: yoga modulations (``("yoga", "<id>:<lift|drop|noted>")``), the H5
    fertility gate (``("beeja_kshetra", ...)``), and lookup-grid surfacing
    (decanate cause, source of gains, Bhavartha inversion, confinement mode,
    organ/tridosha). Lookup rows never change the verdict.
    """
    house: int
    signification: str
    verdict: Verdict
    karaka: str
    lead_frame: Frame
    ledger: FrameLedger
    alt_ledgers: tuple[FrameLedger, ...]
    borderline_shifted: bool
    degree: Degree = "moderate"
    metadata: Metadata = ()


@dataclass(frozen=True)
class HouseProforma:
    """Every signification of a house + the rolled-up house verdict.

    ``metadata`` is the house-level, order-preserving union of the significations'
    metadata, de-duplicated BY KEY (the lead signification's value wins; per-signification
    detail remains on each ``significations[i].metadata``). Deterministic across runs.
    """
    house: int
    lord: str
    significations: tuple[SignificationVerdict, ...]
    rollup: Verdict
    metadata: Metadata = ()

    def as_house_verdict(self) -> HouseVerdict:
        """Reproduce the legacy house-level :class:`HouseVerdict` (drop-in compatibility).

        Lord/karaka are the lead signification's; the verdict is the house rollup;
        the fired-rule evidence is the de-duplicated union across every signification.
        """
        karaka = BHAVA_KARAKA.get(self.house, "Sun")
        benefic: list[rf.FiredRule] = []
        malefic: list[rf.FiredRule] = []
        neutral: list[rf.FiredRule] = []
        seen_b: set[str] = set()
        seen_m: set[str] = set()
        seen_n: set[str] = set()
        for sv in self.significations:
            for fr in sv.ledger.fired_benefic:
                if fr.rule.id not in seen_b:
                    seen_b.add(fr.rule.id); benefic.append(fr)
            for fr in sv.ledger.fired_malefic:
                if fr.rule.id not in seen_m:
                    seen_m.add(fr.rule.id); malefic.append(fr)
            for fr in sv.ledger.fired_neutral:
                if fr.rule.id not in seen_n:
                    seen_n.add(fr.rule.id); neutral.append(fr)
        # Lord/karaka strength MUST describe the SAME planets reported in lord/karaka.
        # `self.lord` is the LAGNA-frame bhava-lord; the lead signification's `ledger`
        # may be the MOON-frame ledger (when the Moon-frame lord has the larger Shadbala),
        # whose lord is frequently a DIFFERENT planet. Reading lord_strong off the lead
        # ledger would pair the lagna lord's NAME with the moon lord's STRENGTH. So we
        # locate the lagna-frame ledger explicitly for the strength readout.
        lead = self.significations[0] if self.significations else None
        lord_strong: Optional[bool] = None
        karaka_strong: Optional[bool] = None
        if lead is not None:
            lagna_ledger = next(
                (L for L in (lead.ledger,) + lead.alt_ledgers if L.frame == "lagna"),
                lead.ledger,
            )
            lord_strong = lagna_ledger.lord_strong
            karaka_strong = lagna_ledger.karaka_strong
        return HouseVerdict(
            house=self.house, verdict=self.rollup, lord=self.lord, karaka=karaka,
            lord_strong=lord_strong, karaka_strong=karaka_strong,
            benefic=tuple(benefic), malefic=tuple(malefic), neutral=tuple(neutral))


# ---------------------------------------------------------------------------
# Small helpers (reuse legacy semantics)
# ---------------------------------------------------------------------------

def _lord_of_sign(sign: int, house_offset: int) -> str:
    """Sign-lord of the house `house_offset` (1..12) counted from rising `sign` (1..12)."""
    return SIGN_LORDS[((sign - 1) + (house_offset - 1)) % 12 + 1]


def _effective_strength(planet: str, raw_rupas: float, chart: RamanChart) -> float:
    """Raman's B1 'effective' strength: the raw total Shadbala (Rupas) folded with the afflictions
    and dignities he weighs alongside Bala (NH_GAP_ANALYSIS Theme 1). Papakartari (hemmed by
    malefics), a dusthana (6/8/12) placement, a node-conjunction, and combustion penalise the
    reading; a dignified planet (exalt/own/moolatrikona, or a cancelled debilitation) credits it.
    Every weight lives on ``shadbala_total`` and DEFAULTS TO 0.0 — with the shipped defaults this
    returns ``raw_rupas`` UNCHANGED via an early return (a strict no-op; the golden ratchet is
    untouched and no affliction work runs). The holdout-locked tuner searches the weights; a
    nonzero config ships only if it improves the fit set without dropping the held-out set."""
    w_pk = shadbala_total.EFF_W_PAPAKARTARI
    w_du = shadbala_total.EFF_W_DUSTHANA
    w_no = shadbala_total.EFF_W_NODE
    w_co = shadbala_total.EFF_W_COMBUST
    w_di = shadbala_total.EFF_W_DIGNITY
    if not (w_pk or w_du or w_no or w_co or w_di):
        return raw_rupas                      # all weights zero -> strict no-op, no affliction work
    p = chart.planets.get(planet)
    if p is None:
        return raw_rupas
    eff = raw_rupas
    if w_pk and HemmedBy(planet, "malefic").evaluate(EvalContext(chart)):
        eff -= w_pk
    if w_du and p.rasi_house in (6, 8, 12):
        eff -= w_du
    if w_no and any(chart.planets.get(n) is not None and chart.planets[n].rasi_house == p.rasi_house
                    for n in ("Rahu", "Ketu") if n != planet):
        eff -= w_no
    if w_co:
        eff -= w_co * (p.combust_fraction or 0.0)
    if w_di and (dignity(planet, chart) in ("exalt", "own", "moolatrikona")
                 or neecha_bhanga(planet, chart)):
        eff += w_di
    return eff


def _strong(planet: str, chart: RamanChart) -> Optional[bool]:
    """Legacy ``house_judge._strong`` semantics: None on Track-B, else is_powerful — now read off
    the B1 effective strength (a strict no-op at the shipped all-zero affliction weights)."""
    p = chart.planets.get(planet)
    if p is None or p.shadbala_rupas is None:
        return None
    eff = _effective_strength(planet, p.shadbala_rupas.total / 60.0, chart)
    return shadbala_total.is_powerful(planet, eff)


#: B1 comparative weighing (DOCTRINE_BACKLOG B1). ENABLED 2026-08-03 on an explicit user
#: decision, knowing it trades strict exact accuracy for fewer catastrophic errors:
#: strict 261/293 -> 259/293, within-1 ordinal 281/293 -> 283/293, real errors (dist>=2) 12 -> 10.
#: Both golden baselines were re-based in the same commit, per the human-bump rule. This is the
#: first DOWNWARD strict re-base in the project's lineage and it is deliberate: a favourable/
#: afflicted inversion is a worse failure than a favourable/mixed boundary call, and HTJAH-I:3788
#: is explicit that a powerless lord denies the matter. Read LIVE off the module so a sweep can
#: rebind it, exactly like the CONTRA_PILLAR_* knobs.
B1_DOMINANT_FACTOR_GUARD: bool = True

#: Houses whose significations the B1 guard does NOT act on. EMPTY by default — the guard
#: applies everywhere. Exists because the enablement measurement showed half the guard's
#: regressions were H12/moksha, and H12 is an atlas-proven INVERTED channel; scoping the guard
#: away from such houses would likely improve both ratchet metrics, but that is fitting to the
#: goldens (MEASURED TRUTH: overfitting to worked examples is not accuracy), so any entry here
#: is a HUMAN decision recorded in DOCTRINE_BACKLOG B1, never a tuner move. Read LIVE.
B1_GUARD_EXEMPT_HOUSES: frozenset[int] = frozenset()

#: DIRECTIONAL PARIVARTANA (DOCTRINE_BACKLOG "Directional parivartana"). Both OFF —
#: this is a MEASUREMENT, not a shipped rule; enabling either is a human decision on the
#: recorded numbers, exactly as B1 was. Read LIVE off the module so a sweep can rebind them.
#:
#: Today `_decide` credits an exchange as flat relief: a debilitated lord or karaka in a
#: parivartana has its penalty bypassed regardless of what the partner is doing. Raman's own
#: worked charts run both ways — "mutually benefiting each other" (HTJAH-I:8837), but also
#: "Saturn who is the 7th lord ALSO IS AFFLICTED BY THIS PARIVARTANA" (HTJAH-I:9119) and
#: "his exchange of signs with 5th lord Saturn is not desirable as it can deny marriage or
#: progeny" (HTJAH-I:9143). On that showing an exchange transmits the partner's condition.
#:
#: Arm A — withhold: grant the relief only when the exchange partner is itself unafflicted.
PARIVARTANA_DIRECTIONAL: bool = False
#: Arm B — transmit: an exchange with an afflicted or dusthana-lording partner makes the
#: lord itself count as hard-afflicted (what HTJAH-I:9119 says in as many words), which is
#: what the B1 dominant-factor guard reads. Strictly stronger than arm A.
PARIVARTANA_TRANSMITS: bool = False


def _lord_hard_afflicted(lord: str, chart: RamanChart) -> Optional[bool]:
    """Does the LORD carry an affliction Raman reads as overriding its Shadbala total?

    HTJAH-I:3788 is the case: "Though the Karaka Mars is well disposed, the fact of the ruler
    of the third becoming combust and hence powerless, renders the third house weak. This
    stands against his having any brothers." The lord's Shadbala reads strong; Raman calls it
    powerless and DENIES the matter — so a strong karaka must not be allowed to carry it.

    Only the two afflictions Raman treats as making a planet powerless in itself count here:
    combustion and an uncancelled debilitation. Dusthana placement is deliberately excluded —
    Raman's dusthana readings are matter-specific (a strong dusthana lord FEEDS an affliction,
    clause 1.5), so folding it in would double-count. None on Track-B."""
    p = chart.planets.get(lord)
    if p is None or p.shadbala_rupas is None:
        return None
    es = effective_strength(lord, chart)
    return bool(es.combust > 0.0 or es.debilitated_uncancelled)


def _total_shadbala(planet: str, chart: RamanChart) -> Optional[float]:
    p = chart.planets.get(planet)
    if p is None or p.shadbala_rupas is None:
        return None
    return p.shadbala_rupas.total


# ---------------------------------------------------------------------------
# Decision rule — ORDER IS LOAD-BEARING.
# ---------------------------------------------------------------------------

def _navamsa_modulate(base: Verdict, L: FrameLedger) -> tuple[Verdict, bool]:
    """D9 only nudges a BORDERLINE 'mixed'; decisive favourable/afflicted never shift."""
    if base in ("favourable", "afflicted"):
        return base, False
    if L.navamsa_status == "confirms" and base == "mixed":
        return "favourable", True
    if L.navamsa_status == "weakens" and base == "mixed":
        return "afflicted", True
    return base, False


def _decide(L: FrameLedger) -> tuple[Verdict, bool]:
    """Collapse a ledger to (verdict, borderline_shifted). The clause order matters."""
    # Longevity guard — SPAN only. For the numeric life-SPAN (`longevity` sig) the span class
    # and maraka are owned by the unbuilt ayurdaya pre-pass, so this judge must NOT emit a
    # span verdict from raw positions (HTJAH-II:3477-3479) — it defers to insufficient-
    # evidence. The guard therefore (a) neutralises maraka_active's verdict-driving effect,
    # (b) replaces the karaka VETO's afflicted with insufficient-evidence, and (c) clamps any
    # afflicted the remaining clauses would produce. The `death` MANNER sig is NOT guarded —
    # it judges the 8th-house affliction directly (see clause 1.5 AFFLICTION_MATTER).
    guarded = "LONGEVITY_GUARD" in L.flags
    # B3 — non-death-marital maraka guard (HTJAH-II:2579): maraka pressure speaks to the
    # DEATH of the spouse ("the death of the husband or wife will occur"), not to marital
    # HAPPINESS. The 7th being a maraka house lands Venus-the-karaka in the maraka set, so
    # without this guard a barely-weak Venus over-afflicts the happiness sub-matter on
    # maraka pressure alone. Same shape as LONGEVITY_GUARD but strictly narrower: only
    # maraka's verdict-driving effect is suppressed — the karaka veto, fired malefics and
    # every other clause keep their full force, and the ledger still records maraka_active
    # honestly for reporting. (The Kuja-dosha CANCELLATIONS are separately encoded in
    # _KujaDosha, HTJAH-II:2593-2601 — this is not a missing-cancellation patch.)
    maraka_drives = (L.maraka_active and not guarded
                     and "MARAKA_NON_DEATH_GUARD" not in L.flags)
    # 1. karaka veto — a broken karaka afflicts the matter regardless of evidence.
    if not L.karaka_intact:
        if guarded:
            return _navamsa_modulate("insufficient-evidence", L)
        return _navamsa_modulate("afflicted", L)
    # 1.5 DUSTHANA-AFFLICTION CONFIRMATION (Stage-3, user-signed-off "B"). For an inherently
    # malefic signification (6th disease/enemies/debts/accidents; 12th incarceration/left_eye;
    # 8th death/manner — flagged AFFLICTION_MATTER in _build_frame_ledger) a fired malefic with
    # NO benefic contradiction CONFIRMS the affliction. This is the directional mirror of the
    # clause-2 navamsa guard: pillar strength does NOT rescue a dusthana evil (a strong 6th lord
    # strengthens disease; a strong chart cannot make a violent death un-afflicted), so the
    # matter must not fall through to clause 6/8 and read as 'mixed', nor be lifted by a
    # confirming navamsa. A BENEFIC contradiction (a Vipareeta / Harsha yoga, a benefic in/on
    # the 8th, or a benefic aspect) routes the matter back to the normal preponderance weigh at
    # clause 2 (preserving the 'natural death' reading on a beneficially-disposed 8th). Applies
    # to `death` (manner) but NOT to the `longevity` SPAN, which is still guarded. The verdict
    # is decisive — _navamsa_modulate never shifts an 'afflicted'.
    if ("AFFLICTION_MATTER" in L.flags and not guarded
            and L.fired_malefic and not L.fired_benefic):
        return _navamsa_modulate("afflicted", L)
    # 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire.
    # Faithful to Raman's THREE-FACTORS doctrine: instead of counting fired-rule surplus,
    # weigh the three strength PILLARS — lord, karaka, Bhava-Bala. Count only the KNOWN
    # pillars (Shadbala present -> not None; fresh-cast goldens HAVE Shadbala, so theirs
    # ARE populated). If enough pillars are weak the "factors" are afflicted; if enough
    # are strong AND the navamsa does not weaken they are favourable; otherwise the matter
    # is genuinely 'mixed'.
    # The two knobs are read LIVE off the module (NOT import-time-bound) so the threshold
    # tuner's monkeypatch of shadbala_total.CONTRA_PILLAR_* takes effect during a sweep.
    # Defaults are 3/2 (Stage-3 calibration, user-signed-off "V2"). On Track-B (all pillars
    # None) the known set is empty -> "mixed" (safe).
    #
    # NAVAMSA GUARD (Stage-3, the load-bearing half of "V2"): the FAVOUR lift additionally
    # requires ``L.navamsa_status != "weakens"``. The navamsa (D9) is Raman's confirmation
    # varga — a contradicted matter the Rasi pillars read as strong but the D9 weakens (lord
    # or karaka D9-debilitated or in a 6/8/12 from the navamsa lagna) is genuinely afflicted,
    # not favourable. Without this guard the strong-pillar 'favourable' is DECISIVE and
    # preempts the navamsa down-modulation below — inverting the H9 father-death charts and
    # the H2 afflictions to 'favourable'. With the guard, a weakening-D9 strong-pillar matter
    # falls through to 'mixed', where _navamsa_modulate then drops it to 'afflicted'. This is
    # the same discipline the navamsa/yoga modulators already obey: a contradiction is never
    # painted over. The AFFLICTED preponderance stays unguarded and DECISIVE (navamsa
    # 'confirms' never lifts an afflicted; only a borderline 'mixed' is nudged).
    if L.fired_benefic and L.fired_malefic:
        pillars = [L.lord_strong, L.karaka_strong, L.bhava_bala_strong]
        known = [p for p in pillars if p is not None]
        weak = sum(1 for p in known if p is False)
        strong = sum(1 for p in known if p is True)
        if known and weak >= shadbala_total.CONTRA_PILLAR_AFFLICT:
            base = "afflicted"
        # B1 DOMINANT-FACTOR GUARD (HTJAH-I:3788): a lord that is combust or debilitated-
        # uncancelled is "powerless" in Raman's own reading, and he DENIES the matter on that
        # basis even though the karaka is well disposed. Counting pillars cannot express it —
        # lord-weak + karaka-strong + bhava-strong counts 2 strong and lifts to favourable,
        # exactly inverting him. So the strong-pillar lift is blocked when the LORD carries a
        # hard affliction; the matter falls through to 'mixed', where the navamsa modulator
        # still has its say. Same shape as the navamsa guard above: a contradiction is never
        # painted over, and the AFFLICTED arm stays untouched.
        elif (known and strong >= shadbala_total.CONTRA_PILLAR_FAVOUR
                and L.navamsa_status != "weakens"
                and not (B1_DOMINANT_FACTOR_GUARD and L.lord_hard_afflicted)):
            base = "favourable"
        else:
            base = "mixed"
        return _navamsa_modulate(base, L)
    # 3. Track-B fallback — no Shadbala -> decide on rule polarity / maraka alone.
    if L.lord_strong is None or L.karaka_strong is None:
        if L.fired_malefic or maraka_drives:
            base: Verdict = "afflicted"
        elif L.fired_benefic:
            base = "favourable"
        else:
            base = "insufficient-evidence"
        v, shifted = _navamsa_modulate(_clamp_longevity(base, guarded), L)
        return _clamp_longevity(v, guarded), shifted
    # 4. both pillars known.
    both_strong = bool(L.lord_strong) and bool(L.karaka_strong)
    bhava_ok = (L.bhava_bala_strong is True) or (L.bhava_bala_strong is None)
    bhava_strong = L.bhava_bala_strong is True
    weak_pillar = (not L.lord_strong) or (not L.karaka_strong)
    # 5. clean strength + supportive bhava + no malefic -> favourable.
    if both_strong and bhava_ok and not L.fired_malefic:
        base = "favourable"
    # 6. a weak pillar with malefic / weak-bhava / maraka pressure -> afflicted...
    elif weak_pillar and (L.fired_malefic or L.bhava_bala_strong is False or maraka_drives):
        base = "afflicted"
        # BHAVA-RESCUE (HTJAH-I:503-505): "if the lord is badly placed, and the house
        # itself has good conjunctions and aspects then evil results should not be
        # predicted." The rescue agent is the BHAVA — benefic rules firing ON the house
        # (fired_benefic) backed by a strong Bhava Bala — NOT the karaka. When the bhava
        # carries good aspects and there is no benefic-vs-malefic contradiction (that
        # contradiction was already routed to 'mixed' at clause 2), demote afflicted.
        if (not L.lord_strong) and L.fired_benefic and bhava_strong:
            base = "mixed"
        # KARAKA-SALVAGE (three-pillar doctrine — methodology §2 / HTJAH-II:221;
        # the lord's dual ownership+karaka role HTJAH-I:985): a decisively strong karaka
        # can still deliver a weak-lord, lone-malefic matter -> demote afflicted to mixed.
        elif L.karaka_strong and not L.lord_strong and L.fired_malefic and not L.fired_benefic:
            base = "mixed"
    # 7. nothing fired at all -> insufficient-evidence.
    elif not (L.fired_benefic or L.fired_malefic or L.fired_neutral):
        base = "insufficient-evidence"
    # 8. everything else is a genuine borderline -> mixed.
    else:
        base = "mixed"
    # 9. final D9 modulation of a borderline mixed (after the longevity clamp).
    v, shifted = _navamsa_modulate(_clamp_longevity(base, guarded), L)
    return _clamp_longevity(v, guarded), shifted


def _clamp_longevity(base: Verdict, guarded: bool) -> Verdict:
    """Under the longevity guard, an 'afflicted' (death) verdict is deferred to the
    Phase-E longevity sub-engine -> reported as insufficient-evidence here."""
    if guarded and base == "afflicted":
        return "insufficient-evidence"
    return base


# Avastha result-strength scores (Layer-A doctrinal deepening). Phaladeepika Ch.3 Sl.3/Sl.10/
# Sl.20 + BPHS Ch.1 Sl.14-16: a graha's avastha scales the INTENSITY of its result (both the
# auspicious AND the inauspicious effect — "decreasing proportionately", Sl.20; "full" at
# praditavastha), NEVER the polarity. Baladi (ageing 5-state) + Jagradadi (consciousness
# 3-state), each -> {+1,0,-1}. Bala (infancy) is scored -1 — "progressing", the least of the
# developing states (Phaladeepika Sl.10), so it weakens delivery.
_BALADI_SCORE: dict[str, int] = {"Yuva": 1, "Kumara": 0, "Bala": -1, "Vriddha": -1, "Mrita": -1}
_JAGRADADI_SCORE: dict[str, int] = {"Jagrad": 1, "Swapna": 0, "Sushupti": -1}
# Avastha degree adjustment: combined deliverer score -1 DEMOTES one step (a Mrita/Sushupti
# deliverer enfeebles), +1 PROMOTES a moderate to strong (Sl.20 "full effect" when both
# deliverers are yuva/jagrad). Promotion lifts only moderate->strong — a marginal/mild verdict
# is not promoted (its margin dominates the avastha).
_DEGREE_DEMOTE: dict[Degree, Degree] = {"strong": "moderate", "moderate": "mild", "mild": "mild"}
_DEGREE_PROMOTE: dict[Degree, Degree] = {"moderate": "strong"}


def _safe_avasthas(chart: RamanChart) -> Optional[dict[str, object]]:
    """Per-planet baladi+jagradadi avastha over the D1, or None when a graha is absent
    (Track-B stated-position book charts). ``compute_avasthas`` RAISES ValueError on a missing
    graha, so the degree modulation degrades gracefully to 'no change' — the mandatory crash
    guard flagged by the doctrine-review."""
    try:
        d1 = {name: {"sign": p.sign, "degree_in_sign": p.lon % 30.0}
              for name, p in chart.planets.items()}
        return compute_avasthas(d1)
    except (ValueError, KeyError):
        return None


def _planet_avastha_score(avasthas: Optional[dict[str, object]], planet: str) -> int:
    """A graha's avastha intensity in {-1, 0, +1}: clamped sum of its baladi + jagradadi
    scores. 0 when the avastha is unavailable (Track-B) or the state is unrecognised."""
    if not avasthas or planet not in avasthas:
        return 0
    info = avasthas[planet]
    score = _BALADI_SCORE.get(info["baladi"], 0) + _JAGRADADI_SCORE.get(info["jagradadi"], 0)
    return max(-1, min(1, score))


def baladi_jagradadi_states(chart: RamanChart) -> dict[str, dict[str, str]]:
    """READ-ONLY accessor (2026-08-17, report-completeness): the per-planet Baladi (ageing)
    and Jagradadi (consciousness) avastha states this judge already computes via
    ``_safe_avasthas`` and uses ONLY to scale verdict intensity (``_avastha_combined`` ->
    ``_compute_degree``). Exposed so the report surfaces can SHOW what the judge consumed —
    it re-reads the same pure computation and touches no verdict logic.

    Provenance (same as the scoring tables above): CLASSICAL_NONCITABLE — Phaladeepika
    Ch.3 Sl.3/Sl.10/Sl.20 + BPHS Ch.1 Sl.14-16 — outside Raman's own canon.

    Returns {graha: {"baladi": state, "jagradadi": state}}; {} on Track-B stated-position
    charts where a graha is missing (the same graceful degradation the judge itself uses).
    """
    avasthas = _safe_avasthas(chart)
    if not avasthas:
        return {}
    return {planet: {"baladi": str(info["baladi"]), "jagradadi": str(info["jagradadi"])}
            for planet, info in avasthas.items()}


def _avastha_combined(avasthas: Optional[dict[str, object]], lord: str, karaka: str) -> int:
    """The verdict's combined deliverer avastha in {-1, 0, +1}: MIN of the lord's and karaka's
    scores. MIN = 'the weakest deliverer caps the intensity' (mirrors the karaka-veto
    philosophy; a strong karaka cannot rescue a Mrita lord, per Phaladeepika Sl.20) — and,
    symmetrically, +1 requires BOTH deliverers in a strong (yuva/jagrad) avastha."""
    return min(_planet_avastha_score(avasthas, lord),
               _planet_avastha_score(avasthas, karaka))


def _compute_degree(verdict: Verdict, lead: FrameLedger, shifted: bool,
                    av_adjust: int = 0) -> Degree:
    """The deterministic INTENSITY of a verdict (Layer A), from the gradation the engine
    already computes — pillar-strength count, the decisive/karaka-veto flags, and whether the
    verdict was nudged at the margin. Surfaces existing strength as strong/moderate/mild; it
    does NOT change the verdict bucket and needs no golden re-grading.

    - mild   : the verdict was shifted at the margin (navamsa modulation / a relief floor) —
               the weakest commitment; or insufficient-evidence (no evidence to grade).
    - strong : the verdict rests on the engine's maximal evidence — for favourable, all known
               pillars strong (navamsa-confirmed) or a 2+ strong majority; for afflicted, a
               decisive-affliction rule / broken karaka, or all known pillars weak.
    - moderate: everything in between (a clear but not maximal majority).

    ``av_adjust`` (Layer-A deepening, in {-1,0,+1}): when the verdict's delivering grahas (lead
    lord + karaka) are net-weak (-1) the intensity drops ONE step (strong->moderate,
    moderate->mild); when both are strong (+1) a moderate is lifted to strong. The verdict
    BUCKET is untouched (a Mrita malefic on an afflicted verdict -> afflicted/mild, a
    weaker-but-real affliction, per Phaladeepika Sl.20).
    """
    base = _base_degree(verdict, lead, shifted)
    if av_adjust <= -1:
        return _DEGREE_DEMOTE[base]
    if av_adjust >= 1:
        return _DEGREE_PROMOTE.get(base, base)
    return base


def _base_degree(verdict: Verdict, lead: FrameLedger, shifted: bool) -> Degree:
    """The pillar/flag-derived intensity, before the avastha post-step."""
    if verdict == "insufficient-evidence":
        return "mild"
    if shifted:
        return "mild"
    pillars = (lead.lord_strong, lead.karaka_strong, lead.bhava_bala_strong)
    known = [p for p in pillars if p is not None]
    n_strong = sum(1 for p in known if p is True)
    n_weak = sum(1 for p in known if p is False)
    if verdict == "afflicted":
        decisive = (not lead.karaka_intact) or any(
            fr.rule.id in _DECISIVE_AFFLICTION_RULE_IDS for fr in lead.fired_malefic)
        if decisive or (known and n_weak == len(known)) or n_weak >= 2:
            return "strong"
        return "moderate"
    if verdict == "favourable":
        if (known and n_strong == len(known) and lead.navamsa_status == "confirms") or n_strong >= 2:
            return "strong"
        return "moderate"
    return "moderate"  # mixed: the genuine middle (mild already handled by the shift flag)


# ---------------------------------------------------------------------------
# Ledger construction
# ---------------------------------------------------------------------------

def _frame_lord(chart: RamanChart, sig: Signification, frame: Frame) -> Optional[str]:
    """The bhava-lord for `frame`. None when a frame cannot be built (missing planet)."""
    if frame == "lagna":
        return _lord_of_sign(chart.asc_sign, sig.house)
    if frame == "moon":
        moon = chart.planets.get("Moon")
        if moon is None:
            return None
        return _lord_of_sign(moon.sign, sig.house)
    # KARAKA frame: alternate-core planet's sign acts as the rising sign.
    core = chart.planets.get(sig.alternate_frame_core) if sig.alternate_frame_core else None
    if core is None:
        return None
    return _lord_of_sign(core.sign, sig.house)


def _navamsa_status(lord: str, karaka: str, chart: RamanChart,
                    extra: tuple[str, ...] = ()) -> NavStatus:
    """Confirm/weaken from D9 — works on Track-B via PlanetPos.navamsa_sign.

    confirms : any pillar is vargottama or D9-exalted/own.
    weakens  : any pillar is D9-debilitated, or sits in a 6/8/12 from the navamsa lagna.
    unknown  : navamsa data absent for all pillars.

    Pillars = the bhava LORD and natural KARAKA, PLUS `extra` (D9-4: the house's HOLLOW
    occupants — exalted in the rashi but debilitated in the navamsa. Raman re-judges a bhava's
    occupants in the navamsa, and a planet 'though exalted [in rashi] ... debilitated in the
    Navamsha' has its promised good withheld [Grahanam Amsakam Balam]; such an occupant
    contributes a weakens, hollowing the bhava's promise just as a weak lord does. The symmetric
    uplift direction (D9-6/B1) — an occupant DEBILITATED in the rashi but EXALTED in the navamsa
    ("debilitated in Rasi but exalted in Navamsa makes the native happy") — is also passed in
    `extra` and routes through the confirms branch, redeeming the bhava's promise.)"""
    nav_lagna_sign = varga.navamsa_sign(chart.asc_lon)
    saw_any = False
    confirms = False
    weakens = False
    for name in (lord, karaka, *extra):
        p = chart.planets.get(name)
        if p is None:
            continue
        nav = getattr(p, "navamsa_sign", None)
        if nav is None:
            continue
        saw_any = True
        # confirms: vargottama, or D9 sign is the planet's exaltation/own sign.
        if p.vargottama:
            confirms = True
        elif name in r.EXALTATION and nav == r.EXALTATION[name][0]:
            confirms = True
        elif SIGN_LORDS.get(nav) == name:
            confirms = True
        # weakens: D9 debilitation, or 6/8/12 from the navamsa lagna.
        if name in r.DEBILITATION and nav == r.DEBILITATION[name][0]:
            weakens = True
        d9_house = ((nav - nav_lagna_sign) % 12) + 1
        if d9_house in _D9_WEAK_HOUSES:
            weakens = True
    if not saw_any:
        return "unknown"
    if confirms and not weakens:
        return "confirms"
    if weakens and not confirms:
        return "weakens"
    return "neutral"


def _saptamsa_status(lord: str, karaka: str, chart: RamanChart,
                     extra: tuple[str, ...] = (), include_seats: bool = False) -> NavStatus:
    """Confirm/weaken from the Sapthamsa (D-7) — the CHILDREN/progeny varga.

    The D-7 confirmation read, scoped to progeny. Where the navamsa is Raman's GENERAL
    confirmation varga, the Sapthamsa is the child-specific one ("Saptamsa for children",
    HPA-11:198; rasi = promise, the varga = fruit, HtJaH:979). It reads the two children
    significators — the D-1 5th ``lord`` and Putrakaraka ``karaka`` (Jupiter) — INSIDE the
    cast D-7 chart, by the dignity + dusthana subset of the reviewer-validated per-varga
    model (``judges/varga_judge.py``). This is a significators-in-the-varga read (mirroring
    ``_navamsa_status``), distinct from the varga_judge REPORT row, which reads the D-7 *lagna* lord.

    ``include_seats`` (D7-4 Item 2): when True, a malefic-afflicted D-7 child-seat
    (``_d7_seat_occupancy``) folds in as an extra WEAKEN (weaken-only — a benefic seat never
    lifts; see that helper). This is the one place occupancy feeds a varga status — justified
    because the D-7 lagna IS the eldest-child seat, not a generic varga lagna. Off by default,
    so every existing caller keeps the pillars-only read.

    Pillars = ``lord`` and ``karaka``, PLUS ``extra`` (D7-4: the 5th house's HOLLOW/REDEEMED
    occupants — the exact D-7 mirror of the D9-4/D9-6 occupant the caller selects for
    ``_navamsa_status``. An occupant exalted in the rashi but debilitated in the D-7 has its
    promised good withheld in the child-varga → routes through the weakens branch; the mirror
    (debilitated in rashi but exalted in the D-7) redeems, routing through confirms. The caller
    (``_saptamsa_gate`` via ``_d7_hollow_redeemed_occupants``) selects only that surgical
    subset, exactly as the D9-4 caller does — the broad "all occupants" form was rejected there.)

    confirms : a pillar is D-7-exalted, or in its own D-7 sign;
    weakens  : a pillar is D-7-debilitated, or sits in a 6/8/12 from the D-7 lagna;
    unknown  : D-7 data absent for all pillars (sparse / Track-B) — a safe no-op.

    NOTE (deliberate): the D1==D9 ``vargottama`` credit is NOT counted here. Vargottama is a
    *navamsa* fact already weighed by ``_navamsa_status`` in the verdict path; crediting it
    again in the D-7 would double-use one datum across two varga layers and let a "D-7 confirm"
    rest on evidence that is not the Sapthamsa's own. So this status is purely D-7-native.

    Works on Track-B: ``cast_varga_chart`` needs only ``asc_lon`` + per-planet ``lon``.
    Pure read — imported into the verdict path ONLY via the children-scoped ``_saptamsa_gate``
    (which nudges a borderline 'mixed' one step, never a decisive verdict)."""
    vc = cast_varga_chart(chart, 7)
    saw_any = False
    confirms = False
    weakens = False
    for name in (lord, karaka, *extra):
        pos = vc.positions.get(name)
        if pos is None:
            continue
        saw_any = True
        sign = pos.sign
        # confirms: the D-7 sign is the planet's exaltation or own sign (D-7-native only —
        # vargottama is a D9 fact and is intentionally excluded; see the docstring NOTE).
        if name in r.EXALTATION and sign == r.EXALTATION[name][0]:
            confirms = True
        elif SIGN_LORDS.get(sign) == name:
            confirms = True
        # weakens: D-7 debilitation, or a 6/8/12 from the D-7 lagna.
        if name in r.DEBILITATION and sign == r.DEBILITATION[name][0]:
            weakens = True
        if pos.house is not None and pos.house in _VARGA_DUSTHANA:
            weakens = True
    if include_seats and _d7_seat_occupancy(vc) == "weakens":
        # Weaken-only: a malefic-afflicted D-7 child-seat tempers a borderline verdict down;
        # it can never lift one (deny-but-never-affirm; see _d7_seat_occupancy).
        saw_any = True
        weakens = True
    if not saw_any:
        return "unknown"
    if confirms and not weakens:
        return "confirms"
    if weakens and not confirms:
        return "weakens"
    return "neutral"


def _d7_hollow_redeemed_occupants(chart: RamanChart, lord: str, karaka: str) -> tuple[str, ...]:
    """The 5th house's HOLLOW / REDEEMED occupants for the D-7 (D7-4) — the exact mirror of the
    D9-4/D9-6 occupant the caller selects for ``_navamsa_status``.

    HOLLOW  : an occupant EXALTED in the rashi but DEBILITATED in the D-7 — the promise set up
              in the rasi is withheld in the child-varga (Grahanam Amsakam Balam applied to the
              Sapthamsa); it contributes a weakens.
    REDEEMED: the mirror — DEBILITATED in the rashi but EXALTED in the D-7 — contributes a
              confirms.

    Only that surgical subset is returned (the broad "all strong occupants" form regressed
    borderline verdicts in D9-4 and is deliberately not used). ``lord``/``karaka`` are excluded
    (already pillars). The confirm/weaken direction is decided downstream by ``_saptamsa_status``
    reading each occupant's own D-7 dignity, so this helper only SELECTS."""
    out: list[str] = []
    for nm, p in chart.planets.items():
        if p.rasi_house != 5 or nm in (lord, karaka):
            continue
        d7 = varga.saptamsa_sign(p.lon)
        exalt_rasi = nm in r.EXALTATION and p.sign == r.EXALTATION[nm][0]
        debil_d7 = nm in r.DEBILITATION and d7 == r.DEBILITATION[nm][0]
        debil_rasi = nm in r.DEBILITATION and p.sign == r.DEBILITATION[nm][0]
        exalt_d7 = nm in r.EXALTATION and d7 == r.EXALTATION[nm][0]
        if (exalt_rasi and debil_d7) or (debil_rasi and exalt_d7):
            out.append(nm)
    return tuple(out)


def _d7_seat_occupancy(vc: VargaChart) -> NavStatus:
    """D7-4 Item 2: the malefic OCCUPANCY of the two child-seats in the D-7. WEAKEN-ONLY.

    Seats: the D-7 lagna (house 1) — the eldest-child seat (D7 methodology §3; the whole D-7
    overlay reading centres on it, e.g. Mars+Ketu there in field_case_01) — and the
    5th-from-D-7-lagna (house 5), the continuity / child-of-the-child seat. A malefic on a
    child-seat afflicts progeny — Raman's Rāśi-5th malefic-occupancy doctrine
    (``saptamsa_reading._MALEFIC_5TH_EFFECT``: Sun/Mars/Saturn/Rahu/Ketu each cited;
    H5.C.18-19 HTJAH-I:5205-5206) applied to the D-7's own child-seats by the general varga
    principle. This is the FIRST place occupancy feeds a varga *status* (report-only in
    ``varga_judge``, absent from ``_navamsa_status``); warranted HERE because the D-7 lagna is
    not a generic varga lagna — it IS the eldest-child seat.

    WEAKEN-ONLY, not symmetric (bphs-doctrine-reviewer ruling, 2026-07-23): Raman's progeny
    apparatus DENIES but never AFFIRMS — the malefic-in-5th map is malefic-only (no "benefic
    confers children" verse), and a benefic-lift would break the same deny-but-never-affirm
    asymmetry the fertility gate and the Item-1 sphuta guard already enforce. So a benefic on a
    child-seat can only OFFSET a malefic ON THE SAME SEAT, never lift a verdict.

    PER-SEAT (not pooled net): each seat is judged on its own occupants, so a benefic on the
    continuity seat (house 5) cannot cancel a malefic on the primary eldest seat (house 1) —
    the eldest seat is the citable locus (``saptamsa_reading.py`` eldest=general-principle).
    Uses the full locked NATURAL_MALEFICS set (Sun + nodes included; cruel-only does not
    transfer to children — Raman names the Sun and both nodes as 5th-house progeny afflictors)."""
    for house in (1, 5):
        ben = mal = 0
        for name, pos in vc.positions.items():
            if pos.house != house:
                continue
            if name in NATURAL_BENEFICS:
                ben += 1
            elif name in NATURAL_MALEFICS:
                mal += 1
        if mal > ben:
            return "weakens"
    return "neutral"


def _combust_graded(planet: str, chart: RamanChart) -> bool:
    """Is `planet` at least half-combust (combust_fraction >= 0.5)? One threshold for all
    planets (B7 unification — the former Saturn/Venus 0.85 exemption was removed; see the
    _COMBUST_HARD_FRACTION note)."""
    p = chart.planets.get(planet)
    if p is None:
        return False
    return p.combust_fraction >= _COMBUST_HARD_FRACTION


def _debilitated_uncancelled(planet: str, chart: RamanChart) -> bool:
    p = chart.planets.get(planet)
    if p is None:
        return False
    return dignity(planet, chart) == "debil" and not neecha_bhanga(planet, chart)


def _maraka_grahas(chart: RamanChart) -> frozenset[str]:
    """The maraka graha set from chart.maraka_points (empty when absent / Track-B)."""
    mp = chart.maraka_points
    if mp is None:
        return frozenset()
    return frozenset(u.graha for u in mp.units)


def _karaka_intact(karaka: str, chart: RamanChart, marakas: frozenset[str]) -> bool:
    """A karaka is NOT intact only when triply afflicted: combust (graded) AND
    debilitated-uncancelled AND a maraka hit. Any single affliction is survivable."""
    maraka_hit = karaka in marakas
    return not (_combust_graded(karaka, chart)
                and _debilitated_uncancelled(karaka, chart)
                and maraka_hit)


def _parivartana_pairs(chart: RamanChart, ctx: EvalContext) -> frozenset[frozenset[str]]:
    """All bhava-lord exchange pairs, cached on the EvalContext. Returns a set of
    2-element frozensets of planet names."""
    def _compute() -> frozenset[frozenset[str]]:
        pairs: set[frozenset[str]] = set()
        for h1 in range(1, 13):
            for h2 in range(h1 + 1, 13):
                if parivartana(h1, h2, chart):
                    l1 = _lord_of_sign(chart.asc_sign, h1)
                    l2 = _lord_of_sign(chart.asc_sign, h2)
                    if l1 != l2:
                        pairs.add(frozenset({l1, l2}))
        return frozenset(pairs)

    return ctx.get_or_compute("parivartana_pairs", _compute)


def _in_parivartana(planet: str, pairs: frozenset[frozenset[str]]) -> bool:
    return any(planet in pair for pair in pairs)


def _parivartana_partners(planet: str, pairs: frozenset[frozenset[str]]) -> frozenset[str]:
    """Every planet `planet` has exchanged signs with (a graha can hold two exchanges)."""
    return frozenset(other for pair in pairs if planet in pair
                     for other in pair if other != planet)


#: Which reading of "afflicted partner" the directional arms use. Raman's two counter-
#: examples do NOT name the same mechanism, so the choice is a doctrine call, not a tuning
#: knob, and each is measured separately:
#:   "condition" — the partner is combust, debilitated-uncancelled, or a maraka.
#:   "dusthana"  — the partner lords a dusthana; this is the mechanism in HTJAH-I:9119
#:                 ("the 8th and 10th lords have exchanged signs so that Saturn ... also is
#:                 afflicted by this parivartana"), where the 8th lordship is what travels.
#:   "either"    — the union.
#: HTJAH-I:9143 ("exchange ... with 5th lord Saturn is not desirable") fits NEITHER: the 5th
#: is no dusthana and Saturn is not described as afflicted there, so that objection is to the
#: exchange itself and is deliberately NOT encoded by any of these.
PARIVARTANA_PARTNER_TEST: str = "either"


def _partner_afflicted(planet: str, pairs: frozenset[frozenset[str]], chart: RamanChart,
                       marakas: frozenset[str]) -> bool:
    """Is the far end of the exchange itself in trouble?

    Built only from vocabulary the module ALREADY judges by — combustion, an uncancelled
    debility, maraka membership, dusthana lordship — so this introduces no new scale, only
    a direction. ANY partner in trouble counts: a graha holding two exchanges cannot be
    shielded by the healthy one while the other transmits (HTJAH-I:9119).
    """
    test = PARIVARTANA_PARTNER_TEST
    for partner in _parivartana_partners(planet, pairs):
        if test in ("condition", "either") and (
                _combust_graded(partner, chart)
                or _debilitated_uncancelled(partner, chart)
                or partner in marakas):
            return True
        if test in ("dusthana", "either") and any(
                _lord_of_sign(chart.asc_sign, d) == partner for d in (6, 8, 12)):
            return True
    return False


def _bhava_bala_for(chart: RamanChart, house: int) -> Optional[float]:
    """Total Bhava Bala (Shashtiamsas) for `house`, or None on Track-B (no madhyas)."""
    if not chart.bhava_madhyas or len(chart.bhava_madhyas) < house:
        return None
    lord = _lord_of_sign(chart.asc_sign, house)
    lord_sb = _total_shadbala(lord, chart)
    if lord_sb is None:
        return None
    madhya = chart.bhava_madhyas[house - 1]
    bhava_sign = int(madhya // 30) + 1
    bhava_sign_deg = madhya % 30.0
    return bhava_bala_mod.bhava_bala(
        house, chart, lord_shadbala=lord_sb, bhava_madhya=madhya,
        bhava_sign=bhava_sign, bhava_sign_deg=bhava_sign_deg)


def _bucket_fired(
    chart: RamanChart, sig: Signification, ctx: EvalContext,
) -> tuple[tuple[rf.FiredRule, ...], tuple[rf.FiredRule, ...], tuple[rf.FiredRule, ...]]:
    """Fired rules for this house filtered to the signification's rule_tags, bucketed by
    polarity. Functional-nature overlay: a fired rule whose subject planet is a functional
    MALEFIC for this Lagna counts toward malefic even if its static polarity is neutral."""
    tags = set(sig.rule_tags)
    benefic: list[rf.FiredRule] = []
    malefic: list[rf.FiredRule] = []
    neutral: list[rf.FiredRule] = []
    for fr in rf.fire_house_cached(chart, sig.house, ctx):
        if tags and fr.rule.signification not in tags:
            continue
        pol = fr.rule.polarity
        if pol in ("malefic", "maraka"):
            malefic.append(fr)
        elif pol == "benefic":
            benefic.append(fr)
        else:
            # neutral by static polarity; promote to malefic if its subject planet is a
            # functional malefic for this Lagna (HTJAH-I:523-604 functional-nature overlay).
            subj = _rule_subject(fr.rule)
            if subj is not None and subj in chart.planets and \
                    ctx.functional_nature(subj) == "malefic":
                malefic.append(fr)
            else:
                neutral.append(fr)
    return tuple(benefic), tuple(malefic), tuple(neutral)


def _rule_subject(rule) -> Optional[str]:
    """Best-effort subject planet of a rule, parsed from its id (e.g. 'H8.P.Saturn').

    Rule ids encode the planet in the trailing component for planet-in-house rules
    (``H<h>.P.<Planet>``). Returns None when no planet token is present (lord/combination
    rules), in which case the functional-nature overlay simply does not apply."""
    parts = rule.id.split(".")
    if len(parts) >= 3 and parts[1] == "P":
        cand = parts[2]
        # strip any trailing sub-id letters (e.g. 'Saturn1' is not expected, but be safe)
        for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                       "Saturn", "Rahu", "Ketu"):
            if cand.startswith(planet):
                return planet
    return None


def _build_frame_ledger(chart: RamanChart, sig: Signification, frame: Frame,
                        ctx: Optional[EvalContext] = None) -> FrameLedger:
    """Assemble the FrameLedger for one signification in one frame.

    `ctx` lets callers share one per-chart memo store (parivartana pairs,
    functional natures, fired yogas) across frames and significations; when
    omitted a fresh context is created (back-compat with direct callers).
    """
    ctx = ctx if ctx is not None else EvalContext(chart)
    lord = _frame_lord(chart, sig, frame) or _lord_of_sign(chart.asc_sign, sig.house)
    karaka = sig.primary_karaka

    flags: list[str] = []
    lord_karaka_identical = (lord == karaka)
    if lord_karaka_identical:
        flags.append("LORD_KARAKA_IDENTITY")

    # Strength pillars. When lord==karaka the two pillars are collapsed to a single value
    # so one affliction is not double-counted.
    lord_strong = _strong(lord, chart)
    lord_hard = (None if sig.house in B1_GUARD_EXEMPT_HOUSES
                 else _lord_hard_afflicted(lord, chart))  # B1 (HTJAH-I:3788)
    karaka_strong = lord_strong if lord_karaka_identical else _strong(karaka, chart)

    marakas = _maraka_grahas(chart)
    pairs = _parivartana_pairs(chart, ctx)
    parivartana_resilient = _in_parivartana(lord, pairs) or _in_parivartana(karaka, pairs)

    # parivartana leniency: a lord/karaka in an exchange bypasses an inimical/debilitation
    # penalty — treat a debil-but-exchanged pillar as not-weak.
    #
    # PARIVARTANA_DIRECTIONAL (arm A, OFF): withhold that relief where the exchange partner
    # is itself afflicted or lords a dusthana — Raman's exchanges transmit the partner's
    # condition (HTJAH-I:9119, :9143) as readily as they benefit (HTJAH-I:8837).
    lord_partner_bad = _partner_afflicted(lord, pairs, chart, marakas) \
        if _in_parivartana(lord, pairs) else False
    karaka_partner_bad = _partner_afflicted(karaka, pairs, chart, marakas) \
        if _in_parivartana(karaka, pairs) else False
    if parivartana_resilient:
        if lord_strong is False and _in_parivartana(lord, pairs) \
                and _debilitated_uncancelled(lord, chart) \
                and not (PARIVARTANA_DIRECTIONAL and lord_partner_bad):
            lord_strong = True
        if karaka_strong is False and _in_parivartana(karaka, pairs) \
                and _debilitated_uncancelled(karaka, chart) \
                and not (PARIVARTANA_DIRECTIONAL and karaka_partner_bad):
            karaka_strong = True
        if lord_karaka_identical:
            karaka_strong = lord_strong

    # PARIVARTANA_TRANSMITS (arm B, OFF): the exchange does not merely fail to shield, it
    # carries the affliction across — "Saturn who is the 7th lord ALSO IS AFFLICTED BY THIS
    # PARIVARTANA" (HTJAH-I:9119). Expressed as the lord counting hard-afflicted, which is
    # the channel the B1 dominant-factor guard already reads; no new scale is introduced.
    if PARIVARTANA_TRANSMITS and lord_partner_bad and sig.house not in B1_GUARD_EXEMPT_HOUSES:
        lord_hard = True
        flags.append("PARIVARTANA_TRANSMITTED_AFFLICTION")

    bb = _bhava_bala_for(chart, sig.house)
    bb_strong: Optional[bool] = None if bb is None else (bb >= shadbala_total.BHAVA_BALA_MIN_SH)

    # D9-4: a bhava occupant EXALTED in the rashi but DEBILITATED in the navamsa hollows the
    # promise (Raman's explicit "though exalted ... debilitated in Navamsha" — the rasi sets up
    # the promise, the navamsa withholds the fruit). Scoped to exactly this case (rare, surgical):
    # the broad "all strong occupants" form regressed borderline verdicts.
    hollow_occupants = tuple(
        nm for nm, p in chart.planets.items()
        if p.rasi_house == sig.house and nm not in (lord, karaka)
        and nm in r.EXALTATION and p.sign == r.EXALTATION[nm][0]
        and nm in r.DEBILITATION and p.navamsa_sign == r.DEBILITATION[nm][0])
    # D9-6/B1 (symmetric uplift): the mirror — a bhava occupant DEBILITATED in the rashi but
    # EXALTED in the navamsa REDEEMS the promise ("a planet debilitated in Rasi but exalted in
    # Navamsa makes the native happy" — Grahanam Amsakam Balam). The navamsa-exalt routes through
    # the existing confirms branch. Surgical mirror of the hollow case (deferred symmetric direction
    # the D9-4 reviewer flagged).
    redeemed_occupants = tuple(
        nm for nm, p in chart.planets.items()
        if p.rasi_house == sig.house and nm not in (lord, karaka)
        and nm in r.DEBILITATION and p.sign == r.DEBILITATION[nm][0]
        and nm in r.EXALTATION and p.navamsa_sign == r.EXALTATION[nm][0])
    navamsa_status = _navamsa_status(lord, karaka, chart, hollow_occupants + redeemed_occupants)
    karaka_intact = _karaka_intact(karaka, chart, marakas)
    maraka_active = bool(marakas) and (lord in marakas or karaka in marakas)

    benefic, malefic, neutral = _bucket_fired(chart, sig, ctx)

    # Longevity guard — SPAN only (2026-06-25, "do H8 like the other houses"). The numeric
    # life-SPAN (Pindayu/Amsayu ayurdaya year-count → alpa/madhya/purna class) is a pre-pass
    # the classics insist be computed before pronouncing the span (HTJAH-II:3477-3479,
    # 4465-4472); the engine can't yet do it, so the `longevity` signification still defers
    # (LONGEVITY_GUARD suppresses maraka_active + karaka-veto → insufficient-evidence). The
    # `death` MANNER signification is NOT guarded: Raman reads the manner/cause directly off
    # the 8th-house affliction apparatus, independent of the span (HTJAH-II combos #1-2
    # malefics-in-8th → unnatural death; Phaladeepika Ch.14 Sl.12-13/20). `death` is instead
    # an AFFLICTION_MATTER (below) so a fired malefic confirms it. bphs-doctrine-reviewer
    # VALIDATED (HIGH).
    if sig.key == "longevity":
        flags.append("LONGEVITY_GUARD")
    # B3 (HTJAH-II:2579): marital HAPPINESS is a non-death matter — maraka pressure must
    # not drive its verdict (see the guard in _decide). The spouse/death matters are NOT
    # flagged: multiplicity/loss indications keep their maraka sensitivity.
    if sig.key == "marital_happiness":
        flags.append("MARAKA_NON_DEATH_GUARD")
    # AFFLICTION_MATTER (Stage-3 "B"): an inherently-malefic dusthana signification (6th
    # afflictions, 12th incarceration/left_eye). _decide clause-1.5 reads this to confirm the
    # affliction on lone-malefic evidence (a strong dusthana lord strengthens, never rescues).
    if sig.key in _DUSTHANA_AFFLICTION_KEYS:
        flags.append("AFFLICTION_MATTER")
    # LONGEVITY_UNKNOWN: informational marker that a maraka touches a pillar of THIS
    # (possibly non-longevity) matter, so its maraka pressure is provisional until the
    # longevity engine confirms it. Kept for downstream reporting; not verdict-driving.
    if "longevity" in sig.rule_tags or "death" == sig.key or maraka_active:
        flags.append("LONGEVITY_UNKNOWN")

    return FrameLedger(
        frame=frame, lord=lord, lord_strong=lord_strong, karaka=karaka,
        karaka_strong=karaka_strong, bhava_bala=bb, bhava_bala_strong=bb_strong,
        navamsa_status=navamsa_status, karaka_intact=karaka_intact,
        maraka_active=maraka_active, parivartana_resilient=parivartana_resilient,
        lord_karaka_identical=lord_karaka_identical,
        fired_benefic=benefic, fired_malefic=malefic, fired_neutral=neutral,
        flags=tuple(dict.fromkeys(flags)), lord_hard_afflicted=lord_hard)


# ---------------------------------------------------------------------------
# Round-8 wiring: yoga modifier (consideration #4) + H5 fertility gate +
# lookup-grid metadata surfacing. Chosen modulation order (documented):
#
#   _decide (incl. navamsa modulation) -> _yoga_modulate -> _fertility_gate
#
# The yoga step runs AFTER _navamsa_modulate, not before it: _decide is the
# frozen per-FRAME decision pipeline (its clause order is load-bearing and
# unit-pinned), while yogas are CHART-level overlays (HTJAH-I:480-482) that —
# like the Phase-E longevity gate — modulate the finished frame verdict from
# outside. Practically this gives the narrower evidence precedence: a D9-shifted
# borderline is already decisive when the yoga step sees it, so a generic chart
# yoga can never resurrect a matter the house's own varga testimony settled.
# Both layers obey the same discipline — only a still-borderline 'mixed' moves,
# one step, and a decisive verdict is NEVER overturned.
# ---------------------------------------------------------------------------

def _yoga_scope_kinds(sig: Signification) -> frozenset[str]:
    """The yoga kinds that may bear on this signification (kind-scoped wiring).

    'lunar'-kind yogas (Sunapha / Anapha / Durudhura et al.) are DELIBERATELY
    excluded from modulation scope in this phase: a conservative encoding of
    consideration #4 (HTJAH-I:480-482) that lets only dhana/arishta/raja move a
    borderline verdict. Lunar yogas will be surfaced as ':noted' metadata at
    Phase G; until then the asymmetry (lunar yogas neither shift a verdict nor
    appear in metadata) is intentional, not an omission.
    """
    tags = set(sig.rule_tags)
    kinds: set[str] = set()
    if sig.house in _DHANA_HOUSES and tags & _DHANA_TAGS:
        kinds.add("dhana")
    if sig.house == 1 and tags & _ARISHTA_TAGS:
        kinds.add("arishta")
    if sig.house in _RAJA_HOUSES and tags & _RAJA_TAGS:
        kinds.add("raja")
    return frozenset(kinds)


def _yoga_modulate(
    verdict: Verdict, lead: FrameLedger, sig: Signification,
    fired: tuple[FiredYoga, ...],
) -> tuple[Verdict, bool, Metadata]:
    """Consideration #4 (HTJAH-I:480-482): fired yogas modulate a BORDERLINE 'mixed'.

    * dhana on H2/H11 wealth/gains: mixed -> favourable, only when no malefic
      fired (a contradiction is never painted over);
    * arishta (Sakata, uncancelled Kemadruma, et al.) on H1 self: mixed ->
      afflicted — but only a STRENGTH-SPLIT mixed. A clause-2 contradiction-mixed
      (benefic AND malefic both fired) is never dropped: that would hide live
      benefic testimony behind a chart-level yoga. The pinned HTJAH-I chart_33
      H1 flip is driven by Y.SAKATA (Moon Virgo = 12th from Jupiter Libra,
      3HC:2984) acting on a benefic-only strength-split ledger — unaffected by
      this guard. (Kemadruma does NOT form on chart_33: the Moon has planets
      in the 2nd from it.)
    * raja on H9/H10 fortune/career: surfaced as metadata, and lifts a clean
      borderline mixed -> favourable (same no-fired-malefic bar as dhana).

    Decisive verdicts NEVER shift (same discipline as the navamsa modulation).
    Every relevant fired yoga is recorded as ("yoga", "<id>:<direction>") where
    direction is 'lift'/'drop' for the kind that drove a shift, else 'noted'.

    LONGEVITY_GUARD note: the ``not guarded`` arm of the arishta branch is
    currently UNREACHABLE in production wiring — arishta scope is H1 'self'
    (_ARISHTA_TAGS) while the guard flag is set only on H8 longevity/death
    matters, two disjoint sets. It is kept as defensive code (unit-pinned by
    test_arishta_noted_not_dropped_under_longevity_guard) in case a future
    signification carries both an arishta scope and the guard.
    """
    scope = _yoga_scope_kinds(sig)
    relevant = tuple(y for y in fired if y.kind in scope)
    if not relevant:
        return verdict, False, ()
    guarded = "LONGEVITY_GUARD" in lead.flags
    kinds = {y.kind for y in relevant}
    shifted_kind: Optional[str] = None
    new: Verdict = verdict
    if verdict == "mixed":
        # The contradiction guard MUST require BOTH polarities fired: chart_33's
        # ledger is legitimately benefic-only with a strength-split mixed, and its
        # Y.SAKATA drop must keep acting.
        if "arishta" in kinds and not guarded \
                and not (lead.fired_benefic and lead.fired_malefic):
            new, shifted_kind = "afflicted", "arishta"
        elif "dhana" in kinds and not lead.fired_malefic:
            new, shifted_kind = "favourable", "dhana"
        elif "raja" in kinds and not lead.fired_malefic:
            new, shifted_kind = "favourable", "raja"
    direction = {"arishta": "drop", "dhana": "lift", "raja": "lift"}
    metadata = tuple(
        ("yoga", f"{y.id}:{direction[y.kind] if y.kind == shifted_kind else 'noted'}")
        for y in relevant)
    return new, shifted_kind is not None, metadata


def _decisive_affliction(
    verdict: Verdict, lead: FrameLedger, sig: Signification,
) -> tuple[Verdict, bool]:
    """DECISIVE-AFFLICTION RULE (Stage-3 H3/H7 rule-authoring) — the rule-level analogue of
    the dusthana clause-1.5. Certain combinations Raman treats as VERDICT-DRIVING (a
    multiply-afflicted karaka, papakartari on the house in the navamsa, a marriage-
    separation yoga) confirm 'afflicted' even against a strong-pillar preponderance and a
    benefic aspect (chart_58: "Except for the single benefic aspect of Jupiter ... the house
    and the karaka come under affliction" -> afflicted).

    SIGNIFICATION-PRECISE: a decisive rule drives ONLY its own matter — the gate
    ``fr.rule.signification == sig.key`` prevents the leak that ``_bucket_fired`` would
    otherwise allow (a signification with empty ``rule_tags`` buckets every fired house rule,
    so a siblings decisive rule must not be allowed to afflict 'courage'/'short_journeys').
    Deferred under the longevity guard (Phase E owns death/span). 'afflicted' is decisive."""
    if "LONGEVITY_GUARD" in lead.flags or verdict == "afflicted":
        return verdict, False
    fired_decisive = any(
        fr.rule.id in _DECISIVE_AFFLICTION_RULE_IDS and fr.rule.signification == sig.key
        for fr in lead.fired_malefic)
    return ("afflicted", True) if fired_decisive else (verdict, False)


def _catastrophic_severity_gate(
    sig: Signification, verdict: Verdict, lead: FrameLedger,
) -> tuple[Verdict, Metadata]:
    """CATASTROPHIC-KEY SEVERITY GATE. Bodily/liberty ruin — imprisonment, blindness (left_eye),
    a grave accident — is a catastrophic pronouncement Raman makes only on a MULTIPLY-afflicted
    configuration (h12_13: "the 2nd AND the 12th heavily afflicted, the Sun in papakartari";
    h12_14: "the 12th lord afflicted by the nodes in Rasi AND Navamsa"). Empirically every
    confirmed-afflicted incarceration/left_eye golden carries >= 3 fired malefic rules, while an
    ordinary dusthana matter (disease/enemies/debts) fires on one. So for a CATASTROPHIC key an
    'afflicted' resting on fewer than ``_CATASTROPHIC_MIN_MALEFIC`` fired malefic rules is
    over-escalated: the affliction is real (dusthana pressure exists) but not to the
    life-shattering grade — DEMOTE it to 'mixed' (never to favourable; the engine cannot assert
    the matter is clean). DEMOTE-ONLY, scoped to _CATASTROPHIC_KEYS; a genuinely multiply-
    afflicted chart (>= 3 malefic) is untouched, so every Raman jail/blind golden stays
    afflicted (over-fire scanned).

    bphs-doctrine-reviewer SOUND-WITH-CAVEAT/KEEP -- core principle VALIDATED (HIGH for
    incarceration/left_eye, MEDIUM for accidents). Raman draws this exact line himself:
    a SINGLE malefic gives 'defective vision' (HTJAH-II:16465) / left eye 'affected'
    (HTJAH-II:16473), while MULTIPLE afflictions make one 'born blind' (HTJAH-II:16451);
    imprisonment doctrine is inherently plural -- 'Malefics in the 2nd, 5th, 9th and 12th
    houses cause captivity' (HTJAH-II:16426), 'joining Rahu or Ketu' (HTJAH-II:16438). Recorded
    caveats: (1) 'accidents' is analogy-grounded (no accidents golden; inferred from the
    death/maraka corpus HTJAH-I:6649/6361) -- re-test the bar if an accidents golden is later
    authored; (2) 'mixed' here means a REAL but MILD affliction (Raman's 'affected/defective',
    HTJAH-II:16473), NOT a clean matter -- downstream text must not read it as 'no issue';
    (3) the count is on the LEAD frame only, so revisit if the frame-selection heuristic
    changes."""
    if sig.key not in _CATASTROPHIC_KEYS or verdict != "afflicted":
        return verdict, ()
    if len(lead.fired_malefic) >= _CATASTROPHIC_MIN_MALEFIC:
        return verdict, ()
    return "mixed", (("catastrophic_gate",
                      f"{sig.key}:demote(malefic<{_CATASTROPHIC_MIN_MALEFIC})"),)


#: H11 gains matters eligible for the Dhana-yoga floor (wealth-accumulation only).
_DHANA_FLOOR_KEYS: Final[frozenset[str]] = frozenset({"gains", "acquisitions"})

#: Malefics whose association "blemishes" Venus for the marital-happiness floor. The Sun is
#: EXCLUDED: the Sun's affliction of a graha is COMBUSTION (checked separately via
#: combust_fraction), not a mere conjunction/aspect, so a non-combusting Sun on Venus does not
#: disqualify "blemishless" (HTJAH-II:1207, chart_03: Sun on Venus, combust 0 -> still blemishless).
_BLEMISH_MALEFICS: Final[frozenset[str]] = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})


def _blemishless_venus_floor(
    chart: RamanChart, sig: Signification, verdict: Verdict, lead: FrameLedger,
) -> tuple[Verdict, bool, Metadata]:
    """H7 BLEMISHLESS-VENUS floor (Stage-3 doctrine-foundation, user-signed-off). Raman: a
    *blemishless* Venus (good dignity, not combust, unafflicted by the malefic grahas) as
    karaka — and as 7th lord / aspecting the 7th — assures a chaste, devoted wife and marital
    happiness, regardless of a marginal Shadbala (HTJAH-II:1207 "the aspect of a blemishless
    Venus as karaka and 7th lord aspecting the 7th house"; HTJAH-II:368 "Venus in exaltation
    or own vargas -> the wife will be good and beautiful"). This is the faithful, marriage-
    SCOPED fix for the over-harsh chart_03 (Venus 5.32, just under the canonical 5.5 bar, but
    blemishless) — it leaves the canonical Venus Shadbala minimum untouched.

    A decisive-favourable for marital_happiness only: it lifts an afflicted/mixed verdict to
    favourable, but NEVER overrides a genuine decisive affliction (a fired separation/besiege
    rule in _DECISIVE_AFFLICTION_RULE_IDS — that is what spares chart_06: blemishless Venus but
    the 7th is besieged) and never demotes. 'Blemish' = the malefic grahas Saturn/Mars/Rahu/
    Ketu (NOT the Sun — combustion is the Sun's mode, gated separately)."""
    if sig.key != "marital_happiness" or verdict == "favourable" \
            or "LONGEVITY_GUARD" in lead.flags:
        return verdict, False, ()
    if any(fr.rule.id in _DECISIVE_AFFLICTION_RULE_IDS for fr in lead.fired_malefic):
        return verdict, False, ()
    v = chart.planets.get("Venus")
    if v is None or dignity("Venus", chart) in ("debil", "enemy") \
            or v.combust_fraction >= 0.5:
        return verdict, False, ()
    for m in _BLEMISH_MALEFICS:
        p = chart.planets.get(m)
        if p is not None and (p.rasi_house == v.rasi_house
                              or drishti.aspects_planet(m, "Venus", chart)):
            return verdict, False, ()
    venus_7th = (_lord_of_sign(chart.asc_sign, 7) == "Venus" or v.rasi_house == 7
                 or drishti.aspects_house("Venus", 7, chart))
    if not venus_7th:
        return verdict, False, ()
    return "favourable", True, (("blemishless_venus", "favourable"),)


def _dhana_floor(
    verdict: Verdict, lead: FrameLedger, sig: Signification,
    fired: tuple[FiredYoga, ...],
) -> tuple[Verdict, bool, Metadata]:
    """H11 Dhana-yoga FLOOR (Stage-3, user-signed-off; the salvaged kernel of the
    architecture-proposal review). A verified Dhana yoga is a STRUCTURAL FLOOR for a
    gains/acquisitions matter that a single malefic or a weakening navamsa cannot strip
    (the document's correct instinct, in the engine's clause idiom). Faithful to Raman's
    own gradation:

    * all three pillars strong -> 'favourable' — an unshakeable wealth floor that
      OVERRIDES even the 'afflicted' that clause-2's navamsa guard produced from a lone
      malefic + weakening D9 (e.g. golden h11_12: Dhana exchange, all pillars strong,
      D9 weakens -> Raman favourable);
    * otherwise (a weak pillar) -> lift only an 'afflicted' up to 'mixed' — the weak
      pillar tempers the yoga to 'wealth, but...' (e.g. golden h11_18: Dhana-59, weak
      karaka -> Raman mixed). A favourable/mixed verdict is NEVER demoted.

    Scoped to H11 gains/acquisitions; deferred under the longevity guard. This is the ONE
    layer permitted to override a DECISIVE 'afflicted' (the doctrinal expansion signed off
    on) — every other modulator only nudges a borderline 'mixed'. Metadata records the
    driving Dhana yoga + the action ('favourable' / 'mixed' / 'noted')."""
    if sig.house != 11 or sig.key not in _DHANA_FLOOR_KEYS \
            or "LONGEVITY_GUARD" in lead.flags:
        return verdict, False, ()
    dhana_ids = tuple(y.id for y in fired if y.kind == "dhana")
    if not dhana_ids:
        return verdict, False, ()
    all_strong = (lead.lord_strong is True and lead.karaka_strong is True
                  and lead.bhava_bala_strong is True)
    new: Verdict = verdict
    if all_strong:
        new = "favourable"
    elif verdict == "afflicted":
        new = "mixed"
    action = new if new != verdict else "noted"
    return new, new != verdict, (("dhana_floor", f"{dhana_ids[0]}:{action}"),)


def _powerful_dhana_kendra_floor(
    chart: RamanChart, sig: Signification, verdict: Verdict, lead: FrameLedger,
) -> tuple[Verdict, Metadata]:
    """DECISIVE gains-favourable floor for Raman's "powerful combination of the 2nd, 7th, 9th
    and 11th lords in a kendra" Dhana yoga (HTJAH-II:15273-15289 -- Chart 218: "The Eleventh
    Lord: The Sun occupies a kendra in exaltation joining the 2nd lord Mars and 9th lord
    Mercury ... The powerful combination of the 2nd, 7th, 9th and 11th lords in the 7th house,
    a kendra, has generated a very strong yoga for gains" -> a newspaper magnate).

    Fires only when the 11th lord -- the gains significator itself -- is the yoga's strong
    anchor: Shadbala-strong AND exalted/own AND occupying a kendra, with >= 2 of the OTHER
    {2,7,9,11} lords conjunct it there. That is a genuinely powerful multi-lord wealth yoga whose
    strength Raman reads as decisively favourable even when the generic gains karaka (Jupiter) is
    weak, so it OVERRIDES the clause-2 navamsa-weakens guard that otherwise leaves the
    contradicted matter 'afflicted' (the same override authority granted to _dhana_floor). Never
    demotes: a favourable verdict is returned unchanged; only afflicted/mixed is lifted.

    Scoped to H11 gains/acquisitions; deferred under the longevity guard. The four-clause
    discriminator (strong + exalted/own + kendra + >= 2 conjunct artha-lords) fires on Chart 218
    ALONE across the H11 golden corpus (over-fire scanned).

    bphs-doctrine-reviewer SOUND-WITH-CAVEAT/KEEP (HIGH). Recorded caveats (all conservative --
    they can only UNDER-fire): (1) the own-sign arm is a dignity-generalization not exercised by
    Chart 218's verbatim "in exaltation"; (2) clause-1 quantifies Raman's positional "well placed"
    as Shadbala is_powerful -- a tightening beyond the words; (3) anchoring on the 11th lord
    narrows Raman's stated aggregate cause ("powerful combination of the 2nd, 7th, 9th and 11th
    lords") -- safe for a lift-only floor but misses a non-11th-lord-anchored variant; (4) the
    navamsa override is inferred from the CONFIRMED favourable outcome, not a verbatim Raman D9
    statement."""
    if (sig.house != 11 or sig.key not in _DHANA_FLOOR_KEYS
            or "LONGEVITY_GUARD" in lead.flags or verdict == "favourable"):
        return verdict, ()
    l11 = _lord_of_sign(chart.asc_sign, 11)
    p = chart.planets.get(l11)
    if p is None or p.rasi_house not in (1, 4, 7, 10):            # 11th lord in a kendra
        return verdict, ()
    if _strong(l11, chart) is not True:                          # and Shadbala-strong
        return verdict, ()
    exalted_or_own = ((l11 in r.EXALTATION and p.sign == r.EXALTATION[l11][0])
                      or SIGN_LORDS[p.sign] == l11)               # "in exaltation" / own sign
    if not exalted_or_own:
        return verdict, ()
    others = {_lord_of_sign(chart.asc_sign, h) for h in (2, 7, 9, 11)} - {l11}
    conjunct = sum(1 for o in others
                   if (q := chart.planets.get(o)) is not None and q.rasi_house == p.rasi_house)
    if conjunct < 2:                                             # >= 2 other artha-lords joining
        return verdict, ()
    return "favourable", (("dhana_kendra_floor", "Y.DHANA.KENDRA:favourable"),)


_AYURDAYA_VERDICT: dict[str, Verdict] = {
    "alpa": "afflicted", "madhya": "mixed", "purna": "favourable"}

_MARITAL_BOND_KEYS: frozenset[str] = frozenset({"spouse", "marital_happiness"})

# Significations whose Dasha timing pivots on the maraka set (death of the native or a relative).
_TIMING_MARAKA_KEYS: frozenset[str] = frozenset(
    {"longevity", "death", "coverture", "father", "mother", "spouse"})

# Display caps for the ``active_periods`` line (REPORT_CRITIQUE_2026-08-17 P0). The maraka
# set can absorb every significator's window (one window per graha, strongest role wins), so
# an uncapped maraka-first sort made the ENTIRE activation line read "(maraka)" for the
# relative-death matters (mother/spouse/coverture/father) — five death-labels and zero
# ordinary fructification windows. At most `_TIMING_MARAKA_DISPLAY_CAP` maraka-tagged windows
# are shown; ordinary windows (afflictor/lord/karaka/timer) fill the remaining slots up to
# `_TIMING_DISPLAY_CAP`. DISPLAY-SELECTION ONLY: the computed window set is unchanged, and
# the verdict is untouched (this composer is metadata-only by contract).
_TIMING_DISPLAY_CAP: Final[int] = 5
_TIMING_MARAKA_DISPLAY_CAP: Final[int] = 2


def _event_timing(
    chart: RamanChart, sig: Signification, verdict: Verdict, lead: FrameLedger, ctx: EvalContext,
) -> tuple[Verdict, Metadata]:
    """Outcome-timing overlay (Layer): annotate WHEN a matter's results are active, from the
    Vimshottari Dasha. METADATA-ONLY — the verdict is returned byte-for-byte unchanged (timing
    annotates, it never resolves the natal verdict). Two data:

    * ``death_window`` (H8 longevity/death): the maraka Bhukti periods in the alloted-span region
      (when the lifespan expires under a maraka). Premature/violent deaths strike a strong EARLIER
      maraka the engine does not isolate (documented limit).
    * ``active_periods`` (every matter): the Mahadasha windows of the matter's significators
      (lord, karaka, fired afflictors/relievers, and — for death/relative-death matters — the
      maraka set), most-salient roles first, bounded.

    No-ops on a Track-B chart (no jd_ut)."""
    if getattr(chart, "jd_ut", None) is None:
        return verdict, ()
    md: list[tuple[str, str]] = []
    if sig.house == 8 and sig.key in ("longevity", "death"):
        windows = ctx.get_or_compute("death_window", lambda: vimshottari.death_window(chart))
        if windows:
            md.append(("death_window", "; ".join(w.label() for w in windows[:3])))
    # General "Time of Fructification" timer-set for THIS house (+ its aux event-houses, e.g.
    # gains reads 2nd+11th) -> the planets that bring the matter's results in their Dasha.
    timers: set[str] = set(vimshottari.timer_set(chart, sig.house))
    for aux in vimshottari._EVENT_AUX_HOUSES.get(sig.house, ()):
        timers |= vimshottari.timer_set(chart, aux)
    grahas: dict[str, frozenset[str]] = {
        "timer": frozenset(timers),
        "lord": frozenset({lead.lord}),
        "karaka": frozenset({sig.primary_karaka}),
        "afflictor": frozenset(
            s for fr in lead.fired_malefic if (s := _rule_subject(fr.rule)) is not None),
    }
    if sig.key in _TIMING_MARAKA_KEYS:
        grahas["maraka"] = ctx.get_or_compute(
            "maraka_lords", lambda: vimshottari.maraka_set(chart).all())
    windows = vimshottari.significator_dasha_windows(chart, grahas)
    if windows:
        # Most event-salient roles first (maraka/afflictor/lord/karaka), then generic timers.
        ordered = sorted(windows, key=lambda w: (
            {"maraka": 0, "afflictor": 1, "lord": 2, "karaka": 3}.get(w.role, 4), w.start_jd))
        # Cap the maraka-tagged windows so ordinary fructification windows stay visible
        # (see _TIMING_MARAKA_DISPLAY_CAP above — selection of what is DISPLAYED only).
        shown: list[vimshottari.EventWindow] = []
        n_maraka = 0
        for w in ordered:
            if w.role == "maraka":
                if n_maraka >= _TIMING_MARAKA_DISPLAY_CAP:
                    continue
                n_maraka += 1
            shown.append(w)
            if len(shown) >= _TIMING_DISPLAY_CAP:
                break
        md.append(("active_periods", "; ".join(w.label() for w in shown)))
    return verdict, tuple(md)
# The CRUEL malefics Raman names in the marital-bond afflictions (Mars/Saturn/Rahu/Ketu) — the
# Sun is deliberately EXCLUDED: it is never the load-bearing 8th-from-Moon marital affliction in
# Raman's worked charts, and including it is the likeliest out-of-sample false-demote
# (bphs-doctrine-reviewer). All four occupants of the 8th-from-Moon in both targets are cruel.
_CRUEL_MALEFICS: frozenset[str] = frozenset({"Mars", "Saturn", "Rahu", "Ketu"})


def _marital_bond_gate(
    chart: RamanChart, sig: Signification, verdict: Verdict, blem_lifted: bool = False,
) -> tuple[Verdict, Metadata]:
    """H7 marital-bond demote: a heavily-afflicted 8th house FROM THE MOON (the Chandra-Lagna
    8th — the marital bond / mangalya from the emotional self) with >= 2 CRUEL malefics
    (Mars/Saturn/Rahu/Ketu) softens an otherwise-FAVOURABLE marriage to MIXED (a troubled /
    unconventional but realized marriage). Demote-only: it never touches a mixed/afflicted
    verdict, and never reaches afflicted.

    Raman reads the 8th-from-Moon affliction as the marriage's flaw even when the 7th lord is clean:
    Chart 28/h7_16 'the 8th house from Chandra Lagna is heavily afflicted by Mars, Rahu, Ketu and
    Saturn ... married a divorcee' (HTJAH-II:2664); Chart 32/h7_19 'all malefics in the 8th [from
    the Moon] ... married a Christian' (HTJAH-II:2877). The >= 2 cruel-malefic gate spares every
    favourable H7 golden (each has <= 1) and is a no-op on the already-mixed twins. Scope is
    key-based (spouse/marital_happiness) so it correctly excludes coverture (the widowhood/death
    matter) and partnership (business, which only carries the 'spouse' rule_tag).
    bphs-doctrine-reviewer SOUND-WITH-CAVEAT (the >= 2 vs Raman's 'heavily' = 3-4 is a logged
    calibration margin)."""
    if sig.key not in _MARITAL_BOND_KEYS or verdict != "favourable":
        return verdict, ()
    if blem_lifted:         # anti-double-move: don't re-demote a verdict the blemishless-Venus floor just lifted
        return verdict, ()
    moon = chart.planets.get("Moon")
    if moon is None:
        return verdict, ()
    n = sum(1 for nm, p in chart.planets.items()
            if nm in _CRUEL_MALEFICS and ((p.rasi_house - moon.rasi_house) % 12) + 1 == 8)
    if n >= 2:
        return "mixed", (("marital_bond", "8th_from_moon_afflicted"),)
    return verdict, ()


def _malefic_occupancy_gate(
    chart: RamanChart, sig: Signification, verdict: Verdict, lead: FrameLedger,
) -> tuple[Verdict, Metadata]:
    """Two-malefic-occupancy demote: a bhava TENANTED by >= 2 cruel malefics (Mars/Saturn/Rahu/
    Ketu) whose LORD does not compensate (the lead lord is not Shadbala-strong) is afflicted enough
    to qualify an otherwise-FAVOURABLE verdict down to MIXED. Demote-only: it never touches a
    mixed/afflicted/insufficient verdict and never reaches afflicted.

    Raman's comparative weighing — multiple malefics tenanting a bhava afflict it UNLESS a strong
    lord carries the house: Notable Horoscopes Chart 100 (Tagore) 'the affliction of the 4th house
    by the presence of Mars and Ketu denotes that his education was of a desultory character'
    (NH:5890) -> mixed (the unconventional schooling). The lord-not-strong clause is the
    compensation exemption: it spares the favourable twin (NH chart_42 H2 — two malefics but a
    STRONG lord) and over-fires 0/109 confirmed-favourable verdicts (with-gate vs without-gate diff
    changes 0 confirmed verdicts). The Sun is deliberately EXCLUDED from `_CRUEL_MALEFICS` (a
    calibration choice mirroring `_marital_bond_gate`, not a claim the Sun never afflicts by
    occupancy). bphs-doctrine-reviewer: SOUND-WITH-CAVEAT (KEEP)."""
    if verdict != "favourable" or lead.lord_strong is True:
        return verdict, ()
    occ = sorted(nm for nm, p in chart.planets.items()
                 if nm in _CRUEL_MALEFICS and p.rasi_house == sig.house)
    if len(occ) >= 2:
        return "mixed", (("malefic_occupancy", f"{'+'.join(occ)}@H{sig.house}:weak_lord"),)
    return verdict, ()


_MARGINAL_BAND: Final[float] = 0.2  # GBB-1:38-60 borderline band (rupas) below MIN_REQUIRED


def _marginal_karaka_gate(
    chart: RamanChart, sig: Signification, verdict: Verdict, lead: FrameLedger,
    *, bond_demoted: bool = False,
) -> tuple[Verdict, Metadata]:
    """GBB B2 marginal-strength band. The MIN_REQUIRED Rupa bars (GBB-8:303-312) are Raman's
    full-strength REFERENCE values, not pass/fail gates — strength is a continuum (GBB-1:38-60,
    'no effect at the sandhi ... full effect at the Bhavamadhya', the rule-of-three principle).
    The engine's `is_powerful` is a hard `>=` cutoff, so a karaka just under its bar (Venus 5.37
    vs 5.5) reads 'decisively weak' and, with maraka pressure, forces an AFFLICTED marriage that
    Raman reads favourable (chart_03/08). When a MARRIAGE verdict is afflicted PURELY because the
    karaka is MARGINALLY weak (within ~0.2 rupa of its bar) AND a STRONG lord carries the house AND
    NO real malefic fired (the affliction is the maraka/cliff artefact, not a genuine evil), this
    RE-DECIDES treating the marginal karaka as not-decisively-weak — it does not force a verdict;
    it adopts whatever `_decide` yields (for chart_08 that is favourable via the both-pillars-strong
    clause, matching Raman's confirmed reading). This is the transpose of the already-approved
    KARAKA-SALVAGE (a strong karaka carries a weak-lord matter, HTJAH-II:221); here a strong lord
    carries a marginal-karaka marriage. Scoped to the marriage significations (Venus karaka) where
    the cliff was identified; 0 over-fire on the confirmed set (the general all-house form clips a
    correct chart_54 H10 afflicted, so it is held to marriage). bphs-doctrine-reviewer:
    SOUND-WITH-CAVEAT (KEEP/FLAG) — calibration rests on n=1 confirmed golden + a hand-tuned 0.2
    band + a 2-level lift (vs KARAKA-SALVAGE's conservative 1-level); re-examine if a second
    marriage golden ever enters the band."""
    # B3 companion (2026-08-17): with the non-death-marital maraka guard in _decide,
    # the maraka/cliff artefact this gate was built to lift no longer FORMS as
    # 'afflicted' — the same chart (e.g. chart_08: strong lord, marginal Venus, no
    # malefic) now falls through to 'mixed' (on an evidence-empty ledger the artefact
    # instead surfaces as insufficient-evidence, which this gate deliberately does not
    # touch). The GBB-1:38-60 continuum principle is unchanged, so the gate's trigger
    # widens from {afflicted} to {afflicted, mixed} under the SAME strict conditions;
    # the re-decide semantics are untouched.
    # ANTI-DOUBLE-MOVE (doctrine-review HIGH, 2026-08-17): a 'mixed' produced by the
    # _marital_bond_gate DEMOTE (>=2 cruel malefics 8th-from-Moon, HTJAH-II:2664/2877)
    # is Raman's own troubled-marriage reading, not the marginal-karaka cliff — the
    # widened trigger must never re-lift it (mirror of the floor's blem_lifted guard).
    if verdict not in ("afflicted", "mixed") or sig.key not in _MARITAL_BOND_KEYS:
        return verdict, ()
    if verdict == "mixed" and bond_demoted:
        return verdict, ()
    if lead.lord_strong is not True or lead.fired_malefic or lead.karaka_strong is not False:
        return verdict, ()
    p = chart.planets.get(lead.karaka)
    req = shadbala_total.MIN_REQUIRED.get(lead.karaka)
    if p is None or p.shadbala_rupas is None or req is None:
        return verdict, ()
    rupas = p.shadbala_rupas.total / 60.0
    if not (req - _MARGINAL_BAND <= rupas < req):
        return verdict, ()
    softened, _ = _decide(dataclasses.replace(lead, karaka_strong=True))
    if softened != verdict:
        return softened, (("marginal_karaka", f"{lead.karaka} {rupas:.2f}<{req}: not decisively weak"),)
    return verdict, ()


_NATURAL_MALEFIC_YK: frozenset[str] = frozenset({"Mars", "Saturn"})


def _yogakaraka_lagna_gate(
    chart: RamanChart, sig: Signification, verdict: Verdict,
) -> tuple[Verdict, Metadata]:
    """Theme 3 — functional-yogakaraka non-affliction. A natural malefic (Mars/Saturn) that is the
    chart's FUNCTIONAL YOGAKARAKA occupying the LAGNA is a Raja-yoga that FORTIFIES the self (the
    'man of action' / dynamic personality), not an affliction. The engine fires the yogakaraka's
    planet-in-Lagna as a malefic (H1.P.Mars + H1.C.28 functional-malefic-in-Lagna), over-afflicting
    a Lagna Raman reads favourable (NH chart_57, chart_69 — both Cancer Lagna, where Mars rules the
    5th [trikona] and 10th [kendra] and so is the yogakaraka, posited in the Lagna). When an
    AFFLICTED self-verdict has a natural-malefic yogakaraka in the Lagna, lift it to favourable.
    Scoped to the LAGNA self-matter (the general any-house form clips 2 correct confirmed-afflicted
    verdicts); 0 over-fire on the confirmed set.

    COMPARATIVE-WEIGHING GUARD (bphs-doctrine-reviewer FLAG): the yogakaraka's Raja-yoga
    fortification does NOT erase the affliction of OTHER malefics tenanting the Lagna — if >= 2
    NON-yogakaraka natural malefics also occupy the Lagna, the self is not cleanly favourable
    (mirrors `_malefic_occupancy_gate` / NH:5890 'two malefics occupying -> at least mixed'). This
    guard holds the gate to the clean anchor NH chart_69 (Mars-YK + Ketu — Raman: 'Cancer Lagna
    occupied by Mars and Ketu confers imagination', favourable) and excludes NH chart_57 (Mars-YK +
    Saturn + Rahu — three malefics, and Raman credits its favourable self to the Moon-in-10th, a
    different mechanism), which stays DRAFT. bphs-doctrine-reviewer: SOUND-WITH-CAVEAT (KEEP/FLAG)."""
    if verdict != "afflicted" or sig.house != 1:
        return verdict, ()
    yk = sorted(n for n in _NATURAL_MALEFIC_YK
                if (p := chart.planets.get(n)) is not None and p.rasi_house == 1
                and is_yogakaraka(n, chart.asc_sign))
    if not yk:
        return verdict, ()
    other_malefics = sum(1 for n in NATURAL_MALEFICS if n not in yk
                         and (p := chart.planets.get(n)) is not None and p.rasi_house == 1)
    if other_malefics >= 2:
        return verdict, ()
    return "favourable", (("yogakaraka_lagna", f"{'+'.join(yk)}@Lagna:raja-yoga"),)


def _longevity_span(
    chart: RamanChart, sig: Signification, verdict: Verdict, ctx: EvalContext,
) -> tuple[Verdict, Metadata]:
    """H8 longevity SPAN — the mathematical ayurdaya (Pindayu/Amsayu, HTJAH-II:3947-4441).

    Replaces the placement-evidence longevity guess with Raman's lifespan computation:
    the span maps to a class -> verdict (alpa/short -> afflicted; madhya/medium -> mixed;
    purna/full -> favourable), and the computed span is surfaced as metadata. The longevity
    SPAN (capacity for a full life) is distinct from the death MANNER (the `death` sig) -- a
    purna-span native can still die violently young (Lincoln), so longevity=favourable +
    death=afflicted is the correct dual reading.

    Falls back to the incoming verdict when the chart lacks a graha (Track-B book charts),
    since the ayurdaya needs all seven.
    """
    if sig.key != "longevity":
        return verdict, ()
    if any(p not in chart.planets for p in ayurdaya.SEVEN):
        return verdict, ()
    res = ctx.get_or_compute("ayurdaya", lambda: ayurdaya.longevity(chart))
    y, m, d = res.ymd()
    md: Metadata = (("ayurdaya", f"{res.method}:{res.longevity_class}:{y}y{m}m{d}d"),)
    return _AYURDAYA_VERDICT[res.longevity_class], md


def _putrakaraka_malefic_afflicted(chart: RamanChart) -> bool:
    """The PutraKaraka Jupiter conjoined or aspected (whole-sign drishti) by >= 1 natural
    malefic — Raman's 'baneful PutraKaraka' (HTJAH-I:5701-5709: 'Jupiter ... his association
    with Rahu and the combined aspects of Mars and Saturn ... rendered him highly malefic ...
    capable of producing the most baneful effects')."""
    jup = chart.planets.get("Jupiter")
    if jup is None:
        return False
    for m in NATURAL_MALEFICS:
        if m == "Jupiter" or m not in chart.planets:
            continue
        if chart.planets[m].rasi_house == jup.rasi_house:   # conjunction
            return True
        if drishti.aspects_planet(m, "Jupiter", chart):     # whole-sign drishti
            return True
    return False


def _fertility_gate(
    chart: RamanChart, sig: Signification, verdict: Verdict,
    lead: FrameLedger, ctx: EvalContext,
) -> tuple[Verdict, Metadata, FrameLedger]:
    """H5 Beeja/Kshetra GATE (HTJAH-I:5517-5527) — the mandatory fertility pre-pass
    for children/progeny matters.

    DOCTRINE (Stage-3 calibration, user-signed-off "O1"): Raman weighs a SINGLE weak
    sphuta (one parent's contribution barren -> reduced but possible), but BOTH sphutas
    weak is the strongest classical denial signal — both the male seed (Beeja) AND the
    female field (Kshetra) are barren, which Raman reads as genuine progeny DENIAL. So:

    * BOTH sphutas weak -> ``afflicted`` (decisive denial), FERTILITY_GATE flag set. This
      is NOT an "auto-deny from nothing": it fires only when the two fertility sphutas
      BOTH fail their odd/even-sign test. The goldens prove it — h5_08 (no malefic, no
      benefic, neutral navamsa) and h5_11 (3 benefics, 0 malefics) are both read
      ``afflicted`` by Raman purely on barren sphutas. The gate runs AFTER _decide /
      yoga, so it OVERRIDES a favourable/mixed children verdict the placement evidence
      produced — barren sphutas trump a strong 5th lord (the children-matter mirror of
      the dusthana rule: significator strength does not beget a child when both seeds
      are barren).
    * Strong sphutas (and the unprinted one-weak partial case) ride along as metadata
      only. None-safe on sparse charts (a missing sphuta planet skips the gate entirely).

    Metadata values are prefixed ``numeric_`` ('numeric_strong' / 'numeric_partial')
    because only the NUMERIC odd/even sphuta test is evaluated here; the
    HTJAH-I:5524-5527 aspect/Rahu-association clauses are deferred to the H5
    judge and NOT checked by this gate — the values deliberately do not claim a
    full fertility assessment.
    """
    if sig.house != 5 or not (
            sig.key in _FERTILITY_KEYS or "progeny" in sig.rule_tags):
        return verdict, (), lead
    bk = ctx.get_or_compute("beeja_kshetra", lambda: beeja_kshetra(chart))
    if bk is None:
        return verdict, (), lead
    if not bk.beeja_strong and not bk.kshetra_strong:
        lead = dataclasses.replace(
            lead, flags=tuple(dict.fromkeys(lead.flags + ("FERTILITY_GATE",))))
        # Both seed and field barren -> denial (decisive; overrides any favourable/mixed
        # the placement evidence produced). A single weak sphuta is handled by the
        # one-weak 'numeric_partial' branch below (weighed, not denied).
        verdict = "afflicted"
        return verdict, (("beeja_kshetra", "weak"),), lead
    if bk.beeja_strong and bk.kshetra_strong:
        return verdict, (("beeja_kshetra", "numeric_strong"),), lead
    # Exactly one sphuta weak: a single barren seed/field. Raman never denies on a lone weak
    # sphuta (HTJAH-I:5507 "children may be born late"), but DENIES it when an independent
    # house/karaka affliction corroborates — his own h5_05 / h5_12 reasoning:
    #   Arm A (h5_12 "5th house spoilt"):    >= 2 fired malefic child-rules.
    #   Arm B (h5_05 "PutraKaraka baneful"): the lead karaka pillar is weak AND the PutraKaraka
    #     Jupiter is itself afflicted by >= 1 natural malefic (conjunction / whole-sign drishti).
    # The AND in Arm B is the faithful discriminator vs the FAVOURABLE twin h5_16, whose Jupiter
    # is ALSO malefic-afflicted but has neecha-bhanga (so karaka_strong is True) and is read as
    # fertile (Raman's count method -> 13 children). h5_10 (engine reads all pillars strong, 0
    # malefic rules) stays a documented limit — a Shadbala-vs-Raman strength disagreement, not a
    # gate gap. bphs-doctrine-reviewer SOUND. The gate is decisive (overrides the placement
    # verdict), like the both-weak arm.
    n_malefic = sum(1 for fr in lead.fired_malefic if fr.rule.signification == sig.key)
    arm_a = n_malefic >= 2
    arm_b = (lead.karaka_strong is False) and _putrakaraka_malefic_afflicted(chart)
    if arm_a or arm_b:
        lead = dataclasses.replace(
            lead, flags=tuple(dict.fromkeys(lead.flags + ("FERTILITY_GATE",))))
        verdict = "afflicted"
        return verdict, (("beeja_kshetra", "one_weak_denied"),), lead
    return verdict, (("beeja_kshetra", "numeric_partial"),), lead


def _saptamsa_gate(
    chart: RamanChart, sig: Signification, verdict: Verdict,
    lead: FrameLedger, ctx: EvalContext,
) -> tuple[Verdict, Metadata]:
    """D-7 (Sapthamsa) CHILDREN layer — the child-varga's confirm/weaken testimony modulates
    a BORDERLINE children verdict; the exact parallel of the D9 navamsa modulation.

    Scope: the H5 children/progeny matter ONLY (the fertility-gate scope). The Sapthamsa is
    Raman's child-specific varga ("Saptamsa for children", HPA-11:198; rasi = promise, the
    varga = fruit, HtJaH:979), so for progeny its testimony is at least as pertinent as the
    general navamsa. Discipline is identical to ``_navamsa_modulate``: only a borderline
    'mixed' moves, one step (confirms -> favourable, weakens -> afflicted); a decisive
    favourable/afflicted NEVER shifts, so the golden ratchet is invariant except where a
    children verdict was genuinely borderline. The confirm/weaken read uses the same
    reviewer-validated four-principle varga model the per-varga judge documents
    (``judges/varga_judge.py``).

    Order: runs AFTER the yoga/floor modulators and BEFORE the decisive Beeja/Kshetra
    ``_fertility_gate``. The Putra-sphuta test (HTJAH-I:5517-5527) is Raman's SPECIFIC,
    decisive fertility signal and outranks the casual D-7 in BOTH directions:
      * a both-barren-sphuta DENIAL overrides a confirming D-7 downstream (barren seed begets
        no child, however promising the amsa) — enforced by ``_fertility_gate`` running last;
      * a both-strong-sphuta AFFIRMATION must not be overridden by a weakening D-7 — but the
        fertility gate only denies, it never lifts, so that guard is enforced HERE: the
        ``weakens -> afflicted`` push is suppressed when both sphutas are strong.

    Always surfaces ``("saptamsa", status)`` as report metadata (the ``("beeja_kshetra", …)``
    style), except when the D-7 is unresolvable (Track-B / sparse) -> no metadata, no effect.
    """
    if sig.house != 5 or not (
            sig.key in _FERTILITY_KEYS or "progeny" in sig.rule_tags):
        return verdict, ()
    status = ctx.get_or_compute(
        "saptamsa_status_h5",
        lambda: _saptamsa_status(
            lead.lord, lead.karaka, chart,
            _d7_hollow_redeemed_occupants(chart, lead.lord, lead.karaka),
            include_seats=True))
    if status == "unknown":
        return verdict, ()
    if verdict == "mixed" and status == "confirms":
        verdict = "favourable"
    elif verdict == "mixed" and status == "weakens":
        # The decisive Putra-sphuta test outranks the casual D-7: when BOTH seed (Beeja) and
        # field (Kshetra) are strong — Raman's positive fertility signal — the child-varga's
        # weakening must not deny progeny. Otherwise the D-7 tempers the borderline downward.
        bk = ctx.get_or_compute("beeja_kshetra", lambda: beeja_kshetra(chart))
        if not (bk is not None and bk.beeja_strong and bk.kshetra_strong):
            verdict = "afflicted"
    return verdict, (("saptamsa", status),)


def _occupants_ordered(chart: RamanChart, house: int) -> tuple[str, ...]:
    """Occupants of whole-sign `house` in canonical graha order (deterministic)."""
    return tuple(p for p in _PLANET_ORDER
                 if p in chart.planets and chart.planets[p].rasi_house == house)


def _drekkana22_cell(asc_lon: float) -> tuple[str, int]:
    """(sign name, decanate index 1-3) of the 22nd drekkana from the Lagna drekkana.

    Same pinned +22 offset as :func:`app.raman_saab.primitives.maraka._drekkana22_lord`
    (HTJAH-II:3692-3695; worked example: Lagna 27deg Aquarius -> 1st decan of Libra) —
    that primitive returns only the LORD, while the cause-of-death grid needs the
    (sign, decanate) cell, so the cycle index is re-derived here from the same math.
    """
    sign_idx = int(asc_lon // 30)
    decan = int((asc_lon % 30) // 10)
    g = (sign_idx * 3 + decan + 22) % 36
    return _SIGN_NAMES[g // 3], (g % 3) + 1


def _lookup_metadata(chart: RamanChart, sig: Signification,
                     lead: FrameLedger) -> Metadata:
    """Doctrine lookup grids surfaced as metadata — None-safe, NEVER verdict-changing.

    * H8 longevity/death: 22nd-drekkana decanate cause-of-death fallback
      (HTJAH-II:3727-3845); skipped on Track-B (no maraka_points pre-pass).
    * H11 gains: per-occupant source-of-gains channels (HTJAH-II:14373-14386);
      nodes are unprinted and skipped.
    * H12: Bhavartha Ratnakara karaka-in-12th inversion for occupants of the 12th
      (HTJAH-II:16543-16569; Mercury has no printed bhava -> skipped), plus the
      Bandhana confinement mode (HTJAH-II:16429-16436) when malefic evidence fired
      on the incarceration matter (Leo/Aquarius lagnas are unprinted -> skipped).
    * H6 disease: organ/tridosha of natural-malefic (afflicting) occupants of the
      6th (HTJAH-I:6437-6458); unprinted planets return None and are skipped.
    """
    out: list[tuple[str, str]] = []
    if sig.house == 8 and sig.key in _H8_DEATH_KEYS and chart.maraka_points is not None:
        sign_name, idx = _drekkana22_cell(chart.asc_lon % 360.0)
        rec = lookups.cause_of_death_fallback(sign_name, idx)
        out.append(("drekkana22_lord", chart.maraka_points.drekkana22_lord))
        out.append(("decanate_cause", f"{sign_name} {idx}: {rec.cause}"))
    elif sig.house == 11 and sig.key in _H11_GAINS_KEYS:
        for p in _occupants_ordered(chart, 11):
            if p in lookups.PLANET_IN_11TH_GAINS:
                out.append(("source_of_gains", f"{p}: {lookups.source_of_gains(p)}"))
    elif sig.house == 12:
        for p in _occupants_ordered(chart, 12):
            rec12 = lookups.KARAKA_IN_12_INVERSIONS.get(p)
            if rec12 is not None and rec12.result is not None:
                out.append(("karaka_in_12", f"{p}: {rec12.result}"))
        if sig.key == "incarceration" and lead.fired_malefic:
            mode = lookups.confinement_mode(_SIGN_NAMES[chart.asc_sign - 1])
            if mode is not None:
                out.append(("confinement_mode", mode))
    elif sig.house == 6 and sig.key in _H6_DISEASE_KEYS:
        for p in _occupants_ordered(chart, 6):
            if p not in NATURAL_MALEFICS:
                continue
            organ = lookups.organ_of(p)
            if organ is not None:
                out.append(("organ_of", f"{p}: {organ}"))
            dosha = lookups.tridosha_of(p)
            if dosha is not None:
                out.append(("tridosha_of", f"{p}: {dosha}"))
    return tuple(out)


# ---------------------------------------------------------------------------
# Matter-specific divisional charts (Shodasavarga): children -> D7, career -> D10,
# parents -> D12, siblings -> D3, disease -> D30.
#
# Provenance corrected 2026-08-19. This block used to assert, uncited, that "Raman
# cross-checks each matter in its OWN varga". He does not, as a rule. What he does:
# names the shodasavarga scheme and DEFERS the per-matter assignment to Parashara
# ("Dwadasamsa for parents, Saptamsa for children, etc.", HPA-11:195-201) — two of
# these five by name, the rest by pointer. His own working division throughout HTJAH
# is the NAVAMSA (marriage HTJAH-II:402-413, children via the navamsa lagna
# HTJAH-II:774-776, profession via the navamsa of the 10th lord HTJAH-II:9729-9811).
# The full policy, per division, is `doctrine/varga_domains.py`.
#
# That thinner footing is exactly why this overlay is verdict-INVARIANT: it surfaces
# the matter-varga testimony as metadata and lets Raman's own D1 method decide
# (PREC-11 — the D1 core decides, the divisional corroborates).
# ---------------------------------------------------------------------------

_MATTER_VARGA: Final[dict[int, tuple[int, str]]] = {
    3: (3, "D3"),     # siblings / courage  — drekkana
    5: (7, "D7"),     # children            — saptamsa
    4: (12, "D12"),   # mother / home       — dwadasamsa
    6: (30, "D30"),   # disease / evils     — trimsamsa
    9: (12, "D12"),   # father / fortune    — dwadasamsa
    10: (10, "D10"),  # career              — dasamsa
}


def _varga_dignity_at(planet: str, chart: RamanChart, n: int) -> str:
    """Sign-only dignity (exalt/debil/own/neutral) of `planet` in the D-`n` divisional chart."""
    p = chart.planets.get(planet)
    if p is None or planet in ("Rahu", "Ketu"):
        return "neutral"
    vs = varga.varga_sign(p.lon, n)
    if planet in r.EXALTATION and vs == r.EXALTATION[planet][0]:
        return "exalt"
    if planet in r.DEBILITATION and vs == r.DEBILITATION[planet][0]:
        return "debil"
    if SIGN_LORDS.get(vs) == planet:
        return "own"
    return "neutral"


def _matter_varga_overlay(chart: RamanChart, sig: Signification, lord: str, karaka: str) -> Metadata:
    """ADDITIVE metadata: report the bhava lord + karaka dignity in the MATTER-specific divisional
    chart (the rasi declares the promise; the matter-varga shows the matter-specific fruit, e.g. D7
    for progeny, D10 for profession). Verdict-INVARIANT — feeding the varga into the decisive verdict
    carries the same distortion risk as the D9 netting (B2), so this only surfaces the testimony."""
    mv = _MATTER_VARGA.get(sig.house)
    if mv is None:
        return ()
    n, name = mv
    ld = _varga_dignity_at(lord, chart, n)
    kd = _varga_dignity_at(karaka, chart, n)
    if ld == "neutral" and kd == "neutral":
        return ()                                   # no varga testimony -> stay silent (not noise)
    return ((f"varga_{name}", f"{lord}:{ld}|{karaka}:{kd}"),)


def _ashtakavarga_overlay(chart: RamanChart, sig: Signification) -> Metadata:
    """ADDITIVE: the Sarvashtakavarga bindus in the bhava — Raman's house-strength backbone (the
    12-sign total is always 337, average ~28; a bhava with more bindus is better supported, fewer
    is weaker). Verdict-invariant; only emits on a full chart (all seven planets present)."""
    if not all(p in chart.planets for p in ashtakavarga.PLANETS):
        return ()
    n = ashtakavarga.bindus_in_house(chart, sig.house)
    band = "strong" if n >= 30 else "weak" if n <= 25 else "average"
    return (("sav_bindus", f"{n}:{band}"),)


# ---------------------------------------------------------------------------
# Per-signification + per-house judging
# ---------------------------------------------------------------------------

def judge_signification(chart: RamanChart, house: int, sig: Signification,
                        ctx: Optional[EvalContext] = None) -> SignificationVerdict:
    """Judge one sub-matter across its frames; lead = stronger of LAGNA/MOON by lord Shadbala.

    After ``_decide`` collapses the lead ledger (navamsa modulation included), the
    chart-level layers run in the documented order: yoga modifier (consideration
    #4) -> H11 Dhana-yoga floor -> H5 fertility gate -> lookup-grid metadata. `ctx`
    shares the per-chart memo store (fired yogas are detected ONCE per chart).
    """
    ctx = ctx if ctx is not None else EvalContext(chart)
    lagna = _build_frame_ledger(chart, sig, "lagna", ctx)
    moon = _build_frame_ledger(chart, sig, "moon", ctx)
    others: list[FrameLedger] = []

    # Lead selection by lord total Shadbala; Track-B -> LAGNA.
    lagna_sb = _total_shadbala(lagna.lord, chart)
    moon_sb = _total_shadbala(moon.lord, chart)
    if lagna_sb is None or moon_sb is None:
        lead = lagna
        others.append(moon)
    elif moon_sb > lagna_sb:
        lead = moon
        others.append(lagna)
    else:
        lead = lagna
        others.append(moon)

    if sig.alternate_frame_core and sig.alternate_frame_core in chart.planets:
        others.append(_build_frame_ledger(chart, sig, "karaka", ctx))

    verdict, shifted = _decide(lead)
    verdict, dec_shifted = _decisive_affliction(verdict, lead, sig)
    verdict, cat_md = _catastrophic_severity_gate(sig, verdict, lead)
    fired_yogas: tuple[FiredYoga, ...] = ctx.get_or_compute(
        "fired_yogas", lambda: detect_yogas(chart))
    verdict, yoga_shifted, yoga_md = _yoga_modulate(verdict, lead, sig, fired_yogas)
    verdict, dhana_shifted, dhana_md = _dhana_floor(verdict, lead, sig, fired_yogas)
    verdict, blem_shifted, blem_md = _blemishless_venus_floor(chart, sig, verdict, lead)
    _v_before_gates = verdict                       # capture for the late-shift (gates/longevity/timing) flag
    verdict, saptamsa_md = _saptamsa_gate(chart, sig, verdict, lead, ctx)
    verdict, gate_md, lead = _fertility_gate(chart, sig, verdict, lead, ctx)
    verdict, longev_md = _longevity_span(chart, sig, verdict, ctx)
    verdict, bond_md = _marital_bond_gate(chart, sig, verdict, blem_lifted=blem_shifted)
    verdict, occ_md = _malefic_occupancy_gate(chart, sig, verdict, lead)
    verdict, marg_md = _marginal_karaka_gate(chart, sig, verdict, lead,
                                             bond_demoted=bool(bond_md))
    verdict, yk_md = _yogakaraka_lagna_gate(chart, sig, verdict)
    verdict, dhana_kendra_md = _powerful_dhana_kendra_floor(chart, sig, verdict, lead)
    verdict, timing_md = _event_timing(chart, sig, verdict, lead, ctx)
    late_shifted = verdict != _v_before_gates       # a gate/longevity/timing moved the verdict
    varga_md = _matter_varga_overlay(chart, sig, lead.lord, lead.karaka)
    av_md = _ashtakavarga_overlay(chart, sig)
    lookup_md = _lookup_metadata(chart, sig, lead)
    metadata: Metadata = tuple(dict.fromkeys(
        cat_md + yoga_md + dhana_md + dhana_kendra_md + blem_md + saptamsa_md + gate_md
        + longev_md + bond_md + occ_md + marg_md + yk_md + varga_md + av_md + timing_md
        + lookup_md))
    shifted_any = (shifted or dec_shifted or bool(cat_md) or yoga_shifted or dhana_shifted
                   or blem_shifted or late_shifted)
    # Layer-A avastha deepening: the lead frame's deliverers (lord + karaka) in a net-weak
    # avastha demote the degree one step (intensity only; the verdict is untouched). Avasthas
    # are computed once per chart and cached on ctx.
    avasthas = ctx.get_or_compute("avasthas", lambda: _safe_avasthas(chart))
    av_adjust = _avastha_combined(avasthas, lead.lord, lead.karaka)
    return SignificationVerdict(
        house=house, signification=sig.key, verdict=verdict, karaka=sig.primary_karaka,
        lead_frame=lead.frame, ledger=lead, alt_ledgers=tuple(others),
        borderline_shifted=shifted_any,
        degree=_compute_degree(verdict, lead, shifted_any, av_adjust), metadata=metadata)


def _default_sig(house: int) -> Signification:
    """Fallback signification for a house with no encoded sub-matters: the BHAVA_KARAKA."""
    return Signification(
        key="general", house=house, primary_karaka=BHAVA_KARAKA.get(house, "Sun"),
        rule_tags=(), source=Citation("HTJAH-I", 983))


_ROLLUP_ORDER: dict[Verdict, int] = {
    # insufficient-evidence is ABSENCE of evidence, not a worse outcome than favourable: it is the
    # MOST ignorable, so a decided sub-matter always outranks an un-ruled one.
    "afflicted": 0, "mixed": 1, "favourable": 2, "insufficient-evidence": 3,
}


def _rollup(verdicts: tuple[Verdict, ...]) -> Verdict:
    """Deterministic house rollup precedence:

    * if BOTH a 'mixed' and a 'favourable' are present -> 'mixed' (a contradicted house
      cannot read as cleanly favourable);
    * otherwise the worst DECIDED verdict present, ordered afflicted > mixed > favourable;
      'insufficient-evidence' only wins when no sub-matter was decided (it never masks a real verdict).
    """
    if not verdicts:
        return "insufficient-evidence"
    present = set(verdicts)
    if "mixed" in present and "favourable" in present:
        return "mixed"
    return min(verdicts, key=lambda v: _ROLLUP_ORDER[v])


def judge_house(chart: RamanChart, house: int) -> HouseProforma:
    """All significations of `house` judged, plus the rolled-up house verdict.

    One EvalContext is shared across the house's significations so per-chart
    computations (fired yogas, parivartana pairs, sphutas) run at most once.
    """
    ctx = EvalContext(chart)
    sigs = significations_of(house) or (_default_sig(house),)
    svs = tuple(judge_signification(chart, house, s, ctx) for s in sigs)
    rollup = _rollup(tuple(sv.verdict for sv in svs))
    lord = _lord_of_sign(chart.asc_sign, house)
    by_key: dict[str, tuple[str, str]] = {}         # house-level: de-dup BY KEY, lead sig's value wins
    for sv in svs:
        for k, v in sv.metadata:
            by_key.setdefault(k, (k, v))
    metadata: Metadata = tuple(by_key.values())
    return HouseProforma(house=house, lord=lord, significations=svs,
                         rollup=rollup, metadata=metadata)


def judge_all_houses(chart: RamanChart) -> list[HouseProforma]:
    return [judge_house(chart, h) for h in range(1, 13)]
