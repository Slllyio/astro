# Forward question log: how to use it

Started 2026-11-03 by the owner's choice to keep the sealed sets closed and test going forward
instead. Rules: pre-registration addendum 1 (item 6) and addendum 2 (Arm B format).

## Why this test is different

Every past test looked back at events already known. Here the answer is written down and locked
before anyone knows the outcome, so nothing about the result can shape the reading. It is also the
only fair test of KP ruling planets and horary, which need the moment a question is asked, and it
uses exact times (the question moment), which the sealed sets do not have.

## Asking a question (one per real, pending matter)

Needed, all recorded at the moment of asking:

1. **The question**, yes/no, about something that will be settled in 12 to 24 months
   ("Will I change jobs?", "Will the house sale close?"). Not about death, lifespan or serious
   illness.
2. **The area**: career, marriage, children, health, wealth, education, travel, parents, other.
3. **A KP horary number from 1 to 249**, said by the asker without thinking about it.
4. **Exact local time and place of asking** (time to the minute, city).
5. **The asker's own guess**: how likely is "yes", from 0 to 1, and the quarter they expect it in
   (e.g. 2027Q2). This is the bar KP has to beat.
6. **The window**: from today to a date 12-24 months away.

Send these in the project thread, or run:

```
python -m tools.predictive.forward_log ask --log docs/predictive/forward_log/questions.jsonl \
  --text "Will I change jobs?" --area career --matter service --number 117 \
  --when "2026-11-03 10:42" --tz 5.5 --lat 26.45 --lon 80.33 \
  --prior 0.6 --quarter 2027Q2 --window 2026-11-03:2028-11-02
```

`--matter` is a KP matter (marriage, children, health, wealth, service, house<N>), or use
`--question <key>` for one of the 35 named KP question rules (promotion, go_abroad, start_business,
...). The tool computes KP's verdict and the ruling planets right away and prints a hash; commit the
log file straight after, so the lock carries a public date.

## Public-event questions

A second log, `docs/predictive/forward_log/public.jsonl`, holds questions about public events with
fixed result dates (rules: `PREDICTIVE_PREREG_2026-11-03_FORWARD_PUBLIC.md`). The horary number is
derived from a hash of the wording and moment, the place is New Delhi, the matter is house 11, and
the "asker" prior is Claude's. It is scored on its own, never pooled with personal questions
(`questions.jsonl`).

## Swapped-chart control (addendum 5, from 2026-11-05)

Every question also locks KP's answer from 20 swapped charts: 20 other horary numbers at the same
moment, and (with `--birth`) 20 birth charts on the same date at random clock times. If the real
chart knows something, it should be right more often than its own swaps. This measures the chance
level instead of assuming 50%. Rules: `PREDICTIVE_PREREG_2026-11-05_FORWARD_CONTROL.md`. The 10
public questions locked on 2026-11-03 got theirs as `decoys` records (`add-decoys --id N`) before
any was resolved.

## Settling a question

When the event happens: `resolve --id N --outcome yes --date YYYY-MM-DD --evidence "..."`.
A "no" can only be recorded after the window closes (the tool refuses earlier). Check the chain with
`verify`; score with `score`.

## When it is judged

At 85 or more decided questions, once per arm. KP passes if it is right at least 65% of the time AND
beats the asker's own guesses on the same questions (McNemar test). The swapped-chart comparison is
judged at the same point: p < 0.025 and the real chart at least 10 points above its swaps. Results are reported whichever way they
come out.

## Privacy

Only the question moment and place are stored, no birth data. Nobody's past personal data from this
project is used.
