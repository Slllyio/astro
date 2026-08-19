# Track C — Raman-styled analysis (worked-chart exemplars → few-shot interpreter)

## The gap this closes
The engine already has an LLM interpreter (`app/medini/doctrine/interpret.py`) that renders its
structured verdicts as prose under a strict grounding contract. But the repo's Raman material
was the **rule-compendium** — atomic significations ("Jupiter in the 7th → devoted to wife"),
not Raman's **worked-chart analyses**: the running reasoning by which he weighs one testimony
against another and delivers a verdict on an actual horoscope. The interpreter was told to
"write in the classical register" but had **no exemplar of how Raman actually chains a chart
analysis** — only his vocabulary. That connective prose is what makes a reading read like him,
and it lives in the HTJAH PDFs, not the compendium.

## C.1 — the exemplar corpus (`data/raman_doctrine/worked_analyses.jsonl`)
**83 verbatim worked-chart analyses**, extracted from HTJAH Vol I & II and tied by unique
birth-line to charts already in the held-out corpora (so each carries a known house + Raman's
graded verdicts). Each record: `{chart_no, house, book, birth_line, analysis_text,
verdict_sentences, raman_verdicts, sha256}`. The prose is sha256-verified (unmodified, like the
compendium). Coverage by house: 3 (6), 5 (13), 6 (10), 8 (28), 10 (20), 12 (6); 33 carry an
explicit verdict-delivery sentence.

A representative exemplar (8th-house chart 43) shows the template the interpreter now learns:

> *The Eighth Lord: Saturn is in the 7th in a kendra but in the 12th house from the 8th house.
> He is aspected by a combust Mars. Āyushkāraka: Saturn is in his own sign but in a marakasthāna
> and aspected by a malefic Mars. Considered from the Moon: the 8th lord is in the 12th from the
> 8th. **Conclusions: The Lagna is fairly strong being Vargottama and the Lagna lord is
> exalted…***

— i.e. **bhāva → lord → kāraka → Chandra-Lagna → conclusion**, Rāśi then Moon, plain
"this is good / this is bad" observations resolving into "**Hence the … is `<verdict>`**".

## C.2 — few-shot wiring (`worked_analyses.py` → `interpret.py`)
`worked_analyses.exemplar_block(houses, k)` selects house-matched, verdict-bearing exemplars and
frames them for the interpreter's system prompt. `interpret_chart(..., style_exemplars=True)`
(default on) appends that block as a **second, cacheable system block**. The framing is
**style-only and preserves the grounding contract**: the exemplars teach *reasoning order and
idiom*, and the block explicitly instructs the model to **never import a placement, planet, or
verdict from an exemplar** and to "ground every claim in the engine evidence, as the rules
above require." The original `GROUNDING IS ABSOLUTE` contract in `_SYSTEM` is untouched.

Opt-out is a single flag (`style_exemplars=False`) — the exemplars are additive and reversible.

## C.3 — validation method (how to score the styling)
Deterministic guards are in place now (`tests/doctrine/test_worked_analyses.py`): the corpus is
verbatim (sha256), exemplar selection prefers the requested house + verdict samples, and the
block carries the style-only / grounding language. The end-to-end prose evaluation (an API run,
not executed here) is specified as:
1. **Verdict fidelity** — for K held-out worked charts, generate the engine's reading and check
   the headline it delivers maps (via the pre-registered `verdict_grade_map`) to Raman's own
   verdict phrase for that chart. This catches a stylist that drifts off the engine's verdict.
2. **Reasoning-order + idiom rubric** — an LLM judge scores each reading on: does it proceed
   bhāva → lord → kāraka → Chandra-Lagna → daśā; does it use Raman's "this is good/bad → hence"
   cadence; and — the hard constraint — does it introduce **any** placement/aspect absent from
   the engine evidence (a single hallucinated fact fails the reading).
Report both, A/B against `style_exemplars=False`; claim only what the rubric measures.

## Honest scope
This is the enabling infrastructure (the missing corpus + the grounded few-shot wiring), plus
deterministic guards. It does not itself assert the prose "sounds like Raman" — that is what the
C.3 API evaluation measures, and it is the explicit next step. No engine change; the doctrine
suite stays green.
