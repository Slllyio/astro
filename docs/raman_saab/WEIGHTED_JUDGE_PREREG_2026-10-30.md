# Weighted judge W1: pre-registration (2026-10-30)

User decision 2026-10-30 ("Ceiling check, then rebuild"). Follows
`CEILING_CHECK_RESULTS_2026-10-30.md`: out of sample the shipped judge (E) scores 87/198 exact,
below a plain rule-polarity count (B3, 131/198). W1 is a **parallel** judge; nothing in the
shipped engine changes unless the user ships W1 after its test.

Fixed before any rule weight is graded and before any W1 number exists. Hold-outs 4 and 5 are
not read until the user says so (final test, below).

## Design

Inputs per matter (house + signification), all already computed by the engine:
- the benefic and malefic rules that fire in the signification's lead ledger;
- the lord's and karaka's condition as the ledger already records it (`lord_strong`,
  `karaka_strong`, `lord_hard_afflicted`; None where unknown).

**Rule weights come from Raman's wording, not from fitting.** Each of the 739 polar rules
(302 benefic, 437 malefic) gets a weight from its own text and cited passage:
- 3 = decisive language ("will be denied", "destroyed", "completely", "certainly", "sure");
- 1 = plain statement of a result;
- 0.5 = hedged or partial ("may", "some", "slight", "a little", "tendency");
- 0.25 = a general dictum Raman himself qualifies or says to apply with caution.
Two independent engine-blind graders grade every polar rule (they see the rule text and the
cited lines, not the rule's polarity, firing counts or any verdict). Weight = mean of the two.
Agreement (exact and weighted kappa) is reported.

Score: S_b = sum of benefic weights, S_m = sum of malefic weights.
Lord/karaka term L = (+1 for each of lord, karaka read strong) + (-1 if the lord is hard
afflicted); unknown counts 0. Weakness is not counted as a malefic vote (Raman: weakness is an
absence of good, RAMAN_PHILOSOPHY section 4).

Model: ordinal logistic, eta = b*S_b - m*S_m + l*L, with two cut points between afflicted <
mixed < favourable. **Five fitted numbers** (b, m, l, two cuts), b and m constrained >= 0,
fitted by maximum likelihood with a mild ridge (lambda 0.1 on b, m, l). No per-house or
per-rule fitted terms. Output: the three probabilities; the verdict is the most probable class.
No worst-matter headline; matters stay separate.

## Development stage (spent data only)

Fit on the pool (389). Report on hold-outs 1-3 (198): exact, within one, real errors, macro
recall, log-loss, against E and B3. This is a sanity check, not the test. Allowed changes after
it: only fixing bugs in code (each one recorded here before re-running), not the design.
Then refit the same design on pool + hold-outs 1-3 (587 rows) and **freeze**: commit the
fitted numbers, the weights table and a SHA-256 of W1's verdicts on the 587 rows.

## Final test (one time, needs the user's say-so)

Hold-outs 4 and 5 together (64 rows; hold-out 4 is sign-only, so W1 must run on stated
positions, which it does). Scored once for W1, E, B3 and always-favourable.

**W1 PASSES only if all hold:**
1. W1 exact >= B3 exact, and W1 exact > E exact;
2. W1 real errors <= B3 real errors;
3. W1 log-loss < the class-frequency log-loss (frequencies from the 587 development rows).

Reported with chart-clustered bootstrap 95% intervals (10,000, seed 20261030) on W1 minus B3
and W1 minus E. With 64 rows a difference of under about 10 rows cannot be told from chance; if
W1 passes the rule but the interval on W1 minus B3 includes 0, the result is reported as
**PASS, UNDERPOWERED**, and no claim of beating the baseline is made.

## Honesty notes

- Hold-outs 1-3 were seen during earlier engine work; using them to fit W1 is fine because the
  final test is on 4 and 5.
- B3 needs no fitting, so it is the fair bar. If W1 cannot beat it, the honest product judge is
  B3-like (a cited count of what fires), and W1's value is limited to calibrated probabilities.

## Addendum 1 (2026-10-30): weights graded, development check run, W1 frozen

**Weights.** Two blind graders graded all 739 polar rules. They agreed exactly on 91.1%
(kappa 0.69). Grades: 1 for about 83%, 3 for 27 rules, 0.5 for 55-66, 0.25 for 24-40. Weight
is the mean of the two (`weighted_judge/rule_weights.json`; both graders' grades in
`rule_weight_grades.json`). Note: the two graders shared a scratch folder; each reports
reading only the rules file and writing its own output.

**Development check (fit on pool, scored on hold-outs 1-3, 198 rows):**

| | exact | within one | real errors | macro recall | log-loss |
|---|---|---|---|---|---|
| W1 | 125 | 132 | 66 | 0.445 | 0.786 |
| B3 (polarity count) | **131** | 138 | 60 | 0.433 | - |
| E (shipped engine) | 87 | **150** | **48** | 0.347 | - |
| class frequencies | - | - | - | - | 0.838 |
| W1 with every weight 1 (exploratory, not pre-registered) | 125 | 132 | 66 | 0.428 | 0.800 |

Fitted on the pool: b 0.52, m 0.34, lord/karaka term l 0.05 (about zero), and W1 never predicts
"mixed".

What this shows:
- W1 does **not** beat B3 on the development check (125 vs 131 exact, 66 vs 60 real errors).
- The text-graded weights add calibration only (log-loss 0.786 vs 0.800 with unit weights),
  not exact matches.
- The lord and karaka condition, as the engine computes it, carries no information about
  Raman's verdict once the fired rules are counted.
- The fired rules carry little information: log-loss improves only from 0.838 to 0.786.
  What Raman uses to decide is mostly not in the engine's fired rules.

W1 is frozen as pre-registered (`weighted_judge/w1_frozen.json`). Recommendation recorded for
the user: do not spend hold-outs 4 and 5 on W1, since it already trails B3 on development data.
