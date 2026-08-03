"""The Raman Style Writer — the pipeline's named final transform for synthesis prose.

Six rules, from Raman's own compositional habits (and the user's phase-10 spec), bounded
by the LLM guard's wording tripwire:

1. Start with the first impression (the ruler/dominant planet opens, HTJAH-I:16001).
2. Speak decisively — but DESCRIPTIVELY: verdict words and the classical indication idiom,
   never decree/forecast language (`_FORBIDDEN_RE` is the hard boundary).
3. Weigh evidence before concluding (name the witnesses before the verdict word).
4. Mention causes before results ("Because X..., the readings there...").
5. Never merely list combinations — every enumeration gets a governing clause.
6. End each unit with a "Conclusion:" sentence.

These helpers are the shared implementation; a builder that composes synthesis prose
should reach for them rather than re-writing the shapes. Everything returned is
guard-safe by test (`tests/raman_saab/test_raman_style.py`).

Usage:
    from app.raman_saab.raman_style import because, conclusion, weighed
"""
from __future__ import annotations


def because(cause: str, result: str) -> str:
    """Rule 4 — cause before result, one sentence."""
    cause = cause.rstrip(".")
    result = result.rstrip(".")
    return f"Because {cause}, {result}."


def weighed(witnesses: str, verdict_clause: str) -> str:
    """Rule 3 — the evidence named first, the verdict word after it."""
    witnesses = witnesses.rstrip(".")
    verdict_clause = verdict_clause.rstrip(".")
    return f"Weighing {witnesses}, {verdict_clause}."


def governed_list(items: tuple[str, ...], governing_clause: str) -> str:
    """Rule 5 — an enumeration is never bare; the governing clause frames it."""
    governing_clause = governing_clause.rstrip(".")
    return f"{governing_clause}: {', '.join(items)}."


def conclusion(statement: str) -> str:
    """Rule 6 — the closing sentence of a unit, always descriptive."""
    statement = statement.rstrip(".")
    return f"Conclusion: {statement}."
