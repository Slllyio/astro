"""Shadbala — the six-fold planetary strength (BPHS ch.27).

Built component by component, in Parashara's units (60 virupas = 1 rupa). Encoded so far, all from
ch.27 and fully computable from a chart:

  * **Naisargika bala** (natural)      — `naisargika` — complete
  * **Dig bala** (directional)         — `dig`       — complete
  * **Sthana bala** (positional)       — `sthana`    — complete (all 5 sub-components:
        Uchcha, Saptavargaja, Ojhayugmarasiamsa, Kendradi, Drekkana)

`total.partial_shadbala` sums these THREE balas and reports `complete=False`, because the full
Shadbala is SIX. The remaining three — **Kala** (temporal: needs birth-time precision — vara/hora
lords, paksha, tribhaga), **Cheshta** (motional: needs planetary speed/retrogression), **Drik**
(aspectual: needs benefic/malefic-weighted drishti) — are the next component tranche and are NOT
folded into a number that would masquerade as a six-fold total.
"""
from __future__ import annotations

VIRUPAS_PER_RUPA = 60.0
