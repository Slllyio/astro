"""House 2 (Dhana — wealth) rule-set subpackage.

Aggregates lord-in-12, planets-in-2nd, and (future) combination rules
into a single ``RULES`` tuple consumed by the rule-set registry.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.rules import RuleRecord

from . import combinations, lord_in_12, planets_in_2nd

RULES: Final[tuple[RuleRecord, ...]] = (
    lord_in_12.RULES
    + planets_in_2nd.RULES
    + combinations.RULES
)
