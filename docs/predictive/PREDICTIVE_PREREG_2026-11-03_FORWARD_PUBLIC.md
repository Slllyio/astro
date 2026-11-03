# Forward log, public-event arm (addendum 4 to PREDICTIVE_PREREG_2026-11-02), 2026-11-03

Written before any public question is logged. The owner asked to run the forward ruling-planet
test (2026-11-03, "do it"); public questions are added so the log fills faster than personal ones.

- **Questions:** yes/no, about public events with a fixed, documented resolution date (sports
  results, central-bank decisions, published market closes). No question about any person's
  health, life or death. No personal or relatives' data.
- **Horary number:** not chosen by a person. It is `int(sha256(question text + "|" + local question
  time).hexdigest(), 16) % 249 + 1`, so it is fixed by the wording and the moment and cannot be
  picked after seeing an answer.
- **Moment and place:** the minute the entry is logged, at New Delhi (28.6139 N, 77.2090 E,
  UTC+5:30), the same neutral place for every public question.
- **Matter:** `house11` (KP's general house of fulfilment; the question is phrased so that "yes"
  is the asked-for outcome).
- **Asker's prior:** Claude's own probability of "yes", written in the same command before KP's
  answer is computed, from public information at that time. Quarter = the quarter the event
  resolves in.
- **Scoring:** as the personal arm (KP right >= 65% on >= 85 decided questions AND better than the
  asker on the same questions, McNemar), but the public arm is scored and reported on its own and
  is never pooled with personal questions.
- Entries are committed to git right after logging, so each lock carries a public date.

Log file: `docs/predictive/forward_log/public.jsonl` (personal questions stay in `questions.jsonl`).
