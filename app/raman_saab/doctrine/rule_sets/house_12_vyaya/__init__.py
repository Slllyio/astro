"""Vyaya Bhava (loss / expenditure / moksha) RuleRecords.

Stage-4 split of the former flat `house_12_vyaya.py` into a subpackage (mirrors the
committed H1-H5/H7/H8/H10 splits). Placements moved verbatim; combinations added.
Karaka: Saturn / Ketu.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, lord_in_12, planets_in_12th

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_12th.RULES
    + combinations.RULES)
