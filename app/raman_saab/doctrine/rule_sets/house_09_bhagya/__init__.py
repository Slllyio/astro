"""Bhagya / Dharma / Pitru Bhava (father / fortune / dharma / travel) RuleRecords.

Stage-4 split of the former flat `house_09_bhagya.py` into a subpackage (mirrors the
committed H1-H5/H7/H8/H10 splits). Placements moved verbatim; combinations added.
Karaka: Jupiter + Sun (PitruKaraka).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, lord_in_12, planets_in_9th

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_9th.RULES
    + combinations.RULES)
