"""House 10 (Karma / Rajya Bhava — profession / status / authority) RuleRecords.

Stage-4 split of the former single module `house_10_karma.py` into a subpackage
(mirrors the committed H1/H2/H3/H7/H8 splits). Each submodule exposes its own
`RULES` tuple; this aggregate preserves the original ordering (the pre-split 21
placement rules first: lord-in-12 then planets-in-10th), followed by the
"Important Combinations" expansion. Import path unchanged.

Karaka: Sun (primary, authority/status), with Mercury/Jupiter/Saturn secondary.
Special varga: D10 Dasamsa (career); D9 Navamsa overlay throughout.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, lord_in_12, planets_in_10th

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_10th.RULES
    + combinations.RULES)
