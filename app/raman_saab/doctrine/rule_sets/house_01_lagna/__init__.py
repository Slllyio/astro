"""House 1 (Tanu Bhava / Lagna — self, body, personality) RuleRecords.

Stage-1 split of the former single module `house_01_lagna.py` into a subpackage.
Each submodule exposes its own `RULES` tuple; this aggregate preserves the
original ordering (the pre-split 21 rules first: lord-in-12 then planets-in-1st),
followed by the Stage-1 expansion groups (currently empty stubs). The package
import path is unchanged — `from app.raman_saab.doctrine.rule_sets import
house_01_lagna` still exposes `RULES` exactly as before.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rule_sets.house_01_lagna import (
    combinations_core, combinations_misc, constitution, lord_in_12, moon_mind,
    navamsa_qualifiers, planets_in_1st, sign_afflictions)
from app.raman_saab.doctrine.rules import RuleRecord

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_1st.RULES
    + combinations_core.RULES
    + navamsa_qualifiers.RULES
    + constitution.RULES
    + moon_mind.RULES
    + sign_afflictions.RULES
    + combinations_misc.RULES)
