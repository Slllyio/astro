# Raman reader LLM: pre-registration (2026-10-31)

Committed before any model is trained or scored. Nothing below is changed after numbers exist;
any later change is an addendum with its date.

## 1. Question

Can an LLM fine-tuned on Raman's worked charts, given only what our engine outputs for a matter,
(a) give Raman's verdict more often than the plain for/against count, and (b) write a reading in
his manner?

## 2. Data (tools/raman_llm/build_dataset.py, data/raman_llm/dataset.jsonl)

651 Raman conclusions on 370 charts:

| split | rows | note |
|---|---|---|
| pool | 389 | CONFIRMED rows; the engine's rules were tuned here |
| H1-H3 | 198 | sealed hold-outs; count B3 131, always-favourable 126, clause judge 87 |
| H4+H5 | 64 | sealed hold-outs, spent 2026-10-31; count B3 40, always-favourable 38, clause judge 29 |

All five hold-outs have already been scored by earlier variants, so none of them is fresh to us.
They are fresh to this model only in the sense that a row is never in training when it is
scored (section 4). That is the only out-of-sample claim this study makes.

Dataset sha256: d339030243cad9ded00df0e49f3a0babdb7ba06158479df0aac5d64318798920

## 3. Input and target

Input (prompt): the matter, chart facts (sign, house, dignity, retrograde, combust, navamsa for
each planet), every rule that fires for and against the matter with its reading and book line,
the raw count, and the generic factor tally from tools/raman_saab/tally_judge.py.

Deliberately left out: the clause judge's own verdict. On the pool it matches Raman 263/389
because it was tuned there, and out of sample only 116/262; a model trained on pool rows would
learn to copy a signal that does not travel.

Target: `VERDICT: <favourable|mixed|afflicted>`, then for pool rows Raman's coded reasons
(docs/raman_saab/reason_coding, signed, decisive marked), then `CONCLUSION:` his own words.

## 4. Split

5 folds by chart, seed 20261031: every conclusion on one chart sits in one fold (the script
asserts no chart crosses train and test). For each fold, a fresh LoRA adapter is trained on the
other four folds and scores the held fold. Every row is therefore scored by a model that never
saw its chart.

## 5. Model and training (fixed before scoring)

Base: the largest Qwen3 that fits the user's GPU in 4-bit (>=44 GB: Qwen3-32B, >=20 GB: 14B,
>=11 GB: 8B, >=7 GB: 4B), QLoRA r=16, alpha 32, all attention and MLP projections, 2 epochs,
lr 2e-4, effective batch 8, max length 1536, one seed. Thinking mode off. The model actually
used is written to run_meta.json. No hyperparameter is tuned on any score; if the run fails for
memory, the next smaller model is used and that is recorded.

## 6. Verdict scoring and pass bar

The verdict is the class with the highest model likelihood for `VERDICT: <class>` after the
prompt (no sampling).

Primary: exact matches on the 262 hold-out rows (H1-H5), out of fold, against count B3 (171/262).
- SIGNAL: LLM exact > 171 and exact two-sided McNemar p < 0.05 against B3.
- WORSE: LLM exact < 171 with p < 0.05.
- otherwise NULL: no detectable difference from the count.

Secondary, reported regardless: H4+H5 (vs 40/64), H1-H3 (vs 131/198), real errors (favourable vs
afflicted), the untrained base model, always-favourable, the clause judge. Pool rows are reported
but carry the warning that the engine's rule firings there were tuned to Raman.

Expected (written now): NULL. Earlier work found Raman's verdicts lean on what was known of the
life, and no chart-only judge beat the count out of sample.

## 7. Reading quality

The model writes a reading for every hold-out row (greedy, up to 220 tokens) while it is out of
fold. Reported: ROUGE-L of its CONCLUSION against Raman's own words, beside a no-model template
(the first two rule readings on the side the count leans to). This is a word-overlap measure, not
a judgment of quality.

No one has judged the readings blind at the time of writing. score.py writes a 30-item blind
packet (Raman's words vs the model's, order shuffled, key in a separate file) for a human reader.
Until someone marks it, the report must say the prose is not blind-judged.

## 8. What the final model is for

After the folds, one adapter is trained on all 651 rows (tools/raman_llm/read.py). Its readings
are a model of how Raman wrote, not a forecast; its fold numbers above are the only evidence of
how well it matches him.
