---
title: "Golden validation worksheet — House 3 (Sahaja / siblings), DRAFT → CONFIRMED"
kind: worksheet
topic: validation
measured: true
updated: 2026-07-24
words: 637
tags: [raman-saab, worksheet, validation]
---
# Golden validation worksheet — House 3 (Sahaja / siblings), DRAFT → CONFIRMED

**What this is:** the 12 House-3 DRAFT goldens (`tests/fixtures/raman_goldens.jsonl`, charts 52-63)
for your validation. House 3 is the second fully-developed house — confirming these unlocks the
**two-house requirement** the tuner needs (F11) to calibrate the preponderance cutoffs.

**How to validate:** for each row pick the ordinal you read from Raman's prose; tell me the calls
(e.g. "apply drafts except 53→mixed") and I flip `verdict_review` to CONFIRMED + re-measure +
re-base the baseline in that commit. Convention: `insufficient-evidence` = ABSENT testimony only;
explicit negative = `afflicted`, explicit positive = `favourable`, granted-then-lost = your call.

**Most of this batch is clear** (the "no brothers" and "deaf" charts are unambiguous). Only 3
sibling-loss ordinals are genuinely contestable — flagged below.

## Sibling charts (9)

| Chart | Raman's conclusion (gist) | Draft | Note / contest | Your call |
|---|---|---|---|---|
| 52 | "6 born, 3 died early; resourceful, courageous, skilful" | **mixed** | granted-but-partial-loss — mixed vs favourable? | ☐ |
| 53 | "3rd lord & Mars well disposed; blessed with a number of brothers & sisters" | favourable | reviewer suggests **mixed** (claims 3 died — but the prose here is positive); your call | ☐ |
| 54 | "3rd lord Saturn powerful; native will have brothers; only two brothers" | favourable | minimal (2) but granted — favourable defensible | ☐ |
| 58 | "house + lord of brothers (Mars) under severe affliction (only Jupiter aspect)" | **afflicted** | clear; *lagna flagged below* | ☐ |
| 59 | "3rd lord Venus combust & powerless → against having brothers" | **afflicted** | clear | ☐ |
| 60 | "Karaka Mars & 3rd house afflicted → the native has no brothers" | **afflicted** | clear | ☐ |
| 61 | "3rd Papakartari in Amsa + afflictions, Karaka weak → denying [brothers]" | **afflicted** | clear | ☐ |
| 62 | "lord-cum-Karaka Mars debilitated in 6th with waning Moon → no brothers" | **afflicted** | clear | ☐ |
| 63 | "Lagna, Mars-in-Lagna, exalted 3rd-lord all connected → cordial relations" | favourable | clear; *sign-only (birth withheld at HTJAH-I:3874)* | ☐ |

## Ear / throat / deafness charts (3) — newly routed to the `ear_throat` signification

I added an `ear_throat` signification to House 3 (a real karya — HTJAH-I:3325 lists "throat, ears";
Mercury karaka) because Raman judges **deafness** on these, not sibling count. They were mis-bucketed
under "siblings" — now corrected. The verdict is unambiguous (deaf = afflicted ear/throat):

| Chart | Raman's conclusion | Draft (ear_throat) | Your call |
|---|---|---|---|
| 55 | "3rd lord Venus in 12th with Mars, both Papakartari → somewhat deaf" | **afflicted** | ☐ |
| 56 | "3rd aspected by Saturn, 3rd lord debilitated in 6th → partially deaf" | **afflicted** | ☐ |
| 57 | "3rd aspected by Mars & Venus, Moon-3rd-lord aspected by Saturn → partially deaf" | **afflicted** | ☐ |

## Data flags for your eye (not verdicts)
- **chart_58 lagna:** printed time 4:30 p.m. fresh-casts Capricorn Lagna (3rd = Pisces), but Raman's
  prose states 3rd = Aries (⇒ Aquarius Lagna, reached ~5:30 p.m.) — a ~1h book inconsistency. I left
  `lagna_sign` null. Confirm whether to correct the printed time to ~5:30 p.m.
- **chart_53 OCR:** year decoded from `24-8-18*0` as 1880 (fresh-cast Pisces Lagna corroborates);
  longitude `5h.20m E` read as 80°E. Confidence 0.5 — cross-check if you have the source.
- **chart_63:** Raman withheld the birth details (HTJAH-I:3874) — sign-only record, Track-B only.

**Engine vs golden note:** the engine currently judges chart_63 `afflicted` (only "malefic in 3rd"
fires) where your draft is favourable — once you confirm, that becomes a Stage-4 H3 mismatch-target
(the cordial-relations combination H3.C.30 may not be firing; I'll investigate).
