"""The Parashara synthesis layer — deterministic reasoning BETWEEN the engine's cited rules.

The rest of `app/parashara/` computes hundreds of individually-cited BPHS facts about a nativity:
bhava verdicts, strengths, avasthas, divisionals, dashas, arudhas, yogas. This subpackage reasons
*across* them. For each topic (a bhava, and named life-matters that read from it) it gathers tiered
evidence — the birth-chart PROMISE, the significators' STRENGTH, the AFFLICTION against it, the
divisional/ashtakavarga CORROBORATION, and the dasha ACTIVATION that times it — resolves the
contradictions by BPHS's own precedence (the birth chart decides; a division corroborates; a dasha
only times), and states a final judgment on the classical axis (granted / delayed / difficult /
denied), every conclusion carrying its full audit trail (sloka -> rule -> condition -> evidence).

Two doctrines bind the whole layer:

  * **Deterministic.** No LLM is ever in the judgment path. The synthesis is a pure, reproducible
    function of the reading. (A language model may narrate the result elsewhere; it never decides it.)
  * **Measured truth.** The confidence attached to a judgment is a *doctrinal-convergence* statement
    — "how strongly Parashara's own cited rules concur for this chart" — never a probability that the
    event occurs. It is reported as a tally beside its reasons ("K of N cited testimonies concur, M
    contradict") plus a convergence tier, and it can never contradict the evidence shown next to it.

Pure-parashara by construction (pinned by `tests/parashara/test_engine_isolation.py`): it consumes a
`ParasharaReading` and this engine's own primitives only.

Usage:
    from app.parashara.chart.cast import cast
    from app.parashara.reading import read
    from app.parashara.synthesis import synthesize
    report = synthesize(read(cast(year=1990, month=7, day=15, hour=12, minute=0,
                                  tz_offset=5.5, latitude=12.97, longitude=77.59)))
"""
from __future__ import annotations

from app.parashara.synthesis.evidence import Evidence, Polarity, Tier
from app.parashara.synthesis.convergence import Convergence, converge
from app.parashara.synthesis.judgment import Judgment, judge_topic
from app.parashara.synthesis.synthesis import SynthesisReport, synthesize

__all__ = [
    "Evidence", "Polarity", "Tier",
    "Convergence", "converge",
    "Judgment", "judge_topic",
    "SynthesisReport", "synthesize",
]
