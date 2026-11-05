# Cited tools: the cited reading, the classical library, the study view

Built 2026-11-03 at the user's request ("I want first 3"), on top of the house audit
(`house_audit.py`), the for-and-against count (`for_against.py`) and the click-to-source
citations the engine already had. Code: `app/raman_saab/cited/`. Tests:
`tests/raman_saab/cited/`.

None of the three changes a verdict, and none makes a predictive claim. They answer "what do
the books say about this, and why", never "what will happen".

## 1. The cited reading (`cited/reading.py`)

One chart, all twelve houses, each read the way a verdict is defended:

- the verdict per matter, beside the plain count of Raman's rules for and against it;
- every rule that fired, with Raman's reading, its citation, and the book's own lines (opens in
  place when the book texts are on the machine);
- whether each rule's condition survives Raman's Bhava and sandhi devices;
- which clause decided each matter, and the verdict without doubtful rules (a sensitivity flag);
- Raman's conclusions on comparable charts of his, each with the line where he wrote it;
- the house re-judged at -20, -10, -5, +5, +10 and +20 minutes.

The page opens with a fixed honesty notice carrying the measured figures: 238 of 365 in-sample (after the 2026-10-31 full-pool label re-review),
23/36, 55/134 and 29/64 on the sealed hold-outs, 131/198 for the plain count, and the null on
real lives.

When the chart is one of Raman's own worked examples (`--golden`), his write-up of the chart and
his conclusion for each house he judged appear beside the engine's.

```
python -m app.raman_saab.cited read --name "Native" --date 1950-01-01 --time 12:00 \
    --tz 5.5 --lat 13.0 --lon 77.6 --out reading.html          # or --format md
python -m app.raman_saab.cited read --golden NH.chart_47 --out roosevelt.html
```

A chart takes about two seconds (most of it the six birth-time re-casts; `--no-stability`
skips them).

## 2. The classical library (`cited/library.py`)

One SQLite full-text file, `data/library/library.sqlite` (gitignored, about 20 MB), holding:

| Kind | What | Count (cloud build, 2026-11-03) |
|---|---|---|
| passage | every book file the citation resolver knows, cut at paragraphs, each with the exact line span as a citation token | 21,603 |
| rule | every rule in the engine's rule store, with its reading and citation | 1,023 |
| example | every confirmed conclusion Raman reached on a worked chart, located to his line where it is a verbatim quote | 389 (365 after the 2026-10-31 label re-review) |

The cloud build covered the Raman books, Prasna Marga and KP Readers 1-6. On the PC the build
also picks up BPHS and Phaladeepika (corroboration) and the Rao lineage books, so the passage
count will be higher there.

Every hit carries a scope label so systems never mix silently: `Raman, natal`,
`Raman, Jaimini system`, `horary`, `electional`, `annual`, `classical, not Raman`,
`Rao lineage, not citable`, `KP, a separate system`.

Search is plain word matching (BM25), with a short fixed list of equivalents (`7th`/`seventh`,
`marriage`/`kalatra`/`spouse`, `lagna`/`ascendant` ...; `SYNONYMS` in the module). Every
search reports the words it actually searched for, and whether all of them had to match or it
fell back to any of them. No model is involved and nothing leaves the machine.

```
python -m app.raman_saab.cited library build
python -m app.raman_saab.cited library search "seventh lord in the eighth"
python -m app.raman_saab.cited library search "kemadruma" --kind example
python -m app.raman_saab.cited library search "sub lord of the 7th cusp" --scope KP --full
python -m app.raman_saab.cited library passage HTJAH-I:1586 --context 8
```

Rebuild after any change to the book texts (for example an OCR fix), since citation line
numbers come from the files.

## 3. The study view (`cited/study.py`)

Each of Raman's 235 worked charts that carry a confirmed conclusion, with:

- the chart, cast as the scored harness casts it;
- Raman's own write-up, verbatim;
- for each matter he judged: his verdict and words, with the line where he wrote them, beside
  the engine's verdict for the same matter, its count of rules for and against, and each rule
  with its citation and text;
- whether the two agree, are one step apart, or are opposite.

The index page totals are the scored in-sample figure, and a test pins them to the golden
harness: 238 agree, 94 one step apart, 33 opposite, on 365 conclusions (re-based 2026-10-31
after the full-pool label re-review; it was 263/91/35 on 389 when the tool was built). The page
says plainly that these are the charts the engine was built against.

209 of the 365 conclusions are verbatim quotes that the tool finds at their exact lines (within
400 lines of the chart's own citations; a match elsewhere in the book is never used). The
other 156 labels are a reviewer's summary or a heavily elided quote; for those the page points
to Raman's full write-up of the chart instead.

```
python -m app.raman_saab.cited study --out data/study                 # static site, ~3 s
python -m app.raman_saab.cited study --out data/study --readings      # plus a cited reading per chart (~8 min)
```

## All three in the browser

```
python -m app.raman_saab.cited serve          # http://127.0.0.1:8765/
```

Standard library only, bound to 127.0.0.1. Pages: `/` (search box, birth form), `/search`,
`/passage?cite=...`, `/study/`, `/study/<record>.html`, `/read?golden=<record>`,
`/read?name=&date=&time=&tz=&lat=&lon=`.

## Limits, stated plainly

- The book texts are OCR. Some passages carry OCR noise; the citation tokens still point at the
  exact lines, so the scan can be checked.
- The library finds words, not meaning. A question phrased differently from the book can miss;
  the "any word" fallback and the equivalents list reduce this but do not remove it.
- Precedents ("Raman on comparable charts") are associations in his printed verdicts, not a
  causal test, and a few charts share only one feature.
- Raman's verdicts on famous lives drew on what he knew of them; the engine's reading of a
  chart is his rules applied faithfully, which on real lives has not predicted outcomes.

## How sure the books are: the spread of indications (added 2026-11-05)

Requested after `HOW_ASTROLOGERS_PREDICT_2026-11-05.md` (section 2.1, too many indications).
Code: `cited/spread.py`. No verdict changes; it re-reads the same ledgers the count uses.

For every matter the reading and the study view now say, in a plain sentence, whether Raman's
rules point for it, against it, both ways, or not at all, with the number of descriptive rules
beside them. Each sentence is set against a fixed baseline: the same count on 2,000 seeded
random charts (date 1920-2010, any time, latitude -40 to 60), stored in
`cited/spread_baseline.json` and rebuilt with
`python -m app.raman_saab.cited spread-baseline` (about 80 s).

The top of each reading carries one line for the whole chart. On Roosevelt's chart: 26 of 57
matters have rules both ways; on the random charts a matter has rules both ways 41% of the
time. Some matters show "both ways" on most charts (self 82%, speech 86%, father 73%), and a
few can never show it because the engine holds rules for only one side (ear and throat:
against only; wealth through marriage: no rule fires on any random chart). The line also says
that a one-sided count is not certainty: the engine holds about 29% of the reasons Raman states
(REASON_CODING_RESULTS_2026-10-31.md).

Rebuild the baseline whenever a rule or the judge changes, since the shares come from the
engine's own rules.
