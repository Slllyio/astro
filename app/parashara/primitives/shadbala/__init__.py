"""Shadbala — the six-fold planetary strength (BPHS ch.27). COMPLETE.

Built component by component, in Parashara's units (60 virupas = 1 rupa). All six balas are encoded
from ch.27 and fully computable from a chart:

  * **Sthana bala** (positional)   — `sthana`     — 5 sub-components (Uchcha, Saptavargaja,
        Ojhayugmarasiamsa, Kendradi, Drekkana)
  * **Dig bala** (directional)     — `dig`
  * **Naisargika bala** (natural)  — `naisargika`
  * **Cheshta bala** (motional)    — `cheshta`    — from planetary speed/retrogression
  * **Drik bala** (aspectual)      — `drik`       — benefic/malefic-weighted drishti; may be NEGATIVE
  * **Kala bala** (temporal)       — `kala`       — 8 sub-components (Nathonnata, Paksha, Tribhaga,
        Varsha, Masa, Vara, Hora, Ayana), from the birth's sunrise/calendar context

`total.partial_shadbala` sums all six and reports `complete=True`. (Its name is historical — the
result is the full six-fold Shadbala, not a partial.)
"""
from __future__ import annotations

VIRUPAS_PER_RUPA = 60.0
