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

## Result — the engine covers the major yogas, is blind to the long tail
`yoga_coverage.run()`: the engine's yoga library (`app/core/yoga_library.py`, `YOGA_DETECTORS`)
exposes **29** distinct detectors; **17 / 64 = 26.6%** of Raman's named yogas match. (An earlier pass
reported 13/64 = 20.3% — a *measurement* undercount: the name extractor missed the Pancha-Mahāpuruṣa
factory and solar/lunar positional names. Corrected here. The 64-count denominator also includes a few
OCR-garbled duplicates — "Adhl", "Daiida", "Gola"×2 — so true coverage is a little above 26.6%.)

- **Covered (17):** the whole **Pancha-Mahāpuruṣa** family (Ruchaka, Bhadra, Hamsa, Malavya, Sasa),
  Gajakesari, Sunapha, Anapha, Amala, Budha-Aditya, Daridra, Kemadruma, Lakshmi, Parijata(ha),
  Rajalakshana, Sarpa, Vasi.
- **Missing (long tail, ~47):** the **Nabhasa Ākṛti** family (Gola, Yupa, Sula, Kedara, Hala, Chapa,
  Chakra, Damini, …), the lunar **Dhurdhura**, **Chatussagara** (all kendras occupied), **Sakata**,
  Sankha, Bheri, Gauri, Mahabhagya, Vasumathi, and the *-muladdhana* dhana yogas — plus OCR-garbled
  duplicates that inflate the count.

**The concrete finding:** the engine knows the *major* classical yogas (the full Mahāpuruṣa family, the
luminary and big dhana/rāja yogas) but is blind to the long tail of combination yogas Raman catalogues.
That tail is the mechanical reason the increment-30 yoga-participation strength token was weak — it was
absent on many of the yogas Raman cites. Closing the cleanly-definable part of the gap is increment 35
(below); the outcome corpus + example charts are the durable data that validate it, and the 39 charts'
balance-of-daśā lines also feed the timing corpus.

Reproduce: `PYTHONPATH=. python3 -m app.medini.doctrine.validation.yoga_coverage`. Measurement only;
no engine change. Pinned by `tests/doctrine/test_yoga_coverage.py`.
