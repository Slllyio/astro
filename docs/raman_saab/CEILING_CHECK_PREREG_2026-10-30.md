# Ceiling check: pre-registration (2026-10-30)

User decision 2026-10-30 ("Ceiling check, then rebuild"). Diagnostic only: no engine code,
rule or threshold changes. **Hold-out 4 and hold-out 5 are not read.** Hold-outs 1-3 are
already spent and are used here as the out-of-sample sets.

Written and committed before any number below exists. What was already known when this was
written (so not a fresh prediction): the engine's pool and hold-out 1-3 scores, the hold-out 2
class split (94 of 134 favourable), and a rough estimate (from WHY_273, not a run) that a
rule-polarity count would score about 245-250 on the pool.

## Part A. Baselines against the engine

Sets: pool (the 389 confirmed worked-example conclusions), H1 (raman_holdout_sealed, 36),
H2 (raman_holdout2_sealed, 134), H3 (raman_holdout3_sealed, 28), and H1-3 combined (198).

Predictors, per conclusion:
- **E** the engine as shipped (this commit's parent), `_signification_verdict`.
- **B0** always "favourable".
- **B1** the pool's most common label, applied everywhere.
- **B2** rule polarity: count the benefic and malefic rules fired in the signification's lead
  ledger. More benefic -> favourable; more malefic -> afflicted; equal and non-zero -> mixed;
  none fired -> favourable.
- **B3** as B2, but a non-zero tie -> favourable.

Metrics: exact, within one step, real errors (ordinal distance >= 2, as in test_goldens),
and macro recall (mean of per-class recall over favourable / mixed / afflicted), which stops
an always-favourable guess looking good on a favourable-heavy set.

Decision rule (H1-3 combined, exact count): difference D = E minus the best of B0-B3
(best chosen on H1-3, which favours the baselines; stated openly). Chart-clustered bootstrap,
10,000 resamples, seed 20261030, 95% interval.
- interval above 0: **engine adds value over baselines out of sample**
- interval below 0: **engine below baseline out of sample**
- otherwise: **no detectable difference**
Real errors and macro recall are reported beside it with the same bootstrap.
Caveat recorded in advance: the engine was patched after hold-outs 1-3 were seen (e.g. G2, S2
and the cast-fidelity re-casts), which can only flatter E.

## Part B. Label agreement (how consistent is the target itself)

80 rows drawn at random from the 389 (Python `random.Random(20261030).sample`, ordered by
golden id + house). Two independent labellers (separate engine-blind agents, no access to the
gold label, the engine or each other) read only Raman's text for each row: the cited passage
lines from the corpus where available, else the record's verdict prose with the verdict word
masked. They label favourable / mixed / afflicted with this codebook, fixed now:
- favourable: Raman's conclusion for that matter is on the whole good (benefits come, even if
  minor blemishes are named);
- afflicted: on the whole bad, denied, destroyed, or lost;
- mixed: he states both a real good and a real bad result for the matter as operative (incl.
  "good, then lost"), without saying one outweighs the other;
- if the text gives no conclusion for that matter: "none" (counted as disagreement).

Reported: exact agreement and Cohen's kappa (unweighted and linear-weighted) for each labeller
against gold and between the two labellers, with bootstrap 95% intervals.

Reading rule, fixed now: let A = mean exact agreement of the two labellers with gold.
- If the engine's pool exact rate is within 10 points of A (>= A - 0.10): the engine is **near
  the label ceiling**; further single-rule tweaks are retired and effort moves to the rebuild.
- Otherwise: **headroom exists**, and its size (A minus engine) is reported.
Either way the rebuild proceeds (user decision); this sets what the rebuild can hope to gain.

## Part C. Raman against himself (descriptive only)

List natives that appear in more than one of pool / H1-3 (same name, or same birth date),
and compare Raman's labels where the same house and matter is judged twice. No pass rule;
counts and the rows are reported.
