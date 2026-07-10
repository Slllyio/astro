# Verdict audit — our scored corpora vs the clean HTJAH full text

Every held-out / fresh corpus verdict was extracted from OCR'd PDF scans or vision reads,
both error-prone. A clean full-text capture of both HTJAH volumes (a browser-saved
archive.org page — clean *prose*, but **no chart figures**) lets us cross-check those
verdicts against a garble-free source. `audit_verdicts.py` does this automatically.

## Key structural finding — the clean text fixes *garble*, not the *offset*

The clean text removes the OCR garble that bit us (dates like `18*0`, `henefice`→benefic,
dropped verdict words). It does **not** remove the layout hazard: **Raman's per-chart
analysis is physically offset from its diagram/birth-line.** A birth-line block still reads
`Chart No. 98 … Conclusion.—[chart 98's conclusion] … The Fifth House.—In Chart No. 99 …`
— i.e. the House/Lord/Kāraka analysis that trails a birth line belongs to the **next**
chart. Correct attribution therefore requires the in-prose `In Chart No. N` markers, not
proximity to a birth line (the audit tool keys on exactly those markers, and joins to our
corpora by **birth date**, since chart *numbers* restart per volume).

This directly vindicates two Tier-2 decisions: dropping ch65/ch91 for "ambiguous
attribution" was correct — the offset is real and present even in clean text, so a
proximity-based read would have mis-paired their verdicts.

## Result — zero verdict disagreements

| metric | value |
|---|---|
| charts recovered from the clean text | 201 |
| scored corpus charts matched by birth date | 28 |
| stored-mappable verdict rows on those charts | 12 |
| rows where the clean source ALSO maps to a grade | 6 |
| **agreement (clean-mappable rows)** | **6 / 6 (100%)** |
| **disagreements** | **0** |

Where a stored verdict and the correctly-attributed clean verdict both resolve to a grade,
they **agree in every case**. The one apparent mismatch a naive (proximity) pass produced
— ch98 lord "weak" vs "moderate" — was the *audit's own* offset error (it had grabbed
ch99's lord); with in-prose attribution it disappears, and the stored ch98 "weak" is
confirmed correct. **No mis-attribution or garble error was found in the scored corpora.**

## Honest limits
- **Coverage, not correctness, is the ceiling.** Only 6 rows are *automatically*
  cross-checkable (both sides must map through the pre-registered grade lattice); the clean
  factor sentence often states the verdict in words the map — correctly — won't grade. The
  audit proves the checked rows are clean; it does not exhaustively re-grade all ~150.
- **34 scored charts weren't matched by date** — some are Vol II nativities whose clean-text
  dates didn't extract, some are date-format edge cases. Not evidence of error; unmatched
  charts are simply not cross-checked here.
- The `.mht` has **no figures**, so it can validate *verdicts* but cannot supply the *sign
  grids* — it cannot, on its own, recover the offset-dropped charts' scores.

## What this unlocks next
The clean text is the garble-free **verdict** source. Combined with vision grids (or
prose-reconstructed rāśi for placement-rich charts), it lets us re-attempt the
offset-dropped fresh charts (ch65, ch91) and add new house-chapter charts with verbatim,
correctly-attributed verdicts — growing the held-out set without the OCR hazard.

## Files
- `app/medini/doctrine/validation/audit_verdicts.py` — offset-aware clean-text extractor +
  by-date corpus cross-check (`HTJAH_CLEAN_TEXT` points at the extracted text).
