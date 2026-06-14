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
CONTRA_PILLAR_AFFLICT: int = 3
CONTRA_PILLAR_FAVOUR: int = 2

# Minimum-required total Shadbala in Rupas per planet (GBB-8:303-312).
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
