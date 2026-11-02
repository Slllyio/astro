# Rectification questions: what splits the window (research run)

200 synthetic births (15 Indian places, 1950-1995, any time of day), window +/- 30 min (61 candidate minutes, 5.93 bits of uncertainty), engines KP + Raman, today (2026, 11, 2).
Bits are expected information gain under a uniform prior, with the reliabilities in `app.kp.rect_questions` (0.8 facts and dates, 0.65 self-descriptions). Date questions assume month precision.

## 1. Value of each question

| fact | kind | median bits | mean | 90th pct | splits the window in | in the chart's top 5 in |
|---|---|---|---|---|---|---|
| date_abroad | date | 0.639 | 0.698 | 1.267 | 94% | 71% |
| speech_style | choice | 0.489 | 0.494 | 0.569 | 100% | 64% |
| date_scholarship | date | 0.431 | 0.468 | 0.918 | 98% | 50% |
| date_study_abroad | date | 0.397 | 0.433 | 0.823 | 98% | 48% |
| date_move | date | 0.356 | 0.412 | 0.871 | 100% | 38% |
| date_job | date | 0.252 | 0.351 | 0.805 | 100% | 32% |
| date_business | date | 0.287 | 0.346 | 0.769 | 100% | 30% |
| date_deputation | date | 0.292 | 0.344 | 0.702 | 100% | 30% |
| date_property | date | 0.266 | 0.334 | 0.752 | 99% | 26% |
| date_property_sold | date | 0.238 | 0.323 | 0.667 | 100% | 26% |
| date_marriage | date | 0.227 | 0.308 | 0.687 | 100% | 24% |
| date_child | date | 0.267 | 0.306 | 0.647 | 100% | 27% |
| date_job_end | date | 0.223 | 0.294 | 0.627 | 99% | 24% |
| salaried_job | yesno | 0.232 | 0.216 | 0.276 | 98% | 5% |
| married | yesno | 0.227 | 0.207 | 0.276 | 97% | 6% |
| children | yesno | 0.065 | 0.062 | 0.073 | 99% | 0% |
| own_property | yesno | 0.053 | 0.053 | 0.097 | 94% | 0% |
| lived_abroad | yesno | 0.053 | 0.052 | 0.092 | 94% | 0% |
| more_than_one_marriage | yesno | 0.051 | 0.045 | 0.072 | 88% | 0% |
| spouse_works | yesno | 0.039 | 0.039 | 0.071 | 86% | 0% |
| serious_danger | yesno | 0.037 | 0.034 | 0.065 | 78% | 0% |
| frequent_illness | yesno | 0.036 | 0.033 | 0.071 | 73% | 0% |
| musician | yesno | 0.027 | 0.028 | 0.069 | 60% | 0% |
| higher_education | yesno | 0.014 | 0.026 | 0.064 | 84% | 0% |
| mother_well | yesno | 0.010 | 0.019 | 0.058 | 57% | 0% |
| good_health | yesno | 0.015 | 0.017 | 0.034 | 98% | 0% |
| siblings_good | yesno | 0.014 | 0.015 | 0.030 | 94% | 0% |
| uniformed_career | yesno | -0.000 | 0.015 | 0.059 | 36% | 0% |
| money_gains | yesno | 0.014 | 0.014 | 0.026 | 96% | 0% |
| father_well | yesno | 0.013 | 0.014 | 0.028 | 94% | 0% |
| borrowed_hardship | yesno | 0.000 | 0.011 | 0.049 | 32% | 0% |
| wishes_fulfilled | yesno | 0.011 | 0.010 | 0.018 | 81% | 0% |
| happy_marriage | yesno | 0.005 | 0.008 | 0.016 | 100% | 0% |
| status_authority | yesno | 0.004 | 0.007 | 0.016 | 100% | 0% |

## 2. How chart-specific the best questions are

Distinct top-5 question sets across 200 charts: 160.
Most common top-5 sets: date_abroad, date_business, date_job, date_move, date_study_abroad (4); date_abroad, date_marriage, date_move, date_study_abroad, speech_style (4); date_abroad, date_marriage, date_move, date_scholarship, speech_style (3).
Median number of changes inside the window (lagna sign, navamsa, any cusp sub-lord): 52.0.

Sum of the top 5 questions' bits by rising sign (short- and long-ascension signs rise at different speeds):

| lagna | median top-5 bits |
|---|---|
| Aries | 2.61 |
| Taurus | 3.07 |
| Gemini | 3.40 |
| Cancer | 2.75 |
| Leo | 2.96 |
| Virgo | 3.27 |
| Libra | 3.39 |
| Scorpio | 3.09 |
| Sagittarius | 3.37 |
| Capricorn | 2.91 |
| Aquarius | 3.29 |
| Pisces | 3.49 |

## 3. Resolution floor

Runs of adjacent minutes that no question in the bank can tell apart: median 61.0 distinct classes per 61-minute window (range 60-61); median class width 1 min; 100% of classes are a single minute (date windows compared at month precision).
Without date questions (yes/no and choice facts only): median 39.0 classes, median width 1 min, widest 8 min.

## 4. Simulated sessions (greedy, highest-information question first)

| answers come from | questions asked | median 90 % set (min) | 90 % set holds the truth | median peak error (min) |
|---|---|---|---|---|
| the rules at the true minute | 1 | 33.0 | 90% | 7.0 |
| the rules at the true minute | 2 | 22.0 | 90% | 4.0 |
| the rules at the true minute | 3 | 16.0 | 90% | 3.0 |
| the rules at the true minute | 5 | 11.0 | 91% | 2.0 |
| the rules at the true minute | 8 | 8.0 | 92% | 1.0 |
| the rules at the true minute | 12 | 7.0 | 92% | 1.0 |
| half the rules, half chance | 1 | 34.0 | 75% | 13.0 |
| half the rules, half chance | 2 | 25.0 | 71% | 9.0 |
| half the rules, half chance | 3 | 19.0 | 69% | 8.0 |
| half the rules, half chance | 5 | 15.0 | 66% | 6.0 |
| half the rules, half chance | 8 | 12.0 | 64% | 5.0 |
| half the rules, half chance | 12 | 11.0 | 65% | 4.0 |
| chance only (rules carry no truth) | 1 | 33.0 | 55% | 20.0 |
| chance only (rules carry no truth) | 2 | 25.0 | 45% | 20.0 |
| chance only (rules carry no truth) | 3 | 22.0 | 37% | 18.0 |
| chance only (rules carry no truth) | 5 | 18.0 | 31% | 18.0 |
| chance only (rules carry no truth) | 8 | 15.0 | 25% | 18.0 |
| chance only (rules carry no truth) | 12 | 13.0 | 23% | 18.0 |
| typical person's questions; the rules | 1 | 45.0 | 90% | 9.0 |
| typical person's questions; the rules | 2 | 34.0 | 89% | 5.0 |
| typical person's questions; the rules | 3 | 27.0 | 90% | 4.0 |
| typical person's questions; the rules | 5 | 20.0 | 92% | 3.0 |
| typical person's questions; the rules | 8 | 17.0 | 92% | 2.0 |
| typical person's questions; the rules | 12 | 14.0 | 92% | 2.0 |
| typical person's questions; chance only | 1 | 46.0 | 66% | 21.0 |
| typical person's questions; chance only | 2 | 35.0 | 54% | 19.0 |
| typical person's questions; chance only | 3 | 30.0 | 45% | 18.0 |
| typical person's questions; chance only | 5 | 25.0 | 38% | 18.0 |
| typical person's questions; chance only | 8 | 22.0 | 36% | 17.0 |
| typical person's questions; chance only | 12 | 21.0 | 36% | 17.0 |
