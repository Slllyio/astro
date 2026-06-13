"""House 5 (Putra Bhava — children / intellect / poorvapunya) RuleRecords.

Stage-4 split of the former single module `house_05_putra.py` into a subpackage
(mirrors the committed H1/H2/H3/H4/H7/H8/H10 splits). Each submodule exposes its
own `RULES` tuple; this aggregate preserves the original ordering (the pre-split 21
placement rules first: lord-in-12 then planets-in-5th), followed by the
"Important Combinations" expansion. Import path unchanged.

Karaka = Jupiter (Putra-Karaka). Children/progeny verdicts pass through the
Beeja/Kshetra fertility gate (judges/house_template.py).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, lord_in_12, planets_in_5th

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_5th.RULES
    + combinations.RULES)
