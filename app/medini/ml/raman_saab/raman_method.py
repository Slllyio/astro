"""Raman-as-practiced death-timing encoder — Run 4.

Runs 1–3 tested textbook *marginals* (fixed lord lists, flat maraka-lord sets,
numeric ayurdaya) and were null. In his worked cases (Notable Horoscopes; How
to Judge a Horoscope) B. V. Raman decides differently: a **gated, graded
synthesis** —

1. judge the **longevity class** qualitatively (Jupiter's aspect on the lagna
   lord / 8th lord / Saturn is "the single strongest indicator"; then Saturn's
   ayushkaraka strength, the lagna lord, the 8th house in radix AND navamsa,
   and a Balarishta screen with its classical cancellations);
2. identify **marakas by relationship hierarchy**, not by list — "planets in
   conjunction with lords of the 2nd and 7th are the most powerful in causing
   death, while the lords themselves are least powerful" (HTJAH, maraka
   adhyaya ⚑), with the benefic-kendradhipati promotion (how Gandhi's Jupiter
   dasha kills) — read from the Lagna, the Moon, and the Navamsa;
3. score each dasha/bhukti's **fatal potency**: maraka rank of MD and AD lord
   × weakness (weak marakas/8L/12L kill) × nakshatra-dispositor-is-maraka
   (his Tilak reading ⚑) × marakasthana occupancy — **gated by the longevity
   class** (marakas do not fire outside the permitted age band: his
   Ramanujacharya argument ⚑);
4. confirm by **transit**: Saturn on the 2nd from the natal Moon; Mars–Saturn
   hard contact (his published Gandhi call ⚑).

Every tunable lives in ``RAMAN_WEIGHTS`` with a citation. Weights may be
calibrated ONLY against the golden fidelity cases (fidelity.py); they freeze
in RUN4_PREREG.md before the population is touched.

⚑ = citation to be pinned verbatim by the bphs-doctrine-reviewer before any
promotion past `provisional` (ratchet rule).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from app.core.drishti_argala import aspects_from_planet
from app.medini.ml.raman_saab import dasha as D
from app.medini.ml.raman_saab.ayurdaya import AyuBand
from app.medini.ml.raman_saab.chart_bundle import (
    GRAHAS, NATURAL_BENEFICS, NATURAL_MALEFICS, ChartBundle,
)
from app.medini.ml.raman_saab.kundali import SIGN_RULER, _nth_sign

LORDS: tuple[str, ...] = D.ALL_LORDS
LORD_IDX: dict[str, int] = {L: i for i, L in enumerate(LORDS)}

_KENDRA = frozenset({1, 4, 7, 10})
_TRIKONA = frozenset({1, 5, 9})
_DUSTHANA = frozenset({6, 8, 12})

# ---------------------------------------------------------------------------
# The single weight surface. Citations abbreviated: HTJAH = How to Judge a
# Horoscope; NH = Notable Horoscopes; HPA = Hindu Predictive Astrology.
# ---------------------------------------------------------------------------
RAMAN_WEIGHTS: dict[str, float] = {
    # ── longevity score (0..1, baseline 0.5) ──────────────────────────────
    "lng.jupiter_aspect": 0.10,       # per protected target in {lagna lord, 8L,
                                      # Saturn}; scaled by Jupiter's strength.
                                      # HTJAH: Jupiter's aspect = strongest
                                      # single longevity indicator ⚑
    "lng.saturn_strength": 0.15,      # ayushkaraka; centered (strength-0.5)*2.
                                      # HPA: strong Saturn = long life ⚑
    "lng.lagna_lord_strength": 0.12,  # centered. HTJAH ⚑
    "lng.lagna_lord_dusthana": 0.08,  # subtract if lagna lord in 6/8/12 ⚑
    "lng.lagna_malefic": 0.04,        # per malefic occupying lagna ⚑
    "lng.lagna_benefic": 0.04,        # per benefic occupying/aspecting lagna ⚑
    # 8H-occupancy lifespan factors ZEROED at round-4 calibration: the primary
    # texts do not support either sign for LIFESPAN (NH Einstein reads his
    # Mars+Rahu in the 8th as hardship, not short life — he died at 76; the
    # repo bhava_judge even inverts dusthana occupancy). Keys kept for
    # lineage; re-enable only with a pinned citation.
    "lng.h8_malefic_radix": 0.0,
    "lng.h8_benefic_radix": 0.0,
    "lng.h8_malefic_navamsa": 0.0,
    "lng.lord8_strength": 0.06,       # centered; strong 8L steadies ayus ⚑
    "lng.luminaries_unafflicted": 0.05,  # Sun AND Moon free of malefic
                                      # conjunction/aspect — NH Shaw: "the
                                      # luminaries are free from affliction"
                                      # among his stated longevity marks
    "lng.lagna_lord_kendra": 0.05,    # lagna lord in a kendra = vitality
                                      # (classical; dual of the dusthana
                                      # penalty) ⚑
    "lng.lord2_in_own_2h": 0.04,      # NH Shaw: "the 2nd lord is in the 2nd"
                                      # listed among longevity combinations
    "lng.lord3_in_lagna": 0.04,       # NH Shaw: "the 3rd lord is in Lagna"
                                      # (3rd = 8th-from-8th ayus-sthana)
    # band thresholds on the 0..1 score:
    "lng.purnayu_min": 0.60,
    "lng.madhyayu_min": 0.42,
    # Balarishta screen (HPA balarishta adhyaya ⚑):
    "lng.balarishta_cancel_strength": 0.60,  # lagna-lord/Moon strength that cancels
    # ── maraka hierarchy (per reference frame) ────────────────────────────
    "mk.ref_lagna": 1.00,
    "mk.ref_moon": 0.50,              # Chandra-lagna as secondary reference ⚑
    "mk.ref_navamsa": 0.50,           # NH uses navamsa marakas throughout ⚑
    "mk.ref_navamsa_moon": 0.30,      # navamsa counted from the Moon's navamsa
                                      # position — NH Ramana: Saturn "occupies
                                      # ... the 7th from Chandra Lagna in the
                                      # Navamsa"
    "mk.conjunct_maraka_lord": 1.00,  # THE rule: conjunct 2L/7L = most powerful ⚑
    "mk.malefic_in_maraka_house": 0.80,
    "mk.lord_2": 0.60,                # lords themselves least powerful of the
    "mk.lord_7": 0.50,                # primary set; 2L slightly over 7L ⚑
    "mk.benefic_in_maraka_house": 0.35,
    "mk.lord_3_8_sambandha": 0.30,    # 3L/8L only WITH sambandha to a maraka ⚑
    "mk.in_8h_aspected_by_maraka": 0.65,  # occupant of the frame's 8H under
                                      # conjunction/aspect of a maraka lord —
                                      # NH Gandhi: "Jupiter is in the 8th
                                      # aspected powerfully by Mars — a maraka"
    "mk.saturn_assoc": 0.70,          # Saturn associated with any maraka carrier
                                      # "kills without compunction" ⚑
    "mk.dusthana_lord": 0.20,         # 6L/12L independent, weak killers ⚑
    "mk.malefic_in_12th": 0.30,       # malefic occupant of the frame's 12H —
                                      # NH Gandhi: "the Sun is in the 12th
                                      # from Lagna and in the 2nd — another
                                      # maraka from the Chandra Lagna"
    "mk.saturn_ayushkaraka_base": 0.40,  # Saturn's standing maraka status as
                                      # ayushkaraka — NH Tilak ("Ayushkaraka
                                      # Saturn who is also a maraka"), NH
                                      # Ramana ("besides being Ayushkaraka")
    "mk.weakest_planet": 0.25,        # the chart's weakest planet as killer ⚑
    "mk.kendradhipati_promotion": 0.60,  # benefic kendra-lord tied to 2/7 —
                                      # Gandhi's Jupiter ⚑
    # ── fatal potency of a (MD, AD) moment ────────────────────────────────
    "fp.md": 0.45,
    "fp.ad": 0.55,                    # Raman times death by the bhukti ⚑
    "fp.weakness": 0.60,              # ×(1 + w·(1−strength)) for scoring lords
    "fp.nakshatra_transfer": 0.80,    # a dasha lord INHERITS its nakshatra
                                      # dispositor's maraka power (effective =
                                      # max(own, transfer × dispositor's)) —
                                      # NH Tilak: Rahu kills BECAUSE it is "in
                                      # the constellation of Mercury", whose
                                      # maraka power it carries; NH Einstein:
                                      # Jupiter "in the constellation of Rahu"
    "fp.marakasthana_occupancy": 0.30,  # MD/AD lord sits in 2/7 (radix or D9) ⚑
    # band gate (Ramanujacharya argument: Purnayu chart VETOES early marakas ⚑)
    "fp.gate_in_band": 1.00,
    "fp.gate_adjacent": 0.60,
    "fp.gate_far": 0.25,
    "fp.gate_blend_years": 4.0,       # band edges blend linearly over ±this —
                                      # the bands are fuzzy verbal categories,
                                      # not sharp cutoffs (round-4 calibration:
                                      # Ramana died 0.3y past the 70.0 edge)
    "fp.dasha_sandhi": 0.30,          # dasha-sandhi (MD junction) peril: the
                                      # opening/closing stretch of a Mahadasha
                                      # is death-capable — NH Tilak ("as soon
                                      # as Rahu Dasa commenced", frac 0.02) and
                                      # NH Einstein ("as soon as Jupiter Dasa
                                      # commenced", frac 0.01) ⚑
    "fp.sandhi_frac": 0.05,           # 'junction' = first/last 5% of the MD
    # ── transit confirmation (small, multiplicative) ──────────────────────
    "tr.saturn_2nd_from_moon": 0.25,  # NH Gandhi analysis ⚑
    "tr.mars_saturn_contact": 0.20,   # conj or mutual 7th, transit-to-transit ⚑
}

# Band age ranges (years) — run-3 P6 cutoffs reused for consistency.
BAND_RANGE: dict[AyuBand, tuple[float, float]] = {
    AyuBand.ALPAYU: (0.0, 32.0),
    AyuBand.MADHYAYU: (32.0, 70.0),
    AyuBand.PURNAYU: (70.0, 120.0),
}


# ---------------------------------------------------------------------------
# relationship helpers
# ---------------------------------------------------------------------------

def _aspects_planet(b: ChartBundle, aspecting: str, target: str) -> bool:
    """Whole-sign graha drishti of `aspecting` onto `target`'s house."""
    return b.house_of(target) in aspects_from_planet(
        aspecting, b.house_of(aspecting))


def _conjunct(b: ChartBundle, a: str, p: str) -> bool:
    return a != p and b.house_of(a) == b.house_of(p)


def _sambandha(b: ChartBundle, a: str, p: str) -> bool:
    """Classical full relation: conjunction, mutual aspect, or exchange."""
    if a == p:
        return False
    if _conjunct(b, a, p):
        return True
    if _aspects_planet(b, a, p) and _aspects_planet(b, p, a):
        return True
    return b.dispositor(a) == p and b.dispositor(p) == a  # parivartana


# ---------------------------------------------------------------------------
# Step 1 — longevity class
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LongevityAssessment:
    score: float                 # 0..1
    band: AyuBand
    balarishta: bool
    factors: Mapping[str, float]


def longevity_score(b: ChartBundle, w: Mapping[str, float] = RAMAN_WEIGHTS,
                    ) -> LongevityAssessment:
    f: dict[str, float] = {}
    s = 0.5

    # F1: Jupiter's protective aspect on lagna lord / 8L / Saturn.
    protected = {b.lagna_lord, b.kundali.lord_8, "Saturn"}
    jup_str = b.strength["Jupiter"]
    for tgt in sorted(protected):
        if tgt != "Jupiter" and (_aspects_planet(b, "Jupiter", tgt)
                                 or _conjunct(b, "Jupiter", tgt)):
            f[f"jupiter_protects_{tgt}"] = w["lng.jupiter_aspect"] * jup_str
    # F2: Saturn as ayushkaraka.
    f["saturn_strength"] = w["lng.saturn_strength"] * (b.strength["Saturn"] - 0.5) * 2
    # F3: lagna lord strength and placement.
    ll = b.lagna_lord
    f["lagna_lord_strength"] = w["lng.lagna_lord_strength"] * (b.strength[ll] - 0.5) * 2
    if b.house_of(ll) in _DUSTHANA:
        f["lagna_lord_dusthana"] = -w["lng.lagna_lord_dusthana"]
    elif b.house_of(ll) in _KENDRA:
        f["lagna_lord_kendra"] = w["lng.lagna_lord_kendra"]
    # F4: lagna occupation/aspect.
    for g in GRAHAS:
        if b.house_of(g) == 1:
            if g in NATURAL_MALEFICS:
                f[f"lagna_malefic_{g}"] = -w["lng.lagna_malefic"]
            elif g in ("Jupiter", "Venus"):
                f[f"lagna_benefic_{g}"] = w["lng.lagna_benefic"]
        elif g in ("Jupiter", "Venus") and 1 in aspects_from_planet(g, b.house_of(g)):
            f[f"lagna_benefic_aspect_{g}"] = w["lng.lagna_benefic"] * 0.5
    # F5: 8H condition, radix and navamsa (Raman's affliction reading).
    for g in GRAHAS:
        if b.house_of(g) == 8:
            if g in NATURAL_MALEFICS:
                f[f"h8_malefic_{g}"] = -w["lng.h8_malefic_radix"]
            elif g in ("Jupiter", "Venus"):
                f[f"h8_benefic_{g}"] = w["lng.h8_benefic_radix"]
        if b.navamsa_house(g) == 8 and g in NATURAL_MALEFICS:
            f[f"h8_nav_malefic_{g}"] = -w["lng.h8_malefic_navamsa"]
    # F6: 8th lord steadiness.
    f["lord8_strength"] = w["lng.lord8_strength"] * (b.strength[b.kundali.lord_8] - 0.5) * 2
    # F7: luminaries free from malefic affliction (NH Shaw).
    if not any(
        g in NATURAL_MALEFICS and (_conjunct(b, g, lum)
                                   or _aspects_planet(b, g, lum))
        for lum in ("Sun", "Moon") for g in GRAHAS if g != lum
    ):
        f["luminaries_unafflicted"] = w["lng.luminaries_unafflicted"]
    # F8: Shaw's stated longevity combinations (NH Shaw, verbatim).
    lord2, lord3 = b.kundali.lord_2, b.sign_lord_of_house(3)
    if b.house_of(lord2) == 2:
        f["lord2_in_own_2h"] = w["lng.lord2_in_own_2h"]
    if b.house_of(lord3) == 1:
        f["lord3_in_lagna"] = w["lng.lord3_in_lagna"]

    s += sum(f.values())
    s = min(1.0, max(0.0, s))

    # Balarishta screen with classical cancellations. NOTE: balarishta is a
    # CHILDHOOD-mortality indication (it operates in the early years and is
    # void once survived) — it flags infancy risk but must NOT set the
    # lifetime band. (Round-2 fidelity caught the earlier band override
    # mis-classifying Einstein, dead at 76, as ALPAYU.)
    moon_h = b.house_of("Moon")
    moon_afflicted = moon_h in _DUSTHANA and any(
        g in NATURAL_MALEFICS and (_conjunct(b, g, "Moon")
                                   or _aspects_planet(b, g, "Moon"))
        for g in GRAHAS)
    cancelled = (
        b.house_of("Jupiter") in _KENDRA
        or b.strength[ll] >= w["lng.balarishta_cancel_strength"]
        or (b.moon_waxing
            and b.strength["Moon"] >= w["lng.balarishta_cancel_strength"])
    )
    balarishta = moon_afflicted and not cancelled

    if s < w["lng.madhyayu_min"]:
        band = AyuBand.ALPAYU
    elif s >= w["lng.purnayu_min"]:
        band = AyuBand.PURNAYU
    else:
        band = AyuBand.MADHYAYU
    return LongevityAssessment(score=s, band=band, balarishta=balarishta,
                               factors=f)


# ---------------------------------------------------------------------------
# Step 2 — maraka hierarchy
# ---------------------------------------------------------------------------

def _frame_houses(b: ChartBundle, frame: str) -> tuple[dict[str, int], int]:
    """(graha -> house, reference sign) in the given frame."""
    if frame == "lagna":
        return dict(b.kundali.planet_house), b.kundali.lagna_sign
    if frame == "moon":
        return ({g: b.house_from_moon(g) for g in GRAHAS},
                b.chart.planet_signs["Moon"])
    if frame == "navamsa":
        return ({g: b.navamsa_house(g) for g in GRAHAS}, b.navamsa_lagna)
    if frame == "navamsa_moon":
        moon_nav = b.navamsa_sign["Moon"]
        return ({g: ((b.navamsa_sign[g] - moon_nav) % 12) + 1
                 for g in GRAHAS}, moon_nav)
    raise ValueError(frame)


def _frame_maraka_contrib(b: ChartBundle, frame: str,
                          w: Mapping[str, float]) -> dict[str, float]:
    """One reference frame's maraka contributions per graha."""
    houses, ref_sign = _frame_houses(b, frame)
    lord2 = SIGN_RULER[_nth_sign(ref_sign, 2)]
    lord7 = SIGN_RULER[_nth_sign(ref_sign, 7)]
    lord3 = SIGN_RULER[_nth_sign(ref_sign, 3)]
    lord8 = SIGN_RULER[_nth_sign(ref_sign, 8)]
    lord6 = SIGN_RULER[_nth_sign(ref_sign, 6)]
    lord12 = SIGN_RULER[_nth_sign(ref_sign, 12)]
    maraka_lords = {lord2, lord7}

    out = {g: 0.0 for g in GRAHAS}
    carriers: set[str] = set()  # planets that carry primary maraka power

    # The hierarchy, most→least powerful (HTJAH ⚑). Each graha takes its
    # single highest applicable rank per frame (max, not sum) so the encoder
    # mirrors Raman's ranked language rather than double-counting.
    def bump(g: str, val: float, *, carrier: bool = False) -> None:
        out[g] = max(out[g], val)
        if carrier:
            carriers.add(g)

    for g in GRAHAS:
        for ml in maraka_lords:
            if g != ml and houses.get(g) == houses.get(ml):
                bump(g, w["mk.conjunct_maraka_lord"], carrier=True)
        if houses.get(g) in (2, 7):
            if g in NATURAL_MALEFICS:
                bump(g, w["mk.malefic_in_maraka_house"], carrier=True)
            else:
                bump(g, w["mk.benefic_in_maraka_house"])
    bump(lord2, w["mk.lord_2"], carrier=True)
    bump(lord7, w["mk.lord_7"], carrier=True)
    # Occupant of this frame's 8H under conjunction/aspect of a maraka lord
    # (NH Gandhi: Jupiter in the 8th aspected by Mars, the Libra maraka).
    # Planet-to-planet aspects are sign-distance relations, frame-independent.
    for g in GRAHAS:
        if houses.get(g) == 8 and any(
            g != ml and (_conjunct(b, ml, g) or _aspects_planet(b, ml, g))
            for ml in maraka_lords
        ):
            bump(g, w["mk.in_8h_aspected_by_maraka"], carrier=True)
    for lg in (lord3, lord8):
        if any(_sambandha(b, lg, ml) for ml in maraka_lords):
            bump(lg, w["mk.lord_3_8_sambandha"])
    for lg in (lord6, lord12):
        bump(lg, w["mk.dusthana_lord"])
    # Malefic occupant of the frame's 12H (NH Gandhi: the Sun in the 12th).
    for g in GRAHAS:
        if houses.get(g) == 12 and g in NATURAL_MALEFICS:
            bump(g, w["mk.malefic_in_12th"])
    # Saturn's association promotion — with any primary carrier.
    if any(_sambandha(b, "Saturn", c) for c in carriers if c != "Saturn"):
        bump("Saturn", w["mk.saturn_assoc"])
    # Benefic kendradhipati promotion (Gandhi's Jupiter ⚑): a natural benefic
    # ruling a kendra of THIS frame while also owning or occupying 2/7.
    for g in ("Jupiter", "Venus", "Mercury"):
        rules_kendra = any(SIGN_RULER[_nth_sign(ref_sign, h)] == g
                           for h in (4, 7, 10))
        tied_to_maraka = g in maraka_lords or houses.get(g) in (2, 7)
        if rules_kendra and tied_to_maraka:
            bump(g, w["mk.kendradhipati_promotion"])
    return out


def maraka_scores(b: ChartBundle, w: Mapping[str, float] = RAMAN_WEIGHTS,
                  ) -> dict[str, float]:
    """Frame-weighted maraka power per graha (lagna + Moon + navamsa)."""
    total = {g: 0.0 for g in GRAHAS}
    for frame, fw in (("lagna", w["mk.ref_lagna"]),
                      ("moon", w["mk.ref_moon"]),
                      ("navamsa", w["mk.ref_navamsa"]),
                      ("navamsa_moon", w["mk.ref_navamsa_moon"])):
        contrib = _frame_maraka_contrib(b, frame, w)
        for g in GRAHAS:
            total[g] += fw * contrib[g]
    # Saturn's standing maraka status as ayushkaraka (applied once, not
    # per frame — NH Tilak/Ramana).
    total["Saturn"] += w["mk.saturn_ayushkaraka_base"]
    # The chart's weakest planet joins the killer set (HTJAH ⚑).
    weakest = min(GRAHAS, key=lambda g: b.strength[g])
    total[weakest] += w["mk.weakest_planet"]
    return total


# ---------------------------------------------------------------------------
# Steps 3–4 — fatal potency of a moment (vectorized per person)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PotencyModel:
    """Per-person precomputation; per-moment evaluation is array lookups."""
    person_id: str
    band: AyuBand
    longevity: LongevityAssessment
    maraka: np.ndarray          # score per LORD_IDX
    lord_factor: np.ndarray     # weakness × occupancy × nakshatra, per lord
    moon_sign: int

    @classmethod
    def from_bundle(cls, b: ChartBundle,
                    w: Mapping[str, float] = RAMAN_WEIGHTS) -> "PotencyModel":
        lng = longevity_score(b, w)
        mk = maraka_scores(b, w)
        # A dasha lord inherits its nakshatra dispositor's maraka power
        # (NH Tilak: Rahu kills as carrier of Mercury's maraka power).
        eff = {}
        for L in LORDS:
            disp = b.nakshatra_lord.get(L)
            inherited = (w["fp.nakshatra_transfer"] * mk.get(disp, 0.0)
                         if disp and disp != L else 0.0)
            eff[L] = max(mk[L], inherited)
        maraka = np.array([eff[L] for L in LORDS], dtype=np.float64)
        factor = np.ones(len(LORDS), dtype=np.float64)
        for i, L in enumerate(LORDS):
            # weakness amplifies planets that already carry killing power
            if eff[L] > 0:
                factor[i] *= 1.0 + w["fp.weakness"] * (1.0 - b.strength[L])
            # marakasthana occupancy, radix or navamsa
            if b.house_of(L) in (2, 7) or b.navamsa_house(L) in (2, 7):
                factor[i] *= 1.0 + w["fp.marakasthana_occupancy"]
        return cls(person_id=b.person_id, band=lng.band, longevity=lng,
                   maraka=maraka, lord_factor=factor,
                   moon_sign=b.chart.planet_signs["Moon"])

    def band_gate(self, ages: np.ndarray,
                  w: Mapping[str, float] = RAMAN_WEIGHTS) -> np.ndarray:
        """Per-band plateaus with linear ramps across the two internal
        boundaries (32, 70) — the bands are fuzzy verbal categories."""
        def plateau(band: AyuBand) -> float:
            d = abs(int(band) - int(self.band))
            return (w["fp.gate_in_band"] if d == 0
                    else w["fp.gate_adjacent"] if d == 1
                    else w["fp.gate_far"])

        vals = {b: plateau(b) for b in BAND_RANGE}
        gate = np.full(ages.shape, vals[AyuBand.PURNAYU], dtype=np.float64)
        for b, (lo, hi) in BAND_RANGE.items():
            m = (ages >= lo) & (ages < hi)
            gate[m] = vals[b]
        blend = w["fp.gate_blend_years"]
        if blend > 0:
            for edge, (b_lo, b_hi) in (
                (32.0, (AyuBand.ALPAYU, AyuBand.MADHYAYU)),
                (70.0, (AyuBand.MADHYAYU, AyuBand.PURNAYU)),
            ):
                near = np.abs(ages - edge) < blend
                if near.any():
                    t = (ages[near] - (edge - blend)) / (2.0 * blend)  # 0..1
                    gate[near] = vals[b_lo] + (vals[b_hi] - vals[b_lo]) * t
        return gate

    def potency(self, md_idx: np.ndarray, ad_idx: np.ndarray,
                ages: np.ndarray,
                sat_sign: np.ndarray | None = None,
                mars_sign: np.ndarray | None = None,
                md_frac: np.ndarray | None = None,
                w: Mapping[str, float] = RAMAN_WEIGHTS) -> np.ndarray:
        """Fatal potency at each (MD, AD, age[, transit, MD-phase]) moment."""
        md_term = (self.maraka * self.lord_factor)[md_idx]
        ad_term = (self.maraka * self.lord_factor)[ad_idx]
        base = w["fp.md"] * md_term + w["fp.ad"] * ad_term
        pot = base * self.band_gate(ages, w)
        if md_frac is not None:
            # dasha-sandhi peril: opening/closing stretch of the Mahadasha
            sandhi = (md_frac < w["fp.sandhi_frac"]) | (
                md_frac > 1.0 - w["fp.sandhi_frac"])
            pot = pot * (1.0 + w["fp.dasha_sandhi"] * sandhi)
        if sat_sign is not None:
            sat_h_from_moon = ((sat_sign - self.moon_sign) % 12) + 1
            pot = pot * (1.0 + w["tr.saturn_2nd_from_moon"]
                         * (sat_h_from_moon == 2))
            if mars_sign is not None:
                contact = ((mars_sign == sat_sign)
                           | (((mars_sign - sat_sign) % 12) == 6))
                pot = pot * (1.0 + w["tr.mars_saturn_contact"] * contact)
        return pot
