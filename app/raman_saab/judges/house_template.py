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
from dataclasses import dataclass, field
from typing import Final, Literal, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart import varga
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine import lookups
from app.raman_saab.doctrine.conditions import EvalContext
from app.raman_saab.doctrine.karakas import BHAVA_KARAKA
from app.raman_saab.doctrine.significations import Signification, significations_of
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.doctrine.yogas import FiredYoga, detect_yogas
from app.raman_saab.judges import rule_firing as rf
from app.raman_saab.judges.house_judge import HouseVerdict
from app.raman_saab.primitives import relationships as r
from app.raman_saab.primitives.bhangas import neecha_bhanga, parivartana
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import NATURAL_MALEFICS
from app.raman_saab.primitives.shadbala import bhava_bala as bhava_bala_mod
from app.raman_saab.primitives.shadbala import total as shadbala_total
from app.raman_saab.primitives.sphutas import beeja_kshetra

Verdict = Literal["favourable", "mixed", "afflicted", "insufficient-evidence"]
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
})

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
    "H7.C.82",  # Saturn+Mars besiege the 7th, no benefic relief (marital separation)
    "H7.C.83",  # 7th lord in the 12th + malefic on the 7th (marital loss/separation)
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
    metadata: Metadata = ()


@dataclass(frozen=True)
class HouseProforma:
    """Every signification of a house + the rolled-up house verdict.

    ``metadata`` is the de-duplicated, order-preserving union of every
    signification's metadata pairs (deterministic across runs).
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


def _strong(planet: str, chart: RamanChart) -> Optional[bool]:
    """Legacy ``house_judge._strong`` semantics: None on Track-B, else is_powerful."""
    p = chart.planets.get(planet)
    if p is None or p.shadbala_rupas is None:
        return None
    return shadbala_total.is_powerful(planet, p.shadbala_rupas.total / 60.0)


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
    # Longevity guard (methodology §1 lines 39-42, §8): for a longevity/death matter the
    # span class and maraka are owned by the Phase-E longevity sub-engine, which runs as a
    # pre-pass and "gates and modulates all house judgment". This judge must NOT emit a
    # death/afflicted verdict for such a matter — it defers to insufficient-evidence. The
    # guard therefore (a) neutralises maraka_active's verdict-driving effect, (b) replaces
    # the karaka VETO's afflicted with insufficient-evidence, and (c) clamps any afflicted
    # the remaining clauses would produce to insufficient-evidence.
    guarded = "LONGEVITY_GUARD" in L.flags
    maraka_drives = L.maraka_active and not guarded
    # 1. karaka veto — a broken karaka afflicts the matter regardless of evidence.
    if not L.karaka_intact:
        if guarded:
            return _navamsa_modulate("insufficient-evidence", L)
        return _navamsa_modulate("afflicted", L)
    # 1.5 DUSTHANA-AFFLICTION CONFIRMATION (Stage-3, user-signed-off "B"). For an inherently
    # malefic signification (6th disease/enemies/debts/accidents; 12th incarceration/left_eye —
    # flagged AFFLICTION_MATTER in _build_frame_ledger) a fired malefic with NO benefic
    # contradiction CONFIRMS the affliction. This is the directional mirror of the clause-2
    # navamsa guard: pillar strength does NOT rescue a dusthana evil (a strong 6th lord
    # strengthens disease), so the matter must not fall through to clause 6/8 and read as
    # 'mixed', nor be lifted by a confirming navamsa. A BENEFIC contradiction (a Vipareeta /
    # Harsha yoga or a benefic aspect) routes the matter back to the normal preponderance
    # weigh at clause 2. Deferred under the longevity guard (Phase E owns death/span). The
    # verdict is decisive — _navamsa_modulate never shifts an 'afflicted'.
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
        elif (known and strong >= shadbala_total.CONTRA_PILLAR_FAVOUR
                and L.navamsa_status != "weakens"):
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


def _navamsa_status(lord: str, karaka: str, chart: RamanChart) -> NavStatus:
    """Confirm/weaken from D9 — works on Track-B via PlanetPos.navamsa_sign.

    confirms : either lord or karaka is vargottama or D9-exalted/own.
    weakens  : either is D9-debilitated, or sits in a 6/8/12 from the navamsa lagna.
    unknown  : navamsa data absent for both pillars.
    """
    nav_lagna_sign = varga.navamsa_sign(chart.asc_lon)
    saw_any = False
    confirms = False
    weakens = False
    for name in (lord, karaka):
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
    for fr in rf.fire_house(chart, sig.house):
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
    karaka_strong = lord_strong if lord_karaka_identical else _strong(karaka, chart)

    marakas = _maraka_grahas(chart)
    pairs = _parivartana_pairs(chart, ctx)
    parivartana_resilient = _in_parivartana(lord, pairs) or _in_parivartana(karaka, pairs)

    # parivartana leniency: a lord/karaka in an exchange bypasses an inimical/debilitation
    # penalty — treat a debil-but-exchanged pillar as not-weak.
    if parivartana_resilient:
        if lord_strong is False and _in_parivartana(lord, pairs) \
                and _debilitated_uncancelled(lord, chart):
            lord_strong = True
        if karaka_strong is False and _in_parivartana(karaka, pairs) \
                and _debilitated_uncancelled(karaka, chart):
            karaka_strong = True
        if lord_karaka_identical:
            karaka_strong = lord_strong

    bb = _bhava_bala_for(chart, sig.house)
    bb_strong: Optional[bool] = None if bb is None else (bb >= shadbala_total.BHAVA_BALA_MIN_SH)

    navamsa_status = _navamsa_status(lord, karaka, chart)
    karaka_intact = _karaka_intact(karaka, chart, marakas)
    maraka_active = bool(marakas) and (lord in marakas or karaka in marakas)

    benefic, malefic, neutral = _bucket_fired(chart, sig, ctx)

    # Longevity guard (methodology §1, lines 39-42; §8): longevity is a pre-pass that
    # OWNS death/span-class judgment and "gates and modulates all house judgment". A
    # longevity/death signification therefore must NOT emit a death verdict here — the
    # Phase-E longevity sub-engine fixes the span class first. LONGEVITY_GUARD is the
    # load-bearing flag _decide reads to suppress maraka_active and karaka-veto afflicted
    # paths for these matters, deferring the call to Phase E.
    if "longevity" in sig.rule_tags or "death" == sig.key:
        flags.append("LONGEVITY_GUARD")
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
        flags=tuple(dict.fromkeys(flags)))


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
    return verdict, (("beeja_kshetra", "numeric_partial"),), lead


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
    fired_yogas: tuple[FiredYoga, ...] = ctx.get_or_compute(
        "fired_yogas", lambda: detect_yogas(chart))
    verdict, yoga_shifted, yoga_md = _yoga_modulate(verdict, lead, sig, fired_yogas)
    verdict, dhana_shifted, dhana_md = _dhana_floor(verdict, lead, sig, fired_yogas)
    verdict, blem_shifted, blem_md = _blemishless_venus_floor(chart, sig, verdict, lead)
    verdict, gate_md, lead = _fertility_gate(chart, sig, verdict, lead, ctx)
    lookup_md = _lookup_metadata(chart, sig, lead)
    metadata: Metadata = tuple(dict.fromkeys(
        yoga_md + dhana_md + blem_md + gate_md + lookup_md))
    return SignificationVerdict(
        house=house, signification=sig.key, verdict=verdict, karaka=sig.primary_karaka,
        lead_frame=lead.frame, ledger=lead, alt_ledgers=tuple(others),
        borderline_shifted=shifted or dec_shifted or yoga_shifted or dhana_shifted
        or blem_shifted, metadata=metadata)


def _default_sig(house: int) -> Signification:
    """Fallback signification for a house with no encoded sub-matters: the BHAVA_KARAKA."""
    return Signification(
        key="general", house=house, primary_karaka=BHAVA_KARAKA.get(house, "Sun"),
        rule_tags=(), source=Citation("HTJAH-I", 983))


_ROLLUP_ORDER: dict[Verdict, int] = {
    "afflicted": 0, "mixed": 1, "insufficient-evidence": 2, "favourable": 3,
}


def _rollup(verdicts: tuple[Verdict, ...]) -> Verdict:
    """Deterministic house rollup precedence:

    * if BOTH a 'mixed' and a 'favourable' are present -> 'mixed' (a contradicted house
      cannot read as cleanly favourable);
    * otherwise the worst present, ordered afflicted > mixed > insufficient-evidence > favourable.
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
    metadata: Metadata = tuple(dict.fromkeys(
        pair for sv in svs for pair in sv.metadata))
    return HouseProforma(house=house, lord=lord, significations=svs,
                         rollup=rollup, metadata=metadata)


def judge_all_houses(chart: RamanChart) -> list[HouseProforma]:
    return [judge_house(chart, h) for h in range(1, 13)]
