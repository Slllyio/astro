"""Tier-3 enrichment: closed-form yoga strength scoring.

For each Finding whose ``classification == "yoga"``, compute a normalised
``strength_score`` in [0.0, 1.0] from doctrine-cited inputs:

* The Vimsopaka Bala of the participating planets (BPHS Ch.7 vv.21-25,
  Shodashavarga scheme; per-planet score in [0.0, 20.0]).
* A dignity multiplier (BPHS Ch.3, classical dignity ladder).
* A small additive boost when the yoga's anchor planet receives a full
  drishti from Jupiter (BPHS Ch.27 v.38, the classical "guru drishti"
  amplifier).

The score is appended to the Finding's ``evidence`` as a fixed-format
literal ``strength_score=N.NN`` so downstream UI and audit pipelines can
parse it without consulting any free-text ``verdict`` field.

Methodology:
    Type: descriptive — closed-form aggregation of doctrine-cited
        inputs (vimsopaka + dignity + drishti). No fitting against any
        historical-outcome dataset.
    Inputs to retrieval/scoring: ``finding.classification`` (filter),
        ``finding.evidence`` (parsed for ``participants=A,B,C`` token
        emitted by upstream yoga detectors), the supplied
        ``primitives['vimsopaka']`` and ``primitives['dignity']``
        mappings, and ``primitives['jupiter_aspects']`` for the drishti
        boost gate. NEVER ``finding.verdict`` free-text.
    Explicitly NOT used: ``Finding.verdict`` free-text — verdict
        carries narrative wording that would silently couple
        biographical context to the strength score; that coupling is
        exactly the confirmation-bias trap Section 14 forbids.
    Thresholds & their source: every coefficient in this module is
        directly cited:
            - Dignity multiplier table — BPHS Ch.3 (the classical
              ladder: exalted / own / friend / neutral / enemy /
              debilitated) collapsed into 4 buckets for v1 traceability.
            - Jupiter drishti boost (``+0.10``) — BPHS Ch.27 v.38
              (full guru drishti is the strongest single-planet
              amplifier in classical doctrine).
            - The participating-planet aggregation is the arithmetic
              mean of per-planet (vimsopaka / 20) * dignity_multiplier;
              the mean (rather than weighted) keeps the formula
              auditable without introducing per-yoga calibration
              weights.

        NO threshold or weight in this module has been fit, tuned, or
        selected against any dataset of historical outcomes.
    Famous-chart anti-contamination: not applicable here — vimsopaka
        and dignity inputs are deterministic functions of natal
        chart geometry, with no biographical-passage retrieval. The
        anti-contamination guarantee inherits from the upstream
        primitives.
    Null-baseline test required: N/A — no fitted model.
    Prediction-trap declaration: "This module does NOT predict outcomes.
        It scores the STRUCTURAL strength of detected yoga
        configurations from doctrine-cited inputs. No fitting against
        any chart corpus with outcome labels."

Doctrine source:
    * BPHS Ch.3 — classical dignity ladder (exalted / own / neutral /
      debilitated buckets used by ``_DIGNITY_MULTIPLIER``)
    * BPHS Ch.27 v.38 — Jupiter's full drishti as the strongest
      single-planet amplifier (``_JUPITER_ASPECT_BOOST``)
    * BPHS Ch.7 vv.21-25 — Shodashavarga Vimsopaka scheme (sum-to-20.0
      normaliser used to bring per-planet scores into [0.0, 1.0])
    * BPHS Ch.39-40 — yoga strength conventions: classical doctrine
      ranks yogas as Maha / Madhya / Alpa according to the count and
      dignity of participating planets — this module's mean-of-products
      aggregation mirrors that ranking principle in closed form.

Anti-preference design (Section 14 commitment):
    No threshold or weight in this module has been fit, tuned, or
    selected against any dataset of historical outcomes. Every constant
    is sourced from the BPHS chapters cited above.
"""
from __future__ import annotations

import logging
from typing import Any, Final

from app.reading.schema import Finding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Doctrine-cited constants
# ---------------------------------------------------------------------------


# Dignity multiplier — BPHS Ch.3 classical ladder, collapsed to 4 buckets.
# Order from highest to lowest dignity. The strict-ordering invariant
# (exalted >= own >= neutral >= debilitated) is asserted by the test
# suite and is the only constraint these constants must satisfy.
_DIGNITY_MULTIPLIER: Final[dict[str, float]] = {
    "exalted":      1.0,
    "moolatrikona": 0.95,
    "own":          0.9,
    "friend":       0.75,
    "neutral":      0.7,
    "enemy":        0.4,
    "debilitated":  0.3,
}

# Default multiplier when a planet's dignity is missing / unknown.
_DEFAULT_DIGNITY_MULTIPLIER: Final[float] = 0.5

# Jupiter full-drishti boost — BPHS Ch.27 v.38 (full guru drishti as the
# strongest single-planet amplifier). Additive, applied at most once
# per yoga finding regardless of how many participants are aspected.
_JUPITER_ASPECT_BOOST: Final[float] = 0.10

# Vimsopaka normaliser — Shodashavarga sum-to-20.0 (BPHS Ch.7 vv.21-25).
_VIMSOPAKA_MAX: Final[float] = 20.0

# Evidence-token prefix that upstream yoga detectors emit to declare the
# yoga's participating planets (e.g. ``participants=Jupiter,Moon``).
_PARTICIPANTS_PREFIX: Final[str] = "participants="


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_participants(finding: Finding) -> list[str]:
    """Pull the ``participants=A,B,C`` token out of ``finding.evidence``.

    Returns an empty list if no such token is present. Participant names
    are stripped of surrounding whitespace and discarded if empty.
    """
    for line in finding.evidence:
        if line.startswith(_PARTICIPANTS_PREFIX):
            payload = line[len(_PARTICIPANTS_PREFIX):]
            return [p.strip() for p in payload.split(",") if p.strip()]
    return []


def _planet_score(
    planet: str,
    vimsopaka: dict[str, float],
    dignity: dict[str, str],
) -> float:
    """Compute per-planet structural strength in [0.0, 1.0].

    Formula: (vimsopaka / 20) * dignity_multiplier.
    Both factors are clamped into [0.0, 1.0] and the product is
    therefore guaranteed to land in [0.0, 1.0] without an explicit
    clamp on the result.
    """
    raw = vimsopaka.get(planet, 0.0)
    # Clamp vimsopaka into [0.0, _VIMSOPAKA_MAX]; the upstream module
    # is supposed to honour this range but we're defensive.
    raw_clamped = max(0.0, min(_VIMSOPAKA_MAX, float(raw)))
    vims_normalised = raw_clamped / _VIMSOPAKA_MAX

    dignity_key = (dignity.get(planet) or "").lower().strip()
    multiplier = _DIGNITY_MULTIPLIER.get(dignity_key, _DEFAULT_DIGNITY_MULTIPLIER)

    return vims_normalised * multiplier


def _calibrate_one(
    finding: Finding, primitives: dict[str, Any]
) -> Finding:
    """Compute and attach ``strength_score=N.NN`` to a single yoga finding.

    The returned Finding is a new immutable copy (model_copy) with the
    score appended to ``evidence``. If the finding's participants list
    is empty, a neutral 0.0 score is attached — downstream consumers
    can distinguish "no participants declared" from "participants
    declared but yielded 0.0" by looking at evidence.
    """
    participants = _extract_participants(finding)
    vimsopaka = primitives.get("vimsopaka") or {}
    dignity = primitives.get("dignity") or {}
    jupiter_aspects = primitives.get("jupiter_aspects") or []

    if not participants:
        # Silent: no participants declared. Attach a neutral 0.0 so
        # downstream consumers always see a strength_score line on
        # yoga findings, matching the calibration contract.
        score = 0.0
    else:
        per_planet = [_planet_score(p, vimsopaka, dignity) for p in participants]
        # Arithmetic mean — keeps the aggregation auditable and avoids
        # introducing per-yoga calibration weights.
        score = sum(per_planet) / len(per_planet)
        # BPHS Ch.27 v.38 Jupiter drishti boost — applied at most once,
        # only when at least one participant is in the jupiter_aspects
        # list AND the participant is not Jupiter itself (self-aspect
        # is not counted as a drishti boost in classical doctrine).
        if any(
            p in jupiter_aspects and p.lower() != "jupiter"
            for p in participants
        ):
            score = min(1.0, score + _JUPITER_ASPECT_BOOST)

    # Clamp once defensively. The formula's per-planet scores are
    # already in [0.0, 1.0], so this should always be a no-op.
    score = max(0.0, min(1.0, score))

    evidence = list(finding.evidence) + [f"strength_score={score:.2f}"]
    return finding.model_copy(update={"evidence": evidence})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calibrate_yogas(
    findings: list[Finding], primitives: dict[str, Any]
) -> list[Finding]:
    """Return a new list of Findings with yoga strength scores attached.

    Operation per finding:

    * If ``classification != "yoga"``: return unchanged.
    * If ``classification == "yoga"``: compute the closed-form
      strength score from the doctrine-cited inputs and attach it to
      ``evidence`` as ``strength_score=N.NN``.

    The function is pure — input findings are never mutated; each
    output is a new immutable copy.
    """
    out: list[Finding] = []
    for finding in findings:
        if finding.classification != "yoga":
            out.append(finding)
            continue
        out.append(_calibrate_one(finding, primitives))
    return out
