"""House 7 (Kalatra / Yuvati Bhava — spouse / marriage) RuleRecords.

Stage-4 split of the former single module `house_07_kalatra.py` into a subpackage
(mirrors the committed `house_01_lagna/`, `house_02_dhana/`, `house_03_sahaja/`,
`house_08_ayur/` splits). Each submodule exposes its own `RULES` tuple; this
aggregate preserves the original ordering (the pre-split 24 rules first:
from-karaka, lord-in-12, planets-in-7th), followed by the "Important Combinations"
expansion. Import path unchanged — `from app.raman_saab.doctrine.rule_sets import
house_07_kalatra` still exposes `RULES`.

Karaka = Venus (Kalatra-Karaka), judged AS A LAGNA (HTJAH-II:225). The 7th is also
a MARAKA house — death/widowhood logic recurs (coverture signification).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, from_karaka, lord_in_12, planets_in_7th

RULES: Final[tuple[RuleRecord, ...]] = (
    from_karaka.RULES
    + lord_in_12.RULES
    + planets_in_7th.RULES
    + combinations.RULES)
