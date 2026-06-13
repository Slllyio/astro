"""House 7 (Kalatra — spouse/marriage) — from-Karaka (Venus-as-Lagna) RuleRecords.

The three rules Raman reads FROM VENUS as if Venus were a Lagna (HTJAH-II:225,
368-430). Moved verbatim from the former flat ``house_07_kalatra.py`` during the
Stage-4 subpackage split.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


def _venus(houses: frozenset[int]) -> C.Condition:
    return C.ClassInHouseFrom("malefic", "Venus", houses)


RULES: Final[tuple[RuleRecord, ...]] = (
    # — from-Karaka (Venus) combinations —
    RuleRecord(
        id="H7.K.1", house=7, signification="virility", group="from_karaka", kind="evaluable",
        condition=C.Or(C.InHouseFrom("Saturn", "Venus", 6), C.InHouseFrom("Saturn", "Venus", 8)),
        fortified="normal virility / potency",
        afflicted="impotency — Saturn in the 6th or 8th from Venus",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 430)),
    RuleRecord(
        id="H7.K.2", house=7, signification="coverture", group="from_karaka", kind="evaluable",
        # Two-branch corpus rule (HTJAH-II:374): "malefics in the 4th/8th/12th from
        # Venus, OR Venus hemmed between malefics, the wife will die soon." Owns BOTH
        # branches so the rec.45 hem is not double-counted in `coverture`. (Citation
        # corrected from 368 — the Venus-exaltation line — to 374, the wife-death line.)
        condition=C.Or(_venus(frozenset({4, 8, 12})), C.HemmedBy("Venus", "malefic")),
        fortified="long-lived partner",
        afflicted="wife dies soon — malefics in the 4th/8th/12th from Venus, or Venus hemmed "
                  "between malefics",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 374)),
    RuleRecord(
        id="H7.K.3", house=7, signification="marital_happiness", group="from_karaka", kind="evaluable",
        condition=_venus({7}),
        fortified="harmonious marriage",
        afflicted="unhappy marriage — malefics in the 7th from Venus",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 376)),
)
