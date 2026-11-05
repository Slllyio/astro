# Learned predictive test: results (Phases 0-2), 2026-11-03

Pre-registration: `docs/predictive/PREDICTIVE_PREREG_2026-11-02.md` with addenda 1-3. Code:
`tools/predictive/`. Raw numbers: `/mnt/project-files/astro/predictive/` (every null run is kept,
one JSON line per run). Data: Astro-Databank development people only (tiers A and B, 47,036
people). The sealed sets C1 and C2 were not opened.

## The answer in one paragraph

The test was built so that astrology could win. A learned model was given everything the project
has encoded (raw sidereal positions, Raman's rules, Parashara verdicts, KP significators,
dasa lords, transits) and asked two questions on real people. It first passed every check that it
could see an effect when one is there. On the real outcomes it found nothing that season, birth
year, age and place do not already explain. Natal charts did not separate actors, writers, office
holders, divorces, large families, cancer or early death from everyone else (12 of 12 targets
bounded below the pre-set size or underpowered, none a signal), and the sky on the day of a real
life event did not differ from the same person's other days (1,356 events, bounded below the
pre-set size). By the pre-registered stop rule, the project stops here and C1 and C2 stay sealed.
This says: these systems, read by this model, show no effect larger than the bounds below in this
data. It does not say astrology cannot work.

One mistake was caught on the way and is reported in full: the first trait score passed, and the
pass came from a data-coverage defect, not from the sky (section 4).

## 1. Is the instrument able to see an effect? (Phase 1)

| Check | What it asks | Result | Verdict |
|---|---|---|---|
| Gauquelin Mars (real data) | Does the model see the sports-champion effect in 14,333 Gauquelin people (1,285 champions)? | Full model ΔAUC −0.0134 vs null mean −0.0147, p 0.18; best family G_Sun, p 0.51 | **Not detected** |
| Planted trait, Moon in Ashwini/Magha/Mula (risk ×2) | Synthetic label, 47,036 people | Detected 5 of 5 (ΔAUC 0.033-0.052, p 0.048 each, the floor for 20 runs) | Pass |
| Planted trait, Mars and Venus in one sign (risk ×2) | Synthetic label | Detected 5 of 5 (ΔAUC 0.036-0.065) | Pass |
| Planted timing, Jupiter 1/5/9 from natal Moon (odds ×3) | Synthetic case date in each real set | Detected 5 of 5 (ΔC 0.062-0.115) | Pass |
| Empty labels (traits) | Random labels must not pass | 0 of 5 detected | Pass |
| Empty labels (timing) | Same | 1 of 3 detected (p 0.048, ΔC 0.017; at most 1 allowed) | Pass |

The planted effects are modest (a doubled rate in about a third or a tenth of people) and the model
found every one. So "the model cannot see effects" is ruled out for effects of that size. The
Gauquelin effect (about +4.7 points among champions, measured earlier) is smaller than the model's
noise floor here: the pre-registration reads this as "this instrument cannot see an effect of the
Gauquelin size", and Phase 2 went ahead. Exploratory only: the Mars family alone sat at about p 0.02
against its own null, which points the right way but was not the pre-registered test.

## 2. Timing: does the sky on an event day differ from the same person's other days? (Task B)

1,356 day-dated, non-death events from 1,356 people, each against 10 control days of the same
person, matched for age at that event type and season. Statistic ΔC: how much more often the real
day outranks the person's control days once astrology is added to age, year and season.
Concordance with age, year and season alone: 0.589; with all astrology added: 0.591.

| Area | Sets | Excess ΔC over null | 95% interval | p | Verdict (SESOI 0.03) |
|---|---|---|---|---|---|
| **All events** | 1,356 | −0.001 | −0.020 to +0.016 | 0.55 | **BOUNDED_NULL** |
| Career (house 10) | 482 | −0.002 | −0.030 to +0.027 | 0.52 | BOUNDED_NULL |
| Marriage, relationships (7) | 462 | −0.015 | −0.047 to +0.018 | 0.75 | BOUNDED_NULL |
| Health (6) | 212 | −0.009 | −0.047 to +0.029 | 0.61 | BOUNDED_NULL |
| Parents (4, 9) | 97 | +0.040 | −0.023 to +0.099 | 0.16 | UNDERPOWERED |
| Children (5) | 19 | +0.133 | −0.021 to +0.296 | 0.10 | UNDERPOWERED |
| Other (2, 3, 8, 11, 12) | 84 | +0.019 | −0.055 to +0.095 | 0.32 | UNDERPOWERED |
| Tier A (minute-exact times) | 688 | −0.013 | −0.038 to +0.016 | 0.75 | BOUNDED_NULL |
| Tier B (quarter-hour times) | 668 | +0.010 | −0.013 to +0.034 | 0.31 | UNDERPOWERED |

Best single family: transiting Mars, +0.0096, p 0.70 against the family-scan null. Raman activation
+0.007, dasa lords +0.007, KP dasa significators +0.007, Parashara activation −0.004. The smallest
effect detectable at 80% power: ΔC 0.047 for the full model, 0.026 for the best family.

**Secondary check, real vs random birth time (N1, 20 runs).** With each person's birth time
replaced by a random time on the same day, the full model scores −0.015 on average (sd 0.004);
with the real time it scores +0.002. Excess +0.017, p 0.048 (the smallest p 20 runs can give).
This is below the pre-set size (0.03) and is a secondary null, so it is not a pass. It is the one
timing thread that leans toward real birth times mattering, and it is worth its own
pre-registered follow-up with more runs. (The real-time pipeline was checked to reproduce the
cached features exactly, so this is not a code difference.) Children: excess +0.067, p 0.048 on
19 sets.

## 3. Traits: does the natal chart separate people? (Task A, corrected run)

16,448 people with every feature track computed (addendum 3). ΔAUC: how much the area under the
curve rises when astrology is added to birth year, season, latitude, longitude, tier and the
size of the birth cohort. Pooled excess over the null: +0.002 (p 0.07); best family scan +0.001
(p 0.12). Pass rule: p < 0.025 and excess ≥ 0.02. **No pass.**

| Area | Target | Cases | Excess ΔAUC | 95% interval | p | Verdict (SESOI 0.02) |
|---|---|---|---|---|---|---|
| Career | A1 Actor | 2,540 | +0.001 | −0.008 to +0.009 | 0.34 | BOUNDED_NULL |
| Career | A2 Public office | 1,071 | 0.000 | −0.012 to +0.012 | 0.51 | BOUNDED_NULL |
| Career | A3 Writer | 3,523 | +0.001 | −0.007 to +0.009 | 0.29 | BOUNDED_NULL |
| Career | A4 Sports | 2,176 | +0.002 | −0.004 to +0.007 | 0.10 | BOUNDED_NULL |
| Career | A5 Military | 1,192 | +0.002 | −0.006 to +0.008 | 0.29 | BOUNDED_NULL |
| Career | A6 Music | 2,107 | +0.007 | −0.004 to +0.017 | 0.10 | BOUNDED_NULL |
| Career | A7 Law | 682 | −0.002 | −0.019 to +0.014 | 0.54 | BOUNDED_NULL |
| Marriage | A8 Noted divorces | 793 | −0.004 | −0.014 to +0.006 | 0.83 | BOUNDED_NULL |
| Children | A9 More than 3 children | 1,475 | −0.004 | −0.011 to +0.004 | 0.90 | BOUNDED_NULL |
| Health | A10 Cancer | 658 | +0.001 | −0.009 to +0.012 | 0.44 | BOUNDED_NULL |
| Life span | A11 Homicide victim | 286 | +0.016 | −0.010 to +0.040 | 0.024 | UNDERPOWERED |
| Life span | A12 Short life (deceased only, 8,378) | 652 | +0.007 | −0.005 to +0.018 | 0.049 | BOUNDED_NULL |

By area (pooled within area): career excess +0.002 (p 0.15), marriage −0.004 (p 0.83), children
−0.004 (p 0.90), health +0.001 (p 0.44), life span +0.011 (p 0.024; below the 0.02 size, so not a
pass). The life-span area is the nearest thing to a lead: homicide victims at the lowest p 40 runs
can give, early death at p 0.05. With 12 targets, one at p 0.024 is about what chance gives
(expected about 0.3 below 0.025, and the targets are correlated), and both sizes are under the
threshold. It is named here so a future, pre-registered test can aim at it; it is not a finding.

By family, every family's best target gain was small: Raman rules and Parashara verdicts (the text
tracks) −0.005 pooled, KP −0.003, geometry families −0.003 to −0.009. Per target the strongest single
families were G_Rahu for law (+0.010) and cancer (+0.004), G_Saturn for public office (+0.003); none
near the size that would count.

Tier split (ΔAUC, before subtracting the null): A and B are close for every target, with no pattern
of tier A (exact times) doing better, which is what a birth-time-sensitive effect would show.

N1 (random birth time, 20 runs, secondary) for Task A: real birth times score no better than random times on the same day. Pooled excess +0.002 (p 0.14), family scan +0.001 (p 0.19); career +0.001, children 0.000, health +0.002, life span +0.010 (p 0.14), marriage −0.007. The life-span lead does not depend on the exact birth time, so it does not behave like a chart effect.

## 4. The defect that looked like a pass (addendum 3)

The pre-registered Task A run, on all 47,036 people, passed on paper: pooled excess +0.026,
p 1/41; divorces +0.090, more than 3 children +0.098, short life +0.074, all through the Raman-rule
and Parashara-verdict families. The size was the warning sign: every geometry family was negative,
and a ΔAUC near 0.1 from rule flags would be far larger than anything ever measured in this field.

The cause: the Raman and Parashara stores were computed only for the 22,177 "verified" charts,
16,448 of the development people (35%), and the build filled everyone else with zeros. The divorce,
children and short-life tags exist only in that same subset (4.8%, 9.0%, 7.8% inside it; 0.0%,
0.0%, 0.02% outside). So "any rule fired" meant "this person is in the well-documented subset",
and the model learned that. The null shuffles features between similar people and so broke the
link, which is why it could not catch it.

The pre-registered result is void (neither a signal nor a null). The corrected run (section 3) is
the only change, written down and committed before it was computed, and is labelled as corrected
after a defect wherever quoted. On the correct population the "effect" vanishes completely
(divorces −0.004, children −0.004, short life +0.007).

## 5. What this means

- **What was tested:** the skies of 47,036 real people with certified birth times, read through
  every system the project encodes, by a model free to find any pattern, against nulls that keep
  season, cohort, age and place fixed.
- **What it found:** nothing above the bounds in the tables. For the most common questions people
  ask (career, marriage, health, the day things happen), the effect, if there is one, is smaller
  than ΔAUC 0.02 natally and ΔC 0.03 in timing, and in most rows the interval rules out even half
  of that.
- **What it did not test:** the small areas (children's timing, parents, other houses) are
  underpowered; whole-life judgment by a human astrologer was not tested; KP ruling planets at the
  moment of a question are only testable going forward (the log is built, section 6).
- **Two threads for a future pre-registered test,** both weak and both below the pre-set size:
  real birth times beating random ones in event timing (excess +0.017, p 0.048), and life-span
  targets (homicide victim p 0.024, early death p 0.049).

## 6. Forward question log

`tools/predictive/forward_log.py` is built: each question is locked with a hash chain before its
window opens, KP's horary answer and the ruling planets at the question are recorded, the asker's own
expectation is recorded, and scoring is against the asker (bar: 65% right on at least 85 decided
questions, and better than the asker). No one's data has been entered.

## 7. Files

| File | Contents |
|---|---|
| `gauquelin_results.json`, `plants_A_results.json`, `plants_B_results.json` | Phase 1 |
| `phase2_B_results.json`, `phase2_B_ci_by_area.json`, `n1_B_results.json` | Task B |
| `phase2_A_results.json`, `phase2_A_observed.json` | Task A as pre-registered (void, section 4) |
| `phase2_A_covered_results.json`, `phase2_A_covered_observed.json` | Task A corrected |
| `verdicts.json` | The equivalence verdicts in the tables above |
| `*_runs.jsonl` | Every null run |
