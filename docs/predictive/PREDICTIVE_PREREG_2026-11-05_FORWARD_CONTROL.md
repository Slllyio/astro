# Forward log: swapped-chart control (addendum 5), 2026-11-05

Written before any control answer is computed and before any forward question is resolved. The
owner approved it on 2026-11-05 ("All", to three proposals; this is the third).

## What is added

With each locked question, the log also locks KP's answer from **20 swapped charts**, made by the
same code at the same moment:

- **Horary (number-based) answers:** the same question, moment and place, judged from 20 other
  horary numbers drawn at random (without replacement, from 1-249 minus the asker's number, using
  the operating system's random source). The ruling planets of the moment are the same for all;
  only the chart cast from the number changes.
- **Natal answers (optional `--birth` block):** the same matter and question window, judged from
  20 birth charts with the same birth date and place and a random clock time each.

The swapped answers are stored next to the real one. Whoever settles a question only records
what happened (yes or no, the date, the evidence) and never chooses between answers, so no blinding
step is needed. The outcome is a documented fact, and the scoring is done by code.

The 10 public questions already locked on 2026-11-03 get their swapped answers as a separate,
hash-chained `decoys` record (one per question), added before any of them is resolved. The swapped
numbers are random, so knowing that an early match in one series has been played cannot influence
them.

## The comparison

Only questions where KP gives a decided answer (YES/PROMISED or NO/DENIED) count. For a swapped
chart, only its decided answers count.

- **Primary statistic:** the number of questions on which the real chart's answer is right.
- **Null:** if the real chart carries no information, it is just one more draw among its swapped
  charts. The null distribution comes from picking, for each question, one answer at random from
  {real, decided swaps} (100,000 draws). p = share of draws with as many right as the real chart
  or more. This uses each question's own chance level, so it does not assume 50%.
- **Reported beside it:** the real chart's accuracy, the swapped charts' mean accuracy, their
  difference with a bootstrap 95% interval over questions, and the comparison against the asker's
  own guesses (McNemar test, as before).

## When it is judged, and with how many

One look per arm (personal and public, never pooled), when an arm reaches **85 decided, resolved
questions**. At that size, the test has 80% power to detect the real chart being right 65% of the
time against 50% for the swaps, at one-sided α = 0.025. Smaller gaps need more questions: 60%
against 50% needs about 200.

The swapped control does not reduce the number of questions needed. What it fixes is the chance
level: KP's own base rate of "yes" answers, and how often a random number happens to be right,
are measured rather than assumed.

**Pass:** p < 0.025 AND real accuracy at least 10 points above the swapped mean. Reported as
SIGNAL, BOUNDED_NULL (the 95% interval of the difference lies below 10 points) or UNDERPOWERED.
