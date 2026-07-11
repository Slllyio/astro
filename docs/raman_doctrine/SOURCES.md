# Raman Doctrine Compendium — Sources

All full texts are archive.org `_djvu.txt` OCR dumps. Per the established
fair-use policy, **full texts are never committed** — they live in the
session scratchpad and are re-fetchable at any time via:

```
python -m app.medini.doctrine.tools.fetch_sources --dest <scratch>/raman_sources
```

The sha256 below pins the exact OCR bytes every page map and every
`quote_sha256` in the compendium was derived from. The QC gate requires:
english_ratio >= 0.5, all book markers present, a near-monotonic folio
chain of >= 30 anchors reaching the book's plausibility floor.
Machine-readable copy of this table: `data/raman_doctrine/sources_qc.json`.
Page maps (mechanical char-offset -> printed-page): `data/raman_doctrine/page_maps/`.

## Fetched sources (QC PASS)

| key | title | archive.org item | bytes | eng | anchors | max page | QC |
|---|---|---|---:|---:|---:|---:|---|
| `hpa` | Hindu Predictive Astrology | `hindupredictiveastrologyofbvraman` | 488,502 | 0.74 | 396 | 460 | PASS |
|  | sha256: `4af231ccb13bc8a50a0d69232f383dec043e0638925ef15d07a0d177962fea02` | file: `Hindu Predictive Astrology of B V Raman_djvu.txt` | | | | | |
| `htjah_vol1` | How to Judge a Horoscope, Vol. 1 (houses I-VI) | `raman-how-to-judge-horoscope-2` | 467,478 | 0.92 | 277 | 304 | PASS |
|  | sha256: `88dc8d83cd83aa5464fe20ac79eb640234bf5cb0343372632772215fa032284e` | file: `raman-how-to-judge-horoscope-1_djvu.txt` | | | | | |
| `htjah_vol2` | How to Judge a Horoscope, Vol. 2 (houses VII-XII) | `raman-how-to-judge-horoscope-2` | 668,360 | 0.83 | 441 | 474 | PASS |
|  | sha256: `481920cf49edbb0b6f6050690f47152e50437ea10efb1045679e05b3dd3ce206` | file: `raman-how-to-judge-horoscope-2_djvu.txt` | | | | | |
| `three_hundred` | Three Hundred Important Combinations | `ThreeHundredImportantCombinationsInVedicAstrology` | 184,672 | 0.63 | 60 | 155 | PASS |
|  | sha256: `69f0e3567b2853142d2c6afa2822d54e48c9732aa1064489ac6a95461257f11e` | file: `Three Hundred Important Combinations in Vedic Astrology_djvu.txt` | | | | | |
| `notable_horoscopes` | Notable Horoscopes | `NotableHoroscopesBVR` | 731,925 | 0.71 | 372 | 439 | PASS |
|  | sha256: `b48f4737e9213a43e0357f759a3a7e695f51c96150cc4afd77eb1fa9338432f2` | file: `Notable Horoscopes_djvu.txt` | | | | | |
| `jaimini_studies` | Studies in Jaimini Astrology | `studies-in-jaimini-astrology-by-b-v-raman-127930441` | 209,041 | 0.85 | 34 | 146 | PASS |
|  | sha256: `9f106110d4a87fd2f6750ba1583570601aa09dee5b3dd15115d000781051986c` | file: `Studies-in-jaimini-astrology-by-b-v-raman-127930441_djvu.txt` | | | | | |
| `graha_bhava_balas` | Graha and Bhava Balas | `gzwo_graha-and-bhava-balas-by-b-v-raman-english-sanskrit-astrology-hindu-astrolo` | 134,978 | 0.73 | 53 | 107 | PASS |
|  | sha256: `3a515f06aeff8fb3c6d34fab4f46baf6484e759276defe6d10a12d2e01cc1c1f` | file: `Graha And Bhava Balas by B V Raman English Sanskrit Astrology Hindu Astrology Bangalore 1942 - Raman Publications_djvu.txt` | | | | | |
| `muhurtha` | Muhurtha (Electional Astrology) | `in.ernet.dli.2015.128092` | 238,966 | 0.80 | 97 | 217 | PASS |
|  | sha256: `dfd15e4c22d5edb74797b6e8ed0d6378e26218530c1cf92622cb8f3bb8aa0b1c` | file: `2015.128092.Muhurtha-Or-Electional-Astrology_djvu.txt` | | | | | |
| `prasna_marga_1` | Prasna Marga, Part 1 | `PrasnaMargaBVR` | 625,992 | 0.75 | 273 | 278 | PASS |
|  | sha256: `136976037ac1b5ce1bd49556c81afd313f02d8f8a2e95da75e0834fc9e0c326a` | file: `Prasna Marga 1_djvu.txt` | | | | | |
| `prasna_marga_2` | Prasna Marga, Part 2 | `prasna-marga-part-2-by-bv-raman` | 561,325 | 0.88 | 0 | — | PASS (no folios) |
|  | sha256: `aa74225e314994f9e39b669899a704132a9b29ddaeb7d287dea09f65afe29e47` | file: `Prasna Marga Part 2 by BV Raman_djvu.txt` | | | | | |
| `manual_hindu_astrology` | A Manual of Hindu Astrology | `ISVP_a-manual-of-hindu-astrology-by-venkat-raman-english-raman-publications-banglore` | 225,878 | 0.69 | 34 | 88 | PASS |
|  | sha256: `d5e4f7e8eab8b84ecf0bc6b141b607c6a95f6948c91750a518d7218e433f7204` | file: `A Manual Of Hindu Astrology By Venkat Raman English - Raman Publications, Banglore_djvu.txt` | | | | | |

## Item-selection notes

- **hpa**: `jmbQ_hindu-predictive-astrology-b.-v.-raman` was rejected — it is
  a Devanagari-script scan (english_ratio 0.00; the "hpa2.txt" precedent).
- **hpa (P2 completion, increments 19a–19g)**: the ~20 remaining HPA chapters
  were encoded from a user-supplied full text rather than a re-fetch. Its
  `<pre>` body was verified **byte-identical** (sha256 `4af231cc…`, 488,502
  bytes) to the pinned OCR above, so the existing page map and every prior
  `quote_sha256` apply unchanged and no source re-pin was needed.
- **htjah_vol1 + htjah_vol2**: one item (`raman-how-to-judge-horoscope-2`)
  carries both volumes' OCR files. Folios are running heads
  ("50 How to Judge a Horoscope" / "Concerning the Seventh House 51"),
  handled by per-book folio patterns.
- **prasna_marga_2**: the body OCR of this scan carries no folio anchors —
  the only bare page numbers are the table-of-contents dotted-leader columns,
  which (if scanned) form a fake monotonic chain fixed in the TOC region. The
  page map is therefore intentionally empty (built over the body slice,
  constrained to the real folio range p.270–430, yields zero anchors), so
  Part 2 records are cited by verbatim quote + sha256 pin with `page: null`.
  The quote-verification honesty gate still holds; only the printed-page
  number is unavailable for this scan.
- **graha_bhava_balas**: contains a year-by-year ayanamsa table (1826-1860)
  that forms a fake monotonic "page" chain; the page-map ceiling
  (max_page=800) plus running-head patterns recover the real folios.
- **jaimini_studies**: the page map was rebuilt over the body (past the
  contents at ~offset 15k) using the two running-head folios
  ("<section> Influences <page>" on right pages, "<page> Studies in Jaimini
  Astrology" on left) — 27 monotonic anchors (p.38–138). Records swept under
  the corrected map (sweep p7_deep, chapters `education`/`financial`) carry
  accurate pages; the earlier p6_t2/ch127 records predate the fix and retain
  their original stamps (records are immutable once written).
- **three_hundred**: ALL THREE archive.org scans of this title
  (`ThreeHundredImportantCombinationsInVedicAstrology`,
  `in.ernet.dli.2015.83552`, the 1947-ed item) are the same TRUNCATED
  volume: the text ends at yoga 162 (~p.156). Yogas 163-300 have no
  retrievable source and are recorded as unavailable in COVERAGE.md —
  extraction covers 1-162 only.

## Raman titles with NO retrievable archive.org text

Recorded so coverage claims stay honest; doctrine normally sourced from
these books must come from the overlapping chapters of the fetched ones
(e.g. ashtakavarga doctrine from HPA Ch. XXVI):

- Ashtakavarga System of Prediction
- A Catechism of Astrology
- My Experiences in Astrology
- Hindu Astrology and the West
- Bhavartha Ratnakara (translation)
