"""Special-grid doctrine lookups for the Raman Saab engine.

Each module is pure DATA — frozen records with per-row ``Citation``s into the
on-disk corpus — plus one accessor. The grids are returned as metadata by the
house judges (doctrinal review promotion #6); no scoring logic lives here.

Modules:
    decanate_cause       H8  — 22nd-drekkana decanate -> cause of death (fallback)
    source_of_gains      H11 — planet-in-11th / 2nd-lord placement -> income channel
    bhavartha_ratnakara  H12 — karaka-in-12th inversion (fortunate re karaka's bhava)
    confinement_modes    H12 — Bandhana mode of captivity by rising sign
    disease_map          H6  — planet -> organ / tridosha / season of appearance
"""
from __future__ import annotations

from app.raman_saab.doctrine.lookups.bhavartha_ratnakara import (
    KARAKA_IN_12_INVERSIONS,
    karaka_in_12_inversion,
)
from app.raman_saab.doctrine.lookups.confinement_modes import (
    CONFINEMENT_MODES,
    confinement_mode,
)
from app.raman_saab.doctrine.lookups.decanate_cause import (
    DECANATE_CAUSES,
    cause_of_death_fallback,
)
from app.raman_saab.doctrine.lookups.disease_map import (
    PLANET_ORGANS,
    PLANET_SEASONS,
    PLANET_TRIDOSHAS,
    organ_of,
    season_of,
    tridosha_of,
)
from app.raman_saab.doctrine.lookups.source_of_gains import (
    PLANET_IN_11TH_GAINS,
    SECOND_LORD_HOUSE_GAINS,
    gains_via_second_lord,
    source_of_gains,
)

__all__ = [
    "CONFINEMENT_MODES",
    "DECANATE_CAUSES",
    "KARAKA_IN_12_INVERSIONS",
    "PLANET_IN_11TH_GAINS",
    "PLANET_ORGANS",
    "PLANET_SEASONS",
    "PLANET_TRIDOSHAS",
    "SECOND_LORD_HOUSE_GAINS",
    "cause_of_death_fallback",
    "confinement_mode",
    "gains_via_second_lord",
    "karaka_in_12_inversion",
    "organ_of",
    "season_of",
    "source_of_gains",
    "tridosha_of",
]
