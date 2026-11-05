# Engine-blind hold-out extraction brief

You are extracting a SEALED HOLD-OUT test set of B. V. Raman's own worked nativities for a
Vedic-astrology engine that tries to reproduce Raman's conclusions. The value of this set
depends entirely on it being ENGINE-BLIND.

## Hard rules
- Do NOT run any code under /home/claude/astro/app, do NOT read files under
  /home/claude/astro/app/raman_saab/judges or /home/claude/astro/app/raman_saab/doctrine,
  and do NOT read /home/claude/astro/tests/fixtures/*.json* . You must not know what the engine says.
- Never read anything under /home/claude/astro/data/private/.
- Read only the source text range you are assigned. Python for parsing text is fine.
- Work from Raman's printed text. The text is OCR and noisy: digits are often garbled
  (l→1, I→1, t→1 or 7, S→5 or 8, B→8, g→9, O/o→0, E→8 ...). Give your best reading AND copy
  the raw OCR string, and flag every digit you were not sure of.

## What to extract, per chart
For each chart (horoscope of a real native) in your range:
- chart_no, first_line, last_line (line numbers in the file, 1-based, as `grep -n` prints them)
- raw_birth: the birth-data line(s) verbatim
- birth: {date "YYYY-MM-DD", time "HH:MM" (24h), time_basis: "LMT"|"IST"|"ghatikas_after_sunrise"|"other", ghatikas (if given, as printed, e.g. "38-10"), lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir, place (if named)} — null fields where not printed
- uncertain: list of the fields whose digits you had to guess, with the alternatives
- dasa_balance: as printed (e.g. "Venus 2-4-24") — this is used to verify the birth data
- lagna_sign_stated: the Lagna sign if Raman's prose or the chart names it (e.g. "Lagna is Scorpio"), else null
- same_as: if Raman says this chart is the same native as another chart number, or the birth data equals another chart's, note it
- conclusions: a list. Each item is ONE conclusion Raman reached about ONE matter of THIS native's life:
  {house: "H1".."H12", signification: one key from the vocabulary below,
   verdict: "favourable"|"afflicted"|"mixed", quote: verbatim words (<= 300 chars),
   line: the line number where the quote starts, why: one sentence on how the quote maps to the verdict}

## The confirmation rule (this is the whole job)
- A conclusion is what Raman says HAPPENED or WILL be the case for the matter in this life:
  "the native became a judge of the High Court" (H10 career favourable); "lost his father early"
  (H9 father afflicted); "had no issues" (H5 children afflicted); "immensely rich" (H2 wealth favourable).
- An OBSERVATION about one factor is NOT a conclusion: "the 5th lord is debilitated",
  "Jupiter aspects the Lagna", "this is a powerful Raja Yoga". Do not record these.
- A statement that a yoga is present is NOT a conclusion about a matter, UNLESS Raman says
  what it produced in this native's life ("the yoga made him a minister" → H10 favourable).
- mixed = Raman explicitly names BOTH poles as operative for the matter in this life
  ("rose to power, then lost everything"; "two marriages, the first wife died"). Not a weak or
  qualified single-pole statement: "moderately well off" is favourable-but-modest → favourable;
  "fairly good education" → favourable; "ordinary" or "not much" → afflicted only if Raman
  frames it as a deficiency.
- If you cannot tell which way Raman went, leave it out. Never guess to fill.
- Generic statements about the yoga in general (not this native) are not conclusions.

## Signification vocabulary (house: keys)
H1: self, body, health | H2: wealth, speech, vision | H3: siblings, courage, ear_throat |
H4: mother, education, happiness, property, vehicles | H5: children, intellect |
H6: enemies_disease, disease_chronic, enemies, debts | H7: marital_happiness, spouse, coverture, virility, partnership |
H8: longevity, death | H9: father, fortune, dharma, long_journeys |
H10: career, status_honour, profession_authority, profession_learned |
H11: gains, elder_siblings, acquisitions | H12: incarceration, expenditure, moksha, left_eye
Use "self" for general character/personality/eminence of the person as a whole, "career" for
profession/position, "status_honour" for fame/honours/titles, "fortune" for luck/general prosperity,
"wealth" for money and riches, "longevity" for length of life (long/short), "death" for the manner of death.

## Output
Write a JSON list (one object per chart, including charts with zero conclusions so we see coverage)
to the output path you are given, then reply with: number of charts, number with birth data,
number of conclusions, and any chart you could not parse.
