"""The conflict narrator (synthesis layer S3) — tensions WOVEN, never hidden.

User decision (2026-08-03): conflicts are narrated in one honest sentence naming BOTH
poles and the governing v18 rule, while every underlying section stays fully visible
(REPORT COMPLETENESS and Measured-Truth stand). This module composes those sentences from
tensions the report has ALREADY detected — the most-contested house (preponderance) and
the dashboard-vs-house grain differences (PREC-1). Nothing is re-judged, nothing is
suppressed; a test pins that both poles' verdict words appear in every sentence.

Usage:
    from app.raman_saab.tension_narrator import narrate_tensions
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: dashboard matter -> the house its dedicated reader judges (for the PREC-1 narration).
_MATTER_HOUSE: dict[str, int] = {
    "health": 6, "wealth": 2, "courage": 3, "happiness": 4, "children": 5,
    "enemies": 6, "marriage": 7, "longevity": 8, "fortune": 9, "career": 10,
    "gains": 11, "losses": 12,
}


def narrate_tensions(r: "DetailedReport") -> tuple[str, ...]:
    """One sentence per already-detected tension, both poles named, rule cited."""
    out: list[str] = []

    # 1. the most-contested house (the digest's own tension finding, PREC-3 governs)
    pp = r.preponderance
    mc = getattr(pp, "most_contested", None)
    if mc:
        ht = next((t for t in pp.houses if t.house == mc), None)
        if ht is not None:
            out.append(
                f"House {mc}'s headline reads {ht.verdict}, though its own witnesses "
                f"divide ({ht.favourable} favourable, {ht.adverse} adverse) — the "
                f"headline stands and the division is disclosed, never re-voted "
                f"(PREC-3).")

    # 2. dashboard-vs-house grain differences (PREC-1) — matter verdict vs house rollup
    for en in r.dashboard.entries:
        house = _MATTER_HOUSE.get(en.matter)
        if house is None or len(r.proformas) < house:
            continue
        rollup = r.proformas[house - 1].rollup
        if (en.verdict in ("favourable", "afflicted") and rollup in ("favourable",
                                                                    "afflicted")
                and en.verdict != rollup):
            out.append(
                f"The reading for {en.matter} is {en.verdict} while house {house} as a "
                f"whole reads {rollup} — the matter is judged by its dedicated reader, "
                f"the house by its weakest decided matter, and neither is wrong "
                f"(PREC-1).")

    return tuple(out)
