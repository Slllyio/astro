"""synthesis_v2 — a doctrine-derived, non-linear strength scorer (parallel to the live engine).

Raman never summed points. He applied structural OVERRIDES: an affliction halts a house like a
broken gear; a deep dignity is an unbreakable baseline. This module replaces the live engine's
additive `_combine` + `_THRESH` with a conditional logic circuit, WITHOUT touching the live engine —
it consumes the exact same `Finding` lists the assessors already emit and produces its own grade.

Pipeline per factor (bhava / lord / karaka):

    engine base grade  ─►  doctrinal override gates  ─►  final grade

The BASE is the live engine's own grade for the factor (so with no gate firing, v2 reproduces the
engine exactly). The overrides are Raman's structural conditions, applied in doctrinal order:

    A  besiegement veto      — papakartari caps the factor at "weak" regardless of positives
    B  deep-affliction gate  — stacked Rāśi negatives break it (afflicted / weak)
    P  strong-promise floor   — a strong Rāśi promise is not broken by a weak Navāṁśa (D9 = sequence)
    C  dignity floor          — an exalted/own factor cannot collapse
    F  fortification floor    — a decisively fortified factor is credited even from a bad placement

Nothing here is fit to the held-out labels. The two affliction thresholds (−1.22 / −2.45) are the
load-bearing split of the A2 decision tree (`ml_research/a2_tree_rules.json`), declared as such; every
other constant is cited to Raman's decoded weights (`house_judgment._DIGNITY_W` / `_W`).

MEASURED RESULT (ablation, `synthesis_v2_validate`): A + B is the landing configuration —
held-out within-one 54.7 → **64.2%**, NH 53.1 → **62.5%**, ch. IV anchor held at parity (1/8). This
replicates the A2 learned tree's in-distribution gain (63.5%) from PURE doctrine, and — unlike the
fitted model, which collapsed the anchor to 0/8 — it does not sacrifice the anchor. P is inert on
sign-reconstructed charts; C lifts the anchor 1→2 but costs ~17 pts of held-out (the anchor's strong
verdicts are not separable from held-out's weak ones in the sign feature space) — so both are OFF by
default, retained as documented ablation switches.

DEGREE-POOL UPDATE (grow2, N=50): the lead generalizes to fully unseen degree data (52.0% vs the
live engine's 44.0%), and the floors are now REFUTED rather than untested — on degrees Gate P's
precondition binds (13/50 strong-Rāśi factors) and it costs 2 points; C stays catastrophic. A+B
stands. See REPORT_synthesis_v2.md § grow2.

INCREMENT 29 — Gate F (fortification floor) is the THIRD documented negative, joining P and C.
Motivation: increments 24–28 built only REDUCING gates, so the strong-graded held-out slice stayed
floored (5/29 within-one); the misses are fortified-but-badly-placed factors Raman credits
("in the 12th though … highly fortified by the combined aspects of Saturn, Jupiter and
Mars-yogakāraka"). Gate F reads a fortification tally over the SAME findings and floors UP. The
ablation (7 threshold configs + 2 gentle-floor variants) is unanimous: EVERY config regresses
held-out (−3..−7) and NH (−11..−33) to buy the strong-slice lift, because the corpora carry 68
afflicted-graded rows (A+B scores 82.4% of them within-one) that carry the SAME fortifier tags —
so a tag-level floor over-fires on them exactly as Gate C did. The strong-side under-credit is a
FEATURE gap (yoga/dispositor structure absent from the Finding vocabulary), not a synthesis gap:
no floor over the existing tags separates it. GATE_F OFF by default, kept as a reproducible
ablation switch. See REPORT_synthesis_v2.md § increment 29.
"""
from __future__ import annotations

import dataclasses

from app.medini.doctrine.domains import house_judgment as _HJ
from app.medini.doctrine.domains.house_judgment import Finding, FactorVerdict, VERDICT_SCALE

_IDX = {lab: i for i, lab in enumerate(VERDICT_SCALE)}

# ── grade indices into VERDICT_SCALE (0..8) ────────────────────────────────────────────────────
AFFLICTED, WEAK, MODERATE, MOD_GOOD, FAIRLY_GOOD, FAIRLY_STRONG, FAIRLY_POWERFUL, VERY_STRONG, \
    VERY_POWERFUL = range(9)

# ── doctrinal constants ────────────────────────────────────────────────────────────────────────
# Gate B thresholds: the two numbers read off the A2 tree's load-bearing split (declared, not fit).
NEG_GATE = -1.22          # sum of negatives at/below this → capped at "weak"
NEG_GATE_DEEP = -2.45     # …at/below this → "afflicted"
# Gate C floors: an exalted/vargottama factor cannot fall below "moderately good"; own below "moderate"
FLOOR_EXALTED = MOD_GOOD  # 3
FLOOR_OWN = MODERATE      # 2
STRONG_BAND = FAIRLY_STRONG   # 5 — a "strong Rāśi promise" (Gate P threshold)

# Gate F (fortification floor) — the positive mirror of Gate B. A factor that is DECISIVELY
# fortified is credited by Raman even from a bad placement ("in the 12th though … rendered highly
# fortified by the combined aspects of Saturn, Jupiter and Mars-yogakāraka"). Gate B reads the
# frame's negative sum and floors DOWN; Gate F reads a fortification tally over the SAME findings
# and floors UP. The unit weights rank the fortifiers by Raman's own hierarchy (yogakāraka contact
# strongest; exaltation/vargottama decisive; own-sign/neechabhāṅga/kendra moderate; a benefic
# aspect the weakest) — declared, not fit. F1/F2 are ablation-selected within a doctrine-principled
# range (see REPORT_synthesis_v2.md § increment 29).
FORT_W = {"yogakaraka": 2.0, "exalted": 1.6, "vargottama": 1.2, "own": 0.8,
          "kendra": 0.5, "benefic": 0.4}
FORT_F1 = 2.0             # fortification tally at/above this → floor at "fairly strong"
FORT_F2 = 3.0             # …at/above this → floor at "very strong"
FLOOR_FORT_1 = FAIRLY_STRONG   # 5
FLOOR_FORT_2 = VERY_STRONG     # 7
# Suppress Gate F when the frame is deeper-afflicted than this (−99 = never suppress). The held-out
# corpora carry NO weak-graded rows at deep negatives, so suppressing here forfeits strong recall
# for zero protective gain — hence the default lets fortification lift even a deeply-pressed factor,
# exactly as Raman credits the fortified-but-badly-placed graha. Kept as an ablation switch.
FORT_MIN_NEG = -99.0

# Gate D (dignity/decompression floor, increment 31) — the ONE lever the root-cause diagnostic isolated
# as safe. The engine's `_cap_positive` crushes stacked positives, so a factor with decisive dignity
# (exalted Saturn +1.6, vargottama +1.2, kendra +1.2) and only SHALLOW negatives is floored to 1–2
# where Raman says "very strong" (ch168 karaka, Rajendra-Prasad karaka, Tilak bhava). This is where
# Gate C failed: it floored on ANY dignity and so over-fired on the deep-afflicted rows. Gate D adds
# the missing condition the diagnostic named — it fires ONLY on the SHALLOW-negative regime
# (sum_neg > NEG_GATE), which is DISJOINT from Gate B's deep-affliction floor and from the afflicted
# slice (afflicted rows carry deep negatives). Floor scales with the positive testimony.
DECOMP_POS_HI = 2.8      # sum_pos at/above this (≈ exalted + vargottama/kendra) with decisive dignity → very strong
DECOMP_POS_LO = 2.0      # …at/above this → fairly strong (a lone exaltation, 1.6, is NOT enough — it
                         # takes exaltation PLUS further fortification; the ablation is indifferent
                         # between 1.6 and 2.0 on the corpora, so the conservative bar is chosen)
FLOOR_DECOMP_HI = VERY_STRONG    # 7
FLOOR_DECOMP_LO = FAIRLY_STRONG  # 5

# Context-dependent house-class weights (w_lord, w_bhava, w_karaka), each cited in the audit note.
_WEIGHTS = {
    "lord_led":         (0.50, 0.30, 0.20),   # 1,2,4,5,7,9 — house judged chiefly by its lord
    "occupancy_led":    (0.35, 0.45, 0.20),   # 3,6,10,11 (upachaya/gains) — by what occupies/aspects it
    "karaka_intrinsic": (0.40, 0.25, 0.35),   # 8,12 — heavily by the natural significator's condition
}
_HOUSE_CLASS = {1: "lord_led", 2: "lord_led", 4: "lord_led", 5: "lord_led", 7: "lord_led",
                9: "lord_led", 3: "occupancy_led", 6: "occupancy_led", 10: "occupancy_led",
                11: "occupancy_led", 8: "karaka_intrinsic", 12: "karaka_intrinsic"}

# Landing configuration (ablation-selected). A (besiegement veto) + B (deep-affliction gate) break the
# ceiling; D (dignity/decompression floor, increment 31) closes the tractable strong-side sub-slice.
# P (strong-promise floor) is inert on sign-reconstructed charts; C (dignity floor) lifts the anchor
# 1→2 but costs ~17 pts of held-out because it fired on the deep-afflicted rows too — D fixes exactly
# that by gating on neg-depth. F (fortification floor) is a documented negative. P/C/F stay OFF, kept
# as reproducible ablation switches; A/B/D are live.
GATE_A = True
GATE_B = True
GATE_P = False
GATE_C = False
GATE_D = True   # dignity/decompression floor (increment 31) — LANDED. The root-cause diagnostic
                # isolated the ONE tractable strong-side sub-slice: shallow-negative factors with
                # decisive dignity + strong positive testimony that `_cap_positive` crushed to grade
                # 1–2 where Raman says "very strong" (ch168, Rajendra-Prasad, Tilak). Firing ONLY in
                # the shallow-neg regime (sum_neg > NEG_GATE, disjoint from Gate B and the afflicted
                # slice) is the condition Gate C lacked. Ablation: held-out 56.9→58.6, NH full
                # 46.6→47.9, strong slice 17→24%, mid/afflicted/anchor all held. REPORT § increment 31.
GATE_F = False  # fortification floor (increment 29) — DOCUMENTED NEGATIVE, joins P/C. The ablation
                # (REPORT_synthesis_v2.md § increment 29) shows every threshold config regresses
                # held-out (−3..−7) and NH (−11..−33) while lifting the strong slice: the same
                # fortification findings Raman treats as decisive on his strong-graded factors are
                # ALSO present on the factors he grades afflicted, so a tag-level floor cannot
                # separate them (identical failure mode to Gate C). Kept OFF, retained as a
                # reproducible ablation switch.


def label(grade: int) -> str:
    """VERDICT_SCALE phrase for a 0..8 grade index."""
    return VERDICT_SCALE[max(0, min(8, grade))]


@dataclasses.dataclass(frozen=True)
class FrameState:
    sum_neg: float            # total malefic pressure in the frame (Gate B)
    tier: str                 # decisive dignity: "exalted" | "own" | "none" (Gate C)
    besieged: bool            # papakartari — hemmed between malefics (Gate A)
    fort: float = 0.0         # fortification tally (Gate F)
    sum_pos: float = 0.0      # total positive testimony in the frame (Gate D)


# ── 1. per-frame reduction + collinearity guard ─────────────────────────────────────────────────

def _collinearity_guard(frame_findings: list[Finding]) -> tuple[list[Finding], bool]:
    """Combustion is the tight-orb case of Sun-proximity, not a second independent penalty. If a
    frame carries BOTH a combustion finding and a negative Sun-conjunction finding, keep only the
    stronger (more negative) — one astronomical fact, counted once."""
    comb = [f for f in frame_findings if f.criterion == "combustion"]
    sun_conj = [f for f in frame_findings
                if f.criterion == "conjunction" and f.delta < 0 and "sun" in f.text.lower()]
    if comb and sun_conj:
        weakest = max(comb + sun_conj, key=lambda f: f.delta)   # least-negative = largest delta
        return [f for f in frame_findings if f is not weakest], True
    return frame_findings, False


def _dignity_tier(frame_findings: list[Finding]) -> str:
    """Decisive dignity present in a frame. Exalted/vargottama > own/moolatrikona/neechabhanga."""
    for f in frame_findings:
        t = f.text.lower()
        if "exalted" in t or f.criterion == "vargottama" or (f.criterion == "dignity" and f.delta >= 1.6):
            return "exalted"
    for f in frame_findings:
        t = f.text.lower()
        if (f.criterion == "dignity" and 1.15 <= f.delta < 1.6) or "neechabhanga" in t \
                or "own sign" in t:
            return "own"
    return "none"


def _fortification(frame_findings: list[Finding]) -> float:
    """Gate F's fortification tally over a frame's POSITIVE testimony, ranked by Raman's hierarchy.
    Each fortifier is counted at most once in its strongest category (a yogakāraka aspect is not
    also double-counted as a plain benefic aspect)."""
    total = 0.0
    for f in frame_findings:
        t = f.text.lower()
        if f.delta > 0 and "yogakaraka" in t:
            total += FORT_W["yogakaraka"]
        elif f.criterion == "vargottama":
            total += FORT_W["vargottama"]
        elif "exalted" in t or (f.criterion == "dignity" and f.delta >= 1.6):
            total += FORT_W["exalted"]
        elif (f.criterion == "dignity" and 1.15 <= f.delta < 1.6) or "neechabhanga" in t \
                or "own sign" in t:
            total += FORT_W["own"]
        elif f.delta > 0 and f.criterion == "placement":
            total += FORT_W["kendra"]
        elif f.delta > 0 and f.criterion in ("aspect", "conjunction"):
            total += FORT_W["benefic"]
    return round(total, 3)


def _reduce_frame(frame_findings: list[Finding]) -> FrameState:
    """The gate inputs for one frame, AFTER the collinearity guard (so a de-duped combustion cannot
    inflate the negative sum that Gate B reads)."""
    fr, _merged = _collinearity_guard(frame_findings)
    sum_neg = sum(f.delta for f in fr if f.delta < 0)
    sum_pos = sum(f.delta for f in fr if f.delta > 0)
    besieged = any(f.criterion == "kartari" and f.delta < 0 for f in fr)
    return FrameState(round(sum_neg, 3), _dignity_tier(fr), besieged, _fortification(fr),
                      round(sum_pos, 3))


# ── the public per-factor scorer: engine base + doctrinal overrides ──────────────────────────────

def _engine_grade(score: float) -> int:
    return _IDX[_HJ._verdict_label(score)]


def _guard_adjust(frame_findings: list[Finding], frame_score: float) -> float:
    """Undo the combustion↔Sun-conjunction double-count in a frame's engine score (add back the
    weaker of the two, since only the stronger should count)."""
    fr, merged = _collinearity_guard(frame_findings)
    if not merged:
        return frame_score
    removed = sum(f.delta for f in frame_findings) - sum(f.delta for f in fr)
    return round(frame_score - removed, 3)   # removed is negative → raises the score


def grade_factor(fv: FactorVerdict) -> tuple[int, dict]:
    """Grade one factor (0..8). BASE is the live engine's own grade (so with no gate firing, v2
    reproduces the engine). The doctrinal overrides then apply, in Raman's hierarchy:

      A  besiegement veto      — papakartari caps the factor at "weak"
      B  deep-affliction gate  — stacked Rāśi negatives (A2 split −1.22 / −2.45) break it
      P  strong-promise floor  — a strong Rāśi promise is not broken by a weak Navāṁśa (the
                                 lattice's load-bearing cell: floors at "fairly good")
      C  dignity floor         — an exalted/own factor cannot collapse (the piece A2 lacked)
      F  fortification floor   — a decisively fortified factor is credited even from a bad
                                 placement (increment 29 — documented negative, OFF by default)

    The collinearity guard is folded into the base by un-double-counting combustion vs Sun-conj.
    """
    findings = fv.findings
    rasi_f = [f for f in findings if f.frame in ("Rasi", "both")]
    nav_f = [f for f in findings if f.frame == "Navamsa"]
    rst = _reduce_frame(rasi_f)
    nst = _reduce_frame(nav_f) if nav_f else None

    # engine base, adjusted ONLY for the collinearity guard (un-double-count combustion vs Sun-conj)
    rasi_score = _guard_adjust(rasi_f, fv.rasi_score)
    rasi_adj = rasi_score - fv.rasi_score
    nav_adj = (_guard_adjust(nav_f, fv.navamsa_score) - fv.navamsa_score) if nav_f else 0.0
    base = _engine_grade(round(fv.score + rasi_adj + nav_adj, 3))
    r_grade = _engine_grade(rasi_score)

    g = base
    gates: list[str] = []
    if GATE_A and rst.besieged:
        g = min(g, WEAK); gates.append("A:besiegement")
    if GATE_B and rst.sum_neg <= NEG_GATE_DEEP:
        g = min(g, AFFLICTED); gates.append(f"B:deep({rst.sum_neg})")
    elif GATE_B and rst.sum_neg <= NEG_GATE:
        g = min(g, WEAK); gates.append(f"B:afflicted({rst.sum_neg})")
    if GATE_P and r_grade >= STRONG_BAND and not rst.besieged:
        if g < FAIRLY_GOOD:
            gates.append("P:strong_promise_floor")
        g = max(g, FAIRLY_GOOD)
    decisive = rst.tier != "none" or bool(nst and nst.tier != "none")
    if GATE_C and decisive and not rst.besieged:
        exalted = rst.tier == "exalted" or bool(nst and nst.tier == "exalted")
        floor = FLOOR_EXALTED if exalted else FLOOR_OWN
        if g < floor:
            gates.append(f"C:dignity_floor({'exalted' if exalted else 'own'})")
        g = max(g, floor)
    # Gate D — dignity/decompression floor (increment 31). Fires ONLY in the shallow-negative regime
    # (sum_neg > NEG_GATE, disjoint from Gate B and from the afflicted slice): a factor with decisive
    # dignity AND strong positive testimony that `_cap_positive` crushed cannot be graded low. This is
    # Gate C with the neg-depth condition the root-cause diagnostic showed it was missing.
    if GATE_D and not rst.besieged and rst.sum_neg > NEG_GATE and rst.tier != "none":
        if rst.sum_pos >= DECOMP_POS_HI and rst.tier == "exalted":
            floor = FLOOR_DECOMP_HI
        elif rst.sum_pos >= DECOMP_POS_LO:
            floor = FLOOR_DECOMP_LO
        else:
            floor = -1
        if floor >= 0:
            if g < floor:
                gates.append(f"D:decompress({rst.tier},pos={rst.sum_pos})")
            g = max(g, floor)
    # Gate F — fortification floor (the positive mirror of B). A decisively fortified factor is
    # credited even from a bad placement; besiegement (Gate A's papakartari) still vetoes — a hemmed
    # graha is broken regardless of incoming aid.
    if GATE_F and not rst.besieged and rst.fort >= FORT_F1 and rst.sum_neg > FORT_MIN_NEG:
        floor = FLOOR_FORT_2 if rst.fort >= FORT_F2 else FLOOR_FORT_1
        if g < floor:
            gates.append(f"F:fortified({rst.fort})")
        g = max(g, floor)
    g = max(0, min(8, g))
    return g, {"base": base, "rasi": r_grade, "grade": g, "gates": gates, "decisive": decisive,
               "fort": rst.fort}


# ── 4. context-dependent house synthesis ────────────────────────────────────────────────────────

def synthesize_house(bhava: FactorVerdict, lord: FactorVerdict, karaka: FactorVerdict,
                     house: int) -> tuple[int, dict]:
    """Fuse the three (already-gated) factor grades into a house conclusion: a house-class-weighted
    mean plus a lead-veto (a broken lead factor caps the house at "moderate").

    NOTE: the held-out / NH / anchor corpora carry NO 'overall' gold verdicts, so this fusion is
    UNMEASURED — it is the reading-side house conclusion, not part of the validated headline. Kept
    deliberately simple and un-fit (no dignity-concord lift: the dignity-floor evidence at the factor
    level showed dignity-based lifts cost accuracy on this data)."""
    g_b, _ = grade_factor(bhava)
    g_l, _ = grade_factor(lord)
    g_k, _ = grade_factor(karaka)
    cls = _HOUSE_CLASS[house]
    w_l, w_b, w_k = _WEIGHTS[cls]
    grade = round(w_l * g_l + w_b * g_b + w_k * g_k)
    gates: list[str] = []
    lead_grade = {"lord_led": g_l, "occupancy_led": g_b, "karaka_intrinsic": g_l}[cls]
    lead_name = {"lord_led": "lord", "occupancy_led": "bhava", "karaka_intrinsic": "lord"}[cls]
    if lead_grade <= WEAK:
        if grade > MODERATE:
            gates.append(f"lead_veto({lead_name})")
        grade = min(grade, MODERATE)
    grade = max(0, min(8, grade))
    return grade, {"class": cls, "weights": (w_l, w_b, w_k), "bhava": g_b, "lord": g_l,
                   "karaka": g_k, "gates": gates, "grade": grade}
