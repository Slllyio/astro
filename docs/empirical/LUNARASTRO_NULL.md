# A third null, on the best birth-time data in this repo

**Date**: 2026-08-21
**Corpus**: LunarAstro research-site scrape, 13,703 tier-A (minute-precise) persons
**Screened**: 49 category tags cleared the 200-row threshold; 97 (bank x category)
tests registered, all cleared the sham gate
**Holdout**: 3,450 persons, frozen and unread
**Status**: screening, exploratory — the pre-registration is still all drafts

## Result

**Zero survivors out of 97 tests, at Benjamini-Hochberg q=0.10.**

| | value |
|---|---:|
| Tests registered | 97 |
| Tests admitted (passed every control arm) | 97 |
| Survivors | **0** |
| Sham statistic range across all 97 tests | 0.4819 - 0.5227 |
| Largest delta observed | **+0.0115** (raw_astronomy / `Profession`, p=0.070, n=2,633) |

No chart bank beat its own chartless twin on any of the 49 tested category tags,
at either the `western` (tropical positions/houses/aspects) or `raw_astronomy`
(the same sky with no astrological interpretation) encoding. The single largest
delta observed across all 97 tests does not clear even the uncorrected p<0.05
bar, let alone survive correction across the full family.

These are the figures from the **second** run, after 182 live consultation
requests from private individuals were flagged and excluded (see below). The
first run, which included 122 of them in its cohort, returned the same verdict
— 98 tests, zero survivors, largest delta +0.0122 at p=0.055 — so the
exclusion changed the population correctly without changing the answer.

## Why this corpus is a stronger test than either prior one

This is the third independent screen against a chartless twin in this repo, and
the strongest test of the three on birth-time quality specifically:

* **Gauquelin** (`TIME_BASIS_CONFOUND.md`): 9,390 tier-A persons, 9 professions.
  Registry-sourced, the best *provenance* of the three, but the smallest and
  narrowest test family.
* **Wikidata** (`EVENT_TIMING_NULL.md`): 683k people, but tier C — no birth time
  at all, so houses/ascendant/Moon are untestable by construction.
* **LunarAstro** (here): 13,703 tier-A persons — more minute-precise births
  than Gauquelin — AND 49 distinct outcome categories, the widest target family
  tested against a chartless twin so far in this project.

If natal-chart features carried real signal for who ends up in these
categories, this is the corpus most likely to have shown it: real times, houses
and angles are computable, and the category taxonomy is far richer than a
single profession label.

## What makes this corpus weaker than Gauquelin, honestly

* **No independent verification.** Gauquelin's times come from civil birth
  registries. LunarAstro's `rodden_rating` column — the standard astrological
  source-reliability scale — is present in the schema and **empty on every one
  of the 29,516 raw rows**. Time-tier honesty here rests entirely on the
  minute-frequency measurement (real Gauquelin-style clerical rounding: only
  4 minute values were over-represented enough to downgrade, out of the whole
  corpus), not on any publisher rating.
* **Real defects found and excluded before scoring, not silently absorbed**:
  1,661 rows (5.6%) carried `date_of_birth == 1970-01-01` — the Unix-epoch
  default — several sharing that exact date across wildly different times and
  continents under generic single-word names (dummy/placeholder profiles, not
  notable people). A handful of rows carried a birth year past 2026, including
  one clearly corrupted "19xx -> 20xx" case (a person known to be born in 1927
  listed as 2027). Both classes are flagged `data_quality != ok` and excluded
  from the scored cohort — never dropped silently, never coerced to a
  plausible-looking value.
* **The category taxonomy is a site's own UI structure, not a designed
  outcome variable.** Tags like "Vocation", "Work" and "Notable" are broad,
  overlapping site-collection labels rather than Gauquelin's precise,
  independently-defined profession codes. A null here says the *chart* adds
  nothing over the chartless twin for these tags; it does not certify the tags
  themselves as meaningful psychological or vocational categories.
* **It is not one population, and part of it is private people.** Most rows
  are curated public-figure records. A tail of **182 rows are live
  consultation requests**: private individuals who gave the site their birth
  data and a question, so their "category" is the question itself — a
  sentence about a relative's suicidal ideation, a baby's medical emergency,
  their own depression. This is both a population confound (ordinary
  help-seekers against notable people — a selection boundary a model can
  learn instead of astrology) and a privacy matter (identifiable living
  individuals; publication to a website does not make it research data).
  `lunarastro_import.flag_consultation_rows` flags them
  `consultation_request` so the standard `data_quality == "ok"` filter
  excludes them from any scored cohort, and redacts the narrative so this
  corpus never carries their words. 122 of them had reached the first
  screening cohort; the numbers reported above are from the re-run after
  exclusion (13,703 tier-A rows, down from 13,825).

  The detection rule is "longer than 40 characters and occurring at most 3
  times". It is deliberately not "occurring exactly once": one question can be
  filed against several charts — the corpus carries *"BOTH PARTNERS BORN ON
  SAME DATE. Will we get married?"* on both partners' nativities — and a
  singleton-only rule left exactly those rows unredacted, which is the worst
  case to miss, since a question spanning two charts is more identifying, not
  less.

## The demographic-confound signal, disclosed rather than hidden

Several categories show the **chartless twin alone** scoring very high —
`Vocation` chartless AUC 0.9457, `Career` 0.8666, `marriage` 0.8869. Birth date
and place alone predict category membership on this corpus extremely well,
almost certainly because who ends up in a rich, well-tagged astrological
profile on a research site correlates heavily with era, nationality and
notability — the same "chartless is already strongly predictive" pattern
`docs/empirical/EVENT_TIMING_NULL.md` and the tournament's own standing bar
(lat/lon/date reaching AUC 0.744 on Wikidata marriage) already document. It is
exactly why every chart bank here is scored as a *delta* over that baseline,
never as a raw AUC — a raw `Vocation` AUC of 0.9462 would read as a triumph
with no baseline in sight; scored as `+0.0006` it is what it actually is.

## What this null does and does not cover

**Covers**: tropical Western chart features (positions, Placidus houses,
Ptolemaic aspects) and the raw uninterpreted sky, against 49 category-tag
outcomes, on 13,703 people with real, minute-frequency-verified birth times,
sham-gated and chartless-baseline-scored throughout.

**Does not cover**:

* **Confirmation.** This is screening. The 3,450-person holdout has never been
  read and no pre-registration row is locked — nothing here is a finding.
* **Vedic/sidereal features.** This screen used only the Western tropical
  toolkit (`app/empirical/western/`); it says nothing about Lahiri-sidereal
  placements, dashas, or any doctrine specific to the Raman engine.
* **Categories below the 200-row threshold.** 2,655 of the 2,704 distinct tags
  in the raw scrape never reached the admission floor and were not tested —
  logged as excluded, not silently absorbed into "nothing found."
* **The rectification-ambiguous rows.** 1,044 duplicate names carried genuinely
  conflicting birth data across rows (different claimed times/places for what
  may or may not be the same person). Identity here is the chart fingerprint
  only, never the name, so these became separate, independently-scored rows —
  correct for a corpus where name collisions are common, but it means no
  attempt was made to resolve which claimed time (if either) is correct.

## Reproduce

```bash
python3 -m app.empirical.acquire.lunarastro_import \
    --raw path/to/raw_lunarastro.csv --out data/empirical/lunarastro.csv
python3 -c "
from app.empirical.tournament.lunarastro_corpus import read_lunarastro_corpus
from app.empirical.tournament.build_feature_banks import build_banks
rows = read_lunarastro_corpus('data/empirical/lunarastro.csv')
frame, _ = build_banks(rows)
frame.to_parquet('data/empirical/lunarastro_feature_banks.parquet', index=False)
"
python3 -m app.empirical.tournament.run_screening_lunarastro \
    --banks data/empirical/lunarastro_feature_banks.parquet \
    --out data/empirical/lunarastro_screening_report.json
```

The raw scrape itself is not part of this repository (see `data/` — gitignored
throughout `app/empirical`); it was supplied directly for this run and is not
redistributed here.
