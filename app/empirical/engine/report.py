"""The product surface — per-claim disclosure, and the honest empty state.

Two rules govern every string this module produces.

**A claim discloses its own information content.** Never "your chart says X".
Always: among N people with birth times of a stated quality, the feature raised
an observed rate from a% to b%, the association was measured in a named corpus,
and it may not transfer to the reader. The delta over the chartless twin is
stated because a raw statistic overstates what was found.

**A null is rendered, not hidden.** When nothing survives, the surface shows what
was tested, which controls each test faced, and what the result was — so a reader
can tell "we looked hard and found nothing" apart from "we did not look". On the
corpus acquired so far this is the live path, not a fallback.

No prose beyond the claims. This module renders measurements; it does not
interpret, advise, or predict, and there is no model call anywhere in it.

Usage:
    from app.empirical.engine.report import render, to_markdown
    payload = render(survivor_set)
"""

from __future__ import annotations

import logging
from typing import Any, Final

from app.empirical.engine.survivors import Claim, SurvivorSet

logger = logging.getLogger(__name__)

__all__ = ["FRAMING", "render", "to_markdown", "claim_sentence"]

#: Attached to every response. The engine is a measurement instrument reporting
#: associations in a named corpus — not a predictor of anyone's life.
FRAMING: Final[str] = (
    "This engine reports associations measured in a named corpus of historical "
    "people. Every claim is stated as its advantage over a baseline that knows "
    "only birthplace and birth date, because that baseline alone is already "
    "strongly predictive. An association measured in a population may not "
    "transfer to any individual. This is not a prediction about you."
)

#: Shown when nothing survived. States the null as a result with its own content.
_NULL_HEADLINE: Final[str] = (
    "No astrological feature has beaten a birthplace-and-date baseline on this "
    "corpus. This is a measured result, not an absence of measurement."
)

_SCREENING_CAVEAT: Final[str] = (
    "These are screening results. Screening decides what is worth confirming; it "
    "does not establish anything. The held-out data has not been read, and no "
    "pre-registration row has been locked, so nothing here is a finding."
)


def claim_sentence(claim: Claim) -> str:
    """One claim, phrased so its information content is visible in the sentence."""
    base_pct = claim.base_rate * 100.0
    lifted_pct = min(1.0, claim.base_rate + claim.delta) * 100.0
    return (
        f"Among {claim.n:,} people with verified birth times, {claim.feature_bank} "
        f"features raised the observed rate of {claim.target} from {base_pct:.1f}% "
        f"to {lifted_pct:.1f}% (calibrated), an advantage of {claim.delta:+.3f} over "
        f"birthplace and birth date alone "
        f"(95% CI {claim.ci_low:+.3f} to {claim.ci_high:+.3f}, p={claim.p_value:.4g}). "
        f"Applies to roughly {claim.coverage * 100:.0f}% of people. "
        f"Association measured in historical-record data; it may not transfer to you."
    )


def render(survivor_set: SurvivorSet) -> dict[str, Any]:
    """The full response payload — claims if any, the null if not.

    Both branches carry ``framing``, ``tested`` and ``controls``: a reader gets
    the same disclosure whether the answer is a claim or a null.
    """
    payload: dict[str, Any] = {
        "framing": FRAMING,
        "corpus": survivor_set.corpus,
        "corpus_hash": survivor_set.corpus_hash,
        "stage": survivor_set.stage,
        "shippable": survivor_set.is_shippable,
        "controls_every_test_faced": list(survivor_set.controls),
        "tests_run": len(survivor_set.tested),
        "tested": [dict(t) for t in survivor_set.tested],
        "generated_from": survivor_set.generated_from,
    }

    if not survivor_set.is_shippable:
        payload["result"] = "screening_only"
        payload["headline"] = _NULL_HEADLINE if survivor_set.is_empty else _SCREENING_CAVEAT
        payload["caveat"] = _SCREENING_CAVEAT
        payload["claims"] = []
        payload["n_claims"] = 0
        return payload

    if survivor_set.is_empty:
        payload["result"] = "null"
        payload["headline"] = _NULL_HEADLINE
        payload["claims"] = []
        payload["n_claims"] = 0
        return payload

    payload["result"] = "claims"
    payload["headline"] = (
        f"{len(survivor_set.claims)} association(s) survived the full protocol on this corpus."
    )
    payload["claims"] = [
        {
            "test_id": c.test_id,
            "feature_bank": c.feature_bank,
            "target": c.target,
            "delta": c.delta,
            "ci": [c.ci_low, c.ci_high],
            "p_value": c.p_value,
            "n": c.n,
            "base_rate": c.base_rate,
            "coverage": c.coverage,
            "statement": claim_sentence(c),
            "calibration": [
                {
                    "score_low": b.score_low,
                    "score_high": b.score_high,
                    "observed_rate": b.observed_rate,
                    "n": b.n,
                }
                for b in c.calibration
            ],
        }
        for c in survivor_set.claims
    ]
    payload["n_claims"] = len(survivor_set.claims)
    return payload


def to_markdown(survivor_set: SurvivorSet) -> str:
    """Human-readable rendering of the same payload, losing nothing.

    Every field the JSON carries appears here too — the null path included.
    """
    payload = render(survivor_set)
    lines: list[str] = ["# Empirical engine — measured associations", ""]
    lines.append(f"**{payload['headline']}**")
    lines.append("")
    lines.append(FRAMING)
    lines.append("")
    lines.append(f"- Corpus: `{payload['corpus'] or 'unnamed'}` (`{payload['corpus_hash'] or 'no hash'}`)")
    lines.append(f"- Stage: `{payload['stage']}` — shippable: `{payload['shippable']}`")
    lines.append(f"- Tests run: {payload['tests_run']}")
    lines.append(f"- Claims served: {payload['n_claims']}")
    if payload.get("caveat"):
        lines.extend(["", f"> {payload['caveat']}"])

    if payload["claims"]:
        lines.extend(["", "## Claims", ""])
        for claim in payload["claims"]:
            lines.append(f"### {claim['test_id']}")
            lines.append("")
            lines.append(claim["statement"])
            lines.append("")
            if claim["calibration"]:
                lines.append("| score range | observed rate | n |")
                lines.append("|---|---:|---:|")
                for b in claim["calibration"]:
                    lines.append(
                        f"| {b['score_low']:.2f}–{b['score_high']:.2f} "
                        f"| {b['observed_rate'] * 100:.1f}% | {b['n']} |"
                    )
                lines.append("")

    if payload["controls_every_test_faced"]:
        lines.extend(["", "## Controls every test faced", ""])
        for control in payload["controls_every_test_faced"]:
            lines.append(f"- `{control}`")

    if payload["tested"]:
        lines.extend(["", "## What was tested", ""])
        lines.append("Shown in full, including the tests that found nothing —")
        lines.append("a null is only readable if the search behind it is visible.")
        lines.append("")
        for entry in payload["tested"]:
            bits = ", ".join(f"{k}={v}" for k, v in entry.items() if k != "outcome")
            lines.append(f"- **{entry.get('outcome', 'tested')}** — {bits}")

    return "\n".join(lines) + "\n"
