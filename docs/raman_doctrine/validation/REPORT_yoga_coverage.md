# Increment 34 — Three Hundred Important Combinations: a fresh yoga corpus + engine coverage audit

## Why this exists
The 9-grade **strength** vein is exhausted across *all* of B. V. Raman's books (increments 29–33; a
full archive.org catalog check confirmed only *How to Judge a Horoscope* + *Notable Horoscopes* carry
"the Nth house/lord is [graded]" verdicts, both mined; *Graha and Bhava Balas* is a shadbala method
book with ~1 narrative verdict). The user chose to bring in genuinely fresh data of a **different
kind**: yoga-outcome material from *Three Hundred Important Combinations* (archive.org
`in.ernet.dli.2015.83552`, DjVuTXT). This book catalogues yogas, each with a **Definition**
(antecedent combination), **Results** (stated outcome), and **example charts**.

## What was extracted (durable corpus)
`docs/raman_doctrine/validation/corpora/three_hundred_yogas.json` — **64 yogas** parsed (Definition +
Results + a coarse multi-label outcome class), and **39 example-chart birth lines**. Extracted verbatim
from the archive.org djvu OCR (the fuller of the two available renderings — a user-supplied .mht of the
same book was the identical OCR but a ~half-length partial capture, so the djvu was kept). The book
text itself is not committed (SOURCES policy). Outcome-class distribution (Raman's stated effects):
wealth 27 · authority 20 · fame 19 · character 13 · learning 13 · longevity 8 · misfortune 7.

## The honest scope — one question answered, one deliberately not
- **Coverage (answered, non-circular):** of the yogas Raman names, how many does our engine's yoga
  library actually know? This is a concrete gap map — and it directly explains why the increment-30
  yoga-participation strength token was a documented negative.
- **Outcome prediction (NOT answered):** Raman's yoga→outcome is **doctrine** (his stated effect), so
  scoring a model that predicts his outcome from his combination is circular. A genuine test needs
  real-birth people with known life outcomes — the deferred population track (Track B). No accuracy
  number is claimed here.

## Result — the engine covers the major yogas, was blind to the long tail
`yoga_coverage.run()` scores coverage on the corpus's **distinct** yogas (OCR duplicates like "Gola"×2
deduped) with **exact** stem matching (an earlier loose substring matcher gave false positives —
"Hala"⊂"Kahala", "Raja"⊂"Rajalakshana" — and its name extractor also undercounted the engine by missing
the Pancha-Mahāpuruṣa factory + solar/lunar positional names; both corrected). On that honest basis the
engine's yoga library (`app/core/yoga_library.py`, `YOGA_DETECTORS`) started at **15 / 62 = 24.2%** —
it knew the *major* classical yogas (the full Mahāpuruṣa family, the luminary and big dhana/rāja yogas)
but was blind to the long tail (Nabhasa, Chatussagara, Sakata, Dhurdhura, the lord-config dhana yogas).
That tail is the mechanical reason the increment-30 yoga-participation strength token was weak — the
detector was absent on many of the yogas Raman cites.

Increments 35–36 encode the cleanly-definable part of the tail, raising coverage **24.2% → 41.9%**
(15 → 26 of 62 distinct yogas). Reproduce:
`PYTHONPATH=. python3 -m app.medini.doctrine.validation.yoga_coverage`; pinned by
`tests/doctrine/test_yoga_coverage.py`.

## Increment 35 — occupancy-only yogas (no daśā, no lord-strength)
8 yogas computable from sign/house occupancy alone, each faithful to Raman's stated Definition:

| yoga | Raman No. | definition encoded |
|---|---|---|
| Dhurdhura | 4 | planets on both sides of the Moon (2nd AND 12th from it) |
| Chatussagara | 8 | all four kendras (1,4,7,10) occupied |
| Vasumathi | 9 | benefics in the upachayas (3,6,10,11) from Lagna or Moon |
| Sakata | 12 | Moon in the 6th/8th/12th from Jupiter |
| Chakra | 84 | all seven planets in odd houses (1,3,5,7,9,11) |
| Gola / Yuga / Sula | 101 | the seven planets confined to one / two / three signs (Nābhasa Saṅkhyā) |

## Increment 36 — lord-based yogas (definitions taken from a cleaner OCR edition)
The increment-34 djvu was noisy ("plawts", "Mo('n"); a cleaner archive.org edition
(`ThreeHundredImportantCombinationsInVedicAstrology`, 0 garble hits) supplied the exact wording. 7
yogas computable from lord placement + dignity (no navāṁśa, no daśā):

| yoga | Raman No. | definition encoded |
|---|---|---|
| Parvata | 14 | benefics in kendras; 6th & 8th empty or benefic-occupied |
| Kahala | 15 | 4th & 9th lords in mutual kendras with a strong Lagna lord |
| Chapa | 31 | exalted Lagna lord with a 4th–10th lord exchange (parivartana) |
| Sreenatha | 32 | exalted 7th lord in the 10th, 10th lord in the 9th |
| Sankha | 45 | 5th & 6th lords in mutual kendras with a strong Lagna lord |
| Bheri | 46 | Venus, Lagna lord & Jupiter in mutual kendras; strong 9th lord |
| Samudra | 72 | all seven planets in even houses (2,4,6,8,10,12) |

Added to `YOGA_DETECTORS` (29 → 44 detectors across both increments). All 46 existing yoga unit tests
stay green; `house_judgment.py` and `synthesis_v2.py` are byte-untouched (the additions live in the
`app/core` reading library — no strength-grade impact). Pinned by `test_yoga_coverage` (coverage floor +
per-detector faithfulness checks: each new yoga fires on a chart built to its definition and is silent
otherwise, incl. a Kahala negative when the Lagna lord is weak). The residual ~36 missing yogas need
navāṁśa (Mridanga, the other Gola), full-Moon, or intricate multi-lord conditions, or are OCR-garbled
duplicates — a further increment, not force-fit here.
