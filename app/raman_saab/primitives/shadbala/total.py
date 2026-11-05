"""Shadbala total assembly and minimum-required verdict.

Usage:
    from app.raman_saab.primitives.shadbala.total import assemble_shadbala, is_powerful, MIN_REQUIRED

    br = assemble_shadbala(sthana, dig, kala, cheshta, naisargika, drik)
    # br.total is in Shashtiamsas; Rupas = br.total / 60
    powerful = is_powerful("Mercury", br.total / 60)
"""
from __future__ import annotations

from app.raman_saab.chart.model import ShadbalaBreakdown

# Minimum-required total Bhava Bala in Shashtiamsas for a house to count as "strong".
# GOLDEN-TUNED (not a Raman-stated threshold): Raman gives no numeric Bhava-Bala cut-off,
# so this is an engine band chosen to separate well-supported bhavas from weak ones on the
# canonical charts. Bhava Bala = Bhavadhipati (lord total Shadbala) + Bhavadig (0..60) +
# Bhava Drig (signed). A lord meeting ~5-6 Rupas (300-360 Shashtiamsas) plus a middling
# Bhavadig already clears this; document any retune here.
#
# NO LONGER A VERDICT PILLAR (2026-10-23, USER DECISION after the engine audit): 97.5% of
# houses cleared this bar, so its vote was close to a constant "strong". The judge now reads
# ``house_template.BHAVA_BALA_PILLAR_VOTES = False``; this value survives for the report-layer
# readers that still quote it (``doctrine/uk_tripod.py``) and for the tuner.
#
# Consequence for the pillar knobs below: with two voting pillars (lord, karaka) a contradicted
# matter is lifted only when BOTH are strong, and ``CONTRA_PILLAR_AFFLICT = 3`` cannot be
# reached. Before the change it needed the Bhava Bala to be weak as well, which happened in
# ~2.5% of houses, so the afflicted arm was already near-dead; the dusthana clause, the
# navamsa and clauses 4-8 carry the afflictions.
#
# NOTE: deliberately NOT typed ``Final`` — this is a documented golden-tuned knob.
# ``tools/raman_saab/tune_thresholds.py`` rebinds it (under a save/restore context
# manager) while scoring candidate thresholds against the golden corpus.
BHAVA_BALA_MIN_SH: float = 300.0

# Pillar-preponderance knobs for the per-signification contradiction weigh (clause-2 of
# ``judges/house_template._decide``). When BOTH a benefic and a malefic rule fire on a
# matter, the judge no longer counts fired-rule surplus; instead — faithful to Raman's
# THREE-FACTORS doctrine (lord strength, karaka strength, Bhava-Bala strength) — it counts
# how many of the three KNOWN pillars (``lord_strong`` / ``karaka_strong`` /
# ``bhava_bala_strong``, ignoring None) are weak vs strong:
#   * ``weak  >= CONTRA_PILLAR_AFFLICT`` -> 'afflicted' (Raman "factors afflicted");
#   * ``strong >= CONTRA_PILLAR_FAVOUR`` AND D9 does not weaken -> 'favourable';
#   * otherwise                          -> 'mixed'.
#
# GOLDEN-TUNED knobs (NOT ``typing.Final``): ``tools/raman_saab/tune_thresholds.py``
# rebinds them (under a save/restore context manager) while scoring candidate pillar counts
# against the golden corpus. On Track-B sparse charts all pillars are None -> the known set
# is empty -> 'mixed' regardless of the knob.
#
# CALIBRATION 2026-06-14 (Stage-3, user-signed-off "V2"): activated from the no-op 99/99 to
# 3/2 after an isolated CONTRA_PILLAR sweep over the 131-verdict golden corpus. AFFLICT=3
# (all three pillars must be weak to condemn a contradicted matter — strict, because the D9
# down-modulation already catches most afflictions); FAVOUR=2 (a two-pillar strong majority
# lifts a contradicted matter to favourable). The FAVOUR lift is GUARDED in clause-2 by the
# navamsa: it does NOT fire when ``L.navamsa_status == "weakens"`` — a strong-pillar majority
# must not paint over a weakening confirmation-varga (that guard alone protected the H9
# father-death charts + the H2 afflictions from inversion). Net: 54/131 -> 63/131 (+9), zero
# afflicted->favourable inversions; the 7 residual misses are mild mixed->favourable
# over-commitments on borderline charts. A pillar count of 1 is too aggressive (a single
# weak factor amid contradicting evidence should not condemn a matter), so do NOT hand-set
# AFFLICT below 2 without a golden that earns the change.
#
# DOCTRINAL AUTHORITY FOUND 2026-08-24 (bphs-doctrine-reviewer, engine-blind): FAVOUR=2 is no
# longer justified by the sweep alone — it is Raman's own operative threshold for the
# house/lord/karaka triad. The prescriptive statement is HTJAH-I:5729-5730 (Chart No. 96):
# "Since the house and the lord are considerably afflicted, the Karaka's moderately benefic
# disposition SHOULD BE IGNORED." Two pillars against one, both testimonies present, and Raman
# orders the dissenting third discarded — unanimity cannot survive that sentence. Applied in
# the favourable direction on worked charts: HTJAH-I:4856-4858 (Chart 80: karaka considerably
# afflicted, house+lord strong -> "very high official position"), HTJAH-I:4619-4621 (Chart 71),
# HTJAH-I:8493-8518 (Chart 1). Ten negative cases consistent, zero usable counterexamples.
# NOTE: HTJAH-I:2113 ("at least two of the three factors") is NOT the citation for this knob —
# its triad is the Lagna/Sun/Moon body-mind-soul trinity (HTJAH-I:1870-1873) and its consequent
# is whole-life fortune, not a bhava verdict. Recorded because it was nearly cited in error.
#
# AFFLICT=3 vs HTJAH-I:5729 — INVESTIGATED AND RESOLVED 2026-08-25: the tension is in the
# PREDICATE, not the threshold. 5729 condemns at TWO afflicted pillars, which looks like
# AFFLICT should be 2 — but measured per-row, lowering it flips exactly 3 scored verdicts and
# ALL THREE move AWAY from Raman (h11_08 becomes a new favourable->afflicted inversion).
# Meanwhile the condemnations Raman actually makes at two afflicted pillars (e.g. HTJAH-I
# Chart 73: "the lord and Karaka are moderately blemished" -> mother lost) sit on pillars this
# apparatus reads as bala-STRONG — no threshold value can reach them. Raman's "considerably/
# moderately afflicted" is CONTACT-BLEMISH severity; these booleans are BALA-weakness. Two
# different predicates. The knob stays 3 because at 2 the bala-boolean misfires; the real fix
# is the graded strength band (DOCTRINE_BACKLOG, three-valued-band design ticket), which would
# let a bala-strong-but-blemished pillar count toward condemnation the way Raman counts it.
CONTRA_PILLAR_AFFLICT: int = 3
CONTRA_PILLAR_FAVOUR: int = 2

# ── B1 effective-strength affliction weights (Rupas) ─────────────────────────────────────────
# Raman reads a planet's "strength" as its Bala FOLDED WITH the afflictions/dignities he weighs
# alongside it (NH_GAP_ANALYSIS Theme 1): papakartari (hemmed by malefics), a dusthana (6/8/12)
# placement, conjunction with a node, and combustion drag the effective strength DOWN; a dignified
# planet (exalt/own/moolatrikona, or a cancelled debilitation) lifts it UP.
# `judges/house_template._effective_strength` subtracts/adds these weights from the raw total before
# `is_powerful` reads it. ALL DEFAULT TO 0.0 -> the fold is a strict NO-OP and `is_powerful` sees
# the raw Shadbala unchanged (golden ratchet untouched). The holdout-locked threshold tuner
# (tools/raman_saab/tune_thresholds.py) searches these; a nonzero config ships ONLY if it improves
# the fit set WITHOUT dropping the held-out set (the anti-overfit gate). These are golden-tuned
# knobs (like MIN_REQUIRED) — intentionally NOT ``Final`` so the tuner can rebind them live.
EFF_W_PAPAKARTARI: float = 0.0
EFF_W_DUSTHANA: float = 0.0
EFF_W_NODE: float = 0.0
EFF_W_COMBUST: float = 0.0
EFF_W_DIGNITY: float = 0.0

# Minimum-required TOTAL Shadbala in Rupas per planet (GBB-8:303-312, Raman's §122
# "Powerful Planets").
#
# VERIFIED AGAINST THE PRINTED TEXT 2026-08-19 (corpus mounted). All seven match his
# figures exactly: "Ravi is held to be powerful when his Shad Bala Pinda is 5 or more
# Rupas. Chandra becomes strong when his Shad Bala Pinda is 6 or more Rupas. Kuja becomes
# powerful when his Shad Bala Pinda does not fall short of 5 Rupas. Budha becomes potent by
# having his Shad Bala Pinda as 7 Rupas. Guru, Sukra and Sani become thoroughly powerful if
# their Shad Bala Pindas are 6.5, 5.5 and 5 Rupas or more respectively."
#
# THIS CLOSES AN OPEN USER DECISION. The backlog carried "Sun MIN_REQUIRED 5.0 (tuned) vs
# GBB-8:303's printed 6.5 - retune or relabel". There is nothing to decide: 6.5 is GURU's
# figure, not the Sun's. Raman's printed minimum for Ravi IS 5.0 and this table already has
# it. The decision was resting on a misread line.
#
# NO PER-COMPONENT MINIMA EXIST. The backlog also asked for "GBB-8's component requirement
# table" to turn the report's weakest-component pointer into a real per-component verdict.
# Searching all nine imported GBB chapters (2026-08-19) finds no such table: §122 sets a bar
# for the shadbala PINDA - the total - and Raman sets none for sthana/dig/kala/chesta/
# naisargika/drik individually. The pointer therefore stays explicitly arithmetic-only,
# which is how it already ships, and that is now a settled finding rather than a gap.
#
# Also a golden-tuned knob (see BHAVA_BALA_MIN_SH note); intentionally not ``Final``.
MIN_REQUIRED: dict[str, float] = {
    "Sun": 5.0,
    "Moon": 6.0,
    "Mars": 5.0,
    "Mercury": 7.0,
    "Jupiter": 6.5,
    "Venus": 5.5,
    "Saturn": 5.0,
}


def assemble_shadbala(
    sthana: float,
    dig: float,
    kala: float,
    cheshta: float,
    naisargika: float,
    drik: float,
) -> ShadbalaBreakdown:
    """Sum the six components (Shashtiamsas; Drik is signed) into a ShadbalaBreakdown.

    `total` is in Shashtiamsas; divide by 60 for Rupas (GBB-8:262).
    Drik Bala is already signed (negative when net malefic aspects dominate) and
    is added directly — it must not be abs()-ed here.
    """
    total_sh = sthana + dig + kala + cheshta + naisargika + drik
    return ShadbalaBreakdown(
        sthana=sthana,
        dig=dig,
        kala=kala,
        cheshta=cheshta,
        naisargika=naisargika,
        drik=drik,
        total=round(total_sh, 3),
    )


def is_powerful(planet: str, total_rupas: float) -> bool:
    """True iff the planet's total Shadbala (Rupas) meets its minimum required (GBB-8:303)."""
    req = MIN_REQUIRED.get(planet)
    return req is not None and total_rupas >= req
