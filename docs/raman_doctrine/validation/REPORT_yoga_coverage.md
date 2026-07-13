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

## Result — the engine is blind to ~four-fifths of Raman's catalogued yogas
`yoga_coverage.run()`: the engine's live yoga library exposes **24** distinct detectable stems;
**13 / 64 = 20.3%** of Raman's named yogas match.

- **Covered:** Gajakesari, Sunapha, Anapha, Amala, Budha-Aditya, Daridra, Kemadruma, Lakshmi,
  Parijata(ha), Rajalakshana, Ardha-Chandra, Sarpa, Vasi.
- **Missing (blind spots, 34):** the entire **Pancha-Mahāpuruṣa** family by member name (Bhadra, Hamsa,
  Malavya, Ruchaka, Sasa — the engine references "Mahapurusha" only as a group, not each member), plus
  Sakata, Sankha, Chatussagara, Parvata, Hamsa, Bheri, Chapa, Gauri, Mahabhagya, Vasumathi, the
  *-muladdhana* dhana yogas, and more.

**This is the concrete finding:** the yoga detector — the same machinery the increment-30 strength
token drew on — recognizes only ~1 in 4 of the combinations Raman actually names. That blindness is a
direct, mechanical reason the yoga-participation feature could not separate the strong slice: it was
absent on most of the yogas that carry Raman's strongest testimony. Closing this gap (encoding the
missing 34 detectors) is a well-defined future engine increment; the outcome corpus + example charts
are the durable data that would validate it, and also feed the daśā-timing corpus (the 41 charts carry
balance-of-daśā lines).

Reproduce: `PYTHONPATH=. python3 -m app.medini.doctrine.validation.yoga_coverage`. Measurement only;
no engine change. Pinned by `tests/doctrine/test_yoga_coverage.py`.
