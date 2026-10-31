# Real-people blind test of the For-and-against reader: pre-registration

Fixed 2026-10-31, before any person is entered. Tool: `tools/raman_saab/real_people_test.py`.

## Question

When the reader (v43, "For and against, matter by matter") leans favourable or afflicted on a
matter, does that match the confirmed facts of the person's life more often than the same reader
run on **someone else's chart**? The shuffled-chart control matters most here. It soaks up base
rates (most people have a living mother, a career and so on), so any edge left over has to come
from the chart itself.

Context: the 2026 Astro-Databank validation (about 47k charts) found no edge for house verdicts
(AUC 0.49 to 0.51). This test is smaller. What it adds is facts confirmed first-hand and a reader
that has not been tested before. It can find only a large effect.

## Participants

- People the user knows, or their family, who agree to take part.
- Each needs a date, a place and a birth time recorded to within 30 minutes.
- Target: at least 30 people. Scoring is not run below 20.
- The time-quality field is recorded. Rectified or guessed times are excluded.

## Sequence (order is binding)

1. The user sends only birth data, as PEOPLE.json.
2. `seal` runs. The SHA-256 of `sealed.json` goes into the log below and is committed and pushed.
3. Only after that does the user collect answers to the fixed questionnaire
   (`REAL_PEOPLE_QUESTIONNAIRE_2026-10-31.md`). The person answering never sees the reading.
4. `score` runs once with the committed hash. Results are reported whatever they show.

## Items and coding (fixed)

There are 15 items (Q01 to Q15), each mapped to one matter (see `QUESTIONS` in the tool). Each
answer is coded good, bad or na using the rules printed in the questionnaire. Coding happens
before scoring and without looking at the sealed file.

The reader commits only when the lean is "leans favourable" or "leans afflicted". "Evenly
balanced" and "no rule speaks" are abstentions. The clause judge (favourable or afflicted; mixed
counts as an abstention) is scored the same way as a secondary reader.

## Primary measure and decision rule

- **Per person:** d = own-chart accuracy minus the mean accuracy of every other batch chart,
  scored against the same person's facts.
- **Statistics:** one-sided person-level sign-flip permutation (20,000 draws, seed 20261031) and a
  90% bootstrap CI on mean d.
- **SIGNAL:** N ≥ 20 and p < 0.05.
- **BOUNDED_NULL:** N ≥ 30 and the upper end of the 90% CI on mean d is below +0.10.
- **Otherwise:** UNDERPOWERED.

Also reported: "always good" accuracy, and the clause judge's result.

## Privacy

Birth data, names and facts stay in `/mnt/project-files/astro/real_people/` and are never
committed. The repository holds only this protocol, the tool, hashes and aggregate results.

## Log

| Date | Event | sha256 / note |
|---|---|---|
| 2026-10-31 | Protocol and tool committed; tool checked on synthetic data only | n/a |
| 2026-10-31 08:35 UTC | Batch 1 sealed: 20 people (P01-P20), birth details only; no facts collected. Vaishali excluded (her facts were seen 2026-10-30 before any seal). Assumptions: "sitaberi mela ground" cast at Nagpur Sitabuldi 21.15N 79.08E, "05.34" read as a.m., Sultanpur MP cast at Raisen-district Sultanpur 23.14N 77.93E; time quality "family-given" for all | cc1e6bb39eabbd22907db979890cfe923cf70faf179fd79c093088e646ae19fb |
