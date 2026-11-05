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
        # ★ INVENTED COMPLEMENT REMOVED 2026-09-01. `fortified` read "normal virility /
        # potency". Raman states the position CAUSES impotency, flatly and with no escape
        # clause: "The following planetary positions cause one to be impotent: ... 2. Saturn
        # in the 6th or the 8th house from Venus." (HTJAH-II:425-430). The CONDITION here
        # already encodes the affliction, so the rule only ever fires in the malefic case —
        # yet `_branch` picks `fortified` on a strong karaka, and a chart with Saturn in the
        # 6th/8th from a strong Venus was shown "normal virility", the inverse of Raman's
        # plain sentence. `fortified=None` makes `_branch` surface the afflicted text, which
        # is the handling this corpus already documents at
        # `house_01_lagna/moon_mind.py:147-151` for exactly this shape.
        fortified=None,
        afflicted="impotency — Saturn in the 6th or 8th from Venus",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 430)),
    RuleRecord(
        id="H7.K.2", house=7, signification="coverture", group="from_karaka", kind="evaluable",
        # Two-branch corpus rule (HTJAH-II:374): "malefics in the 4th/8th/12th from
        # Venus, OR Venus hemmed between malefics, the wife will die soon." Owns BOTH
        # branches so the rec.45 hem is not double-counted in `coverture`. (Citation
        # corrected from 368 — the Venus-exaltation line — to 374, the wife-death line.)
        condition=C.Or(_venus(frozenset({4, 8, 12})), C.HemmedBy("Venus", "malefic")),
        # Same invented complement as K.1; same repair. Raman gives no contrary result.
        fortified=None,
        afflicted="wife dies soon — malefics in the 4th/8th/12th from Venus, or Venus hemmed "
                  "between malefics",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 374)),
    RuleRecord(
        id="H7.K.3", house=7, signification="marital_happiness", group="from_karaka", kind="evaluable",
        condition=_venus({7}),
        # Same invented complement as K.1; same repair. Raman gives no contrary result.
        fortified=None,
        afflicted="unhappy marriage — malefics in the 7th from Venus",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 376)),
)
