"""House 8 (Ayur / Randhra / Mrityu Bhava — longevity / death) RuleRecords.

Stage-4 split of the former single module `house_08_ayur.py` into a subpackage
(mirrors the committed `house_01_lagna/`, `house_02_dhana/`, `house_03_sahaja/`
splits). Each submodule exposes its own `RULES` tuple; this aggregate preserves
the original ordering (the pre-split 21 placement rules first: lord-in-12 then
planets-in-8th), followed by the "Important Combinations" expansion. The package
import path is unchanged — `from app.raman_saab.doctrine.rule_sets import
house_08_ayur` still exposes `RULES`.

Karaka = Saturn (Ayushkaraka AND Mrutyukaraka simultaneously, HTJAH-II:4606).
Death/manner/cause/place rules carry `signification="death"` and the placements
`"longevity"` — both LONGEVITY_GUARD-clamped until the Phase-E longevity engine.
The non-guarded, measurable matters are `legacies` and `sudden_gains`.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, lord_in_12, planets_in_8th

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_8th.RULES
    + combinations.RULES)
