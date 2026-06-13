"""House 4 (Sukha / Bandhu Bhava — mother / home / vehicles / lands / happiness).

Stage-4 split of the former single module `house_04_sukha.py` into a subpackage
(mirrors the committed H1/H2/H3/H7/H8/H10 splits). Each submodule exposes its own
`RULES` tuple; this aggregate preserves the original ordering (the pre-split 21
placement rules first: lord-in-12 then planets-in-4th), followed by the
"Important Combinations" expansion. Import path unchanged.

Karaka: Moon (mother), Venus (vehicles), Mars (property), Jupiter (happiness/
education). Mother-death rules here are NOT longevity-guarded.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, lord_in_12, planets_in_4th

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_4th.RULES
    + combinations.RULES)
