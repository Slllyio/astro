"""Raman-as-practiced encoder v2 — Run 5 (audit-corrected).

Differences from the refuted run-4 ``raman_method.py`` (kept frozen for
reproducibility), each grounded in the three-agent audit:

LONGEVITY — the v1 additive score was degenerate (ALPAYU predicted 1.4% of
the time). v2 uses Raman's only SYSTEMATIC ayurdaya algorithm (HTJAH p.212):
the lagna lord and natural benefics vote by placement class (Kendra→PURNAYU,
Panapara→MADHYAYU, Apoklima→ALPAYU), the 8th lord and natural malefics vote
the INVERSE, each vote weighted by planetary strength ("the relative
strengths of the planets must be balanced" — verbatim); band = argmax.
Jupiter's protective aspect promotes one band on narrow margins. Band
cutoffs move to 8/32/**75**/120 — HPA p.110 explicitly REJECTS the 32/70
split v1 used.

MARAKA — frame-aware conjunction/sambandha (v1 computed D9-frame relations
in radix houses); occupant-of-2nd > occupant-of-7th > lord-2 > lord-7 as
ordered keys (HPA: "The 2nd house is always stronger … Planets who occupy
the 2nd are stronger than the planets who own it"); double-2/7-lordship
bonus; planet-ASPECTING-the-2nd/7th term (NH Tilak: "Rahu aspects the
7th"); independent 8L base; planet-conjunct-12L path (HPA p.126); the Sun
joins the kendra-lord "sure maraka" promotion (HPA: "If the Sun and Sukra
… get Kendradhipatya — they are sure to become marakas"); and the
per-lagna kill/spare override table (HPA Ch. XVII, verbatim per row below).

POTENCY — the nakshatra transfer now inherits the dispositor's
weakness-amplified total (v1 dropped the weakness that is doctrinally WHY
it kills); nodes additionally inherit their SIGN dispositor's total
("shadowy planet gives the results of …", ~10 NH cases); the occupancy
double-count is removed (lord factor = weakness only); weakness finally
consumes combustion and the graded Shadbala; NEW terms: tara/star-of-death
(Vipat=3rd, Pratyak=5th, Naidhana=7th tara from the janma nakshatra —
primary killer argument in ≥5 NH cases) and the MD↔AD shashtashtaka (6/8)
/ dwirdwadasa (2/12) natal-sign relation (~8 NH cases). Dasha-sandhi kept
(≥12 NH cases).

TRANSITS — Raman-frame Saturn ingress tables: sadesathi-3rd-cycle (≥4 NH
cases) and the HPA p.127 composite point (Sat+Jup+Sun+Moon longitudes
summed mod 360; Saturn's 1st/2nd/3rd transit over it for short/middle/long
life). Their inclusion in the run-5 primaries is decided on the
calibration half only (prereg rule).

Weights live in ``RAMAN_WEIGHTS_V2`` (doctrine-ordered defaults) and are
overridden by the calibrated ``data/raman_saab/run5_weights.json`` at
freeze. Ordering constraints that calibration must preserve are listed in
``ORDERING_CONSTRAINTS``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
_PANAPARA = frozenset({2, 5, 8, 11})
_APOKLIMA = frozenset({3, 6, 9, 12})
_NAK_SPAN = 360.0 / 27.0

# Tara counting: 1-based position of a nakshatra from the janma nakshatra,
# folded mod 9. Fatal taras (NH usage): Vipat=3, Pratyak=5, Naidhana=7.
TARA_FATAL: frozenset[int] = frozenset({3, 5, 7})

BAND_RANGE_V2: dict[AyuBand, tuple[float, float]] = {
    AyuBand.ALPAYU: (0.0, 32.0),      # balarishta (<8) folds into ALPAYU
    AyuBand.MADHYAYU: (32.0, 75.0),   # HPA p.110: "as far as 75 from the 33rd year"
    AyuBand.PURNAYU: (75.0, 120.0),
}


def band_of_age_v2(age_years: float) -> AyuBand:
    if age_years < 32.0:
        return AyuBand.ALPAYU
    if age_years < 75.0:
        return AyuBand.MADHYAYU
    return AyuBand.PURNAYU


RAMAN_WEIGHTS_V2: dict[str, float] = {
    # ── longevity v2 (placement-class votes) ──────────────────────────────
    "lng2.lagna_lord": 1.00,     # Raman leads with the lagna lord (HTJAH p.212)
    "lng2.lord8": 0.80,
    "lng2.benefic": 0.50,        # per natural benefic
    "lng2.malefic": 0.50,        # per natural malefic (inverted class)
    "lng2.promotion_margin": 0.15,  # Jupiter-aspect promotes one band when the
                                    # top-two vote margin is below this
    "lng2.balarishta_cancel_strength": 0.60,
    # ── maraka hierarchy v2 (ordered; see ORDERING_CONSTRAINTS) ───────────
    "mk2.conjunct_maraka_lord": 1.00,   # most powerful (HTJAH p.16)
    "mk2.occupant_2_malefic": 0.85,     # occupant > owner; 2nd > 7th (HPA p.125)
    "mk2.occupant_7_malefic": 0.75,
    "mk2.lord_both_2_7": 0.80,          # double maraka lordship
    "mk2.lord_2": 0.60,
    "mk2.lord_7": 0.50,
    "mk2.occupant_2_benefic": 0.40,     # secondary determinants (HTJAH p.16)
    "mk2.occupant_7_benefic": 0.30,
    "mk2.aspect_2_malefic": 0.35,       # NH Tilak: "Rahu aspects the 7th"
    "mk2.aspect_7_malefic": 0.30,
    "mk2.aspect_benefic_factor": 0.50,  # benefic aspect on 2/7 at half weight
    "mk2.in_8h_aspected_by_maraka": 0.65,  # NH Gandhi
    "mk2.lord_3_8_sambandha": 0.30,
    "mk2.lord_8_base": 0.20,            # independent tertiary (HTJAH p.16)
    "mk2.dusthana_lord": 0.20,          # 6L / 12L
    "mk2.malefic_in_12th": 0.30,        # NH Gandhi (Sun in the 12th)
    "mk2.conjunct_lord_12": 0.25,       # HPA p.126 (12L-conjunction path)
    "mk2.saturn_assoc": 0.70,           # "in preference to any of those planets"
    "mk2.saturn_ayushkaraka_base": 0.40,
    "mk2.kendradhipati_promotion": 0.60,  # Jupiter/Venus/Mercury/SUN (HPA p.126)
    "mk2.weakest_planet": 0.25,
    "mk2.override_spare": 0.25,         # HPA Ch. XVII "does not kill" multiplier
    "mk2.override_kill_floor": 0.50,    # HPA Ch. XVII named killers floor
    # ── frame weights ─────────────────────────────────────────────────────
    "mk2.ref_lagna": 1.00,
    "mk2.ref_moon": 0.50,
    "mk2.ref_navamsa": 0.50,
    "mk2.ref_navamsa_moon": 0.30,
    # ── potency v2 ────────────────────────────────────────────────────────
    "fp2.md": 0.45,
    "fp2.ad": 0.55,
    "fp2.weakness": 0.60,
    "fp2.combust_weak": 0.30,           # combustion adds to the weakness term
    "fp2.nakshatra_transfer": 0.80,     # inherits the dispositor's FULL
                                        # weakness-amplified total (audit fix)
    "fp2.node_sign_dispositor": 0.60,   # nodes give their sign-dispositor's
                                        # results (~10 NH cases)
    "fp2.tara_death": 0.40,             # lord's natal star in a fatal tara
    "fp2.md_ad_shashtashtaka": 0.25,    # 6/8 natal-sign relation MD↔AD
    "fp2.md_ad_dwirdwadasa": 0.20,      # 2/12
    "fp2.dasha_sandhi": 0.30,
    "fp2.sandhi_frac": 0.05,
    # band gate
    "fp2.gate_in_band": 1.00,
    "fp2.gate_adjacent": 0.60,
    "fp2.gate_far": 0.25,
    "fp2.gate_blend_years": 4.0,
    # ── transits (inclusion decided at calibration; see prereg) ───────────
    "tr2.sadesathi_3rd": 0.25,
    "tr2.composite_point": 0.30,
    "tr2.composite_orb_deg": 15.0,
}

# Calibration must preserve these strict orderings (HPA/HTJAH hierarchy).
ORDERING_CONSTRAINTS: tuple[tuple[str, str], ...] = (
    ("mk2.conjunct_maraka_lord", "mk2.occupant_2_malefic"),
    ("mk2.occupant_2_malefic", "mk2.occupant_7_malefic"),
    ("mk2.occupant_7_malefic", "mk2.lord_2"),
    ("mk2.lord_both_2_7", "mk2.lord_2"),
    ("mk2.lord_2", "mk2.lord_7"),
    ("mk2.lord_7", "mk2.occupant_2_benefic"),
    ("mk2.occupant_2_benefic", "mk2.occupant_7_benefic"),
)

# HPA Ch. XVII (pp.134-137) verbatim kill/spare rules, keyed by lagna sign.
# "spares": planets that "do not kill … even if possessed of Maraka power";
# "kills": planets the text singles out as inflicting death when maraka.
# Libra's third named killer is an OCR ambiguity ("Mars" repeated where the
# parallel construction implies "Mercury") — omitted conservatively.
LAGNA_MARAKA_OVERRIDES: dict[int, dict[str, frozenset[str]]] = {
    1:  {"spares": frozenset({"Venus"}),                    # "If Venus becomes a
         "kills": frozenset({"Saturn"})},                   #  Maraka he will not
                                                            #  kill … Saturn will"
    2:  {"spares": frozenset(),                             # "killed in the periods
         "kills": frozenset({"Jupiter", "Venus", "Moon"})}, #  … of Jupiter, Venus
                                                            #  and the Moon"
    3:  {"spares": frozenset({"Moon"}), "kills": frozenset()},  # "Moon will not kill"
    4:  {"spares": frozenset({"Sun"}),                      # "Sun does not kill …
         "kills": frozenset({"Venus"})},                    #  Venus and other
                                                            #  inauspicious … kill"
    5:  {"spares": frozenset({"Saturn"}),                   # "Saturn does not kill
         "kills": frozenset({"Mercury"})},                  #  … Mercury and other
                                                            #  evil planets inflict"
    6:  {"spares": frozenset({"Sun"}),                      # "Sun does not kill …
         "kills": frozenset({"Venus", "Moon", "Jupiter"})}, #  Venus, Moon, Jupiter
                                                            #  will inflict death"
    7:  {"spares": frozenset({"Mars"}),                     # "Mars himself will not
         "kills": frozenset({"Jupiter", "Venus"})},         #  kill … Jupiter, Venus
                                                            #  [Mercury?] certainly"
    8:  {"spares": frozenset({"Jupiter"}),                  # "Jupiter, even if he
         "kills": frozenset({"Mercury"})},                  #  becomes a Maraka does
                                                            #  not … Mercury …"
    9:  {"spares": frozenset({"Saturn"}),                   # "Saturn does not bring
         "kills": frozenset({"Venus"})},                    #  about death … Venus
                                                            #  causes death"
    10: {"spares": frozenset(), "kills": frozenset()},      # no kill/spare stated
    11: {"spares": frozenset(), "kills": frozenset()},      # no kill/spare stated
    12: {"spares": frozenset({"Mars"}), "kills": frozenset()},  # "Mars himself does
                                                            #  not kill"
}


def load_weights(path: str | Path | None) -> dict[str, float]:
    """RAMAN_WEIGHTS_V2 overlaid with a calibrated JSON, if given."""
    w = dict(RAMAN_WEIGHTS_V2)
    if path:
        w.update({k: float(v) for k, v in json.loads(Path(path).read_text()).items()})
    return w


# ---------------------------------------------------------------------------
# frame helpers (audit fix: relations computed in the frame's own varga)
# ---------------------------------------------------------------------------

def _frame_signs(b: ChartBundle, frame: str) -> tuple[dict[str, int], int]:
    """(graha -> sign in this frame's varga, reference sign)."""
    if frame == "lagna":
        return dict(b.chart.planet_signs), b.kundali.lagna_sign
    if frame == "moon":
        return dict(b.chart.planet_signs), b.chart.planet_signs["Moon"]
    if frame == "navamsa":
        return dict(b.navamsa_sign), b.navamsa_lagna
    if frame == "navamsa_moon":
        return dict(b.navamsa_sign), b.navamsa_sign["Moon"]
    raise ValueError(frame)


def _house_in_frame(signs: Mapping[str, int], ref_sign: int, g: str) -> int:
    return ((signs[g] - ref_sign) % 12) + 1


def _aspect_distances(planet: str) -> tuple[int, ...]:
    # distances derived from the repo drishti table (house-from-self counts)
    return aspects_from_planet(planet, 1)


def _frame_conjunct(signs: Mapping[str, int], a: str, p: str) -> bool:
    return a != p and signs[a] == signs[p]


def _frame_aspects(signs: Mapping[str, int], a: str, p: str) -> bool:
    if a == p:
        return False
    dist = ((signs[p] - signs[a]) % 12) + 1
    return dist in _aspect_distances(a)


def _frame_sambandha(b: ChartBundle, signs: Mapping[str, int],
                     a: str, p: str) -> bool:
    """Conjunction or mutual aspect IN THIS FRAME; parivartana stays radix
    (sign ownership is frame-independent — pinned choice)."""
    if a == p:
        return False
    if _frame_conjunct(signs, a, p):
        return True
    if _frame_aspects(signs, a, p) and _frame_aspects(signs, p, a):
        return True
    return b.dispositor(a) == p and b.dispositor(p) == a


# ---------------------------------------------------------------------------
# longevity v2 — placement-class argmax (HTJAH p.212)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LongevityV2:
    band: AyuBand
    votes: Mapping[AyuBand, float]
    promoted: bool
    balarishta: bool


_POSITIVE_CLASS = {**{h: AyuBand.PURNAYU for h in _KENDRA},
                   **{h: AyuBand.MADHYAYU for h in _PANAPARA},
                   **{h: AyuBand.ALPAYU for h in _APOKLIMA}}
_NEGATIVE_CLASS = {**{h: AyuBand.ALPAYU for h in _KENDRA},
                   **{h: AyuBand.MADHYAYU for h in _PANAPARA},
                   **{h: AyuBand.PURNAYU for h in _APOKLIMA}}


def longevity_v2(b: ChartBundle,
                 w: Mapping[str, float] = RAMAN_WEIGHTS_V2) -> LongevityV2:
    votes = {band: 0.0 for band in AyuBand}
    ll, l8 = b.lagna_lord, b.kundali.lord_8
    # positive group: lagna lord + natural benefics
    for p in {ll} | NATURAL_BENEFICS:
        grp = w["lng2.lagna_lord"] if p == ll else w["lng2.benefic"]
        votes[_POSITIVE_CLASS[b.house_of(p)]] += grp * b.strength[p]
    # negative group: 8th lord + natural malefics (inverted classes)
    for p in {l8} | NATURAL_MALEFICS:
        grp = w["lng2.lord8"] if p == l8 else w["lng2.malefic"]
        votes[_NEGATIVE_CLASS[b.house_of(p)]] += grp * b.strength[p]

    ranked = sorted(votes, key=lambda k: votes[k], reverse=True)
    band = ranked[0]
    if votes[ranked[0]] == votes[ranked[1]]:  # tie: lagna lord's vote decides
        ll_band = _POSITIVE_CLASS[b.house_of(ll)]
        band = ll_band if votes[ll_band] == votes[ranked[0]] else AyuBand.MADHYAYU

    # Jupiter's protective aspect promotes one band on a narrow margin
    promoted = False
    margin = votes[ranked[0]] - votes[ranked[1]]
    if band != AyuBand.PURNAYU and margin < w["lng2.promotion_margin"]:
        protected = {ll, l8, "Saturn"}
        signs = dict(b.chart.planet_signs)
        if any(t != "Jupiter" and (_frame_conjunct(signs, "Jupiter", t)
                                   or _frame_aspects(signs, "Jupiter", t))
               for t in protected):
            band = AyuBand(int(band) + 1)
            promoted = True

    # balarishta: childhood-mortality flag only (never sets the band)
    moon_h = b.house_of("Moon")
    signs = dict(b.chart.planet_signs)
    moon_afflicted = moon_h in {6, 8, 12} and any(
        g in NATURAL_MALEFICS and (_frame_conjunct(signs, g, "Moon")
                                   or _frame_aspects(signs, g, "Moon"))
        for g in GRAHAS)
    cancelled = (b.house_of("Jupiter") in _KENDRA
                 or b.strength[ll] >= w["lng2.balarishta_cancel_strength"]
                 or (b.moon_waxing
                     and b.strength["Moon"] >= w["lng2.balarishta_cancel_strength"]))
    return LongevityV2(band=band, votes=votes, promoted=promoted,
                       balarishta=moon_afflicted and not cancelled)


# ---------------------------------------------------------------------------
# maraka v2
# ---------------------------------------------------------------------------

def _frame_contrib_v2(b: ChartBundle, frame: str,
                      w: Mapping[str, float]) -> dict[str, float]:
    signs, ref_sign = _frame_signs(b, frame)
    houses = {g: _house_in_frame(signs, ref_sign, g) for g in GRAHAS}
    lord2 = SIGN_RULER[_nth_sign(ref_sign, 2)]
    lord7 = SIGN_RULER[_nth_sign(ref_sign, 7)]
    lord3 = SIGN_RULER[_nth_sign(ref_sign, 3)]
    lord6 = SIGN_RULER[_nth_sign(ref_sign, 6)]
    lord8 = SIGN_RULER[_nth_sign(ref_sign, 8)]
    lord12 = SIGN_RULER[_nth_sign(ref_sign, 12)]
    maraka_lords = {lord2, lord7}

    out = {g: 0.0 for g in GRAHAS}
    carriers: set[str] = set()

    def bump(g: str, val: float, *, carrier: bool = False) -> None:
        out[g] = max(out[g], val)
        if carrier:
            carriers.add(g)

    for g in GRAHAS:
        # conjunct a maraka lord — THE most powerful (frame-aware)
        for ml in maraka_lords:
            if _frame_conjunct(signs, g, ml):
                bump(g, w["mk2.conjunct_maraka_lord"], carrier=True)
        # occupancy, ordered 2nd > 7th, malefic > benefic
        if houses[g] == 2:
            key = ("mk2.occupant_2_malefic" if g in NATURAL_MALEFICS
                   else "mk2.occupant_2_benefic")
            bump(g, w[key], carrier=g in NATURAL_MALEFICS)
        elif houses[g] == 7:
            key = ("mk2.occupant_7_malefic" if g in NATURAL_MALEFICS
                   else "mk2.occupant_7_benefic")
            bump(g, w[key], carrier=g in NATURAL_MALEFICS)
        # aspect on the 2nd/7th house of this frame (NH Tilak)
        else:
            own_house = houses[g]
            targets = {((own_house - 1 + d - 1) % 12) + 1
                       for d in _aspect_distances(g)}
            factor = 1.0 if g in NATURAL_MALEFICS else w["mk2.aspect_benefic_factor"]
            if 2 in targets:
                bump(g, w["mk2.aspect_2_malefic"] * factor)
            elif 7 in targets:
                bump(g, w["mk2.aspect_7_malefic"] * factor)
        # malefic occupant of the 12th (NH Gandhi)
        if houses[g] == 12 and g in NATURAL_MALEFICS:
            bump(g, w["mk2.malefic_in_12th"])
        # conjunct the 12th lord (HPA p.126)
        if _frame_conjunct(signs, g, lord12):
            bump(g, w["mk2.conjunct_lord_12"])

    # lords of 2/7 (least powerful of the primary set; double lordship higher)
    if lord2 == lord7:
        bump(lord2, w["mk2.lord_both_2_7"], carrier=True)
    else:
        bump(lord2, w["mk2.lord_2"], carrier=True)
        bump(lord7, w["mk2.lord_7"], carrier=True)
    # occupant of the frame's 8H under conjunction/aspect of a maraka lord
    for g in GRAHAS:
        if houses[g] == 8 and any(
            g != ml and (_frame_conjunct(signs, ml, g)
                         or _frame_aspects(signs, ml, g))
            for ml in maraka_lords
        ):
            bump(g, w["mk2.in_8h_aspected_by_maraka"], carrier=True)
    # 3L/8L with sambandha to a maraka lord; 8L independent base
    for lg in (lord3, lord8):
        if any(_frame_sambandha(b, signs, lg, ml) for ml in maraka_lords):
            bump(lg, w["mk2.lord_3_8_sambandha"])
    bump(lord8, w["mk2.lord_8_base"])
    for lg in (lord6, lord12):
        bump(lg, w["mk2.dusthana_lord"])
    # Saturn's association with any primary carrier
    if any(_frame_sambandha(b, signs, "Saturn", c)
           for c in carriers if c != "Saturn"):
        bump("Saturn", w["mk2.saturn_assoc"])
    # kendra-lord "sure maraka" promotion — now including the Sun (HPA p.126)
    for g in ("Jupiter", "Venus", "Mercury", "Sun"):
        rules_kendra = any(SIGN_RULER[_nth_sign(ref_sign, h)] == g
                           for h in (4, 7, 10))
        tied = g in maraka_lords or houses[g] in (2, 7)
        if rules_kendra and tied:
            bump(g, w["mk2.kendradhipati_promotion"])

    # per-lagna kill/spare overrides — lagna frame only (HPA Ch. XVII)
    if frame == "lagna":
        ov = LAGNA_MARAKA_OVERRIDES[b.kundali.lagna_sign]
        for g in ov["spares"]:
            out[g] *= w["mk2.override_spare"]
        for g in ov["kills"]:
            out[g] = max(out[g], w["mk2.override_kill_floor"])
    return out


def maraka_scores_v2(b: ChartBundle,
                     w: Mapping[str, float] = RAMAN_WEIGHTS_V2
                     ) -> dict[str, float]:
    total = {g: 0.0 for g in GRAHAS}
    for frame, fw in (("lagna", w["mk2.ref_lagna"]),
                      ("moon", w["mk2.ref_moon"]),
                      ("navamsa", w["mk2.ref_navamsa"]),
                      ("navamsa_moon", w["mk2.ref_navamsa_moon"])):
        contrib = _frame_contrib_v2(b, frame, w)
        for g in GRAHAS:
            total[g] += fw * contrib[g]
    total["Saturn"] += w["mk2.saturn_ayushkaraka_base"]
    weakest = min(GRAHAS, key=lambda g: b.strength[g])
    total[weakest] += w["mk2.weakest_planet"]
    return total


# ---------------------------------------------------------------------------
# potency v2
# ---------------------------------------------------------------------------

def _strength_v2(b: ChartBundle, g: str) -> float:
    """½ Vimsopaka + ½ graded Shadbala (visible 7); nodes keep dispositor
    Vimsopaka on both halves (pinned)."""
    vim = b.strength[g]
    sr = b.shadbala_ratio.get(g)
    if sr is None:
        return vim
    return 0.5 * vim + 0.5 * min(sr, 2.0) / 2.0


def _nak_index(lon: float) -> int:
    return int((lon % 360.0) // _NAK_SPAN)


def _tara_of(lord_lon: float, moon_lon: float) -> int:
    """1-based tara of the lord's natal star counted from the janma star."""
    return ((_nak_index(lord_lon) - _nak_index(moon_lon)) % 27) % 9 + 1


@dataclass(frozen=True)
class PotencyModelV2:
    person_id: str
    band: AyuBand
    longevity: LongevityV2
    maraka: np.ndarray        # effective (post-transfer) per LORD_IDX
    pair_factor: np.ndarray   # (9, 9) MD↔AD relation multiplier
    moon_sign: int
    composite_point: float    # (Sat+Jup+Sun+Moon) natal longitudes mod 360

    @classmethod
    def from_bundle(cls, b: ChartBundle,
                    w: Mapping[str, float] = RAMAN_WEIGHTS_V2
                    ) -> "PotencyModelV2":
        lng = longevity_v2(b, w)
        mk = maraka_scores_v2(b, w)
        # weakness-amplified own totals (occupancy no longer double-counted)
        own = {}
        for g in GRAHAS:
            weak = 1.0
            if mk[g] > 0:
                weak += w["fp2.weakness"] * (1.0 - _strength_v2(b, g))
                if b.combust.get(g):
                    weak += w["fp2.combust_weak"]
            own[g] = mk[g] * weak
        # transfers inherit the dispositor's FULL amplified total
        eff = {}
        for g in GRAHAS:
            e = own[g]
            disp = b.nakshatra_lord.get(g)
            if disp and disp != g:
                e = max(e, w["fp2.nakshatra_transfer"] * own[disp])
            if g in ("Rahu", "Ketu"):
                sd = b.dispositor(g)
                if sd != g:
                    e = max(e, w["fp2.node_sign_dispositor"] * own[sd])
            # tara/star-of-death: the lord's natal star in a fatal tara
            if _tara_of(b.chart.planet_lons[g],
                        b.chart.planet_lons["Moon"]) in TARA_FATAL:
                e *= 1.0 + w["fp2.tara_death"]
            eff[g] = e
        maraka = np.array([eff[L] for L in LORDS], dtype=np.float64)
        # MD↔AD natal-sign relation matrix
        pair = np.ones((len(LORDS), len(LORDS)), dtype=np.float64)
        for i, mdl in enumerate(LORDS):
            for j, adl in enumerate(LORDS):
                if i == j:
                    continue
                dist = ((b.chart.planet_signs[adl]
                         - b.chart.planet_signs[mdl]) % 12) + 1
                if dist in (6, 8):
                    pair[i, j] *= 1.0 + w["fp2.md_ad_shashtashtaka"]
                elif dist in (2, 12):
                    pair[i, j] *= 1.0 + w["fp2.md_ad_dwirdwadasa"]
        comp = (b.chart.planet_lons["Saturn"] + b.chart.planet_lons["Jupiter"]
                + b.chart.planet_lons["Sun"] + b.chart.planet_lons["Moon"]) % 360.0
        return cls(person_id=b.person_id, band=lng.band, longevity=lng,
                   maraka=maraka, pair_factor=pair,
                   moon_sign=b.chart.planet_signs["Moon"],
                   composite_point=comp)

    def band_gate(self, ages: np.ndarray,
                  w: Mapping[str, float] = RAMAN_WEIGHTS_V2) -> np.ndarray:
        def plateau(band: AyuBand) -> float:
            d = abs(int(band) - int(self.band))
            return (w["fp2.gate_in_band"] if d == 0
                    else w["fp2.gate_adjacent"] if d == 1
                    else w["fp2.gate_far"])
        vals = {b_: plateau(b_) for b_ in BAND_RANGE_V2}
        gate = np.full(ages.shape, vals[AyuBand.PURNAYU], dtype=np.float64)
        for b_, (lo, hi) in BAND_RANGE_V2.items():
            m = (ages >= lo) & (ages < hi)
            gate[m] = vals[b_]
        blend = w["fp2.gate_blend_years"]
        if blend > 0:
            for edge, (b_lo, b_hi) in ((32.0, (AyuBand.ALPAYU, AyuBand.MADHYAYU)),
                                       (75.0, (AyuBand.MADHYAYU, AyuBand.PURNAYU))):
                near = np.abs(ages - edge) < blend
                if near.any():
                    t = (ages[near] - (edge - blend)) / (2.0 * blend)
                    gate[near] = vals[b_lo] + (vals[b_hi] - vals[b_lo]) * t
        return gate

    def potency(self, md_idx: np.ndarray, ad_idx: np.ndarray,
                ages: np.ndarray,
                md_frac: np.ndarray | None = None,
                transit_mult: np.ndarray | None = None,
                w: Mapping[str, float] = RAMAN_WEIGHTS_V2) -> np.ndarray:
        base = w["fp2.md"] * self.maraka[md_idx] + w["fp2.ad"] * self.maraka[ad_idx]
        pot = base * self.pair_factor[md_idx, ad_idx] * self.band_gate(ages, w)
        if md_frac is not None:
            sandhi = ((md_frac < w["fp2.sandhi_frac"])
                      | (md_frac > 1.0 - w["fp2.sandhi_frac"]))
            pot = pot * (1.0 + w["fp2.dasha_sandhi"] * sandhi)
        if transit_mult is not None:
            pot = pot * transit_mult
        return pot


# ---------------------------------------------------------------------------
# Raman-frame transit terms (inclusion decided at calibration)
# ---------------------------------------------------------------------------

def transit_multiplier_v2(pm: PotencyModelV2, birth_jd: float,
                          jds: np.ndarray, sat_table,
                          w: Mapping[str, float] = RAMAN_WEIGHTS_V2
                          ) -> np.ndarray:
    """1 + sadesathi-3rd-cycle + composite-point terms, per moment.

    ``sat_table`` must be a Raman-frame IngressTable for Saturn. Sadesathi
    cycle = count of completed entries into the 12th-from-Moon sign since
    birth (from the ingress table). Composite point (HPA p.127): Saturn
    within orb of (Sat+Jup+Sun+Moon natal sum) AND the Saturn cycle index
    since birth matching the band (ALPAYU→1, MADHYAYU→2, PURNAYU→3).
    """
    mult = np.ones(jds.shape, dtype=np.float64)
    sat_sign = sat_table.sign_at(jds)
    h = ((sat_sign - pm.moon_sign) % 12) + 1
    in_ss = (h == 12) | (h == 1) | (h == 2)
    sign_12th = ((pm.moon_sign + 10) % 12) + 1
    entries = sat_table.ingress_jd[sat_table.sign == sign_12th]
    entries = entries[entries >= birth_jd]
    cycle = np.searchsorted(entries, jds, side="right")
    mult += w["tr2.sadesathi_3rd"] * (in_ss & (cycle == 3))
    # composite point: cycle index from Saturn's sidereal period since birth
    sat_cycle = np.floor((jds - birth_jd) / (29.4571 * 365.2425)).astype(int) + 1
    expected = {AyuBand.ALPAYU: 1, AyuBand.MADHYAYU: 2, AyuBand.PURNAYU: 3}[pm.band]
    # sign-level orb proxy: |sat_lon − point| ≤ orb via table signs is too
    # coarse; use the sign containing the point ± orb spill into neighbours.
    point = pm.composite_point
    orb = w["tr2.composite_orb_deg"]
    point_signs = {int(((point + d) % 360.0) // 30) + 1 for d in (-orb, 0.0, orb)}
    on_point = np.isin(sat_sign, list(point_signs))
    mult += w["tr2.composite_point"] * (on_point & (sat_cycle == expected))
    return mult
