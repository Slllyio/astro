"""LLM narrative + 4-critic adversarial verification on top of the
integrated reading.

The integrated reading is ~1 MB of structured JSON. This module composes
it into a polished, doctrine-grounded narrative — then immediately runs 4
adversarial critics that try to REFUTE each claim before it ships:

- BPHS purist     — does this match canonical doctrine?
- Skeptic         — is this claim plausible-but-wrong?
- Modern translator — does this apply to 2026 life context?
- Contradiction hunter — does this contradict another claim?

Only claims that survive >= 3 of 4 critics are kept. Claims that fail
two or more critics are flagged with the critics' verdicts attached.

Public surface
--------------
- ``compose_narrative(reading, *, llm=None)`` -> ``NarrativeOutput``
- ``run_critics(narrative, reading, *, llm=None)`` -> ``CriticReview``
- ``narrate_and_verify(reading, *, llm=None)`` -> ``VerifiedNarrative``

If ``llm`` is None, ``StubClient`` is used (canned response) so tests +
offline usage work without API keys / Ollama running.
"""

from __future__ import annotations

from app.integration.narrative.composer import (
    DomainNarrative,
    NarrativeOutput,
    compose_narrative,
)
from app.integration.narrative.critics import (
    CriticReview,
    CriticVerdict,
    run_critics,
)
from app.integration.narrative.synthesizer import (
    VerifiedClaim,
    VerifiedNarrative,
    narrate_and_verify,
)

__all__ = [
    "DomainNarrative",
    "NarrativeOutput",
    "compose_narrative",
    "CriticReview",
    "CriticVerdict",
    "run_critics",
    "VerifiedClaim",
    "VerifiedNarrative",
    "narrate_and_verify",
]
