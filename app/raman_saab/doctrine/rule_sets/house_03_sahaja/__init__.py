"""House 3 (Sahaja / Bhratru Bhava — younger siblings / courage) RuleRecords.

Stage-1 split of the former single module `house_03_sahaja.py` into a subpackage
(mirrors the committed `house_01_lagna/` split). Each submodule exposes its own
`RULES` tuple; this aggregate preserves the original ordering (the pre-split 21
rules first: lord-in-12 then planets-in-3rd), followed by the "Important
Combinations" expansion. The package import path is unchanged — `from
app.raman_saab.doctrine.rule_sets import house_03_sahaja` still exposes `RULES`.

Karaka = Mars (Kuja / Bhratru-Karaka). The 3rd is the house of YOUNGER siblings;
the elder brother is read from the 11th (HTJAH-I:3444-3445).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rule_sets.house_03_sahaja import (
    combinations, lord_in_12, planets_in_3rd)
from app.raman_saab.doctrine.rules import RuleRecord

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_3rd.RULES
    + combinations.RULES)
